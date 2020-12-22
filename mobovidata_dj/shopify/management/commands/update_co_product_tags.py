from django.core.management.base import BaseCommand
from mobovidata_dj.shopify.scripts.update_product_tags import update_co_product_tags


class Command(BaseCommand):
    help = 'Update all product tags for CO Shopify'

    def handle(self, *args, **options):
        update_co_product_tags()
        self.stdout.write(self.style.SUCCESS('Tags successfully updated.'))
