from django.db import models

from user.models import User
from workspace.models import Workspace, Role
from zalo.models import ZaloOA, UserZalo


class Employee(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Đang hoạt động'
        INACTIVE = 'INACTIVE', 'Tạm nghỉ'
        TERMINATED = 'TERMINATED', 'Nghỉ việc'

    account = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, null=False, blank=False)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=255, choices=Status.choices, default=Status.ACTIVE, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='user_create_employee')
    updated_at = models.DateTimeField(null=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='user_update_employee')


class EmployeeUserZalo(models.Model):
    class Meta:
        verbose_name = 'EmployeeUserZalo'
        db_table = 'employee_userzalo'

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=False)
    customer = models.ForeignKey(UserZalo, on_delete=models.CASCADE, null=False)


class EmployeeOa(models.Model):
    class Meta:
        verbose_name = 'EmployeeOa'
        db_table = 'employee_oa'

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=False)
    oa = models.ForeignKey(ZaloOA, on_delete=models.CASCADE, null=False)
