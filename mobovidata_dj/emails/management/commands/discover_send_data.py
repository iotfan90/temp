from django.core.management.base import BaseCommand, CommandError
from mobovidata_dj.emails.tasks import discover_send_data

class Command(BaseCommand):
    help = 'Discovers send data csv files for importing'

    def handle(self, *args, **options):
        discover_send_data()

