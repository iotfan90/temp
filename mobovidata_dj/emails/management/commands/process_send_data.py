from django.core.management.base import BaseCommand, CommandError
from mobovidata_dj.emails.tasks import process_send_data_batch

class Command(BaseCommand):
    help = 'Processes send data csv files'

    def handle(self, *args, **options):
        process_send_data_batch()
