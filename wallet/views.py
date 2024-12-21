import uuid
from datetime import timedelta, datetime

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Sum
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from package.models import Price
from utils.convert_response import convert_response
from common.pay_os.pay_os_init import payOS
from payos import PaymentData, ItemData

from .models import Wallet, WalletTransaction
from reward.models import Reward, RewardBenefit


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
        type_payment = data.get('type')
        cancelUrl = data.get('cancelUrl')
        returnUrl = data.get('returnUrl')
        if not cancelUrl or not returnUrl:
            return convert_response('Yêu cầu cancelUrl và returnUrl', 400)
        wallet_trans = WalletTransaction.objects.create(
            amount=amount,
            total_amount=amount,
            method=WalletTransaction.Method.TRANSFER,
            type=WalletTransaction.Type.DEPOSIT,
            wallet=wallet,
            user=wallet.owner,
        )
        description = 'Nạp vào tài khoản'
        if type_payment == WalletTransaction.Type.IN_PACKAGE:
            description = type_payment
        payment_data = PaymentData(
            orderCode=wallet_trans.id, amount=amount, description=description,
            items=[],
            cancelUrl=cancelUrl,
            returnUrl=returnUrl
        )

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
        wallet = Wallet.objects.get(owner=wallet_trans.user)
        # nếu hành động nạp tiền là để mua gói
        if data.get('description') == WalletTransaction.Type.IN_PACKAGE:
            reward_tier = wallet.owner.level
            if reward_tier:
                reward_benefit = RewardBenefit.objects.filter(tier_id=reward_tier, type=Price.Type.START).first()
                if reward_benefit:
                    if reward_benefit.value.value != 0:
                        wallet_trans = WalletTransaction.objects.create(
                            amount=reward_benefit.value.value,
                            total_amount=reward_benefit.value.value,
                            method=WalletTransaction.Method.TRANSFER,
                            type=WalletTransaction.Type.OUT_START,
                            wallet=wallet,
                            user=wallet.owner,
                        )
                        Reward.objects.create(
                            customer_id=wallet.owner,
                            event=wallet_trans,
                            points_earned=wallet.owner.package.points_reward,
                            expiration_date=datetime.now() + timedelta(days=90)
                        )
        else:
            Reward.objects.create(
                customer_id=wallet_trans.user,
                event=wallet_trans,
                points_earned=wallet_trans.total_amount,
                expiration_date=datetime.now() + timedelta(days=90)
            )
        # channel_layer = get_channel_layer()
        # async_to_sync(channel_layer.group_send)(
        #     f'wallet_{wallet.id}',
        #     {
        #         'type': 'message_handler',
        #         'wallet_trans_id': wallet_trans.id
        #     },
        # )
        return convert_response('success', 200)


class WalletTransApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = request.GET.copy()
        page_size = int(data.get('page_size', 20))
        offset = (int(data.get('page', 1)) - 1) * page_size

        wallet_tras = WalletTransaction.objects.filter(
            wallet__owner=user
        )

        type_trans = data.get('type')
        if type_trans:
            wallet_tras = wallet_tras.filter(type=type_trans)

        date_start = data.get('date_start')
        if date_start:
            date_start = datetime.strptime(date_start, '%d-%m-%Y')
            wallet_tras = wallet_tras.filter(created_at__gte=date_start)
        
        date_end = data.get('date_end')
        if date_end:
            date_end = datetime.strptime(date_end, '%d-%m-%Y')
            wallet_tras = wallet_tras.filter(created_at__lte=date_end)
        
        total = wallet_tras.count()

        types_in = [WalletTransaction.Type.DEPOSIT, WalletTransaction.Type.IN_MESSAGE, WalletTransaction.Type.IN_ZNS]
        total_in = wallet_tras.filter(type__in=types_in).values().annotate(
            total_money=Sum('total_amount')
        ).values('total_money').first()
        total_in = total_in['total_money'] if total_in else 0
        total_out = wallet_tras.exclude(type__in=types_in).values().annotate(
            total_money=Sum('total_amount')
        ).values('total_money').first()
        total_out = total_out['total_money'] if total_out else 0
        wallet_tras = wallet_tras.order_by('-id')[offset: offset + page_size].values()
        return convert_response('success', 200, data=wallet_tras, total=total, total_in=total_in, total_out=total_out)

    def post(self, request):
        pass
