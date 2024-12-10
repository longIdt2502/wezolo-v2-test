from django.db import models

from customer.models import Customer
from tags.models import Tag
from zalo.models import ZaloOA, UserZalo
from user.models import User


class Progress(models.Model):
    class Meta:
        verbose_name = 'Progress'
        db_table = 'progress'

    title = models.CharField(max_length=255, null=True, blank=True)
    oa = models.ForeignKey(ZaloOA, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, null=False, on_delete=models.CASCADE, related_name='user_create_progress')
    updated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='user_update_progress')


class ProgressTag(models.Model):
    class Meta:
        verbose_name = 'ProgressTag'
        db_table = 'progress_tag'

    class Type(models.TextChoices):
        BEGIN = 'BEGIN', 'Bắt đầu'
        MIDDLE = 'MIDDLE', 'Trung gian'
        END = 'END', 'Kết thúc'

    title = models.CharField(max_length=255, null=True, blank=True)
    color_text = models.CharField(max_length=255, null=False, blank=False, default='ffffff')
    color_fill = models.CharField(max_length=255, null=False, blank=False, default='ffffff')
    color_border = models.CharField(max_length=255, null=False, blank=False, default='ffffff')
    type = models.CharField(max_length=255, choices=Type.choices, null=True)
    progress = models.ForeignKey(Progress, null=False, on_delete=models.CASCADE)
    oa = models.ForeignKey(ZaloOA, null=True, on_delete=models.SET_NULL)
    order = models.IntegerField(default=1, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, null=False, on_delete=models.CASCADE, related_name='user_create_progress_tag')
    updated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='user_update_progress_tag')


class ProgressTagCustomer(models.Model):
    class Meta:
        verbose_name = 'ProgressTagCustomer'
        db_table = 'progress_tag_customer'

    customer = models.ForeignKey(Customer, null=False, on_delete=models.CASCADE)
    tag = models.ForeignKey(ProgressTag, null=False, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, null=False, on_delete=models.CASCADE,
                                   related_name='user_create_progress_tag_customer')
    updated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL,
                                   related_name='user_update_progress_tag_customer')


class ProgressTagCustomerHistory(models.Model):
    class Meta:
        verbose_name = 'ProgressTagCustomerHistory'
        db_table = 'progress_tag_customer_history'

    customer = models.ForeignKey(Customer, null=False, on_delete=models.CASCADE)
    tag = models.ForeignKey(ProgressTag, null=False, on_delete=models.CASCADE)
    actor = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    action_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(null=True)


class ProgressTagUserZalo(models.Model):
    class Meta:
        verbose_name = 'ProgressTagUserZalo'
        db_table = 'progress_tag_user_zalo'

    user_zalo = models.ForeignKey(UserZalo, null=False, on_delete=models.CASCADE)
    tag = models.ForeignKey(ProgressTag, null=False, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, null=False, on_delete=models.CASCADE,
                                   related_name='user_create_progress_tag_user_zalo')
    updated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL,
                                   related_name='user_update_progress_tag_user_zalo')


class ProgressTagUserZaloHistory(models.Model):
    class Meta:
        verbose_name = 'ProgressTagUserZaloHistory'
        db_table = 'progress_tag_user_zalo_history'

    user_zalo = models.ForeignKey(UserZalo, null=False, on_delete=models.CASCADE)
    tag = models.ForeignKey(ProgressTag, null=False, on_delete=models.CASCADE)
    actor = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    action_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(null=True)

















