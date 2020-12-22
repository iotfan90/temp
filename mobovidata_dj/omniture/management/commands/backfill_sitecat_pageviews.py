from datetime import timedelta, datetime
from django.core.management.base import BaseCommand

from mobovidata_dj.omniture.utils import (get_pdp_view_data,
                                          get_pdp_view_report,
                                          update_sc_product_data_table)
from modjento.models import SalesFlatOrderItem
from modjento.utils import chunk_ids


class Command(BaseCommand):
    help = 'Backfills sitecat product data to the start of magento (May, 2015)'

    def handle(self, *args, **options):
        # Goes through and grabs all sitecat pageviews, visits for products sold
        #  in magento.
        sold_product_ids = SalesFlatOrderItem.objects.values('product_id')
        spi = set()
        for r in sold_product_ids:
            spi.add(r['product_id'])
        spi = list(spi)
        ids = ['^%s$' % i for i in spi]
        chunks = []
        for c in chunk_ids(ids):
            chunks.append(c)
        start_date = datetime.strptime('2015-05-01', '%Y-%m-%d')
        end_date = datetime.strptime('2015-06-01', '%Y-%m-%d')
        while end_date < datetime.now():
            start_time = datetime.datetime.now()
            for c in chunks:
                c_time = datetime.datetime.now()
                print 'Proccessing chunk %s' % c
                load_chunk(c, start_date, end_date)
                d = datetime.datetime.now() - c_time
                print '\t finished chunk in %s' % d.seconds
            end_time = datetime.datetime.now() - start_time
            print '%s' % end_time.seconds
            start_date = start_date + timedelta(days=30)
            end_date = end_date + timedelta(days=30)


def load_chunk(c, start_date, end_date):
    data, norm_data = get_pdp_view_report(c, start_date, end_date)
    print '\t get_pdp_view_report complete'
    pdp_data = get_pdp_view_data(data, c)
    print '\t get_pdp_view_data complete'
    update_sc_product_data_table(pdp_data, c)
    print '\t update_sc_product_data_table complete'
