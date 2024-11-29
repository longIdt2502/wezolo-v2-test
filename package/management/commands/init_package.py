from django.core.management.base import BaseCommand
import json
from package.models import Package


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write('Creating package...')
        data = json.loads(open("package/management/data/package_data.json").read())
        for item in data:
            package = Package.objects.filter(code=item.get('code')).first()
            if not package:
                Package().from_json(item)
        self.stdout.write(self.style.SUCCESS('Create package!'))
