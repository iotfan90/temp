import dateutil.parser
import math
import re
import string

from bs4 import BeautifulSoup
from datetime import timedelta
from django.utils import timezone

from .models import Model, Product, Store
from .utils import get_currency_exchange_rate

from mobovidata_dj.feeds.tasks import get_product_group_by_sku


# ################### CO ###################

def package_customer_co(customer, models):
    rows = []
    row = {}
    row['record_id'] = customer.customer_id
    row['email'] = customer.email
    row['account_created_on'] = customer.created_at.strftime('%Y-%m-%d')
    row['full_name'] = '{} {}'.format(customer.first_name and customer.first_name.encode("utf-8") or None,
                                      customer.last_name and customer.last_name.encode("utf-8") or None)
    b = set()
    m = set()
    os = set()
    for order in customer.order_set.all():
        for line in order.orderline_set.all():
            handle = line.collection_handle
            if handle and handle in models:
                b.add(models[handle].brand.name)
                m.add(models[handle].model)
    if any('apple' in s.lower() for s in b):
        os.add('iOS')
    if any('apple' not in s.lower() for s in b):
        os.add('Android')
    row['brand'] = b and ','.join(b) or None
    row['model'] = m and ','.join(m) or None
    row['os'] = os and ','.join(os) or None
    rows.append(row)
    return rows


def package_product_co_master(product, variant, collection, image,
                              master_products, master_categories, color):
    tags = product.producttag_set.all().values_list('name', flat=True)

    rows = []
    product_row = {}
    
    try:
        m_category = master_categories[collection]
    except KeyError:
        return rows
    try:
        mpid = master_products[variant.sku]
    except KeyError:
        mpid = None
    product_row['barcode'] = variant.barcode
    product_row['brand'] = m_category.brand_name
    product_row['category_name'] = m_category.category_name
    product_row['collection'] = collection
    product_row['color'] = color
    product_row['condition'] = 'new'
    product_row['custom_label_0'] = get_custom_label(tags, 'feed-cl0-')
    product_row['custom_label_1'] = get_custom_label(tags, 'feed-cl1-')
    product_row['custom_label_2'] = get_custom_label(tags, 'feed-cl2-')
    product_row['custom_label_3'] = get_custom_label(tags, 'feed-cl3-')
    product_row['custom_label_4'] = get_custom_label(tags, 'feed-cl4-')
    product_row['description'] = product.body_html and get_description(
        product.body_html)
    product_row['google_product_category'] = google_product_category(
        product.product_type)
    product_row['image_url'] = image.src
    product_row['in_stock'] = True if variant.inventory_quantity > 0 else False
    product_row['inventory_quantity'] = variant.inventory_quantity
    product_row['mcid'] = m_category.mcid
    product_row['model'] = m_category.model_name
    product_row['mpid'] = mpid
    product_row['price'] = variant.price
    product_row['product_handle'] = product.handle
    product_row['product_title'] = product.title.encode('utf8')
    product_row['product_type'] = product.product_type
    product_row['published_at'] = variant.product.published_at
    product_row['retail_price'] = variant.compare_at_price
    product_row['shop_url'] = product.store.shop_url
    product_row['sku'] = variant.sku
    product_row['variant_id'] = variant.variant_id
    product_row['weight'] = variant.weight
    product_row['weight_unit'] = variant.weight_unit
    product_row['product_id'] = product.product_id

    rows.append(product_row)
    return rows


def package_product_co_bing(df):
    headers = {
        'Availability': 'Availability',
        'barcode': 'UPC',
        'Bingads_label': 'Bingads_label',
        'BingCategory': 'BingCategory',
        'brand': 'Brand',
        'category_name': 'MerchantCategory',
        'custom_label_0': 'Ruben',
        'custom_label_1': 'Custom Label 1',
        'custom_label_2': 'Custom Label 2',
        'custom_label_3': 'Custom Label 3',
        'custom_label_4': 'Custom Label 4',
        'Description': 'Description',
        'google_product_category': 'google_product_category',
        'image_url': 'ImageURL',
        'ISBN': 'ISBN',
        'MerchantProductID': 'MerchantProductID',
        'model': 'Bingads_grouping',
        'price': 'Price',
        'Product_type': 'Product_type',
        'ProductURL': 'ProductURL',
        'Shipping': 'Shipping',
        'ShippingWeight': 'ShippingWeight',
        'SKU': 'SKU',
        'Title': 'Title',
    }
    df['MerchantProductID'] = df.apply(lambda row: f_full_product_id(row), axis=1)
    df['Title'] = df.apply(lambda row: f_full_product_title(row, 150), axis=1)
    df['ISBN'] = 'ruben'
    df['SKU'] = df.apply(lambda row: f_full_product_id(row), axis=1)
    df['ProductURL'] = df.apply(lambda row: f_full_link(row, '&utm_source=bing&utm_campaign=PLA&utm_medium=cpc&utm_term={}'.format(f_full_product_id(row))), axis=1)
    df['Product_type'] = df.apply(lambda row: f_full_product_type(row), axis=1)
    df['Availability'] = df.apply(lambda row: f_in_stock_label(row).title(), axis=1)
    df['Description'] = df.apply(lambda row: f_description(row), axis=1)
    df['Shipping'] = 5.99
    df['ShippingWeight'] = df.apply(lambda row: f_full_shipping_weight(row), axis=1)
    df['Bingads_label'] = df['category_name']
    df['google_product_category'] = df['google_product_category']
    df['BingCategory'] = df['google_product_category']
    df = df[[k for k in headers.keys()]]
    df = df.rename(columns=headers)
    return df


def package_product_co_connexity_shopzilla(df):
    headers = {
        'availability': 'availability',
        'barcode': 'gtin',
        'brand': 'brand',
        'color': 'color',
        'condition': 'condition',
        'custom_label_0': 'Ruben',
        'custom_label_1': 'Custom Label 1',
        'custom_label_2': 'Custom Label 2',
        'custom_label_3': 'Custom Label 3',
        'custom_label_4': 'Custom Label 4',
        'description': 'description',
        'GoogleAffiliateNetworkProductURL': 'GoogleAffiliateNetworkProductURL',
        'google_product_category': 'google_product_category',
        'unique id': 'unique id',
        'identifier_exists': 'identifier_exists',
        'image_url': 'image url',
        'inventory_quantity': 'quantity_in_stock',
        'legacy_id': 'legacy_id',
        'product url': 'product url',
        'model': 'adwords_grouping',
        'payment_accepted': 'payment_accepted',
        'price': 'current price',
        'category': 'category',
        'product_type': 'product_type',
        'promotion_id': 'promotion_id',
        'retail_price': 'original price',
        'ship weight': 'ship weight',
        'sku': 'sku',
        'title': 'title',
    }
    df['availability'] = df.apply(lambda row: f_in_stock_label(row), axis=1)
    df['category'] = df['product_type']
    df['description'] = df.apply(lambda row: f_description(row), axis=1)
    df['GoogleAffiliateNetworkProductURL'] = df.apply(lambda row: f_full_link(row), axis=1)
    df['unique id'] = df.apply(lambda row: f_full_product_id(row), axis=1)
    df['identifier_exists'] = df.apply(lambda row: 'yes' if row['barcode'] else 'no', axis=1)
    df['legacy_id'] = 'ruben'
    df['product url'] = df.apply(lambda row: f_full_link(row, '&utm_source=shopzilla&utm_medium=CSE&utm_term={}&utm_campaign='.format(f_full_product_id(row))), axis=1)
    df['payment_accepted'] = 'Visa,MasterCard,American Express,Discover'
    df['current price'] = df.apply(lambda row: f_price_iso(row), axis=1)
    df['product_type'] = df.apply(lambda row: f_full_product_type(row), axis=1)
    df['promotion_id'] = 'ruben'
    df['original price'] = df.apply(lambda row: f_compare_at_price_iso(row), axis=1)
    df['ship weight'] = df.apply(lambda row: f_full_shipping_weight(row), axis=1)
    df['title'] = df.apply(lambda row: f_full_product_title(row, 150), axis=1)
    df = df[[k for k in headers.keys()]]
    df = df.rename(columns=headers)
    return df


def package_product_co_dy(df):
    headers = {
        'brand': 'brand',
        'categories': 'categories',
        'color': 'color',
        'group_id': 'group_id',
        'image_url': 'image_url',
        'in_stock': 'in_stock',
        'model': 'model',
        'name': 'name',
        'product_type': 'product_type',
        'price': 'price',
        'retail_price': 'retail_price',
        'sku': 'skuid',
        'sku2': 'sku',
        'url': 'url',
        'reviews': 'ruben'
    }
    df['categories'] = df['product_type']
    df['group_id'] = df.apply(lambda row: f_product_id(row), axis=1)
    df['name'] = df.apply(lambda row: f_full_product_title(row), axis=1)
    df['sku2'] = df.apply(lambda row: f_full_product_id(row), axis=1)
    df['url'] = df.apply(lambda row: f_full_link(row), axis=1)
    df['reviews'] = ruben
    df = df[[k for k in headers.keys()]]
    df = df.rename(columns=headers)
    return df


def package_product_co_ebay(df):
    headers = {
        'barcode': 'UPC',
        'brand': 'Manufacturer',
        'color': 'Color',
        'condition': 'Condition',
        'image_url': 'Image URL',
        'price': 'Current Price',
        'Product Description': 'Product Description',
        'Product Name': 'Product Name',
        'Product URL': 'Product URL',
        'Category': 'Category',
        'sku': 'MPN/ISBN',
        'Stock Availability': 'Stock Availability',
        'Unique Merchant SKU': 'ruben',
    }
    df['Category'] = df.apply(lambda row: f_full_product_type(row), axis=1)
    df['Product Description'] = df.apply(lambda row: f_description(row), axis=1)
    df['Product Name'] = df.apply(lambda row: f_full_product_title(row, 150), axis=1)
    df['Product URL'] = df.apply(lambda row: f_full_link(row, '&utm_source=EbayShopping&utm_medium=CSE'), axis=1)
    df['Stock Availability'] = df.apply(lambda row: f_in_stock_label(row).title(), axis=1)
    df['Unique Merchant SKU'] = df.apply(lambda row: f_full_product_id(row), axis=1)
    df = df[[k for k in headers.keys()]]
    df = df.rename(columns=headers)
    return df


def package_product_co_fb(df):
    headers = {
        'availability': 'availability',
        'barcode': 'mpn',
        'brand': 'brand',
        'color': 'color',
        'condition': 'condition',
        'Custom Label 2': 'Custom Label 2',
        'Custom Label 3': 'Custom Label 3',
        'description': 'description',
        'google_product_category': 'google_product_category',
        'id': 'id',
        'image_url': 'image_link',
        'inventory_quantity': 'inventory',
        'link': 'link',
        'model': 'brand',
        'price': 'price',
        'product_type': 'product_type',
        'sale_price': 'sale_price',
        'title': 'ruben',
    }
    cad_rate = get_currency_exchange_rate('CAD')
    rupee_rate = get_currency_exchange_rate('INR')

    df['Custom Label 2'] = df.apply(lambda row: f_price_currency_exchange_rate(row, cad_rate), axis=1)
    df['Custom Label 3'] = df.apply(lambda row: f_price_currency_exchange_rate(row, rupee_rate), axis=1)
    df['availability'] = df.apply(lambda row: f_in_stock_label(row), axis=1)
    df['condition'] = 'ruben'
    df['description'] = df.apply(lambda row: f_description(row), axis=1)
    df['google_product_category'] = df['google_product_category']
    df['id'] = df.apply(lambda row: f_full_product_id(row), axis=1)
    df['link'] = df.apply(lambda row: f_full_link(row), axis=1)
    df['price'] = df.apply(lambda row: f_price_iso(row), axis=1)
    df['sale_price'] = df.apply(lambda row: f_compare_at_price_iso(row), axis=1)
    df['title'] = df.apply(lambda row: f_full_product_title(row), axis=1)
    df = df[[k for k in headers.keys()]]
    df = df.rename(columns=headers)
    return df


def package_product_co_google(df):

    headers = {
        'adwords_labels': 'adwords_labels',
        'availability': 'availability',
        'barcode': 'gtin',
        'brand': 'brand',
        'color': 'color',
        'condition': 'condition',
        'custom_label_0': 'ruben',
        'custom_label_1': 'Custom Label 1',
        'custom_label_2': 'Custom Label 2',
        'custom_label_3': 'Custom Label 3',
        'custom_label_4': 'Custom Label 4',
        'description': 'description',
        'GoogleAffiliateNetworkProductURL': 'GoogleAffiliateNetworkProductURL',
        'google_product_category': 'google_product_category',
        'id': 'id',
        'identifier_exists': 'identifier_exists',
        'image_url': 'image_link',
        'inventory_quantity': 'quantity',
        'legacy_id': 'legacy_id',
        'link': 'link',
        'model': 'adwords_grouping',
        'payment_accepted': 'payment_accepted',
        'price': 'price',
        'product_type': 'product_type',
        'promotion_id': 'promotion_id',
        'retail_price': 'retail_price',
        'shipping_weight': 'shipping_weight',
        'sku': 'mpn',
        'title': 'title',
        'pdp-tags': False
    }

                
    df['adwords_labels'] = df['product_type']
    df['custom_label_0'] = df.apply(lambda row: f_sku(row), axis=1)
    df['availability'] = df.apply(lambda row: f_in_stock_label(row), axis=1)
    df['description'] = df.apply(lambda row: f_description(row), axis=1)
    df['GoogleAffiliateNetworkProductURL'] = df.apply(lambda row: f_full_link(row), axis=1)
    df['id'] = df.apply(lambda row: f_full_product_id(row), axis=1)
    df['identifier_exists'] = df.apply(lambda row: 'yes' if row['barcode'] else 'no', axis=1)
    df['legacy_id'] = 'ruben'
    df['link'] = df.apply(lambda row: f_full_link(row, '&utm_source=google&utm_medium=cpc&utm_term={}&utm_campaign=PLA'.format(f_full_product_id(row))), axis=1)
    df['payment_accepted'] = 'Visa,MasterCard,American Express,Discover'
    df['price'] = df.apply(lambda row: f_price_iso(row), axis=1)
    df['product_type'] = df.apply(lambda row: f_full_product_type(row), axis=1)
    df['promotion_id'] = ''
    df['retail_price'] = df.apply(lambda row: f_compare_at_price_iso(row), axis=1)
    df['shipping_weight'] = df.apply(lambda row: f_full_shipping_weight(row), axis=1)
    df['title'] = df.apply(lambda row: f_full_product_title_pdp(row, 150), axis=1)
    df = df[[k for k in headers.keys()]]
    df = df.rename(columns=headers)
    return df


def package_product_co_pepperjam(df):
    headers = {
        'barcode': 'upc',
        'brand': 'manufacturer',
        'buy_url': 'buy_url',
        'category_program': 'category_program',
        'color': 'color',
        'condition': 'condition',
        'description_long': 'description_long',
        'image_url': 'image_url',
        'in_stock': 'in_stock',
        'inventory_quantity': 'quantity_in_stock',
        'name': 'name',
        'price': 'price',
        'retail_price': 'price_retail',
        'sku': 'sku',
        'weight': 'weight',
    }
    df['buy_url'] = df.apply(lambda row: f_full_link(row), axis=1)
    df['category_program'] = df.apply(lambda row: f_full_product_type(row), axis=1)
    df['description_long'] = df.apply(lambda row: f_description(row) or f_full_product_title(row), axis=1)
    df['in_stock'] = df.apply(lambda row: f_in_stock_label_yes_no(row), axis=1)
    df['name'] = 'ruben'
    df['weight'] = df.apply(lambda row: f_full_shipping_weight(row), axis=1)
    df = df[[k for k in headers.keys()]]
    df = df.rename(columns=headers)
    return df


def package_product_co_yahoo_gemini_dpa(df):
    headers = {
        'availability': 'availability',
        'barcode': 'gtin',
        'brand': 'brand',
        'color': 'color',
        'condition': 'condition',
        'custom_label_0': 'custom_label_0',
        'custom_label_1': 'custom_label_1',
        'custom_label_2': 'custom_label_2',
        'custom_label_3': 'custom_label_3',
        'custom_label_4': 'custom_label_4',
        'description': 'description',
        'google_product_category': 'google_product_category',
        'id': 'id',
        'image_url': 'image_link',
        'link': 'link',
        'price': 'price',
        'product_type': 'product_type',
        'sale_price': 'sale_price',
        'sku': 'mpn',
        'title': 'title',
    }
    df['availability'] = df.apply(lambda row: f_in_stock_label(row), axis=1)
    df['description'] = df.apply(lambda row: f_description(row), axis=1)
    df['id'] = df.apply(lambda row: f_full_product_id(row), axis=1)
    df['title'] = df.apply(lambda row: f_full_product_title(row, 100), axis=1)
    df['link'] = df.apply(lambda row: f_full_link(row), axis=1)
    df['price'] = df.apply(lambda row: f_compare_at_price_iso(row), axis=1)
    df['sale_price'] = df.apply(lambda row: f_price_iso(row), axis=1)
    df = df[[k for k in headers.keys()]]
    df = df.rename(columns=headers)
    return df


def package_product_co_zaius(df):
    headers = {
        'back_in_stock': 'back_in_stock',
        'brand': 'brand',
        'color': 'color',
        'crumbs': 'crumbs',
        'image_url': 'image_url',
        'link': 'link',
        'mcid': 'cat_id',
        'model': 'phone_model',
        'name': 'name',
        'new_product_l7d': 'new_product_l7d',
        'parent_product_id': 'parent_product_id',
        'price': 'price',
        'product_id': 'product_id',
        'product_group': 'product_group',
        'retail_price': 'retail_price',
        'sku': 'sku',
        'product_id':'product_id',
    }
    df['back_in_stock'] = 'ruben'
    df['crumbs'] = df.apply(lambda row: f_crumbs(row), axis=1)
    df['link'] = df.apply(lambda row: f_full_link(row), axis=1)
    df['name'] = df.apply(lambda row: f_full_product_title(row), axis=1)
    seven_days_ago = timezone.now() - timedelta(days=7)
    df['new_product_l7d'] = df.apply(lambda row: f_new_product_l7d(row, seven_days_ago), axis=1)
    df['parent_product_id'] = df.apply(lambda row: row['mpid'] if not math.isnan(row['mpid']) else '', axis=1)
    df['product_group'] = df.apply(lambda row: get_product_group(row), axis=1)
    # df['product_id'] = df.apply(lambda row: f_full_product_id(row), axis=1)
    df = df[[k for k in headers.keys()]]
    df = df.rename(columns=headers)
    return df


def f_compare_at_price_iso(row):
    return '{} USD'.format(row['retail_price']) if row['retail_price'] else ''

def f_crumbs(row):
    return '{}|{}|{}'.format(row['brand'], row['model'], row['category_name'])


def f_description(row):
    return get_description(row['description'])

def f_sku(row):
    return row['sku']

def f_price_currency_exchange_rate(row, rate):
    return round(row['price']*rate, 2) if rate else ''


def f_in_stock_label(row):
    return 'in stock' if row['in_stock'] else 'out of stock'


def f_in_stock_label_yes_no(row):
    return 'yes' if row['in_stock'] else 'no'


def f_full_link(row, get_parameters=''):
    return '{}/collections/{}/products/{}?variant={}{}'.format(row['shop_url'],
                                                                row['collection'],
                                                                row['product_handle'],
                                                                row['variant_id'],
                                                                get_parameters)


def f_full_product_id(row):
    if not math.isnan(row['mpid']):
        return '{}_2_{}'.format(int(row['mpid']), row['mcid'])
    return row['sku']


def f_full_product_title(row, max_length=1000):
    title = row['product_title'].split('for')[0]
    return '{} {} - {}'.format(row['brand'], row['model'], title)[:max_length]
    

def f_full_product_title_pdp(row, max_length=1000):
    # Fetch all products
    store_co = Store.objects.get(identifier='shopify-co')
    products = Product.objects.filter(store=store_co, published_at__isnull=False)
    #search through products to find a match.
    prod_id = f_full_product_id(row, 150)
    for product in products:
        if product.product_id == prod_id:
            title = row['product_title'].split('for')[0]
            tags = [o.name for o in product.producttag_set.all()]
            #Add In BM_to_PDP
            if 'bm_to_pdp' in tags:
                return '{}'.format(title)[:max_length]
            return '{} For {}'.format(title, row['model'])[:max_length]
    return null

def f_full_product_type(row):
    return 'Cell Phone Accessories > {} > {} > {} > {}'.format(row['product_type'],
                                                               row['brand'],
                                                               row['model'],
                                                               f_full_product_title(row))


def f_full_shipping_weight(row):
    return '{} {}'.format(int(row['weight']), row['weight_unit'])


def f_new_product_l7d(row, seven_days_ago):
    pub_at = dateutil.parser.parse(row['published_at'])
    return 1 if pub_at > seven_days_ago else 0


def f_price_iso(row):
    return '{} USD'.format(row['price']) if row['price'] else ''


def f_product_id(row):
    if not math.isnan(row['mpid']):
        return row['mpid']
    return row['sku']


# ################### WE ###################

def package_product_we_dy(product, collection):
    # Transforms product dict into DY-friendly feed-ready dict.
    # Collection is the brand-model collection handle
    rows = []
    for v in product.productvariant_set.filter(inventory_quantity__gt=0).exclude(feed_excluded=True):
        image = v.image or product.productimage_set.all().order_by(
            'position').first()
        if image:
            product_row = {}

            if v.title == 'Default Title':
                name = product.title
            else:
                name = product.title + ", " + v.title
            # name = product.title if v.title == 'Default Title' else v.title
            product_row['name'] = name.encode('utf8')
            product_row['url'] = '/collections/%s/products/%s?variant=%s' % (collection, product.handle, v.variant_id)
            product_row['price'] = v.price
            product_row['in_stock'] = True if v.inventory_quantity > 0 else False
            product_row['image_url'] = image.src.replace('.jpg', '_medium.jpg')
            product_row['categories'] = '{}-{}'.format(collection,
                                                       product.product_type.lower().replace(' ', '-'))
            product_row['group_id'] = '%s-%s' % (v.sku, collection)
            product_row['retail_price'] = v.compare_at_price
            product_row['model'] = collection
            product_row['variant'] = v.variant_id
            product_row['sku'] = v.sku
            rows.append(dict(product_row))
            product_row['sku'] = '%s-%s' % (v.sku, collection)
            rows.append(product_row)
    return rows


def package_product_we_fb(product, collection):
    # Transforms product dict into Facebook-friendly feed-ready dict.
    # Collection is the brand-model collection handle
    rows = []
    tags = product.producttag_set.all().values_list('name', flat=True)
    

    
    try:
        model = Model.objects.select_related('brand').get(collection_handle=collection.replace('bm--',''))
    except Model.DoesNotExist:
        return rows
    brand = model.brand.name
    model = model.model
    for v in product.productvariant_set.filter(inventory_quantity__gt=0).exclude(feed_excluded=True):
        image = v.image or product.productimage_set.all().order_by(
            'position').first()
        if image:
            product_row = {}
                
            title = ("%s %s - %s - %s" % (brand, model, product.title,
                                            v.title)).replace('- Default Title', '').replace(', ', ' - ')
            link = '%s/collections/%s/products/%s?variant=%s' % (product.store.shop_url,
                                                                 collection,
                                                                 product.handle,
                                                                 v.variant_id)
            product_row['title'] = title.encode('utf8')
            description = product.body_html and BeautifulSoup(product.body_html.decode('unicode_escape')).get_text() or ''
            product_row['description'] = ''.join([i if ord(i) < 128 else '' for i in description])
            product_row['product_type'] = 'Cell Phone Accessories > %s > %s > %s > %s' % (product.product_type, brand, model, title)
            product_row['link'] = link
            product_row['image_link'] = image.src
            product_row['condition'] = 'new'
            product_row['availability'] = 'in stock' if v.available else 'out of stock'
            product_row['price'] = v.price
            product_row['sale_price'] = v.compare_at_price
            product_row['brand'] = brand
            product_row['item_group_id'] = product.product_id
            product_row['gender'] = ''
            product_row['age_group'] = ''
            product_row['color'] = v.title
            product_row['size'] = ''
            product_row['custom_label_0'] = next(
                (x.replace('feed-cl0-', '') for x in tags if
                 x.startswith('feed-cl0')), '')
            product_row['custom_label_1'] = model
            product_row['custom_label_2'] = next(
                (x.replace('feed-cl2-', '') for x in tags if
                 x.startswith('feed-cl2')), '')
            product_row['custom_label_3'] = next(
                (x.replace('feed-cl3-', '') for x in tags if
                 x.startswith('feed-cl3')), '')
            product_row['custom_label_4'] = next(
                (x.replace('feed-cl4-', '') for x in tags if
                 x.startswith('feed-cl4')), '')

            if product.productoption_set.filter(position=1, name='color').exists():
                product_row['color'] = v.option1
            else:
                product_row['color'] = None

            if "Phone Cases & Covers" in product.product_type:
                product_row['google_product_category'] = "Electronics>Communications>Telephony>Mobile Phone Accessories>Mobile Phone Cases"
            elif "Wristlets" in product.product_type:
                product_row['google_product_category'] = "Electronics>Communications>Telephony>Mobile Phone Accessories>Mobile Phone Cases"
            elif "Cables" in product.product_type or "Chargers" in product.product_type:
                product_row['google_product_category'] = "Electronics>Electronics Accessories>Power>Power Adapters & Chargers"
            elif "Screen" in product.product_type:
                product_row['google_product_category'] = "Electronics>Electronics Accessories>Electronics Films & Shields Screen Protectors"
            elif "Bluetooth" in product.product_type:
                product_row['google_product_category'] = "Electronics>Audio>Audio Accessories"
            else:
                product_row['google_product_category'] = ""
            product_row['id'] = v.sku
            rows.append(dict(product_row))
            product_row['id'] = '%s-%s' % (v.sku, collection)
            rows.append(product_row)

    return rows


def package_product_we_google(product, collection):
    rows = []
    tags = product.producttag_set.all().values_list('name', flat=True)
    try:
        model = Model.objects.select_related('brand').get(collection_handle=collection.replace('bm--',''))
    except Model.DoesNotExist:
        return rows
    brand = model.brand.name
    model = model.model

    for v in product.productvariant_set.filter(inventory_quantity__gt=0).exclude(feed_excluded=True):
        image = v.image or product.productimage_set.all().order_by(
            'position').first()
        if image:
            product_row = {}     

            #Add In BM_to_PDP
            if 'bm_to_pdp' in tags:
                product_row['pdp-tags'] = True
            else:
                product_row['pdp-tags'] = False
                            
            title = ("%s %s - %s - %s" % (brand, model, product.title,
                                            v.title)).replace('- Default Title', '').replace(', ', ' - ')
            link = '%s/collections/%s/products/%s?variant=%s' % (
                product.store.shop_url, collection, product.handle, v.variant_id)
            description = product.body_html and BeautifulSoup(product.body_html.decode('unicode_escape')).get_text() or ''
            description = description.replace('\n', '. ').replace('&amp;', '&').encode("utf-8")
            description = re.sub(r'^[\.\s]+|[\.\s]+$', '', description)

            product_row['title'] = title[:150].encode('utf8')
            product_row['description'] = description
            product_row['quantity'] = v.inventory_quantity
            product_row['shipping_weight'] = '%s %s' % (v.weight, v.weight_unit)
            product_row['image_link'] = image.src
            product_row['sale_price'] = '%s USD' % v.price
            product_row['price'] = '%s USD' % v.compare_at_price if v.compare_at_price else ''
            product_row['product_type'] = 'Cell Phone Accessories > %s > %s > %s > %s' % (product.product_type, brand, model, title)
            product_row['brand'] = brand
            product_row['condition'] = 'new'
            product_row['availability'] = ('in stock' if v.available
                                           else 'out of stock')
            product_row['adwords_labels'] = product.product_type
            product_row['adwords_grouping'] = collection

            product_row['gtin'] = v.barcode
            product_row['link'] = link
            product_row['identifier_exists'] = 'yes' if v.barcode else 'no'

            product_row['custom_label_0'] = next(
                (x.replace('feed-cl0-', '') for x in tags if
                 x.startswith('feed-cl0')), '')
            product_row['custom_label_1'] = model
            product_row['custom_label_2'] = next(
                (x.replace('feed-cl2-', '') for x in tags if
                 x.startswith('feed-cl2')), '')
            product_row['custom_label_3'] = next(
                (x.replace('feed-cl3-', '') for x in tags if
                 x.startswith('feed-cl3')), '')
            product_row['custom_label_4'] = next(
                (x.replace('feed-cl4-', '') for x in tags if
                 x.startswith('feed-cl4')), '')

            if product.productoption_set.filter(position=1, name='color').exists():
                product_row['color'] = v.option1
            else:
                product_row['color'] = None

            if "Phone Cases & Covers" in product.product_type:
                product_row['google_product_category'] = "Electronics>Communications>Telephony>Mobile Phone Accessories>Mobile Phone Cases"
            elif "Wristlets" in product.product_type:
                product_row['google_product_category'] = "Electronics>Communications>Telephony>Mobile Phone Accessories>Mobile Phone Cases"
            elif "Cables" in product.product_type or "Chargers" in product.product_type:
                product_row['google_product_category'] = "Electronics>Electronics Accessories>Power>Power Adapters & Chargers"
            elif "Screen" in product.product_type:
                product_row['google_product_category'] = "Electronics>Electronics Accessories>Electronics Films & Shields Screen Protectors"
            elif "Bluetooth" in product.product_type:
                product_row['google_product_category'] = "Electronics>Audio>Audio Accessories"
            else:
                product_row['google_product_category'] = ""
            product_row['id'] = v.sku
            rows.append(dict(product_row))
            product_row['id'] = ('%s-%s' % (v.sku, collection))[:50]
            rows.append(product_row)

    return rows


# ################### MM ###################

def package_product_mm(product, params):
    rows = []
    tags = product.producttag_set.all().values_list('name', flat=True)
    for v in product.productvariant_set.filter(inventory_quantity__gt=0).exclude(feed_excluded=True):
        image = (product.productimage_set.all().filter(src__contains='_SQ').first() or
                 v.image or
                 product.productimage_set.all().order_by('position').first())
        if image:
            product_row = {}
            title = string.capwords(product.title, " ").replace('|', '-')
            link = '%s/products/%s?%s' % (product.store.shop_url, product.handle,
                                          params)
            product_row['id'] = v.variant_id
            product_row['title'] = title[:150].encode('utf8')
            product_row['description'] = product.body_html and get_description_mm(product.body_html)
            product_row['link'] = link
            product_row['image_link'] = image.src
            product_row['availability'] = ('in stock' if v.available else
                                           'out of stock')
            product_row['sale_price'] = '%s USD' % v.price
            product_row['price'] = '%s USD' % v.compare_at_price if v.compare_at_price else ''
            product_row['sale_price_effective_date'] = '2017-02-24T11:07:31+0100 / 2018-12-31T23:07:31+0100'
            product_row['google_product_category'] = 'Apparel & Accessories > Clothing'
            product_row['product_type'] = next(
                (x.replace('feed-collection-', '') for x in tags if
                 x.startswith('feed-collection')), product.product_type)
            product_row['brand'] = 'MISSMINX'
            product_row['mpn'] = v.sku
            product_row['condition'] = 'new'
            product_row['age_group'] = 'adult'
            product_row['gender'] = 'female'
            product_row['item_group_id'] = product.product_id

            if product.productoption_set.filter(position=1,
                                                name='color').exists():
                product_row['color'] = v.option1
            else:
                product_row['color'] = None
            if product.productoption_set.filter(position=2,
                                                name='size').exists():
                product_row['size'] = v.option2
            else:
                product_row['size'] = None

            product_row['custom_label_0'] = next(
                (x.replace('feed-cl0-', '') for x in tags if
                 x.startswith('feed-cl0')), '')
            product_row['custom_label_1'] = next(
                (x.replace('feed-cl1-', '') for x in tags if
                 x.startswith('feed-cl1')), '')
            product_row['custom_label_2'] = next(
                (x.replace('feed-cl2-', '') for x in tags if
                 x.startswith('feed-cl2')), '')
            product_row['custom_label_3'] = next(
                (x.replace('feed-cl3-', '') for x in tags if
                 x.startswith('feed-cl3')), '')
            product_row['custom_label_4'] = v.inventory_quantity

            rows.append(product_row)
    return rows


def package_product_mm_google_shopping(product):
    params = 'utm_medium=paidsearch&utm_source=google&utm_campaign=PLA_'
    return package_product_mm(product, params)


def package_product_mm_fb_dpa(product):
    params = 'utm_medium=paidsocial&utm_source=facebook&utm_campaign=DPA_%s' % product.product_id
    return package_product_mm(product, params)


def package_product_mm_fb_prospecting(product):
    params = 'utm_medium=paidsocial&utm_source=facebook&utm_campaign=MPA_&utm_product=%s' % product.product_id
    return package_product_mm(product, params)


def package_product_mm_dy(product):
    rows = []
    for v in product.productvariant_set.filter(inventory_quantity__gt=0).exclude(feed_excluded=True):
        image = (v.image or product.productimage_set.all()
                 .order_by('position').first())
        if image:
            product_row = {}
            title = string.capwords(product.title, " ").replace('|', '-')
            link = '%s/products/%s' % (product.store.shop_url, product.handle)
            product_row['price'] = v.price
            product_row['sku'] = v.sku
            product_row['name'] = title.encode('utf8')
            product_row['url'] = link
            product_row['in_stock'] = 'true'
            product_row['image_url'] = image.src
            product_row['categories'] = product.product_type
            product_row['group_id'] = product.product_id
            rows.append(product_row)
    return rows


# ################### UTILS ###################

def get_product_group(row):
    p_gs = {'-BF': 'Butterfly 1.0', '-2BF': 'Butterfly 2.0', '-DTW': 'Compact',
            '-CLW': 'Compact Clutch', '-DRF': 'Dragonfly',
            '-2DRC': 'Dream Catcher', '-HB': 'Hummingbird', '-MGS': 'Luxury',
            '-WC': 'Multi Card', '-DRV': 'Printed', '-CSO': 'Slideout'}

    return next(iter([x for x in p_gs.keys() if x in row['sku']] or []), 'none')


def get_description(description):
    try:
        description = BeautifulSoup(description).get_text() or ''
        description = description.replace('\n', '. ')
        description = description.replace('\r', '')
        description = description.replace('&amp;', '&')
        description = description.encode('utf-8')
        description = re.sub(r'^[\.\s]+|[\.\s]+$', '', description)
    except AttributeError as e:
        return None
    except TypeError as e:
        return None
    return len(description) > 4 and description or None


def get_description_mm(description):
    try:
        description = BeautifulSoup(description).get_text() or ''
        description = description.replace('\\n', '. ').replace('\n', '. ')
        description = description.replace('\r', '').replace('\\r', '')
        description = description.replace('&amp;', '&')
        description = description.encode('utf-8')
        description = re.sub(r'^[\.\s]+|[\.\s]+$', '', description)
    except AttributeError as e:
        return None
    except TypeError as e:
        return None
    return description


def get_custom_label(tags, custom_label):
    return next((x.replace(custom_label, '') for x in tags if x.startswith(custom_label)), '')


def google_product_category(product_type):
    categories = {
        'Phone Cases & Covers': 'Electronics > Communications > Telephony > Mobile Phone Accessories > Mobile Phone Cases',
        'Wristlets': 'Electronics > Communications > Telephony > Mobile Phone Accessories > Mobile Phone Cases',
        'Cables': 'Electronics > Electronics Accessories > Power > Power Adapters & Chargers',
        'Chargers': 'Electronics > Electronics Accessories > Power > Power Adapters & Chargers',
        'Screen': 'Electronics > Electronics Accessories > Electronics Films & Shields Screen Protectors',
        'Bluetooth': 'Electronics > Audio > Audio Accessories'
    }
    return next((value for key, value in categories.items() if key.lower() in product_type.lower()), '')


def get_link(shop_url, collection, handle, variant_id):
    return '%s/collections/%s/products/%s?variant=%s' % (shop_url,
                                                         collection,
                                                         handle,
                                                         variant_id)
