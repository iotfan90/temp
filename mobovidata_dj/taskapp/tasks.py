import grp
import gzip
import os
import pwd
import shutil
import subprocess

from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

from .utils import s3_backup_connection, upload_s3_sql_backup
from mobovidata_dj.taskapp.models import BackupLog
from mobovidata_dj.emails.models import CSVImport

log = get_task_logger(__name__)


@shared_task(ignore_results=True)
def backup_to_s3():
    backup_log = BackupLog.objects.create()
    try:
        backup_log.output = backup_sql_to_s3()
        backup_log.output += '\n' + backup_senddata_to_s3()
        backup_log.status = 'success'
    except Exception as e:
        backup_log.status = 'error'
        backup_log.output = (backup_log.output or '') + "\n%s" % e
    backup_log.finished_at = timezone.now()
    backup_log.save()
    return '%s: %s' % (backup_log.status, backup_log.output)


@shared_task(ignore_results=True)
def backup_sql_to_s3():
    backup_file = './data/backup.sql'
    backup_gz = '%s.gzip' % backup_file

    DT_FORMAT = '%Y-%m-%d_%H:%M:%S.gzip'
    target_fn = datetime.utcnow().strftime(DT_FORMAT)

    # Make the DB dumps

    # BELOW: mysqldump method with nonblocking/single-transaction
    with open('./data/.my.cnf', 'w+') as fh:
        fh.write("[mysqldump]\npassword=%s" %
                 settings.DATABASES['default']['PASSWORD'])
    CMD = "mysqldump --defaults-file=./data/.my.cnf --single-transaction --quick -u %s -h %s -P %s %s > %s" % (
        settings.DATABASES['default']['USER'],
        settings.DATABASES['default']['HOST'],
        settings.DATABASES['default']['PORT'],
        settings.DATABASES['default']['NAME'],
        backup_file
    )
    subprocess.call(CMD, shell=True)
    os.unlink('./data/.my.cnf')

    # Alternative -- this is the django dumpdata command, but it doesnt
    # work in mobovidata because of an undetermined issue with the
    # responsys + lifecycle apps
    """
    EXCLUDES = ['bigdata', 'modjento', 'corsheaders']
    backup_file = './data/backup.json'
    backup_gz = '%s.gzip'%backup_file

    management.call_command('dumpdata', exclude=EXCLUDES, output=backup_file)
    """

    # gzip the file
    with open(backup_file, 'rb') as f_in, gzip.open(backup_gz, 'wb+') as f_out:
        shutil.copyfileobj(f_in, f_out)

    # Put it on S3
    upload_s3_sql_backup(backup_gz, target_fn)

    uid = pwd.getpwnam("www-data").pw_uid
    gid = grp.getgrnam("www-data").gr_gid
    os.chown(backup_gz, uid, gid)

    # And clean up old backups
    s3 = s3_backup_connection()
    bucket = s3.get_bucket(settings.S3_SQL_BACKUP_BUCKET)
    backups = list(bucket.list())
    deleted = []
    for obj in backups:
        try:
            dtf = datetime.strptime(obj.key, DT_FORMAT)
        except Exception as e:
            log.info("Unable to parse filename: %s, ignoring" % obj.key)
            continue
        age = datetime.utcnow() - dtf
        # Keep everything less than 14 days old, and the first of every month
        # but don't delete ANYTHING if we're less than 10 backups
        if len(backups) > 10 and age > timedelta(days=14) and (dtf.weekday() != 1):
            log.info("DELETING old backup %s" % obj.key)
            deleted.append(obj.key)
            obj.delete()
    return 'SQL Backup OK to %s/%s - deleted %s' % (bucket.name, target_fn, deleted)


@shared_task(ignore_results=True)
def backup_senddata_to_s3():
    ready_to_backup = CSVImport.objects.filter(
         status__in=['success', 'almost', 'partial'],
    )
    path = settings.RESPONSYS_SEND_DATA_PATH['tgt']
    backup_age = datetime.utcnow() - timedelta(days=14)
    files = []
    for m in CSVImport.model_types():
        name = m._meta.label
        on_disk = m.csv_files(path)
        for fn in on_disk:
            key = fn.split('/')[-1]
            find_record = ready_to_backup.filter(filename=fn)

            if find_record.count() == 0: continue

            find_record.get().post_process()

    return 'Senddata Backup OK to %s' % (settings.S3_SENDDATA_BACKUP_BUCKET)
