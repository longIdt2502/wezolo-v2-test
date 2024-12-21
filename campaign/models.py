from django.db import models
import django_rq
from common.redis.send_message_campain_job import send_message_campain_job, send_zns_campain_job

from customer.models import Customer
from user.models import User
from wallet.models import WalletTransaction
from zalo.models import Message, UserZalo, ZaloOA
from zns.models import Zns, ZnsSent


class Campaign(models.Model):
    class Meta:
        verbose_name = 'Campaign'
        db_table = 'campaign'
        ordering = ['-created_at']

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Nháp'
        PENDING = 'PENDING', 'Chờ thực hiện'
        IN_PROGRESS = 'IN_PROGRESS', 'Đang diễn ra'
        REJECT = 'REJECT', 'Đã hủy'
        DONE = 'DONE', 'Hoàn thành'
        REFUND = 'REFUND', 'Hoàn thành, đã hoàn trả'
    
    class Type(models.TextChoices):
        MESSAGE = 'MESSAGE', 'Tin nhắn thường'
        ZNS = 'ZNS', 'Tin nhắn ZNS'

    name = models.CharField(max_length=255, null=True, blank=True)
    oa = models.ForeignKey(ZaloOA, on_delete=models.CASCADE)
    status = models.CharField(max_length=255, choices=Status.choices, default=Status.DRAFT)
    type = models.CharField(max_length=255, choices=Type.choices, null=True, blank=True)
    start_sent_at = models.DateTimeField(null=True, blank=True)
    zns = models.ForeignKey(Zns, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(max_length=2000, null=True, blank=True)
    message_file = models.JSONField(null=True, blank=True)
    price_zns = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    total_sent = models.IntegerField(default=0)
    total_success = models.IntegerField(null=True, blank=True)
    total_amount = models.IntegerField(null=True, blank=True)
    total_refund = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_campaigns')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_campaigns')

    def __str__(self):
        return self.name or f"Campaign {self.id}"

    def from_json(self, data):
        campaign = Campaign.objects.create(
            name=data.get('name'),
            oa_id=data.get('oa'),
            status=data.get('status'),
            type=data.get('type'),
            start_sent_at=data.get('start_sent_at'),
            zns_id=data.get('zns_id'),
            message=data.get('message'),
            message_file=data.get('message_file'),
            total_amount=data.get('price_zns', 0),
            price_zns=data.get('price_zns', 0),
            total=data.get('total', 0),
            created_by_id=data.get('created_by'),
        )
        return campaign
    
    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "oa_id": self.oa.id,
            "status": self.status,
            "type": self.type,
            "start_sent_at": self.start_sent_at.isoformat() if self.start_sent_at else None,
            "zns_id": self.zns.id if self.zns else None,
            "message": self.message,
            "message_file": self.message_file,
            "price_zns": self.price_zns,
            "total": self.total,
            "total_sent": self.total_sent,
            "total_success": self.total_success,
            "total_amount": self.total_amount,
            "total_refund": self.total_refund,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by_name": self.created_by.full_name if self.created_by else None,
            "updated_by_name": self.updated_by.full_name if self.updated_by else None,
        }
        

class StatusMessage(models.TextChoices):
        SENT = 'SENT', 'Đã gửi'
        PENDING = 'PENDING', 'Chờ thực hiện'
        REJECT = 'REJECT', 'Đã hủy'


class CampaignMessage(models.Model):
    class Meta:
        verbose_name = 'CampaignMessage'
        db_table = 'campaign_message'
        ordering = ['-created_at']

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True)
    user_zalo = models.ForeignKey(UserZalo, on_delete=models.CASCADE)
    status = models.CharField(max_length=255, choices=StatusMessage.choices, default=StatusMessage.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
        

class CampaignZns(models.Model):
    class Meta:
        verbose_name = 'CampaignZns'
        db_table = 'campaign_zns'
        ordering = ['-created_at']

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    zns = models.ForeignKey(Zns, on_delete=models.SET_NULL, null=True)
    zns_params = models.JSONField(null=True)
    zns_sent = models.ForeignKey(ZnsSent, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=255, choices=StatusMessage.choices, default=StatusMessage.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    response_json = models.JSONField(null=True)
    is_refund = models.BooleanField(default=False)

