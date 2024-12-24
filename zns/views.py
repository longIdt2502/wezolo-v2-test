import json
from datetime import datetime
from typing import Optional
import uuid

from django.db import transaction
from django.db.models import OuterRef, Q, F, Case, When, Value, CharField, IntegerField
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

from common.core.subquery import *
from .common.lhe import *
from employee.models import Employee, EmployeeOa
from package.models import Price
from reward.models import RewardBenefit
from utils.check_financial_capacity import checkFinancialCapacity
from utils.convert_response import convert_response
from workspace.models import Role
from zalo.models import UserZalo, ZaloOA
from zalo.utils import convert_phone
from zalo_messages.utils import send_message_text, send_zns
from zns.models import *
from zns.utils import (
    createZnsFieldTitle, createZnsFieldParagraph, createZnsFieldOTP,
    createZnsFieldTable, createZnsFieldLogo, createZnsFieldImage,
    createZnsFieldButton, createZnsFieldPayment, createZnsFieldVoucher
)


class ZnsApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = request.GET.copy()
        page_size = int(data.get('page_size', 20))
        offset = (int(data.get('page', 1)) - 1) * page_size

        zns = Zns.objects.filter()
        employee = Employee.objects.filter(account=user)
        ws_query = data.get('workspace')
        if ws_query:
            employee = employee.filter(workspace_id=ws_query)
            zns = zns.filter(oa__company_id=ws_query)

        oa_query = data.get('oa')
        if oa_query:
            oa = ZaloOA.objects.get(id=oa_query)
            employee = employee.filter(workspace=oa.company)
            zns = zns.filter(oa_id=oa_query)

        employee = employee.first()

        if not employee:
            return convert_response('Bạn không có quyền truy cập')
        if employee.role == Role.Code.SALE:
            employee_oa = EmployeeOa.objects.filter(employee=employee)
            oas = employee_oa.values_list('oa_id', flat=True)
            zns = zns.filter(oa_id__in=oas)
            if oa_query not in oas:
                return convert_response('Bạn không có quyền truy cập OA', 400)

        search = data.get('search')
        if search:
            zns = zns.filter(Q(name__icontains=search) | Q(template__icontains=search))
        total = zns.count()

        status = data.get('status')
        if status:
            zns = zns.filter(status=status)

        type_zns = data.get('type')
        if type_zns:
            zns = zns.filter(type=type_zns)

        tag = data.get('tag')
        if tag:
            zns = zns.filter(tag=tag)

        oa_subquery = SubqueryJson(
            ZaloOA.objects.filter(id=OuterRef('oa_id')).values(
                'id', 'oa_name', 'oa_avatar'
            )[:1]
        )

        params_query = SubqueryJsonAgg(
            ZnsParams.objects.filter(zns_id=OuterRef('id')).values()
        )

        _, _, price = checkFinancialCapacity(user, Price.Type.ZNS)

        zns = zns.order_by('-id')[offset: offset + page_size].values().annotate(
            oa_data=oa_subquery,
            params=params_query,
        )

        for item in zns:
            item['price'] = price.value.value

        return convert_response('success', 200, data=zns, total=total)


class ZnsCreateApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data.copy()
        data = json.loads(request.POST.get('data'))
        files = request.FILES.getlist('images', None)
        logo_light = request.FILES.get('logo_light', None)
        logo_dark = request.FILES.get('logo_dark', None)

        try:
            with transaction.atomic():
                zns = Zns.objects.create(
                    name=data.get('name'),
                    status=data.get('status'),
                    type=data.get('type'),
                    tag=data.get('tag'),
                    oa_id=data.get('oa'),
                    note=data.get('note'),
                    price=data.get('price', 0),
                    created_by=user,
                )

                components = data.get('components', [])
                for item in components:
                    err = create_zns_field(zns, item, files, logo_light, logo_dark)
                    if err:
                        raise Exception(err)

                params = data.get('params', [])
                for item in params:
                    ZnsParams.objects.create(
                        zns=zns,
                        name=item.get('name'),
                        type=item.get('type'),
                        sample_value=item.get('sample_value')
                    )

                return convert_response('success', 201, data=zns.id)
        except Exception as e:
            return convert_response(str(e), 400)


def create_zns_field(zns: Zns, data, files, logo_light, logo_dark) -> Optional[str]:
    type_field = data.get('type')
    if type_field == 'TITLE':
        return createZnsFieldTitle(zns=zns, data=data)
    elif type_field == 'PARAGRAPH':
        return createZnsFieldParagraph(zns=zns, data=data)
    elif type_field == 'OTP':
        return createZnsFieldOTP(zns=zns, data=data)
    elif type_field == 'TABLE':
        return createZnsFieldTable(zns=zns, data=data)
    elif type_field == 'LOGO':
        if not logo_dark or not logo_light:
            return 'Thiếu trường ảnh Logo sáng/tối'
        return createZnsFieldLogo(zns=zns, data=data, logo_light=logo_light, logo_dark=logo_dark)
    elif type_field == 'IMAGES':
        if not files or len(files) == 0:
            return 'Thiếu trường ảnh'
        return createZnsFieldImage(zns=zns, data=data, files=files)
    elif type_field == 'BUTTONS':
        return createZnsFieldButton(zns=zns, data=data)
    elif type_field == 'PAYMENT':
        return createZnsFieldPayment(zns=zns, data=data)
    elif type_field == 'VOUCHER':
        return createZnsFieldVoucher(zns=zns, data=data)
    return 'Loại component không hợp lệ'


class ZnsDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, _, pk):
        zns = Zns.objects.filter(id=pk)
        if not zns:
            return convert_response('Không tìm thấy Zns', 404)
        component_subquery = SubqueryJsonAgg(
            ZnsComponentZns.objects.filter(
                zns_id=OuterRef('id')
            ).order_by('order').annotate(
                component_name=F('component__name'),
                type=F('component__type'),
                layout=F('component__layout'),
                component_data=Case(
                    When(component__type='TITLE', then=SubqueryJson(
                        ZnsFieldTitle.objects.filter(component_id=OuterRef('id')).values()[:1]
                    )),
                    When(component__type='PARAGRAPH', then=SubqueryJson(
                        ZnsFieldParagraph.objects.filter(component_id=OuterRef('id')).values()[:1]
                    )),
                    When(component__type='OTP', then=SubqueryJson(
                        ZnsFieldOTP.objects.filter(component_id=OuterRef('id')).values()[:1]
                    )),
                    When(component__type='TABLE', then=SubqueryJsonAgg(
                        ZnsFieldTable.objects.filter(component_id=OuterRef('id')).values()
                    )),
                    When(component__type='LOGO', then=SubqueryJson(
                        ZnsFieldLogo.objects.filter(component_id=OuterRef('id')).values()[:1]
                    )),
                    When(component__type='IMAGES', then=SubqueryJsonAgg(
                        ZnsFieldImage.objects.filter(component_id=OuterRef('id')).values()
                    )),
                    When(component__type='BUTTONS', then=SubqueryJsonAgg(
                        ZnsFieldButton.objects.filter(component_id=OuterRef('id')).values()
                    )),
                    When(component__type='PAYMENT', then=SubqueryJson(
                        ZnsFieldPayment.objects.filter(component_id=OuterRef('id')).values()[:1]
                    )),
                    When(component__type='VOUCHER', then=SubqueryJson(
                        ZnsFieldVoucher.objects.filter(component_id=OuterRef('id')).values()[:1]
                    )),
                    default=Value(None),
                    output_field=JSONField()
                )
            )
        )
        price = SubqueryJson(
            Price.objects.filter(id=OuterRef('value_id')).values()[:1]
        )
        price_query = SubqueryJson(
            RewardBenefit.objects.filter(tier_id=OuterRef('created_by__level'), type='ZNS').values().annotate(
                price=price
            )[:1]
        )
        params_subquery = SubqueryJsonAgg(
            ZnsParams.objects.filter(zns_id=OuterRef('id')).annotate(
                type_label=Case(
                    When(type='1', then=Value('Tên khách hàng (30)')),
                    When(type='2', then=Value('Số điện thoại (15)')),
                    When(type='3', then=Value('Địa chỉ (200)')),
                    When(type='4', then=Value('Mã số (30)')),
                    When(type='5', then=Value('Nhãn tùy chỉnh (30)')),
                    When(type='6', then=Value('Trạng thái giao dịch (30)')),
                    When(type='7', then=Value('Thông tin liên hệ (50)')),
                    When(type='8', then=Value('Giới tính / Danh xưng (5)')),
                    When(type='9', then=Value('Tên sản phẩm / Thương hiệu (200)')),
                    When(type='10', then=Value('Số lượng / Số tiền (20)')),
                    When(type='11', then=Value('Thời gian (20)')),
                    When(type='12', then=Value('OTP (10)')),
                    When(type='13', then=Value('URL (200)')),
                    When(type='14', then=Value('Tiền tệ (VNĐ) (12)')),
                    When(type='15', then=Value('Bank transfer note (90)')),
                    default=Value(''),
                    output_field=CharField()
                )
            )
        )
        oa_subquery = SubqueryJson(
            ZaloOA.objects.filter(id=OuterRef('oa_id')).values(
                'id', 'oa_name', 'oa_avatar',
            )[:1]
        )
        zns = zns.values().annotate(
            components=component_subquery,
            params=params_subquery,
            price=price_query,
            oa=oa_subquery,
        )[:1]
        return convert_response('success', 200, data=zns[0])

    def put(self, request, pk):
        user = request.user
        data = json.loads(request.POST.get('data'))
        files = request.FILES.getlist('images', None)
        logo_light = request.FILES.get('logo_light', None)
        logo_dark = request.FILES.get('logo_dark', None)

        try:
            with transaction.atomic():
                zns = Zns.objects.get(id=pk)
                if not user.is_superuser:
                    employee = Employee.objects.filter(account=user, workspace=zns.oa.company).first()
                    if not employee or employee.role.code == 'SALE':
                        raise Exception('Từ chối quyền truy cập')
                if zns.status != 'DRAFT' and zns.status != 'REJECTED':
                    raise Exception('Trạng thái ZNS không thể chỉnh sửa')

                zns.name = data.get('name', zns.name)
                zns.type = data.get('type', zns.type)
                zns.tag = data.get('tag', zns.tag)
                zns.note = data.get('note', zns.note)
                zns.save()

                components = data.get('components', [])
                for item in components:
                    err = create_zns_field(zns, item, files, logo_light, logo_dark)
                    if err:
                        raise Exception(err)

                params = data.get('params', [])
                params_in_zns = ZnsParams.objects.filter(zns=zns)
                for item in params_in_zns:
                    item.delete()
                for item in params:
                    ZnsParams.objects.create(
                        zns=zns,
                        name=item.get('name'),
                        type=item.get('type'),
                        sample_value=item.get('sample_value')
                    )

                return convert_response('success', 201, data=zns.id)
        except Exception as e:
            return convert_response(str(e), 400)

    def patch(self, request, pk):
        try:
            user = request.user
            data = request.data.copy()
            zns = Zns.objects.get(id=pk)

            if not user.is_superuser:
                employee = Employee.objects.filter(account=user, workspace=zns.oa.company).first()
                if not employee or employee.role.code == 'SALE':
                    raise Exception('Từ chối quyền truy cập')

            zns.status = data.get('status', zns.status)
            zns.template = data.get('template', zns.template)
            zns.updated_by = user
            zns.updated_at = datetime.now()
            zns.save()
            return convert_response('success', 203, data=zns.id)
        except Exception as e:
            return convert_response(str(e), 400)

    def delete(self, request, pk):
        user = request.user
        zns = Zns.objects.get(id=pk)

        try:
            if not user.is_superuser:
                employee = Employee.objects.filter(account=user, workspace=zns.oa.company).first()
                if not employee or employee.role.code == 'SALE':
                    raise Exception('Từ chối quyền truy cập')

            if zns.status != 'DRAFT' and zns.status != 'REJECTED':
                raise Exception('Trạng thái ZNS không thể chỉnh sửa')

            zns.delete()
            return convert_response('success', 200)
        except Exception as e:
            return convert_response(str(e), 400)


class ZnsTypePrice(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        price_subquery = SubqueryJson(
            Price.objects.filter(id=OuterRef('value'))
        )
        reward_benefit = RewardBenefit.objects.filter(tier_id=user.level, type='ZNS').values().annotate(
            price=price_subquery
        )
        return convert_response('success', 200, data=reward_benefit)



class MessageOpenApi(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        authorization = request.headers.get("Authorization")
        application_id = request.headers.get("X-Application-Id")
        secret_key = request.headers.get("X-Secret-Key")
        data = request.data.copy()

        oa_id = data.get("oa_id")
        data = data.get("data")
        # find oa object has oa_id equal oa_id in serializer
        oa = ZaloOA.objects.filter(oa_id=oa_id).first()
        if not oa:
            return convert_response("Error", 400, data={"message": "oa not found"})
        # amount = os.environ.get("ZNS_DEFAULT_PRICE", 350)
        type_str = data.get("type")
        phone = data.get("phone")
        if phone.startswith('0'):
            phone = phone.replace('0', '84', 1)
        user_follow = UserZalo.objects.filter(phone=phone, oa_id=oa_id).first()
        if user_follow is not None and oa.id == 6:
            message = ""
            if type_str == Zns.TemplateTypes.SEND_OTP:
                message = data.get("otp")
            if oa.id == 6 and type_str == Zns.TemplateTypes.CONFIRM_ORDER:
                message = generate_confirmation_order_pharmago(data)
            if type_str == Zns.TemplateTypes.LHE_CREATED_ORDER:
                message = generate_created_order_lhe(data)
            if type_str == Zns.TemplateTypes.LHE_CONFIRM_ORDER:
                message = generate_confirm_order_lhe(data)
            # res = send_message_v2(oa, user_follow.user_id, message, uuid.uuid4().hex, [], request.user.id)
            res = send_message_text(oa, user_follow.user_zalo_id, message)
            return convert_response("Success", 200, data=res)
        else:
            mode = data.get("mode", "development")

            tracking_id = uuid.uuid4().hex
            template = Zns.objects.filter(type_third_party=type_str, oa=oa).first()
            if not template:
                return convert_response("Error", 400, data={"message": "template not found"})
            template_id = template.template
            # zns_custom = ZNSWorkspaceCustom.objects.filter(template_id=template_id).first()
            res = {}
            # amount = oa.get_pricing_zns(zns_custom.id)
            can_send, wallet, reward_benefit = checkFinancialCapacity(oa.company.created_by, Price.Type.ZNS)
            amount = reward_benefit.value.value
            if mode == "development":
                res = send_zns(oa, template_id, data, phone, tracking_id, mode)
            elif mode == "production":
                # can_send = check_account_balance(oa, int(reward_benefit.value.value))
                if not can_send:
                    return convert_response("Error", 400, data={"message": "Số dư trong ví không đủ để thực hiện"})
                WalletTransaction.objects.create(
                    wallet=wallet,
                    type=WalletTransaction.Type.OUT_ZNS,
                    method=WalletTransaction.Method.WALLET,
                    amount=amount,
                    user=wallet.owner,
                    total_amount=amount,
                    oa=oa,
                    used_at=datetime.now()
                )
                res = send_zns(oa, template_id, data, phone, tracking_id, mode)
            res = json.loads(res)
            success = res.get("message", "") == "Success" and int(
                res.get("error", 1)) == 0
            if not success:
                WalletTransaction.objects.create(
                    wallet=wallet,
                    type=WalletTransaction.Type.IN_ZNS,
                    method=WalletTransaction.Method.WALLET,
                    amount=amount,
                    user=wallet.owner,
                    total_amount=amount,
                    oa=oa,
                    used_at=datetime.now()
                )
            # save send log
            # ZNSSendLog.objects.create(
            #     oa=oa,
            #     template_id=template_id,
            #     data=data,
            #     mode=mode,
            #     to=phone,
            #     res=res
            # )
            return convert_response("Success", 200, data=res)



class MessageOpenApiV2(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        authorization = request.headers.get("Authorization")
        application_id = request.headers.get("X-Application-Id")
        secret_key = request.headers.get("X-Secret-Key")
        
        data = request.data.copy()

        oa_id = data.get('oa')
        payload = data.get('payload')
        zns_id = data.get('zns')
        if not oa_id or not zns_id or not payload:
            return convert_response("Error", 400, data={"message": "Missing required parameters"})
        phone_number = data.get('phone')
        tracking_id = data.get('tracking_id', uuid.uuid4().hex)
        if phone_number.startswith("0"):
            phone_number = convert_phone(phone_number)
        mode = data.get("mode", "development")
        oa = ZaloOA.objects.filter(oa_id=oa_id).first()
        res = {}
        if mode == "development":
            res = send_zns(oa, zns_id, payload, phone_number, tracking_id, mode)
        elif mode == "production":
            can_send, wallet, reward_benefit = checkFinancialCapacity(oa.company.created_by, Price.Type.ZNS)
            if not can_send:
                return convert_response("Error", 400, data={"message": "Số dư trong ví không đủ"})
            amount = reward_benefit.value.value
            WalletTransaction.objects.create(
                wallet=wallet,
                type=WalletTransaction.Type.OUT_ZNS,
                method=WalletTransaction.Method.WALLET,
                amount=amount,
                user=wallet.owner,
                total_amount=amount,
                oa=oa,
                used_at=datetime.now()
            )
            res = send_zns(oa, zns_id, payload, phone_number, tracking_id, mode)
            # if not isinstance(res, dict):
            #     res = json.loads(res)
            success = res.get("message", "") == "Success" and int(
                res.get("error", 1)) == 0
            if not success:
                WalletTransaction.objects.create(
                    wallet=wallet,
                    type=WalletTransaction.Type.IN_ZNS,
                    method=WalletTransaction.Method.WALLET,
                    amount=amount,
                    user=wallet.owner,
                    total_amount=amount,
                    oa=oa,
                    used_at=datetime.now()
                )
        return convert_response("success", 200, data=res)
