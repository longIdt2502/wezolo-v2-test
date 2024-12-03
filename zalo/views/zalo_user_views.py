from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.db.models import OuterRef, Q

from common.core.subquery import *
from utils.convert_response import convert_response
from zalo.models import UserZalo
from employee.models import EmployeeUserZalo, ZaloOA
from user.models import User


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

        oa_id = data.get('oa_id')
        total_user = UserZalo.objects.filter(oa_id=oa_id).count()
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'oa_{str(oa_id)}',
            {
                'type': 'message_handler',
                'message': {
                    'sync_done': total_user,
                }
            },
        )
        return convert_response('success', 200, data=user_zalo.id)


class ZaloUserList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            data = request.GET.copy()
            page_size = int(data.get('page_size', 20))
            offset = (int(data.get('page', 1)) - 1) * page_size
            oa = data.get('oa')
            if not oa:
                raise Exception('thiếu thông tin Oa')
            customers = UserZalo.objects.filter(oa_id=oa)
            total = customers.count()

            is_follow = data.get('is_follow')
            if is_follow:
                is_follow = True if is_follow == 'true' else False
                customers = customers.filter(is_follower=is_follow)

            search = data.get('search')
            if search:
                customers = customers.filter(Q(name__icontains=search), Q(phone__icontains=search))

            user_subquery = SubqueryJson(
                User.objects.filter(id=OuterRef('employee__account_id')).values(
                    'phone', 'full_name', 'avatar', 'email'
                )
            )

            employee_subquery = SubqueryJsonAgg(
                EmployeeUserZalo.objects.filter(customer_id=OuterRef('id')).values().annotate(
                    user=user_subquery
                )
            )

            customers = customers.values()[offset: offset + page_size].annotate(
                employee=employee_subquery
            )
            return convert_response('success', 200, data={
                "data": customers,
                "total": total
            })
        except Exception as e:
            return convert_response(str(e), 400)
