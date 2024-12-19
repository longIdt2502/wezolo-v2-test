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
        try:
            # print('---start')
            # signature = request.headers.get('X-ZEvent-Signature')
            # timestamp = request.data.get('timestamp')
            # print(timestamp)
            # data = json.dumps(request.data)
            # print(data)
            # app_id = os.environ.get('ZALO_APP_ID')
            # oa_secret_key = os.environ.get('OA_SECRET_KEY')
            # print(app_id)
            # print(oa_secret_key)
            # mac = hmac.new(
            #     key=oa_secret_key.encode('utf-8'),
            #     msg=f'{app_id}{request.data}{timestamp}{oa_secret_key}'.encode('utf-8'),
            #     digestmod=hashlib.sha256
            # ).hexdigest()
            # print(mac)
            # print(signature)
            #
            # if signature != mac:
            #     return convert_response('Invalid Signature', 403)

            event_type = request.data.get('event_name')
            if event_type == ZaloEventName.follow or event_type == ZaloEventName.un_follow:
                handle_follow_event(request.data.copy())
            if event_type == ZaloEventName.user_submit_info:
                handle_user_submit_info(request.data.copy())
            if event_type == ZaloEventName.user_submit_info:
                handle_user_submit_info(request.data.copy())
            if event_type == ZaloEventName.change_template_status:
                handle_change_template_status(request.data.copy())
            if event_type == ZaloEventName.user_seen_message:
                handle_seen_message(request.data.copy())
            if event_type in [
                ZaloEventName.user_send_audio,
                ZaloEventName.user_send_business_card,
                ZaloEventName.user_send_file,
                ZaloEventName.user_send_gif,
                ZaloEventName.user_send_location,
                ZaloEventName.user_send_image,
                ZaloEventName.user_send_link,
                ZaloEventName.user_send_sticker,
                ZaloEventName.user_send_video,
                ZaloEventName.user_send_text,
            ] :
                handle_message_hook(request.data.copy())
            if event_type in [
                ZaloEventName.oa_send_audio,
                ZaloEventName.oa_send_business_card,
                ZaloEventName.oa_send_file,
                ZaloEventName.oa_send_gif,
                ZaloEventName.oa_send_location,
                ZaloEventName.oa_send_image,
                ZaloEventName.oa_send_link,
                ZaloEventName.oa_send_sticker,
                ZaloEventName.oa_send_video,
                ZaloEventName.oa_send_text,
            ] :
                handle_message_oa_send_hook(request.data.copy())


            return convert_response('success', 200)
        except Exception as e:
            print(str(e))
            return convert_response('fail', 400)
