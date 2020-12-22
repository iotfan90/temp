from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings

from supplier_inventory.utils import update_supplier_inventory_table

logger = get_task_logger(__name__)


@shared_task(ignore_results=True)
def import_supplier_inventory():
    for vendor, info in settings.SUPPLIER_INFO.items():
        update_supplier_inventory_table(info['feed_url'], info['id'])
