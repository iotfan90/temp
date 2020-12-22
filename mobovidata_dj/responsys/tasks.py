import csv
import time
import zipfile

from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime
from django.core.cache import cache
from django.utils import timezone

from .connect import ResponsysFtpConnect
from .models import (NetPromoterScore, OptedOutEmails, ResponsysCredential,
                     RiidEmail)
from .utils import get_responsys_token, ResponsysApi, ResponsysUnbounceEvent
from .views import UnsubForm
from mobovidata_dj.webhooks.models import Dojomojo, Unbounce

logger = get_task_logger(__name__)


@shared_task(ignore_results=True)
def get_update_responsys_token():
    """
    Creates/updates the responsys API token
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
    logger.info('Updated Access Token')


@shared_task(ignore_results=True)
def drop_and_load_opt_out_emails_table():
    OptedOutEmails.objects.load_optout_list()


# @shared_task(ignore_results=True)
# def update_subscriptions_status():
#     e = Extract()
#     paths = e.extract(['54084_OPT_IN', '54084_OPT_OUT'])
#     all_paths = []
#     for v in paths.itervalues():
#         all_paths += v
#     OptInOutLoad().load(all_paths)


@shared_task(ignore_results=True)
def check_cache(cache_key='pending_responsys_requests:get_riids'):
    """
    Checks for failed get_riids calls and reruns them
    @param str cache_key: name of key in cache to fetch
    @return: void
    """
    if cache.get(cache_key):
        pending_requests = []
        for r in cache.get(cache_key):
            email_address = r.get('email_address', False)
            print 'Found email %s' % email_address
            if email_address:
                response = ResponsysApi().get_riids(email_address)
                print response.status_code

                if response.status_code == 503:
                    pending_requests.append(r)
                elif response.status_code == 404:
                    riids = []
                elif response.status_code != 200:
                    continue
                else:
                    riids = UnsubForm().parse_get_riids_response(response)

                if len(riids) == 0 or r.get('EMAIL_PERMISSION_STATUS_', False):
                    UnsubForm().opt_out_email(email_address, contact_list='TEST_CONTACT_LIST')
                else:
                    print 'No updates made'
                if len(riids) != 0:
                    UnsubForm().update_email_preferences_table(riids, r)
                    UnsubForm().update_email_preferences_feedback_table(riids, r)

        cache.set(cache_key, pending_requests)
    else:
        print 'Key not found'


@shared_task(ignore_results=True)
def update_riid_email_table(remote_path=None):
    """
    Updates RiidEmail table with RIIDs and customer emails from Responsys CONTACT_LIST
    @return: void
    """
    if not remote_path:
        date_suffix = datetime.now().strftime('%Y%m%d')
        remote_path = '/home/cli/wirelessemp_scp/download/RIID_EMAIL%s.csv.zip' % date_suffix
        csv_file_path = './static/RIID_EMAIL%s.csv' % date_suffix
    else:
        csv_file_path = './static/%s' % remote_path.replace('.zip', '')
        remote_path = '/home/cli/wirelessemp_scp/download/%s' % remote_path
    local_path = './static/riid_email_update.csv.zip'
    max_retries = 3
    # Download file from Responsys
    for _ in xrange(max_retries):
        try:
            ResponsysFtpConnect().download_file(remote_path, local_path)
            break
        except Exception as ex:
            print 'Error while downloading file: %s', ex
    time.sleep(5)
    # Unzip file
    zip_ref = zipfile.ZipFile('./static/riid_email_update.csv.zip', 'r')
    zip_ref.extractall('./static/')
    # Import into table
    with open(csv_file_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            RiidEmail.objects.update_or_create(
                riid=row['RIID_'],
                defaults={'email': row['EMAIL_ADDRESS_']}
            )


@shared_task(ignore_results=True)
def upload_nps_responsys():
    """
    Upload NetPromoterScore table to Responsys
    @return: void
    """
    # Dump NetPromoterScore data into CSV
    with open('./static/net_promoter_scores.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile)
        fields = [field.name for field in NetPromoterScore._meta.fields]
        writer.writerow(fields)
        for values in NetPromoterScore.objects.all().values_list():
            row = []
            for v in values:
                if isinstance(v, datetime):
                    row.append(v.strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    row.append(v)
            writer.writerow(row)

    # Upload CSV to Responsys
    remote_path = './download/net_promoter_scores.csv'
    local_path = './static/net_promoter_scores.csv'
    ResponsysFtpConnect().upload_file(remote_path, local_path)


@shared_task(ignore_results=True)
def upload_dojomojo_to_responsys():
    """
    Upload Dojomojo results to Responsys
    @return: void
    """
    try:
        while Dojomojo.objects.filter(status=Dojomojo.UNPROCESSED).exists():
            r_api = ResponsysApi()
            field_names = ['email_address_', 'ACQ_SOURCE', 'ACQ_CAMPAIGN']

            dojomojos = (Dojomojo.objects.filter(status=Dojomojo.UNPROCESSED)
                         .values_list('pk', 'email', 'campaign_name')[:200])
            dojomojos_pks = [x[0] for x in dojomojos]
            records = [[x[1], 'DojoMojo', x[2]] for x in dojomojos]

            response = r_api.merge_list_members(field_names, records,
                                                match1='EMAIL_ADDRESS_',
                                                match2='')
            riids, errors = ResponsysApi.get_riids_from_response(response)

            if response.status_code == 200 and not errors:
                (Dojomojo.objects.filter(pk__in=dojomojos_pks)
                 .update(status=Dojomojo.PROCESSED))
            else:
                (Dojomojo.objects.filter(pk__in=dojomojos_pks)
                 .update(status=Dojomojo.ERROR))
                logger.error('[Responsys] Merge list member failed: %s', errors,
                             extra=locals())

    except Exception as e:
        logger.exception('[Responsys] Merge list member failed.',
                         extra=locals())


@shared_task(ignore_results=True)
def upload_unbounce_to_responsys():
    """
    Upload Unbounce results to Responsys
    @return: void
    """
    try:
        while Unbounce.objects.filter(status=Unbounce.UNPROCESSED).exists():
            r_api = ResponsysApi(list_name='CONTACT_LIST_STAGING')
            field_names = ['email_address_']

            unbounces = (Unbounce.objects.filter(status=Unbounce.UNPROCESSED)
                         .values_list('pk', 'email_address')[:200])
            unbounces_pks = [x[0] for x in unbounces]
            records = [[x[1], ] for x in unbounces]

            response = r_api.merge_list_members(field_names, records,
                                                match1='EMAIL_ADDRESS_',
                                                match2='')

            riids, errors = ResponsysApi.get_riids_from_response(response)

            if response.status_code == 200 and not errors:
                custom_event = ResponsysUnbounceEvent()
                emails = [item for sublist in records for item in sublist]
                data = zip(riids, emails)
                event_response = custom_event.send(data)
                event_riids, event_errors = custom_event.get_riids_from_response(event_response)
                if event_response.status_code == 200 and not event_errors:
                    (Unbounce.objects.filter(pk__in=unbounces_pks)
                     .update(status=Unbounce.PROCESSED,
                             date_processed=timezone.now()))
                else:
                    (Unbounce.objects.filter(pk__in=unbounces_pks)
                     .update(status=Unbounce.ERROR,
                             date_processed=timezone.now()))
                    logger.error('[Responsys] Trigger custom event failed: %s',
                                 errors,
                                 extra=locals())
            else:
                (Unbounce.objects.filter(pk__in=unbounces_pks)
                 .update(status=Unbounce.ERROR, date_processed=timezone.now()))
                logger.error('[Responsys] Merge list member failed: %s', errors,
                    extra=locals())

    except Exception as e:
        logger.exception('[Responsys] Merge list member failed.',
                         extra=locals())
