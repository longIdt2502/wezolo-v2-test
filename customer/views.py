from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from utils.convert_response import convert_response

from .models import Customer, CustomerUserZalo


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
