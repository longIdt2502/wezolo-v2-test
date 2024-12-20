from datetime import timedelta
from typing import Tuple

from django.db.models import Sum
from django.utils import timezone

from wallet.models import Wallet, WalletTransaction
from user.models import User
from reward.models import RewardBenefit, Price, RewardTier, Reward
from package.models import Package, Price


def checkFinancialCapacity(user: User, type_check: Price.Type) -> Tuple[bool, Wallet, RewardBenefit]:
    try:
        # rewards = Reward.objects.filter(customer_id=user, expiration_date__lte=timezone.now() - timedelta(days=180))
        # total_point = rewards.aggregate(
        #     total_point=Sum('points_earned')
        # )['total_point'] or 0
        # reward_tier = RewardTier.objects.filter(min_points__lte=total_point).order_by('-min_points__lte').first()
        # user.level = reward_tier
        # user.save()

        wallet = Wallet.objects.get(owner=user)
        benefit = RewardBenefit.objects.filter(tier_id=user.level, type=type_check).exclude(value__value=0).first()
        if not benefit:
            raise Exception('Không tìm thấy lợi ích giá phù hợp')
        return wallet.balance >= benefit.value.value, wallet, benefit
    except Exception as e:
        return False, Wallet(), RewardBenefit()
