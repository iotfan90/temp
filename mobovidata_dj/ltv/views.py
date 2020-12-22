import base64
import json

from collections import OrderedDict
from datetime import timedelta, datetime
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.utils.timezone import utc
from pytz import timezone

from .models import CustomerIdOrderId
from modjento.models import SalesFlatOrder


def update_daily_orders(lookback_window=90):
    """
    Stores past 90d of repeat order information in cache. Lookback window is the number of days from today for which
    we want to retrieve data.
    :type lookback_window: int()
    """
    current_time = datetime.utcnow().replace(tzinfo=utc).astimezone(timezone('US/Pacific'))
    start_date = current_time - timedelta(days=lookback_window)
    orders = CustomerIdOrderId.objects.filter(created_at__gte=start_date.strftime('%Y-%m-%d'))

    order_ids = {}
    for o in orders:
        order_ids[o.order_id] = {
            'order_id': o.order_id,
            'order_date': o.created_at.strftime('%Y-%m-%d'),
            'repeat_customer': o.repeat_customer
            }
    rev = SalesFlatOrder.objects.filter(
            increment_id__in=[o for o in order_ids.keys()]
        ).values(
            'increment_id',
            'base_grand_total',
        )
    for o in rev:
        order_ids[long(o['increment_id'])]['base_grand_total'] = o['base_grand_total']
    agg_orders = {}
    for k, v in order_ids.iteritems():
        order_date = v['order_date']
        data = agg_orders.get(order_date, False)
        repeat_customer_rev = v['base_grand_total'] if v['repeat_customer'] == 1 else 0
        if not data:
            data = {
                'revenue': v['base_grand_total'],
                'repeat_customer_revenue': repeat_customer_rev,
                'repeat_customer_orders': v['repeat_customer'],
                'orders': 1
            }
            agg_orders[order_date] = data
        else:
            data['revenue'] += v['base_grand_total']
            data['repeat_customer_revenue'] += repeat_customer_rev
            data['repeat_customer_orders'] += v['repeat_customer']
            data['orders'] += 1
    reorder_data = []
    agg_orders = OrderedDict(sorted(agg_orders.items()))
    for k, v in agg_orders.iteritems():
        v.update({'date': k})
        v['revenue'] = float(v['revenue'])
        v['repeat_customer_revenue'] = float(v['repeat_customer_revenue'])
        v['repeat_customer_orders'] = int(v['repeat_customer_orders'])
        reorder_data.append(v)
    updated_at = datetime.now(timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S')
    cache.set(
        'repeat_customer_report:%s' % lookback_window,
        {'updated_at': updated_at, 'reorder_data': reorder_data},
        60*60*24)
    json_reorder_data = json.dumps({'updated_at': updated_at,
                                    'reorder_data': reorder_data})
    return json_reorder_data


def repeat_customer_report(request):
    """
    Order counts broken down by repeat and new customers for each day
    """
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            if auth[0].lower() == 'basic':
                uname, passwd = base64.b64decode(auth[1]).split(':')
                user = authenticate(username=uname, password=passwd)
                if user is not None and user.is_active:
                    request.user = user
                    repeat_orders = cache.get('repeat_customer_report:90')
                    # repeat_orders = json.loads(repeat_orders)
                    return JsonResponse(repeat_orders, safe=False)
    response = HttpResponse()
    response.status_code = 401
    response['content'] = 'Credentials not authorized. Username: %s, Pass: %s' % (uname, passwd)
    response['WWW-Authenticate'] = 'Basic Auth Protected'

    return response
