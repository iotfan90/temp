from django.core.management.base import BaseCommand
from mobovidata_dj.shopify.scripts.delete_products import delete_co_skus


class Command(BaseCommand):
    help = 'Remove all products from Shopify that have multiple variants'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)

    def handle(self, *args, **options):
        delete_co_skus(options['file_path'])
        self.stdout.write(self.style.SUCCESS('Products successfully removed.'))
