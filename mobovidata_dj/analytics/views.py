import base64
import collections
import csv
import datetime
import hashlib
import json
import logging
import math
import os
import pytz
import re
import requests
import StringIO
import urllib
import zipfile

from collections import defaultdict
from decimal import Decimal
from facebookads.api import FacebookAdsApi
from facebookads.adobjects.lead import Lead
from requests.auth import HTTPBasicAuth

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import IntegrityError
from django.db.models import F, Q
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.timezone import utc
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .forms import TrackingForm
from .models import (Customer, CustomerCart, CustomerDevice, CustomerPageView,
                     CustomerLifecycleTracking, CustomerOrder, CustomerSession,
                     CustomerStrandsId, EmailSignUpTrack, FacebookAdEmails,
                     GmailAdEmails, MobovidaCustomerEmails)
from .utils import SlickText
from mobovidata_dj.facebook.carousel_ads import generate_url_prefix
from mobovidata_dj.helpscout.helpcout_api import HelpscoutConnect
from mobovidata_dj.lifecycle.models import SenderLog
from mobovidata_dj.ltv.models import CustomerId, CustomerIdOrderId
from mobovidata_dj.responsys.connect import ResponsysFtpConnect
from mobovidata_dj.responsys.models import (ResponsysCredential, RiidEmail,
                                            OptedOutEmails)
from modjento.models import (EavAttribute, ErpInventoryPurchaseOrder,
                             SalesFlatOrder, SalesFlatOrderAddress,
                             SalesFlatOrderPayment, SalesFlatShipmentTrack,
                             Salesrule)


logger = logging.getLogger(__name__)


@login_required()
def recent_pageviews(request):
    pageviews = CustomerPageView.objects.filter(
        modified_dt__gte=datetime.datetime.now() - datetime.timedelta(minutes=60)
    ).order_by('-id')
    count = pageviews.count()

    return render(request, 'recent_pageviews.html',
                  {'pageviews': pageviews[:50], 'count': count})


@csrf_exempt
def get_customer_info(request):
    """
    Takes customer's RIID and returns customer order data
    @param request: (obj) request object
    @return: (obj) JSON containing customer's order data
    """
    param = request.GET.get('param')
    num_orders = -1
    result = 'error'

    try:
        validate_email(param)
        num_orders = CustomerId.objects.get(email=param).num_orders
        result = 'email'
    except ValidationError:
        pass # it's not an email
    except ObjectDoesNotExist:
        num_orders = 0

    try:
        riid = int(param)
        email = RiidEmail.objects.get(riid=riid)
        num_orders = CustomerId.objects.get(email=email).num_orders
        result = 'riid'
    except ValueError:
        pass  # it's not an int.
    except ObjectDoesNotExist:
        num_orders = 0

    if num_orders == -1:
        logger.error('Data bad format. No email or riid was received.',
                     extra=locals())

    mp_order_data = json.dumps({'num_orders': num_orders,
                                result: param})
    return HttpResponse(mp_order_data, content_type='application/json')


class AjaxableResponseMixin(object):
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    http_method_names = ['post']

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(AjaxableResponseMixin, self).dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        response = super(AjaxableResponseMixin, self).form_invalid(form)
        return response

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super(AjaxableResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            data = {
                'result': 'success'
            }
            return JsonResponse(data)
        return response


class GmailAds(View):
    """
    When a user registers for our gmail ads, Mobovidata will fire a Custom Event
    Trigger via Responsys API.
    """
    def __init__(self):
        """
        Constructor of GmailAds
        :return:
        """
        super(GmailAds, self).__init__()
        self.event_name = 'Gmail_Ad_Email_Submit'
        self.auth = ResponsysCredential.objects.all()[0]
        self.headers = {'Authorization': self.auth.token}
        self.eventEndpoint = ('%s/rest/api/v1.1/events/%s' %
                              (self.auth.endpoint, self.event_name))

    def get(self, request, *args, **kwargs):
        email = request.GET.get('email', '')
        redirect_url = request.GET.get('redirect', False)
        if not email:
            logger.warning('No email address found')
            return JsonResponse({
                'message': 'No email address found'
            }, safe=False)
        riid = self.get_riid_from_email(email)[0][0]
        data = {
            'customEvent': {
                'eventNumberDataMapping': '',
                'eventDateDataMapping': '',
                'eventStringDataMapping': ''
            },
            'recipientData': [{
                'recipient': {
                    'recipientId': riid,
                    'listName': {
                        'folderName': '!MageData',
                        'objectName': 'CONTACT_LIST'
                    },
                    'emailFormat': 'HTML_FORMAT'
                }
            }]
        }
        r = requests.post(self.eventEndpoint, json=data, headers=self.headers)
        if r.status_code == 200:
            r_content = json.loads(r.content)
            GmailAdEmails.objects.get_or_create(email=email,
                                                riid=r_content[0]['recipientId']
                                                )
            if redirect_url:
                base_url = 'http://www.cellularoutfitter.com'
                redirect_url = '%s%s&dz_riid=%s' % (
                    base_url,
                    urllib.unquote(redirect_url),
                    r_content[0]['recipientId']
                )
                return redirect(redirect_url)
            else:
                return JsonResponse({'result': 'ok'})
            # return JsonResponse(r_content, safe=False)
        else:
            logger.error('Responsys api request failed with error code %s. '
                         'Content: %s' % (r.status_code, r.content))
            if settings.DEBUG:
                return JsonResponse({
                    'message': 'Request failed.',
                    'Error code': '%s' % r.status_code,
                    'Reason': '%s' % r.content,
                    'data': '%s' % data,
                    'Email': '%s' % email,
                    'RIID': '%s' % riid
                })
            else:
                return JsonResponse({'Error': 'Something went wrong'})

    def get_riid_from_email(self, email, source="Gmail"):
        """
        Returns first RIID found for a given email address.
        @param email: list()
        @param source: str()
        @return: str(riid)
        """
        r = self._call_responsys_members_ep(
            ['email_address_', 'signup_source'],
            [email, source],
            update_on_match=False
        )
        if r.status_code == 200:
            records = json.loads(r.content)['recordData']['records'][0][0]
            if 'MERGEFAILED' in records:
                # Indicates that the subscriber already exists in Responsys,
                # so re-call
                r = self._call_responsys_members_ep(
                    ['email_address_'],
                    [email],
                    update_on_match=True
                )
                if r.status_code == 200:
                    return json.loads(r.content)['recordData']['records']
            else:
                return json.loads(r.content)['recordData']['records']
        else:
            logger.error('Responsys api request failed with error code %s. '
                         'Content: %s' % (r.status_code, r.content))
            if settings.DEBUG:
                return JsonResponse({
                    'message': 'Request failed.',
                    'Error code': '%s' % r.status_code,
                    'Reason': '%s' % r.content,
                    'Email': '%s' % email
                })
            else:
                return JsonResponse({'Error': 'Something went wrong'})

    def _call_responsys_members_ep(self, fields, values, update_on_match=True):
        """
        Calls responsys members endpoint with the specified fields and values.
        Does not process result of API request.
        @param fields: list()
        @param values: list()
        @param fields: list
        @return: Result of API request object
        """
        if update_on_match:
            update_on_match = 'UPDATE_ALL'
        else:
            update_on_match = 'NO_UPDATE'
        auth = ResponsysCredential.objects.all()[0]
        headers = {'Authorization': auth.token}
        list_name = 'CONTACT_LIST'
        merge_endpoint = '%s/rest/api/v1.1/lists/%s/members' % (auth.endpoint,
                                                                list_name)
        data = {
            "recordData": {
                "fieldNames": fields,
                "records": [
                    values,
                ],
            },
            "mergeRule": {
                "htmlValue": "H",
                "optinValue": "I",
                "textValue": "T",
                "insertOnNoMatch": True,
                "updateOnMatch": update_on_match,
                "matchOperator": "NONE",
                "matchColumnName1": "email_address_",
                "optoutValue": "O",
                "defaultPermissionStatus": "OPTIN"
            }
        }
        return requests.post(merge_endpoint, json=data, headers=headers)


def tracking(request):
    """
    GET request has to have parameters required to handle tracking
    All logic below determines which user to associate with the request and
    which data to store and in which table.
    @param request: HTTP request object
    """

    # TODO: Change form.cleaned_data to a var and ref var in this function
    form = TrackingForm(request.GET)
    if form.is_valid():
        # Get customer information
        try:
            customer = Customer.objects.get(uuid=form.cleaned_data['mvid'])
        except Customer.DoesNotExist:
            # This is needed for cases where the customer was assigned a UUID
            # in a previous db incarnation
            customer = (Customer.objects
                        .add_customer(uuid=form.cleaned_data['mvid']))
        except ValueError as e:
            http_response = HttpResponse(e)
            http_response.status_code = 505
            return http_response
        if form.cleaned_data.get('mvrid'):
            # Get uuid with matching RIID (even if its this uuid)
            customer = (Customer.objects
                        .update_customer(customer.uuid,
                                         riid=form.cleaned_data['mvrid'])['customer'])

        # Get session information
        try:
            session = (CustomerSession.objects
                       .get(session_id=form.cleaned_data['mvsid']))
        except CustomerSession.DoesNotExist:
            device_headers = ''
            if form.cleaned_data['mvhdrs']:
                device_headers = form.cleaned_data['mvhdrs']
            session = CustomerSession(customer=customer,
                                      session_id=form.cleaned_data['mvsid'],
                                      device_headers=device_headers)
            session.save()

        # Get pageview information
        prod_id = ''
        params = ''
        if form.cleaned_data['mvpid']:
            # Product id
            prod_id = form.cleaned_data['mvpid']
        if form.cleaned_data['mvprm']:
            # URL parameters
            params = request.GET.get('mvprm')
            params = params.replace('-%amp%-', '&')
            params = params.replace('-%eq%-', '=')
        if form.cleaned_data['mvsl']:
            # url slug
            new_pageview = CustomerPageView(session=session,
                                            url_path=form.cleaned_data['mvsl'],
                                            product_fullid=prod_id,
                                            url_parameters=params)
            new_pageview.save()
            if form.cleaned_data['mvt']:
                page_type = form.cleaned_data['mvt']
                if len(prod_id) > 0:
                    (CustomerLifecycleTracking.objects
                     .set_lifecycle_stage_to_product(new_pageview.id,
                                                     customer=customer))
                elif page_type == 'search' and form.cleaned_data['mvst']:
                    (CustomerLifecycleTracking.objects
                        .set_lifecycle_stage_to_search(new_pageview.id,
                                                       form.cleaned_data['mvst'],
                                                       customer=customer))
                elif page_type in ['homepage', 'category']:
                    (CustomerLifecycleTracking.objects
                        .set_lifecycle_stage_to_browse(new_pageview.id,
                                                       customer=customer))

        if form.cleaned_data['mvapi'] == 'cr':
            # This is a cart pageview
            if form.cleaned_data['mvcid']:
                (CustomerCart.objects
                 .process_cart(cart_id=form.cleaned_data['mvcid'],
                               session=session))

        elif form.cleaned_data['mvapi'] == 'or':
            # This is an order confirmation page
            if form.cleaned_data['mvoid']:
                (CustomerOrder.objects
                 .process_order(order_id=form.cleaned_data['mvoid'],
                                session=session))

        if form.cleaned_data.get('strandsid', False):
            CustomerStrandsId.objects.update_or_create(
                customer=customer,
                defaults={'strands_id': form.cleaned_data['strandsid']})

        # Get and store user's device
        if (form.cleaned_data.get('mvdv', False) and
                form.cleaned_data.get('mvrid', False)):
            mvrid = form.cleaned_data.get('mvrid')
            if len(mvrid) <= 15:
                try:
                    mvrid = int(mvrid)
                except ValueError:
                    pass
                else:
                    CustomerDevice.objects.update_or_create(
                        riid='%s' % mvrid,
                        defaults={'device': form.cleaned_data.get('mvdv'),
                                  'uploaded': False}
                    )

        session.num_page_views += 1
        # session.customer = customer
        session.save()
        customer.save()
        return HttpResponse("success")
    return HttpResponse("invalid get parameters: %s" % json.dumps(form.errors))


@csrf_exempt
def eval_user(request):
    """
    Receives RIID, UUID from client browser, and runs functions to check if
    RIID already exists. If so, returns the RIID's corresponding UUID to the
    browser for cookie storage and re-associates all existing sessions IDs for
    the original UUID with the UUID matching the RIID.

    If request.POST.get('mvid') is blank, returns a UUID.
    """
    if request.is_ajax():
        try:
            uuid = request.POST.get('mvid')
            riid = request.POST.get('riid')
            eval_riid = Customer.objects.update_customer(uuid, riid=riid)
            return JsonResponse({'eval_user_result': 'success',
                                 'uuid': str(eval_riid['customer'].uuid)})
        except IntegrityError:
            return JsonResponse({'eval_user_result': 'fail',
                                 'error': 'ADD ERROR DETAILS HERE'})
    return JsonResponse({"eval_user_result": "ajax only allowed"})


@csrf_exempt
def get_riid(request):
    """
    Gets email address from client browser and fetches RIID from responsys
    @param request: request object
    @return: JSON containing result status and RIID if successful
    """
    from mobovidata_dj.responsys.utils import ResponsysApi
    if request.is_ajax():
        try:
            response = ResponsysApi().get_riids(request.POST.get('email'))
            if response.status_code == 200:
                content = json.loads(response.content)
                riid = content['recordData']['records'][0][0]
                return JsonResponse({'result': 'success', 'riid': riid})
        except IntegrityError:
            return JsonResponse({'result': 'FAIL'})
    return JsonResponse({'result': 'ajax only allowed'})


@csrf_exempt
def register_user(request):
    """
    Assigns UUID to new visitor to the site
    """
    if request.is_ajax():
        try:
            new_user = (Customer.objects
                        .create_customer(riid=request.POST.get('riid')))
            return JsonResponse({'register_user_result': 'success',
                                 'uuid': new_user.uuid})
        except IntegrityError:
            riid = request.POST.get('riid')
            cust = Customer.objects.get_customer_from_riid(riid=riid)
            return JsonResponse({'register_user_result': 'success',
                                 'uuid': cust.uuid})
    return JsonResponse({"register_user_result": "ajax only allowed"})


@csrf_exempt
def check_uuid(request):
    """
    Recieves a UUID (and optionally RIID), checks for its existence in db.
    Called whenever new sessions start for visitors who already have a UUID.
        If RIID in db, return uuid corresponding to that RIID
        If UUID in db, but RIID is not in db, add RIID to that uuid, return that
        uuid
        If UUID in db, but no RIID was sent, return that UUID
        If UUID not in db, create new user (optionally with RIID assigned) and
        return new UUID
    """
    if request.is_ajax():

        uuid = request.POST.get('mvid')
        riid = request.POST.get('riid')
        try:
            # Will throw an error if uuid does not exist in db
            eval_riid = Customer.objects.update_customer(uuid, riid=riid)
            return JsonResponse({'check_uuid_result': 'success',
                                 'uuid': eval_riid['customer'].uuid})
        except Customer.DoesNotExist:
            # Customer does not exist in db, create new cust and return approp
            # uuid
            if riid:
                customer = Customer.objects.create_customer(riid=riid)
                return JsonResponse({'check_uuid_result': 'success',
                                     'uuid': customer.uuid})
    return JsonResponse({"check_uuid_result": "ajax only allowed"})


@method_decorator(csrf_exempt, name='dispatch')
class LeadGenEmails(View):
    """
    Get email addresses from FB lead gen and store data in Django. Merge email
    addresses into Responsys.
    Requires that public-facing URL is registered w/ Facebook app.
    To register a URL:
        from facebook import FacebookConnetct
        f = FacebookConnect()
        f.register_webhook_endpoint(YOUR_PUBLIC_ENDPOINT/apis/lead-gens/)
    After registering your URL, you can test the endpoint with:
    https://developers.facebook.com/tools/lead-ads-testing
    """
    def __init__(self):
        super(LeadGenEmails, self).__init__()
        self.step = 200
        self.auth = ResponsysCredential.objects.all()[0]
        self.list_name = 'CONTACT_LIST'
        self.folder_name = '!MageData'
        self.event_name = 'Gmail_Ad_Email_Submit'
        self.headers = {'Authorization': self.auth.token}
        self.list_endpoint = ('%s/rest/api/v1.1/folders/%s/suppData/%s/members'
                             % (self.auth.endpoint, self.folder_name,
                                self.list_name))
        self.event_endpoint = '%s/rest/api/v1.1/events/%s' % (
            self.auth.endpoint, self.event_name)

    def get(self, request):
        challenge = request.GET.get('hub.challenge', '')
        verify_token = request.GET.get('hub.verify_token')
        print request.GET
        if verify_token == 'abc123':
            return HttpResponse(challenge)

    def post(self, request):
        body = json.loads(request.body)
        cache.set('fb_ping', body)
        data = cache.get('fb_ping')
        email_list = []
        FacebookAdsApi.init(
            settings.FACEBOOK_API['app_id'],
            settings.FACEBOOK_API['app_secret'],
            settings.FACEBOOK_API['user_token']
        )
        ga = GmailAds()
        for x in data['entry']:
            for change in x['changes']:
                leadgen_id = change['value']['leadgen_id']
                lead_info = Lead(leadgen_id)
                lead_data = lead_info.remote_read()
                email_field = reduce(lambda x, y: x if x['name'] == 'email' else y, lead_data['field_data'])
                email = email_field['values'][0] if email_field['values'] else ''
                # get_riid_from_email function will merge the email into
                # Responsys Profile list.
                riid_info = ga.get_riid_from_email(email, source="Facebook")
                if type(riid_info) is list:
                    riid = riid_info[0][0] or ''
                    email_list.append([riid, email])
                    r = self.fire_custom_event(riid)
                    if r.status_code == 200:
                        record = FacebookAdEmails.objects.create(email=email,
                                                                 riid=riid)
                        record.save()
                    else:
                        logger.error('Failed to request Responsys Api custom '
                                     'event: %s' % r.reason, extra=locals())
                        return JsonResponse({
                            'message': 'Failed to request Responsys Api custom '
                                       'event'
                        })
                else:
                    logger.error('Failed to merge the email address: %s' %
                                 riid_info)
        return JsonResponse({
            'success': True
        })

    def fire_custom_event(self, riid):
        """
        Given riid, fire the responsys 'Gmail_Ad_Email_Submit' event to collect
        data
        @param riid:
        @return:
        """
        data = {
            'customEvent': {
                'eventNumberDataMapping': '',
                'eventDateDataMapping': '',
                'eventStringDataMapping': ''
            },
            'recipientData': [{
                'recipient': {
                    'recipientId': riid,
                    'listName': {
                        'folderName': '!MageData',
                        'objectName': 'CONTACT_LIST'
                    },
                    'emailFormat': 'HTML_FORMAT'
                }
            }]
        }
        r = requests.post(self.event_endpoint, json=data, headers=self.headers)
        return r


@csrf_exempt
def email_optin(request):
    from mobovidata_dj.responsys.utils import ResponsysApi
    r = ResponsysApi()
    # source = request.GET.get('source', '')
    email = request.POST.get('email', False)
    r.get_riid_from_email([email])
    print email
    ep = 'https://api.zaius.com/v2/events'
    headers={'Zaius-Tracker-Id': '5YVK2LhYpKWTjZ4G035Dlw'}
    params = {'type': 'newsletter',
              'data': {
                 'action': 'signup',
                 'email': email}
              }
    r = requests.post(ep, json=params, headers=headers)
    return JsonResponse('Success', safe=False)

@csrf_exempt
def mobovida_email_signup(request):
    if request.is_ajax():
        m = MobovidaEmailSignup()
        source = request.POST.get('source', '')
        email = request.POST.get('email', False)
        print email, source
        return JsonResponse(json.loads(m.subscribe_email(email.lower(), source))
                            , safe=False)
    return JsonResponse({"mobovida_email_signup_result": "ajax only allowed"})


class MobovidaEmailSignup(View):
    """
    Accepts email address in get request and passes it to mailchimp list.
    Used on mobovida.com so we can avoid Mailchimp's double opt-in process.
    """
    def __init__(self):
        """
        Constructor of MobovidaEmailSignup
        :return:
        """
        super(MobovidaEmailSignup, self).__init__()
        self.api_key = settings.MAILCHIMP_API_KEY

    def subscribe_email(self, email, source):
        response = requests.post(
            '%s/lists/c46817ff36/members' % settings.MAILCHIMP_ENDPOINT,
            auth=HTTPBasicAuth('anystring', self.api_key),
            json={
                'email_address': email,
                'status': 'subscribed',
                'merge_fields': {
                    'SOURCE': source
                }
            }
        )
        if response.status_code == 200:
            MobovidaCustomerEmails.objects.get_or_create(
                email=email,
                email_md5=hashlib.md5(email).hexdigest()
            )
        elif response.status_code == 400:
            if json.loads(response.content)['title'] == 'Member Exists':
                MobovidaCustomerEmails.objects.get_or_create(
                    email=email,
                    email_md5=hashlib.md5(email).hexdigest()
                )
        return response.content


class TrackingEmailSignUp(LoginRequiredMixin, TemplateResponseMixin, View):
    """
    Get count of new signup and unsubscribe and store into EmailSignUpTrack.
    """
    def __init__(self):
        super(TrackingEmailSignUp, self).__init__()
        self.dir = settings.RESPONSYS_EMAIL_PATH['dir']
        self.in_mode = settings.RESPONSYS_EMAIL_PATH['in']
        self.out_mode = settings.RESPONSYS_EMAIL_PATH['out']
        self.field = 'EVENT_CAPTURED_DT'
        self.local_path = settings.RESPONSYS_EMAIL_PATH['local']

    def get(self, request):
        track_list = []
        email_sign_up = EmailSignUpTrack.objects.all()
        for entry in email_sign_up:
            track_list.append({
                'day': entry.day,
                'new_email': entry.new_email,
                'unsubscribes': entry.unsubscribe_email,
                'net_change': entry.new_email - entry.unsubscribe_email
            })
        return render(request, 'email_signup_track.html',
                      {'email_sign_up': json.dumps(track_list)})

    def download_files(self):
        """
        Download files matching specific pattern
        """
        file_folder = self.dir.split('/')[-2]
        r = ResponsysFtpConnect()
        # Get list of filepaths for files matching *_mode on Responsys FTP
        in_paths = r.get_file_path(self.in_mode, remote_path=file_folder)
        out_paths = r.get_file_path(self.out_mode, remote_path=file_folder)
        # Remove files that have already been processed
        processed_files = json.loads(cache.get('responsys:processed_ced_files',
                                               '[]'))
        in_paths = [f for f in in_paths if f.split('/')[-1] not in processed_files]
        out_paths = [f for f in out_paths if f.split('/')[-1] not in processed_files]
        # Download unprocessed files
        for p in in_paths:
            r.download_file(p, self.get_local_path(p))
        for p in out_paths:
            r.download_file(p, self.get_local_path(p))
        # Get local paths to downloaded files
        in_paths = [self.get_local_path(p) for p in in_paths]
        out_paths = [self.get_local_path(p) for p in out_paths]
        # Parse the opt in/out files.
        in_count = self.read_files(in_paths)
        out_count = self.read_files(out_paths)
        for day in in_count:
            if not EmailSignUpTrack.objects.filter(day=day).exists():
                t = EmailSignUpTrack.objects.create(
                    day=day,
                    new_email=in_count.get(day),
                    unsubscribe_email=out_count.get(day),
                    analysis_date=datetime.datetime.utcnow().replace(tzinfo=utc)
                )
                t.save()
            else:
                entry = EmailSignUpTrack.objects.get(day=day)
                entry.__dict__.update(
                    new_email=entry.new_email + in_count.get(day),
                    unsubscribe_email=entry.unsubscribe_email + out_count.get(day),
                    analysis_date=datetime.datetime.utcnow().replace(tzinfo=utc)
                )
                entry.save()
        # Store filenames from in_paths and out_paths in cache so we don't
        # extract these files in the future.
        self.log_processed_files(in_paths + out_paths)
        r.close_connection()

    def log_processed_files(self, local_file_paths):
        """
        Stores the name of processed files to cache so we don't re-read these
        files in the future.
        :param local_file_paths: List of local file paths that have already been
        processed.
        :type local_file_paths: list
        :return: None
        """
        processed_files = json.loads(cache.get('responsys:processed_ced_files',
                                               '[]'))
        processed_files += [f.split('/')[-1] for f in local_file_paths]
        cache.set('responsys:processed_ced_files', json.dumps(processed_files),
                  timeout=None)

    def get_local_path(self, path):
        if not os.path.exists(self.local_path):
            os.makedirs(self.local_path)
            # create dir with full permission
            os.chmod(self.local_path, 0777)
        local_path = os.path.join(self.local_path, path.split('/')[-1])
        return local_path

    def read_files(self, local_paths):
        """
        Accepts a list of paths to zip files, reads them
        and counts occurences of dates in those files.
        :type local_paths: list
        """
        mp_date = defaultdict(int)
        for l in local_paths:
            with zipfile.ZipFile(self.get_local_path(l), 'r') as archive:
                for f in archive.namelist():
                    data = StringIO.StringIO(archive.read(f))
                    reader = csv.DictReader(data)
                    for row in reader:
                        mp_date[
                            datetime.datetime.strptime(row[self.field], '%d-%b-%Y %H:%M:%S').strftime('%Y-%m-%d')
                        ] += 1
        return mp_date


@csrf_exempt
def check_md5_emails(request):
    email_list = request.body
    if not email_list:
        return JsonResponse({'message': 'No hashed email found'}, safe=False)
    email_list = json.loads(email_list).get('q')
    emails = OptedOutEmails.objects.filter(md5__in=email_list)
    blacklist_map = {0: 'true', 1: 'false'}
    email_statuses = {e.md5: blacklist_map.get(e.subscription_status) for e in emails}
    response_list = []
    for m in email_list:
        if email_statuses.get(m, False):
            response_list.append({
                'md5': m,
                'blacklisted': email_statuses.get(m)
            })
        else:
            response_list.append({
                'md5': m,
                'blacklisted': 'false',
            })
    return JsonResponse(response_list, safe=False)


class CallResponsys:
    """
    Connect Responsys Api
    """
    def __init__(self):
        self.auth = ResponsysCredential.objects.all()[0]
        self.headers = {'Authorization': self.auth.token}

    def merge_or_update_plist(self, list_name, data):
        if not list_name:
            logger.warning('No list name found.')
            return
        list_endpoint = ('%s/rest/api/v1.1/lists/%s/members' %
                         (self.auth.endpoint, list_name))
        response = requests.post(list_endpoint, json=data, headers=self.headers)
        return {
            'response': response,
        }

    def retrieve_from_plist_by_riid(self, list_name, riid, params):
        if not riid or not params:
            logger.warning('Please check riid or params.')
            return
        list_endpoint = '%s/rest/api/v1.1/lists/%s/members' % (self.auth.endpoint
                                                               , list_name)
        retrieve_endpoint = '%s/%s' % (list_endpoint, riid)
        response = requests.get(retrieve_endpoint, params=params,
                                headers=self.headers)
        return {
            'response': response,
        }

    def get_riid_from_email(self, email, list_name='CONTACT_LIST', ):
        """
        Returns a list of RIIDs associated with a given email address
        :type list_name: str
        :type email: str
        :return: List of riids associated with the email address
        """
        params = {
            'qa': 'e',
            'id': email,
            'fs': 'riid_'
        }
        list_endpoint = ('%s/rest/api/v1.1/lists/%s/members' %
                         (self.auth.endpoint, list_name))
        return requests.get(list_endpoint, params=params, headers=self.headers)


@method_decorator(csrf_exempt, name='dispatch')
class TextSignUp(View):
    def __init__(self):
        super(TextSignUp, self).__init__()

    def get(self, request):
        """
        Used to subscribe customers to SlickText and redirecs them to the passed
        redirect_url.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        number = request.GET.get('number', False)
        # Have to standardize the number because it could contain all sorts of
        # funky chars
        number = re.sub("[^0-9]", "", urllib.unquote(number))
        number = int(number[:11])
        riid = request.GET.get('dz_riid', False)
        redirect_url = request.GET.get('redirect_url',
                                       'http://www.cellularoutfitter.com')
        textword = request.GET.get('textword', 31996)
        resp = SlickText().register_sms(number, textword)
        redirect_url = '%s?dz_riid=%s&number=%s&textword=%s' % (
            urllib.unquote(redirect_url),
            riid,
            number,
            textword
        )
        return redirect(redirect_url)

    def post(self, request):
        riid = request.POST.get('riid')
        number = request.POST.get('number')
        textword = request.POST.get('textword', 31996)
        data = {
                'recordData': {
                    'fieldNames': ['RIID_', 'PHONE'],
                    'records':
                        [['%s' % riid, number]],
                },
                'mergeRule': {
                    'htmlValue': 'H',
                    'optinValue': 'I',
                    'textValue': 'T',
                    'insertOnNoMatch': False,
                    'updateOnMatch': True,
                    'matchOperator': 'NONE',
                    'matchColumnName1': 'RIID_',
                    'optoutValue': 'O',
                    'defaultPermissionStatus': 'OPTIN'
                }
            }
        res = CallResponsys().merge_or_update_plist('CONTACT_LIST', data)
        resp = SlickText().register_sms(number, textword)
        return JsonResponse({
            'responsys_result': res['response'].status_code,
            'responsys_content': res['response'].content,
            'slicktext_result': resp.status_code,
            'slicktext_content': resp.content
        })


class CustomerDashboard(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'customer_dash.html'
    login_url = '/accounts/login'

    def get(self, request):
        email = request.GET.get('email')
        context = self.pull_customer_info(email)
        return self.render_to_response(context)

    # def post(self, request, *args, **kwargs):
    #     email = request.POST.get('email')
    #     context = self.pull_customer_info(email)
    #     return self.render_to_response(context)

    def pull_customer_info(self, email):
        orders, sessions_info, pageviews, order_summary, lifecycle_list = [], [], [], {}, []
        if email:
            email = '%s' % email
            # orders
            customer_order = (SalesFlatOrder.objects
                              .filter(customer_email=email)
                              .values_list('increment_id',
                                           'status',
                                           'grand_total',
                                           'created_at'))
            for iid, status, total, created_at in customer_order:
                mp_order = {
                    'increment_id': iid,
                    'created_at': created_at.strftime('%b %d, %Y %I:%M%p'),
                    'total': '%.2f' % total,
                    'status': status
                }
                orders.append(mp_order)

            response = CallResponsys().get_riid_from_email(email)
            rcontent = json.loads(response.content)['recordData']['records']
            # There are often multiple RIIDs associated with a single email
            # address, so we want to get all of them.
            riids = [int(r[0]) for r in rcontent]

            # sessions
            sessions = (CustomerSession.objects.filter(customer__riid__in=riids)
                        .all())
            sessions_ids = []
            for session in sessions:
                sessions_ids.append(session.session_id)
                session_info = {
                    'session_id': session.session_id,
                    'created_at': session.created_dt.strftime('%b %d, %Y %I:%M%p'),
                    'device_headers': session.device_headers,
                    'num_page_views': session.num_page_views
                }
                sessions_info.append(session_info)

            # pageviews
            page_views = (CustomerPageView.objects
                          .filter(session__in=sessions_ids)
                          .order_by('created_date').all())
            for page_view in page_views:
                page_view_info = {
                    'created_at': page_view.created_dt.strftime('%b %d, %Y %I:%M%p'),
                    'url_path': page_view.url_path,
                    'product_fullid': '%s' % page_view.product_fullid,
                    'url_parameters': page_view.url_parameters,
                    'session': '%s' % page_view.session.session_id
                }
                pageviews.append(page_view_info)

            # Customer Order Summary
            customer_order_summary = (CustomerId.objects.filter(email=email)
                                      .all())
            if not customer_order_summary:
                order_summary = {}
            else:
                customer_order_summary = customer_order_summary[0]
                customer_order_total = CustomerIdOrderId.objects.filter(
                    customer_id=customer_order_summary.id
                ).order_by('-created_at').values_list('order_grand_total',
                                                      'created_at')
                customer_lifetime_value = sum([total for total, created_at in customer_order_total])
                last_order_at = customer_order_total[0][1]
                num_orders = len(customer_order_total)
                order_summary = {
                    'id': customer_order_summary.id,
                    'nums': num_orders,
                    'first_order_dt': customer_order_summary.first_order_dt.strftime('%b %d, %Y %I:%M%p'),
                    'last_order_at': last_order_at.strftime('%b %d, %Y %I:%M%p'),
                    'lifetime_value': '%.2f' % customer_lifetime_value
                }

            # LifeCycle
            lifecycle = (CustomerLifecycleTracking.objects
                         .filter(customer__riid__in=riids)
                         .values_list('funnel_step',
                                      'lifecycle_messaging_stage',
                                      'lifecycle_messaging_data',
                                      'modified_dt'
                                      ))
            for funnel_step, lifecycle_messaging_stage, lifecycle_messaging_data, modified_dt in lifecycle:
                mp_lc = {
                    'funnel_step': funnel_step,
                    'lifecycle_messaging_stage': lifecycle_messaging_stage,
                    'lifecycle_messaging_data': lifecycle_messaging_data,
                    'modified_dt': modified_dt.strftime('%b %d, %Y %I:%M%p'),
                }
                lifecycle_list.append(mp_lc)
        context = {
            'email': json.dumps(email),
            'orders': json.dumps(orders),
            'sessions': json.dumps(sessions_info),
            'pageviews': json.dumps(pageviews),
            'order_summary': json.dumps(order_summary),
            'lifecycle': json.dumps(lifecycle_list)
        }
        return context


class CustomerEmail(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'customer_email.html'
    login_url = '/accounts/login'

    def get(self, request):
        context = {}
        return self.render_to_response(context)


def open_purchase_orders(request):
    """
    Returns open purchase orders. Used in a Google Spreadsheet:
    https://docs.google.com/spreadsheets/d/1-vARZLSWx94rnwc3_5akMFZk6i3vXwnk2Z_nYEOhmYY/edit#gid=0
    """
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            if auth[0].lower() == 'basic':
                uname, passwd = base64.b64decode(auth[1]).split(':')
                user = authenticate(username=uname, password=passwd)
                if user is not None and user.is_active:
                    request.user = user
                    open_pos = ErpInventoryPurchaseOrder.objects.filter(status=5).exclude(
                        create_by='BO Upload, User: abrahama')
                    open_info = []
                    for o in open_pos:
                        open_info.append({
                                'purchase_order_id': o.purchase_order_id,
                                'purchase_time': o.purchase_on.astimezone(
                                    pytz.timezone('US/Pacific')).strftime('%Y-%m-%d %H:%S'),
                                'created_by': o.create_by,
                                'supplier_name': o.supplier_name,
                                'expected_date': o.expected_date,
                                'total_products': o.total_products,
                                'status': o.status
                            })
                    # timeout sets the cache to expire in 60 minutes.
                    return JsonResponse(open_info, safe=False)
    response = HttpResponse()
    response.status_code = 401
    response['content'] = ('Credentials not authorized. Username: %s, Pass: %s'
                           % (uname, passwd))
    response['WWW-Authenticate'] = 'Basic Auth Protected'
    return response


class LifecycleAnalytics(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = "lifecycle_analytics.html"

    def get(self, request):
        current_time = datetime.datetime.now(utc).astimezone(pytz.timezone('US/Pacific'))
        earlier_time = current_time - datetime.timedelta(hours=24)
        if not cache.get('lifecycle_today'):
            self.get_lifecycle_status()
        mp_sender_today = json.loads(cache.get('lifecycle_today'))
        mp_sender_yesterday = json.loads(cache.get('lifecycle_yesterday'))
        mp_sender_week = json.loads(cache.get('lifecycle_week'))
        context = {
            'senders_today': json.dumps(mp_sender_today),
            'senders_yesterday': json.dumps(mp_sender_yesterday),
            'senders_week': json.dumps(mp_sender_week),
            'date_from': json.dumps(earlier_time.strftime('%Y-%m-%d %H')),
            'date_to': json.dumps(current_time.strftime('%Y-%m-%d %H')),

        }
        return self.render_to_response(context)

    def get_lifecycle_status(self):
        # lifecycle status for today, from 23 hour ago to now
        t_to = datetime.datetime.now(utc).astimezone(pytz.timezone('US/Pacific'))
        t_from = t_to - datetime.timedelta(hours=23)
        # lifecycle status for yesterday
        y_to = t_to - datetime.timedelta(hours=24)
        y_from = y_to - datetime.timedelta(hours=23)
        # lifecycle status for 7 days average preceding yesterday
        # eg: today is July 20 then the avg # of sends per hour metric should
        # reflect those averages from July 12 - 18.
        w_from = t_to - datetime.timedelta(hours=239)
        w_to = t_to - datetime.timedelta(hours=72)
        lifecycle_today = self.get_lifecycle(t_from, t_to, '%Y-%m-%d %H')
        lifecycle_yesterday = self.get_lifecycle(y_from, y_to, '%Y-%m-%d %H')
        lifecycle_week = self.get_lifecycle(w_from, w_to, '%H', avg=True)
        cache.set('lifecycle_today', json.dumps(lifecycle_today), 3600)
        cache.set('lifecycle_yesterday', json.dumps(lifecycle_yesterday), 3600)
        cache.set('lifecycle_week', json.dumps(lifecycle_week), 3600)

    def get_lifecycle(self, dt_from, dt_to, time_format, avg=False):
        mp_lifecycle = []
        mp_sender = collections.OrderedDict()
        dt_earlier = dt_from
        while dt_earlier <= dt_to:
            mp_sender[dt_earlier.strftime(time_format)] = 0
            dt_earlier += datetime.timedelta(hours=1)
        sender_log = SenderLog.objects.filter(send_datetime__lte=dt_to,
                                              send_datetime__gt=dt_from
                                              ).order_by('send_datetime')
        for sender in sender_log:
            send_datetime = sender.send_datetime
            response = sender.response
            send_hour = send_datetime.astimezone(pytz.timezone('US/Pacific')).strftime(time_format)
            mp_sender[send_hour] += response.count("u'success': True")

        for hour in mp_sender:
            if avg:
                mp_sender[hour] = mp_sender.get(hour) / 7.0
            mp_lifecycle.append({
                'hour': hour,
                'num': int(math.ceil(mp_sender[hour]))
            })
        mp_lifecycle = mp_lifecycle[:-1]
        print('done')
        return mp_lifecycle


class OrderLookup(LoginRequiredMixin, TemplateResponseMixin, View):

    template_name = 'order_lookup.html'

    def gen_query(self, request, *args, **kwargs):
        """
        Generate basic query
        If it is partial search, then use "contains" else use "="
        @param request:
        @param args:
        @param kwargs:
        @return:
        """
        assert len(args) > 0
        if kwargs.get('contains'):
            query_info = map(lambda e: self.load_params(request, e, contains=True), args)
        else:
            query_info = map(lambda e: self.load_params(request, e), args)
        queries = [Q(**x) for x in query_info if x]
        if queries:
            return reduce(lambda x, y: x & y, queries)
        else:
            return Q()

    def get(self, request):
        """
        Get query params from frontend and generate different queries
        Each query can search without other criteria
        Add pagination for orders
        @param request:
        @return:
        """
        datefrom = request.GET.get('datefrom')
        dateto = request.GET.get('dateto')
        lastfour = request.GET.get('lastfour')

        address_query = self.gen_query(request, 'postcode', 'telephone',
                                       contains=False)
        address_query = Q(
            shipping_address__in=SalesFlatOrderAddress.objects.filter(address_query)) if address_query else Q()

        if datefrom and dateto:
            datefrom = json.loads(datefrom)
            dateto = json.loads(dateto)
            date_query = Q(created_at__gte=datefrom, created_at__lte=dateto)
        elif datefrom:
            datefrom = json.loads(datefrom)
            date_query = Q(created_at__gte=datefrom)
        elif dateto:
            dateto = json.loads(dateto)
            date_query = Q(created_at__lte=dateto)
        else:
            date_query = Q()

        order_query = self.gen_query(request, 'increment_id', 'customer_email',
                                     'customer_firstname', 'customer_lastname',
                                     contains=True)

        if lastfour:
            lastfour = json.loads(lastfour)
            parent_ids = (SalesFlatOrderPayment.objects
                          .filter(cc_last4=lastfour)
                          .values_list('parent_id', flat=True))
            parent_ids = [parent_id for parent_id in parent_ids]
            payment_query = Q(entity_id__in=parent_ids)
        else:
            payment_query = Q()

        if (not order_query and
                not address_query and
                not payment_query and
                not date_query):
            rg_orders = []
        else:
            orders = SalesFlatOrder.objects.filter(order_query, address_query,
                                                   date_query, payment_query)
            rg_orders = self.pull_order_info(orders).get('rg_orders')

        page = request.GET.get('page', 1)
        paginator = Paginator(rg_orders, 50)
        try:
            orders = paginator.page(page)
        except PageNotAnInteger:
            orders = paginator.page(1)
        except EmptyPage:
            orders = paginator.page(paginator.num_pages)
        page_ranges = list(paginator.page_range)

        context = {
            'page_orders': json.dumps({
                'page': orders.object_list,
                'current': orders.number,
                'previous': orders.has_previous(),
                'next': orders.has_next(),
                'last_page': paginator.num_pages,
                'pages': page_ranges
            }),
            'orders': json.dumps(rg_orders)

        }
        return self.render_to_response(context)

    def load_params(self, request, field, contains=False):
        """
        Load data from front end and prepare for generating queries
        Create a pair of a field and its query format for each field in data
        @param request:
        @param field:
        @param contains:
        @return:
        """
        field_val = request.GET.get(field)
        if field_val:
            field_val = json.loads(field_val)
            if not contains:
                return {field: field_val}
            else:
                return {'%s%s' % (field, '__icontains'): field_val}
        else:
            return None

    def pull_order_info(self, orders):
        """
        Pull order information from db according to querys
        @param orders:
        @return: A dict with orders and date information
        """
        orders = orders.prefetch_related('salesflatorderitem_set',
                                         'salesflatorderpayment_set',
                                         'billing_address',
                                         'shipping_address')

        order_ids = [order.entity_id for order in orders]
        rg_shipment_track = list(SalesFlatShipmentTrack.objects.filter(
            parent__order_id__in=order_ids
        ).values_list('parent__order_id', 'carrier_code', 'track_number',
                      'parent_id'))
        mp_tracks = defaultdict(dict)
        for order_id, carrier_code, track_number, parent_id in rg_shipment_track:
            mp_tracks[order_id] = {
                'carrier_code': carrier_code,
                'track_number': track_number,
            }
        rg_orders = []
        product_ids = []
        customer_orders = orders
        for order in customer_orders:
            for item in order.salesflatorderitem_set.all():
                product_ids.append((item.product_id,
                                    item.added_from_category_id))

        total_rev = 0
        for order in customer_orders:
            order_items = []
            order_payment_method = []
            order_payment_last4 = []
            item_qty = 0
            for item in order.salesflatorderitem_set.all():
                item_qty += int(item.qty_ordered)
                item_info = {
                    'product_id': item.product_id,
                    'sku': item.sku,
                    'qty': int(item.qty_ordered),
                    'price': '%.2f' % item.price,
                    'discount': '%.2f' % item.discount_amount if item.discount_amount else 0,
                    'total': float(item.price * item.qty_ordered),
                    'name': item.name,
                }
                order_items.append(item_info)
            for payment in order.salesflatorderpayment_set.all():
                order_payment_method.append(payment.method)
                order_payment_last4.append(payment.cc_last4)

            payment_last4 = ' '.join([x for x in order_payment_last4 if x])
            payment_method = ' '.join([x for x in order_payment_method if x])

            order_info = {
                'entity_id': order.entity_id,
                'order_number': order.increment_id,
                'name': '%s %s' % (order.customer_firstname,
                                   order.customer_lastname),
                'email': order.customer_email,
                'firstname': order.customer_firstname,
                'lastname': order.customer_lastname,
                'billing_address': model_to_dict(order.billing_address),
                'shipping_address': model_to_dict(order.shipping_address),
                'products': order_items,
                'payment_method': payment_method,
                'payment_last4': payment_last4,
                'status': order.status,
                'grand_total': '%.2f' % order.grand_total if order.grand_total else 0,
                'shipping_amount': '%.2f' % order.shipping_amount if order.shipping_amount else 0,
                'subtotal': '%.2f' % order.subtotal if order.subtotal else 0,
                'total_refunded': '%.2f' % order.total_refunded if order.total_refunded else 0,
                'tax_amount': '%.2f' % order.tax_amount if order.tax_amount else 0,
                'order_id': order.increment_id,
                'discount_amount': '%.2f' % order.discount_amount if order.discount_amount else 0,
                'coupon_code': order.coupon_code or 'N/A',
                'shipping_description': order.shipping_description,
                'track': mp_tracks.get(order.entity_id),
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'order_source': order.order_source or 'N/A',
                'order_from': order.store_name or 'N/A'

            }
            rg_orders.append(order_info)
            total_rev += order.grand_total if order.status != 'cancel' else 0
        first_date = rg_orders[-1].get('created_at') if len(rg_orders) else 'N/A'
        return {
            'first_date': first_date,
            'total_rev': '%.2f' % total_rev,
            'rg_orders': rg_orders
        }


class OrderDetails(LoginRequiredMixin, TemplateResponseMixin, View):

    template_name = 'order_details.html'

    def get(self, request):
        order_id = request.GET.get('orderNum')
        email = request.GET.get('orderEmail')
        recent_orders = (SalesFlatOrder.objects
                         .filter(customer_email=email)
                         .order_by('-created_at')[:3])
        orders = SalesFlatOrder.objects.filter(increment_id=order_id)
        rg_coupons = []
        coupons = SalesFlatOrder.objects.filter(
            customer_email=email, coupon_code__isnull=False).annotate(
            discount_percent=F('discount_amount') / F('subtotal')).values(
            'coupon_code', 'max_discount_amount', 'discount_amount',
            'discount_percent', 'applied_rule_ids', 'subtotal')

        # Get coupon rule
        ms_rule_ids = set()
        for coupon in coupons:
            applied_rule_ids = map(int, coupon.get('applied_rule_ids').split(','))
            for rule_id in applied_rule_ids:
                ms_rule_ids.add(rule_id)

        # Get coupon rule
        rg_values = Salesrule.objects.filter(
            rule_id__in=ms_rule_ids
        ).values_list('rule_id', 'name', 'description', 'simple_action',
                      'discount_amount', 'apply_to_shipping')
        mp_rules = {}

        for rule_id, name, description, simple_action, discount_amount, b_shipping in rg_values:
            mp_rules[rule_id] = {
                'description': description,
                'displayname': name,
                'itemid': name,
                'apply_to_shipping': b_shipping,
            }

        for coupon in coupons:
            applied_rule_ids = map(int, coupon.get('applied_rule_ids').split(','))
            coupon_info = {
                'coupon_code': coupon.get('coupon_code'),
                'discount_amount': '%.2f' % coupon.get('discount_amount'),
                'subtotal': '%.2f' % coupon.get('subtotal'),
                'max_discount_amount': '%.2f' % coupon.get('max_discount_amount'),
                'discount_percent': '%.0f%s' % (-coupon.get('discount_percent') * 100, '%'),
                'applied_rule_ids': coupon.get('applied_rule_ids'),
                'rule_limit': [mp_rules.get(rule_id) for rule_id in applied_rule_ids],
            }
            rg_coupons.append(coupon_info)
        order_lookup = OrderLookup()
        rg_orders = order_lookup.pull_order_info(orders).get('rg_orders')
        rg_recent_orders = order_lookup.pull_order_info(recent_orders)
        recent_orders = rg_recent_orders.get('rg_orders')
        customer_lifecycle = self.get_customer_total(email)
        helpscout_info = {}
        hsc = HelpscoutConnect()
        conversations = []
        if email:
            helpscout = hsc.get_customer_profile(email)
            if helpscout.get('success') and isinstance(helpscout.get('content'),
                                                       str):
                helpscout_info = json.loads(helpscout.get('content'))
                profile = helpscout_info.get('items')
                if profile:
                    customer_id = profile[0].get('id')
                    # Get all conversations for a customer
                    conversations = hsc.get_customer_conversation(customer_id)
        context = {
            'orders': json.dumps(rg_orders),
            'recent_orders': json.dumps(recent_orders),
            'helpscout_info': json.dumps(helpscout_info),
            'coupons': json.dumps(rg_coupons),
            'email': json.dumps(email),
            'customer_lifecycle': json.dumps(customer_lifecycle),
            'conversations': json.dumps(conversations)
        }
        return self.render_to_response(context)

    # def get_avg_ship(self):
    #     current_time = datetime.datetime.now(utc).astimezone(pytz.timezone('US/Pacific'))
    #     earlier_time = current_time - datetime.timedelta(days=7)
    #     SalesFlatOrder.objects.filter(created_at__gte=earlier_time).aggregate(Avg(F('delivery_at')-F('created_at')))

    def get_customer_total(self, email):
        customer_order_summary = CustomerId.objects.filter(email=email).all()
        if not customer_order_summary:
            order_summary = {}
        else:
            customer_ids = [customer.id for customer in customer_order_summary]
            customer_order_total = CustomerIdOrderId.objects.filter(
                customer_id__in=customer_ids
            ).order_by('created_at').values_list('order_grand_total', 'created_at')
            first = customer_order_total[0][1]
            customer_lifetime_value = sum([total for total, created_at in customer_order_total])
            num_orders = len(customer_order_total)
            order_summary = {
                'nums': num_orders,
                'first_order_dt': first.strftime('%b %d, %Y %I:%M%p'),
                'lifetime_value': '%.2f' % customer_lifetime_value
            }
        return order_summary


class OrderCancelEmail(TemplateResponseMixin, View):

    def __init__(self):
        super(OrderCancelEmail, self).__init__()
        self.auth = ResponsysCredential.objects.all()[0]
        self.headers = {'Authorization': self.auth.token}
        self.campaign_name = 'CO_OrderCancellation_Trans'
        self.campaign_endpoint = ('%s/rest/api/v1.1/campaigns/%s/email' %
                                  (self.auth.endpoint, self.campaign_name))
        self.list_name = 'CONTACT_LIST'
        self.product_attributes = []
        self.order_ids = []
        self.order_details = {}

    def get(self, request):
        """
        Used to subscribe customers to SlickText and redirecs them to the passed
        redirect_url.
        @param request:
        @return:
        """
        order_id = request.GET.get('order_id', False)
        if order_id:
            return JsonResponse({
                'result': self.send_order_cancellation_email(order_id)
            })
        return JsonResponse({'result': 'Need order ID in URL parameters'})

    def send_order_cancellation_email(self, order_id):
        orders = SalesFlatOrder.objects.filter(increment_id=order_id)
        print 'Found %s matching orders' % orders.count()
        orders = orders.prefetch_related('salesflatorderitem_set',
                                         'billing_address', 'shipping_address')
        order_map = {x.increment_id: x for x in orders}

        rg_orders = []
        product_ids = []
        customer_orders = order_map.values()

        for order in customer_orders:
            for item in order.salesflatorderitem_set.all():
                product_ids.append((item.product_id, item.added_from_category_id))
        rg_fields = ['name', 'image', 'product_type',
                     'price', 'special_price', 'msrp',
                     'special_from_date', 'special_to_date',
                     'url_path', 'url_key']
        rg_temp = list({x for x, _ in product_ids})
        p_attr = EavAttribute.objects.get_values(rg_temp, field_names=rg_fields)

        for order in customer_orders:
            order_items = []
            item_qty = 0
            for item in order.salesflatorderitem_set.all():
                data = p_attr.get(item.product_id, {})
                item_qty += int(item.qty_ordered)
                item_info = {
                    'product_id': item.product_id,
                    'sku': item.sku,
                    'qty': int(item.qty_ordered),
                    'price': data.get('price'),
                    'special_price': item.price,
                    'total': float(item.price * item.qty_ordered),
                    'name': item.name,
                    'url_path': '%s%s' % (
                        generate_url_prefix(item.added_from_category_id).replace('.html', '/'),
                        data.get('url_path')
                    ),
                    'image': self.get_image_url(data.get('image', '')),
                    'save_percent': round(
                        (
                            data.get('price', 0) - float(item.price)
                        ) / data.get('price'), 4) * 100,
                    'save_dollars': int(round(
                        (data.get('price', 0) * float(item.qty_ordered)) - int(item.price * item.qty_ordered), 0
                    )),
                }
                order_items.append(item_info)
            order_info = {
                'products': order_items,
                'items_count': item_qty,
                'billing_address': model_to_dict(order.billing_address),
                'shipping_address': model_to_dict(order.shipping_address),
                'customer_email': order.customer_email,
                'grand_total': order.grand_total,
                'tax_amount': order.tax_amount,
                'order_id': order.increment_id,
                'created_at': order.created_at,
                'updated_at': order.updated_at,
                'discount_amount': order.discount_amount,
                'coupon_code': order.coupon_code,
                'shipping_amount': order.shipping_amount,
                'shipping_description': order.shipping_description,
                'subtotal': order.subtotal
            }
            rg_orders.append(order_info)
        rg_orders = self.append_strands_products(rg_orders)
        return self.call_oc_responsys(rg_orders)

    def append_strands_products(self, rg_orders):
        # Run through rg_orders and check for strands_id in
        # map_order_id_strands_id
        map_order_id_strands_id = self.map_order_ids_strands_ids(rg_orders)
        for r in rg_orders:
            if map_order_id_strands_id.get(r['order_id'], False):
                strands_products = self.get_strands_products(map_order_id_strands_id[r['order_id']])
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

    def get_strands_products(self, strands_id):
        params = {
            'apid': settings.STRANDS_APID,
            'tpl': 'conf_3',
            'format': 'json',
            'user': strands_id,
            'amount': 6,
        }
        response = requests.get(settings.STRANDS_ENDPOINT, params=params)
        strands_products = []
        if response.status_code == 200:
            results = json.loads(response.content)
            for r in results['result']['recommendations']:
                product = r['metadata']
                img_url = product.get('picture', '') if 'http' in product.get('picture', '') else 'https://%s' % product.get('picture', '')
                p = {
                    'url_path': product.get('link', ''),
                    'name': product.get('name', ''),
                    'special_price': float(product.get('price', '')),
                    'image': img_url,
                    'price': float(product['properties'].get('cretail_price', [0])[0]),
                }
                try:
                    p['save_percent'] = round(
                        (p['price'] - p['special_price']) / p['price'], 4) * 100
                    p['save_dollars'] = int(round(p['price'] - p['special_price'], 0))
                except KeyError:
                    p['save_percent'] = 0
                    p['save_dollars'] = 0
                    p['special_price'] = p['price']
                strands_products.append(p)
            # customer_data[customer]['strands_product_attributes'] = ';;-;;'.join(strands_products[0].keys())
        return strands_products

    def get_image_url(self, image):
        if not image:
            return image
        if image.startswith('URL/'):
            image = image.replace('URL', 'http://cellularoutfitter.com/media/catalog/product')
        else:
            image = 'http://cellularoutfitter.com/media/catalog/product/%s' % (image,)
        return image

    def call_oc_responsys(self, data):
        """
        :param data:
        :param :
        :return:
        """
        if len(data) == 0:
            return None
        request_payload = self.make_request_payload(data)
        r = requests.post(self.campaign_endpoint, json=request_payload,
                          headers=self.headers)
        if r.status_code == 200:
            r_content = json.loads(r.content)
            self.process_send_result(r_content)
            return r_content
        logger.error('The request to post the data to CampaignEndpoint failed '
                     ': %s', r.reason, extra=locals())
        return {
            'message': r.reason
        }

    def process_send_result(self, r_content):
        """
        Update OrderConfirmationSendLog with the results of each attempted call
        to Responsys.
        :type r_content: dict
        :param r_content: Response from Responsys call
        :return: None
        """
        # order_id_results = []
        pass
        #     order_id_results.append(
        #         OrderConfirmationSendLog(
        #             order_id = order_id,
        #             response = r['success'],
        #             order_updated_at = self.order_details[order_id]['order_updated_at'],
        #             base_grand_total = self.order_details[order_id]['order_grand_total'],
        #         )
        #     )
        # OrderConfirmationSendLog.objects.bulk_create(order_id_results)

    def make_request_payload(self, data):
        """
        Transforms list of order data dicitonaries into format suitable for
        responsys.
        :type data: list(dict)
        :rtype: tuple(dict, dict)
        :return: Request payload for Responsys API call, order_id-keyed
        dictionary with information for OrderConfirmationSendLog table.
        """
        self.product_attributes = {'products': data[0]['products'][0].keys()}
        recipients = []
        orders = data
        for d in orders:
            if d.get('includes_strands', '') == 'yes':
                self.product_attributes['strands_products'] = d['strands_products'][0].keys()

        email_to_riids = self.get_riid_from_email([o.get('customer_email', '') for o in orders])
        if settings.DEBUG:
            email_to_riids.update(self.get_riid_from_email(settings.RESPONSYS_EMAIL))
        for order in orders:
            self.order_ids.append(order['order_id'])
            self.order_details[order['order_id']] = {
                'order_updated_at': order['created_at'],
                'order_grand_total': order['grand_total']
            }
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
                            self.normalize_data_type(product.get(p_k))
                            for p_k in self.product_attributes['products']]))
                        opt_products_data.append(opt_products)
                    opt_products_data = ';;-;;'.join(opt_products_data)
                    opt_data.append({'name': 'products', 'value': opt_products_data})
                elif k == 'strands_products':
                    for product in v:
                        # self.strands_product_attributes = k['strands_products'][0].keys()
                        opt_products = ';-;'.join(map(str, [
                                self.normalize_data_type(product.get(p_k))
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
                    v = self.normalize_data_type(v)
                    for original, replacement in address_map.iteritems():
                        opt_data.append({'name': replacement % k.split('_')[0].upper(), 'value': v[original]})
                else:
                    opt_data.append({'name': k, 'value': self.normalize_data_type(v)})
            if not settings.DEBUG:
                riid = email_to_riids.get(customer_email)
            else:
                riid = email_to_riids.get(settings.RESPONSYS_EMAIL)
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

    def normalize_data_type(self, data_type):
        if isinstance(data_type, Decimal):
            data_type = '%s' % round(data_type, 2)
        elif isinstance(data_type, datetime.datetime):
            data_type = data_type.isoformat()
        return data_type

    def get_riid_from_email(self, email):
        """
        Returns RIID found for a given email address.
        @param email: list()
        @return: dict[str, str]
        """
        merge_endpoint = ('%s/rest/api/v1.1/lists/%s/members' %
                          (self.auth.endpoint, self.list_name))
        data = {
            'recordData': {
                'fieldNames': ['email_address_'],
                'records': [[e] for e in email],
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
            return {e: riids[ix][0] for ix, e in enumerate(email)}
        logger.error('Failed to request Responsys Api custom event: %s' %
                     r.reason, extra=locals())
        return JsonResponse({
            'message': 'Failed to request Responsys Api custom event'
        })


def send_order_cancellation_email(request):
    uname = ''
    passwd = ''
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            if auth[0].lower() == 'basic':
                uname, passwd = base64.b64decode(auth[1]).split(':')
                user = authenticate(username=uname, password=passwd)
                if user is not None and user.is_active:
                    request.user = user
                    order_id = request.GET.get('order_id', False)
                    if order_id:
                        return JsonResponse({'result': OrderCancelEmail().send_order_cancellation_email(order_id)})
                    return JsonResponse({'result': 'Need order_id in params'})
    response = HttpResponse()
    response.status_code = 401
    response['content'] = ('Credentials not authorized. Username: %s, Pass: %s'
                           % (uname, passwd))
    response['WWW-Authenticate'] = 'Basic Auth Protected'
    return response
