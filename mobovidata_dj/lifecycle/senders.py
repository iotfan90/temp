"""
    Contains methods for packaging data and sending to 3rd party APIs
"""
import decimal
import json
import requests

from mobovidata_dj.responsys.models import ResponsysCredential


class Responsys(object):
    def __init__(self, campaign, auth):
        if not auth:
            auth = ResponsysCredential.objects.all()[0]
        self.headers = {'Authorization': auth['token']}
        self.auth = auth
        self.endpoint = auth['endpoint'] + '/rest/api/v1.1/campaigns/' + campaign + '/email'
        self.list_folder = '!MageData'
        self.list_name = 'CONTACT_LIST'
        self.campaign_name = campaign
        self.num_products = []
        self.product_attributes = ['color',
                                   'added_from_category_id',
                                   'base_row_total',
                                   'is_in_stock',
                                   'qty',
                                   'product_sku',
                                   'product_id',
                                   'sku',
                                   'category_id',
                                   'name',
                                   'url',
                                   'base_row_total_incl_tax',
                                   'reviews_rating',
                                   'reviews',
                                   'product_full_id',
                                   'base_price',
                                   'images']

    def make_product_str(self, p):
        """ Accepts a dict of product attributes and returns a ;-; sep. string of those product attributes"""
        product = [p[a] for a in self.product_attributes if a != 'images']
        product.append(p['images'][0])
        return ';-;'.join(map(str, product))

    def make_request_payload(self, data_package):
        recipients = []
        for customer in data_package:
            opt_data = [].append({
                'name': 'product_attributes',
                'value': ';;-;;'.join(map(str, self.product_attributes))
            })
            customer_data = data_package[customer]
            for k in customer_data.keys():
                if k != 'riid' and k != 'products':
                    if isinstance(customer_data[k], decimal.Decimal):
                        customer_data[k] = str(customer_data[k])
                    opt_data.append({'name': k, 'value': customer_data[k]})
                if k == 'products':
                    """ Each product's data will be sep by ;;-;;
                        Attributes for each product will be sep by ;;_;;"""
                    products = customer_data[k]
                    self.num_products.append(len(products))

                    opt_data_products = [self.make_product_str(p) for p in products]
                    opt_data_products_s = ';;-;;'.join(opt_data_products)
                    opt_data.append({'name': 'products', 'value': opt_data_products_s})

            recip = {
                "recipient": {
                    "listName": {
                        "folderName": self.list_folder,
                        "objectName": self.list_name,
                    },
                    #                     "recipientId" : 274342105,
                    "recipientId": customer_data['riid'],
                    "emailFormat": "HTML_FORMAT"
                },
                "optionalData": opt_data
            }
            recipients.append(recip)
        return {"recipientData": recipients}

    def send(self, data):
        r = requests.post(self.endpoint, json=self.make_request_payload(data),
                          headers=self.headers)
        r_content = json.loads(r.content)
        return r_content

    def get_profile_data(self, riid):
        ep = self.auth['endpoint'] + "/rest/api/v1.1/lists/" + self.list_name + "/members/" + str(riid)
        fields = {'fs': 'all'}
        r = requests.get(ep, params=fields, headers=self.headers)
        return r
