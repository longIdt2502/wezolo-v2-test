from django.core.management.base import BaseCommand
import json
from reward.models import RewardTier


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write('Creating reward tier...')
        data = json.loads(open("reward/management/data/reward_tier_data.json").read())
        for item in data:
            reward_tier = RewardTier.objects.filter(code=item.get('code')).first()
            if not reward_tier:
                RewardTier().from_json(item)
        self.stdout.write(self.style.SUCCESS('Create reward tier!'))
