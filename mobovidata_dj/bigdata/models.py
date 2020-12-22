# Author: Lee Bailey, l@lwb.co
# 8/9/2016

"""
Class overview

+ EmailBase: (from base_model.py) Parent class, 13 fields
+  EmailBrowserBase: 4 extra fields of browser data (17 total)
+    EmailOfferBase: 4 extra fields of offer data (21 total)

... Rest of classes inherit from one of
EmailBase, BrowserBase, or OfferBase

"""

from django.db import models
import django.db.models.options as options

from .base_email_model import EmailBase, CSV_ETL_Mixin, EMAIL_BASE_CSV_FIELDS


if 'in_db' not in options.DEFAULT_NAMES:
    """
    Required for our Django DB routing, this adds
    an extra "in_db" option to model.Meta (it would
    otherwise throw an error that in_db is unsupported)
    """
    options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('in_db',)


class EmailBrowserBase(EmailBase):
    user_agent_string = models.CharField(max_length=255, null=True, blank=True)
    operating_system = models.CharField(max_length=3, null=True, blank=True)
    browser = models.CharField(max_length=2, null=True, blank=True)
    browser_type = models.CharField(max_length=2, null=True, blank=True)

    class Meta:
        abstract = True


class EmailOfferBase(EmailBrowserBase):
    offer_name = models.CharField(max_length=255, null=True, blank=True)
    offer_number = models.IntegerField(null=True, blank=True)
    offer_category = models.CharField(max_length=255, null=True, blank=True)
    offer_url = models.CharField(max_length=4096, null=True, blank=True)

    class Meta:
        abstract = True


class EmailBounced(EmailBase):
    __csv_type__ = 'BOUNCE'
    __csv_fields__ = EMAIL_BASE_CSV_FIELDS + ['email', 'email_format',
                                              'bounce_type', 'reason',
                                              'reason_code', 'subject',
                                              'contact_info']
    bounce_type = models.CharField(max_length=255, null=True, blank=True,
                                   choices=(('H', 'Hard Bounce'),
                                            ('S', 'Soft Bounce')))
    reason = models.CharField(max_length=255, null=True, blank=True)
    reason_code = models.CharField(max_length=255, null=True, blank=True)
    subject = models.CharField(max_length=255, null=True, blank=True)
    contact_info = models.CharField(max_length=1024, null=True, blank=True)

    class Meta:
        managed = False


class EmailClick(EmailOfferBase):
    __csv_type__ = 'CLICK'
    __csv_fields__ = EMAIL_BASE_CSV_FIELDS + [
        'email_format',
        'offer_name', 'offer_number', 'offer_category', 'offer_url',
        'user_agent_string', 'operating_system', 'browser', 'browser_type']

    class Meta:
        managed = False


class EmailComplaint(EmailBase):
    __csv_type__ = 'COMPLAINT'
    __csv_fields__ = EMAIL_BASE_CSV_FIELDS + [
        'email_format', 'reason', 'email',
        'email_isp', 'complainer_email', 'spam_type',
        'contact_info', 'complaint_dt']

    reason = models.CharField(max_length=512)
    complainer_email = models.CharField(max_length=255)
    spam_type = models.CharField(max_length=16)
    complaint_dt = models.DateTimeField(null=True, blank=True)
    contact_info = models.CharField(max_length=1024, null=True, blank=True)

    class Meta:
        managed = False


class EmailConverted(EmailOfferBase):
    __csv_type__ = 'CONVERT'
    __csv_fields__ = EMAIL_BASE_CSV_FIELDS + [
        'source', 'email_format', 'offer_name',
        'offer_number', 'offer_category', 'offer_url',
        'order_id', 'order_total', 'order_quantity',
        'user_agent_string', 'operating_system', 'browser', 'browser_type']

    source = models.CharField(max_length=255)
    order_id = models.CharField(max_length=255)
    order_total = models.FloatField()
    order_quantity = models.FloatField()

    class Meta:
        managed = False


class EmailFailed(EmailBase):
    __csv_type__ = 'FAIL'
    __csv_fields__ = EMAIL_BASE_CSV_FIELDS + [
        'email', 'email_isp', 'email_format',
        'offer_signature_id', 'dynamic_content_signature_id',
        'message_size', 'segment_info', 'contact_info', 'reason']
    offer_signature_id = models.IntegerField(null=True, blank=True)
    dynamic_content_signature_id = models.IntegerField(null=True, blank=True)
    message_size = models.IntegerField(null=True, blank=True)
    segment_info = models.CharField(max_length=4096, null=True, blank=True)
    contact_info = models.CharField(max_length=1024, null=True, blank=True)
    reason = models.CharField(max_length=1024, null=True, blank=True)

    class Meta:
        managed = False


class EmailOpened(EmailBrowserBase):
    __csv_type__ = 'OPEN'
    __csv_fields__ = EMAIL_BASE_CSV_FIELDS + [
        'email_format', 'user_agent_string', 'operating_system',
        'browser', 'browser_type']

    class Meta:
        managed = False


class EmailSent(EmailBase):
    __csv_type__ = 'SENT'
    __csv_fields__ = EMAIL_BASE_CSV_FIELDS + [
        'email', 'email_isp', 'email_format',
        'offer_signature_id', 'dynamic_content_signature_id',
        'message_size', 'segment_info', 'contact_info']

    offer_signature_id = models.IntegerField(null=True, blank=True)
    dynamic_content_signature_id = models.IntegerField(null=True, blank=True)
    message_size = models.IntegerField(null=True, blank=True)
    segment_info = models.CharField(max_length=4096, null=True, blank=True)
    contact_info = models.CharField(max_length=1024, null=True, blank=True)

    # For the stats aggregation runner
    aggregated_at = models.DateTimeField(default='1970-01-01 00:00', null=True,
                                         blank=True)

    class Meta:
        managed = False


class EmailSkipped(EmailBase):
    __csv_type__ = 'SKIPPED'
    __csv_fields__ = EMAIL_BASE_CSV_FIELDS + [
        'email', 'email_isp', 'email_format',
        'offer_signature_id', 'dynamic_content_signature_id',
        'message_size', 'segment_info', 'contact_info', 'reason']
    offer_signature_id = models.IntegerField(null=True, blank=True)
    dynamic_content_signature_id = models.IntegerField(null=True, blank=True)
    message_size = models.IntegerField(null=True, blank=True)
    segment_info = models.CharField(max_length=4096, null=True, blank=True)
    contact_info = models.CharField(max_length=1024, null=True, blank=True)
    reason = models.CharField(max_length=1024, null=True, blank=True)

    class Meta:
        managed = False


class EmailOptIn(EmailBase):
    __csv_type__ = 'OPT_IN'
    __csv_fields__ = ["event_type_id", "account_id", "list_id", "riid",
                      "customer_id", "event_captured_dt", "event_stored_dt",
                      "campaign_id", "launch_id", "email_format", "source",
                      "reason", "email"]
    source = models.CharField(max_length=1024, null=True, blank=True)
    reason = models.CharField(max_length=1024, null=True, blank=True)

    class Meta:
        managed = False


class EmailOptOut(EmailBase):
    __csv_type__ = 'OPT_OUT'
    __csv_fields__ = ["event_type_id", "account_id", "list_id", "riid",
                      "customer_id", "event_captured_dt", "event_stored_dt",
                      "campaign_id", "launch_id", "email_format", "source",
                      "reason", "email",  "contact_info"]
    source = models.CharField(max_length=1024, null=True, blank=True)
    reason = models.CharField(max_length=1024, null=True, blank=True)
    contact_info = models.CharField(max_length=1024, null=True, blank=True)

    class Meta:
        managed = False


class LaunchState(CSV_ETL_Mixin, models.Model):
    __csv_type__ = 'LAUNCH_STATE'
    __csv_fields__ = ["account_id", "list_id", "event_captured_dt",
                      "event_stored_dt", "campaign_id", "launch_id",
                      "external_campaign_id", "sf_campaign_id", "campaign_name",
                      "launch_name", "launch_status", "launch_type",
                      "launch_charset", "purpose", "subject", "description",
                      "product_category", "product_type", "marketing_strategy",
                      "marketing_program", "launch_error_code",
                      "launch_started_dt", "launch_completed_dt"]

    id = models.CharField(max_length=255, primary_key=True)
    account_id = models.IntegerField()
    list_id = models.IntegerField(null=True, blank=True)
    event_captured_dt = models.DateTimeField()
    event_stored_dt = models.DateTimeField()

    campaign_id = models.IntegerField()
    launch_id = models.IntegerField()
    external_campaign_id = models.CharField(max_length=255)
    sf_campaign_id = models.CharField(max_length=255)

    campaign_name = models.CharField(max_length=255)
    launch_name = models.CharField(max_length=255)
    launch_status = models.CharField(max_length=1)
    launch_type = models.CharField(max_length=1)
    launch_charset = models.CharField(max_length=255)

    purpose = models.CharField(max_length=1)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    product_category = models.CharField(max_length=255)
    product_type = models.CharField(max_length=255)
    marketing_strategy = models.CharField(max_length=255)
    marketing_program = models.CharField(max_length=255)

    launch_error_code = models.CharField(max_length=255)
    launch_started_dt = models.DateTimeField()
    launch_completed_dt = models.DateTimeField()

    @classmethod
    def pk_from_dict(cls, info):
        return '%s-%s-%s' % (
            info['campaign_id'],
            info['launch_id'],
            info['event_captured_dt']
        )

    @classmethod
    def add_pk(cls, info):
        info['id'] = cls.pk_from_dict(info)
        return info

    @classmethod
    def create_from_dict(cls, info):
        cls.objects.create(**cls.add_pk(info))

    @classmethod
    def csv_files(cls, path=None, account='*', date='*'):
        import glob
        import os
        path = path or './send_data'
        find = '%s_%s_%s_*.txt' % (account, cls.__csv_type__, date)
        return glob.glob(os.path.join(path, find))

    class Meta:
        managed = False
        ordering = ('-event_captured_dt', )


EMAIL_MODELS = [EmailBounced, EmailComplaint, EmailSkipped, EmailFailed,
                EmailClick, EmailConverted, EmailSent, EmailOpened, EmailOptIn,
                EmailOptOut, LaunchState]
