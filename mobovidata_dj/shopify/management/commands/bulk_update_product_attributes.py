from django.core.management.base import BaseCommand
from mobovidata_dj.shopify.scripts.metafields import bulk_update_product_attributes


class Command(BaseCommand):
    help = 'Bulk update product metafields'

    def handle(self, *args, **options):
        bulk_update_product_attributes()
        self.stdout.write(self.style.SUCCESS('Successfully updated product attributes'))
