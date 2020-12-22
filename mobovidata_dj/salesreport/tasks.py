import os
import csv

from celery import shared_task
from celery.utils.log import get_task_logger
import datetime

from .views import SalesReport
from modjento.models import (CataloginventoryStockItem,
                             CatalogProductEntityDecimal)

logger = get_task_logger(__name__)


@shared_task(ignore_results=True)
def get_sales_report():
    """
    Celery task to get product sales info for past 90 days and store info in
    redis cache
    """
    SalesReport().get_sales_report()


@shared_task(ignore_results=True)
def get_inventory(data_dir='./data/inventory/'):
    """
    Celery task to get today's inventory for each product id
    :return:
    """
    product_stock = CataloginventoryStockItem.objects.all().only(
            'product_id',
            'qty',
            'is_in_stock',
            'backorders')
    now = datetime.datetime.now()

    ps = [{
            'product_id': p.product_id,
            'qty': int(p.qty),
            'is_in_stock': p.is_in_stock,
            'backorders': p.backorders,
            'created_at': '%s' % now
        } for p in product_stock]
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    with open('%sinventory_qty_%s.csv' % (data_dir,
                                          datetime.datetime.strftime(now, '%Y-%m-%d')), 'wb') as f:
        r = csv.DictWriter(f, fieldnames=[k for k in ps[0].keys()])
        r.writeheader()
        r.writerows(ps)


@shared_task(ignore_results=True)
def get_inventory_cogs(data_dir='./data/inventory/'):
    product_cogs = CatalogProductEntityDecimal.objects.filter(
        attribute_id=79,
        store_id=0,
        entity_type_id=4
    ).only(
            'entity_id', 'value'
    )
    now = datetime.datetime.now()

    ps = [{
            'product_id': p.entity_id,
            'cost': p.value,
            'created_at': '%s' % now
        } for p in product_cogs]
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    with open('%sinventory_cogs_%s.csv' % (data_dir, datetime.datetime.strftime(now, '%Y-%m-%d')), 'wb') as f:
        r = csv.DictWriter(f, fieldnames=[k for k in ps[0].keys()])
        r.writeheader()
        r.writerows(ps)


@shared_task(ignore_results=True)
def get_inventory_special_price(data_dir='./data/inventory/'):
    product_special_price = CatalogProductEntityDecimal.objects.filter(
        attribute_id=76,
        store_id=0,
        entity_type_id=4,
        value__isnull=False
    ).only(
            'entity_id', 'value'
    )
    now = datetime.datetime.now()

    ps = [{
            'product_id': p.entity_id,
            'special_price': p.value,
            'created_at': '%s' % now
        } for p in product_special_price]
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    with open('%sinventory_special_price_%s.csv' % (data_dir,
                                                    datetime.datetime.strftime(now, '%Y-%m-%d')), 'wb') as f:
        r = csv.DictWriter(f, fieldnames=[k for k in ps[0].keys()])
        r.writeheader()
        r.writerows(ps)


@shared_task(ignore_results=True)
def get_inventory_retail_price(data_dir='./data/inventory/'):
    product_retail_price = CatalogProductEntityDecimal.objects.filter(
        attribute_id=75,
        store_id=0,
        entity_type_id=4,
        value__isnull=False
    ).only(
            'entity_id', 'value'
    )
    now = datetime.datetime.now()

    ps = [{
            'product_id': p.entity_id,
            'retail_price': p.value,
            'created_at': '%s' % now
        } for p in product_retail_price]
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    with open('%sinventory_retail_price_%s.csv' % (data_dir,
                                                   datetime.datetime.strftime(now, '%Y-%m-%d')), 'wb') as f:
        r = csv.DictWriter(f, fieldnames=[k for k in ps[0].keys()])
        r.writeheader()
        r.writerows(ps)
