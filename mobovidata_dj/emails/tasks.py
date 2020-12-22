import csv
import glob
import gzip
import json
import os
import subprocess
import zipfile

from celery import shared_task
from celery.utils.log import get_task_logger
from collections import defaultdict
from datetime import datetime
from django.conf import settings

from mobovidata_dj.bigdata.utils import get_redshift_connection
from mobovidata_dj.emails.models import CSVImport
from mobovidata_dj.taskapp.utils import upload_s3_senddata_backup


log = get_task_logger(__name__)


@shared_task(ignore_results=True)
def sync_contact_list():
    """
    Celery task to download responsys contact_list.zip
    You must set settings.SEND_DATA_PATH
    """
    cmd_data = dict(
        settings.RESPONSYS_SEND_DATA_PATH,
        key=settings.RESPONSYS_FTP['pkey'],
        user=settings.RESPONSYS_FTP['user'],
        url=settings.RESPONSYS_FTP['url'],
    )
    tgt = settings.RESPONSYS_SEND_DATA_PATH['tgt']

    # Find the latest CONTACT_LIST file
    cmd = "eval $(ssh-agent) && ssh-add {key} ; "
    cmd += "ssh {user}@{url} 'ls -lh download/CED_Data/CONTACT_LIST_*.csv.zip | tail -n1'"
    cmd = cmd.format(**cmd_data)

    get_file = cmd_data['get_file'] = subprocess.check_output(cmd, shell=True).strip().split('/')[-1]
    put_file = cmd_data['put_file'] = os.path.join(tgt, get_file)

    log.info('Found contact_list: %s' % get_file)

    # Delete old zip files to save space
    for fn in glob.glob(os.path.join(tgt, '*.zip')):
        if fn != put_file:
            os.unlink(fn)

    # Download the file if we don't already have it
    if not os.path.exists(put_file):
        cmd = "eval $(ssh-agent) && ssh-add {key} ; "
        cmd += "rsync -r -a -v -x {user}@{url}:download/CED_Data/{get_file} {put_file}"
        cmd = cmd.format(**cmd_data)

        log.info(subprocess.call(cmd, shell=True))
    else:
        log.info('File exists, skipping: %s' % put_file)

    # Extract the .zip
    archive = zipfile.ZipFile(put_file, 'r')
    csv_fn = archive.namelist()[0]
    csv_fh = archive.open(csv_fn)
    out_csv_fn = os.path.join(tgt, csv_fn)
    out_gzip_fn = out_csv_fn+'.gz'
    out_csv_fh = gzip.open(out_gzip_fn, 'w+')

    # Trim the columns
    want_columns = ["RIID_", "CUSTOMER_ID_", "EMAIL_ADDRESS_", "EMAIL_DOMAIN_",
                    "EMAIL_ISP_", "EMAIL_FORMAT_", "EMAIL_PERMISSION_STATUS_",
                    "EMAIL_DELIVERABILITY_STATUS_", "CREATED_DATE_",
                    "MODIFIED_DATE_", "STORE_ID", "FIRST_SUBSCRIBE_DATE",
                    "BRAND_NAME_01", "MODEL_ID_01", "MODEL_NAME_01",
                    "BRAND_NAME_02", "MODEL_ID_02", "MODEL_NAME_02",
                    "BRAND_NAME_03", "MODEL_ID_03", "MODEL_NAME_03"]
    clean_column = lambda s: s.strip('_').lower()
    reader = csv.DictReader(csv_fh)
    writer = csv.DictWriter(out_csv_fh,
                            fieldnames=map(clean_column, want_columns),
                            quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for row in reader:
        output = {clean_column(k): row[k] for k in want_columns}
        try:
            check_date = lambda d: d and datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
            check_date(output['created_date'])
            check_date(output['modified_date'])
            check_date(output['first_subscribe_date'])
        except Exception as e:
            print("INVALID DATES IN ROW:", row)
            print e
            continue
        writer.writerow(output)
    csv_fh.close()
    out_csv_fh.close()

    # Upload to s3
    print('Uploading to s3...', out_gzip_fn)
    upload_s3_senddata_backup(out_gzip_fn)

    # Import new redshift data
    redshift_table = 'responsys.contact_list'
    statement = """
    COPY %s
    FROM 's3://%s/%s'
    TIMEFORMAT 'YYYY-MM-DD HH:MI:SS'
    CREDENTIALS 'aws_access_key_id=%s;aws_secret_access_key=%s'
    COMPUPDATE OFF STATUPDATE OFF
    REGION 'us-east-1' CSV GZIP ignoreheader 1;
    """ % (
        redshift_table,
        settings.S3_SENDDATA_BACKUP_BUCKET,
        out_gzip_fn,
        settings.S3_BACKUP_KEY,
        settings.S3_BACKUP_SECRET)
    cnx = get_redshift_connection()
    try:
        print 'importing into redshift: ', redshift_table, out_gzip_fn
        cursor = cnx.cursor()
        cursor.execute("DELETE FROM responsys.contact_list")
        print cursor.execute(statement)
        cursor.execute("SELECT COUNT(*) FROM %s" % redshift_table)
        print cursor.fetchone(), 'rows imported'
        cnx.commit()
        success = True
    except Exception as e:
        print(e)
        success = False
    cnx.close()
    return success


@shared_task(ignore_results=True)
def discover_send_data():
    """
    Celery task to download and discover new Responsys CSVs
    You must set settings.SEND_DATA_PATH
    """
    cmd_data = dict(
        settings.RESPONSYS_SEND_DATA_PATH,
        key=settings.RESPONSYS_FTP['pkey'],
        user=settings.RESPONSYS_FTP['user'],
        url=settings.RESPONSYS_FTP['url'],
    )

    cmd = "eval $(ssh-agent) && ssh-add {key} ; "
    cmd += "rsync -r -a -v -x {user}@{url}:{dir}/\* {tgt}"
    cmd = cmd.format(**cmd_data)

    log.info(subprocess.call(cmd, shell=True))

    discovered = CSVImport.discover()
    log.info('Successfully discovered: ' +
             json.dumps({k: len(v) for k, v in discovered.items()}, indent=2))


@shared_task(ignore_results=True)
def process_send_data_batch():
    """
    Celery task to import the data of new Responsys CSVs
    You must run Discover first
    """
    pending = CSVImport.get_pending()
    if not pending:
        log.info('Nothing to import.')
        return
    log.info(
        'Importing files: ' +
        json.dumps({k._meta.label: len(v) for k, v in pending.items()},
                   indent=2)
    )
    results = defaultdict(list)
    for m, csvs in pending.items():
        for _cached in csvs:
            csv = CSVImport.objects.get(pk=_cached.pk)
            if csv.status != 'new':
                log.info("""Warning - Job already processing: %s looks like a
                race condition between two running workers, skipping this
                one...""")
                continue

            log.debug('Importing %s...'%csv.filename)
            csv.process(m)
            log.debug(csv.status)
            results[csv.status].append(csv)
            break
    log.info('Processed: '+ json.dumps({
                k: len(v) for k,v in results.items()
            }, indent=2))

process_send_data_batch.predicate = lambda: sum([_type.count() for name, _type
                                                 in CSVImport.get_pending().items()])
