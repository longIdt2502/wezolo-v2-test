from django.db import models
from datetime import timedelta

from wallet.models import WalletTransaction
from django.utils import timezone

from user.models import User
from package.models import Price


class Reward(models.Model):
    class Meta:
        verbose_name = 'Reward'
        db_table = 'reward'

    customer_id = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    event = models.ForeignKey(WalletTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    points_earned = models.IntegerField(default=0, null=False, blank=False)
    expiration_date = models.DateTimeField(default=timezone.now() + timedelta(days=180))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField()


class RewardTier(models.Model):
    class Meta:
        verbose_name = 'RewardTier'
        db_table = 'reward_tier'

    class Name(models.TextChoices):
        SILVER = 'SILVER', 'Bạc'
        GOLD = 'GOLD', 'Vàng'
        PLATINUM = 'PLATINUM', 'Bạch kim'

    name = models.CharField(max_length=255, choices=Name.choices, null=True, blank=True)
    min_points = models.IntegerField(default=0, null=False, blank=False)
    benefit_description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def from_json(self, data):
        RewardTier.objects.create(
            name=data.get('name'),
            min_points=data.get('min_points'),
        )


class RewardBenefit(models.Model):
    class Meta:
        verbose_name = 'RewardBenefit'
        db_table = 'reward_benefit'

    tier_id = models.ForeignKey(RewardTier, on_delete=models.SET_NULL, null=True)
    benefit_name = models.TextField(null=False, blank=False)
    benefit_description = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=255, choices=Price.Type.choices, null=True, blank=True)
    value = models.IntegerField(default=0, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField()
