# _author__ = 'Yuki'

import json
import logging
import requests

from config import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.http import JsonResponse
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin

from mobovidata_dj.responsys.models import ResponsysCredential
from mobovidata_dj.responsys.utils import ResponsysApi

logger = logging.getLogger(__name__)


class HelpScoutEmails(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'email_list.html'
    login_url = '/accounts/login'

    def __init__(self):
        super(HelpScoutEmails, self).__init__()
        self.endpoint = settings.HELPSCOUT_API['endpoint']
        self.api_key = settings.HELPSCOUT_API['api_key']
        self.boxes = settings.HELPSCOUT_MAILBOXES
        if settings.DEBUG:
            self.boxes = [self.boxes[0]]
        self.list_name = 'CONTACT_LIST'
        self.r_auth = ResponsysCredential.objects.all()[0]
        self.headers = {'Authorization': self.r_auth.token}
        self.pet_name = 'OPEN_HELPSCOUT_TICKETS'
        self.cl_endpoint = ('%s/rest/api/v1.1/lists/%s/members/' %
                            (self.r_auth.endpoint, self.list_name))
        self.pe_endpoint = ('%s/rest/api/v1.1/lists/%s/listExtensions/%s/members'
                            % (self.r_auth.endpoint, self.list_name,
                               self.pet_name))

    def get(self, request, *args, **kwargs):
        response = self.update_helpscout()
        return response

    def update_helpscout(self):
        email_riid_list = []
        add_response_list = []
        remove_response_list = []
        step = 200

        for box in self.boxes:
            url = ('%s/v1/mailboxes/%s/conversations.json?status=active' %
                   (self.endpoint, box))
            response = requests.get(url, auth=(self.api_key, '1'))
            response_data = json.loads(response.content)
            if response_data and response_data.get('items'):
                for item in response_data.get('items'):
                    email = item['customer']['email']
                    responsys_call = ResponsysApi().get_riids(email)
                    if responsys_call.status_code != 200:
                        continue
                    riids = json.loads(responsys_call.content)['recordData']['records']
                    for r in riids:
                        email_riid_list.append(('%s' % r[0], r[1]))
        if settings.DEBUG:
            email_riid_list = email_riid_list[:1]

        stored_email_riid_list = email_riid_list
        while email_riid_list:
            members = email_riid_list[:step]
            email_riid_list = email_riid_list[step:]
            response = self.add_members(members)
            add_response_list.append(response.content)
            if settings.DEBUG:
                retrieve_response = ResponsysApi().get_pet_record([x[0] for x in members], self.pet_name)
        previous_email_list = cache.get('previous_email_list', [])
        print previous_email_list
        closed_email_list = set(previous_email_list) - set(stored_email_riid_list)
        logger.debug('closed list %s', closed_email_list)

        while closed_email_list:
            closed_email_list = list(closed_email_list)
            members = [x[0] for x in closed_email_list[:step]]
            closed_email_list = closed_email_list[step:]
            for mem in members:
                response = ResponsysApi().delete_pet_record(mem, 'OPEN_HELPSCOUT_TICKETS')
                remove_response_list.append(response.content)

        cache.set('previous_email_list', stored_email_riid_list)

        return JsonResponse({
            'add_response_list': add_response_list,
            'remove_response_list': remove_response_list,
            'success': True,
            'message': 'Successfully added new members into responsys.'
        })

    def add_members(self, riid_email_list):
        request_data = {
            'recordData': {
                'fieldNames': ['riid_', 'email_address_'],
                'records': riid_email_list,
                'mapTemplateName': None
            },
            'insertOnNoMatch': True,
            'updateOnMatch': 'REPLACE_ALL',
            'matchColumnName1': 'RIID',
            'matchColumnName2': 'EMAIL_ADDRESS'
        }
        response = requests.post(self.pe_endpoint, json=request_data,
                                 headers=self.headers)
        if response.status_code != 200:
            response_content = json.loads(response.content)
            return JsonResponse({
                'success': False,
                'message': response_content
            })
        else:
            return JsonResponse({
                'success': True,
                'message': response.content
            })

    def remove_members(self, riids):
        for riid in riids:
            del_pe_endpoint = self.pe_endpoint = '%s/rest/api/v1.1/lists/%s/listExtensions/%s/members/%s' % (
                self.r_auth.endpoint, self.list_name, self.pet_name, riid
            )
            response = requests.delete(del_pe_endpoint, headers=self.headers)
            if response.status_code != 200:
                response_content = json.loads(response.content)
                return JsonResponse({
                    'success': False,
                    'message': response_content
                })
        else:
            return JsonResponse({
                'success': True
            })

    def retrieve_members(self, riids):
        response_list = []
        for riid in riids:
            retr_pe_endpoint = '%s/rest/api/v1.1/lists/%s/listExtensions/%s/members/%s' % (
                self.r_auth.endpoint, self.list_name, self.pet_name, riid
            )
            response = requests.get(retr_pe_endpoint, params={'fs': ['RIID_']},
                                    headers=self.headers)
            response_list.append(response.content)
            if response.status_code != 200:
                response_content = json.loads(response.content)
                return JsonResponse({
                    'success': False,
                    'message': response_content
                })
        return JsonResponse({
            'success': True,
            'message': response_list
        })
