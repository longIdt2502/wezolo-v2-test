import hashlib
import hmac
import json
import os

from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from common.zalo.event_name import ZaloEventName
from utils.convert_response import convert_response
from zalo.hook.event import *


class ZaloHook(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Lấy thông tin từ headers
        signature = request.headers.get('X-ZEvent-Signature')
        timestamp = request.headers.get('timeStamp')

        # Lấy nội dung data từ request body
        data = json.dumps(request.data)

        # Xác thực chữ ký
        app_id = os.environ.get('ZALO_APP_ID')
        oa_secret_key = os.environ.get('ZALO_APP_SECRET')

        mac = hmac.new(
            key=oa_secret_key.encode('utf-8'),
            msg=f'{app_id}{data}{timestamp}'.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()

        if signature != mac:
            return convert_response('Invalid Signature', 403)

        # Xử lý logic khi nhận được sự kiện
        event_type = request.data.get('event_name')
        user_id = request.data.get('follower').get('id')
        uid_zalo_oa = request.data.get('oa_id')

        if event_type == ZaloEventName.follow or event_type == ZaloEventName.un_follow:
            is_follow = True if event_type == ZaloEventName.follow else False
            handle_follow_event(is_follow)

        return convert_response('success', 200)
