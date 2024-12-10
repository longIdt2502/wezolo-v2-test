from django.db import models

from zalo.models import ZaloOA, UserZalo
from user.models import User
from customer.models import Customer


class Tag(models.Model):
    title = models.CharField(max_length=20, null=True, blank=True)
    color_text = models.CharField(max_length=255, null=False, blank=False, default='ffffff')
    color_fill = models.CharField(max_length=255, null=False, blank=False, default='ffffff')
    color_border = models.CharField(max_length=255, null=False, blank=False, default='ffffff')
    oa = models.ForeignKey(ZaloOA, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, null=False, on_delete=models.CASCADE, related_name='user_created_tag')
    updated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='user_updated_tag')

    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "color_text": self.color_text,
            "color_fill": self.color_fill,
            "color_border": self.color_border,
            "oa": self.oa.to_json(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by.full_name,
            "updated_by": self.updated_by.full_name if self.updated_by else None,
        }


class TagCustomer(models.Model):
    class Meta:
        verbose_name = 'TagCustomer'
        db_table = 'tag_customer'

    customer = models.ForeignKey(Customer, null=False, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, null=False, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, null=False, on_delete=models.CASCADE, related_name='user_created_tag_customer')
    updated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='user_updated_tag_customer')


class TagCustomerHistory(models.Model):
    class Meta:
        verbose_name = 'TagCustomerHistory'
        db_table = 'tag_customer_history'

    class Type(models.TextChoices):
        GAN_TAG = 'GAN_TAG', 'Gán Tag'
        GO_TAG = 'GO_TAG', 'Gỡ Tag'
    customer = models.ForeignKey(Customer, null=False, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, null=False, on_delete=models.CASCADE)
    actor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action_at = models.DateTimeField(auto_now_add=True)
    type_action = models.CharField(max_length=255, choices=Type.choices, null=True, blank=True)


class TagUserZalo(models.Model):
    class Meta:
        verbose_name = 'TagUserZalo'
        db_table = 'tag_user_zalo'

    user_zalo = models.ForeignKey(UserZalo, null=False, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, null=False, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, null=False, on_delete=models.CASCADE, related_name='user_created_tag_user_zalo')
    updated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='user_updated_tag_user_zalo')


class TagUserZaloHistory(models.Model):
    class Meta:
        verbose_name = 'TagUserZaloHistory'
        db_table = 'tag_user_zalo_history'

    class Type(models.TextChoices):
        GAN_TAG = 'GAN_TAG', 'Gán Tag'
        GO_TAG = 'GO_TAG', 'Gỡ Tag'
    user_zalo = models.ForeignKey(UserZalo, null=False, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, null=False, on_delete=models.CASCADE)
    actor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action_at = models.DateTimeField(auto_now_add=True)
    type_action = models.CharField(max_length=255, choices=Type.choices, null=True, blank=True)
