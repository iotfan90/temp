# _author__ = 'Yuki'

import json
import logging
import requests

from config import settings

logger = logging.getLogger(__name__)


class HelpscoutConnect(object):
    '''
    A class call helpscout api
    '''
    def __init__(self):
        self.boxes = settings.HELPSCOUT_MAILBOXES
        self.endpoint = settings.HELPSCOUT_API['endpoint']
        self.api_key = settings.HELPSCOUT_API['api_key']

    def get_customer_conversation(self, customer_id):
        conversations = []
        for box in self.boxes:
            url = ('%s/v1/mailboxes/%s/customers/%s/conversations.json' %
                   (self.endpoint, box, customer_id))
            if settings.DEBUG:
                url = ('%s/v1/mailboxes/%s/customers/%s/conversations.json' %
                       (self.endpoint, box, '94466899'))
            response = requests.get(url, auth=(self.api_key, '1'))
            if response.status_code == 200:
                response_data = json.loads(response.content)
                items = response_data.get('items')
                for item in items:
                    subject = item.get('subject')
                    method = item.get('source').get('type')
                    owner = item.get('owner')
                    preview = item.get('preview')
                    conversation_info = {
                        'subject': subject,
                        'owner': owner,
                        'type': method,
                        'preview': preview
                    }
                    conversations.append(conversation_info)
            else:
                continue
        return conversations

    def get_customer_profile(self, email):
        url = '%s/v1/customers.json?email=%s' % (self.endpoint, email)
        response = requests.get(url, auth=(self.api_key, '1'))
        if response.status_code == 200:
            r_content = response.content
            return {
                'success': True,
                'content': r_content
            }
        return {
            'success': False
        }
