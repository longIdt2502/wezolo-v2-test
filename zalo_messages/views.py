from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import OuterRef, Q

from utils.convert_response import convert_response
from ws.event import send_message_to_ws
from common.core.subquery import *

from zalo.models import UserZalo, ZaloOA
from zalo_messages.models import Message
from tags.models import TagUserZalo


class MessageApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = request.GET.copy()

        page_size = int(data.get('page_size', 20))
        offset = (int(data.get('page', 1)) - 1) * page_size

        zalo_oa_id = data.get('oa')
        if not zalo_oa_id:
            return convert_response('Yêu cầu truyền OA', 400)
        oa = ZaloOA.objects.filter(uid_zalo_oa=zalo_oa_id).first()
        if not oa:
            return convert_response('Oa không tồn tại', 400)
        user = UserZalo.objects.filter(oa=oa)
        total = user.count()

        tags_subquery = SubqueryJsonAgg(
            TagUserZalo.objects.filter(user_zalo_id=OuterRef('id')).values()
        )

        last_message_subquery = SubqueryJson(
            Message.objects.filter(Q(from_id=OuterRef('user_zalo_id')) | Q(to_id=OuterRef('user_zalo_id')))[:1]
        )

        search = data.get('search')
        if search:
            user = user.filter(Q(name__icontains=search) | Q(phone__icontains=search))

        tags = data.get('tags')
        if tags:
            tags = tags.split(',')
            tags_query = TagUserZalo.objects.filter(id__in=tags)
            user_id_in_tags = tags_query.values_list('user_zalo_id', flat=True)
            user = user.filter(id__in=user_id_in_tags)
        
        user = user[offset: offset + page_size].values().annotate(
            tags=tags_subquery,
            last_message=last_message_subquery,
        )
        return convert_response('success', 200, data=user, total=total)

    def post(self, request):
        try:
            user = request.user
            data = request.data.copy()

            oa = ZaloOA.objects.get(id=data.get('oa'))
            user_zalo = UserZalo.objects.get(user_zalo_id=data.get('user_zalo_id'))

            send_message_to_ws(f'message_{user_zalo.user_zalo_id}', 'message_handler', {})

            Message.objects.create(
                src=Message.Src.OA,
                type_message=data.get('type_message'),
                type_send=data.get('type_send'),
                message_text=data.get('message_text'),
                from_id=oa.uid_zalo_oa,
                to_id=user_zalo.user_zalo_id,
                success=True,
                send_by=user,
                oa=oa
            )

            return convert_response('success', 200)
        except Exception as e:
            return convert_response(str(e), 400)
