from django.core.management.base import BaseCommand
import json
from reward.models import RewardTier


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write('Creating package...')
        data = json.loads(open("reward/management/data/reward_tier_data.json").read())
        for item in data:
            RewardTier().from_json(item)
        self.stdout.write(self.style.SUCCESS('Create package!'))
