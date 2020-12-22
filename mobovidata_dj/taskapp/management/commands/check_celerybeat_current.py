import pytz
from datetime import datetime, timedelta
import os

from django.core.management.base import BaseCommand
from django.core.mail import mail_admins
from django.conf import settings
from django.db import connections
from django.db.models import Max

from mobovidata_dj.lifecycle.models import SenderLog
from mobovidata_dj.responsys.models import ResponsysCredential
from mobovidata_dj.ltv.models import CustomerId, CustomerIdOrderId
from modjento.models import SalesFlatOrder
from mobovidata_dj.responsys.connect import ResponsysFtpConnect


def do_check(function, *args):
    return function(*args)
    # val = callable(function) and function()
    # if max_age:
    #     if isinstance(val, datetime): val = datetime.now(pytz.utc) - val
    #     val = isinstance(val, ( int, float )) and val <= max_age
    # return val


def handle_failure(subject, message):
    if settings.DEBUG:
        print subject
        print message
    else:
        mail_admins(subject, message)


def check_responsys_auth_running():
    # Verify that the Responsys token updates are processing appropriately
    max_age = datetime.now(pytz.utc) - timedelta(seconds=5400)
    age = ResponsysCredential.objects.get().modified_dt
    return age >= max_age


def check_lifecycle_logs(campaign_id):
    # Verify that existing lifecycle emails are firing at the appropriate schedules
    now = datetime.now(pytz.utc)
    last_hour = now - timedelta(hours=1)
    cursor = connections['default'].cursor()
    cursor.execute(
                '''
                select
                    count(*) as num_sends
                from lifecycle_senderlog
                where send_datetime >= %s
                    and send_datetime < %s
                    and campaign_id = %s;
                ''', [
                    last_hour.strftime('%Y-%m-%d %H'),
                    now.strftime('%Y-%m-%d %H'),
                    campaign_id, ])
    results = cursor.fetchall()
    num_sends = results[0][0]
    return True if num_sends > 5 else False

def check_process_new_orders():
    max_age = datetime.now(pytz.utc) - timedelta(hours=24)
    min_age = max_age - timedelta(hours=24)
    latest_updated = CustomerIdOrderId.objects.all().aggregate(Max('created_at')).get('created_at__max')
    print ('latest=%s' % latest_updated)
    if not latest_updated:
        return False
    return latest_updated.strtime('%Y-%m-%d') == max_age.strtime('%Y-%m-%d')

def check_make_feeds():
    now = datetime.now()
    max_age = now - timedelta(hours=24)
    fb_feeds = settings.FACEBOOK_FEED['feed_name']
    fb_last_modified = datetime.fromtimestamp(os.path.getmtime(fb_feeds))

    r_name = 'resp_co_com.csv'
    r_feeds = os.path.join(settings.RESPONSYS_FEED['destination'], r_name)
    rftp = ResponsysFtpConnect()
    r_has_file = rftp.get_modified_date(r_feeds)[0]
    r_last_modified = rftp.get_modified_date(r_feeds)[1]
    print ('Check make feeds: responsys feed last modified at %s' % r_last_modified)
    print ('Check make feeds: fb feed last modified at %s' % fb_last_modified)

    if not os.path.isfile(fb_feeds) or not r_has_file:
        return False
    return fb_last_modified >= max_age and r_last_modified >= max_age


def check_lifecycle_success(days=7):
    """
    Gets success rates (successful sends / total sends) for each campaign
    within specified timespan (defaults to 1 week)
    Returns True if previous day's send rate is greater than or equal to
    50% of lowest nonzero success rate of week prior, False otherwise.
    """
    time_window = datetime.now() - timedelta(days=days)
    success_report = {}
    failing_campaigns = []
    campaign_ids = range(2, 16)
    for cp_id in campaign_ids:
        one_week_logs = SenderLog.objects.filter(send_datetime__gte=time_window, campaign_id=cp_id)
        success_rates = [float(logs.sends_successful) / logs.sends_total for logs in one_week_logs]
        success_report.update({
            'Campaign %s' % cp_id: success_rates
        })

        THRESHOLD = min(filter(lambda y: y != 0, success_rates)) * 0.5

        one_day_ago = datetime.now() - timedelta(days=1)
        yesterday_logs = SenderLog.objects.filter(send_datetime__gte=one_day_ago, campaign_id=cp_id)
        rates = [float(logs.sends_successful) / logs.sends_total for logs in yesterday_logs]
        is_successful = all(map(lambda x: x <= THRESHOLD, rates))
        if not is_successful:
            failing_campaigns.append(cp_id)

    return True if not failing_campaigns else False


class Command(BaseCommand):
    help = 'Checks for outdated CeleryBeat tasks'

    def handle(self, *args, **options):
        # Checks is a dictionary of Name => CheckFunc
        # CheckFunc can be a boolean function, or a tuple of (func, max_age)
        # If max_age is defined, Func should return either a int/float of
        # seconds since last run, or a datetime object of the last run time

        checks = {
            # 'some-boolean-check': (True, ),
            # 'some-100-less-than-3600-check': (lambda: 100, 3600)
            # 'some-now-is-this-hour-check': (lambda: datetime.now(), 3600)
            'cart_abandon_1': (check_lifecycle_logs, 2),
            'cart_abandon_2': (check_lifecycle_logs, 3),
            'cart_abandon_3': (check_lifecycle_logs, 4),
            'browse_abandon_1': (check_lifecycle_logs, 5),
            'browse_abandon_2': (check_lifecycle_logs, 6),
            'browse_abandon_3': (check_lifecycle_logs, 7),
            'browse_abandon_4': (check_lifecycle_logs, 8),
            'cart_abandon_day2': (check_lifecycle_logs, 9),
            'cart_abandon_day3': (check_lifecycle_logs, 10),
            'cart_abandon_day4': (check_lifecycle_logs, 11),
            'browse_abandon_1_nopdp': (check_lifecycle_logs, 12),
            'browse_abandon_2_nopdp': (check_lifecycle_logs, 13),
            'browse_abandon_3_nopdp': (check_lifecycle_logs, 14),
            'browse_abandon_4_nopdp': (check_lifecycle_logs, 15),
            'responsys-auth-running': (check_responsys_auth_running, ),
            'process-new-orders': (check_process_new_orders, ),
            'make_feeds': (check_make_feeds, ),
            'lifecycle_email_success': (check_lifecycle_success, ),
        }

        failures = []

        for name, args in checks.items():
            result = do_check(*args)
            if not result:
                failures.append(name)

        if failures:
            handle_failure(
                '*** WARNING *** Celerybeat tasks are outdated:',
                """ The following celery tasks are not running on schedule: %s """ % failures
            )
