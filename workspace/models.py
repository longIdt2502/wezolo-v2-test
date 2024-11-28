from datetime import datetime
from django.apps import apps
from django.db import models
import random
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.files.base import ContentFile

from common.s3 import AwsS3

from user.models import User, Address


class WorkspaceStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Đang hoạt động'
    INACTIVE = 'INACTIVE', 'Dừng hoạt động'


# Create your models here.
class Workspace(models.Model):
    class Meta:
        verbose_name = 'Workspace'
        db_table = 'workspace'

    name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    address = models.ForeignKey(Address, null=True, on_delete=models.SET_NULL)
    status = models.CharField(choices=WorkspaceStatus.choices, default=WorkspaceStatus.ACTIVE, max_length=255)
    dev_note = models.CharField(max_length=100, null=True, blank=True)
    tax_number = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(_('email address'), null=True, blank=True)
    image = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)

    def from_json(self, data):
        return Workspace.objects.create(
            name=data.get('name'),
            description=data.get('description'),
            dev_note=data.get('dev_note'),
            tax_number=data.get('tax_number'),
            email=data.get('email'),
            category=data.get('category'),
            created_by_id=data.get('created_by')
        )

    def update_from_json(self, data):
        ws = self
        ws.name = data.get('name', ws.name)
        ws.description = data.get('description', ws.description)
        ws.dev_note = data.get('dev_note', ws.dev_note)
        ws.tax_number = data.get('tax_number', ws.tax_number)
        ws.email = data.get('email', ws.email)
        ws.category = data.get('category', ws.category)
        ws.status = data.get('status', ws.status)
        ws.updated_at = datetime.now()
        ws.name = data.get('name', ws.name)
        ws.save()
        return ws

    def to_json(self):
        employee = apps.get_model('employee', 'Employee')
        total_employee = employee.objects.filter(workspace=self).count()
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "dev_note": self.dev_note,
            "tax_number": self.tax_number,
            "email": self.email,
            "total_employee": total_employee,
            "category": self.category,
            "address": self.address.to_json() if self.address else None,
            "image": self.image,
            "created_by_id": self.created_by_id
        }

    def save_image(self, file):
        r = random.randint(100000, 999999)
        file_name = f"{self.name}_{r}.png"
        image_file = ContentFile(file.read(), name=file_name)
        uploaded_file_name = AwsS3.upload_file(image_file, 'workspace/')
        self.image = uploaded_file_name
        self.save()
        return self


class WorkspaceCategory(models.Model):
    class Meta:
        verbose_name = 'WorkspaceCategory'
        db_table = 'workspace_category'

    code = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)


class Journey(models.Model):
    class JourneyStatus(models.TextChoices):
        START = 'START', 'bắt đầu'
        DECLARE = 'DECLARE', 'khai báo'
        CONFIRM = 'CONFIRM', 'xác nhận'
        LOW = 'LOW', 'không đủ tài khoản'
        ERR = 'ERR', 'lỗi hệ thống'
        SUCCESS = 'SUCCESS', 'thành công'

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=100, choices=JourneyStatus.choices, default=JourneyStatus.START, null=False, blank=False)
    name = models.CharField(max_length=255, null=True, blank=True)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(WorkspaceCategory, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    dev_note = models.CharField(max_length=100, null=True, blank=True)
    tax_number = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    image = models.TextField(null=True, blank=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)


class Role(models.Model):
    class Code(models.TextChoices):
        OWNER = 'OWNER', 'Chủ sở hữu'
        ADMIN = 'ADMIN', 'Quản lý workspace'
        ADMIN_OA = 'ADMIN_OA', 'Quản lý OA'
        SALE = 'SALE', 'Nhân viên sale'

    code = models.CharField(max_length=100, choices=Code.choices, null=True)
    title = models.CharField(max_length=100, null=False, blank=False)
    is_default = models.BooleanField(default=True, null=False)
    note = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='user_create_role')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='user_update_role')
    updated_at = models.DateTimeField(null=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True, null=False)

    def from_json(self, data):
        role = self
        role.code = data.get('code')
        role.title = data.get('title'),
        role.note = data.get('note'),
        role.save()


class Permission(models.Model):
    title = models.CharField(max_length=100, null=False, blank=False)
    code = models.CharField(max_length=100, null=False, blank=False)


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=False)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, null=False)