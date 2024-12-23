from asgiref.sync import async_to_sync
from django.db import models
from django.utils import timezone
from django.db.models import F

from channels.layers import get_channel_layer

from user.models import User, Address
from wallet.service.create_trans_wallet_thirdparty import create_transaction_third_party
from ws.event import send_message_to_ws
from zalo.models import ZaloOA


class Wallet(models.Model):
    class Meta:
        verbose_name = 'Wallet'
        db_table = 'wallet'

    wallet_uid = models.UUIDField(null=False, blank=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    balance = models.IntegerField(default=0, null=False, blank=False)
    private_key = models.TextField(null=False, blank=False)
    wallet_authorization = models.TextField(null=True, blank=True)

    def to_json(self):
        return {
            "id": self.id,
            "wallet_uid": str(self.wallet_uid),
            "balance": self.balance,
            "owner": {
                "id": self.owner.id,
                "phone": self.owner.phone,
                "full_name": self.owner.full_name,
                "avatar": self.owner.avatar,
            },
            "wallet_authorization": self.wallet_authorization,
        }

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'wallet_{self.id}',
            {
                'type': 'message_handler',
                'message': {}
            },
        )


class WalletTransaction(models.Model):
    class Meta:
        verbose_name = 'WalletTransaction'
        db_table = 'wallet_transaction'

    class Type(models.TextChoices):
        DEPOSIT = 'DEPOSIT', 'Nạp tiền'
        IN_PACKAGE = 'IN_PACKAGE', 'Mua gói'
        OUT_ZNS = 'OUT_ZNS', 'Gửi tin zns'
        OUT_MESS = 'OUT_MESS', 'Gửi tin vượt khung'
        OUT_START = 'OUT_START', 'Khởi tạo'
        OUT_CREATE_OA = 'OUT_CREATE_OA', 'Tạo zalo OA'
        OUT_CONECT_OA = 'OUT_CONECT_OA', 'Kết nối zalo OA'
        OUT_CREATE_WS = 'OUT_CREATE_WS', 'Tạo wordspace'
        OUT_OA_PREMIUM = 'OUT_OA_PREMIUM', 'Nâng cấp OA premium'
        IN_ZNS = 'IN_ZNS', 'Hoàn tiền zns'
        IN_MESSAGE = 'IN_MESSAGE', 'Hoàn tiền tin nhắn'

    class Method(models.TextChoices):
        CASH = 'CASH', 'tiền mặt'
        TRANSFER = 'TRANSFER', 'chuyển khoản'

    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    type = models.CharField(max_length=255, choices=Type.choices, default=Type.DEPOSIT, null=False, blank=False)
    method = models.CharField(max_length=255, choices=Method.choices, default=Method.CASH, null=False, blank=False)
    pay_os_reference = models.CharField(max_length=255, null=True, blank=True)
    # TODO: voucher
    oa = models.ForeignKey(ZaloOA, on_delete=models.SET_NULL, null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    amount = models.IntegerField(default=0, null=False, blank=False)
    bonus_amount = models.IntegerField(default=0, null=False, blank=False)
    total_amount = models.IntegerField(default=0, null=False, blank=False)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # Check if the object is being created
        is_new = self.pk is None

        if is_new:
            # Lấy giá trị thực của balance từ cơ sở dữ liệu
            self.wallet.refresh_from_db()
            current_balance = self.wallet.balance

            if self.type in [
                self.Type.OUT_ZNS, self.Type.OUT_MESS, self.Type.OUT_START,
                self.Type.OUT_CREATE_OA, self.Type.OUT_CONECT_OA, self.Type.OUT_CREATE_WS, self.Type.OUT_OA_PREMIUM,
            ]:
                if current_balance < self.amount:
                    raise ValueError("Insufficient wallet balance")
                self.wallet.balance = F('balance') - self.amount
            if self.type in [self.Type.IN_PACKAGE, self.Type.IN_MESSAGE, self.Type.IN_ZNS]:
                self.wallet.balance = F('balance') + self.amount
            create_transaction_third_party(self, None)
            self.wallet.save()

        # Save transaction
        super().save(*args, **kwargs)
        if is_new and self.type in [
            self.Type.IN_PACKAGE, self.Type.OUT_ZNS, self.Type.OUT_MESS, self.Type.OUT_START,
            self.Type.OUT_CREATE_OA, self.Type.OUT_CONECT_OA, self.Type.OUT_CREATE_WS, self.Type.OUT_OA_PREMIUM,
            self.Type.IN_MESSAGE, self.Type.IN_ZNS
        ]:
            send_message_to_ws(f'wallet_{self.wallet.id}', 'message_handler', {
                'trans_id': self.pk,  # Now `self.pk` is valid
            })
        # Nếu là nạp tiền thì check xem -> giao dịch này đã nạp tiền thành công hay chưa dựa vào pay_os_reference
        if self.type == self.Type.DEPOSIT and self.pay_os_reference is not None:
            self.wallet.balance = F('balance') + self.amount
            self.wallet.save()
            send_message_to_ws(f'wallet_{self.wallet.id}', 'message_handler', {
                'trans_id': self.pk,
            })
            create_transaction_third_party(self, None)

    def to_json(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'type': self.type,
            'method': self.method,
            'amount': self.amount,
            'bonus_amount': self.bonus_amount,
            'total_amount': self.total_amount,
            'created_at': self.created_at.isoformat(),
        }


class WalletInvoice(models.Model):
    class Meta:
        verbose_name = 'WalletInvoice'
        db_table = 'wallet_invoice'

    transaction = models.ForeignKey(WalletTransaction, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=False, blank=False, default='')
    tax_number = models.CharField(max_length=255, null=False, blank=False, default='')
    email = models.CharField(max_length=255, null=True, blank=True)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)