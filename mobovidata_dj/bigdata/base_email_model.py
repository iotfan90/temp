# Author: Lee Bailey, l@lwb.co
# 8/5/2016

from __future__ import unicode_literals

from dateutil.parser import parse
from django.db import models


FORMAT_CHOICES = (
    ('H', 'HTML'),
    ('T', 'Text'),
    ('N', 'No Prefered'),
    ('M', 'Multipart'),
)


class CSV_ETL_Mixin(object):
    """
Performs extract-transform-load logic for
    Responsys style email CSV data.
    CSV filenames are in the format
    "ACCTID_TYPE_DATE_TIME.txt"
    """

    @classmethod
    def csv_to_rows(cls, fh):
        """ Returns dictionary data, based on names
            parsed from first row of data (required)
        """
        import csv
        mapping = {}
        for row in csv.reader(fh):
            if not mapping and 'EVENT_TYPE_ID' in row:
                for i, r in enumerate(row):
                    mapping[i] = r.lower()
            else:
                yield {
                    mapping[i]: r
                    for i, r in enumerate(row)
                }

    @classmethod
    def csv_row_to_dict(cls, row):
        """ Returns model data, from the row of a CSV
            performing all casting, according to the
            django field types
            :return:
        """
        def cast_field(f, v):
            _type = cls._meta.get_field(f)
            if not v:
                return None
            if isinstance(_type, models.IntegerField):
                return int(v or "0")
            if isinstance(_type, models.FloatField):
                return float(v or "0")
            if isinstance(_type, models.DateTimeField):
                return parse(v)
            return v
        return {
            field: cast_field(field, row[field])
            for i, field in enumerate(cls.__csv_fields__)
            if field in row
        }

    @classmethod
    def csv_to_dicts(cls, fh):
        for row in cls.csv_to_rows(fh):
            yield cls.csv_row_to_dict(row)

EMAIL_BASE_CSV_FIELDS = ['event_type_id', 'account_id', 'list_id', 'riid',
                         'customer_id', 'event_captured_dt', 'event_stored_dt',
                         'campaign_id', 'launch_id', ]


class EmailBase(CSV_ETL_Mixin, models.Model):
    """
        Used as a base for all responsys send data models
        Includes the ETL, a method for generating the primary key
        and methods for creating the objects straight from CSV data
    """
    id = models.CharField(max_length=255, primary_key=True)
    event_type_id = models.IntegerField()
    account_id = models.IntegerField()
    list_id = models.IntegerField(null=True, blank=True)
    riid = models.IntegerField()
    customer_id = models.CharField(max_length=255, null=True, blank=True)
    event_captured_dt = models.DateTimeField()
    event_stored_dt = models.DateTimeField()
    campaign_id = models.IntegerField()
    launch_id = models.IntegerField()
    email = models.CharField(max_length=255, null=True, blank=True)
    email_isp = models.CharField(max_length=255)
    email_format = models.CharField(max_length=1, choices=FORMAT_CHOICES,
                                    default='N')

    @classmethod
    def pk_from_dict(cls, info):
        return '%s-%s-%s-%s' % (
            info['riid'],
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
        abstract = True
        ordering = ('-event_captured_dt', )
