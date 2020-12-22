from django.db import transaction

from .api_processing import (ProcessOrders, ProcessProducts,
                             ProcessSmartCollections)
from .models import Store


PRODUCTS_CREATE = 'products/create'
PRODUCTS_UPDATE = 'products/update'
PRODUCTS_DELETE = 'products/delete'
COLLECTIONS_CREATE = 'collections/create'
COLLECTIONS_UPDATE = 'collections/update'
COLLECTIONS_DELETE = 'collections/delete'
ORDERS_CREATE = 'orders/create'
ORDERS_UPDATED = 'orders/updated'
ORDERS_DELETE = 'orders/delete'
ORDERS_CANCELLED = 'orders/cancelled'
ORDERS_FULFILLED = 'orders/fulfilled'
ORDERS_PARTYALLY_FULLFILLED = 'orders/partially_fulfilled'
ORDERS_PAID = 'orders/paid'


@transaction.atomic
def process_webhook(shopify_domain, topic, content):
    store = Store.objects.get(api_url=shopify_domain)
    if topic in [PRODUCTS_CREATE, PRODUCTS_UPDATE]:
        process = ProcessProducts(store, [content, ])
        process.parse_products()
    elif topic in [PRODUCTS_DELETE, ]:
        process = ProcessProducts(store)
        process.delete_products([content['id'], ])
    elif topic in [COLLECTIONS_CREATE, COLLECTIONS_UPDATE]:
        process = ProcessSmartCollections(store, [content, ])
        process.parse_smart_collections()
    elif topic in [COLLECTIONS_DELETE, ]:
        process = ProcessSmartCollections(store)
        process.delete_collections([content['id'], ])
    elif topic in [ORDERS_CREATE, ORDERS_UPDATED, ORDERS_CANCELLED,
                   ORDERS_FULFILLED, ORDERS_PARTYALLY_FULLFILLED, ORDERS_PAID]:
        process = ProcessOrders(store, [content, ])
        process.parse_orders()
    elif topic in [ORDERS_DELETE]:
        process = ProcessOrders(store)
        process.delete_orders([content['id'], ])
