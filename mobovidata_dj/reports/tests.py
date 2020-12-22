import json
import sys

from django.test import TestCase
from django.utils import timezone
from unittest import skip

from logging import getLogger

from .models import ReportQuery
from mobovidata_dj.facebook.models import AdStatWindow, FacebookAd

log = getLogger(__name__)


TEST_CMD = ' '.join(sys.argv)


def skip_unless_explicit(func):
    if 'manage.py test' in TEST_CMD and 'reports' in TEST_CMD:
        return func
    return skip(func)


class TestExportCSV(TestCase):

    def test_run_query(self):
        rq = ReportQuery.objects.create(source='mvd', title='my_query', query="""
                    SELECT * FROM reports_reportquery""".strip())
        results = list(rq.iterate_rows_as_dict())
        self.assertEqual(1, len(results))

    def test_execute_local_csv(self):
        rq = ReportQuery.objects.create(source='mvd', title='my_query', query="""
                    SELECT * FROM reports_reportquery""".strip())
        exc = rq.execute()
        self.assertEqual(exc.on_disk, True)
        exc.remove_from_disk()

    def test_execute_local_csv_gzip(self):
        rq = ReportQuery.objects.create(source='mvd', title='my_query', query="""
                    SELECT * FROM reports_reportquery""".strip())
        exc = rq.execute(gzip=True)
        self.assertEqual(exc.on_disk, True)
        exc.remove_from_disk()

    @skip_unless_explicit
    def test_report_to_s3(self):
        rq = ReportQuery.objects.create(source='mvd', title='my_query', query="""
                    SELECT * FROM reports_reportquery""".strip())
        exc = rq.execute()
        self.assertEqual(exc.on_disk, True)

        exc.upload_to_s3(True)
        self.assertEqual(exc.on_disk, False)

    def test_column_metadata_for_facebookads(self):
        today = timezone.now().date()

        ad = FacebookAd(account_id=123, campaign_id=456, ad_set_id=789,
                        ad_id=999, products=json.dumps([{'entity_id': '500'}]))
        ad.save()

        AdStatWindow.objects.create(date_start=today, date_stop=today,
                                    ad_obj=ad, ad_id=999, adset_id=789,
                                    spend=100, sales=4, cost_per_sale=25)

        ad.associate_products()

        rq = ReportQuery.objects.create(source='mvd', title='my_query', query="""
                    SELECT * FROM facebook_facebookad""".strip())
        exc = rq.execute()
        exc.remove_from_disk()
        self.assertEqual(exc.metadata['ad_id']['type'], 'varchar(3)')
        self.assertEqual(exc.metadata['ad_id']['size'], 3)
        self.assertEqual(exc.metadata['created_dt']['type'], 'timestamp')

        rq = ReportQuery.objects.create(source='mvd', title='my_query', query="""
                    SELECT * FROM facebook_adstatwindow""".strip())
        exc = rq.execute()
        exc.remove_from_disk()

        self.assertEqual(exc.metadata['spend']['type'], 'float')
        self.assertEqual(exc.metadata['created_at']['type'], 'timestamp')

        rq = ReportQuery.objects.create(source='mvd', title='my_query', query="""
                    SELECT * FROM facebook_advertisedproduct_ad_objs""".strip())
        exc = rq.execute()
        exc.remove_from_disk()
        self.assertEqual(exc.metadata['facebookad_id']['type'], 'integer')
        self.assertEqual(exc.metadata['advertisedproduct_id']['type'], 'integer')
        self.assertEqual(exc.metadata['_count'], 1)

    @skip_unless_explicit
    def test_redshift_target(self):
        today = timezone.now().date()
        ad = FacebookAd(account_id=123, campaign_id=456, ad_set_id=789,
                        ad_id=999, products=json.dumps([{'entity_id': '500'}]))
        ad.save()

        AdStatWindow.objects.create(date_start=today, date_stop=today,
                                    ad_obj=ad, ad_id=999, adset_id=789,
                                    spend=100, sales=4, cost_per_sale=25)
        products = ad.associate_products()

        product = products.first()
        product.get_stat_windows().today()

        rq = ReportQuery.objects.create(source='mvd',
                                        title='mY! test~*() query-4516&^',
                                        query="""SELECT * FROM facebook_facebookad""".strip())
        rq.execute(format='csv', gzip=True, target='redshift')
