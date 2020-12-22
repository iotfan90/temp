import json
import logging
import requests
import time

logger = logging.getLogger(__name__)


class ShopifyConnect(object):

    def __init__(self, store):
        super(ShopifyConnect, self).__init__()
        self.shop_url = "https://%s:%s@%s" % (
            store.api_key,
            store.password,
            store.api_url
        )

    def datetime_to_iso_8601(self, date_time):
        """
        Convert datetime object to string ISO 8601
        Format example: 2014-04-25T16:15:47-04:00
        :param time:
        :return: string
        """
        return date_time.replace(microsecond=0).isoformat()

    def generate_http_get_query_params(self, *args, **kwargs):
        """
        Generates a string with all parameters for a HTTP GET request to
        shopify API
        :param args:
        :param kwargs:
        :return: string
        """
        params = {'limit': 250}
        if kwargs.get('fields', False):
            params['fields'] = ','.join(kwargs.get('fields'))
        if kwargs.get('ids', False):
            params['ids'] = ','.join(kwargs.get('ids'))
        if kwargs.get('limit', False):
            params['limit'] = kwargs.get('limit')
        if kwargs.get('page', False):
            params['page'] = kwargs.get('page')
        if kwargs.get('created_at_min', False):
            t = kwargs.get('created_at_min')
            params['created_at_min'] = self.datetime_to_iso_8601(t)
        if kwargs.get('updated_at_min', False):
            t = kwargs.get('updated_at_min')
            params['updated_at_min'] = self.datetime_to_iso_8601(t)
        if kwargs.get('product_id', False):
            params['product_id'] = kwargs.get('product_id')
        if kwargs.get('status', False):
            params['status'] = kwargs.get('status')
        if kwargs.get('ids', False):
            params['ids'] = kwargs.get('ids')
        if kwargs.get('namespace', False):
            params['namespace'] = kwargs.get('namespace')
        if kwargs.get('key', False):
            params['key'] = kwargs.get('key')

        return params

    def get_products_total_quantity(self, *args, **kwargs):
        """
        Get the total quantity of products.
        """
        response = ''
        payload = self.generate_http_get_query_params(*args, **kwargs)
        try:
            url = '%s/admin/products/count.json' % self.shop_url
            resp = requests.get(url, params=payload)
            response = json.loads(resp.content)
        except Exception, ex:
            logger.exception('There was an error while calling shopify %s', ex)
        return response

    def get_products(self, *args, **kwargs):
        """
        Get a list of products. Optional param fields should be a list of field
        names.
        """
        response = ''
        payload = self.generate_http_get_query_params(*args, **kwargs)
        try:
            url = '%s/admin/products.json' % self.shop_url
            resp = requests.get(url, params=payload)
            response = json.loads(resp.content)
        except Exception, ex:
            logger.exception('There was an error while calling shopify %s', ex)
        return response

    def create_product(self, attributes, *args, **kwargs):
        """
        :type product_id: string
        :type attributes: {}
        """
        headers = {'Content-Type': 'application/json'}
        params = {'product': attributes}

        max_retry = 5
        for counter in xrange(max_retry):
            try:
                resp = requests.post('%s/admin/products.json' % self.shop_url,
                                     data=json.dumps(params), headers=headers)
                return resp.status_code, json.loads(resp.content)
            except OSError as ex:
                if counter == max_retry:
                    raise
            time.sleep(1)

    def update_product(self, product_id, attributes, *args, **kwargs):
        """
        :type product_id: string
        :type attributes: {}
        """
        headers = {'Content-Type': 'application/json'}
        params = {
            "product": {
                "id": product_id,
            }
        }
        params['product'].update(attributes)

        max_retry = 5
        for counter in xrange(max_retry):
            try:
                resp = requests.put('%s/admin/products/%s.json' % (
                    self.shop_url,
                    product_id
                ), data=json.dumps(params), headers=headers)
                return resp
            except OSError as ex:
                if counter == max_retry:
                    raise
            time.sleep(1)

    def delete_product(self, obj_id, *args, **kwargs):
        """
        :type obj_id: string
        """
        headers = {'Content-Type': 'application/json'}

        max_retry = 5
        for counter in xrange(max_retry):
            try:
                resp = requests.delete('%s/admin/products/%s.json' %
                                       (self.shop_url, obj_id),
                                       headers=headers)
                return resp.status_code, json.loads(resp.content)
            except OSError as ex:
                if counter == max_retry:
                    raise
            time.sleep(1)

    def get_pages_total_quantity(self, *args, **kwargs):
        """
        Get the total quantity of pages.
        """
        response = ''
        payload = self.generate_http_get_query_params(*args, **kwargs)
        try:
            url = '%s/admin/pages/count.json' % self.shop_url
            resp = requests.get(url, params=payload)
            response = json.loads(resp.content)
        except Exception, ex:
            logger.exception('There was an error while calling shopify %s', ex)
        return response

    def get_pages(self, *args, **kwargs):
        """
        Get a list of pages.
        Optional param fields should be a list of field names.
        """
        response = ''
        payload = self.generate_http_get_query_params(*args, **kwargs)
        try:
            url = '%s/admin/pages.json' % self.shop_url
            resp = requests.get(url, params=payload)
            response = json.loads(resp.content)
        except Exception, ex:
            logger.exception('There was an error while calling shopify %s', ex)
        return response

    def create_page(self, attributes, *args, **kwargs):
        """
        :type attributes: {}
        """
        headers = {'Content-Type': 'application/json'}
        params = {'page': {}}
        params['page'].update(attributes)

        max_retry = 5
        for counter in xrange(max_retry):
            try:
                resp = requests.post('%s/admin/pages.json' %
                                     self.shop_url, data=json.dumps(params),
                                     headers=headers)
                return resp.status_code, json.loads(resp.content)
            except OSError as ex:
                if counter == max_retry:
                    raise
            time.sleep(1)

    def delete_page(self, obj_id, *args, **kwargs):
        """
        :type obj_id: string
        """
        headers = {'Content-Type': 'application/json'}

        max_retry = 5
        for counter in xrange(max_retry):
            try:
                resp = requests.delete('%s/admin/pages/%s.json' %
                                       (self.shop_url, obj_id),
                                       headers=headers)
                return resp.status_code, json.loads(resp.content)
            except OSError as ex:
                if counter == max_retry:
                    raise
            time.sleep(1)

    def get_smart_colletions_total_quantity(self, *args, **kwargs):
        """
        Get the total quantity of smart collections.
        """
        response = ''
        payload = self.generate_http_get_query_params(*args, **kwargs)
        try:
            url = '%s/admin/smart_collections/count.json' % self.shop_url
            resp = requests.get(url, params=payload)
            response = json.loads(resp.content)
        except Exception, ex:
            logger.exception('There was an error while calling shopify %s', ex)
        return response

    def get_smart_collections(self, *args, **kwargs):
        """
        Get a list of smart collections.
        Optional param fields should be a list of field names.
        """
        response = ''
        payload = self.generate_http_get_query_params(*args, **kwargs)
        try:
            url = '%s/admin/smart_collections.json' % self.shop_url
            resp = requests.get(url, params=payload)
            response = json.loads(resp.content)
        except Exception, ex:
            logger.exception('There was an error while calling shopify %s', ex)
        return response

    def create_smart_collection(self, attributes, *args, **kwargs):
        """
        :type attributes: {}
        """
        headers = {'Content-Type': 'application/json'}
        params = {'smart_collection': {}}
        params['smart_collection'].update(attributes)

        max_retry = 5
        for counter in xrange(max_retry):
            try:
                resp = requests.post('%s/admin/smart_collections.json' %
                                     self.shop_url, data=json.dumps(params),
                                     headers=headers)
                return resp.status_code, json.loads(resp.content)
            except OSError as ex:
                if counter == max_retry:
                    raise
            time.sleep(1)

    def update_smart_collection(self, collection_id, attributes, *args, **kwargs):
        """
        :type collection_id: string
        :type attributes: {}
        """
        headers = {'Content-Type': 'application/json'}
        params = {'smart_collection': {
            'id': collection_id
        }}
        params['smart_collection'].update(attributes)

        max_retry = 5
        for counter in xrange(max_retry):
            try:
                resp = requests.put('%s/admin/smart_collections/%s.json' %
                                     (self.shop_url, collection_id),
                                     data=json.dumps(params), headers=headers)
                return resp.status_code, json.loads(resp.content)
            except OSError as ex:
                if counter == max_retry:
                    raise
            time.sleep(1)

    def delete_smart_collection(self, obj_id, *args, **kwargs):
        """
        :type obj_id: string
        """
        headers = {'Content-Type': 'application/json'}

        max_retry = 5
        for counter in xrange(max_retry):
            try:
                resp = requests.delete('%s/admin/smart_collections/%s.json' %
                                       (self.shop_url, obj_id),
                                       headers=headers)
                return resp.status_code, json.loads(resp.content)
            except OSError as ex:
                if counter == max_retry:
                    raise
            time.sleep(1)

    def get_discount_code(self, code, *args, **kwargs):
        """
        Get discount code details.
        """
        response = ''
        payload = {'code': code}
        try:
            url = '%s/admin/discount_codes/lookup.json' % self.shop_url
            resp = requests.get(url, params=payload, allow_redirects=False)
            if resp.status_code == 303:
                url = '%s%s.json' % (self.shop_url,
                                dict(resp.headers)['Location'].split('.com')[1])
                resp = requests.get(url)
                response = json.loads(resp.content)
        except Exception, ex:
            logger.exception('There was an error while calling shopify %s', ex)
        return response, resp.status_code

    def get_price_rule(self, price_rule_id, *args, **kwargs):
        """
        Get a price rule from shopify.
        names.
        """
        response = ''
        try:
            url = '%s/admin/price_rules/%s.json' % (self.shop_url,
                                                    price_rule_id)
            resp = requests.get(url)
            response = json.loads(resp.content)
        except Exception, ex:
            logger.exception('There was an error while calling shopify %s', ex)
        return response

    def get_themes(self, *args, **kwargs):
        """
        Get a list of shopify themes.
        """
        response = ''
        try:
            url = '%s/admin/themes.json' % self.shop_url
            resp = requests.get(url)
            response = json.loads(resp.content)
        except Exception, ex:
            logger.exception('There was an error while calling shopify %s', ex)
        return response

    def create_update_asset(self, theme_id, attributes, *args, **kwargs):
        """
        :type product_id: string
        :type attributes: {}
        """
        headers = {'Content-Type': 'application/json'}
        params = {'asset': {}}
        params['asset'].update(attributes)

        max_retry = 5
        for counter in xrange(max_retry):
            try:
                resp = requests.put('%s/admin/themes/%s/assets.json' %
                                     (self.shop_url, theme_id),
                                     data=json.dumps(params),
                                     headers=headers)
                resp = json.loads(resp.content)
                return resp
            except OSError as ex:
                if counter == max_retry:
                    raise
            time.sleep(1)

    def get_orders_total_quantity(self, *args, **kwargs):
        """
        Get the total quantity of orders.
        """
        response = ''
        payload = self.generate_http_get_query_params(*args, **kwargs)
        try:
            url = '%s/admin/orders/count.json' % self.shop_url
            resp = requests.get(url, params=payload)
            response = json.loads(resp.content)
        except Exception, ex:
            logger.exception('There was an error while calling shopify %s', ex)
        return response

    def get_orders(self, *args, **kwargs):
        """
        Get a list of orders. Optional param fields should be a list of field
        names.
        """
        response = ''
        payload = self.generate_http_get_query_params(*args, **kwargs)
        try:
            url = '%s/admin/orders.json' % self.shop_url
            resp = requests.get(url, params=payload)
            response = json.loads(resp.content)
        except Exception, ex:
            logger.exception('There was an error while calling shopify %s', ex)
        return response

    def get_webhooks(self, *args, **kwargs):
        """
        Get a list of webhooks. Optional param fields should be a list of field
        names.
        """
        response = ''
        payload = self.generate_http_get_query_params(*args, **kwargs)
        try:
            url = '%s/admin/webhooks.json' % self.shop_url
            resp = requests.get(url, params=payload)
            response = json.loads(resp.content)
        except Exception, ex:
            logger.exception('There was an error while calling shopify %s', ex)
        return response

    def create_webhook(self, attributes, *args, **kwargs):
        """
        :type attributes: {}
        """
        headers = {'Content-Type': 'application/json'}
        params = {'webhook': {}}
        params['webhook'].update(attributes)

        max_retry = 5
        for counter in xrange(max_retry):
            try:
                resp = requests.post('%s/admin/webhooks.json' % self.shop_url,
                                    data=json.dumps(params), headers=headers)
                return resp.status_code, json.loads(resp.content)
            except OSError as ex:
                if counter == max_retry:
                    raise
            time.sleep(1)

    def delete_webhook(self, webhook_id, *args, **kwargs):
        """
        :type product_id: string
        :type attributes: {}
        """
        headers = {'Content-Type': 'application/json'}

        max_retry = 5
        for counter in xrange(max_retry):
            try:
                resp = requests.delete('%s/admin/webhooks/%s.json' %
                                       (self.shop_url, webhook_id),
                                       headers=headers)
                return resp.status_code, json.loads(resp.content)
            except OSError as ex:
                if counter == max_retry:
                    raise
            time.sleep(1)

    def get_products_metafields_total_quantity(self, id, *args, **kwargs):
        response = ''
        payload = self.generate_http_get_query_params(*args, **kwargs)
        try:
            url = '{}/admin/products/{}/metafields/count.json'.format(self.shop_url, id)
            resp = requests.get(url, params=payload)
            response = json.loads(resp.content)
        except Exception, ex:
            logger.exception('There was an error while calling shopify %s', ex)
        return response

    def get_smart_collections_metafields_total_quantity(self, id, *args, **kwargs):
        response = ''
        payload = self.generate_http_get_query_params(*args, **kwargs)
        try:
            url = '{}/admin/collections/{}/metafields/count.json'.format(self.shop_url, id)
            resp = requests.get(url, params=payload)
            response = json.loads(resp.content)
        except Exception, ex:
            logger.exception('There was an error while calling shopify %s', ex)
        return response

    def get_metafields(self, type_of_resource, id, *args, **kwargs):
        response = ''
        payload = self.generate_http_get_query_params(*args, **kwargs)
        try:
            url = '{}/admin/{}/{}/metafields.json'.format(self.shop_url,
                                                          type_of_resource, id)
            resp = requests.get(url, params=payload)
            response = json.loads(resp.content)
        except Exception, ex:
            logger.exception('There was an error while calling shopify %s', ex)
        return response

    def create_metafield(self, type_of_resource, id, attributes, *args, **kwargs):
        """
        :type attributes: {}
        """
        headers = {'Content-Type': 'application/json'}
        params = {'metafield': {}}
        params['metafield'].update(attributes)

        max_retry = 5
        for counter in xrange(max_retry):
            try:
                resp = requests.post('{}/admin/{}/{}/metafields.json'.format(self.shop_url,
                                                                             type_of_resource,
                                                                             id),
                                     data=json.dumps(params), headers=headers)
                return resp.status_code, json.loads(resp.content)
            except OSError as ex:
                if counter == max_retry:
                    raise
            time.sleep(1)

    def delete_metafield(self, id, *args, **kwargs):
        headers = {'Content-Type': 'application/json'}

        max_retry = 5
        for counter in xrange(max_retry):
            try:
                resp = requests.delete('%s/admin/metafields/%s.json' %
                                       (self.shop_url, id), headers=headers)
                return resp.status_code, json.loads(resp.content)
            except OSError as ex:
                if counter == max_retry:
                    raise
            time.sleep(1)
