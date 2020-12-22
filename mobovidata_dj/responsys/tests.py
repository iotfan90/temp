from django.conf import settings
from django.test import TestCase
from django.test.client import Client

from .models import OptedOutEmails
from .tasks import get_update_responsys_token
from .views import UnsubForm
from mobovidata_dj.lifecycle.models import ShippingStatusTracking
from modjento.models import SalesFlatOrder


# class NPSEmailTests(TestCase):
#     def setUp(self):
#         """
#         Create shipping confirmation object
#         """
#         order = SalesFlatOrder.objects.filter(customer_email=settings.RESPONSYS_EMAIL[0])
#         unsent_confirmation = ShippingStatusTracking.objects.create(
#             order_id = order[0].increment_id,
#             event = 'Delivered',
#             courier = 'MAILMAN',
#             tracking_number = '1234512345',
#             confirmation_sent = 0
#         )
#         sent_confirmation = ShippingStatusTracking.objects.create(
#             order_id = order[1].increment_id,
#             event = 'Delivered',
#             courier = 'MAILMAN',
#             tracking_number = '1234512345',
#             confirmation_sent = 1
#         )
#         get_update_responsys_token()
#
#
#     def test_send_nps_emails_task(self):
#         """
#         Tests the full send_nps_emails function. Expect to see an email in your inbox.
#         :return:
#         """
#         # { 'rg_response': sends, # list of responses from Responsys
#         #   'count': 'Message with information about how many emails were sent.' }
#         response = send_nps_emails()
#         for each in response.get('rg_response'):
#             print each.json()
#         self.assertEqual(response['count'], 1)
#         self.assertEqual(response['rg_response'].content, 'yes')


class OptOutEmailsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_opt_out_email_updates_optedoutemails_table(self):
        """
        Opt out requests should also add an opt out record the responsysidemail table
        :return:
        """
        get_update_responsys_token()
        UnsubForm().opt_out_email(email_address=settings.RESPONSYS_EMAIL[0])
        record = OptedOutEmails.objects.get(email=settings.RESPONSYS_EMAIL[0])
        self.assertEqual(record.subscription_status, 0)


class EmailPreferencesTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_email_preferences_unsub_updates_optedoutemails_table(self):
        """
        Post requests to email-preferences should update the OptedOutEmails table
        :return:
        """
        get_update_responsys_token()
        c = self.client
        post_content = {
            'email_address': settings.RESPONSYS_EMAIL[0],
            'EMAIL_PERMISSION_STATUS_': 1,
        }
        response = self.client.post(
            '/responsys/email-preferences/',
            post_content
        )
        record = OptedOutEmails.objects.get(email=settings.RESPONSYS_EMAIL[0])
        self.assertEqual(record.subscription_status, 0)
