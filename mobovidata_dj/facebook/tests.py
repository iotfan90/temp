import sys
import json

from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from logging import getLogger
from unittest import skip

from .models import (AdStatWindow, FacebookAd, OptimizeCheck,
                     OptimizeNotification)

log = getLogger(__name__)

TEST_CMD = ' '.join(sys.argv)


def skip_api_commands_unless_explicit(func):
    # These tests consume facebook API (with caching)
    # and might fail if yesterday's stats are zero
    # for
    if 'manage.py test' in TEST_CMD and 'facebook' in TEST_CMD:
        return func
    return skip(func)


class FacebookAdInsightsTest(TestCase):
    def setUp(self):
        from .connect import FacebookConnect
        self.cnx = FacebookConnect()
        self.today = str((timezone.now()).date())
        self.yst = str((timezone.now()-timedelta(days=1)).date())

    @skip_api_commands_unless_explicit
    def test_get_facebook_stats(self):
        data = self.cnx.get_ad_insights(start=self.yst, end=self.yst)
        log.debug('Ad insight data:')
        log.debug(json.dumps(data, indent=2, sort_keys=2))
        self.assertGreater(len(data), 0)
        self.assertGreater(sum(map(lambda k: data[k]['spend'], data)), 0)
        self.assertGreater(sum(map(lambda k: data[k]['impressions'], data)), 0)

    @skip_api_commands_unless_explicit
    def test_build_stat_windows(self):
        data = AdStatWindow.build_stats(date=self.yst)
        self.assertGreater(len(data), 0)
        self.assertEqual(AdStatWindow.objects.yesterday().count(), len(data))

        log.info('%s stat windows created' % AdStatWindow.objects.count())

    @skip_api_commands_unless_explicit
    def test_accurate_revenues(self):
        ERROR = 0.01
        known_stats = {
            '2016-09-23': 23811.83,
            '2016-09-24': 23587.17,
            '2016-09-25': 28558.90,
            '2016-09-26': 18291.91,
            '2016-09-27': 15323.89,
            '2016-09-28': 14446.55,
            '2016-09-29': 23564.31,
            '2016-09-30': 38854.95,
            '2016-10-01': 44740.80,
            '2016-10-02': 41149.62
        }

        observed = {}
        difference = {}
        compare = {}
        AdStatWindow.objects.all().delete()
        for date, expected in known_stats.items():
            windows = AdStatWindow.build_stats(date=date)
            observed[date] = sum(window.sales_revenue
                                 for window in AdStatWindow.objects.for_date(date))
            difference[date] = abs(known_stats[date] - observed[date])
            compare[date] = '%0.2f - %0.2f = %0.2f' % (known_stats[date], observed[date], difference[date])

        self.assertGreater(ERROR * sum(known_stats.values()),
                                   sum(difference.values()))

    def test_product_stat_windows(self):
        today = timezone.now().date()

        ad = FacebookAd(account_id=123, campaign_id=456, ad_set_id=789,
                        ad_id=999, products=json.dumps([{'entity_id': '500'}]))
        ad.save()

        window = AdStatWindow.objects.create(date_start=today, date_stop=today,
                                             ad_obj=ad, ad_id=999, adset_id=789,
                                             spend=100, sales=4,
                                             cost_per_sale=25)

        products = ad.associate_products()

        self.assertEqual(products.count(), 1)
        self.assertNotEqual(products.get(product_id=500), None)
        product = products.first()
        windows = product.get_stat_windows().today()

        self.assertEqual(windows.count(), 1)
        self.assertEqual(windows.first().spend, 100)
        self.assertEqual(windows.first().cost_per_sale, 25)


class AdOptimizerTest(TestCase):
    def test_rule_checks(self):
        check = OptimizeCheck.do_check

        # EQ check
        self.assertEqual(check('eq', 1, 1), True)
        self.assertEqual(check('eq', 1, 2), False)

        # GT check
        self.assertEqual(check('gt', 10, 1), True)
        self.assertEqual(check('gt', 2, 1), True)
        self.assertEqual(check('gt', 1, 1), False)
        self.assertEqual(check('gt', 0, 1), False)

        # GTE check
        self.assertEqual(check('gte', 10, 1), True)
        self.assertEqual(check('gte', 2, 1), True)
        self.assertEqual(check('gte', 1, 1), True)
        self.assertEqual(check('gte', 0, 1), False)

        # LT check
        self.assertEqual(check('lt', 1, 10), True)
        self.assertEqual(check('lt', 1, 2), True)
        self.assertEqual(check('lt', 1, 1), False)
        self.assertEqual(check('lt', 1, 0), False)

        # LTE check
        self.assertEqual(check('lte', 1, 10), True)
        self.assertEqual(check('lte', 1, 2), True)
        self.assertEqual(check('lte', 1, 1), True)
        self.assertEqual(check('lte', 1, 0), False)

    def test_check(self):
        check, _new = OptimizeCheck.objects.get_or_create(
            if_the='sales',
            check_type='gte',
            value=20
        )
        window = AdStatWindow(sales=20)
        self.assertEqual(check.evaluate(window), True)

        window = AdStatWindow(sales=200)
        self.assertEqual(check.evaluate(window), True)

        window = AdStatWindow(sales=19)
        self.assertEqual(check.evaluate(window), False)

        window = AdStatWindow(clicks=500)
        self.assertEqual(check.evaluate(window), False)

        window = AdStatWindow(clicks=500, sales=20)
        self.assertEqual(check.evaluate(window), True)

        check, _new = OptimizeCheck.objects.get_or_create(
            if_the='cost_per_sale',
            check_type='gte',
            value=10
        )
        window = AdStatWindow(clicks=500, sales=20, cost_per_sale=25)
        self.assertEqual(check.evaluate(window), True)

        window = AdStatWindow(clicks=5000, sales=20, cost_per_sale=2.50)
        self.assertEqual(check.evaluate(window), False)

    def test_basic_optimizer(self):
        from .fixtures import basic_optimizer
        today = timezone.now().date()
        o = basic_optimizer()
        # Dummy FB Adset
        ad = FacebookAd(account_id=123, campaign_id=456, ad_set_id=789,
                        ad_id=123)
        ad.save()
        window = AdStatWindow.objects.create(date_start=today, date_stop=today,
                                             ad_obj=ad, ad_id=123, adset_id=789,
                                             spend=100, sales=4,
                                             cost_per_sale=25)

        self.assertEqual(o.apply_to_window(window, dry_run=False, manual=True),
                         o.rules.get(title='High CPA on a new ad'))

        self.assertEqual(OptimizeNotification.objects.count(), 1)
        notify = OptimizeNotification.objects.first()
        self.assertEqual(notify.action, 'pause')
        self.assertEqual(notify.window.id, window.id)
        self.assertEqual(notify.optimizer.id, o.id)
