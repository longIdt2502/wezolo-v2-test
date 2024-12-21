from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db.models import OuterRef

from reward.models import RewardBenefit, RewardTier
from utils.convert_response import convert_response
from common.core.subquery import *
from package.models import Package


class PackageListApi(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        
        reward_benefit = SubqueryJsonAgg(
            RewardBenefit.objects.filter(tier_id_id=OuterRef('id'))
        )

        reward_tier = SubqueryJson(
            RewardTier.objects.filter(min_points__lte=OuterRef('points_reward')).order_by('min_points')[:1].values().annotate(
                reward_benefit=reward_benefit
            )
        )
        
        packages = Package.objects.filter().values().annotate(
            reward_tier=reward_tier
        )

        return convert_response('success', 200, data=packages)
