import hashlib
import hmac
import json
import os
import django_rq

from django.db.models import Q
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from common.redis.connect_oa_job import detail_customer_oa_job

from common.zalo.event_name import ZaloEventName
from utils.convert_response import convert_response
from zalo.hook.event import *


class ZaloHook(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            sender_id = None
            recipient_id = None
            sender = data.get('sender')
            if sender:
                sender_id = sender.get('id')
            recipient = data.get('recipient')
            if recipient:
                recipient_id = recipient.get('id')
            if sender_id or recipient_id:
                user_zalo = UserZalo.objects.filter(
                    Q(user_zalo_id=sender_id) | 
                    Q(user_zalo_id=recipient_id)
                ).first()
                oa = ZaloOA.objects.filter(
                    Q(uid_zalo_oa=sender_id) | 
                    Q(uid_zalo_oa=recipient_id)
                ).first()
                if not user_zalo and oa:
                    django_rq.enqueue(detail_customer_oa_job, oa.access_token, sender_id, oa.id)
                    django_rq.enqueue(detail_customer_oa_job, oa.access_token, recipient_id, oa.id)

            event_type = request.data.get('event_name')
            if event_type == ZaloEventName.follow or event_type == ZaloEventName.un_follow:
                handle_follow_event(data)
            if event_type == ZaloEventName.user_submit_info:
                handle_user_submit_info(data)
            if event_type == ZaloEventName.change_template_status:
                handle_change_template_status(data)
            if event_type == ZaloEventName.user_seen_message:
                handle_seen_message(data)
            if event_type == ZaloEventName.user_received_message:
                handle_user_received_message(data)
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
                handle_message_hook(data)
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
                handle_message_oa_send_hook(data)


            return convert_response('success', 200)
        except Exception as e:
            print(str(e))
            return convert_response('fail', 400)
