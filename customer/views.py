from django.contrib.postgres.aggregates import ArrayAgg
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from django.db.models import OuterRef, F, Q

from common.core.subquery import *
from utils.convert_response import convert_response

from .models import Customer, CustomerUserZalo, ZaloOA
from user.models import User


class CustomerCreate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            data = request.data.copy()
            ws = data.get('workspace')
            if not ws:
                raise Exception('Yêu cầu thông tin workspace')
            oa = data.get('oa')
            phone = data.get('phone')
            customer = Customer.objects.filter(workspace_id=ws, phone=phone).first()
            if customer:
                customer_user_zalo = CustomerUserZalo.objects.filter(
                    customer=customer, oa_id=oa
                )
                if customer_user_zalo:
                    raise Exception('Khách hàng đã tồn tại trong Workspace và Zalo Oa')
                else:
                    CustomerUserZalo.objects.create(
                        customer=customer,
                        oa_id=oa,
                    )
                    return convert_response('success', 200, data=customer.id)

            customer = Customer.objects.create(
                phone=phone,
                prefix_name=data.get('prefix_name'),
                email=data.get('email'),
                address=data.get('address'),
                gender=data.get('gender'),
                note=data.get('note'),
                workspace_id=ws,
                created_by=user,
            )
            CustomerUserZalo.objects.create(
                customer=customer,
                oa_id=oa,
            )
            return convert_response('success', 200, data=customer.id)

        except Exception as e:
            return convert_response(str(e), 400)


class CustomerList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = request.GET.copy()
        ws = data.get('workspace')
        if not ws:
            raise Exception('Yêu cầu thông tin Workspace')
        customer = Customer.objects.filter(workspace_id=ws)

        oa_id = data.get('oa')
        if oa_id:
            customer_user_zalo = CustomerUserZalo.objects.filter(oa_id=oa_id).values_list('customer_id', flat=True)
            customer = customer.filter(id__in=customer_user_zalo)

        gender = data.get('gender')
        if gender:
            customer = customer.filter(customer__gender=gender)

        oa_subquery = SubqueryJsonAgg(
            CustomerUserZalo.objects.filter(user_zalo__is_follower=True).exclude(oa_id=None).values().annotate(
                oa_name=F('oa__oa_name'),
                oa_avatar=F('oa__oa_avatar')
            )
        )

        oa_unfollow_subquery = SubqueryJsonAgg(
            CustomerUserZalo.objects.filter(user_zalo__is_follower=False).exclude(oa_id=None).values().annotate(
                oa_name=F('oa__oa_name'),
                oa_avatar=F('oa__oa_avatar')
            )
        )

        customer = customer.values().annotate(
            oa_follow=oa_subquery,
            oa_unfollow_subquery=oa_unfollow_subquery,
            created_user=SubqueryJson(
                User.objects.filter(id=OuterRef('created_by_id')).values(
                    'id', 'phone', 'full_name', 'avatar'
                )[:1]
            )
        )

        return convert_response('success', 200, data=customer)
