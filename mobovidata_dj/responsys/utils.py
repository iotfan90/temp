import csv
import datetime
import json
import logging
import models
import os
import pytz
import requests
import StringIO
import zipfile

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone

from .connect import ResponsysFtpConnect

logger = logging.getLogger(__name__)


def get_responsys_token():

    # Returns dict-response of Responsys API authorization call
    # authToken, endPoint, issuedAt
    responsys_auth = {
        'user_name': settings.RESPONSYS_AUTH['user_name'],
        'password': settings.RESPONSYS_AUTH['password'],
        'auth_type': 'password'
    }

    responsys_auth_url = settings.RESPONSYS_AUTH['auth_url']

    resp_auth_req = requests.post(responsys_auth_url, data=responsys_auth)

    auth_content = resp_auth_req.content
    auth_info = json.loads(auth_content)
    return auth_info


class ResponsysApi(object):
    def __init__(self, list_name=None):
        super(ResponsysApi, self).__init__()
        self.auth = models.ResponsysCredential.objects.all()[0]
        if settings.DEBUG and ((timezone.now() - self.auth.modified_dt).seconds / 60) > 90:
            auth_token = get_responsys_token()
            try:
                obj = models.ResponsysCredential.objects.get()
                obj.token = auth_token['authToken']
                obj.endpoint = auth_token['endPoint']
                obj.save()
            except models.ResponsysCredential.DoesNotExist:
                obj = models.ResponsysCredential(
                    token=auth_token['authToken'],
                    endpoint=auth_token['endPoint']
                )
                obj.save()
        if not list_name:
            self.list_name = 'CONTACT_LIST'
        else:
            self.list_name = list_name
        self.auth = models.ResponsysCredential.objects.all()[0]
        self.headers = {'Authorization': self.auth.token}
        self.endpoint = '%s/rest/api/v1.1/' % self.auth.endpoint

    def get_riids(self, email_address):
        """
        Retrieve RIID of a member of a CONTACT_LIST from a single email address
        @param email_address: (str)
        @return: JSON containing requested data
        """
        endpoint = '%s/rest/api/v1.1/lists/%s/members' % (self.auth.endpoint,
                                                          self.list_name)
        params = {
            'qa': 'e',
            'id': email_address,
            'fs': ['riid_', 'email_address_', 'store_id']
        }
        return requests.get(endpoint, params=params, headers=self.headers)

    def get_riid_from_email(self, email):
        """
        Returns RIIDs found for a given list of email addresses.
        @param email: (list)
        @return: dict(str, str)
        """
        merge_endpoint = '%s/rest/api/v1.1/lists/%s/members' % (self.auth.endpoint,
                                                                self.list_name)

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

    def merge_list_members(self, fields, values, match1, match2):
        """
        Update members of specified existing profile list
        @param fields: (list) fields to be updated
        @param values: (list(list)) data corresponding to fields for each member
        @param match1: (str) column used to match to record in supplemental table
        @param match2: (str) same as above
        @return:
        """
        endpoint = '%s/rest/api/v1.1/lists/%s/members' % (self.auth.endpoint,
                                                          self.list_name)
        mp_member_data = {
            'recordData': {
                'fieldNames': fields,
                'records': values,
                'mapTemplateName': ''
            },

            'mergeRule': {
                'htmlValue': 'H',
                'optinValue': 'I',
                'textValue': 'T',
                'insertOnNoMatch': True,
                'updateOnMatch': 'REPLACE_ALL',
                'matchColumnName1': match1,
                'matchColumnName2': match2,
                'matchOperator': 'NONE',
                'optoutValue': 'O',
                'rejectRecordIfChannelEmpty': None,
                'defaultPermissionStatus': 'OPTIN'
            }
        }
        return requests.post(endpoint, json=mp_member_data,
                             headers=self.headers)

    def get_profile_data_from_riid(self, riid):
        """
        Retrieve entire data profile from Responsys via RIID
        @param riid: (int) Responsys unique identifier
        @return: (obj) response
        """
        endpoint = '%s/rest/api/v1.1/lists/%s/members/%s' % (
            self.auth.endpoint, self.list_name, str(riid)
        )
        fields = {'fs': 'all'}
        return requests.get(endpoint, params=fields, headers=self.headers)

    def delete_pet_record(self, riid, pet_name):
        """
        Deletes a member of a profile extension table based on RIID.
        @type riid: (int) Responsys unique identifier
        @param pet_name: (str) name of profile extension table in Responsys
        @return: (obj) response
        """
        endpoint = '%s/rest/api/v1.1/lists/%s/listExtensions/%s/members/%s' % (
            self.auth.endpoint, self.list_name, pet_name, riid)
        return requests.delete(endpoint, headers=self.headers)

    def get_pet_record(self, riid, pet_name):
        """
        Fetch a member of profile extension table based on RIID
        @param riid: (int)
        @param pet_name: (str) name of profile extension table to draw from
        @return: (obj) response
        """
        endpoint = '%s/rest/api/v1.1/lists/%s/listExtensions/%s/members/%s' % (
            self.auth.endpoint, self.list_name, pet_name, riid)
        return requests.get(endpoint, params={'fs': ['RIID_']},
                            headers=self.headers)

    def get_email_from_riid(self, riid, fields=('EMAIL_ADDRESS_',)):
        """
        Fetch email address corresponding to specified RIID.
        @param riid: (int) Responsys unique identifier
        @param fields: (tup(str)) fields to fetch
        @return: (str) requested email address if record exists
        """
        endpoint = '%s/rest/api/v1.1/lists/%s/members/%s' % (
            self.auth.endpoint, self.list_name, riid)
        response = requests.get(endpoint, params={'fs': fields},
                                headers=self.headers)
        if response.json().get('errorCode'):
            return response.json()
        if response.json().get('title') == 'Record not found':
            return response.json().get('title')
        return response.json()['recordData']['records'][0][0]

    def merge_update_pet_members(self, pet_name, fields, values):
        """
        Update specified fields for members of specified PET
        @param pet_name: (str) name of profile extension table
        @param fields: (list) fields to be updated
        @param values: (list(list)) data corresponding to fields
        @return: (obj) response
        """
        endpoint = '%s/rest/api/v1.1/lists/%s/listExtensions/%s/members' % (
            self.auth.endpoint, self.list_name, pet_name)
        mp_data = {
            'recordData': {
                'fieldNames': fields,
                'records': values,
                'mapTemplateName': None
            },
            'insertOnNoMatch': True,
            'updateOnMatch': 'REPLACE_ALL',
            'matchColumnName1': 'RIID',
            'matchColumnName2': None,
        }
        return requests.post(endpoint, json=mp_data, headers=self.headers)

    def send_email_campaign(self, campaign_name, recipients):
        """
        Sends specified email campaign via responsys
        @param campaign_name: (str) name of campaign
        @param recipients: (list) customers to send campaign to
        @return: (dict) success message
        """
        campaign_endpoint = '%s/rest/api/v1.1/campaigns/%s/email' % (self.auth.endpoint,
                                                                     campaign_name)

        # Responsys's recipient limit
        recipients = recipients[:999]

        response = requests.post(campaign_endpoint,
                                 json={'recipientData': recipients},
                                 headers=self.headers)
        if response.status_code != 200:
            return response.json()

        return {
            'rg_response': json.loads(response.content),
            'count': len(json.loads(response.content))
        }

    @staticmethod
    def get_riids_from_response(response):
        """
        Get riids and errors from a response.
        :param response:
        :return [], []: return riids and errors if exists.
        """
        content = json.loads(response.content)
        riids, errors = [], []

        if response.status_code == 200:
            records = content['recordData']['records']
            errors = [x[0] for x in records if not x[0].isdigit()]
            riids = [int(x[0]) for x in records if x[0].isdigit()]

        return riids, errors


class Extract(object):
    """
    Download zip files from Responsys FTP if files don't already exist in local
    extraction directory.
    """
    def __init__(self):
        super(Extract, self).__init__()
        self.dir = settings.RESPONSYS_EMAIL_PATH['dir']
        self.local_path = settings.RESPONSYS_EMAIL_PATH['local']

    def extract(self, patterns_list):
        """
        Extracts files matching patterns_list from responsys and returns a dict
        of pattern:file paths.

            Example usage to find opt_in and opt_out data:
                e = Extract()
                paths = e.extract(['54084_OPT_IN', '54084_OPT_OUT'])
        :type patterns_list: list()
        :param patterns_list: List of patterns to use as regex matches for
        determining which files to download from FTP.
        :return: Dict of downloaded file paths, keyed to values of patterns_list
        """
        file_folder = self.dir.split('/')[-2]
        r = ResponsysFtpConnect()
        # Get list of filepaths for files matching *_mode on Responsys FTP
        paths = {}
        for pattern in patterns_list:
            paths[pattern] = r.get_file_path(pattern, file_folder)
        # Remove files that have already been processed
        processed_files = cache.get('responsys:processed_ced_files_complete', '[]')
        for ptrn, filepaths in paths.iteritems():
            filepaths = [f for f in filepaths if f.split('/')[-1] not in processed_files]
            for fp in filepaths:
                r.download_file(fp, self.get_local_path(fp))
            filepaths = [self.get_local_path(p) for p in filepaths]
            paths[ptrn] = filepaths
        return paths

    def get_local_path(self, path):
        if not os.path.exists(self.local_path):
            os.makedirs(self.local_path)
            # create dir with full permission
            os.chmod(self.local_path, 0777)
        local_path = os.path.join(self.local_path, path.split('/')[-1])
        return local_path


class Load(object):
    def __init__(self):
        """
        Superclass of Load operations.  Subclasses should be called directly and
        should only use the load method.
        This ensures that data is logged properly after the load is complete.
        :return:
        """
        super(Load, self).__init__()
        self.local_path = settings.RESPONSYS_EMAIL_PATH['local']
        self.field_map = settings.RESPONSYS_CONTACT_EVENT_DATA_MAP

    def load(self, data_to_load):
        """
        :param data_to_load: list of file paths that will be loaded into the db.
        :type data_to_load: list()
        :return:
        """
        loaded_data = []
        for data in data_to_load:
            loaded_data.append(self.load_data(data))
        self.add_processed_files(loaded_data)

    def add_processed_files(self, loaded_data):
        """
        Saves filename of processed files in cache so we don't process them again.
        :type loaded_data: list()
        """
        loaded_data = [f.split('/')[-1] for f in loaded_data]
        processed_files = cache.get('responsys:processed_ced_files_complete', [])
        processed_files += loaded_data
        cache.set('responsys:processed_ced_files_complete', processed_files)

    def load_data(self, data_to_load):
        raise Exception('ERROR: _update_table should never be called from parent class')

    def read_file(self, local_path):
        """
        Accepts a path to a zip file, reads it
        and returns the rows
        :type local_path: str
        """
        rg_records = []
        with zipfile.ZipFile(self.get_local_path(local_path), 'r') as archive:
            for f in archive.namelist():
                data = StringIO.StringIO(archive.read(f))
                reader = csv.DictReader(data)
                for row in reader:
                    rg_records.append(row)
        return rg_records

    def get_local_path(self, path):
        if not os.path.exists(self.local_path):
            os.makedirs(self.local_path)
            # create dir with full permission
            os.chmod(self.local_path, 0777)
        local_path = os.path.join(self.local_path, path.split('/')[-1])
        return local_path


class OptInOutLoad(Load):
    """ Load sent data into db """
    def __init__(self):
        Load.__init__(self)

    def load_data(self, data_to_load):
        """
        Method that actually tries to load data into the db. If the load is
        successful, returns data_to_load.
        :param data_to_load: Path to the zip file from which we should read data
        :type data_to_load: str
        :return: data_to_load or None
        """
        data = self.read_file(data_to_load)
        for r in data:
            models.opted_out_emails.objects.add_or_update_email(
                r['RIID'],
                r['EVENT_TYPE_ID'],
                datetime.datetime.strptime(r['EVENT_CAPTURED_DT'], '%d-%b-%Y %H:%M:%S').replace(tzinfo=pytz.UTC),
                r['EMAIL']
            )
        # Store filenames from in_paths and out_paths in cache so we don't extract these files in the future.
        return data_to_load


class ResponsysUnbounceEvent(object):

    def make_request_payload(self, data):
        """
        Construct payload for Responsys API
        :param data:
        :return:
        """
        recipients = []
        for pkg in data:
            recip = {
                "recipient": {
                    "emailAddress": pkg[1],
                    "listName": {
                        "folderName": settings.RESPONSYS_LIST_FOLDER,
                        "objectName": settings.RESPONSYS_CONTACT_LIST,
                    },
                    "recipientId": pkg[0],
                    "emailFormat": "HTML_FORMAT"
                },
            }
            recipients.append(recip)
        return {
            "customEvent": {
                "eventNumberDataMapping": '',
                "eventDateDataMapping": '',
                "eventStringDataMapping": ''
            },
            "recipientData": recipients
        }

    def send(self, data):
        """
        Sends custom event to Responsys API
        :param data:
        :return:
        """
        auth = models.ResponsysCredential.objects.all()[0]
        headers = {'Authorization': auth.token}
        endpoint = '%s/rest/api/v1.1/events/%s' % (auth.endpoint,
                                                   settings.RESPONSYS_UNBOUNCE_EVENT)
        request_payload = self.make_request_payload(data)

        return requests.post(endpoint, json=request_payload, headers=headers)

    @staticmethod
    def get_riids_from_response(response):
        """
        Get riids and errors from a response.
        :param response:
        :return [], []: return riids and errors if exists.
        """
        content = json.loads(response.content)
        riids, errors = [], []

        if response.status_code == 200:
            errors = [x['errorMessage'] for x in content if not x['success']]
            riids = [x['recipientId'] for x in content if x['success']]

        return riids, errors
