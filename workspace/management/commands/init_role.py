from django.core.management.base import BaseCommand
import json
from workspace.models import Role


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write('Creating role...')
        data = json.loads(open("workspace/management/data/roles.json").read())
        for item in data:
            role = Role.objects.filter(code=item.get('code')).first()
            if not role:
                Role().from_json(item)
        self.stdout.write(self.style.SUCCESS('Create role!'))
