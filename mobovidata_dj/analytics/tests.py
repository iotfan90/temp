import datetime
import json
import logging
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import resolve
from django.test import RequestFactory, TestCase
from django.test.client import Client
from hashlib import md5
from unittest import skip

from .models import Customer, CustomerLifecycleTracking
from .views import tracking

User = get_user_model()

logger = logging.getLogger(__name__)


class TrackingAPITests(TestCase):
    """ Basic tests for routing and essential error handling for tracking
    function """
    def setUp(self):
        """ Every method needs access to the RequestFactory """
        self.factory = RequestFactory()
        self.request = self.factory.get('/api/tracking.gif')

    def test_tracking_returns_appropriate_status_code(self):
        """ Make sure /api/tracking.gif maps to tracking func """
        track = resolve('/api/tracking.gif')
        self.assertEqual(track.func, tracking)

    def test_returns_appropriate_response_code_and_text(self):
        resp = tracking(self.request)
        self.assertEquals(resp.status_code, 200)
        self.assertTrue('invalid get parameters' in resp.content)

    def test_returns_invalid_get_parameters(self):
        self.request.method = 'GET'
        self.request.GET = {
            'mvid' : '0000000',
        }
        resp = tracking(self.request)
        self.assertTrue('invalid get parameters' in resp.content)


class RegisterUserTests(TestCase):
    """ Tests on views.register_user
    """
    def setUp(self):
        """ Every method needs access to the Client """
        self.client = Client()

    def test_register_user_requires_ajax(self):
        """ ajax called to register_user should return result: success with a
        'uuid' key """
        c = self.client
        response = c.post('/api/register_user',
                          **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        response_content = json.loads(response.content)
        self.assertEquals(response_content['register_user_result'], 'success')

    def test_register_user_accepts_riid(self):
        """ register_user ajax calls accept an riid parameter """
        c = self.client
        response = c.post('/api/register_user', {'riid': 1234},
                          **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        response_content = json.loads(response.content)
        self.assertEquals(response_content['register_user_result'], 'success')
        self.assertTrue('uuid' in response_content)


class CheckUUIDTests(TestCase):
    """ Tests on views.check_uuid
    """
    def setUp(self):
        """ Every method needs access to the Client """
        self.client = Client()
        # response = self.client.post('/api/register_user',
        #  **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        # response_content = json.loads(response.content)
        # self.uuid = response_content['uuid']
        self.uuid = uuid.uuid4()
        self.riid = 123123123
        self.customer = Customer.objects.create(uuid=self.uuid, riid=self.riid)
        self.customer.save()

    def test_check_uuid_requires_ajax(self):
        """ ajax called to register_user should return result: success with a
        'uuid' key """
        c = self.client
        response = c.post('/api/check_uuid', {'mvid': self.uuid},
                          **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        response_content = json.loads(response.content)
        self.assertEquals(response_content['check_uuid_result'], 'success')


class UpdateCustomerTests(TestCase):
    """
    Tests on Customer.objects.update_customer method
    """
    def setUp(self):
        self.client = Client()
        # response = self.client.post('/api/register_user',
        #  **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        # response_content = json.loads(response.content)
        # self.uuid = response_content['uuid']
        self.uuid = uuid.uuid4()
        self.riid = 123123123
        self.customer = Customer.objects.create(uuid=self.uuid, riid=self.riid)
        self.customer.save()

    def test_customerlifecycletracking_saves_lifecycle_stage(self):
        """
        Ensures that set_lifecycle_stage_to_product saves that customer's
        lifecycle stage.
        :return:
        """
        (CustomerLifecycleTracking.objects
         .set_lifecycle_stage_to_product(123, customer=self.customer))
        self.assertEquals(self.customer.customerlifecycletracking.funnel_step,
                          700)


class CustomerLifecycleAttributesTests(TestCase):
    """
    Tests for missing lifecycle attributes don't raise Exceptions when called
    """
    def setUp(self):
        self.uuid = uuid.uuid4()
        self.riid = 123123123
        self.customer = Customer.objects.create(uuid=self.uuid, riid=self.riid)
        self.customer.save()
        self.customerlifecycletracking = CustomerLifecycleTracking.objects.create(
            customer=self.customer,
            funnel_step=0,
            lifecycle_messaging_stage=-1,
        )
        self.messaging_data = {}

    def test_missing_cart_id_returns_none(self):
        """
        Verifies that cart_id returns `None` if doesn't exist
        """
        if 'QUOTE_ID' not in self.messaging_data:
            self.assertIsNone(self.customerlifecycletracking.cart_id)

    def test_missing_noproduct_pageviews_returns_none(self):
        """
        Verifies that noproduct_pageviews returns `None` if doesn't exist
        """
        if 'PAGES' not in self.messaging_data:
            self.assertIsNone(self.customerlifecycletracking.noproduct_pageviews)

    def test_missing_product_pageviews_returns_none(self):
        """
        Verifies that product_pageviews returns `None` if doesn't exist
        """
        if 'PRODUCTS' not in self.messaging_data:
            self.assertIsNone(self.customerlifecycletracking.product_pageviews)


class OrderDetailsTests(TestCase):
    def setUp(self):
        self.order_id = '200805437'
        self.email = json.dumps("ying.wang@ice.com")
        self.date_from = json.dumps('2014-08-01')
        self.date_to = json.dumps('2016-09-01')
        self.date_to_wrong = json.dumps('2014-07-01')
        self.user = User.objects.create_user('test', 'test@mobovida.com',
                                             'test')
        self.client = Client()
        self.client.login(username='test', password='test')

    @skip
    def test_order_search(self):
        response_iid = self.client.get(
            '%s%s' % ('/api/order_lookup/?increment_id=', self.order_id),
            follow=True,
        )

        self.assertEqual(response_iid.status_code, 200)
        self.assertEqual(len(json.loads(response_iid.context['orders'])), 1)

        response_email = self.client.get(
            '%s%s' % ('/api/order_lookup/?customer_email=', self.email),
            follow=True,
        )
        self.assertEqual(response_email.status_code, 200)
        self.assertEqual(len(json.loads(response_email.context['orders'])), 1)
        response_iid_email = self.client.get(
            '%s%s%s%s' % ('/api/order_lookup/?increment_id=', self.order_id,
                          '&customer_email=', self.email),
            follow=True,
        )
        self.assertEqual(response_iid_email.status_code, 200)
        self.assertEqual(len(json.loads(response_iid_email.context['orders'])),
                         1)
        response_wrong_date = self.client.get(
            '%s%s%s%s' % ('/api/order_lookup/?increment_id=', self.order_id,
                          '&dateto=', self.date_to_wrong),
            follow=True,
        )
        self.assertEqual(response_wrong_date.status_code, 200)
        self.assertEqual(len(json.loads(response_wrong_date.context['orders'])),
                         0)


class TestMdFiveEmailEmails(TestCase):
    """
    Test return value when md5 is submitted to check_md5_emails when the md5
    doesn't exist in the db.
    Test return value when md5 is submitted to check_md5_emails when md5 DOES
    exist in the db.
    """
    def setUp(self):
        self.client = Client()

    def test_mystery_md5_case(self):
        """
        Unknown MD5 emails should return blacklisted: false.
        A post request with the following unknown md5s:
            { "q":
                [
                "046811a0a151cf419a9da90b82e02c88",
                "0721aa54a316d3fe767d1b08cf39f33f"
                ]
            }
        Should return:
            [
                {"md5":"046811a0a151cf419a9da90b82e02c88",
                "blacklisted":"false"
                },
                {"md5":"0721aa54a316d3fe767d1b08cf39f33f ",
                "blacklisted":"false"
                },
            ]
        """
        hashed_emails = [md5(e).hexdigest() for e in settings.RESPONSYS_EMAIL]
        expected_return = [{"md5": m, "blacklisted": "false"} for m in hashed_emails]
        post_content = {
                'q': hashed_emails
        }
        response = self.client.post(
            '/api/md5-optout/',
            json.dumps(post_content),
            content_type="application/json"
        )
        response_content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_content, expected_return)

    def test_known_md5_case(self):
        """
        Known md5s should return blacklisted true if they are opted out,
        false otherwise
        A post request with the following known md5s (first is opted out,
        second opted in):
            { "q":
                [
                "046811a0a151cf419a9da90b82e02c88",
                "0721aa54a316d3fe767d1b08cf39f33f"
                ]
            }
        Should return:
            [
                {"md5":"046811a0a151cf419a9da90b82e02c88",
                "blacklisted":"false"
                },
                {"md5":"0721aa54a316d3fe767d1b08cf39f33f ",
                "blacklisted":"true"
                },
            ]
        """
        from mobovidata_dj.responsys.models import OptedOutEmails
        # Create responsys_id_email records
        OptedOutEmails.objects.update_or_create(
                        riid=12345,
                        email=settings.RESPONSYS_EMAIL[0],
                        md5=md5(settings.RESPONSYS_EMAIL[0]).hexdigest(),
                        modified_dt=datetime.datetime.now(),
                        subscription_status=1
                    )
        OptedOutEmails.objects.update_or_create(
                        riid=54321,
                        email=settings.RESPONSYS_EMAIL[1],
                        md5=md5(settings.RESPONSYS_EMAIL[1]).hexdigest(),
                        created_at=datetime.datetime.now(),
                        subscription_status=0
                    )

        hashed_emails = [md5(e).hexdigest() for e in settings.RESPONSYS_EMAIL]
        expected_return = [
            {"md5": hashed_emails[0], "blacklisted": "false"},
            {"md5": hashed_emails[1], "blacklisted": "true"}
        ]

        post_content = {
                'q': hashed_emails
        }
        response = self.client.post(
            '/api/md5-optout/',
            json.dumps(post_content),
            content_type="application/json"
        )
        response_content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_content, expected_return)
