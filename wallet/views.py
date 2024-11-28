import uuid

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from utils.convert_response import convert_response
from common.pay_os.pay_os_init import payOS
from payos import PaymentData, ItemData

from .models import Wallet, WalletTransaction
from reward.models import Reward


class WalletView(APIView):
    def get(self, request):
        pass


class WalletDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        wallet = Wallet.objects.filter(wallet_uid=pk, owner=user).first()
        if not wallet:
            return convert_response('Ví không tồn tại', 404)
        return convert_response('success', 200, data=wallet.to_json())
        pass

    def delete(self, request):
        pass


class WalletPayment(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data.copy()
        amount = data.get('amount', 0)
        wallet = Wallet.objects.filter(owner=user).first()
        if not wallet:
            return convert_response('Ví không khả dụng với người dùng', 400)
        wallet_trans = WalletTransaction.objects.create(
            amount=amount,
            total_amount=amount,
            method=WalletTransaction.Method.TRANSFER,
            type=WalletTransaction.Type.DEPOSIT,
            wallet=wallet,
            user=wallet.owner,
        )
        description = 'Nạp vào tài khoản'
        payment_data = PaymentData(orderCode=wallet_trans.id, amount=amount, description=description,
                                   items=[],
                                   cancelUrl="http://localhost:8000",
                                   returnUrl="http://localhost:8000")

        payment_link_data = payOS.createPaymentLink(paymentData=payment_data)
        return convert_response('success', 200, data=payment_link_data.to_json())


class WalletReceiveHookPayment(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        body = request.data.copy()
        is_success = body.get('success', False)
        if not is_success:
            return convert_response('unsuccessfully', 400)
        data = body.get('data')
        wallet_trans = WalletTransaction.objects.filter(id=data.get('orderCode')).first()
        if not wallet_trans:
            return convert_response('wallet not found', 400)
        wallet_trans.pay_os_reference = data.get('reference')
        wallet_trans.save()
        Reward.objects.create(
            customer_id=wallet_trans.user,
            event=wallet_trans,
            points_earned=wallet_trans.total_amount,
        )
        wallet = Wallet.objects.get(owner=wallet_trans.user)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'wallet_{wallet.id}',
            {
                'type': 'message_handler',
                'wallet_trans_id': wallet_trans.id
            },
        )
        return convert_response('success', 200)


class WalletTransApi(APIView):
    def post(self, request):
        pass
