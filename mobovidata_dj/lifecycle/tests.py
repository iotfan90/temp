# -*- coding: utf-8 -*-
import sys

from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from logging import getLogger
from unittest import skip

from .fixtures import BUILD_ORDER_INFO_TEST
from .models import (OrderConfirmationEmailsLog, ShippingStatusTracking,
                     ProductReviewEntity)
from .utils import get_internal_search_products
from mobovidata_dj.responsys.tasks import get_update_responsys_token
from mobovidata_dj.lifecycle.utils import normalize_data_type
from modjento.models import SalesFlatOrder

log = getLogger(__name__)

TEST_CMD = ' '.join(sys.argv)


def skip_api_commands_unless_explicit(func):
    # These tests consume responsys API (with caching)
    if 'manage.py test' in TEST_CMD and 'lifecycle' in TEST_CMD:
        return func
    return skip(func)


# Isolated from the original code for testing purposes
def normalized_data(data, normal_fun, is_decimal=False):
        """
        Get formatted data for reviews
        :param data:
        :param normal_fun: function type
        :param is_decimal: boolean to check whether the field needs to be decimal.
        :return: data
        """
        if data:
            data = normal_fun(data)
        elif normal_fun == int:
            data = 0
        else:
            data = ''

        if not is_decimal:
            return data
        else:
            return Decimal.from_float(data).quantize(Decimal('0.0000'))


class OrderConfirmationEmailsTest(TestCase):

    def setUp(self):
        self.orders = SalesFlatOrder.objects.filter(customer_email=settings.RESPONSYS_EMAIL[0])

    def test_responsys_email_setting_works_and_has_order(self):
        self.assertIsNotNone(self.orders)

    def test_build_order_info(self):
        orders = SalesFlatOrder.objects.filter(increment_id='200198066')
        orders = orders.prefetch_related('salesflatorderitem_set',
                                         'billing_address',
                                         'shipping_address')
        order_map = { x.increment_id: x for x in orders }
        rg_orders = SalesFlatOrder.build_order_info(order_map.values())
        self.assertEqual(rg_orders, BUILD_ORDER_INFO_TEST)

    def test_check_order_sends_removes_existing_orders(self):
        updated_at = datetime.now()
        orders = SalesFlatOrder.objects.filter(customer_email='kenny@mobovida.com')[:2]
        orders_map = { x.increment_id: x for x in orders}
        OrderConfirmationEmailsLog.objects.create(
            order_id=orders[0].increment_id,
            order_updated_at=orders[0].updated_at,
            base_grand_total=orders[0].base_grand_total,
            response=1)
        new_orders_map = OrderConfirmationEmailsLog.check_order_sends(orders_map)
        self.assertIsNone(new_orders_map.get(orders[0].increment_id))
        self.assertIsNotNone(new_orders_map.get(orders[1].increment_id))

    def test_orders_with_same_order_id_different_totals_log_two_records(self):
        """
        Ensure that no order id is sent more than 2 emails
        """
        updated_at = datetime.now()
        orders = SalesFlatOrder.objects.filter(customer_email='kenny@mobovida.com')[:2]
        orders_map = {x.increment_id: x for x in orders}
        OrderConfirmationEmailsLog.objects.create(
            order_id=orders[0].increment_id,
            order_updated_at=orders[0].updated_at,
            base_grand_total=orders[0].base_grand_total,
            response=1)
        OrderConfirmationEmailsLog.objects.create(
            order_id=orders[0].increment_id,
            order_updated_at=orders[0].updated_at,
            base_grand_total=Decimal(999.99),
            response=1)
        new_orders_map = OrderConfirmationEmailsLog.check_order_sends(orders_map)
        counting = OrderConfirmationEmailsLog.objects.filter(order_id=orders[0].increment_id)
        self.assertEquals(2, counting.count())

    def test_orders_with_two_records_are_not_excluded_from_check_order_sends(self):
        """
        When an order id is included in OrderConfirmationEmailsLog two or more
        times, it should be automatically removed from the orders map.
        """
        updated_at = datetime.now()
        orders = SalesFlatOrder.objects.filter(customer_email='kenny@mobovida.com')[:2]
        orders_map = {x.increment_id: x for x in orders}

        OrderConfirmationEmailsLog.objects.create(
            order_id=orders[0].increment_id,
            order_updated_at=orders[0].updated_at,
            base_grand_total=Decimal(9999.99),
            response=1)
        OrderConfirmationEmailsLog.objects.create(
            order_id=orders[0].increment_id,
            order_updated_at=orders[0].updated_at,
            base_grand_total=Decimal(999.99),
            response=1)
        OrderConfirmationEmailsLog.objects.create(
            order_id=orders[0].increment_id,
            order_updated_at=orders[0].updated_at,
            base_grand_total=Decimal(1000.00),
            response=1)
        new_orders_map = OrderConfirmationEmailsLog.check_order_sends(orders_map)
        self.assertIsNone(new_orders_map.get(orders[0].increment_id))
        self.assertIsNotNone(new_orders_map.get(orders[1].increment_id))


class ProductReviewSubmitTest(TestCase):

    def setUp(self):
        """ Every method needs access to the Client """
        self.client = Client()

    def test_product_review_url_returns_200_status_code(self):
        """
        A url with a valid order_id and product_id should return a 200 status code
        """
        PRODUCT_ID = 246
        ORDER_ID = 200198066
        RIID = 274399105
        c = self.client
        response = c.get(
            '/lifecycle/product-review/',
            {
                'product_id': PRODUCT_ID,
                'order_id': ORDER_ID,
                'riid': RIID
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_product_review_url_with_bad_order_id_returns_check_product_id_order_id_message(self):
        """
        A url with an invalid order_id should return a messaging saying 'Please
        check the product id and order id'
        :return:
        """
        PRODUCT_ID = 246
        ORDER_ID = 123
        RIID = 274399105
        c = self.client
        response = c.get(
            '/lifecycle/product-review/',
            {
                'product_id': PRODUCT_ID,
                'order_id': ORDER_ID,
                'riid': RIID
            },
        )
        self.assertEquals(response.content.index('Please check the product id and order id'), 8536)

    def test_post_to_product_review_view(self):
        """
        A valid post request to the product review view should log the data into the db.
        :return:
        """
        c = self.client
        post_content = {
            'name': 'angry penguin',
            'title': 'not enough ice',
            'content': 'Too much water around here! It should be colder..',
            'rating': 1,
            'email': 'notmadjustunhappy@southpole.gov',
            'order_id': '12345',
            'product_id': 123,
            'price_paid': 10.99,
            'riid': '999999',
        }
        response = c.post(
            '/lifecycle/product-review/',
            post_content
        )
        self.assertTrue(ProductReviewEntity.objects.filter(order_id='12345').exists())

class NPSEmailTests(TestCase):
    def setUp(self):
        """
        Create shipping confirmation object
        """
        self.orders = SalesFlatOrder.objects.filter(customer_email=settings.RESPONSYS_EMAIL[0])
        unsent_confirmation = ShippingStatusTracking.objects.create(
            order_id=self.orders[0].increment_id,
            event='Delivered',
            courier='MAILMAN',
            tracking_number='1234512345',
            confirmation_sent=0
        )
        sent_confirmation = ShippingStatusTracking.objects.create(
            order_id=self.orders[1].increment_id,
            event='Delivered',
            courier='MAILMAN',
            tracking_number='1234512345',
            confirmation_sent=0
        )
        get_update_responsys_token()

    def test_get_order_ids(self):
        """
        End to end test of NPS function. Ensures that successful sends lead to updated table rows.
        :return:
        """
        response = ShippingStatusTracking.send_nps_emails()
        order_ids = ShippingStatusTracking.get_order_ids()
        print order_ids
        self.assertEqual(order_ids, [])


class SearchAbandonTests(TestCase):
    def setUp(self):
        self.customers = [1]
        self.customer_data = {c: {} for c in self.customers}

    def test_get_internal_search_products(self):
        """
        Tests get_internal_search_products method
        @return:
        """
        internal_search_products = get_internal_search_products('bolt')
        product_key_types = {
            'url_path': unicode,
            'name': unicode,
            'image': unicode,
            'price': float,
            'special_price': float,
            'save_dollars': float,
            'save_percent': float
        }
        # Check that the structure is a list
        self.assertIsInstance(internal_search_products, list)
        # Check that the first element in the list is a dict
        self.assertIsInstance(internal_search_products[0], dict)
        # Make sure the required keys exist
        for each in internal_search_products[0].keys():
            self.assertIn(each, product_key_types.keys())
        # Make sure there are the same number of keys as required
        self.assertEquals(len(internal_search_products[0].keys()), len(product_key_types.keys()))
        # Test types are correct
        for each in internal_search_products[0].items():
            self.assertEquals(
                type(each[1]), product_key_types.get(each[0]),
                msg='%s <> %s. Values: %s, %s' % (type(each[1]), product_key_types.get(each[0]), each[1], each[0])
            )

    def test_get_internal_search_products_no_results(self):
        """
        Tests the case when the user's search query yields no results
        @return:
        """
        internal_search_products = get_internal_search_products('otterbox')
        self.assertEqual(internal_search_products, [])

    def test_get_internal_search_products_non_ascii(self):
        """
        Tests the case when the user's search query contains non-ascii characters
        @return:
        """
        internal_search_products = get_internal_search_products('360° clear')
        # Test will fail if it raises an error in the process


class StrandsProductTest(TestCase):
    def setUp(self):
        self.customers = [1]
        self.customer_data = {c: {} for c in self.customers}
        self.strands_id = 186456

    def test_get_strands_products(self):
        """
        Tests get_strands_products method
        @return:
        """
        from mobovidata_dj.lifecycle.utils import get_strands_products
        product_key_types = {
            'url_path': unicode,
            'name': unicode,
            'image': unicode,
            'price': float,
            'special_price': float,
            'save_dollars': float,
            'save_percent': float
        }
        strands_products = get_strands_products(self.strands_id)
        # Check that the structure is a list
        self.assertIsInstance(strands_products, list)
        # Check that the first element in the list is a dict
        self.assertIsInstance(strands_products[0], dict)
        # Make sure the required keys exist
        for each in strands_products[0].keys():
            self.assertIn(each, product_key_types.keys())
        # Make sure there are the same number of keys as required
        self.assertEquals(len(strands_products[0].keys()), len(product_key_types.keys()))
        # Test types are correct
        for each in strands_products[0].items():
            self.assertEquals(
                type(each[1]), product_key_types.get(each[0]),
                msg='%s <> %s. Values: %s, %s' % (
                    type(each[1]), product_key_types.get(each[0]), each[1], each[0]
                )
            )


class DataNormalizersTest(TestCase):

    def setUp(self):
        """ Every method needs access to the Client """
        self.client = Client()

    def test_normalized_data(self):
        """
        Tests the normalize_data function
        @return:
        """
        data = normalized_data('', int)
        self.assertEqual(data, 0)

    def test_normalize_data_type(self):
        """
        Tests that for any kind of input the output of normalize_data_type is utf-encodable
        @return:
        """
        inputs = ['string', Decimal(4.6), datetime.now()]
        for input in inputs:
            normalize_data_type(input).encode('utf-8')
            # Test will fail if it raises an error in the process
