from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Load data alerts'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Loading alerts fixtures...'))
        call_command('loaddata', 'alerts_fixtures.json')
        self.stdout.write(self.style.SUCCESS('Alerts fixtures loaded successfully!'))
