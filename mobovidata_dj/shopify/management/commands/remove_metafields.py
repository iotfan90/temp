from django.core.management.base import BaseCommand
from mobovidata_dj.shopify.scripts.metafields import remove_metafields


class Command(BaseCommand):
    help = 'Remove all products from Shopify that have multiple variants'

    def add_arguments(self, parser):
        parser.add_argument('store_identifier', type=str)
        parser.add_argument('type_of_resource', type=str)
        parser.add_argument('namespace', type=str)
        parser.add_argument('key', type=str)

    def handle(self, *args, **options):
        remove_metafields(options['store_identifier'],
                          options['type_of_resource'],
                          options['namespace'],
                          options['key'])
        self.stdout.write(self.style.SUCCESS('Metafields were successfully removed.'))
