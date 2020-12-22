import decimal
import json
import logging
import requests
import string
import urllib

from bs4 import BeautifulSoup
from datetime import datetime
from django.conf import settings

from .models import SenderLog
from mobovidata_dj.responsys.utils import ResponsysApi

logger = logging.getLogger(__name__)


def update_senderlog_success():
    """
    Updates lifecyle_senderlog table where no send success breakdown exists
    Parses response for total sends, successful sends, and failed sends
    @return: message describing if table was updated or if table is up to date
    """
    null_entries = SenderLog.objects.filter(total_sends=-1)

    for log in null_entries:
        try:
            res = eval(log.response)
            log.total_sends = len(res)
            log.successful_sends = len([line for line in res if line.get('success', '')])
            log.failed_sends = len([line for line in res if not line.get('success', '')])
            log.save()
        except AttributeError:
            # Evaluation of this log's response returns a dict containing error messages
            # In this situation, there were no sends and thus we log zeroes
            log.total_sends = log.successful_sends = log.failed_sends = 0
            log.save()

    if not null_entries:
        return 'No null entries. Table is up to date.'
    else:
        return 'Table updated.'


def make_responsys_request_payload(data):
    """
    Transforms list of order data dicitonaries into format suitable for responsys.
    @type data: list(dict)
    @rtype: tuple(dict, dict)
    @return: Request payload for Responsys API call, order_id-keyed dictionary
    with information for OrderConfirmationSendLog table.
    """
    product_attributes = {'products': data[0]['products'][0].keys()}
    recipients = []
    orders = data
    for d in orders:
        if d.get('includes_strands', '') == 'yes':
            product_attributes['strands_products'] = d['strands_products'][0].keys()

    email_to_riids = ResponsysApi().get_riid_from_email([o.get('customer_email', '') for o in orders])
    if settings.DEBUG:
        email_to_riids.update(ResponsysApi().get_riid_from_email(settings.RESPONSYS_EMAIL))
    for order in orders:
        if settings.DEBUG:
            products = order.get('products')
        opt_data = []
        opt_strands_products_data = []
        opt_data.append({'name': 'product_attributes',
                         'value': ';;-;;'.join(map(str, product_attributes['products']))})
        if order.get('includes_strands', '') == 'yes':
            opt_data.append({'name': 'strands_product_attributes',
                             'value': ';;-;;'.join(map(str, product_attributes['strands_products']))})
        customer_email = order.get('customer_email', '')
        if not customer_email:
            continue
        opt_data.append({'name': 'riid', 'value': email_to_riids.get(customer_email)})
        for k, v in order.items():
            if k == 'products':
                # List of unique vendors
                ds_vendors = list(set([abb_sku(vendor) for vendor in [
                                       s.get('sku', '') for s in v if s.get('sku').startswith('DS-')]]))
                # Buckets for dropship and non-dropship items
                mp_ds_products = {s: [] for s in ds_vendors}
                mp_ds_products['NON_DS'] = []

                for product in v:
                    # Organize dropship and non-dropship items
                    psku = abb_sku(product['sku'])
                    if psku in mp_ds_products:
                        mp_ds_products[psku].append(product)
                    else:
                        mp_ds_products['NON_DS'].append(product)

                # Product attributes concatenation
                all_items = [[';-;'.join(map(str, normalize_data_type(each.values()))) for each in products]
                             for sku, products in mp_ds_products.iteritems()]
                # Product concatenation
                all_products = [';;-;;'.join(items) for items in all_items]
                # Dropship / Non-dropship concatenation
                opt_products_data = ';;;-;;;'.join(all_products)

                opt_data.append({'name': 'products', 'value': opt_products_data})
            elif k == 'strands_products':
                for product in v:
                    # self.strands_product_attributes = k['strands_products'][0].keys()
                    opt_products = ';-;'.join(map(str, [
                            normalize_data_type(product.get(p_k))
                            for p_k in product_attributes['strands_products']]))
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
                    opt_data.append({'name': replacement % k.split('_')[0].upper(), 'value': v.get(original)})
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


def normalize_data_type(data_type):
    if isinstance(data_type, decimal.Decimal):
        data_type = '%s' % round(data_type, 2)
    elif isinstance(data_type, datetime):
        data_type = data_type.isoformat()
    try:
        normalized = unicode(data_type, "utf-8")
    except TypeError:
        normalized = data_type
    return normalized


def abb_sku(sku):
    """
    Converts full sku (A-B-C-D-E) to format A-B
    @param sku: (str) SKU to be abbreviated
    @return (str) SKU abbreviated as described above
    """
    return '-'.join(sku.split('-')[:2])


def get_strands_products(strands_id, amount=6):
    """
    Process customer's strands_id and recommend items
    @param strands_id: (unicode str) customer's strands ID
    @param amount: (int) number of products to recommend
    @return: (list) strands product recommendations
    """
    # Data sent to Strands
    params = {
        'apid': settings.STRANDS_APID,
        'tpl': 'conf_3',
        'format': 'json',
        'user': strands_id,
        'amount': amount,
    }
    # Call Strands, load and return product recommendations
    response = requests.get(settings.STRANDS_ENDPOINT, params=params)
    strands_products = []
    if response.status_code == 200:
        results = json.loads(response.content)
        for r in results['result']['recommendations']:
            product = r['metadata']
            if 'http' in product.get('picture', ''):
                image = product.get('picture', '')
            else:
                image = 'https://%s' % product.get('picture', '')
            item = {
                'url_path': product.get('link', ''),
                'name': product.get('name', ''),
                'special_price': float(product.get('price', '')),
                'image': image,
                'price': float(product['properties'].get('cretail_price', [0])[0]),
            }
            try:
                item['save_percent'] = round((item['price'] - item['special_price']) / item['price'], 4) * 100
                item['save_dollars'] = float(round(item['price'] - item['special_price'], 0))
            except KeyError:
                item['save_percent'] = 0
                item['save_dollars'] = 0
                item['special_price'] = item['price']
            strands_products.append(item)

    return strands_products


def get_internal_search_products(query, amount=4):
    """
    Constructs search url from query and crawls for search results
    @param query: (str) Customer's search query
    @param amount: (int) Number of items from search results to return, default: 4
    @return: list of dictionaries of item data if results exist, empty list if not
    """
    if not len(query):
        return 'ERROR: No query specifed'

    filtered_query = filter(lambda x: x in string.printable, query)

    url = '%s%s' % (settings.MAGENTO_URL_PREFIXES.get(
        'search', 'https://www.cellularoutfitter.com/search/result?q='), filtered_query.replace(' ', '%20'))

    raw_html = urllib.urlopen(url).read()
    html = BeautifulSoup(raw_html)
    results = html.find(id="crosssell-products-list")

    if not results:
        return []

    top_four_items_info = []
    for each in results.find_all('li')[:amount]:
        item = {
            'url_path': 'http://www.cellularoutfitter.com%s' % each.a['href'],
            'name': '%s' % each.a['title'],
            'image': 'http://%s' % each.img['src'].replace('//', ''),
            'price': float(each.find_all(class_="price")[0].text.strip().replace('$', '')),
        }
        try:
            item['special_price'] = float(each.find_all(class_="price")[1].text.strip().replace('$', ''))
            item['save_percent'] = round((item['price'] - item['special_price']) / item['price'], 4) * 100
            item['save_dollars'] = float(round(item['price'] - item['special_price'], 2))
        except IndexError:
            item['special_price'] = item['price']
        except KeyError:
            item['save_percent'] = 0
            item['save_dollars'] = 0
            item['special_price'] = item['price']

        top_four_items_info.append(item)

    return top_four_items_info
