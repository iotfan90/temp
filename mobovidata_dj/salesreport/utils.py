import datetime
import numpy as np
import pytz

from collections import defaultdict
from decimal import *
from django.conf import settings
from django.db import connections
from django.utils.timezone import utc
from pytz import timezone
from scipy import optimize
from sklearn import linear_model

from modjento.models import (CatalogProductEntity, ErpInventoryDelivery,
                             ErpInventoryPurchaseOrderProduct,
                             SalesFlatOrderItem)


def get_product_sales_windows(product_ids, days_before=None, windows=None):
    """
    :param product_ids: list of product ids to include
    :param windows: list of integers representing aggregate sales data to return
    :param days_before: integer, the earliest day
    :returns: {window[product_id]:qty_sold}
    """
    if not days_before:
        days_before = 120
    if not windows:
        windows = [1, 3, 7, 14, 30, 90]
    current_time = datetime.datetime.utcnow().replace(tzinfo=utc).astimezone(pytz.timezone('US/Pacific'))
    date_from = current_time - datetime.timedelta(days=days_before)
    dfrom = date_from.strftime('%Y-%m-%d')
    cursor = connections['magento'].cursor()
    cursor.execute(
    '''
    SELECT item.product_id, date(item.created_at), sum(item.qty_ordered)
    FROM sales_flat_order_item item
    INNER JOIN sales_flat_order odr ON item.order_id=odr.entity_id
    WHERE item.product_id in %s
    AND item.created_at > %s
    AND odr.status != 'canceled'
    GROUP BY item.product_id, date(item.created_at)
    ORDER BY date(item.created_at);
    ''', [
            product_ids,
            dfrom])
    rg_products = [{
                'product_id': product_id,
                'date': date,
                'qty_ordered': qty_ordered,
            } for product_id, date, qty_ordered in cursor.fetchall()]

    rg_products_dates = defaultdict(dict)
    for rg in rg_products:
        d = rg_products_dates[rg.get('date')]
        d[rg.get('product_id')] = float(d.get(rg.get('product_id'), 0) + rg.get('qty_ordered', 0))
    until_today = {}
    sum_until_today = {}
    for day_diff in windows:
        earlier_time = current_time - datetime.timedelta(days=day_diff)
        earlier_day = earlier_time.date()
        sum_that_day = rg_products_dates[earlier_day]
        for p_id, qty in sum_that_day.iteritems():
            sum_until_today[p_id] = sum_until_today.get(p_id, 0) + qty
        until_today[day_diff] = dict(sum_until_today)
    return until_today


def get_weekly_sales(mp_sales_until, product_id, weights=None):
    if not weights:
        weights = settings.PO_DEFAULTS['default_avg_weights']
    week_daily_avgs = get_forecast_daily_avgs(mp_sales_until, product_id)
    return [get_daily_demand(*zip(week_daily_avgs[0], weights)),
            get_daily_demand(*zip(week_daily_avgs[1], weights)),
            get_daily_demand(*zip(week_daily_avgs[2], weights)),
            get_daily_demand(*zip(week_daily_avgs[3], weights))
            ]


def get_weekly_periods(cons, days):
    return [[y+days for y in x] for x in cons]


def get_daily_demand(*args, **kwargs):
    return sum([k * v for k, v in args])


def get_weights(model):
    window_weights = []
    if model.objects.count() > 0:
        weights = model.objects.all().values()[0]
        window_weights.extend([
            weights.get('day_1'),
            weights.get('day_3'),
            weights.get('day_7'),
            weights.get('day_14'),
            weights.get('day_30'),
            weights.get('day_90')
        ])
    else:
        default_weights = settings.PO_DEFAULTS['default_avg_weights']
        window_weights.extend(default_weights)
    return window_weights


def min_rmse(product_ids, mp_sales_until):
    X, y = [], []
    for product_id in product_ids:
        forecast_daily_avgs = get_forecast_daily_avgs(mp_sales_until,
                                                      product_id)
        actual_daily_avgs = get_actual_sales(mp_sales_until, product_id)
        for i in range(4):
            X.append(forecast_daily_avgs[i])
            y.append(actual_daily_avgs[i])
    X, y = np.array(X), np.array(y)

    # ElasticNetCV(Linear model) to minimize RMSE
    # alphas: from 10^(-15) to 10^(9)
    # cv: 10-fold cross validation
    # positive: enforce coefficient to be non-negative
    # max: max iteration times is 5000
    # reg = linear_model.ElasticNetCV(alphas=[10.**i for i in range(-15, 10)],
    #                                 positive=True, cv=10, max_iter=5000)
    # reg.fit(X, y)
    # print('coef=%s' % reg.coef_)
    # return list(reg.coef_)

    bounds = [(0, 1)] * X.shape[1]

    def cost_func(w, X, y):
        return (X.dot(w) - y).sum() / y.size

    def jac_func(w, X, y):
        return (X.dot(w) - y).dot(X) * 2.0 / y.size

    ret = optimize.minimize(cost_func,
                            np.array([0.24, 0.19, 0.1, 0.2, 0.31, 0.1]),
                            args=(X, y), jac=jac_func, bounds=bounds,
                            method='SLSQP')
    return list(ret.x)


def get_forecast_daily_avgs(mp_sales_until, product_id):
    week4_cons = [(7, 8), (8, 10), (10, 14), (14, 21), (21, 37), (37, 97)]
    week3_cons = get_weekly_periods(week4_cons, 7)
    week2_cons = get_weekly_periods(week4_cons, 14)
    week1_cons = get_weekly_periods(week4_cons, 21)
    days_in_between = [1.0, 2.0, 4.0, 7.0, 16.0, 60.0]
    week_cons = [week4_cons, week3_cons, week2_cons, week1_cons]
    week_daily_avgs = []
    for week_con in week_cons:
        week_sales = [mp_sales_until.get(date_pair[1]).get(product_id, 0.0) -
                      mp_sales_until.get(date_pair[0]).get(product_id, 0.0) for date_pair in week_con]
        week_daily_avg = [a / b for a, b in zip(week_sales, days_in_between)]
        week_daily_avgs.append(week_daily_avg)
    return week_daily_avgs


def get_square_errors(mp_sales_until, product_id, weights):
    square_errors = []
    forecast_daily_avgs = get_weekly_sales(mp_sales_until, product_id, weights)
    actual_sales = get_actual_sales(mp_sales_until, product_id)
    for x in xrange(4):
        square_errors.append((forecast_daily_avgs[x] - actual_sales[x])**2)
    return square_errors


def get_actual_sales(mp_sales_until, product_id):
    weekly_cons = [(1, 8), (8, 15), (15, 22), (21, 29)]
    days_in_week = 7.0
    actual_daily_avgs = [(mp_sales_until.get(date_pair[1]).get(
        product_id, .0) - mp_sales_until.get(date_pair[0]).get(product_id, .0)) / days_in_week for date_pair in
                         weekly_cons]
    return actual_daily_avgs


def get_product_ids(date_from=None):
    if not date_from:
        current_time = datetime.datetime.utcnow().replace(tzinfo=utc).astimezone(timezone('US/Pacific'))
        date_from = current_time - datetime.timedelta(days=90)
    rg_visible_ids = CatalogProductEntity.objects.get_visible_ids()
    rg_ids_sold_90 = SalesFlatOrderItem.objects.filter(created_at__gte=date_from).values_list('product_id', flat=True)
    rg_ids_sold_90, rg_visible_ids = set(rg_ids_sold_90), set(rg_visible_ids)
    rg_product_ids = rg_visible_ids.union(rg_visible_ids)
    rg_product_ids = [r for r in rg_product_ids]
    return rg_product_ids


def get_daily_sales(mp_until_today_ordered, product_id, windows=None):
    """
    Get daily sales, total sales and average daily sales for windows like [1,3,7,14,30,90]
    :param mp_until_today_ordered: Ordered Dict with day as key, total sales as value
    :param product_id: integer, product id
    :param windows: list with special days
    :return: daily sales, total sales and average daily sales
    """
    if not windows:
        windows = [1, 3, 7, 14, 30, 90]
    item_info = {}
    windows_sales, window_daily_avg = [], []
    daily_sales = []
    prev_daily_sales = 0
    for day, units_sold_day in mp_until_today_ordered.items():
        if day in windows:
            windows_sales.append(units_sold_day.get(product_id, 0.00))
            day_format = '%s_%s' % ('day', day)
            item_info[day_format] = units_sold_day.get(product_id, 0.00)
        cur_daily_sales = units_sold_day.get(product_id, 0)
        net_daily_sales = cur_daily_sales - prev_daily_sales
        daily_sales.append(net_daily_sales)
        prev_daily_sales = cur_daily_sales
    window_daily_avg.append(windows_sales[0])
    for i in xrange(len(windows_sales) - 1):
        window_daily_avg.append((windows_sales[i+1]-windows_sales[i]) / (windows[i+1] - windows[i]))
    return daily_sales, item_info, window_daily_avg


def get_po_run_rate_old(sale_info, inventory_qty):
    return dict((key, float(inventory_qty / Decimal(value)) if value else 'N/A')
                for key, value in sale_info.iteritems())


def get_item_price(mp_data):
    d_special_price = mp_data.get('special_price', False)
    dt_now = datetime.datetime.utcnow().replace(tzinfo=utc).astimezone(timezone('US/Pacific'))
    dt_from = mp_data.get('special_from_date')
    dt_to = mp_data.get('special_to_date')
    if d_special_price and (
            not dt_from or dt_from <= dt_now) or (
            not dt_to or dt_to >= dt_now):
        price = d_special_price
    else:
        price = mp_data.get('price', Decimal(0.0000))
    return price


def get_product_order_deliveries(rg_product_ids):
    po_products = ErpInventoryPurchaseOrderProduct.objects.filter(
        product_id__in=rg_product_ids,
        purchase_order__status__in=[5, 6]
    ).prefetch_related(
        'purchase_order'
    )
    # Get delivery dates in po_id _ product_id hashed dict
    po_deliveries = ErpInventoryDelivery.objects.filter(
        purchase_order_id__in=[p.purchase_order_id for p in po_products],
        product_id__in=rg_product_ids
    )
    # po_id _ product_id = hash to lookup deliveries
    return {'%s_%s' % (p.purchase_order_id, p.product_id): p.delivery_date for p in po_deliveries}


def get_pending_order(rg_product_ids):
    """
    Gets purchase order information for each sku in the rg_product_ids list.
    :param rg_product_ids:
    :return:
    """
    # Get PO info
    po_products = ErpInventoryPurchaseOrderProduct.objects.filter(
        product_id__in=rg_product_ids,
        purchase_order__status__in=[5, 6]).prefetch_related(
        'purchase_order')
    mp_product_deliveries = get_product_order_deliveries(rg_product_ids)
    oldest_time = datetime.datetime(1990, 9, 24, 0, 26, 52, 985635, pytz.utc).astimezone(timezone('US/Pacific'))
    mp_po_last_date = defaultdict(lambda: oldest_time)
    mp_po_pending = defaultdict(list)
    mp_po_product_qty = defaultdict(int)
    for po_product in po_products:
        po_id = po_product.purchase_order_id
        po_product_id = po_product.product_id
        purchase_on = po_product.purchase_order.purchase_on
        poid_product_id = '%s_%s' % (po_id, po_product_id)
        if po_product.purchase_order.status == 5:
            mp_po_pending[po_product_id].append([po_id, po_product.qty, purchase_on.isoformat()])
        elif po_product.purchase_order.status == 6:
            if mp_po_last_date[po_product_id] < purchase_on and mp_product_deliveries.get(poid_product_id):
                mp_po_last_date[po_product_id] = mp_product_deliveries[poid_product_id]
                mp_po_product_qty[po_product_id] = po_product.qty
            else:
                pass
        else:
            pass
    return [mp_po_pending, mp_po_last_date, mp_po_product_qty]
