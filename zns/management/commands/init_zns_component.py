from django.core.management.base import BaseCommand
import json
from zns.models import ZnsComponent


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write('Creating Zns Component...')
        data = json.loads(open("zns/management/data/data_zns_component.json").read())
        for item in data:
            zns_component = ZnsComponent.objects.filter(
                name=item.get('name'),
                type=item.get('type'),
                layout=item.get('layout')
            ).first()
            if not zns_component:
                ZnsComponent.objects.create(
                    name=item.get('name'),
                    type=item.get('type'),
                    layout=item.get('layout')
                )
        self.stdout.write(self.style.SUCCESS('Created Zns Component!'))
