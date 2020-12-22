from celery.utils.log import get_task_logger
from django.utils import timezone

from mobovidata_dj.shopify.connect import ShopifyConnect
from mobovidata_dj.shopify.models import Store, Customer, Order

logger = get_task_logger(__name__)


class ProcessOrders(object):

    def __init__(self, store, orders=[]):
        self._store = store
        self._orders = orders

    def parse_orders(self):
        try:
            for order in self._orders:
                # Customer
                customer = order.get('customer', None)
                cust_obj = None
                if customer:
                    cust_obj, created_cust = (Customer.objects
                        .filter(store=self._store)
                        .update_or_create(
                            customer_id=customer['id'],
                            defaults={
                                'store': self._store,
                                'accepts_marketing': customer.get('accepts_marketing',
                                                                  False),
                                'created_at': customer.get('created_at', None),
                                'email': customer.get('email', None),
                                'phone': customer.get('phone', None),
                                'first_name': customer.get('first_name', None),
                                'last_name': customer.get('last_name', None),
                                'note': customer.get('note', None),
                                'orders_count': customer.get('orders_count', None),
                                'state': customer.get('state', None),
                                'total_spent': customer.get('total_spent', None),
                                'updated_at': customer.get('updated_at', None),
                                'tags': customer.get('tags', None),
                            }))

                # Order
                shipping_address = order.get('shipping_address', {})
                ord_obj, created_ord = (Order.objects
                    .filter(store=self._store)
                    .update_or_create(
                        order_id=order['id'],
                        defaults={
                            'store': self._store,
                            'customer': cust_obj,
                            'created_at': order.get('created_at', None),
                            'email': order.get('email', None),
                            'financial_status': order.get('financial_status', None),
                            'landing_site': order.get('landing_site', None),
                            'name': order.get('name', None),
                            'order_number': order.get('order_number', None),
                            'referring_site': order.get('referring_site', None),
                            'source_name': order.get('source_name', None),
                            'subtotal_price': order.get('subtotal_price', None),
                            'total_discounts': order.get('total_discounts', None),
                            'total_price': order.get('total_price', None),
                            'total_tax': order.get('total_tax', None),
                            'cancel_reason': order.get('cancel_reason', None),
                            'cancelled_at': order.get('cancelled_at', None),
                            'closed_at': order.get('closed_at', None),
                            'shipping_address_address1': shipping_address.get('address1', None),
                            'shipping_address_address2': shipping_address.get('address2', None),
                            'shipping_address_city': shipping_address.get('city', None),
                            'shipping_address_company': shipping_address.get('company', None),
                            'shipping_address_country': shipping_address.get('country', None),
                            'shipping_address_first_name': shipping_address.get('first_name', None),
                            'shipping_address_last_name': shipping_address.get('last_name', None),
                            'shipping_address_latitude': shipping_address.get('latitude', None),
                            'shipping_address_longitude': shipping_address.get('longitude', None),
                            'shipping_address_phone': shipping_address.get('phone', None),
                            'shipping_address_province': shipping_address.get('province', None),
                            'shipping_address_zip': shipping_address.get('zip', None),
                            'shipping_address_name': shipping_address.get('name', None),
                            'shipping_address_country_code': shipping_address.get('country_code', None),
                            'shipping_address_province_code': shipping_address.get('province_code', None),
                        }))

                # Order line items
                line_items = order['line_items']

                for line in line_items:
                    brand_model = next((p['value'] for p in line.get('properties', None)
                                        if p['name'] == 'collectionHandle'), None)
                    ord_l_obj, created_ord_l = (ord_obj.orderline_set
                        .update_or_create(
                            line_id=line['id'],
                            defaults={
                                'order': ord_obj,
                                'price': line.get('price', None),
                                'quantity': line.get('quantity', None),
                                'sku': line.get('sku', None),
                                'title': line.get('title', None),
                                'variant_title': line.get('variant_title', None),
                                'name': line.get('name', None),
                                'product_id': line.get('product_id', None),
                                'variant_id': line.get('variant_id', None),
                                'total_discount': line.get('total_discount', None),
                                'brand_model': brand_model,
                            }))
        except Exception as ex:
            print 'Order ID: ', order['id']
            print repr(ex)
            raise

    def delete_orders(self, order_ids):
        (Order.objects
         .filter(store=self._store, order_id__in=order_ids)
         .delete())


def get_shopify_orders():
    stores = Store.objects.all()

    for store in stores:
        shopify = ShopifyConnect(store)

        try:
            orders_qty = shopify.get_orders_total_quantity(
                updated_at_min=store.order_task_run_at, status='any')['count']
            total_pages = -(-orders_qty // 250)

            for page in xrange(1, total_pages+1):
                orders = []
                response = shopify.get_orders(page=page, status='any',
                                              updated_at_min=store.order_task_run_at)
                orders.extend(response['orders'])
                print 'page: ', page
                process = ProcessOrders(store, orders)
                process.parse_orders()

            store.order_task_run_at = timezone.now()
            store.save()
        except Exception, ex:
            logger.exception('There was an error while executing shopify task %s',
                             ex)
            raise

#get_shopify_orders()

