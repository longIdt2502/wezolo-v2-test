from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from wallet.models import Wallet, WalletTransaction
from user.models import User
from reward.models import RewardBenefit, Price, RewardTier, Reward
from package.models import Package


def CheckFinancialCapacity(user: User):
    current_time = timezone.now()
    future_time = current_time + timedelta(days=30)
    rewards = Reward.objects.filter(customer_id=user)
    total_point = rewards.aggregate(
        total_point=Sum('points_earned')
    )['total_point'] or 0
    pass
