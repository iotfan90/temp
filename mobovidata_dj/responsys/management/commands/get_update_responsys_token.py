from __future__ import absolute_import

from django.core.management.base import BaseCommand

from mobovidata_dj.responsys.models import ResponsysCredential
from mobovidata_dj.responsys.utils import get_responsys_token


class Command(BaseCommand):
    """
    Accessed every 90 mins to update access token of responsysapi
    Usage:
        'Python manage.py update_responsys_token'
    """
    help = 'Update responsysapi access token'

    def handle(self, *args, **options):
        """
        Update responsysapi access token
        """
        auth_token = get_responsys_token()
        try:
            obj = ResponsysCredential.objects.get()
            obj.token = auth_token['authToken']
            obj.endpoint = auth_token['endPoint']
            obj.save()
        except ResponsysCredential.DoesNotExist:
            obj = ResponsysCredential(
                token=auth_token['authToken'],
                endpoint=auth_token['endPoint']
            )
            obj.save()
        print 'Updated Access Token'
