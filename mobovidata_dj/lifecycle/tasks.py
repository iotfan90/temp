import csv

from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta
from django.core.cache import cache
from django.utils import timezone

from .models import Campaign, ShippingStatusTracking, ProductReviewEntity
from .views import (CustomersCanceledOrder, OrdersReviews,
                    SendOrderConfirmationEmail, SendShippingConfirmationEmail)
from mobovidata_dj.analytics.models import CustomerLifecycleTracking
from mobovidata_dj.responsys.connect import ResponsysFtpConnect
from mobovidata_dj.responsys.utils import ResponsysApi
from modjento.models import SalesFlatOrder

logger = get_task_logger(__name__)


@shared_task(ignore_results=True)
def run_campaigns():
    """
    Celery task to run all campaigns. This is 100% sequential for now, but can
    be split into subtasks if/as needed (e.g, to parallelize I/O heavy tasks
    like mass email sending or distribute load between cores & machines).
    """
    for campaign in Campaign.objects.all():
        # There are two ways to go about it:
        # - ask the components to do their tasks themselves (more OO)
        # - ask the components for data (and small processing) and run the process separately
        #  (easier to parallelize)
        #
        # A third option would be to factor the task of running the pipleline into a separate
        #  component that could have different implementations (parallel and not, strategy pattern)
        #  But we'll stick with what's the simplest for now.
        logger.debug("Running campaign '%s' [id=%d]" % (campaign.name, campaign.id))
        # Check to make sure no other campaign logs exist for this campaign in the last 5 minutes
        run_campaign.delay(campaign.id)


@shared_task(ignore_results=True)
def run_campaign(campaign_id):
    campaign_cache = 'campaign_run:%s' % campaign_id
    last_run = cache.get(campaign_cache)
    now = datetime.now()
    if last_run:
        return 'continue on...'
    cache.set(campaign_cache, now, 60*5)
    campaign = Campaign.objects.get(pk=campaign_id)
    campaign.run()


@shared_task(ignore_results=True)
def run_order_confirmation():
    """
    Celery task to find orders in past 5 minutes and send order confirmation emails.
    """
    campaign_cache = 'campaign_run:order_confirmation'
    last_run = cache.get(campaign_cache)
    now = datetime.now()
    status = cache.get('campaign_run_status:order_confirmation')
    if last_run:
        time_since_last_run = now - last_run
        minutes_since = time_since_last_run.seconds / 60
        # If the process was run within 5 minutes, we should return so the caller can move on to the next campaign
        if minutes_since < 5:
            return 'continue on...'
        if status == 'active':
            # if status is pending we don't want to queue the task
            return 'continue on...'
    cache.set('campaign_run_status:order_confirmation', 'active', 60)
    SendOrderConfirmationEmail().run_order_confirmation()
    cache.set('campaign_run_status:order_confirmation', 'complete', 60)
    cache.set(campaign_cache, now, None)


@shared_task(ignore_results=True)
def run_search_abandon():
    """
    Celery task finds customers who have search abandoned and sends them an email
    """
    campaign = Campaign.objects.get(name='CO_Search_Abandon_1')
    customers = campaign.initial_customer_set()
    customer_data = {c: {} for c in customers}
    for f in campaign.filters.all():
        customers, customer_data = f.filter(customers, customer_data)
    campaign.sender.send(customers, customer_data)


@shared_task(ignore_results=True)
def reset_cart_abandon_lifecycle_stage():
    """
    Changes funnel_step to 0 and lifecycle_messaging_stage to 0 for abandoned
    carts with more than 2 days since last
    update.
    """
    dt_now = timezone.now()
    dt_threshold = dt_now - timedelta(days=2)
    CustomerLifecycleTracking.objects.filter(
        modified_dt__lte=dt_threshold,
        funnel_step__gte=1000
    ).update(lifecycle_messaging_stage=0, funnel_step=0)


@shared_task(ignore_results=True)
def exclude_canceled_order_email():
    """
    Celery task to exclude customer's email whose order has been canceled
    """
    CustomersCanceledOrder().exclude_canceled_order()


@shared_task(ignore_results=True)
def run_order_review():
    """
    Send product review emails to customers
    """
    OrdersReviews().send_review_emails()


@shared_task()
def run_shipping_confirmation():
    """
    Celery task to find customers whose orders have shipped and sends a
    shipping confirmation email if they have not been sent one already.
    """
    SendShippingConfirmationEmail().run_shipping_confirmation()


@shared_task()
def run_nps_emails():
    """
    Runs NPS emails task that sends these emails to customers.
    """
    campaign_cache = 'campaign_run:nps'
    last_run = cache.get(campaign_cache)
    now = datetime.now()
    status = cache.get('campaign_run_status:nps')
    if last_run:
        time_since_last_run = now - last_run
        minutes_since = time_since_last_run.seconds / 60
        # If the process was run within 5 minutes, we should return so the caller can move on to the next campaign
        if minutes_since < 24:
            return 'continue on...'
        if status == 'active':
            # if status is pending we don't want to queue the task
            return 'continue on...'
    cache.set('campaign_run_status:nps', 'active', 60)
    ShippingStatusTracking.send_nps_emails()
    cache.set('campaign_run_status:nps', 'complete', 60)
    cache.set(campaign_cache, now, None)


@shared_task()
def run_review_emails():
    """
    Run product review emails
    """
    from mobovidata_dj.lifecycle.views import OrdersReviews
    campaign_cache = 'campaign_run:review'
    last_run = cache.get(campaign_cache)
    now = datetime.now()
    status = cache.get('campaign_run_status:review')
    if last_run:
        time_since_last_run = now - last_run
        minutes_since = time_since_last_run.seconds / 60
        # If the process was run within 5 minutes, we should return so the caller can move on to the next campaign
        if minutes_since < 24:
            return 'continue on...'
        if status == 'active':
            # if status is pending we don't want to queue the task
            return 'continue on...'
    cache.set('campaign_run_status:review', 'active', 60)
    OrdersReviews().send_review_emails()
    cache.set('campaign_run_status:review', 'complete', 60)
    cache.set(campaign_cache, now, None)


@shared_task()
def check_upload_reviews_responsys():
    campaign_cache = 'reviews_upload_status:lastRun'
    last_run = cache.get(campaign_cache)
    now = datetime.now()
    status = cache.get('reviews_upload_status:status')
    if last_run:
        time_since_last_run = now - last_run
        # If the process was run within 5 minutes, we should return so the caller can move on to the next campaign
        if time_since_last_run.days == 0:
            return 'continue on...'
        if status == 'active':
            # if status is pending we don't want to queue the task
            return 'continue on...'
    cache.set('reviews_upload_status:status', 'active', 60)
    rg_fields = [each.name for each in ProductReviewEntity._meta.fields]
    with open('./static/product_reviews.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(rg_fields)
        for obj in ProductReviewEntity.objects.all():
            writer.writerow([
                obj.id,
                obj.email,
                obj.order_id,
                obj.product_id,
                obj.rating,
                obj.price_paid,
                obj.review_title,
                obj.review_content,
                obj.nickname,
                obj.created_dt.strftime('%Y-%m-%d %H:%M:%S')])
    remote_path = './download/product_reviews.csv'
    local_path = './static/product_reviews.csv'
    r_ftp = ResponsysFtpConnect()
    r_ftp.upload_file(remote_path, local_path)
    r_ftp.close_connection()
    cache.set('reviews_upload_status:status', 'complete', 1224)
    cache.set(campaign_cache, now, None)


@shared_task()
def check_upload_shipping_status_responsys():
    campaign_cache = 'shipping_status:lastRun'
    last_run = cache.get(campaign_cache)
    now = datetime.now()
    status = cache.get('shipping_status:status')
    if last_run:
        time_since_last_run = now - last_run
        # If the process was run within 5 minutes, we should return so the caller can move on to the next campaign
        if time_since_last_run.days == 0:
            return 'continue on...'
        if status == 'active':
            # if status is pending we don't want to queue the task
            return 'continue on...'
    cache.set('shipping_status:status', 'active', 60)
    upload_shipping_status_responsys()
    cache.set('shipping_status:status', 'complete', 1224)
    cache.set(campaign_cache, now, None)


def upload_shipping_status_responsys():
    """
    Post orders with event not equal to 'Delivered' to Responsys with RIID
    """
    # Column names
    rg_fields = [each.name for each in ShippingStatusTracking._meta.fields]
    rg_fields.append('riid')
    # Map order id's to customer email addresses
    rg_oids = [oid[0] for oid in ShippingStatusTracking.objects.exclude(event='Delivered').values_list('order_id')]
    rg_emails = map(lambda x: x[0], list([
        SalesFlatOrder.objects.filter(increment_id__in=rg_oids).values_list('customer_email')][0]))
    mp_oid_email = dict(zip(rg_oids, rg_emails))
    # Map RIID to customer email addresses
    mp_riid_email = ResponsysApi().get_riid_from_email(mp_oid_email.values())
    with open('./static/shipping_status.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(rg_fields)
        for obj in ShippingStatusTracking.objects.exclude(event='Delivered'):
            writer.writerow([
                obj.order_id, obj.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                obj.event, obj.courier, obj.tracking_number,
                obj.confirmation_sent, obj.nps_sent, obj.product_review_sent,
                mp_riid_email.get(mp_oid_email.get(obj.order_id))
            ])

    # Upload CSV to Responsys
    remote_path = './download/shipping_status.csv'
    local_path = './static/shipping_status.csv'
    r_ftp = ResponsysFtpConnect()
    r_ftp.upload_file(remote_path, local_path)
    r_ftp.close_connection()
