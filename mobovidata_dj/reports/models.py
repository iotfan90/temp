import csv
import datetime
import json
import os

from collections import OrderedDict
from decimal import Decimal
from django.conf import settings
from django.db import models, connections
from django.utils import timezone

from mobovidata_dj.bigdata.utils import get_redshift_connection

REPORT_DIR = './data/reports/'

DB_SOURCES = [
    ('redshift', 'Redshift'),
    ('mvd', 'Mobovidata'),
    ('modjento', 'Modjento'),
]

"""
# Looker has stated that there is no way to determine which PDT is most recent
# Leaving this here for posterity
def get_looker_pdts():
    cnx = get_redshift_connection()
    cur = cnx.cursor()
    cur.execute("select table_name from information_schema.tables where table_schema = 'looker_scratch';")
    looker_tables = {'_'.join(t[0].split('_')[1:]): t[0]
                     for t in cur.fetchall() if t[0].startswith('lr')}
    return looker_tables
"""


class ReportQuery(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=128)
    source = models.CharField(max_length=128, choices=DB_SOURCES)
    query = models.TextField()

    @property
    def cleaned_query(self):
        q = self.query.strip()
        if not q.endswith(';'):
            q = '%s;' % q
        return q

    @property
    def connection(self):
        if self.source == 'redshift':
            return get_redshift_connection()
        if self.source == 'mvd':
            return connections['default']
        if self.source == 'modjento':
            return connections['magento']

    @property
    def csv_url(self):
        return '/export_report/%s.csv' % self.pk

    def run_query(self):
        cursor = self.connection.cursor()
        cursor.execute(self.cleaned_query)
        columns = [col[0] for col in cursor.description]
        return columns, cursor

    def iterate_rows_as_dict(self):
        columns, cursor = self.run_query()
        for row in cursor.fetchall():
            yield OrderedDict(zip(columns, row))
        cursor.close()

    def execute(self, target=None, format=None, gzip=False):
        from gzip import open as gz_open
        target = target or 'local'
        format = format or 'csv'
        exc = ReportExecution.objects.create(query=self, status='running',
                                             started_at=timezone.now(),
                                             target=target, format=format,
                                             gzip=gzip)
        try:
            columns, cursor = self.run_query()

            if not os.path.exists(REPORT_DIR):
                os.mkdir(REPORT_DIR)

            f_open = gzip and gz_open or open
            with f_open(exc.full_path, 'wb+') as fh:
                if format == 'csv':
                    writer = csv.DictWriter(fh, fieldnames=columns,
                                            quoting=csv.QUOTE_ALL)
                    writer.writeheader()
                for row in cursor.fetchall():
                    row = ((isinstance(f, unicode) and f.encode('utf-8'))
                           or f for f in row)
                    data = OrderedDict(zip(columns, row))
                    exc.discover_metadata(data)
                    if format == 'csv':
                        writer.writerow(data)
                    if format == 'json':
                        fh.write(json.dumps(data))
            if target == 's3':
                exc.upload_to_s3(True)
            if target == 'redshift' and columns:
                exc.redshift_copy(destroy=True)
            exc.status = 'ok'
        except Exception as e:
            exc.status = 'error'
            exc.message = str(e)
            print('Error running query: %s' % e)
            raise
        exc.completed_at = timezone.now()
        exc.save()
        return exc

    def delay_execute(self, *args, **kwargs):
        from .tasks import execute_query
        return execute_query.delay(self.id, *args, **kwargs)

QUERY_STATUS = [
    (None, 'Not yet started'),
    ('running', 'Running'),
    ('ok', 'OK'),
    ('error', 'Error'),
]

TARGETS = [
    ('local', 'Local (server)'),
    ('download', 'Download'),
    ('s3', 'S3'),
]

FORMATS = [
    ('csv', 'CSV'),
    ('json', 'JSON'),
]


class ReportExecution(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    query = models.ForeignKey(ReportQuery)

    status = models.CharField(max_length=32, null=True, blank=True,
                              choices=QUERY_STATUS)
    message = models.TextField(null=True, blank=True)
    metadata_json = models.TextField(null=True, blank=True)

    target = models.CharField(max_length=32, choices=TARGETS, default='s3')
    format = models.CharField(max_length=32, choices=FORMATS, default='csv')
    gzip = models.BooleanField(default=False)

    on_s3_at = models.BooleanField(default=False)
    s3_filename = models.BooleanField(default=False)

    def __str__(self):
        return '[%s] %s'%(self.status, self.filename)

    @property
    def full_path(self):
        return '%s/%s'%(REPORT_DIR,self.filename)

    @property
    def full_format(self):
        return (self.gzip and '%s.gz' or '%s') % self.format

    @property
    def filename(self):
        return '%s.%s.%s'%(self.query.title,
                           self.created_at.strftime('%Y-%m-%d.%H-%I-%S'),
                           self.full_format)

    @property
    def on_disk(self):
        return os.path.exists(self.full_path)

    @property
    def metadata(self):
        if not hasattr(self, '_metadata_parsed'):
            self._metadata_parsed = json.loads(self.metadata_json or '{}') or {}
        return self._metadata_parsed

    def save(self, *args, **kwargs):
        if hasattr(self, '_metadata_parsed'):
            self.metadata_json = json.dumps(self._metadata_parsed)

        return super(ReportExecution, self).save(*args, **kwargs)

    def remove_from_disk(self):
        return os.unlink(self.full_path)

    def upload_to_s3(self, remove_on_complete=False, callback=None):
        from mobovidata_dj.taskapp.utils import upload_to_s3
        if self.s3_filename and self.on_s3_at:
            return self.s3_filename
        with open(self.full_path, 'rb') as fh:
            output = upload_to_s3(settings.S3_BACKUP_KEY,
                                  settings.S3_BACKUP_SECRET,
                                  fh, settings.S3_REPORT_BUCKET, self.filename,
                                  callback=callback)
            self.on_s3_at = timezone.now()
            self.s3_filename = output
            self.save()
            if remove_on_complete:
                self.remove_from_disk()
            return output

    @property
    def column_names(self):
        if not self.metadata or '_order' not in self.metadata:
            self._metadata_parsed = {'_order': []}
        return self.metadata['_order']

    @property
    def columns(self):
        if not self.metadata or '_order' not in self.metadata:
            self._metadata_parsed = {'_order': []}
        return OrderedDict((k, self.metadata.get(k, {})) for k in self.column_names)

    def discover_metadata(self, row_data):
        metadata = self.metadata or {'_count': 0}
        metadata['_order'] = list(row_data.keys())
        metadata['_count'] += 1
        for k, v in row_data.items():
            if v is None: continue
            if not metadata.get(k, None):
                metadata[k] = {}

            if isinstance(v, ( str, unicode )):
                metadata[k]['type'] = 'text'
                metadata[k]['size'] = max(
                    metadata[k].get('size', 0), len(v))
                if metadata[k]['size'] < 65535:
                    metadata[k]['type'] = 'varchar(%s)'%(metadata[k]['size'])

            if isinstance(v, (datetime.datetime, datetime.date)):
                metadata[k]['type'] = 'timestamp'

            if isinstance(v, (int, long)):
                # If previous rows were float, but this
                # is an integer, don't update to float
                if not metadata[k].get('type', '') == 'float':
                    metadata[k]['type'] = 'integer'

            if isinstance(v, (float, Decimal)):
                metadata[k]['type'] = 'float'
        self._metadata_parsed = metadata

    @property
    def stubify_name(self):
        import re
        underscores = re.sub('( |-|__)', '_', self.query.title.lower())
        return re.sub('[^\d\w]', '', underscores)

    def redshift_drop_table_if_exists(self, table=None, schema='reports'):
        full_table = '%s.%s'%(schema, table or self.stubify_name)
        cnx = get_redshift_connection()
        cur = cnx.cursor()
        query = "DROP TABLE IF EXISTS %s" % full_table
        print query
        cur.execute(query)
        cnx.commit()

    def redshift_create_table(self, table=None, destroy=False,
                              schema='reports'):
        full_table = '%s.%s' % (schema, table or self.stubify_name)
        if destroy:
            self.redshift_drop_table_if_exists(table, schema)

        columns = '\n%s\n' % ',\n'.join(
            '%s %s' % (k, v.get('type', 'varchar(255)'))
            for k, v in self.columns.items()
        )
        cnx = get_redshift_connection()
        cur = cnx.cursor()
        query = "CREATE TABLE %s (%s)" % (full_table, columns)
        print query
        cur.execute(query)
        cnx.commit()

    def redshift_copy(self, table=None, create=True, destroy=True,
                      schema='reports'):
        full_table = '%s.%s' % (schema, table or self.stubify_name)

        self.upload_to_s3()

        if create:
            self.redshift_create_table(table, destroy=destroy, schema=schema)

        cnx = get_redshift_connection()
        cur = cnx.cursor()
        query = """
        COPY %s
        FROM 's3://%s/%s'
        TIMEFORMAT 'YYYY-MM-DD HH:MI:SS' ACCEPTANYDATE
        CREDENTIALS 'aws_access_key_id=%s;aws_secret_access_key=%s'
        COMPUPDATE OFF STATUPDATE OFF
        REGION 'us-west-1'
        %s %s ;
        """ % (
            full_table,
            settings.S3_REPORT_BUCKET,
            self.s3_filename,
            settings.S3_BACKUP_KEY,
            settings.S3_BACKUP_SECRET,
            self.format == 'csv' and 'CSV IGNOREHEADER 1' or '',
            self.gzip and 'GZIP' or ''
        )

        print query

        cur.execute(query)
        cnx.commit()
