from django.core.management.base import BaseCommand, CommandError
from django.core.mail import mail_admins
from django.conf import settings
from datetime import datetime

from mobovidata_dj.taskapp.tasks import backup_to_s3
import pytz

class Command(BaseCommand):
    def handle(self, *args, **options):
        backup_to_s3()
