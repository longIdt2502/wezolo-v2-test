import base64
import hashlib
import json
import os
import random

from datetime import datetime, timedelta

import django_rq

from common.redis.config import task_queue
from django.db import transaction
from rest_framework.views import APIView
from utils.convert_response import convert_response
from rest_framework.permissions import IsAuthenticated, AllowAny
from common.file_ext import get_file_extension
from common.pref_keys import PrefKeys

from common.redis.connect_oa_job import connect_oa_job
from .utils import get_token_from_code, get_oa_info
from .models import ZaloOA, CodeVerifier, UserZalo, Message
from user.models import Address
from wallet.models import WalletTransaction, Wallet
from reward.models import RewardBenefit
from package.models import Price
from workspace.models import Workspace


class ZaloOaAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        zalo_oa = ZaloOA.objects.filter().order_by('-id').values()
        return convert_response('success', 200, data=zalo_oa)

    def post(self, request):
        user = request.user

        data = json.loads(request.POST.get('data'))
        address_data = json.loads(request.POST.get('address'))
        if not address_data:
            return convert_response('Yêu cầu thông tin địa chỉ', 400)

        # check money in wallet user
        oa = ZaloOA.objects.filter(created_by=user).count()
        if oa > 0:
            wallet = Wallet.objects.filter(owner=user).first()
            if not wallet:
                return convert_response('Ví không tồn tại', 400)
            reward_benefit = RewardBenefit.objects.filter(tier_id=user.level, type=Price.Type.CREATE_OA).first()
            if not reward_benefit:
                return convert_response('Không tìm thấy gói lợi ích giá phù hợp', 400)
            if wallet.balance < reward_benefit.value.value:
                return convert_response('Số dư ví không đủ để thực hiện thao tác', 400)

        # handle file upload
        image_avatar = request.FILES.get('image_avatar')
        if not image_avatar:
            return convert_response('Cần ảnh đại diện OA', 400)
        image_cover = request.FILES.get('image_cover')
        if not image_cover:
            return convert_response('Cần ảnh bìa OA', 400)
        giay_dang_ky = request.FILES.get('giay_dang_ky')
        cccd_truoc = request.FILES.get('cccd_truoc')
        cccd_sau = request.FILES.get('cccd_sau')
        ho_chieu = request.FILES.get('ho_chieu')
        cong_van = request.FILES.get('cong_van')
        chung_minh = request.FILES.get('chung_minh')
        if (not giay_dang_ky or not cccd_truoc or not cccd_sau) and (not cong_van or not chung_minh):
            return convert_response('Thiếu tài liệu tạo OA', 400)

        check = True
        while check:
            code = random.randint(100000, 999999)
            zalo_oa_ins = ZaloOA.objects.filter(code_ref=code).first()
            if zalo_oa_ins:
                continue
            zalo_oa = ZaloOA.objects.create(
                company_id=data.get('workspace'),
                code_ref=code,
                status=ZaloOA.Status.PENDING,
                description=f"[{code}] {data.get('description')}",
                oa_name=data.get('oa_name'),
                cate_name=data.get('cate_name'),
                created_by=user,
            )
            address_ins = Address().create_from_json(address_data)
            zalo_oa.address = address_ins
            url = zalo_oa.upload_file(image_avatar, f'image_avatar{get_file_extension(image_avatar.name)}')
            zalo_oa.oa_avatar = url
            url = zalo_oa.upload_file(image_cover, f'image_cover{get_file_extension(image_cover.name)}')
            zalo_oa.oa_cover = url
            if giay_dang_ky:
                url = zalo_oa.upload_file(giay_dang_ky, f'giay_dang_ky{get_file_extension(giay_dang_ky.name)}')
                zalo_oa.giay_dang_ky = url
            if cccd_truoc and cccd_sau:
                url_front = zalo_oa.upload_file(cccd_truoc, f'cccd_truoc{get_file_extension(cccd_truoc.name)}')
                url_back = zalo_oa.upload_file(cccd_sau, f'cccd_sau{get_file_extension(cccd_sau.name)}')
                zalo_oa.cccd_truoc = url_front
                zalo_oa.cccd_sau = url_back
            if cong_van:
                url = zalo_oa.upload_file(cong_van, f'cccd_sau{get_file_extension(cong_van.name)}')
                zalo_oa.cong_van = url
            if chung_minh:
                url = zalo_oa.upload_file(chung_minh, f'cccd_sau{get_file_extension(chung_minh.name)}')
                zalo_oa.chung_minh = url
            if ho_chieu:
                url = zalo_oa.upload_file(ho_chieu, f'ho_chieu{get_file_extension(ho_chieu.name)}')
                zalo_oa.ho_chieu = url
            zalo_oa.save()

            WalletTransaction.objects.create(
                wallet=wallet,
                user=user,
                type=WalletTransaction.Type.EXPENDITURE,
                method=WalletTransaction.Method.TRANSFER,
                amount=reward_benefit.value.value,
                total_amount=reward_benefit.value.value,
                oa=zalo_oa,
            )

            check = False
            return convert_response('success', 201, data=zalo_oa.id)


class ZaloOaDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        zalo_oa = ZaloOA.objects.filter(id=pk).values(
            'code_ref', 'status', 'app_id', 'oa_id', 'oa_name', 'oa_avatar', 'oa_cover', 'cate_name',
            'description', 'oa_type', 'num_follower', 'package_name', 'package_valid_through_date',
            'package_auto_renew_date'
        ).first()
        return convert_response('success', 200, data=zalo_oa)

    def put(self, request, pk):
        zalo_oa = ZaloOA.objects.get(id=pk)
        if not zalo_oa:
            return convert_response('Dữ liệu không tồn tại', 400)
        if zalo_oa.status != ZaloOA.Status.PENDING:
            return convert_response('Thông tin đã được gửi lên Zalo, không thể chỉnh sửa', 400)
        data = json.loads(request.POST.get('data'))
        zalo_oa.cate_name = data.get('cate_name', zalo_oa.cate_name)
        zalo_oa.description = data.get('description', zalo_oa.description)
        zalo_oa.oa_name = data.get('oa_name', zalo_oa.oa_name)
        zalo_oa.cate_name = data.get('cate_name', zalo_oa.cate_name)
        zalo_oa.cate_name = data.get('cate_name', zalo_oa.cate_name)
        zalo_oa.save()

        address_data = json.loads(request.POST.get('address'))
        if address_data:
            if zalo_oa.address:
                zalo_oa.address.update_from_json(address_data)
                zalo_oa.address.save()

        # handle file upload
        image_avatar = request.FILES.get('image_avatar')
        if image_avatar:
            url = zalo_oa.upload_file(image_avatar, f'image_avatar{get_file_extension(image_avatar.name)}')
            zalo_oa.oa_avatar = url

        image_cover = request.FILES.get('image_cover')
        if image_cover:
            url = zalo_oa.upload_file(image_cover, f'image_cover{get_file_extension(image_cover.name)}')
            zalo_oa.oa_cover = url

        giay_dang_ky = request.FILES.get('giay_dang_ky')
        if giay_dang_ky:
            url = zalo_oa.upload_file(giay_dang_ky, f'giay_dang_ky{get_file_extension(giay_dang_ky.name)}')
            zalo_oa.giay_dang_ky = url

        cccd_truoc = request.FILES.get('cccd_truoc')
        cccd_sau = request.FILES.get('cccd_sau')
        if cccd_truoc and cccd_sau:
            url_front = zalo_oa.upload_file(cccd_truoc, f'cccd_truoc{get_file_extension(cccd_truoc.name)}')
            url_back = zalo_oa.upload_file(cccd_sau, f'cccd_sau{get_file_extension(cccd_sau.name)}')
            zalo_oa.cccd_truoc = url_front
            zalo_oa.cccd_sau = url_back

        ho_chieu = request.FILES.get('ho_chieu')
        if ho_chieu:
            url = zalo_oa.upload_file(ho_chieu, f'ho_chieu{get_file_extension(ho_chieu.name)}')
            zalo_oa.ho_chieu = url

        cong_van = request.FILES.get('cong_van')
        if cong_van:
            url = zalo_oa.upload_file(cong_van, f'cccd_sau{get_file_extension(cong_van.name)}')
            zalo_oa.cong_van = url
        chung_minh = request.FILES.get('chung_minh')
        if chung_minh:
            url = zalo_oa.upload_file(chung_minh, f'cccd_sau{get_file_extension(chung_minh.name)}')
            zalo_oa.chung_minh = url

        zalo_oa.save()

        return convert_response('success', 200, data=zalo_oa.id)


class ZaloOaAcceptAuth(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            with transaction.atomic():
                data = request.GET.copy()
                oa_id = data.get('oa_id_wezolo')
                workspace = Workspace.objects.get(id=pk).company

                # wallet check
                wallet = Wallet.objects.filter(owner=workspace.created_by).first()
                if not wallet:
                    raise Exception('Ví không hợp lệ')
                if wallet.balance < 1500000:
                    raise Exception('Số dư ví không đủ để thực hiện kết nối')

                # gen access_token from code and code_challenge
                code = data.get('code')
                code_challenge = data.get('code_challenge')
                code_verify = CodeVerifier.objects.filter(code_challenge=code_challenge).last()
                if not code:
                    raise Exception('Không nhận được code từ Zalo')

                res_token = get_token_from_code(code, code_verify.code_verifier)
                err = res_token.get('error_name')
                if err:
                    raise Exception(str(err))

                access_token = res_token['access_token']
                refresh_token = res_token['refresh_token']

                # check Zalo Info: package_name nâng cao
                oa_info = get_oa_info(access_token, refresh_token)
                data_oa_info = oa_info.get('data')
                package_name = data_oa_info.get('package_name')
                if not package_name:
                    raise Exception('Gói tài khoản Zalo OA chưa được nâng cấp')

                # update zalo_oa in wezolo db
                # zalo_oa = ZaloOA()
                if oa_id != 'None':
                    zalo_oa = ZaloOA.objects.filter(id=oa_id).first()
                    if not zalo_oa:
                        raise Exception('Zalo Oa không tồn tại')
                    oa_id_zalo = data_oa_info.get('oa_id')
                    if zalo_oa.oa_id and zalo_oa.oa_id != oa_id_zalo:
                        raise Exception('Zalo Oa đã được kết nối trước đó')
                    zalo_oa.oa_id = oa_id_zalo
                    zalo_oa.access_token = access_token
                    zalo_oa.refresh_token = refresh_token
                    zalo_oa.save()
                else:
                    zalo_oa = ZaloOA.objects.filter(oa_id=data_oa_info.get('oa_id')).first()
                    if zalo_oa and zalo_oa.company != workspace:
                        raise Exception('Zalo Oa đã được kết nối với Workspace khác')
                    if zalo_oa:
                        zalo_oa.oa_id = data_oa_info.get('oa_id')
                        zalo_oa.oa_name = data_oa_info.get('name')
                        zalo_oa.description = data_oa_info.get('description')
                        zalo_oa.oa_type = data_oa_info.get('oa_type')
                        zalo_oa.cate_name = data_oa_info.get('cate_name')
                        zalo_oa.num_follower = data_oa_info.get('num_follower')
                        zalo_oa.oa_avatar = data_oa_info.get('oa_avatar')
                        zalo_oa.oa_cover = data_oa_info.get('oa_cover')
                        zalo_oa.package_name = data_oa_info.get('package_name')
                        zalo_oa.access_token = data_oa_info.get('access_token')
                        zalo_oa.access_token = data_oa_info.get('access_token')
                        zalo_oa.refresh_token = data_oa_info.get('refresh_token')
                        zalo_oa.status = ZaloOA.Status.CONNECTED
                        zalo_oa.package_valid_through_date = datetime.strptime(
                            data_oa_info.get('package_valid_through_date'),
                            "%d/%m/%Y"
                        )
                        zalo_oa.package_auto_renew_date = datetime.strptime(
                            data_oa_info.get('package_auto_renew_date'),
                            "%d/%m/%Y"
                        )
                        zalo_oa.save()
                    else:
                        zalo_oa = ZaloOA.objects.create(
                            oa_id=data_oa_info.get('oa_id'),
                            oa_name=data_oa_info.get('name'),
                            description=data_oa_info.get('description'),
                            oa_type=data_oa_info.get('oa_type'),
                            cate_name=data_oa_info.get('cate_name'),
                            num_follower=data_oa_info.get('num_follower'),
                            oa_avatar=data_oa_info.get('avatar'),
                            oa_cover=data_oa_info.get('cover'),
                            package_name=data_oa_info.get('package_name'),
                            access_token=access_token,
                            refresh_token=refresh_token,
                            activate=True,
                            status=ZaloOA.Status.CONNECTED,
                            package_valid_through_date=datetime.strptime(
                                data_oa_info.get('package_valid_through_date'),
                                "%d/%m/%Y"
                            ),
                            package_auto_renew_date=datetime.strptime(
                                data_oa_info.get('package_auto_renew_date'),
                                "%d/%m/%Y"
                            )
                        )

                django_rq.enqueue(connect_oa_job, access_token, zalo_oa.id)

                return convert_response('success', 200, data=zalo_oa.to_json())
        except Exception as e:
            return convert_response(str(e), 400)


class ZaloOaUrlConnection(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            query = request.GET.copy()
            workspace_id = query.get('workspace')
            zalo_oa_id = query.get('zalo_oa')
            workspace = Workspace.objects.filter(id=workspace_id).first()
            if not workspace:
                raise Exception('workspace không tồn tại')
            # oa = ZaloOA.objects.filter(id=zalo_oa_id).first()
            # if not workspace:
            #     raise Exception('Zalo Oa không tồn tại')
            # if oa.company != workspace or workspace.created_by != user:
            #     raise Exception('Thông tin người dùng/Workspace không hợp lệ')
            code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
            code_verifier = code_verifier.rstrip('=')
            # Create SHA-256 hash of the code verifier
            hashed = hashlib.sha256(code_verifier.encode('utf-8')).digest()
            # Base64 URL-encode the hash
            code_challenge = base64.urlsafe_b64encode(hashed).decode('utf-8')
            code_challenge = code_challenge.rstrip('=')
            CodeVerifier.objects.create(workspace_id=workspace_id, code_verifier=code_verifier,
                                        code_challenge=code_challenge)
            oa_auth_domain = os.getenv(PrefKeys.ZALO_OA_AUTH_DOMAIN)
            app_id = os.getenv(PrefKeys.ZALO_APP_ID)
            redirect_uri = f'https%3A%2F%2F5b80-222-252-18-38.ngrok-free.app%2Fv1%2Fzalo%2Fzalo_oa_accept_auth%2Fhook%2F{workspace_id}%3Fcode_challenge%3D{code_challenge}%26oa_id_wezolo%3D{zalo_oa_id}%0A'
            # url = f"{oa_auth_domain}?app_id={app_id}&code_challenge={code_challenge}&redirect_uri={redirect_uri}"
            url = f"{oa_auth_domain}?app_id={app_id}&code_challenge={code_challenge}&redirect_uri=replace_uri"
            return convert_response('success', 200, data=url)
        except Exception as e:
            return convert_response(str(e), 400)


class ZaloUserCreate(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()
        user_zalo = UserZalo.objects.create(
            name=data.get('name'),
            phone=data.get('phone'),
            user_zalo_id=data.get('user_zalo_id'),
            avatar_small=data.get('avatar_small'),
            avatar_big=data.get('avatar_big'),
            oa_id=data.get('oa_id'),
            is_follower=data.get('is_follower')
        )
        return convert_response('success', 200, data=user_zalo.id)


class ZaloMessageCreate(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            items = request.data.copy()
            if len(items) == 0:
                return convert_response('Dữ liệu rỗng', 400)
            user = UserZalo.objects.filter(user_zalo_id=items[0].get('user_zalo_oa')).first()
            if not user:
                return convert_response('Người dùng Zalo không tồn tại', 400)
            message_ins = [
                Message(
                    message_id=item.get('message_id'),
                    src=item.get('src'),
                    send_by=user,
                    time=item.get('time'),
                    send_at=datetime.strptime(item.get('sent_time'), "%H:%M:%S %d/%m/%Y") if item.get(
                        'sent_time') else None,
                    type_message=Message.Type.TEXT,
                    type_send=Message.TypeSend.USER,
                    message_thumb=item.get('message_thumb'),
                    from_id=item.get('from_id'),
                    to_id=item.get('to_id'),
                    success=True,
                    oa=user.oa,
                    message_text=item.get('message'),
                )
                for item in items
            ]
            Message.objects.bulk_create(message_ins)
            return convert_response('success', 200)
        except Exception as e:
            return convert_response(str(e), 400)
