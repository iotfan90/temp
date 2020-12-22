import json
import requests

from django.conf import settings
from requests.auth import HTTPBasicAuth


class SlickText(object):
    def __init__(self,
                 endpoint=settings.SLICKTEXT['endpoint'],
                 user=settings.SLICKTEXT['user'],
                 pw=settings.SLICKTEXT['pw']):
        super(SlickText, self).__init__()
        self.endpoint = endpoint
        self.user = user
        self.pw = pw

    def get_textwords(self):
        """
        :type return: Dictionary of textwords
        """
        req = requests.get('%stextwords' % self.endpoint,
                           auth=HTTPBasicAuth(self.user, self.pw))
        if req.status_code == 200:
            return json.loads(req.content)
        else:
            return req

    def register_sms(self, number, textword):
        """
        Registers number to the textword list at slicktext using
        doubleoptin=TRUE
        :type number: int
        :type textword: int
        """
        params = {
            'action':'DOUBLEOPTIN',
            'number':number,
            'textword':textword
        }
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        req = requests.post(
            '%scontacts/%s' % (self.endpoint, params['number']),
            auth=HTTPBasicAuth(self.user, self.pw),
            data=params,
            headers=headers
        )

        return req
