from datetime import datetime
import json
import random
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.db.models import OuterRef, Q, Case, When, Value
from django.core.files.base import ContentFile
from common.s3 import AwsS3
from common.zalo.request import update_token_oa
import requests
from rest_framework import response, status
from utils.convert_response import convert_response
from workspace.models import Role
from ws.event import send_message_to_ws
from common.core.subquery import *

from zalo.models import UserZalo, ZaloOA
from zalo_messages.models import Message
from tags.models import TagUserZalo
from employee.models import Employee, EmployeeUserZalo
from zalo_messages.utils import send_message_text


class MessageApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = request.GET.copy()

        page_size = int(data.get('page_size', 20))
        offset = (int(data.get('page', 1)) - 1) * page_size

        # Kiểm tra user request có quyền truy cập vào OA đã chọn không
        zalo_oa_id = data.get('oa')
        if not zalo_oa_id:
            return convert_response('Yêu cầu truyền OA', 400)
        oa = ZaloOA.objects.filter(uid_zalo_oa=zalo_oa_id).first()

        workspaces = Employee.objects.filter(account=user).values_list('workspace_id', flat=True)
        if oa.company.id not in workspaces:
            return convert_response('Bạn không có quyền truy cập', 403)

        if not oa:
            return convert_response('Oa không tồn tại', 400)

        # Kiểm tra quyền -> Nếu là SALE -> tìm các khách hàng được phần công cho nhân viên
        employee = Employee.objects.get(account=user, workspace=oa.company)
        user = UserZalo.objects.filter(oa=oa)
        if employee.role == Role.Code.SALE:
            employee_userzalo = EmployeeUserZalo.objects.filter(employee=employee).values_list('customer_id', flat=True)
            user = user.filter(id__in=employee_userzalo)
        total = user.count()

        search = data.get('search')
        if search:
            user = user.filter(Q(name__icontains=search) | Q(phone__icontains=search))

        tags = data.get('tags')
        if tags:
            tags = tags.split(',')
            tags_query = TagUserZalo.objects.filter(tag_id__in=tags)
            user_id_in_tags = tags_query.values_list('user_zalo_id', flat=True)
            user = user.filter(id__in=user_id_in_tags)
        
        user = user.annotate(
            is_null_last_message_time=Case(
                When(last_message_time__isnull=True, then=Value(1)),
                When(last_message_time__isnull=False, then=Value(0)),
            )
        )
        users = user.order_by('is_null_last_message_time', '-last_message_time')[offset: offset + page_size]
        res = []
        for item in users:
            res.append(item.to_json())
        return convert_response('success', 200, data=res, total=total)

    def post(self, request):
        try:
            user = request.user

            data = json.loads(request.POST.get('data'))
            user_zalo_id = data.get('user_zalo_id')
            oa = ZaloOA.objects.get(id=data.get('oa'))
            user_zalo = UserZalo.objects.get(user_zalo_id=user_zalo_id)
            
            attachment = {}
            # message_url = None
            images = request.FILES.getlist('images', None)
            if images:
                # message_url = []
                attachment['type'] = 'template'
                attachment['payload'] = {
                    "template_type": "media",
                    "elements": []
                }
                for file in images:
                    r = random.randint(100000, 999999)
                    file_name = f"file_{r}.png"
                    image_file_light = ContentFile(file.read(), name=file_name)
                    url = AwsS3.upload_file(image_file_light, f'message_attachment/{user_zalo.user_zalo_id}/')
                    attachment['payload']['elements'].append({
                        "media_type": "image",
                        "url": url
                    })
                    # message_url.append({
                    #     "payload": {
                    #         "thumbnail": url,
                    #         "url": url
                    #     },
                    #     "type": "image"
                    # })
            
            if data.get('type_message') == Message.Type.FILE:
                # message_url = []
                attachment = {
                    "type": "file",
                    "payload": {
                        "token": data.get('attachment_token')
                    }
                }
                # message_url.append({
                #     "payload": {
                #         "thumbnail": url,
                #         "url": url
                #     },
                #     "type": "image"
                # })

            if data.get('type_message') == Message.Type.STICKER:
                # message_url = []
                attachment = {
                    "type": "template",
                    "payload": {
                        "template_type": "media",
                        "elements": [{
                            "media_type": "sticker",
                            "attachment_id": data.get('attachment_id')
                        }]
                    }
                }
                # message_url.append({
                #     "payload": {
                #         "url": data.get('attachment_url'),
                #         "id": data.get('attachment_id')
                #     },
                #     "type": "sticker"
                # })

            res = send_message_text(oa, user_zalo_id, {
                'text': data.get('message'),
                'quote_message_id': data.get('quote_message_id'),
                'attachment': attachment
            })
            print(res)
            # if res['error'] == 0:
            #     Message.objects.create(
            #         src=Message.Src.OA,
            #         type_message=data.get('type_message'),
            #         type_send=data.get('type_send'),
            #         message_text=data.get('message'),
            #         message_url=json.dumps(message_url),
            #         from_id=oa.uid_zalo_oa,
            #         to_id=user_zalo.user_zalo_id,
            #         success=True,
            #         send_by=user,
            #         oa=oa,
            #         send_at=int(datetime.now().timestamp() * 1000),
            #     )

            return convert_response('success', 200)
        except Exception as e:
            return convert_response(str(e), 400)


class MessageListApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        data = request.GET.copy()
        
        page_size = int(data.get('page_size', 20))
        offset = (int(data.get('page', 1)) - 1) * page_size
        messages = Message.objects.filter(Q(from_id=pk) | Q(to_id=pk))
        total = messages.count()
        messages = messages.order_by('-id')[offset: offset + page_size].values()

        return convert_response('success', 200, data=messages, total=total)

class MessageFileListApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        data = request.GET.copy()
        
        page_size = int(data.get('page_size', 20))
        offset = (int(data.get('page', 1)) - 1) * page_size
        
        messages = Message.objects.filter(Q(from_id=pk) | Q(to_id=pk)).order_by('-id').filter(
            type_message=Message.Type.PHOTO
        )[offset: offset + page_size].values()

        return convert_response('success', 200, data=messages)


class MessageFileUploadApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = json.loads(request.POST.get('data'))
        oa = ZaloOA.objects.get(uid_zalo_oa=data.get('oa_uid'))
        file = request.FILES.get('file', None)
        url = "https://openapi.zalo.me/v2.0/oa/upload/file"
        payload = {}
        files = {
            'file': (file.name, file, file.content_type)
        }
        headers = {
            'access_token': oa.access_token
        }
        response = requests.request("POST", url, headers=headers, data=payload, files=files)
        response = response.json()
        print(response)
        return convert_response('success', 200, data={
            'uuid': data.get('uuid'),
            'token': response.get('data').get('token')
        })


class MessageStickerApi(APIView):
    permission_classes = [AllowAny]

    def get(self, _):
        url = "https://stickers.zaloapp.com/sticker"
        payload = {}
        headers = {}
        res = requests.request("GET", url, headers=headers, data=payload)

        return response.Response(status=status.HTTP_200_OK, data=res.json())


class MessageStickerDetailApi(APIView):
    permission_classes = [AllowAny]

    def get(self, _, pk):
        url = f"https://stickers.zaloapp.com/cate-stickers?cid={pk}"
        payload = {}
        headers = {}
        res = requests.request("GET", url, headers=headers, data=payload)

        return response.Response(status=status.HTTP_200_OK, data=res.json())
