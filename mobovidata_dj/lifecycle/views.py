# encoding: utf-8
from __future__ import unicode_literals

import base64
import csv
import json
import logging
import pytz
import requests

from datetime import datetime, timedelta
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import StreamingHttpResponse, HttpResponse, JsonResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin

from .models import (Campaign, OopsEmailSendLog, OrderConfirmationEmailsLog,
                     OrderReviewSendLog, ProductReviewEntity,  SenderLog,
                     ShippingStatusTracking)
from .utils import (normalize_data_type, make_responsys_request_payload,
                    get_strands_products)
from mobovidata_dj.analytics.models import (CustomerLifecycleTracking,
                                            CustomerOrder,
                                            CustomerStrandsId)
from mobovidata_dj.responsys.models import ResponsysCredential
from mobovidata_dj.responsys.utils import ResponsysApi
from modjento.models import EavAttribute, SalesFlatOrder, SalesFlatOrderItem

logger = logging.getLogger(__name__)


@login_required()
def campaign_preview(request):
    """
    Filter customers and Get campaign info from Campaign model and CustomerLifecycleTracking
    In order to select the campaign, we need to pull all the campaigns from campaign object.
    For each campaign, we need to get the modified time and riid, lc data, lc message from CustomerLifecycleTracking
    :return: Http response of campaigns info
    """
    c = Campaign.objects.all()
    campaign_info = []
    for campaign in c:
        results = campaign.run(preview_only=True)
        recipients = []
        if results['customers']:
            for r in CustomerLifecycleTracking.objects.filter(
                customer__in=[c.uuid for c in results['customers']]
            ).values('customer__riid',
                     'lifecycle_messaging_data',
                     'lifecycle_messaging_stage',
                     'funnel_step',
                     'modified_dt'):
                r['modified_dt'] = r['modified_dt'].strftime('%Y-%m-%d %H:%M:%S')
                recipients.append(r)

        campaign_info.append({'campaign': campaign.name,
                              'description': campaign.description,
                              'funnel_step': campaign.funnel_step,
                              'lifecycle_messaging_stage': campaign.lifecycle_messaging_stage,
                              'num_recipients': len(recipients),
                              'product_attributes': results['attributes']['product_attributes'],
                              'recipient_data': recipients,
                              'product_string_example': results['attributes']['product_string']})

    return render_to_response('campaign_preview.html',
                              {'campaigns': campaign_info},
                              context_instance=RequestContext(request))


class LifecycleLogView(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'campaign_logs.html'
    login_url = '/accounts/login'

    def get(self, request):
        """
        Get campaign log data for page campaign_logs.html, each page has at most 100 logs
        In order to show the log lists, we need the info of logs. If there are too many logs,
        we will use paginator to limit the numbers of logs in each page.
        :param request:
        :return: Http response of campaign logs data and pages info
        """
        paginator = Paginator(SenderLog.objects.all().values('campaign_id',
                                                             'response',
                                                             'send_datetime').order_by('-send_datetime'), 100)

        page = request.GET.get('page')
        try:
            log_list = paginator.page(page)
        except PageNotAnInteger:
            log_list = paginator.page(1)
        except EmptyPage:
            log_list = paginator.page(paginator.num_pages)

        logs = []
        for log in log_list:
            log['campaign'] = Campaign.objects.get(id=log['campaign_id']).name
            log['send_datetime'] = log['send_datetime'].strftime('%Y-%m-%d %H:%M:%S')
            log['num_successful_sends'] = len(
                [l for l in eval(log['response'])
                 if isinstance(eval(log.get('response', '')), list)
                 and l.get('success', '')]
            )
            logs.append(log)

        if paginator.num_pages > 10:
            if log_list.number > 5:
                max_page = log_list.number + 5 if log_list.number + 5 < paginator.num_pages else paginator.num_pages
                page_ranges = range(log_list.number - 5, max_page)
            else:
                page_ranges = range(1, 6)
        else:
            page_ranges = list(paginator.page_range)
        context = {
            'page_data': json.dumps({'current': log_list.number,
                                     'previous': log_list.has_previous(),
                                     'next': log_list.has_next(),
                                     'pages': page_ranges,
                                     'last_page': paginator.num_pages}),
            'logs': json.dumps(logs)
        }

        return self.render_to_response(context)


class SendOrderConfirmationEmail(LoginRequiredMixin, TemplateResponseMixin, View):
    """
    This is to get the new orders and send the email through Responsys Api
    """
    def __init__(self):
        """
        Constructor for this class.
        :return:
        """
        super(SendOrderConfirmationEmail, self).__init__()
        self.PREVIOUS_ORDERS = []
        self.auth = ResponsysCredential.objects.all()[0]
        self.headers = {'Authorization': self.auth.token}
        self.campaign_name = 'CO_OrderConfirmation_V2_Trans'
        self.campaign_endpoint = '%s/rest/api/v1.1/campaigns/%s/email' % (self.auth.endpoint, self.campaign_name)
        self.list_name = 'CONTACT_LIST'
        self.product_attributes = []
        self.order_ids = []
        self.order_details = {}

    def get(self, request):
        response = self.run_order_confirmation(preview_only=True)
        if response is not None:
            json_info = JsonResponse({
                'orders': response
            })
        else:
            json_info = JsonResponse({
                'message': 'There are no orders in 5 mins'
            })
        return json_info

    def run_order_confirmation(self, **kwargs):
        """
        To get the new orders in past 1 hours. Checks each order to see if we've
        already sent an order confirm email by comparing order_id and
        order_grand_total to the emails we've sent recently.
        :param kwargs:
        :return:
        """
        if kwargs.get('lookback_hours'):
            lookback_hours = kwargs.get('lookback_hours')
        else:
            lookback_hours = 1
        if settings.DEBUG:
            if kwargs.get('order_id'):
                orders = SalesFlatOrder.objects.filter(increment_id=kwargs.get('order_id'))
            else:
                orders = SalesFlatOrder.objects.filter(customer_email=settings.RESPONSYS_EMAIL[0])
        else:
            current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
            earlier_time = current_time - timedelta(hours=lookback_hours)
            orders = SalesFlatOrder.objects.filter(created_at__gte=earlier_time, store_id=2)


        # orders = orders.prefetch_related('salesflatorderitem_set', 'billing_address', 'shipping_address')
        order_map = {x.increment_id: x for x in orders}
        order_map = OrderConfirmationEmailsLog.check_order_sends(order_map)
        if not order_map:
            return None

        customer_orders = order_map.values()
        rg_orders = SalesFlatOrder.build_order_info(customer_orders)
        for r in rg_orders:
            self.order_ids.append(r['order_id'])
            self.order_details[r['order_id']] = {
                'order_updated_at': r['created_at'],
                'order_grand_total': r['grand_total']
            }
        rg_orders = CustomerStrandsId.objects.append_strands_products(rg_orders)
        if not kwargs.get('preview_only', ''):
            return self.send_responsys_email(rg_orders)
        return rg_orders

    def send_responsys_email(self, data, test_only=False):
        """
        :param data:
        :param test_only: Binary. When True, this returns the json object we'll actually send to Responsys.
        :return:
        """
        if len(data) == 0:
            return None
        data = data[:999]
        if settings.DEBUG:
            data = [data[0]]
        request_payload = make_responsys_request_payload(data)
        if test_only:
            return request_payload
        r = requests.post(self.campaign_endpoint, json=request_payload, headers=self.headers)
        if r.status_code == 200:
            r_content = json.loads(r.content)
            self.process_send_result(r_content)
            return r_content
        logger.error('The request to post the data to CampaignEndpoint failed : %s', r.reason, extra=locals())
        return {
            'message': r.reason
        }

    def process_send_result(self, r_content):
        """
        Update OrderConfirmationSendLog with the results of each attempted call to Responsys.
        :type r_content: dict
        :param r_content: Response from Responsys call
        :return: None
        """
        for n, r in enumerate(r_content):
            order_id = self.order_ids[n]
            OrderConfirmationEmailsLog.objects.create(
                order_id=order_id,
                response=r['success'],
                order_updated_at=self.order_details[order_id]['order_updated_at'],
                base_grand_total=self.order_details[order_id]['order_grand_total']
            )

    def make_request_payload(self, data):
        """
        Transforms list of order data dicitonaries into format suitable for responsys.
        :type data: list(dict)
        :rtype: tuple(dict, dict)
        :return: Request payload for Responsys API call, order_id-keyed dictionary with information for
        OrderConfirmationSendLog table.
        """
        self.product_attributes = {'products': data[0]['products'][0].keys()}
        recipients = []
        orders = data
        for d in orders:
            if d.get('includes_strands', '') == 'yes':
                self.product_attributes['strands_products'] = d['strands_products'][0].keys()

        if settings.DEBUG:
            email_to_riids = self.get_riid_from_email([settings.RESPONSYS_EMAIL[0]])
        else:
            email_to_riids = self.get_riid_from_email([o.get('customer_email', '') for o in orders])
        for order in orders:
            opt_data = []
            opt_products_data = []
            opt_strands_products_data = []
            opt_data.append({'name': 'product_attributes',
                             'value': ';;-;;'.join(map(str, self.product_attributes['products']))})
            if order.get('includes_strands', '') == 'yes':
                opt_data.append({'name': 'strands_product_attributes',
                                 'value': ';;-;;'.join(map(str, self.product_attributes['strands_products']))})
            customer_email = order.get('customer_email', '')
            opt_data.append({'name': 'riid', 'value': email_to_riids.get(customer_email)})
            for k, v in order.items():
                if k == 'products':
                    for product in v:
                        opt_products = ';-;'.join(map(str, [
                            normalize_data_type(product.get(p_k))
                            for p_k in self.product_attributes['products']]))
                        opt_products_data.append(opt_products)
                    opt_products_data = ';;-;;'.join(opt_products_data)
                    opt_data.append({'name': 'products', 'value': opt_products_data})
                elif k == 'strands_products':
                    for product in v:
                        # self.strands_product_attributes = k['strands_products'][0].keys()
                        opt_products = ';-;'.join(map(str, [
                                normalize_data_type(product.get(p_k))
                                for p_k in self.product_attributes['strands_products']]))
                        opt_strands_products_data.append(opt_products)
                    opt_strands_products_data = ';;-;;'.join(opt_strands_products_data)
                    opt_data.append({'name': 'strands_products', 'value': opt_strands_products_data})
                elif k in ('shipping_address', 'billing_address'):
                    # opt_data.append({'name': k, 'value': self.get_formated_address(self.normalize_data_type(v), k)})
                    address_map = {
                        'city': '%s_CITY',
                        'firstname': '%s_FNAME',
                        'lastname': '%s_LNAME',
                        'telephone': '%s_PHONE',
                        'region': '%s_STATE',
                        'street': '%s_STREET',
                        'postcode': '%s_ZIP'
                    }
                    v = normalize_data_type(v)
                    for original, replacement in address_map.iteritems():
                        opt_data.append({'name': replacement % k.split('_')[0].upper(), 'value': v[original]})
                else:
                    opt_data.append({'name': k, 'value': normalize_data_type(v)})
            if not settings.DEBUG:
                riid = email_to_riids.get(customer_email)
            else:
                riid = email_to_riids.get(settings.RESPONSYS_EMAIL[0])
            recipient = {
                'recipient': {
                    "recipientId": riid,
                    'listName': {
                        'folderName': '!MageData',
                        'objectName': 'CONTACT_LIST'
                    },
                    'emailFormat': 'HTML_FORMAT',
                },
                'optionalData': opt_data
            }
            recipients.append(recipient)
        return {'recipientData': recipients}

    def get_riid_from_email(self, email):
        """
        Returns RIIDs found for a given list of email addresses.
        :type email: list()
        :rtype: dict(str, str)
        """
        merge_endpoint = '%s/rest/api/v1.1/lists/%s/members' % (self.auth.endpoint, self.list_name)
        mp_riids = {}
        customer_emails = list(set(email))
        email_chunks = [customer_emails[x:x+200] for x in xrange(0, len(customer_emails), 200)]
        for chunk in email_chunks:
            data = {
                'recordData': {
                    'fieldNames': ['email_address_'],
                    'records': [[e] for e in chunk],
                },
                'mergeRule': {
                    'htmlValue': 'H',
                    'optinValue': 'I',
                    'textValue': 'T',
                    'insertOnNoMatch': True,
                    'updateOnMatch': 'REPLACE_ALL',
                    'matchOperator': 'NONE',
                    'matchColumnName1': 'email_address_',
                    'optoutValue': 'O',
                    'defaultPermissionStatus': 'OPTIN'
                }
            }
            r = requests.post(merge_endpoint, json=data, headers=self.headers)
            if r.status_code == 200:
                riids = json.loads(r.content)['recordData']['records']
                rv = {e: riids[ix][0] for ix, e in enumerate(chunk)}
                mp_riids.update(rv)
            else:
                logger.error('Failed to request Responsys Api custom event: %s' % r.reason, extra=locals())
                return JsonResponse({'message': 'Failed to request Responsys Api custom event'})

        return mp_riids


class SendShippingConfirmationEmail(View):
    """
    Gets list of customers who have updates to their order tracking and have not
    been sent an email and sends them a shipping confirmation email
    """
    def __init__(self):
        super(SendShippingConfirmationEmail, self).__init__()
        self.auth = ResponsysCredential.objects.all()[0]
        self.headers = {'Authorization': self.auth.token}
        self.campaign_name = 'CO_ShipConfirmation_Trans'
        self.campaign_endpoint = '%s/rest/api/v1.1/campaigns/%s/email' % (self.auth.endpoint, self.campaign_name)
        self.list_name = 'CONTACT_LIST'
        self.order_ids = []

    def run_shipping_confirmation(self, **kwargs):
        """
        To get the new orders in past 24 hours. Checks each order to see if we've already sent a
        shipconfirm email by comparing order_id and confirmation_sent to the emails we've sent recently.
        """
        orders = ShippingStatusTracking.objects.filter(
            confirmation_sent=False,
            event='InTransit'
        )
        order_ids = [o.order_id for o in orders]
        self.order_ids = order_ids
        emails = SalesFlatOrder.objects.values_list('customer_email', flat=True).filter(
            increment_id__in=order_ids)
        rg_orders = []
        for i, order in enumerate(orders):
            order_info = {
                'order_id': order.order_id,
                'tracking_number': order.tracking_number,
                'courier': order.courier,
                'updated_at': order.updated_at,
                'includes_strands': 'no',
                'customer_email': emails[i],
            }
            rg_orders.append(order_info)
        # Add strands product recommendations
        # rg_orders = self.append_strands_products(rg_orders)
        if not kwargs.get('preview_only', ''):
            for each in orders:
                each.confirmation_sent = True
                each.save()
            return self.call_responsys(rg_orders)
        return rg_orders

    def call_responsys(self, data):
        if len(data) == 0:
            return None
        request_payload = self.make_request_payload(data)
        r = requests.post(self.campaign_endpoint, json=request_payload, headers=self.headers)
        if r.status_code == 200:
            r_content = json.loads(r.content)
            return r_content
        logger.error('The request to post the data to CampaignEndpoint failed : %s' % r.reason, extra=locals())
        return {'message': r.reason}

    def make_request_payload(self, data):
        """
        Transforms list of order data dicitonaries into format suitable for responsys.
        :type data: list(dict)
        :rtype: tuple(dict, dict)
        :return: Request payload for Responsys API call, order_id-keyed dictionary with information for
        OrderConfirmationSendLog table.
        """
        recipients = []
        orders = data

        # for d in orders:
        #     if d.get('includes_strands', '') == 'yes':
        #         self.product_attributes['strands_products'] = d['strands_products'][0].keys()

        email_to_riids = self.get_riid_from_email([o.get('customer_email', '') for o in orders])

        if settings.DEBUG:
            email_to_riids.update(self.get_riid_from_email(settings.RESPONSYS_EMAIL))

        for order in orders:
            opt_data = []
            customer = SalesFlatOrder.objects.get(increment_id=order.get('order_id'))
            opt_data.append({'name': 'ORDER_ID',         'value': order.get('order_id')})
            opt_data.append({'name': 'BILLING_FNAME',    'value': customer.customer_firstname})
            opt_data.append({'name': 'TRACKING_NUMBER',  'value': order.get('tracking_number', '')})
            opt_data.append({'name': 'COURIER',          'value': order.get('courier', '')})
            opt_data.append({'name': 'includes_strands', 'value': 'yes'})

            if not settings.DEBUG:
                riid = email_to_riids.get(customer.customer_email)
            else:
                riid = email_to_riids.get(settings.RESPONSYS_EMAIL[0])
            recipient = {
                'recipient': {
                    'recipientId': riid,
                    'listName': {
                        'folderName': '!MageData',
                        'objectName': self.list_name
                    },
                    'emailFormat': 'HTML_FORMAT',
                },
                'optionalData': opt_data
            }
            recipients.append(recipient)
        return {'recipientData': recipients}

    def get_riid_from_email(self, email):
        """
        Returns RIID found for a given email address.
        :type email: list()
        :rtype: dict(str: str)
        """
        merge_endpoint = '%s/rest/api/v1.1/lists/%s/members' % (self.auth.endpoint, self.list_name)
        mp_riids = {}
        customer_emails = list(set(email))
        # Split customer emails into 200 email chunks
        email_chunks = [customer_emails[x:x+200] for x in xrange(0, len(customer_emails), 200)]
        for chunk in email_chunks:
            data = {
                'recordData': {
                    'fieldNames': ['email_address_'],
                    'records': [[e] for e in chunk],
                },
                'mergeRule': {
                    'htmlValue': 'H',
                    'optinValue': 'I',
                    'textValue': 'T',
                    'insertOnNoMatch': True,
                    'updateOnMatch': 'REPLACE_ALL',
                    'matchOperator': 'NONE',
                    'matchColumnName1': 'email_address_',
                    'optoutValue': 'O',
                    'defaultPermissionStatus': 'OPTIN'
                }
            }
            r = requests.post(merge_endpoint, json=data, headers=self.headers)
            if r.status_code == 200:
                riids = json.loads(r.content)['recordData']['records']
                rv = {e: riids[ix][0] for ix, e in enumerate(chunk)}
                mp_riids.update(rv)
            else:
                logger.error('Failed to request Responsys Api custom event: %s' % r.reason, extra=locals())
                return JsonResponse({'message': 'Failed to request Responsys Api custom event'})

        return mp_riids

    def append_strands_products(self, rg_orders):
        # Run through rg_orders and check for strands_id in map_order_id_strands_id
        map_order_id_strands_id = self.map_order_ids_strands_ids(rg_orders)
        for r in rg_orders:
            if map_order_id_strands_id.get(r['order_id'], False):
                strands_products = get_strands_products(map_order_id_strands_id[r['order_id']])
                # strands_products = self.get_strands_products(map_order_id_strands_id[r['order_id']])
                if len(strands_products) > 0:
                    r['includes_strands'] = 'yes'
                    r['strands_products'] = strands_products
        return rg_orders

    def map_order_ids_strands_ids(self, rg_orders):
        customer_orders = CustomerOrder.objects.filter(order_id__in=[r['order_id'] for r in rg_orders])
        map_order_id_strands_id = {}
        if customer_orders.exists():
            for o in customer_orders:
                session = o.session
                customer = session.customer
                if not hasattr(customer, 'customerstrandsid'):
                    continue
                map_order_id_strands_id[o.order_id] = customer.customerstrandsid.strands_id
        return map_order_id_strands_id

    # def get_strands_products(self, strands_id):
    #     params = {
    #         'apid': settings.STRANDS_APID,
    #         'tpl': 'conf_3',
    #         'format': 'json',
    #         'user': strands_id,
    #         'amount': 6,
    #     }
    #     response = requests.get(settings.STRANDS_ENDPOINT, params=params)
    #     strands_products = []
    #     if response.status_code == 200:
    #         results = json.loads(response.content)
    #         for r in results['result']['recommendations']:
    #             product = r['metadata']
    #             p = {
    #                 'url_path': product.get('link', ''),
    #                 'name': product.get('name', ''),
    #                 'special_price': float(product.get('price', '')),
    #                 'image': 'http:%s' % product.get('picture', ''),
    #                 'price': float(product['properties'].get('cretail_price', [0])[0]),
    #             }
    #             try:
    #                 p['save_percent'] = round(
    #                     (p['price'] - p['special_price']) / p['price'], 4) * 100
    #                 p['save_dollars'] = int(round(p['price'] - p['special_price'], 0))
    #             except KeyError:
    #                 p['save_percent'] = 0
    #                 p['save_dollars'] = 0
    #                 p['special_price'] = p['price']
    #             strands_products.append(p)
    #         # customer_data[customer]['strands_product_attributes'] = ';;-;;'.join(strands_products[0].keys())
    #     return strands_products

    def process_send_result(self, r_content):
        """
        Update ShippingStatusTracking with the results of each attempted call to Responsys.
        :type r_content: dict
        :param r_content: Response from Responsys call
        :return: None
        """
        for n, r in enumerate(r_content):
            order_id = self.order_ids[n]
            ShippingStatusTracking.objects.update_or_create(
                order_id=order_id,
                defaults={
                    'confirmation_sent': r['success']
                }
            )


class Echo(object):
    """
    An object that implements just the write method of the file-like interface
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def lifecycle_log_csv(request):
    """A view that streams a large CSV file."""
    # Generate a sequence of rows. The range is based on the maximum number of
    # rows that can be handled by a single sheet in most spreadsheet
    # applications.
    current_month = datetime.now()
    filter_month = current_month - timedelta(days=30)
    logs = [['riid', 'campaign', 'send_date', 'send_hour']]
    for log in SenderLog.objects.filter(send_datetime__gte=filter_month):
        campaign = log.campaign.name
        send_date = log.send_datetime.day
        send_hour = log.send_datetime.hour
        response = eval(log.response)
        for r in response:
            if isinstance(r, dict):
                if r.get('success', False):
                    logs.append([r['recipientId'], campaign, send_date, send_hour])
    # rows = (["Row {}".format(idx), str(idx)] for idx in range(700000))
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in logs),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="individual_send_logs.csv"'
    return response


class CustomersCanceledOrder(LoginRequiredMixin, TemplateResponseMixin, View):
    """
    Scans the Mage DB for orders that have been canceled in the past 24 hours, and update info in Responsys
    """
    def __init__(self):
        """
        Initialize the class variable
        """
        super(CustomersCanceledOrder, self).__init__()
        self.auth = ResponsysCredential.objects.all()[0]
        self.headers = {'Authorization': self.auth.token}
        self.folder_name = '!MageData'
        self.table = 'ORDERS'
        self.step = 200
        if self.auth.endpoint.endswith('/'):
            self.table_endpoint = '%srest/api/v1.1/folders/%s/suppData/%s/members' % (
                self.auth.endpoint, self.folder_name, self.table)
        else:
            self.table_endpoint = '%s/rest/api/v1.1/folders/%s/suppData/%s/members' % (
                self.auth.endpoint, self.folder_name, self.table)

    def get(self, request):
        """
        Get a list of customer riids who canceled their order and call responsys api to exclude them from email list
        """
        response = self.exclude_canceled_order()
        return response

    def exclude_canceled_order(self):
        if not settings.DEBUG:
            current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
            earlier_time = current_time - timedelta(hours=24)
            canceled_orders = SalesFlatOrder.objects.filter(
                status='canceled', created_at__gte=earlier_time
            ).values_list('increment_id', flat=True)
        else:
            canceled_orders = ['200491619']
        canceled_orders = list(canceled_orders)
        if not canceled_orders:
            return JsonResponse({
                'message': 'No orders have been canceled in past 24 hours',
                'success': True
            })
        values_list = CustomerOrder.objects.filter(order_id__in=canceled_orders).values_list(
            'order_id', 'session__customer_id', 'session_id', 'session__customer__riid')
        riid_order_ids = []
        for order_id, uuid, session_id, riid in values_list:
            riid_order_ids.append(['%s' % riid, '%s' % order_id, '1'])
        while riid_order_ids:
            customers = riid_order_ids[0:self.step]
            riid_order_ids = riid_order_ids[self.step:]
            request_data = {
                'recordData': {
                    'fieldNames': ['RIID_', 'ORDER_ID', 'IS_CANCELED'],
                    'records': customers,
                    'mapTemplateName': ''
                },
                'insertOnNoMatch': True,
                'updateOnMatch': 'REPLACE_ALL'
            }
            response = requests.post(self.table_endpoint, json=request_data, headers=self.headers)
            response_content = json.loads(response.content)
            if response.status_code != 200:
                return JsonResponse(response_content)
        return JsonResponse({
            'message': 'Successfully called Responsys Api',
            'success': True,
        })


class ProductReview(TemplateResponseMixin, View):
    template_name = "product_review.html"

    def __init__(self):
        super(ProductReview, self).__init__()

    def get(self, request):
        authenticated = True if request.user.is_authenticated() else False
        stars = [
            u'⭐☆☆☆☆',
            u'⭐⭐☆☆☆',
            u'⭐⭐⭐☆☆',
            u'⭐⭐⭐⭐☆',
            u'⭐⭐⭐⭐⭐',
        ]
        products, email, product, order_id, strands_products = [], '', {}, '', []
        order_id = request.GET.get('order_id')
        product_id = request.GET.get('product_id')
        riid = request.GET.get('dz_riid')
        if order_id and product_id and riid:
            product_id, order_id = int(product_id), '%s' % order_id
            product = self.get_order_details(product_id, order_id)
            order = SalesFlatOrder.objects.filter(increment_id=order_id).values_list('customer_email', flat=True)
            email = order[0] if order else ''
            strands_products = self.get_strands(riid)
            print email
            print product_id
            print order_id
        return self.render_to_response(
            context={
                'stars': json.dumps(stars),
                'email': json.dumps(email),
                'product': json.dumps(product),
                'order_id': json.dumps(order_id),
                'strands_products': json.dumps(strands_products),
                'authenticated': json.dumps(authenticated),
                'riid': json.dumps(riid),
                'product_id': json.dumps(product_id),
            }
        )

    def get_order_details(self, product_id, order_id):
        product = SalesFlatOrderItem.objects.filter(product_id=product_id, order__increment_id=order_id).values(
            'price',
            'name'
        )
        if product.count() == 0 or product.count() > 1:
            print 'Found 0 products'
            return None
        else:
            rg_fields = ['name', 'image']
            p_attr = EavAttribute.objects.get_values(
                [product_id],
                field_names=rg_fields,
            )
            data = p_attr.get(product_id, {})
            if data.get('image', None) and data.get('image').startswith('URL/'):
                image = data.get('image').replace('URL', 'http://cellularoutfitter.com/media/catalog/product')
            else:
                image = 'http://cellularoutfitter.com/media/catalog/product%s' % (data.get('image',))
            product_info = {
                'product_id': product_id,
                'price': '%.2f' % product[0].get('price', 0.00),
                'name': product[0].get('name', ''),
                'image': image,
            }
            print 'FOUND PRODUCTS!'
            print product_info
            return product_info

    def get_strands(self, riid):
        strands = CustomerStrandsId.objects.filter(customer__riid=riid).values_list('strands_id', flat=True)
        if strands:
            strand_id = strands[0]
            strand_products = get_strands_products(strands_id=strand_id)
            return strand_products
        else:
            return []

    def post(self, request):
        """
        Get review data from frontend and save them in product review entity table.
        Here riid is set to unnecessary field in case responsys does not work properly.
        :param request:
        :return:
        """
        strands_products = []
        authenticated = True if request.user.is_authenticated() else False
        name = self.normalized_data(request.POST.get('name'), str)
        title = self.normalized_data(request.POST.get('title'), str)
        content = self.normalized_data(request.POST.get('content'), str)
        rating = self.normalized_data(request.POST.get('rating'), int)
        email = self.normalized_data(request.POST.get('email'), str)
        order_id = self.normalized_data(request.POST.get('order_id'), str)
        product_id = self.normalized_data(request.POST.get('product_id'), int)
        price_paid = self.normalized_data(request.POST.get('price_paid'), float, is_decimal=True)
        riid = self.normalized_data(request.POST.get('riid'), str)

        if riid:
            strands_products = self.get_strands(riid)
        # In case of responsys does not work properly sometimes, setting riid to None
        # try:
        #     riid = GmailAds().get_riid_from_email(email)[0][0]
        # except AttributeError:
        #     riid = None

        # Nickname as well as other fields except for riid are required in frontend.
        ProductReviewEntity.objects.create(
            nickname=name,
            review_title=title,
            review_content=content,
            rating=rating,
            order_id=order_id,
            product_id=product_id,
            price_paid=price_paid,
            email=email
        )
        response = TemplateResponse(request, 'review_submit.html', context={
            'authenticated': json.dumps(authenticated),
            'strands_products': json.dumps(strands_products)
        })
        return response

    def normalized_data(self, data, normal_fun, is_decimal=False):
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


class OrdersReviews(View):
    """
    Package data about the products in customers' orders and send that data to responsys.
    """
    def __init__(self):
        super(OrdersReviews, self).__init__()
        self.auth = ResponsysCredential.objects.all()[0]
        self.headers = {'Authorization': self.auth.token}
        self.campaign_name = 'co_review'
        self.campaign_endpoint = '%s/rest/api/v1.1/events/%s' % (self.auth.endpoint, self.campaign_name)
        self.list_name = 'CONTACT_LIST'
        self.product_attributes = []
        self.rg_orders = []
        self.max = 200

    def get_order_ids(self):
        # Order_ids that have status 'Delivered' for at least 5 days.
        current_time = datetime.now(timezone.utc).astimezone(pytz.timezone('US/Pacific'))
        target_date = current_time - timedelta(days=5)
        return map(int, [
            obj.order_id for obj in ShippingStatusTracking.objects.filter(
                event='Delivered', product_review_sent=False, updated_at__lte=target_date, order_id__startswith='2')
            ])[:200]

    def send_review_emails(self, preview_only=False, **kwargs):
        # target_date = current_time - timedelta(days=14)
        # early_date = current_time - timedelta(days=13)
        if kwargs.get('order_ids'):
            order_ids = kwargs.get('order_ids')
        else:
            order_ids = self.get_order_ids()

        orders = SalesFlatOrder.objects.filter(increment_id__in=order_ids, customer_email__isnull=False)
        product_ids = set()
        orders = orders.prefetch_related('salesflatorderitem_set')
        for order in orders:
            for item in order.salesflatorderitem_set.all():
                if item.product_id != 5631:
                    product_ids.add(item.product_id)
        rg_fields = ['name', 'image', 'price']
        p_attr = EavAttribute.objects.get_values(
            product_ids,
            field_names=rg_fields,
        )
        for order in orders:
            order_items = []
            for item in order.salesflatorderitem_set.all():
                if item.product_id == 5631:
                    continue
                data = p_attr.get(item.product_id, None)
                # Sometimes an ordered product may no longer exist in our db. If this is the case, skip the product.
                if not data:
                    continue
                save_pct = round((data.get('price', 0) - float(item.price)) / data.get('price'), 4) * 100
                save_dollars = int(data.get('price', 0.00) - float(item.price))
                if data.get('image', None) and data.get('image').startswith('URL/'):
                    image = data.get('image').replace('URL', 'http://cellularoutfitter.com/media/catalog/product')
                else:
                    image = 'http://cellularoutfitter.com/media/catalog/product%s' % (data.get('image',))
                item_info = {
                    'product_id': '%d' % item.product_id,
                    'special_price': '%.2f' % item.price,
                    'name': item.name,
                    'image': image,
                    'price': '%.2f' % data.get('price', 0.00),
                    'save_percent': '%s' % save_pct,
                    'save_dollars': '%s' % save_dollars,
                    'url_path': '%s/lifecycle/product-review/?product_id=%s&order_id=%s' % (
                        settings.ROOT_DOMAIN,
                        item.product_id,
                        order.increment_id,
                    ),
                }
                order_items.append(item_info)
            order_info = {
                'products': order_items,
                'customer_email': order.customer_email.encode('ascii', 'ignore').replace(' ', ''),
                'order_id': order.increment_id,
            }
            if settings.DEBUG:
                order_info['customer_email'] = settings.RESPONSYS_EMAIL[0]
            self.rg_orders.append(order_info)
        if preview_only:
            return self.rg_orders
        response = self.call_responsys(self.rg_orders)
        return response

    def make_request_payload(self, rg_orders):
        product_attributes = {'products': rg_orders[0]['products'][0].keys()}
        recipients = []
        orders = rg_orders
        # emails = [o.get('customer_email', '') for o in orders]
        email_to_riids = SendOrderConfirmationEmail().get_riid_from_email(
            [o.get('customer_email', '').encode('ascii', 'ignore').replace(' ', '') for o in orders]
        )
        if settings.DEBUG:
            email_to_riids = SendOrderConfirmationEmail().get_riid_from_email(settings.RESPONSYS_EMAIL)
        kept_orders = []
        for order in orders:
            opt_data = []
            opt_products_data = []
            opt_data.append({'name': 'PRODUCT_ATTRIBUTES',
                             'value': ';;-;;'.join(map(str, product_attributes['products']))})

            customer_email = order.get('customer_email', '')
            opt_data.append({'name': 'RIID', 'value': email_to_riids.get(customer_email)})
            for k, v in order.items():
                if k == 'products':
                    for product in v:
                        try:
                            opt_products = ';-;'.join([
                                normalize_data_type(product.get(p_k)).encode('utf-8')
                                for p_k in product_attributes['products']])
                        except UnicodeDecodeError, ex:
                            logger.exception(
                                'Failed to normalize product info for order : %s',
                                order.get('order_id'), extra=locals())
                            break
                        opt_products_data.append(opt_products)
                    opt_products_data = ';;-;;'.join(opt_products_data)
                    opt_data.append({'name': 'PRODUCTS', 'value': opt_products_data})
                else:
                    opt_data.append({'name': k.upper(), 'value': normalize_data_type(v)})
            if not settings.DEBUG:
                riid = email_to_riids.get(customer_email)
                try:
                    int(riid)
                except:
                    continue
            else:
                riid = email_to_riids.get(settings.RESPONSYS_EMAIL[0])
            recipient = {
                'recipient': {
                    "recipientId": riid,
                    'listName': {
                        'folderName': '!MageData',
                        'objectName': 'CONTACT_LIST'
                    },
                    'emailFormat': 'HTML_FORMAT',
                },
                'optionalData': opt_data
            }
            recipients.append(recipient)
            kept_orders.append(order)
        return {
            'customEvent': {
                "eventNumberDataMapping": '',
                "eventDateDataMapping": '',
                "eventStringDataMapping": ''
            },
            'recipientData': recipients
        }

    def call_responsys(self, orders):
        if settings.DEBUG:
            orders = [orders[0]]
        print ('total %s' % len(orders))
        request_payload = self.make_request_payload(orders)
        self.send_email(request_payload, orders)


    def send_email(self, request_payload, orders):
        response = requests.post(self.campaign_endpoint, json=request_payload, headers=self.headers)
        if response.status_code == 200:
            response_content = json.loads(response.content)
            if settings.DEBUG:
                print response_content
            self.add_sender_log(response_content, orders)
        else:
            logger.exception(
                'The request to post the data to CampaignEndpoint failed : %s',
                response.reason, extra=locals())
        return {
            'message': 'Finished calling responsys Api for order review'
        }

    def add_sender_log(self, response_content, orders):
        for index in xrange(len(response_content)):
            order = orders[index]
            order_id, customer_email = int(order.get('order_id')), '%s' % order.get('customer_email')
            OrderReviewSendLog.objects.update_or_create(
                order_id=order_id,
                customer_email=customer_email,
                defaults={'response': response_content[index].get('success')}
            )
            o = ShippingStatusTracking.objects.get(order_id=order.get('order_id'))
            o.product_review_sent = 1
            o.save()


class SendOopsEmail(object):
    """
    Send emails to customers if we detect a delay in shipping
    """

    def __init__(self):
        """
        Initialize the class and prepare responsys data such as folder name, campaign name, and credentials
        """
        super(SendOopsEmail, self).__init__()
        self.auth = ResponsysCredential.objects.all()[0]
        self.headers = {'Authorization': self.auth.token}
        self.folder_name = '!MageData'
        self.campaign_name = 'CO_OopsLateShip_Trans'
        self.list_name = 'CONTACT_LIST'
        self.rg_orders = []

    def send_email(self):
        """
        Send emails to customers.
        Call get_delayed_orders to prepare delayed orders
        Call send_email_campaign ito send emails
        :return: response from Responsys
        """
        self.get_delayed_orders()
        if len(self.rg_orders) == 0:
            return None
        recipients = self.make_request_payload(self.rg_orders)
        r_api = ResponsysApi()
        response = r_api.send_email_campaign(self.campaign_name, recipients)
        if response.get('rg_response'):
            r_content = response.get('rg_response')
            self.process_send_result(r_content)
            return r_content
        return response

    def get_delayed_orders(self):
        """
        Get delayed orders.
        Use OrderConfirmationEmailsLog as a base and then filtered out orders that were already shipped
        Store order id and customer email in self.rg_orders
        :return: Nothing
        """
        current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        one_day = current_time - timedelta(hours=24)
        two_day = current_time - timedelta(hours=48)
        initial_orders = OrderConfirmationEmailsLog.objects.filter(
            created_dt__gte=two_day, created_dt__lt=one_day).exclude(
            order_id__in=ShippingStatusTracking.get_order_ids()).values_list('order_id', flat=True)
        order_ids = [order_id for order_id in initial_orders]
        rg_orders = SalesFlatOrder.objects.filter(
            increment_id__in=order_ids, status='processing').values_list('increment_id', 'customer_email')
        self.rg_orders = CustomerStrandsId.objects.append_strands_products(
            [{'order_id': order_id, 'email': email} for order_id, email in rg_orders])

    def make_request_payload(self, rg_orders):
        """
        Normalize request data
        Each recipient must have a riid and order id.
        If a customer has strands id, we also append strands products in optional data.
        :param rg_orders: self.rg_orders, type: list
        :return:
        """
        recipients = []
        mp_email_riids = ResponsysApi().get_riid_from_email([v for k, v in rg_orders if k == 'email'])
        if settings.DEBUG:
            mp_email_riids.update(ResponsysApi().get_riid_from_email(settings.RESPONSYS_EMAIL))
            rg_orders = rg_orders[:2]
        for mp_order in rg_orders:
            opt_data = []
            if mp_order.get('includes_strands', '') == 'yes':
                strands_attr = mp_order['strands_products'][0].keys()
                opt_data.append({'name': 'strands_product_attributes', 'value': ';;-;;'.join(map(str, strands_attr))})
                opt_products = [';-;'.join(
                    map(str, [normalize_data_type(product.get(p_k)) for p_k in strands_attr]
                        )) for product in mp_order['strands_products']]
                opt_data.append({'name': 'strands_products', 'value': ';;-;;'.join(opt_products)})
            opt_data.append({'name': 'ORDER_ID', 'value': mp_order.get('order_id')})
            if not settings.DEBUG:
                riid = mp_email_riids.get(mp_order.get('email'))
            else:
                riid = mp_email_riids.get(settings.RESPONSYS_EMAIL[0])
            recipient = {
                'recipient': {
                    'recipientId': riid,
                    'listName': {
                        'folderName': '!MageData',
                        'objectName': self.list_name
                    },
                    'emailFormat': 'HTML_FORMAT',
                },
                'optionalData': opt_data
            }
            recipients.append(recipient)
        return recipients

    def process_send_result(self, r_content):
        """
        Update OopsEmailSendLog with the results of each attempted call to Responsys.
        :type r_content: dict
        :param r_content: Response from Responsys call
        :return: None
        """
        for n, r in enumerate(r_content):
            order_id = self.rg_orders[n].get('order_id')
            try:
                OopsEmailSendLog.objects.create(
                    order_id=order_id,
                    response=r['success'],
                )
            except Exception as e:
                logger.exception(msg='There is an error while saving oops email data %s for order %s' % (e, order_id))
                continue


class ProductReviewsReport(View):
    def get(self, request, **kwargs):
        """
        Exports the product reviews table entries for the date passed in the request
        """
        if 'HTTP_AUTHORIZATION' in request.META:
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2:
                if auth[0].lower() == 'basic':
                    uname, passwd = base64.b64decode(auth[1]).split(':')
                    user = authenticate(username=uname, password=passwd)
                    if user is not None and user.is_active:
                        request.user = user
                        date_from = '%s-%s-%s' % (kwargs.get('year'), kwargs.get('month'), kwargs.get('day'))
                        data = ProductReviewEntity.objects.filter(created_dt__gte=date_from).values()
                        data_holder = []
                        for r in data:
                            data_holder.append({k.upper():v for k, v in r.iteritems()})
                        for r in data_holder:
                            r['REVIEW_DATE'] = r['CREATED_DT'].strftime('%Y-%m-%d')
                            r['REVIEW_DT'] = r['CREATED_DT'].strftime('%Y-%m-%d %H:%M:%S')
                            r['PRICE_PAID'] = float(r['PRICE_PAID'])
                            r['QTY'] = 1
                            r['RIID'] = 1

                        return JsonResponse(data_holder, safe=False)
            response = HttpResponse()
            response.status_code = 401
            response['content'] = 'Credentials not authorized. Username: %s, Pass: %s' % (uname, passwd)
            response['WWW-Authenticate'] = 'Basic Auth Protected'

            return response
