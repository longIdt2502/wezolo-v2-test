from django.core.management.base import BaseCommand
import json
from package.models import Price


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write('Creating price...')
        data = json.loads(open("package/management/data/price_data.json").read())
        for item in data:
            price = Price.objects.filter(type=item.get('type'), value=item.get('value')).first()
            if not price:
                Price.objects.create(
                    type=item.get('type'),
                    value=item.get('value')
                )
        self.stdout.write(self.style.SUCCESS('Create price!'))
