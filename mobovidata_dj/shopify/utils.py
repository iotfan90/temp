import json
import logging
import requests
import time

from collections import OrderedDict
from django.conf import settings
from django.db import models

from .connect import ShopifyConnect
from .models import (Brand, Customer, MetadataCollection,
                     MetadataCollectionAttribute, Model, Order, OrderLine,
                     Product, ProductImage, ProductOption, ProductVariant,
                     SmartCollection)

logger = logging.getLogger(__name__)


class ShopifyMVD(object):

    def __init__(self):
        super(ShopifyMVD, self).__init__()
        self.shop_url = "https://%s:%s@mobovida.myshopify.com/admin" % (
            settings.SHOPIFY['API_KEY'],
            settings.SHOPIFY['PASSWORD']
        )

    def get_product_variant(self, product_id):
        """
        Get a list of product variants
        """
        req = requests.get('%s/products/%s/variants.json' % (self.shop_url,
                                                             product_id))
        resp = json.loads(req.content)
        return resp

    def get_products(self, *args, **kwargs):
        """
        Get a list of products. Optional param fields should be a list of field
        names.
        """
        fields = ''
        page = ''
        limit=250
        if kwargs.get('fields', False):
            fields = ','.join(kwargs.get('fields'))
            fields = '&fields=%s' % fields
        if kwargs.get('limit', False):
            limit = kwargs.get('limit')
        if kwargs.get('page', False):
            page = '&page=%s' % kwargs.get('page')
        params = '?limit=%s%s%s' % (limit, fields, page)
        req = requests.get('%s/products.json%s' % (self.shop_url, params))
        resp = json.loads(req.content)
        return resp

    def update_inventory(self, variant_id, qty, *args, **kwargs):
        """
        :type variant_id: int
        :type qty: int
        """
        headers = {'Content-Type': 'application/json'}
        params = {
                  "variant": {
                    "id": variant_id,
                    "inventory_quantity": qty,
                    "inventory_management": "shopify"
                  }
                }

        max_retry = 5
        for _ in xrange(max_retry):
            try:
                resp = requests.put('%s/variants/%s.json' % (
                    self.shop_url,
                    variant_id
                ), data=json.dumps(params), headers=headers)
                return resp
            except OSError as ex:
                logger.exception('There is an error while calling shopify %s',
                                 ex)
            time.sleep(10)
        raise OSError('Reach max try')


def generate_brand_model_js_file():
    # Get brand name collections
    brand_name_collections = OrderedDict()
    query = (Model.objects
             .all()
             .values('brand__name', 'collection_handle')
             .order_by('brand__name', 'collection_handle'))
    for result in query:
        brand_name_collections.setdefault(result['brand__name'].lower(),
                                          []).append(
            result['collection_handle'])

    # Get brand name map
    brand_name_map = OrderedDict()
    query = (Model.objects
             .all()
             .values('brand__name', 'model', 'collection_handle')
             .order_by('brand__name', 'model'))
    for result in query:
        brand_name_map.setdefault(result['brand__name'], OrderedDict())[
            result['model']] = result['collection_handle']

    # Get top models
    query = (Model.objects
             .filter(top_model=True)
             .values('brand__name', 'model', 'collection_handle')
             .order_by('brand__name', 'model'))
    for result in query:
        brand_name_map[result['brand__name']].setdefault('topModels',
                                                         OrderedDict())[
            result['model']] = result['collection_handle']

    js = ('window.brand_name_collections = %s;window.brand_name_map = %s;' %
          (json.dumps(brand_name_collections), json.dumps(brand_name_map)))
    return js


def generate_brand_model_images_js_file():
    brands = {}
    for brand in Brand.objects.all():
        models = {}
        for model in brand.model_set.all():
            img_url = '{}{}.jpg'.format(settings.SHOPIFY_CDN_FILES_URL,
                                        model.collection_handle)
            models[model.collection_handle] = model.shopify_image or img_url
        brands[brand.name] = models

    js = 'var brandModelImages = {};'.format(json.dumps(brands))
    return js


def generate_collection_attrs_from_model(collection, model):
    attributes = {}
    if model.image:
        absolute_url = '%s%s' % (settings.DOMAIN_URL, model.image.url)
        attributes['image'] = {'src': absolute_url}
    rules = collection.get_rules_dict_format()
    attributes['rules'] = rules
    update_collection_rules(model, attributes)

    if model.collection_description:
        attributes['body_html'] = model.collection_description
    return attributes


def update_collection_rules(model, attributes):
    collection_handle = {
        'column': 'tag',
        'relation': 'equals',
        'condition': 'bm--{}'.format(model.collection_handle)
        }
    adaptor_type = {
            'column': 'tag',
            'relation': 'equals',
            'condition': 'cw--{}'.format(model.adaptor_type)
        }
    device_type = {
            'column': 'tag',
            'relation': 'equals',
            'condition': 'cw--{}'.format(model.device_type)
        }
    headset_type = {
            'column': 'tag',
            'relation': 'equals',
            'condition': 'cw--{}'.format(model.headset_type)
        }
    pouch_size = {
            'column': 'tag',
            'relation': 'equals',
            'condition': 'cw--{}'.format(model.pouch_size)
        }
    universal_products = {
            'column': 'tag',
            'relation': 'equals',
            'condition': 'universal-products'
        }

    if model.collection_handle and collection_handle not in attributes['rules']:
        attributes['rules'].append(collection_handle)
    if model.adaptor_type and adaptor_type not in attributes['rules']:
        attributes['rules'].append(adaptor_type)
    if model.device_type and device_type not in attributes['rules']:
        attributes['rules'].append(device_type)
    if model.headset_type and headset_type not in attributes['rules']:
        attributes['rules'].append(headset_type)
    if model.pouch_size and pouch_size not in attributes['rules']:
        attributes['rules'].append(pouch_size)
    if model.device_type == Model.D_T_CELL_PHONE and universal_products not in attributes['rules']:
        attributes['rules'].append(universal_products)


# Remove duplicates scripts

def remove_duplicates_by_model(store, django_model, unique_fields):
    duplicates = django_model.objects.filter(store=store).values(*unique_fields).order_by().annotate(
        max_id=models.Max('id'), count_id=models.Count('id')).filter(
        count_id__gt=1)

    for duplicate in duplicates:
        (django_model.objects.filter(store=store).filter(**{x: duplicate[x] for x in unique_fields})
         .exclude(id=duplicate['max_id'])
         .delete())


def remove_duplicates_by_order_one_level(store, django_model, unique_fields):
    duplicates = django_model.objects.filter(order__store=store).values(*unique_fields).order_by().annotate(
        max_id=models.Max('id'), count_id=models.Count('id')).filter(
        count_id__gt=1)

    for duplicate in duplicates:
        (django_model.objects.filter(order__store=store).filter(**{x: duplicate[x] for x in unique_fields})
         .exclude(id=duplicate['max_id'])
         .delete())


def remove_duplicates_by_product_one_level(store, django_model, unique_fields):
    duplicates = django_model.objects.filter(product__store=store).values(*unique_fields).order_by().annotate(
        max_id=models.Max('id'), count_id=models.Count('id')).filter(
        count_id__gt=1)

    for duplicate in duplicates:
        (django_model.objects.filter(product__store=store).filter(**{x: duplicate[x] for x in unique_fields})
         .exclude(id=duplicate['max_id'])
         .delete())


def remove_duplicates_by_store(store):
    # Orders
    remove_duplicates_by_model(store, Customer, ['customer_id', ])
    remove_duplicates_by_order_one_level(store, OrderLine, ['line_id', ])
    remove_duplicates_by_model(store, Order, ['order_id', ])
    # Products
    remove_duplicates_by_product_one_level(store, ProductImage, ['image_id', ])
    remove_duplicates_by_product_one_level(store, ProductOption, ['option_id', ])
    remove_duplicates_by_product_one_level(store, ProductVariant, ['variant_id', ])
    remove_duplicates_by_model(store, Product, ['product_id', ])
    # Smart collections
    remove_duplicates_by_model(store, SmartCollection, ['collection_id', ])


def update_collection_metafield(store, c_name, key, value, m_type, namespace):
    try:
        m = MetadataCollectionAttribute.objects.get(
            collection_metadata__store=store,
            collection_metadata__name=c_name,
            key=key,
            m_type=m_type)
        if m.value != value:
            m.value = value
            m.status = MetadataCollectionAttribute.UNSYNCED
            m.save()
    except MetadataCollectionAttribute.DoesNotExist:
        m_c_obj, created = MetadataCollection.objects.get_or_create(store=store,
                                                                    name=c_name)

        m = MetadataCollectionAttribute(collection_metadata=m_c_obj,
                                        key=key,
                                        value=value,
                                        m_type=m_type,
                                        namespace=namespace)
        m.save()


def check_mandatory_csv_file_columns_product_association(columns):
    mandatory_file_columns = ['sku', 'color', 'associated_products']
    columns = set(mandatory_file_columns).difference(columns)
    return columns


def check_mandatory_csv_file_columns_product_create(columns):
    mandatory_file_columns = ['mpid', 'Handle', 'Title', 'Body (HTML)',
                              'Vendor', 'Type', 'Tags', 'Published',
                              'Option1 Name', 'Option1 Value', 'Option2 Name',
                              'Option2 Value', 'Option3 Name', 'Option3 Value',
                              'Variant SKU', 'Variant Grams',
                              'Variant Inventory Tracker',
                              'Variant Inventory Qty',
                              'Variant Inventory Policy',
                              'Variant Fulfillment Service', 'Variant Price',
                              'Variant Compare At Price',
                              'Variant Requires Shipping', 'Variant Taxable',
                              'Variant Barcode', 'Image Src', 'Image Position',
                              'Image Alt Text', 'Gift Card', 'SEO Title',
                              'SEO Description',
                              'Google Shopping / Google Product Category',
                              'Google Shopping / Gender',
                              'Google Shopping / Age Group',
                              'Google Shopping / MPN',
                              'Google Shopping / AdWords Grouping',
                              'Google Shopping / AdWords Labels',
                              'Google Shopping / Condition',
                              'Google Shopping / Custom Product',
                              'Google Shopping / Custom Label 0',
                              'Google Shopping / Custom Label 1',
                              'Google Shopping / Custom Label 2',
                              'Google Shopping / Custom Label 3',
                              'Google Shopping / Custom Label 4',
                              'Variant Image', 'Variant Weight Unit']
    columns = set(mandatory_file_columns).difference(columns)
    return columns


def check_mandatory_csv_file_columns_model_update(columns):
    mandatory_file_columns = ['brand', 'model', 'collection_handle',
                              'top_model', 'image', 'shopify_image',
                              'sku_add_on', 'categories', 'height', 'width',
                              'depth', 'bluetooth', 'headset_type',
                              'adaptor_type', 'wireless_charger', 'device_type',
                              'pouch_size', 'bluetooth_version',
                              'removable_battery', 'collection_description']
    columns = set(mandatory_file_columns).difference(columns)
    return columns


def check_csv_has_variant(columns):
    variant_columns = ['Variant Grams', 'Variant Inventory Tracker',
                       'Variant Inventory Qty', 'Variant Inventory Policy',
                       'Variant Fulfillment Service', 'Variant Price',
                       'Variant Compare At Price',
                       'Variant Requires Shipping',
                       'Variant Taxable', 'Variant Barcode',
                       'Variant Image',
                       'Variant Weight Unit']
    return set(variant_columns).intersection(columns)


def check_csv_has_img(columns):
    variant_columns = ['Image Src', 'Image Position']
    return set(variant_columns).intersection(columns)


def check_mandatory_csv_file_columns_product_update(columns):
    mandatory_file_columns = ['Handle', ]
    variant_mandatory_file_columns = ['Variant SKU', ]
    img_mandatory_file_columns = ['Image Src', 'Image Position']
    if check_csv_has_variant(columns):
        mandatory_file_columns.extend(variant_mandatory_file_columns)
    if check_csv_has_img(columns):
        mandatory_file_columns.extend(img_mandatory_file_columns)
    columns = set(mandatory_file_columns).difference(columns)
    return columns


def check_mandatory_fields(fields, mandatory_fields):
    return [k for k, v in fields.items() if k in mandatory_fields and not v]


def get_all_product_metafields(product):
    shopify = ShopifyConnect(product.store)
    qty = shopify.get_products_metafields_total_quantity(product.product_id)['count']
    total_pages = -(-qty // 250)
    metafields = []

    for page in xrange(1, total_pages + 1):
        response = shopify.get_metafields('products', product.product_id,
                                          page=page)
        metafields.extend(response['metafields'])
    return metafields


def get_currency_exchange_rate(to_currency_code, from_currency_code='USD'):
    url = 'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={}&to_currency={}&apikey={}'
    r = requests.get(url.format(from_currency_code,
                                to_currency_code,
                                settings.ALPHAVANTAGE_API_KEY))
    if r.status_code == 200:
        data = json.loads(r.content)
        rate = float(data['Realtime Currency Exchange Rate']['5. Exchange Rate'])
        return rate
    else:
        return None
