from django.core.management.base import BaseCommand
from mobovidata_dj.shopify.scripts.inventory_supplier import save_inventory_suppliers_mapping


class Command(BaseCommand):
    help = 'Import inventory suppliers mapping (vendor code - SKU) from Magento DB'

    def handle(self, *args, **options):
        save_inventory_suppliers_mapping()
        self.stdout.write(self.style.SUCCESS('Inventory suppliers mapping successfully imported'))
