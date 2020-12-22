from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from jsonfield import JSONField


class WebhookTransaction(models.Model):
    UNPROCESSED = 'UNPROCESSED'
    PROCESSED = 'PROCESSED'
    ERROR = 'ERROR'
    STATUS_CHOICES = (
        (UNPROCESSED, 'Unprocessed'),
        (PROCESSED, 'Processed'),
        (ERROR, 'Error'),
    )
    AFTERSHIP = 'AFTERSHIP'
    DOJOMOJO = 'DOJOMOJO'
    SHOPIFY = 'SHOPIFY'
    UNBOUNCE = 'UNBOUNCE'
    WEBHOOK_TYPE_CHOICES = (
        (AFTERSHIP, 'Aftership'),
        (DOJOMOJO, 'Dojomojo'),
        (SHOPIFY, 'SHOPIFY'),
        (UNBOUNCE, 'Unbounce'),
    )

    body = JSONField()
    date_processed = models.DateTimeField(blank=True, null=True)
    date_received = models.DateTimeField(default=timezone.now)
    error_msg = models.TextField('Error message', blank=True, null=True)
    request_meta = JSONField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES,
                              default=UNPROCESSED)
    webhook_type = models.CharField(max_length=30, choices=WEBHOOK_TYPE_CHOICES)

    def __unicode__(self):
        return u'{0} - {1}'.format(self.date_received,
                                   self.get_webhook_type_display())


class Dojomojo(models.Model):
    MALE = 'Male'
    FEMALE = 'Female'
    GENDER_CHOICES = (
        (MALE, 'Male'),
        (FEMALE, 'Female'),
    )
    UNPROCESSED = 'UNPROCESSED'
    PROCESSED = 'PROCESSED'
    ERROR = 'ERROR'
    STATUS_CHOICES = (
        (UNPROCESSED, 'Unprocessed'),
        (PROCESSED, 'Processed'),
        (ERROR, 'Error'),
    )
    birthday = models.DateField(blank=True, null=True)
    campaign_name = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    custom_field = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField()
    firstname = models.CharField(max_length=30, blank=True, null=True)
    fullname = models.CharField(max_length=65, blank=True, null=True)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, blank=True,
                              null=True)
    ip = models.GenericIPAddressField(blank=True, null=True)
    lastname = models.CharField(max_length=30, blank=True, null=True)
    phone = models.CharField(max_length=25, blank=True, null=True)
    referrer = models.CharField(max_length=50, blank=True, null=True)
    source = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES,
                              default=UNPROCESSED)
    street_address = models.CharField(max_length=100, blank=True, null=True)
    zipcode = models.CharField(max_length=10, blank=True, null=True)


class Unbounce(models.Model):
    UNPROCESSED = 'UNPROCESSED'
    PROCESSED = 'PROCESSED'
    ERROR = 'ERROR'
    STATUS_CHOICES = (
        (UNPROCESSED, 'Unprocessed'),
        (PROCESSED, 'Processed'),
        (ERROR, 'Error'),
    )

    email_address = models.EmailField()
    date_submitted = models.DateField()
    date_processed = models.DateTimeField(blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    page_name = models.CharField(max_length=100)
    page_url = models.URLField()
    page_uuid = models.CharField(max_length=50)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES,
                              default=UNPROCESSED)
    time_submitted = models.TimeField()
    variant = models.CharField(max_length=25)
