from django.core.management.base import BaseCommand
from mobovidata_dj.shopify.scripts.flat_co_products import flat_co_products


class Command(BaseCommand):
    help = 'Remove all products from Shopify that have multiple variants'

    def handle(self, *args, **options):
        flat_co_products()
        self.stdout.write(self.style.SUCCESS('Products successfully removed.'))
