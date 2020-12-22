# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import logging
import random
import requests
import urllib

from collections import defaultdict

from django import template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.db import IntegrityError
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.template.response import TemplateResponse
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin

from .models import NetPromoterScore, OptedOutEmails, ResponsysCredential
from mobovidata_dj.lifecycle.models import BirthdaySubmission
from mobovidata_dj.responsys.utils import ResponsysApi
from modjento.models import CatalogCategoryFlatStore2

logger = logging.getLogger(__name__)

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    group = Group.objects.get(name=group_name)
    return True if group in user.groups.all() else False


class IsCS(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(name='CS').exists()


@login_required()
def token_list(request):
    """
    Update responsys credential if there is a update request from front end,
    else get the existing credentials from  ResponsysCredential model.
    :param request: http request
    :return: http response of credentials
    """
    credentials = ResponsysCredential.objects.all()

    if request.method == 'POST':
        ResponsysCredential.objects.update_responsys_token()
        messages.add_message(request, messages.INFO, 'Token updated successfully.')
        return render_to_response(
            'responsys/credentials.html',
            {'credentials': credentials},
            context_instance=RequestContext(request)
        )
    else:
        return render_to_response(
            'responsys/credentials.html',
            {'credentials': credentials},
            context_instance=RequestContext(request)
        )


class EmailRIIDLookup(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'email_riid_lookup.html'
    login_url = '/accounts/login/'

    def get(self, *args, **kwargs):
        """
        Not needed here for now.
        :param args:
        :param kwargs:
        :return:
        """
        context = {}
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Accept riid from storefront, and send it to backend to translate riid
        and email if uiid is empty, we will call get_riid_from_email to get it.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        riid = None
        email = None
        try:
            riid = int(request.POST.get('riid'))
        except:
            email = request.POST.get('riid')
        if riid:
            context = {
                'riid': riid,
                'email': ResponsysApi().get_email_from_riid(riid)
            }
        elif email:
            response = ResponsysApi().get_riids(email)
            if response.status_code == 200:
                riids = json.loads(response.content)
                riids = riids['recordData']['records']
                riids = ['%s' % r[0] for r in riids]
                context = {
                    'riid': ', '.join(riids),
                    'email': email,
                }
            else:
                context = {
                    'riid': json.loads(response.content),
                    'email': email
                }
        else:
            context = {
                'riid': 'Please enter an riid',
                'email': 'Or enter an email address'
            }

        return self.render_to_response(context)


class UnsubForm(TemplateResponseMixin, View):
    """
    When customers call to unsubscribe, they can just type their email addresses
    and Responsys Api will be triggered
    """
    template_name = 'unsub_form.html'
    raise_exception = True
    permission_denied_message = 'You do not have permission to access this page'
    login_url = '/accounts/login/'

    def __init__(self):
        """
        :return:
        """
        super(UnsubForm, self).__init__()
        if settings.DEBUG:
            self.list_name = 'CONTACT_LIST_STAGING'
        else:
            self.list_name = 'CONTACT_LIST'
        self.auth = ResponsysCredential.objects.all()[0]
        self.headers = {'Authorization': self.auth.token}
        self.list_endpoint = '%s/rest/api/v1.1/lists/%s/members/' % (self.auth.endpoint,
                                                                     self.list_name)

    def get(self, request, *args, **kwargs):
        """
        Return unsub_form.html page
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        authenticated = True if request.user.is_authenticated() else False
        return self.render_to_response({
            'authenticated': json.dumps(authenticated),
            'isUnsubbed': 0,
            'email': 0
        })

    def update_email_preferences_table(self, riids, request_data):
        """
        Updates email preferences table in Responsys based on data passed in request.POST
        :type riids: list
        :type request_data: dict
        :return:
        """
        table_records_ep = '%s/rest/api/v1.1/folders/%s/suppData/%s/members' % (
            self.auth.endpoint, '!MageData', 'EMAIL_PREFERENCES'
        )
        table_fields = ['EMAIL_PERMISSION_STATUS_', 'NEWSLETTERS', 'PROMOTIONS',
                        'NEW_PRODUCTS']
        preferences = [request_data.get(f, 0) for f in table_fields]
        table_records_request = {
            'recordData': {
                'fieldNames': [
                    'RIID_', 'EMAIL_PERMISSION_STATUS_', 'NEWSLETTERS', 'PROMOTIONS', 'NEW_PRODUCTS',
                ],
                'records': [[r] + preferences for r in riids],
                'mapTemplateName': ''
            },
            'insertOnNoMatch': True,
            'updateOnMatch': 'REPLACE_ALL'
        }
        return requests.post(table_records_ep, json=table_records_request,
                             headers=self.headers)

    def update_email_preferences_feedback_table(self, riids, request_data):
        """
        Updates email_preferences_feedback table in Responsys based on data
        passed in request.POST
        :param riids: list
        :param request_data: dict
        :return:
        """
        table_records_ep = '%s/rest/api/v1.1/folders/%s/suppData/%s/members' % (
            self.auth.endpoint, '!MageData', 'EMAIL_PREFERENCES_FEEDBACK'
        )
        table_fields = ['TOO_MANY_EMAILS',
                        'EMAILS_NOT_RELEVANT',
                        'EMAILS_CONTAINED_ERRORS',
                        'ADDITIONAL_COMMENTS',
                        'PRODUCT_NEG',
                        'PRODUCT_REC']
        preferences = [request_data.get('%s' % f, '%s' % 0) for f in table_fields]
        table_records_request = {
            'recordData': {
                'fieldNames': [
                    'RIID_',
                    'TOO_MANY_EMAILS',
                    'EMAILS_NOT_RELEVANT',
                    'EMAILS_CONTAINED_ERRORS',
                    'ADDITIONAL_COMMENTS',
                    'PRODUCT_NEG',
                    'PRODUCT_REC',
                ],
                'records': [[r] + preferences for r in riids],
                'mapTemplateName': ''
            },
            'insertOnNoMatch': True,
            'updateOnMatch': 'REPLACE_ALL'
        }
        return requests.post(table_records_ep, json=table_records_request,
                             headers=self.headers)

    def parse_get_riids_response(self, response):
        records = json.loads(response.content)['recordData']['records']
        return [r[0] for r in records if r[2] == '2']

    def opt_out_email(self, email_address, is_authenticated=False, contact_list='CONTACT_LIST'):
        fields = ['email_permission_status_', 'email_address_']
        values = [['O', email_address]]
        response = ResponsysApi(list_name=contact_list).merge_list_members(
            fields, values, match1='EMAIL_ADDRESS_', match2=None)

        riids, errors = ResponsysApi.get_riids_from_response(response)

        if response.status_code != 200 and response.status_code != 503:
            OptedOutEmails.objects.add_email_unsub(
                    email_address
                )
            return False
        elif response.status_code == 503:
            if 'pending_responsys_requests:merge_list_members' in cache:
                pending_requests = cache.get('pending_responsys_requests:merge_list_members')
                pending_requests.append({'fields': fields,
                                         'values': values,
                                         'match1': 'EMAIL_ADDRESS_',
                                         'match2': None, })
                cache.set('pending_responsys_requests:merge_list_members', pending_requests)
            else:
                cache.set('pending_responsys_requests:merge_list_members',
                          [{'fields': fields,
                            'values': values,
                            'match1': 'EMAIL_ADDRESS_',
                            'match2': None, }])
            OptedOutEmails.objects.add_email_unsub(email_address)
        # Update OptedOutEmails table if customer unsubsribed
        elif response.status_code == 200 and errors:
            logger.warning('[Responsys API] - Merge list members parsing error',
                           extra=locals())
            return False
        elif response.status_code == 200:
            j = json.loads(response.content)
            riid = j['recordData']['records'][0][0]
            OptedOutEmails.objects.add_email_unsub(
                email_address,
                riid=riid,
            )
        return True

    def opt_out_riids(self, riids, is_authenticated=False, contact_list='CONTACT_LIST'):
        result = False
        fields = ['email_permission_status_', 'riid_']
        values = [['O', riid] for riid in riids]
        response = ResponsysApi(list_name=contact_list).merge_list_members(
            fields, values, match1='RIID_', match2=None)

        riids, errors = ResponsysApi.get_riids_from_response(response)

        if response.status_code == 200 and not errors:
            result = True

        return result

    def post(self, request, *args, **kwargs):
        """
        Update email_permission_status_ value to opt out in contact list given
        an email address
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        email_address = request.POST.get('email_address', '')
        authenticated = True if request.user.is_authenticated() else False
        is_unsubbed = 1 if request.POST.get('EMAIL_PERMISSION_STATUS_') else 0
        if not email_address:
            logger.warning('Please enter an email address.')
            messages.add_message(request, messages.INFO, 'Please enter a valid email address.')
            authenticated = True if request.user.is_authenticated() else False
            return self.render_to_response({
                'authenticated': json.dumps(authenticated)
            })
        permission_status = request.POST.get('EMAIL_PERMISSION_STATUS_')
        # permission_status = request.POST.get('EMAIL_PERMISSION_STATUS_', False)
        response = ResponsysApi().get_riids(email_address)
        cache.set('pending_responsys_requests:get_riids', [{k: v for k, v in request.POST.items()}, ])
        if response.status_code != 200 and response.status_code != 503:
            riids = []
        elif response.status_code == 503:
            if 'pending_responsys_requests:get_riids' in cache:
                pending_requests = cache.get('pending_responsys_requests:get_riids')
                pending_requests.append({k: v for k, v in request.POST.items()})
                cache.set('pending_responsys_requests:get_riids', pending_requests)
            else:
                cache.set('pending_responsys_requests:get_riids', [{k: v for k, v in request.POST.items()}, ])
            messages.add_message(
                request, messages.INFO, 'Successfully updated customer preferences for %s' % email_address
            )
            return self.render_to_response({'authenticated': json.dumps(authenticated)})
        else:
            riids = self.parse_get_riids_response(response)

        if len(riids) == 0 or request.POST.get('EMAIL_PERMISSION_STATUS_', False):
            authenticated = True if request.user.is_authenticated() else False
            if len(riids) > 0:
                success = self.opt_out_riids(riids, is_authenticated=authenticated)
            else:
                success = self.opt_out_email(email_address, is_authenticated=authenticated)
            if len(riids) == 0:
                if not success:
                    messages.add_message(
                        request, messages.INFO, 'Failed to request Responsys Api: %s' % json.loads(response.content)
                    )
                else:
                    messages.add_message(
                        request, messages.INFO, 'Successfully updated customer preferences for %s' % email_address
                    )
                return self.render_to_response({
                    'authenticated': json.dumps(authenticated)
                })

        request_data = {k: v for k, v in request.POST.items()}
        response = self.update_email_preferences_table(riids, request_data)
        if response.status_code != 200:
            response_content = json.loads(response.content)
            messages.add_message(
                request, messages.INFO, 'Failed to request update EMAIL_PREFERENCES table: %s' % response_content
            )
        response = self.update_email_preferences_feedback_table(riids, request_data)
        if response.status_code != 200:
            response_content = json.loads(response.content)
            messages.add_message(
                    request, messages.INFO, 'Failed to request update EMAIL_PREFERENCES table: %s' % response_content
            )
        messages.add_message(request, messages.INFO, 'Successfully updated customer preferences for %s' % email_address)

        return self.render_to_response({
            'authenticated': json.dumps(authenticated),
            'isUnsubbed': is_unsubbed,
            'email': email_address
        })

        # messages.add_message(request, messages.INFO, 'Failed to request Responsys Api: {}'.format(response_content))
        # return self.render_to_response({})


class BDaySubmission(TemplateResponseMixin, View):
    template_name = "bday_submission.html"

    def __init__(self):
        super(BDaySubmission, self).__init__()

    def get(self, request, *args, **kwargs):
        authenticated = True if request.user.is_authenticated() else False
        frequency_options = [
            '1. Not often. I only upgrade my accessories when I upgrade my phone.',
            '2. Occasionally. I update my phone case 1 - 2 times per year.',
            '3. Addictively. I change phone cases like I change outifts.'
        ]
        email = ''
        riid = request.GET.get('riid')
        if riid:
            riid = json.loads(riid)
            email = ResponsysApi().get_email_from_riid(riid)
        mp_model_id = defaultdict(str)
        brand_model_info = CatalogCategoryFlatStore2.objects.filter(level=3, children_count=10).values(
            'entity_id', 'name', 'parent_id'
        ).distinct()
        parent_ids = [p['parent_id'] for p in brand_model_info if p['parent_id'] > 100]
        parent_names = CatalogCategoryFlatStore2.objects.filter(level=2, entity_id__in=parent_ids).values(
            'entity_id', 'name'
        ).distinct()
        parent_ids_names = {r['entity_id']: r['name'] for r in parent_names}
        parent_names = set()
        for r in parent_ids_names.values():
            parent_names.add(r)
        brand_model_info = [r for r in brand_model_info if parent_ids_names.get(r['parent_id'])]
        for r in brand_model_info:
            r['brand_name'] = parent_ids_names.get(r['parent_id'])
        mp_brand_model = defaultdict(set)
        for r in brand_model_info:
            mp_brand_model[r['brand_name']].add(r['name'])
        device_brands = set()
        for k in mp_brand_model.keys():
            device_brands.add(k)
        mp_brand_model = dict([(k, list(mp_brand_model[k])) for k in mp_brand_model])
        return self.render_to_response(
            context={
                'email': json.dumps(email),
                'frequency_options': json.dumps(frequency_options),
                'authenticated': json.dumps(authenticated),
                'device_brands': json.dumps(sorted(list(device_brands))),
                'mp_brand_models': json.dumps(mp_brand_model),
                'riid': json.dumps(riid),
                'mp_model_id': json.dumps(mp_model_id),
            }
        )

    def post(self, request, *args, **kwargs):
        mp_colors = {
            'Red': '#FF0000',
            'Orange': '#FFA500',
            'Yellow': '#ffff00',
            'Green': '#008000',
            'Blue': '#0000FF',
            'Purple': '#800080',
            'Gold': '#D4AF37',
            'Silver': '#C0C0C0',
            'White': '#ffffff',
            'Black': '#000000'
        }
        authenticated = True if request.user.is_authenticated() else False

        # email, birthday, frequency, brand, model are all required fields
        email = request.POST.get('email')
        birthday = request.POST.get('birthday')
        model_id = self.get_normalized_data(request.POST.get('modelId'))
        frequency = self.get_normalized_data(request.POST.get('frequency'))
        brand = self.get_normalized_data(request.POST.get('device_brand'))
        model = self.get_normalized_data(request.POST.get('model'))

        # riid will be passed automatically
        riid = '%s' % request.POST.get('riid')
        r_api = ResponsysApi(list_name='CONTACT_LIST')

        # Save info into contact list pet
        pet_name = 'BIRTHDAY'
        pet_fields = ['riid_', 'bday']
        pet_values = [[riid, birthday]]
        pet_response = r_api.merge_update_pet_members(pet_name, pet_fields, pet_values)

        # Save info into contact list
        brand_model_fields = ['riid_', 'email_address_', 'BRAND_NAME_01',
                              'MODEL_NAME_01', 'MODEL_ID_01']
        brand_model_values = [[riid, email, brand, model, model_id]]
        list_response = r_api.merge_list_members(
            brand_model_fields, brand_model_values, match1='RIID_', match2='EMAIL_ADDRESS_')

        p_success, p_content = self.process_response(request, pet_response)
        l_success, l_content = self.process_response(request, list_response)

        # save color preference into django model
        color = self.get_normalized_data(request.POST.get('color'))
        color_code = mp_colors.get(color)
        BirthdaySubmission.objects.update_or_create(
            riid=riid,
            defaults={
                'color': color,
                'color_code': color_code,
                'frequency': frequency,
                'con_response_success': l_success,
                'con_response': l_content,
                'pet_response_success': p_success,
                'pet_response': p_content,
            }
        )
        response = TemplateResponse(request, 'bday_after_sub.html',
                                    context={'authenticated': json.dumps(authenticated)})
        return response

    def get_normalized_data(self, data):
        data = ('%s' % data).split(':')
        if data and len(data) > 1:
            normalized_data = data[1]
            return normalized_data
        return None

    def process_response(self, request, response):
        if response.status_code != 200:
            success = False
            messages.add_message(
                request, messages.INFO, 'Failed to request Responsys Api: %s' % json.loads(response.content)
            )
        else:
            success = True
        content = json.loads(response.content)
        return success, content


class NpsSubmission(TemplateResponseMixin, View):
    template_name = 'nps_submission.html'

    def __init__(self):
        super(NpsSubmission, self).__init__()

    def get(self, request, *args, **kwargs):
        # Pull customer's data from url params
        if request.GET:
            riid = int(request.GET.get('dz_riid'))
            nps_score = int(request.GET.get('nps'))
            medium = request.GET.get('utm_medium')
            campaign = request.GET.get('utm_campaign')
            promocode = request.GET.get('utm_promocode')

            try:
                NetPromoterScore.objects.update_or_create(
                    riid=riid,
                    nps_score=nps_score,
                    medium=medium,
                    campaign=campaign,
                    promocode=promocode
                )
            except IntegrityError:
                existing_riid = int(riid)
                updating = NetPromoterScore.objects.get(riid=existing_riid)
                updating.nps_score = nps_score
                updating.save()

            if nps_score:
                if nps_score in range(1, 4):
                    # Currently redirecting them to MVD until email form complete
                    return TemplateResponse(request, 'nps_submission.html', context={})
                return redirect(urllib.unquote(self.get_redirect_url(nps_score)))

        return TemplateResponse(request, 'nps_submission.html', context={})

    def get_redirect_url(self, nps_score):
        """
        Based on passed nps_score, will return appropriate url
        @param nps_score: (int) Net promoter score given by customer
        @return: (str) redirect url
        """
        mp_score = {
            1: 'https://www.cellularoutfitter.com/',
            2: 'https://www.cellularoutfitter.com/',
            3: 'https://www.cellularoutfitter.com/',
            4: 'https://www.cellularoutfitter.com/contacts/',
            5: 'https://www.cellularoutfitter.com/contacts/',
            6: 'https://www.cellularoutfitter.com/contacts/',
            7: 'https://www.cellularoutfitter.com/',
            8: 'https://www.cellularoutfitter.com/',
            9: self.coin_flip(),
            10: self.coin_flip(),
        }
        return mp_score.get(nps_score)

    def coin_flip(self):
        """
        @return: (str) pseudo-random choice between SiteJabber or ResellerRatings CO url
        """
        coin = bool(random.getrandbits(1))
        site_jabber = 'https://www.sitejabber.com/online-business-review#cellularoutfitter.com_(CellularOutfitter)'
        reseller_ratings = 'https://www.resellerratings.com/store/survey/Cellular_Outfitter'
        return site_jabber if coin else reseller_ratings
