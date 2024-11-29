from django.core.management.base import BaseCommand
import json
from reward.models import RewardBenefit, RewardTier
from package.models import Price


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write('Creating Reward Benefit...')
        data = json.loads(open("reward/management/data/reward_benefit_data.json").read())
        for item in data:
            reward_tier = RewardTier.objects.get(code=item.get('tier_name'))
            price = Price.objects.get(type=item.get('type'), value=item.get('value'))
            reward_benefit = RewardBenefit.objects.filter(tier_id=reward_tier, value=price).filter()
            if not reward_benefit:
                RewardBenefit.objects.create(
                    tier_id=reward_tier,
                    benefit_name=item.get('benefit_name'),
                    benefit_description=item.get('benefit_name'),
                    type=item.get('type'),
                    value=price
                )
        self.stdout.write(self.style.SUCCESS('Create Reward Benefit!'))
