import base64
import csv
import datetime
import json
import logging
import math
import pytz

from collections import defaultdict, OrderedDict
from decimal import *
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, JsonResponse
from django.utils.timezone import utc
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin
from pytz import timezone
from scipy.stats import norm

from .models import DailyAvgWeights, ProductQuarantine, AgingInventory
from mobovidata_dj.salesreport.utils import *
from modjento.models import (CatalogCategoryEntityVarchar,
                             CatalogCategoryProductIndex,
                             CataloginventoryStockItem, CatalogProductEntity,
                             EavAttribute, ErpInventorySupplierProduct,
                             SalesFlatOrder, SalesFlatOrderItem)
from supplier_inventory.models import SupplierInventory

logger = logging.getLogger(__name__)


class SalesReport(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'salesreport.html'
    login_url = '/accounts/login'

    def __init__(self):
        """
        :return:
        """
        super(SalesReport, self).__init__()
        self.lead_time = settings.PO_DEFAULTS['lead_time']
        self.days_between = settings.PO_DEFAULTS['days_between']
        self.service_level = settings.PO_DEFAULTS['service_level']

    def get_sales_report(self, *args, **kwargs):
        """
        Get sales report from redis and return to page
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        current_time = datetime.datetime.utcnow().replace(tzinfo=utc).astimezone(timezone('US/Pacific'))
        earlier_time = current_time - datetime.timedelta(days=120)
        product_list = self.prepare_data(earlier_time)
        po_product_list = [product for product in product_list if not product.get('sku').startswith('FPA') and not product.get('sku').startswith('GST')]
        cache.set('poreport:products', json.dumps(po_product_list))
        cache.set('salesreport:products', json.dumps(product_list))
        cache.set(
            'salesreport:updated_dt',
            datetime.datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S')
        )

    def get(self, request, *args, **kwargs):
        """
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        product_list = json.loads(cache.get('salesreport:products'))
        last_updated_dt = cache.get('salesreport:updated_dt')
        page = request.GET.get('page', 1)
        size = request.GET.get('size', 50)
        search = request.GET.get('searchField')
        if search:
            search = json.loads(search)
            search_field = [search_field for search_field in search]
            for search_field in search:
                search_value = search.get(search_field)
                if search_value:
                    product_list = filter(lambda x: str(search_value).upper() in str(x.get(search_field)) or
                                                    str(search_value).lower() in str(x.get(search_field)), product_list)
                else:
                    pass
        st_sort = request.GET.get('sort', '')
        if st_sort:
            b_reverse = st_sort[0] == '-'
            field = st_sort[1:] if b_reverse else st_sort
            product_list.sort(key=lambda x: x[field], reverse=b_reverse)
        try:
            size = int(size)
        except ValueError:
            size = 50
        paginator = Paginator(product_list, size)
        try:
            products = paginator.page(page)

        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)
        if paginator.num_pages > 10:
            if products.number >= 10:
                max_page = products.number + 10 if products.number + 10 < paginator.num_pages else paginator.num_pages
                page_ranges = range(products.number, max_page)
            else:
                page_ranges = range(1, 11)
        else:
            page_ranges = list(paginator.page_range)
        context = {
            # 'products': json.dumps(product_list),
            'last_updated_dt': last_updated_dt,
            'page_products': json.dumps({
                'page': products.object_list,
                'current': products.number,
                'previous': products.has_previous(),
                'next': products.has_next(),
                'last_page': paginator.num_pages,
                'pages': page_ranges
            }),
            'st_sort': st_sort,
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Manually triggering Sales/PO Reports
        :return json object:
        """
        try:
            self.get_sales_report()
        except Exception as e:
            logger.exception(
                msg='There was an error manually refreshing PO report.',
                extra=locals())
            result = {
                'message': 'We were not able to refresh report: %s' % e,
                'success': False,
            }
        else:
            result = {
                'message': 'Report refreshed successfully!',
                'success': True,
            }
        return JsonResponse(result)

    def get_inventory_left(self, qty, num_sold, days):
        if num_sold == 0:
            return 'N/A'
        return float(qty * days / num_sold)

    def get_average_inventory_left(self, run_rates):
        total_rate = 0
        for run_rate in run_rates:
            if isinstance(run_rate, str) and run_rate == 'N/A':
                run_rate = 0
            total_rate += run_rate
        avg_rr = total_rate / len(run_rates)
        return avg_rr

    def get_average_po_run_rate(self, run_rates):
        total_rate = 0
        for run_rate in run_rates:
            if isinstance(run_rate, str) and run_rate == 'N/A':
                run_rate = 0
            total_rate += run_rate
        avg_rr = total_rate / len(run_rates)
        return avg_rr

    def get_margin(self, price, mp_data):
        if price > 0:
            margin = '%s%s' % (round((float(price) - float(mp_data.get('cost', 0.0))) * 100 / float(price), 2), '%')
        else:
            margin = 'Not Available'
        return margin

    def get_daily_avg(self, sales1, sales2, days):
        return float((sales2-sales1)/days)

    def get_standardized_metric_of_service_level(self, service_level):
        return norm.ppf(service_level)

    def get_demand_stdev(self, daily_sales, *args):
        avg = sum(daily_sales) * 1.0 / len(daily_sales)
        variance = map(lambda x: (x - avg) ** 2, daily_sales)
        standard_deviation = math.sqrt(sum(variance) * 1.0 / len(variance))
        return standard_deviation

    def get_vp_stdev_demand(self, stdev_demand, lead_time, days_between):
        return math.sqrt((lead_time+days_between) * (stdev_demand**2))

    def get_vulnerable_demand(self, daily_demand, lead_time, days_between):
        return daily_demand*(lead_time+days_between)

    def get_safety_stock(self, standardized_metric_of_service_level, stdev_of_demand_over_vp):
        return float(standardized_metric_of_service_level) * float(stdev_of_demand_over_vp)

    def get_qty_needed_for_vp(self, safety_stock, demand_for_vp):
        return safety_stock + demand_for_vp

    def get_order_qty(self, is_order, qty_needed_for_vp, qty):
        return qty_needed_for_vp - qty if is_order else 0

    def order_or_not(self, hr_qty, qty_needed_for_vp, qty):
        if hr_qty < 6:
            return False
        else:
            if qty_needed_for_vp >= 10 and qty_needed_for_vp > qty:
                return True
            return False

    def get_order_celling(self, sku, order_qty):
        if sku and sku.upper().startswith('SCR'):
            if order_qty < 50:
                order_celling = int(math.ceil(order_qty / 10.0)) * 10
            else:
                order_celling = int(math.ceil(order_qty / 50.0)) * 50
        else:
            order_celling = int(math.ceil(order_qty / 5.0)) * 5
        return order_celling

    def get_vendor_sku(self, product_ids):
        vendor_sku = ErpInventorySupplierProduct.objects.filter(product_id__in=product_ids)
        vendor_info = vendor_sku.prefetch_related('supplier')
        mp_vendor_skus, mp_vendor_names = defaultdict(list), defaultdict(list)
        vendor_name_list, vendor_sku_pair = set(), defaultdict(dict)
        for item in vendor_info:
            mp_vendor_skus[item.product_id].append(item.supplier_sku)
            mp_vendor_names[item.product_id].append(item.supplier.name)
            vendor_name_list.add(item.supplier.name)
            # Map vendor name and vendor sku for each product for the purchase team
            vendor_sku_pair[item.product_id][item.supplier.name] = item.supplier_sku
        return mp_vendor_skus, mp_vendor_names, vendor_name_list, vendor_sku_pair

    def prepare_data(self, date_from):
        # Get sales for past 120 days, not daily sales, but sales up to date
        rg_product_ids = get_product_ids(date_from)
        units_sold_everyday = get_product_sales_windows(rg_product_ids,
                                                        days_before=120,
                                                        windows=[x for x in xrange(1, 121)])
        # Get pending orders
        pending_order = get_pending_order(rg_product_ids)
        mp_po_pending, mp_po_last_date, mp_po_product_qty = pending_order[0], pending_order[1], pending_order[2]

        mp_brand_models = dict(SalesFlatOrderItem.objects.filter(
            product_id__in=rg_product_ids).values_list('product_id', 'brand_model'))

        rg_product_fields = [
            'entity_id',
            'vendor_sku',
            'name',
            'image',
            'attribute_set',
            'category',
            'price',
            'special_price',
            'special_from_date',
            'special_to_date',
            'cost'
        ]
        mp_values = EavAttribute.objects.get_values(
            rg_product_ids,
            entity_type=4,
            field_names=rg_product_fields,
            json_values=False)
        product_stock = list(CataloginventoryStockItem.objects.filter(product_id__in=rg_product_ids).only(
            'product_id',
            'qty',
            'is_in_stock',
            'backorders'))
        for item in product_stock:
            mp_values[item.product_id].update({
                'qty': int(item.qty),
                'is_in_stock': item.is_in_stock,
                'back_orders': 1 if item.backorders > 0 else 0
            })
        rg_product_category_ids = list(CatalogCategoryProductIndex.objects.filter(
            product_id__in=rg_product_ids
        ).values_list('product_id', 'category_id'))
        ms_category_ids = {category_id: product_id for product_id, category_id in rg_product_category_ids}
        rg_categories = CatalogCategoryEntityVarchar.objects.filter(
            entity_id__in=ms_category_ids.keys(),
            attribute_id=41
        ).values_list('entity_id', 'value')
        mp_categories = {ms_category_ids.get(entity_id): category for entity_id, category in rg_categories}

        vendors = self.get_vendor_sku(rg_product_ids)
        vendor_skus, vendor_names, vendor_name_list, vendor_sku_pair = vendors[0], vendors[1], vendors[2], vendors[3]

        mp_skus = dict(CatalogProductEntity.objects.filter(entity_id__in=rg_product_ids).values_list('entity_id', 'sku'))

        # Get HR qtys from SupplierInventory
        hr_qtys = dict(SupplierInventory.objects.filter(product_id__in=rg_product_ids).values_list('product_id', 'stock'))

        # Get weights for daily avg, default values are [0.24, 0.19, 0.1, 0.2, 0.31, 0.1]
        daily_avg_weights = get_weights(DailyAvgWeights)

        # Get weights to minimize rmse for forecast
        product_ids = set(rg_product_ids)
        min_weights = min_rmse(product_ids, units_sold_everyday)

        # Maintain an ordered dict to get everyday sales
        od_daily_sales = OrderedDict(sorted(units_sold_everyday.items()))

        # Initial product ids and default values to product attributes
        product_list = []
        product_ids_set = set()
        lead_time, days_between, service_level = self.lead_time, self.days_between, self.service_level

        # Prepare data for each product
        for product_id in rg_product_ids:
            if product_id not in product_ids_set:
                product_ids_set.add(product_id)
                data = mp_values.get(product_id, {})
                qty = int(data.get('qty', 0))
                brand_model = mp_brand_models.get(product_id)
                # Get week models for each product
                week_models = get_weekly_sales(units_sold_everyday,
                                               product_id, weights=min_weights)
                # Get square errors
                square_errors = get_square_errors(units_sold_everyday,
                                                  product_id, min_weights)
                # Get daily sales for stdev of demand
                price = get_item_price(data)

                # Get daily sales, total sales and average daily sales for windows [1,3,7,14,30,90]
                daily_sales, item_info, windows_avg = get_daily_sales(od_daily_sales, product_id, windows=[1, 3, 7, 14, 30, 90])

                # Get stdev of demand
                stdev_demand = self.get_demand_stdev(daily_sales)

                # Get forecast daily demand
                daily_demand = get_daily_demand(*zip(daily_avg_weights, windows_avg))

                # Get fields used for forecast
                standardized_metric_of_service_level = self.get_standardized_metric_of_service_level(service_level)
                stdev_of_demand_over_vp = self.get_vp_stdev_demand(stdev_demand, lead_time, days_between)
                demand_for_vp = self.get_vulnerable_demand(daily_demand, lead_time, days_between)
                safety_stock = self.get_safety_stock(standardized_metric_of_service_level, stdev_of_demand_over_vp)
                qty_needed_for_vp = self.get_qty_needed_for_vp(safety_stock, demand_for_vp)
                hr_qty = hr_qtys.get('%s' % product_id, 0)
                is_order = self.order_or_not(hr_qty, qty_needed_for_vp, qty)
                order_qty = self.get_order_qty(is_order, qty_needed_for_vp, qty)
                sku = mp_skus.get(product_id, '')
                order_celling = self.get_order_celling(sku, order_qty)

                # Get inventory left and run rate for sales report and po report
                day_consts = [1., 3., 7., 14., 30., 90.]
                inventory_lefts = dict([(key, self.get_inventory_left(
                    qty, value, const)) for (key, value), const in zip(item_info.items(), day_consts)])
                po_run_rate_old = get_po_run_rate_old(item_info, qty)

                # Current po run rate: qty/daily_demand
                po_run_rate = round(float(qty) / daily_demand, 2) if daily_demand else None

                margin = self.get_margin(price, data)
                pending_po = mp_po_pending.get(product_id, [])
                po_last_date = mp_po_last_date.get(product_id)

                # general product attribute data
                item_info.update({
                    'name': data.get('name', ''),
                    'qty': qty,
                    'brand_model': brand_model,
                    'is_in_stock': data.get('is_in_stock', 0),
                    'back_orders': data.get('back_orders', 0),
                    'base_cost': '%.2f' % data.get('cost', 0.0) or 'N/A',
                    'price': '%.2f' % price,
                    'margin': margin,
                    'image': self.get_image_url(data.get('image', '')),
                    'vendor_sku': vendor_skus.get(product_id, ''),
                    'vendor_name': vendor_names.get(product_id, ''),
                    'attribute_set': mp_categories.get(product_id, ''),
                })

                # po fields not including fb and vp data
                item_info.update({
                    'inventory_days_remain': round(qty / daily_demand, 2) if daily_demand else None,
                    'po_day1_avg': '%.2f' % windows_avg[0],
                    'po_day3_avg': '%.2f' % windows_avg[1],
                    'po_day7_avg': '%.2f' % windows_avg[2],
                    'po_day14_avg': '%.2f' % windows_avg[3],
                    'po_day30_avg': '%.2f' % windows_avg[4],
                    'po_day90_avg': '%.2f' % windows_avg[5],
                    'po_run_rate': po_run_rate,
                    'forecast_daily_demand': daily_demand,
                    'pending_po_id': [po[0] for po in pending_po],
                    'pending_po_qty': ['%d' % po[1] for po in pending_po],
                    'pending_po_len': len(pending_po),
                    'pending_po_date': [po[2] for po in pending_po],
                    'last_received_date': po_last_date.isoformat() if po_last_date else None,
                    'last_received_qty': '%d' % mp_po_product_qty.get(product_id, 0),
                })

                # Save data into aging inventory table
                AgingInventory.objects.update_or_create(
                    product_id=product_id,
                    sku=sku,
                    defaults=item_info
                )

                item_info.update({
                    'product_id': product_id,
                    'sku': sku,
                })

                # PO fields for fb
                item_info.update({
                    'day_7_avg': round(windows_avg[2] / 7.0, 2),
                    'day_3_avg': round(windows_avg[1] / 7.0, 2),
                    'fb_decay_discount': '20%',
                    'pre_fb_run_rate': '%.2f' % (windows_avg[1] / 3.0 * 1.2),
                    'lead_time': lead_time,
                    'num_of_days': 1,
                    'reorder_units': round(windows_avg[1] / 3.0 * lead_time, 2),
                    'est_total_buy': 'N/A' if not data.get('cost') else
                    round((windows_avg[1] / 3.0 * 1.2 * 1.5 * lead_time * float(data.get('cost', 0.0))), 2),
                })

                # PO fields for vp
                item_info.update({
                    'standardized_metric_of_service_level': '%.2f' % standardized_metric_of_service_level,
                    'stdev_of_demand': stdev_demand,
                    'stdev_of_demand_over_vp': stdev_of_demand_over_vp,
                    'demand_for_vp': demand_for_vp,
                    'safety_stock': safety_stock,
                    'qty_needed_for_vp': qty_needed_for_vp,
                    'hr_qty': hr_qty,
                    'is_order': is_order,
                    'order_qty': order_qty,
                    'order_celling': order_celling,
                    'w4_model': round(week_models[0], 2),
                    'w3_model': round(week_models[1], 2),
                    'w2_model': round(week_models[2], 2),
                    'w1_model': round(week_models[3], 2),
                    'w4_square_errors': round(square_errors[0], 2),
                    'w3_square_errors': round(square_errors[1], 2),
                    'w2_square_errors': round(square_errors[2], 2),
                    'w1_square_errors': round(square_errors[3], 2)})

                # S fields
                item_info.update({
                    # 'category': mp_brand_model.get(product_id, 'N/A'),
                    'day_3_left': '%.2f' % inventory_lefts.get('day_3') if inventory_lefts.get('day_3') != 'N/A' else 'N/A',
                    'day_7_left': '%.2f' % inventory_lefts.get('day_7') if inventory_lefts.get('day_7') != 'N/A' else 'N/A',
                    'run_rate_7': '%.2f' % inventory_lefts.get('day_7') if inventory_lefts.get('day_7') != 'N/A' else 'N/A',
                    'run_rate_14': '%.2f' % inventory_lefts.get('day_14') if inventory_lefts.get('day_14') != 'N/A' else 'N/A',
                    'run_rate_30': '%.2f' % inventory_lefts.get('day_30') if inventory_lefts.get('day_30') != 'N/A' else 'N/A',
                    'run_rate_90': '%.2f' % inventory_lefts.get('day_90') if inventory_lefts.get('day_90') != 'N/A' else 'N/A',
                    'avg_left': '%.2f' % self.get_average_inventory_left(
                        [run_rate for day, run_rate in inventory_lefts.items() if day == 'day_3' or day == 'day_7'],
                    ),
                    'avg_run_rate': '%.2f' % self.get_average_inventory_left(
                        [run_rate for day, run_rate in inventory_lefts.items()],
                    ),

                    'avg_run_rate_po': '%.2f' % self.get_average_po_run_rate(
                        [run_rate for day, run_rate in po_run_rate_old.items()],
                    ),
                })
                product_list.append(item_info)
            else:
                pass
        cache.set('po_report: vendor_name_list', vendor_name_list)
        cache.set('po_report: vendor_sku_pair', vendor_sku_pair)
        product_list.sort(key=lambda e: -e['day_90'])
        return product_list

    def get_image_url(self, image):
        if not image:
            return image
        if image.startswith('URL/'):
            image = image.replace('URL', 'http://cellularoutfitter.com/media/catalog/product')
        else:
            image = 'http://cellularoutfitter.com/media/catalog/product/%s' % (image,)
        return image


class SalesReportCsvExport(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # products_data = request.POST.get('products_json')
        # products_data = json.loads(products_data)
        products_data = json.loads(cache.get('salesreport:products'))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sales-report-customers.csv"'
        writer = csv.writer(response)
        rg_field = [
            'product_id',
            'sku',
            'name',
            'qty',
            'is_in_stock',
            'back_orders',
            'base_cost',
            'price',
            'margin',
            'image',
            'attribute_set',
            'category',
            'day_1',
            'day_3',
            'day_7',
            'day_14',
            'day_30',
            'day_90',
            'day_7_avg',
            'day_3_avg',
            'day_3_left',
            'day_7_left',
            'run_rate_7',
            'run_rate_14',
            'run_rate_30',
            'run_rate_90',
            # 'avg_left',
            'avg_run_rate',
        ]
        writer.writerow(rg_field)
        for x in products_data:
            writer.writerow([unicode(x.get(field)).encode('utf-8') for field in rg_field])
        return response


def mobovida_sales(request):
    """
    Returns daily sales information for mobovida skus over last 30 days
    """
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            if auth[0].lower() == 'basic':
                uname, passwd = base64.b64decode(auth[1]).split(':')
                user = authenticate(username=uname, password=passwd)
                if user is not None and user.is_active:
                    request.user = user
                    return_products = cache.get('salesreport:mobovida', default=None)
                    if return_products:
                        return_products = json.loads(return_products)
                    else:
                        current_time = datetime.datetime.utcnow().replace(tzinfo=utc).astimezone(timezone('US/Pacific'))
                        earlier_time = current_time - datetime.timedelta(days=30)
                        products = SalesFlatOrderItem.objects.filter(
                            created_at__gt=earlier_time, sku__contains='MOB-'
                        ).values(
                            'created_at', 'sku', 'order_id', 'qty_ordered', 'base_price',
                            'base_cost', 'base_row_total_incl_tax', 'base_original_price'
                        )
                        orders = SalesFlatOrder.objects.filter(entity_id__in=[p['order_id'] for p in products]).values(
                            'base_shipping_amount', 'total_qty_ordered', 'increment_id', 'entity_id'
                        )
                        orders = {o['entity_id']: o for o in orders}
                        return_products = []
                        for p in products:
                            order = orders.get(p['order_id'], {})
                            shipping_per_product = float(
                                order.get('base_shipping_amount') or 0
                            ) / float(order.get('total_qty_ordered') or 1)
                            return_products.append({
                                'base_cost': float(p.get('base_cost') or 0),
                                'base_price': float(p.get('base_price') or 0),
                                'base_row_total_incl_tax': float(p.get('base_row_total_incl_tax') or 0),
                                'qty_ordered': float(p.get('qty_ordered') or 0),
                                'created_at': p['created_at'].strftime('%Y-%m-%d'),
                                'shipping_rev': shipping_per_product * float(p.get('qty_ordered') or 0),
                                'order_id': order['increment_id'],
                                'sku': p['sku'],
                                'increment_id': order['entity_id']
                            })
                    # timeout sets the cache to expire in 60 minutes.
                        cache.set('salesreport:mobovida', json.dumps(return_products), timeout=60*60)
                    return JsonResponse(return_products, safe=False)
    response = HttpResponse()
    response.status_code = 401
    response['content'] = 'Credentials not authorized. Username: %s, Pass: %s' % (uname, passwd)
    response['WWW-Authenticate'] = 'Basic Auth Protected'

    return response


class PurchaseOrderReport(LoginRequiredMixin, TemplateResponseMixin, View):
    """
    Purchase order report with search by sku and filter functions
    """
    template_name = 'poreport.html'
    login_url = '/accounts/login'

    def __init__(self):
        super(PurchaseOrderReport, self).__init__()
        self.lead_time = settings.PO_DEFAULTS['lead_time']
        self.days_between = settings.PO_DEFAULTS['days_between']
        self.service_level = settings.PO_DEFAULTS['service_level']

    def get(self, request, *args, **kwargs):
        last_updated_dt = cache.get('salesreport:updated_dt')
        vendor_name_list = cache.get('po_report: vendor_name_list', [])
        vendor_sku_pair = cache.get('po_report: vendor_sku_pair', {})
        vendor = request.GET.get('vendor', '')
        search_skus = request.GET.get('searchSkus', '')
        page = request.GET.get('page', 1)
        size = request.GET.get('size', 50)
        st_sort = request.GET.get('sort', '')
        lead_time = request.GET.get('leadTime')
        days_between = request.GET.get('daysBetweenOrder')
        service_level = request.GET.get('serviceLevel')
        fb_discount = request.GET.get('fb_discount')
        reorder_days = request.GET.get('numOfDays')
        checked = request.GET.get('checked')
        product_list = []
        # Refine products to that match search_skus
        if search_skus:
            product_list = json.loads(cache.get('poreport:products'))
            vendor_name_list = []
            search_skus = [s.strip() for s in str(search_skus).split(',')]
            if len(search_skus) == 1:
                product_list = filter(lambda x: search_skus[0].upper() in x.get('sku'), product_list)
            else:
                product_list = filter(lambda x: x.get('sku').upper() in search_skus, product_list)

            # Get vendors that sell products with search_skus
            for p in product_list:
                vendor_name_list.extend(p.get('vendor_name'))
            vendor_name_list = list(set(vendor_name_list))

        # Get product list that current vendor sells
        if vendor:
            product_list = product_list or json.loads(cache.get('poreport:products'))
            product_list = filter(lambda x: vendor in x.get('vendor_name'), product_list)
            # Get the only vendor and vendor_sku
            for product in product_list:
                p_id = product.get('product_id')
                vendor_sku = vendor_sku_pair.get(p_id).get(vendor)
                product['vendor_name'] = [vendor]
                product['vendor_sku'] = [vendor_sku]

        lead_time = json.loads(lead_time) if lead_time else self.lead_time
        days_between = json.loads(days_between) if days_between else self.days_between
        service_level = json.loads(service_level) if service_level else self.service_level

        fb_discount = json.loads(fb_discount) if fb_discount else 0.0
        reorder_days = json.loads(reorder_days) if reorder_days else 1

        # update product info after use types some field values
        for product in product_list:
            # avg_3_day = float(product.get('day_3_avg').strip(' "'))
            avg_3_day = product.get('day_3_avg')
            avg_7_day = product.get('day_7_avg')
            # avg_7_day = float(product.get('day_7_avg').strip(' "'))
            # avg_90_day = float(product.get('day_90')/90)
            avg_90_day = product.get('day_90') / 90.0

            # Update the following fields according to lead_time and days_between from search options
            stdev_of_demand_over_vp = float(product.get('stdev_of_demand_over_vp'))
            demand_for_vp = float(product.get('demand_for_vp'))
            safety_stock = float(product.get('safety_stock'))
            hr_qty = float(product.get('hr_qty'))
            qty = float(product.get('qty'))
            greater_avg = max([avg_3_day, avg_7_day, avg_90_day])
            product['num_of_days'] = reorder_days
            product['lead_time'] = lead_time
            product['fb_decay_discount'] = '%.2f' % fb_discount
            product['pre_fb_run_rate'] = '%.2f' % (avg_3_day * (1 + fb_discount))
            product['stdev_of_demand_over_vp'] = '%.2f' % (stdev_of_demand_over_vp * (lead_time+days_between) / 14.0 )
            new_demand_for_vp = demand_for_vp * (lead_time+days_between) / 14.0
            product['demand_for_vp'] = '%.2f' % new_demand_for_vp
            product['forecast_daily_demand'] = '%.2f' % product.get('forecast_daily_demand')
            product['stdev_of_demand'] = '%.2f' % product.get('stdev_of_demand')
            product['standardized_metric_of_service_level'] = '%.2f' % (norm.ppf(service_level))
            product['safety_stock'] = '%.2f' % (safety_stock * norm.ppf(service_level) / norm.ppf(self.service_level))
            product['qty_needed_for_vp'] = round((safety_stock + new_demand_for_vp), 2)
            sr = SalesReport()
            qty_needed_for_vp = product.get('qty_needed_for_vp')
            product['is_order'] = sr.order_or_not(hr_qty, qty_needed_for_vp, qty)
            product['order_qty'] = sr.get_order_qty(product.get('is_order'), qty_needed_for_vp, qty)
            product['order_celling'] = sr.get_order_celling(product.get('sku'), product.get('order_qty'))

            if checked and json.loads(checked):
                reorder_units = (greater_avg * (1 + fb_discount) * (lead_time + reorder_days))
            else:
                reorder_units = (greater_avg * reorder_days) - (product.get('qty') - (greater_avg * lead_time))
            # Set rounding rules
            if float(product.get('base_cost')) < 10:
                if product.get('sku').split('-')[0] in ['LC0', 'CC1', 'TC1', 'WSLV', 'SCR']:
                    if reorder_units < 0:
                        reorder_units = 0
                    elif reorder_units < 11:
                        reorder_units = 10
                    elif reorder_units < 21:
                        reorder_units = 20
                    else:
                        reorder_units = '%.0f' % (math.ceil(reorder_units / 50.0) * 50.0)
                else:
                    reorder_units = '%.0f' % (math.ceil(reorder_units / 5.0) * 5.0)
            if int(reorder_units) < 0:
                reorder_units = 0
            product['reorder_units'] = reorder_units
            product['extended_grand_total'] = float(product.get('base_cost')) * int(reorder_units)

        # Sort the list
        if st_sort:
            b_reverse = st_sort[0] == '-'
            field = st_sort[1:] if b_reverse else st_sort
            product_list.sort(key=lambda x: x[field], reverse=b_reverse)
        try:
            size = int(size)
        except ValueError:
            size = 50
        paginator = Paginator(product_list, size)
        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)
        if paginator.num_pages > 10:
            if products.number >= 10:
                max_page = products.number + 10 if products.number + 10 < paginator.num_pages else paginator.num_pages
                page_ranges = range(products.number, max_page)
            else:
                page_ranges = range(1, 11)
        else:
            page_ranges = list(paginator.page_range)
        context = {
            'last_updated_dt': last_updated_dt,
            'page_products': json.dumps({
                'page': products.object_list,
                'current': products.number,
                'previous': products.has_previous(),
                'next': products.has_next(),
                'last_page': paginator.num_pages,
                'pages': page_ranges
            }),
            'st_sort': st_sort,
            'vendors': json.dumps(sorted(map(lambda x: x, vendor_name_list)))
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        try:
            SalesReport().get_sales_report()
        except Exception as e:
            logger.exception(
                msg='There was an error manually refreshing PO report.')
            result = {
                'message': 'We were not able to refresh report: %s' % e,
                'success': False,
            }
        else:
            result = {
                'message': 'Report has been refreshed!',
                'success': True,
            }
        return JsonResponse(result)


class PurchaseOrderReportCsvExport(LoginRequiredMixin, View):
    """
    Download the report csv that match the current filter
    """
    def __init__(self):
        super(PurchaseOrderReportCsvExport, self).__init__()
        self.lead_time = settings.PO_DEFAULTS['lead_time']
        self.days_between = settings.PO_DEFAULTS['days_between']
        self.service_level = settings.PO_DEFAULTS['service_level']

    def post(self, request, *args, **kwargs):
        product_list = []
        vendor = request.POST.get('selectedVendor')
        search_skus = request.POST.get('searchSku')
        fb_discount = request.POST.get('fb_DecayDiscount')
        lead_time = request.POST.get('leadTime')

        days_between = request.POST.get('daysBetweenOrder')
        service_level = request.POST.get('serviceLevel')

        reorder_days = request.POST.get('numOfDays')
        checked = request.POST.get('checked')
        vendor_sku_pair = cache.get('po_report: vendor_sku_pair', {})
        if search_skus:
            product_list = json.loads(cache.get('poreport:products'))
            search_skus = [s.strip() for s in str(search_skus).split(',')]
            if len(search_skus) == 1:
                product_list = filter(lambda x: search_skus[0].upper() in x.get('sku'), product_list)
            else:
                product_list = filter(lambda x: x.get('sku').upper() in search_skus, product_list)

        # Get product list that current vendor sells
        if vendor:
            product_list = product_list or json.loads(cache.get('poreport:products'))
            product_list = filter(lambda x: vendor in x.get('vendor_name'), product_list)
            # Get the only vendor and vendor_sku
            for product in product_list:
                p_id = product.get('product_id')
                vendor_sku = vendor_sku_pair.get(p_id).get(vendor)
                product['vendor_name'] = [vendor]
                product['vendor_sku'] = [vendor_sku]

        # Get optional field values from frontend
        lead_time = json.loads(lead_time) if lead_time else self.lead_time
        reorder_days = json.loads(reorder_days) if reorder_days else 1
        fb_discount = json.loads(fb_discount) if fb_discount else 0.0

        days_between = json.loads(days_between) if days_between else self.days_between
        service_level = json.loads(service_level) if service_level else self.service_level

        # update product info after use types some field values for csv file
        for product in product_list:
            avg_3_day = product.get('day_3_avg')
            avg_7_day = product.get('day_7_avg')
            avg_90_day = product.get('day_90') / 90.0
            greater_avg = max([avg_3_day, avg_7_day, avg_90_day])
            product['num_of_days'] = reorder_days
            product['lead_time'] = lead_time
            product['fb_decay_discount'] = '%.2f' % fb_discount
            product['pre_fb_run_rate'] = '%.2f' % (avg_3_day * (1 + fb_discount))
            if checked and json.loads(checked):
                reorder_units = (greater_avg * (1 + fb_discount) * (lead_time + reorder_days))
            else:
                reorder_units = (greater_avg * reorder_days) - (product.get('qty') - (greater_avg * lead_time))
            # Set rounding rules
            if float(product.get('base_cost')) < 10:
                if product.get('sku').split('-')[0] in ['LC0', 'CC1', 'TC1', 'WSLV', 'SCR']:
                    if reorder_units < 0:
                        reorder_units = 0
                    elif reorder_units < 11:
                        reorder_units = 10
                    elif reorder_units < 21:
                        reorder_units = 20
                    else:
                        reorder_units = '%.0f' % (math.ceil(reorder_units / 50.0) * 50.0)
                else:
                    reorder_units = '%.0f' % (math.ceil(reorder_units / 5.0) * 5.0)
            if int(reorder_units) < 0:
                reorder_units = 0
            product['reorder_units'] = reorder_units
            product['extended_grand_total'] = float(product.get('base_cost')) * int(reorder_units)

            # Update forecast fields according to lead_time and days_between
            stdev_of_demand_over_vp = float(product.get('stdev_of_demand_over_vp'))
            demand_for_vp = float(product.get('demand_for_vp'))
            safety_stock = float(product.get('safety_stock'))
            hr_qty = float(product.get('hr_qty'))
            qty = float(product.get('qty'))

            product['stdev_of_demand_over_vp'] = '%.2f' % (stdev_of_demand_over_vp * (lead_time + days_between) / 14.0)
            new_demand_for_vp = demand_for_vp * (lead_time + days_between) / (self.lead_time + self.days_between)
            product['demand_for_vp'] = '%.2f' % new_demand_for_vp
            product['standardized_metric_of_service_level'] = '%.2f' % (norm.ppf(service_level))
            product['safety_stock'] = '%.2f' % (safety_stock * norm.ppf(service_level) / norm.ppf(self.service_level))
            product['qty_needed_for_vp'] = round((safety_stock + new_demand_for_vp), 2)
            product['forecast_daily_demand'] = '%.2f' % product.get('forecast_daily_demand')
            product['stdev_of_demand'] = '%.2f' % product.get('stdev_of_demand')
            sr = SalesReport()
            qty_needed_for_vp = product.get('qty_needed_for_vp')
            product['is_order'] = sr.order_or_not(hr_qty, qty_needed_for_vp, qty)
            product['order_qty'] = sr.get_order_qty(product.get('is_order'), qty_needed_for_vp, qty)
            product['order_celling'] = sr.get_order_celling(product.get('sku'), product.get('order_qty'))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="po-report-customers.csv"'
        writer = csv.writer(response)
        rg_field = [
            'product_id',
            'sku',
            'name',
            'qty',
            'is_in_stock',
            'back_orders',
            'base_cost',
            'price',
            'margin',
            'image',
            'vendor_sku',
            'vendor_name',
            'attribute_set',
            'category',
            'day_1',
            'day_3',
            'day_7',
            'day_14',
            'day_30',
            'day_90',
            # 'day_7_avg',
            # 'day_3_avg',
            'po_day1_avg',
            'po_day3_avg',
            'po_day7_avg',
            'po_day14_avg',
            'po_day30_avg',
            'po_day90_avg',
            'forecast_daily_demand',
            'stdev_of_demand',
            'standardized_metric_of_service_level',
            'stdev_of_demand_over_vp',
            'demand_for_vp',
            'safety_stock',
            'qty_needed_for_vp',
            'hr_qty',
            'is_order',
            'order_qty',
            'order_celling',
            'day_3_left',
            'day_7_left',
            # 'run_rate_7_po',
            # 'run_rate_14_po',
            # 'run_rate_30_po',
            # 'run_rate_90_po',
            # 'avg_left',
            'avg_run_rate',
            # 'est_days_in_stock',
            'lead_time',
            'num_of_days',
            'reorder_units',
            'est_total_buy',
            'pending_po_id',
            'pending_po_qty',
            'pending_po_len',
            'pending_po_date',
            'last_received_date',
            'last_received_qty',
            'w1_model',
            'w2_model',
            'w3_model',
            'w4_model',
            'w4_square_errors',
            'w3_square_errors',
            'w2_square_errors',
            'w1_square_errors',

        ]
        # if checked and json.loads(checked) and fb_discount:
        if checked and json.loads(checked):
            rg_field.extend(['fb_decay_discount', 'pre_fb_run_rate'])
        writer.writerow(rg_field)
        for x in product_list:
            writer.writerow([self.formalize_field(x, field) for field in rg_field])
        return response

    def formalize_field(self, data_row, field):
        if isinstance(data_row.get(field), list) and data_row.get(field):
            return '  '.join([unicode(x).encode('utf-8') for x in data_row.get(field)])
        else:
            return unicode(data_row.get(field)).encode('utf-8')


class InventoryQuarantine(LoginRequiredMixin, TemplateResponseMixin, View):

    template_name = 'inventory_quarantine.html'
    login_url = '/accounts/login'

    def get(self, request, *args, **kwargs):
        return self.render_to_response(context = {})

    def post(self, request, *args, **kwargs):
        try:
            my_uploaded_file = request.FILES['uploadedFile']
        except Exception as e:
            messages.add_message(request, messages.INFO, 'Please upload a csv file.')
            return self.render_to_response(context={})
        reader = csv.reader(my_uploaded_file)
        mp_sku_sprice = {}
        for row in reader:
            try:
                mp_sku_sprice[row[0]] = row[2]
            except IndexError:
                continue

        mp_sku_product = dict(CatalogProductEntity.objects.filter(
            sku__in=[sku for sku in mp_sku_sprice]).values_list('entity_id', 'sku'))

        mp_values = EavAttribute.objects.get_values(
            [p_id for p_id in mp_sku_product],
            entity_type=4,
            field_names=['price', 'special_price'],
            json_values=False)
        quarantine_products_added = 0
        quarantine_products_updated = 0
        try:
            for product_id, sku in mp_sku_product.iteritems():
                pre_quarantine_price = mp_values.get(product_id).get('special_price')
                if not pre_quarantine_price:
                    pre_quarantine_price = mp_values.get(product_id).get('price')
                current_price = Decimal(mp_sku_sprice.get(sku))
                quarantine_level = '%s%s' % (((pre_quarantine_price - current_price
                                               ) * 100 / pre_quarantine_price).quantize(Decimal(10) ** -2), '%')
                pq = ProductQuarantine.objects.update_or_create(
                    product_id = product_id,
                    sku = sku,
                    defaults={
                        'pre_quarantine_price': pre_quarantine_price,
                        'current_price': current_price,
                        'quarantine_level': quarantine_level,
                        'quarantine_level_updated_at': datetime.datetime.now(tz=utc)
                    }
                )
                if pq[1]:
                    quarantine_products_added += 1
                else:
                    quarantine_products_updated += 1
        except Exception:
            messages.add_message(
                request, messages.INFO, 'Failed to process this file, please check later.'
            )
            return self.render_to_response(context={})
        messages.add_message(
            request,
            messages.INFO,
            '''
            File processed successfully. Added %s products. Updated: %s products.
            ''' % (quarantine_products_added, quarantine_products_updated))
        return self.render_to_response(context={})
