from datetime import datetime, timedelta
from django.db.models import Q, Max
from hashlib import md5

from .models import CustomerId, CustomerIdOrderId
from celery import shared_task
from celery.utils.log import get_task_logger
from mobovidata_dj.ltv.views import update_daily_orders
from modjento.models import SalesFlatOrder


def get_orders_start_date(days_offset=30):
    """
    Finds the date of the most recently recorded order in mobovidata and returns a date 3 days before that.
    This date is used as the starting point from which we update the other LTV tables.
    :type days_offset: int()
    """
    try:
        max_date = CustomerIdOrderId.objects.all().aggregate(Max('created_at'))
        max_date = max_date.get('created_at__max', datetime.today())
        start_date = max_date - timedelta(days=days_offset)
    except TypeError:
        start_date = datetime.today() - timedelta(days=days_offset)
    return start_date


logger = get_task_logger(__name__)


@shared_task(ignore_results=True)
def process_new_orders(start_date=None, num_days=45):
    """
    :type start_date: datetime.datetime()
    :type num_days: int()
    """
    if not start_date:
        start_date = get_orders_start_date()
    end_date = start_date + timedelta(days=num_days)
    print 'Processing orders from %s to %s' % (start_date, end_date)
    recent_orders = SalesFlatOrder.objects.filter(
        ~Q(status='canceled') | ~Q(status='closed'),
        updated_at__gte=start_date,
        updated_at__lte=end_date,
        store_id=2,
        admin_email__isnull=True,
        base_grand_total__gt=0
    ).values(
        'increment_id',
        'created_at',
        'updated_at',
        'customer_email',
        'store_id',
        'base_grand_total'
    ).order_by('created_at')

    order_ids = [long(o['increment_id']) for o in recent_orders]
    existing_orders = CustomerIdOrderId.objects.filter(order_id__in=order_ids)
    existing_orders = [o.order_id for o in existing_orders]

    new_orders = [o for o in recent_orders if
                  long(o['increment_id']) not in existing_orders]
    errors = []
    added_orders = []
    for i, o in enumerate(new_orders):
        email = o.get('customer_email', False)
        if not email:
            errors.append(o)
            continue
        email = email.lower()
        try:
            mdfive = md5(email).hexdigest()
        except:
            errors.append(o)
            continue
        # Try to get customer using email
        repeat_customer = 1
        new_customer = False
        customer = CustomerId.objects.filter(email=email)
        # Sometimes Magento will log an order with no created_at. When this happens, use updated_at instead.
        if not o['created_at']:
            print 'created_at not found'
            o['created_at'] = o['updated_at']
        if not o['created_at']:
            errors.append(o)
            continue
        if not customer.exists():
            # Not found, try to get customer using order id before creating new record
            customer = CustomerId.objects.filter(
                first_order_id=o['increment_id'])
        if not customer.exists():
            # Create new customer
            new_customer = True
            customer = CustomerId(
                md5=mdfive,
                first_order_id=o['increment_id'],
                first_order_dt=o['created_at'],
                num_orders=1,
                email=email,
            )
            repeat_customer = 0
        if not new_customer:
            customer = customer[0]
            customer.num_orders = customer.num_orders + 1
        existing_order = CustomerIdOrderId.objects.filter(
            order_id=o['increment_id'])
        if not existing_order.exists():
            customer.save()
            new_order = CustomerIdOrderId(
                order_id=o['increment_id'],
                customer=customer,
                created_at=o['created_at'],
                repeat_customer=repeat_customer,
                order_grand_total=o['base_grand_total']
            )
            new_order.save()
            added_orders.append(new_order)
    return len(added_orders), len(errors)


@shared_task(ignore_results=True)
def repeat_customers_cache():
    update_daily_orders()
