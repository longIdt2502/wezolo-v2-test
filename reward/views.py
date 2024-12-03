from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Sum, OuterRef
from utils.convert_response import convert_response
from common.core.subquery import SubqueryJson
from datetime import timedelta
from django.utils import timezone

from .models import Reward, RewardTier
from wallet.models import WalletTransaction


class RewardsApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = request.GET.copy()
        page_size = int(data.get('page_size', 20))
        offset = (int(data.get('page', 1)) - 1) * page_size

        rewards = Reward.objects.filter(customer_id=user)
        total_point = rewards.aggregate(
            total_point=Sum('points_earned')
        )['total_point'] or 0

        detail = rewards[
            offset: offset + page_size
        ].values().annotate(
            event_data=SubqueryJson(
                WalletTransaction.objects.filter(id=OuterRef('event')).values()[:1]
            )
        )

        point_to_next_level = 0
        reward_next_level = RewardTier.objects.filter(min_points__gte=total_point).first()
        if reward_next_level:
            point_to_next_level = reward_next_level.min_points - total_point

        current_time = timezone.now()
        future_time = current_time + timedelta(days=30)
        point_near_expiry = rewards.filter(expiration_date__gte=current_time, expiration_date__lt=future_time).aggregate(
            total_point=Sum('points_earned')
        )['total_point'] or 0
        return convert_response('success', 200, data=detail,
                                total=total_point, point_to_next_level=point_to_next_level,
                                point_near_expiry=point_near_expiry)

    def post(self, request):
        user = request.user
        data = request.data.copy()
        pass


class RewardsTierApi(APIView):
    permission_classes = [AllowAny]

    def get(self, _):
        rewards_tier = RewardTier.objects.filter().values()
        return convert_response('success', 200, data=rewards_tier)
