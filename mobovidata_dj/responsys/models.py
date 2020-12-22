from __future__ import unicode_literals

from django.db import models

from .managers import OptedOutEmailsManager


class ResponsysCredentialManager(models.Manager):
    """
    Code used to refresh the responsys api access token.
    """
    def update_responsys_token(self):
        """
        Creates/updates the responsys API token
        """
        auth_token = get_responsys_token()
        try:
            credentials = ResponsysCredential.objects.get()
            credentials.token = auth_token['authToken']
            credentials.endpoint = auth_token['endPoint']
            credentials.save()
        except ResponsysCredential.DoesNotExist:
            credentials = ResponsysCredential(
                token=auth_token['authToken'],
                endpoint=auth_token['endPoint']
            )
            credentials.save()
        return credentials


class ResponsysCredential(models.Model):
    token = models.CharField(unique=True, max_length=200)
    endpoint = models.URLField()
    campaign_endpoint = models.CharField(max_length=200,
                                         default="/rest/api/v1/campaigns/")
    event_endpoint = models.CharField(max_length=200,
                                      default="/rest/api/v1/events/")
    modified_dt = models.DateTimeField(auto_now=True)

    objects = ResponsysCredentialManager()

    def get_event_endpoint(self, endpoint_type):
        end_points = {
            'campaign': '/rest/api/v1/campaigns/',
            'event': '/rest/api/v1/events/'
        }
        return self.endpoint + end_points[endpoint_type]

    class Meta:
        db_table = "responsys_credential"


class OptedOutEmails(models.Model):
    """
    Used for Criteo abandonment emails opt out checks.
    No primary key to speed loads, since this table is truncated and reloaded
    nightly.
    """
    riid = models.IntegerField(null=True)
    email = models.EmailField()
    md5 = models.CharField(max_length=32)
    subscription_status = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    objects = OptedOutEmailsManager()

    class Meta:
        db_table = "opted_out_emails"


# class ResponsysIdEmail(models.Model):
#     """
#     Used for Criteo abandonment emails opt out checks.
#     No primary key to speed loads, since this table is truncated and reloaded nightly.
#     """
#     riid = models.IntegerField(primary_key=True)
#     email = models.EmailField()
#     md5 = models.CharField(max_length=32)
#     subscription_status = models.IntegerField()
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         db_table = "responsys_id_email"


class NetPromoterScore(models.Model):
    """
    Collects customer's NPS Submissions
    """
    riid = models.IntegerField(primary_key=True, unique=True)
    nps_score = models.IntegerField(db_index=True)
    medium = models.CharField(max_length=128)
    campaign = models.CharField(max_length=128)
    promocode = models.CharField(max_length=128)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'responsys_nps'


class RiidEmail(models.Model):
    """
    Map of Responsys Unique identifier to email address
    """
    riid = models.IntegerField(primary_key=True, unique=True)
    email = models.CharField(max_length=128)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'responsys_riid_email'

from .tasks import get_responsys_token
