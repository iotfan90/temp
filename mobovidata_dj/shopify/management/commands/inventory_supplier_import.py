from django.core.management.base import BaseCommand
from mobovidata_dj.shopify.scripts.inventory_supplier import save_inventory_suppliers


class Command(BaseCommand):
    help = 'Import inventory suppliers from Magento DB'

    def handle(self, *args, **options):
        save_inventory_suppliers()
        self.stdout.write(self.style.SUCCESS('Inventory suppliers successfully imported'))
