from django.db import models

from user.models import Gender, User
from workspace.models import Workspace
from zalo.models import ZaloOA, UserZalo


class CustomerImport(models.Model):
    class Meta:
        verbose_name = 'CustomerImport'
        db_table = 'customer_import'

    class Status(models.TextChoices):
        IN_PROCESS = 'IN_PROCESS', 'Đang xử lý'
        SUCCESS = 'SUCCESS', 'Đã xử lý'
        ERROR = 'ERROR', 'Lỗi'
    file_url = models.CharField(max_length=100, null=True)
    file_name = models.CharField(max_length=255, null=True)
    customer_total = models.IntegerField(null=True)
    customer_success = models.IntegerField(null=True)
    customer_double = models.IntegerField(null=True)
    status = models.CharField(max_length=255, choices=Status.choices, default=Status.IN_PROCESS, null=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)


class Customer(models.Model):
    class Meta:
        verbose_name = 'Customer'
        db_table = 'customer'

    prefix_name = models.CharField(max_length=255, null=False, blank=False)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    gender = models.CharField(max_length=255, choices=Gender.choices, default=Gender.MALE, null=True, blank=True)
    birthday = models.DateField(null=True)
    source = models.IntegerField(null=True)
    note = models.TextField(null=True)
    file_import = models.ForeignKey(CustomerImport, on_delete=models.SET_NULL, null=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def to_json(self):
        return {
            "prefix_name": self.prefix_name,

        }


class CustomerUserZalo(models.Model):
    class Meta:
        verbose_name = 'CustomerUserZalo'
        db_table = 'customer_user_zalo'

    user_zalo = models.ForeignKey(UserZalo, on_delete=models.SET_NULL, null=True)
    oa = models.ForeignKey(ZaloOA, on_delete=models.SET_NULL, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
