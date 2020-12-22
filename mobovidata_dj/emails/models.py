# Author: Lee Bailey, l@lwb.co
# 8/5/2016

"""
Class overview

+ CSVImport: One instance per CSV file to be imported
+ CSVImportError: One instance per error encountered

+ UserStatsDenorm: One per riid, per-user targetting for email campaigns

"""

from __future__ import unicode_literals
import json
import logging
import os

from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone

from mobovidata_dj.taskapp.utils import upload_s3_senddata_backup

log = logging.getLogger(__name__)

IMPORT_STATUS_CHOICES = [
    ('new', 'New'),
    ('started', 'Started'),
    ('success', 'Success'),
    ('almost', 'Success (>95%)'),
    ('partial', 'Partial'),
    ('error', 'Error')
]


class CSVImport(models.Model):
    discovered_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    target_type = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=IMPORT_STATUS_CHOICES,
                              default='new')
    parsed_at = models.DateTimeField(null=True, blank=True)
    expected_rows = models.PositiveIntegerField(null=True, blank=True)
    parsed_rows = models.PositiveIntegerField(null=True, blank=True)

    uploaded_to_s3_at = models.DateTimeField(null=True, blank=True)
    s3_filename = models.CharField(max_length=255, null=True, blank=True)

    import_to_redshift_at = models.DateTimeField(null=True, blank=True)
    redshift_result = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ('-parsed_at',)

    def get_success_rate(self):
        if ((self.expected_rows == None and self.parsed_rows == 0) or
                    self.expected_rows == self.parsed_rows):
            return '100%'
        if self.expected_rows and self.parsed_rows:
            return '%s%%'%round(100.0*self.parsed_rows/self.expected_rows,1)
        return '-'

    def __str__(self):
        status = self.status
        if self.status == 'partial':
            status += self.get_success_rate()
        return '[%s] %s'%(status, self.filename)

    @classmethod
    def model_types(cls):
        from mobovidata_dj.bigdata.models import EMAIL_MODELS
        return EMAIL_MODELS

    @classmethod
    def discover(cls, path=None, account='*', date='*'):
        path = path or settings.RESPONSYS_SEND_DATA_PATH['tgt']
        discovered = {}
        for m in cls.model_types():
            name = m._meta.label
            try:
                fns = m.csv_files(path, account=account, date=date)
                for fn in fns:
                    expected_path = '%s._counts' % fn
                    if os.path.exists(expected_path):
                        try:
                            expected = int(open(expected_path).read())
                        except:
                            expected = None
                    csv, _new = CSVImport.objects.get_or_create(
                        filename=fn, target_type=name)
                    if expected and expected != csv.expected_rows:
                        csv.expected_rows = expected
                        csv.save()

            except Exception as e:
                fns = []
                CSVImportError.objects.create(error=str(e))
            discovered[name] = fns
        return discovered

    @classmethod
    def get_pending_type(cls, model_type):
        name = model_type._meta.label
        return CSVImport.objects.filter(target_type=name, status='new')

    @classmethod
    def get_pending(cls):
        return {k: v for k, v in
                    {m: cls.get_pending_type(m)
                     for m in cls.model_types()}.items()
                if v.count()}

    def process(self, model_class):
        self.parsed_at = timezone.now()
        self.status = 'started'
        self.save()
        """
        try: rows = model_class.csv_to_rows(open(self.filename, 'rb'))
        except Exception as e:
            CSVImportError.objects.create(csv=self, error=str(e))
            self.status = 'error'
            self.parsed_rows = self.parsed_rows or 0
            self.save()
            return
        ok, errors = {}, {}
        No longer importing into crate
        for i, row in enumerate(rows):
            if len(ok) and i % 1000 == 0:
                self.parsed_rows = len(ok)
                self.save()

            try: data = model_class.csv_row_to_dict(row)
            except Exception as e:
                CSVImportError.objects.create(csv=self, row=i,
                        error='Parse error: %s'%str(e),
                        data=row)
                errors[i] = row
                continue

            try: model_class.create_from_dict(data)
            except Exception as e:
                CSVImportError.objects.create(csv=self, row=i,
                        error='Import error: %s'%str(e),
                        data=str(data))
                errors[i] = row
                continue
            ok[i] = row
        self.parsed_rows = len(ok)
        """

        self.status = 'success'
        self.save()

        if self.status != 'error':
            self.post_process()

    @property
    def on_disk(self):
        return os.path.exists(self.filename)

    def read_columns_from_file(self):
        if not self.on_disk: return []
        header = open(self.filename, 'rb').readline().lower()
        columns = [c.strip().strip('"') for c in header.split(',') if c]
        return columns

    def read_columns_from_json(self):
        return json.loads(open('mobovidata_dj/bigdata/columns/'+self.target_type.split('.')[-1]+'.json').read())


    def post_process(self):
        if self.import_to_redshift():
            self.cleanup()

    @property
    def s3_key(self):
        return self.filename.split('/')[-1]

    def upload_to_s3(self):
        if self.uploaded_to_s3_at and self.s3_filename:
            return self.s3_filename

        if not self.on_disk: return False

        result = upload_s3_senddata_backup(self.filename, self.s3_key)
        if result:
            self.s3_filename = result
            self.uploaded_to_s3_at = timezone.now()
            self.save()
            return self.s3_filename

    @classmethod
    def update_exists_on_s3(cls):
        from mobovidata_dj.taskapp.utils import s3_backup_connection
        bucket = s3_backup_connection().get_bucket(settings.S3_SENDDATA_BACKUP_BUCKET)
        for key in bucket.list():
            updated = cls.objects.filter(filename__endswith=key.key
                               ).update(
                    s3_filename=key.key,
                    uploaded_to_s3_at=key.last_modified
                    )
            print(updated)

    @property
    def redshift_table(self):
        return ('responsys.%s' %
               self.target_type.split('.')[-1].lower()
                .replace('email', 'email_'))

    def import_to_redshift(self):
        from mobovidata_dj.bigdata.utils import get_redshift_connection
        if not self.upload_to_s3():
            print('Cant upload to s3, skipping')
            return False
        # Only run Redshift commands on production
        if os.environ.get('ENV_TYPE') != 'production':
            return False
        columns = self.read_columns_from_json()
        if not columns:
            log.info('import_to_redshift: Skipping empty file: %s' %
                     self.filename)
            return
        statement = """
        COPY %s
        FROM 's3://%s/%s'
        TIMEFORMAT 'DD-MON-YYYY HH:MI:SS'
        CREDENTIALS 'aws_access_key_id=%s;aws_secret_access_key=%s'
        COMPUPDATE OFF STATUPDATE OFF
        REGION 'us-east-1' CSV ignoreheader 1;
        """ % (
            self.redshift_table,
            settings.S3_SENDDATA_BACKUP_BUCKET,
            self.s3_filename,
            settings.S3_BACKUP_KEY,
            settings.S3_BACKUP_SECRET)
        cnx = get_redshift_connection()
        try:
            print 'importing into redshift: ', self.redshift_table, self.s3_filename
            cursor = cnx.cursor()
            self.redshift_result = cursor.execute(statement)
            cursor.execute("SELECT COUNT(*) FROM %s" % self.redshift_table)
            print cursor.fetchone(), 'rows imported'
            cnx.commit()
            success = True
        except Exception as e:
            self.redshift_result = str(e)
            success = False
        cnx.close()

        self.import_to_redshift_at = timezone.now()
        self.save()
        return success

    @property
    def _redshift_create_statement_file(self):
        return ('./mobovidata_dj/bigdata/redshift_schema/create-%s.txt' %
                self.redshift_table)

    def _build_redshift_create_statement(self):
        """ Creating a redshift table requires developer intervention --
            First, run this method, it will create a file holding a
            CREATE statement in the data/redshift_schema folder;
            Then, you must edit it by hand and fix the column types.
            Finally, run the query on redshift to create the table.
        """
        if not self.upload_to_s3():
            return False
        header = open(self.filename, 'rb').readline().lower()
        columns = [c.strip().strip('"') for c in header.split(',') if c]
        if not columns:
            return

        _types = {
            # Defaults to varchar(255) if not specified
            # (or TIMESTAMP if endswith '_dt')
            'event_type_id': 'integer',
            'account_id': 'integer',
            'list_id': 'integer',
            'riid': 'integer',
            'campaign_id': 'integer',
            'launch_id': 'integer',
            'email_format': 'varchar(1)',
            'offer_url': 'varchar(1024)'
        }
        output = 'CREATE TABLE %s (' % self.redshift_table
        for col in columns:
            if col.endswith('_dt'):
                _type = 'TIMESTAMP'
            else:
                _type = _types.get(col, 'varchar(255)')
            output += '\n  %s %s' % (col, _type)
            if col != columns[-1]:
                output += ','
        output += ');\n'
        with open(self._redshift_create_statement_file, 'w+') as fh:
            fh.write(output)
        return output

    @classmethod
    def _build_all_redshift_create_statements(cls):
        """ Quick and dirty helper utility for building all the responsys
        textfiles """
        from mobovidata_dj.bigdata.models import EMAIL_MODELS
        _types = [CSVImport.objects.filter(target_type=m._meta.label) for m in EMAIL_MODELS]
        for results in _types:
            for instance in results:
                if os.path.exists(instance._redshift_create_statement_file):
                    continue
                statement = instance._build_redshift_create_statement()
                if statement:
                    print statement
                    break

    def cleanup(self):
        # Is it already missing?
        if not self.on_disk:
            return True

        # Only clean up successfuly backed-up rows
        if self.status == 'error':
            return False

        # Only clean up if it's backed up to S3
        if not self.s3_filename:
            return False

        # Don't clean it up unless its 2wks old, or else
        # responsys rsync will download it again
        keep_window = timedelta(days=14)
        keep_date = timezone.now() - keep_window
        if self.discovered_at >= keep_date:
            return False

        # So it exists, it's on S3, it's 2wks old
        os.unlink(self.filename)

        # And cleanup that pesky _counts file
        count_path = '%s._counts' % self.filename
        if os.path.exists(count_path):
            os.unlink(count_path)


class CSVImportError(models.Model):
    at = models.DateTimeField(auto_now_add=True)
    csv = models.ForeignKey(CSVImport, null=True, blank=True)
    row = models.PositiveIntegerField(null=True, blank=True)
    error = models.TextField()
    data = models.TextField()
