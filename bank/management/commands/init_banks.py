from django.core.management.base import BaseCommand
import json
from bank.models import Banks


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write('Creating bank...')
        data = json.loads(open("bank/management/data/data_banks.json").read())
        for item in data:
            bank = Banks.objects.filter(bin_code=item.get('bin')).first()
            if not bank:
                Banks.objects.create(
                    code=item.get('code'),
                    name=item.get('name'),
                    bin_code=item.get('bin'),
                    logo=item.get('logo'),
                    short_name=item.get('short_name'),
                    swift_code=item.get('swift_code'),
                    support=item.get('support'),
                    is_transfer=item.get('isTransfer'),
                    lookup_supported=item.get('lookupSupported'),
                    transfer_supported=item.get('transferSupported'),
                )
        self.stdout.write(self.style.SUCCESS('Create bank!'))
