from django.db import models
from django.utils import timezone
from django.db.models import F

from user.models import User, Address
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
            "wallet_uid": self.wallet_uid,
            "balance": self.balance,
            "owner": {
                "id": self.owner.id,
                "phone": self.owner.phone,
                "full_name": self.owner.full_name,
                "avatar": self.owner.avatar,
            },
            "wallet_authorization": self.wallet_authorization,
        }


class WalletTransaction(models.Model):
    class Meta:
        verbose_name = 'WalletTransaction'
        db_table = 'wallet_transaction'

    class Type(models.TextChoices):
        DEPOSIT = 'DEPOSIT', 'nạp tiền'
        EXPENDITURE = 'EXPENDITURE', 'chi tiêu'
        RETURN = 'RETURN', 'trả lại'
        PACKAGE = 'PACKAGE', 'mua gói'

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

        # Save transaction
        super().save(*args, **kwargs)

        if is_new:
            if self.type == self.Type.DEPOSIT and self.pay_os_reference is None:
                self.wallet.balance = F('balance') + self.amount
            elif self.type == self.Type.RETURN or self.type == self.Type.EXPENDITURE or self.type == self.Type.PACKAGE:
                if self.wallet.balance < self.amount:
                    raise ValueError("Insufficient wallet balance")
                self.wallet.balance = F('balance') - self.amount

            self.wallet.save()

    def to_json(self):
        return {
            'transaction_id': self.transaction_id,
            'type': self.type,
            'method': self.method,
            'amount': self.amount,
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