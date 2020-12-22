import json

from django.utils import timezone

from .connect import ShopifyConnect
from .exception import ShopifyTransactionException
from .models import (MasterAttributeSet, MasterProduct, Product,
                     ShopifyTransaction)
from .utils import get_all_product_metafields


def generate_product_structure(t):
    product = load_product(t)
    images = load_images(t)
    options = load_options(t)
    variant = load_variant(t)
    metafields = load_metafields(t)
    if images:
        product['images'] = images
    if options:
        product['options'] = options
    if variant:
        product['variants'] = [variant, ]
    if metafields:
        product['metafields'] = metafields
    return product


def process_transaction(t):
    if t.transaction_type == ShopifyTransaction.PRODUCT_CREATE:
        product_create(t)
    elif t.transaction_type == ShopifyTransaction.PRODUCT_UPDATE:
        product_update(t)
    else:
        raise ShopifyTransactionException('Transaction type processing not implemented: {}'.format(t.transaction_type))


def product_create(t):
    shopify = ShopifyConnect(t.store)
    content = t.content

    # Create master product
    try:
        mpid = content[0]['mpid']
        sku = content[0]['Variant SKU']
        product_type = content[0]['Type']

        if not mpid:
            mpid = MasterProduct.get_next_available_mpid()
        try:
            attribute_set = MasterAttributeSet.objects.get(
                attribute_set_name=product_type)
        except MasterAttributeSet.DoesNotExist:
            raise ShopifyTransactionException(
                'Master attribute set name does not exist for product type: {}'.format(
                    [product_type]))
        MasterProduct.objects.get_or_create(mpid=mpid,
                                            defaults={
                                                'attribute_set': attribute_set,
                                                'created_at': timezone.now(),
                                                'sku': sku,
                                            })
    except Exception as e:
        raise ShopifyTransactionException(
            'Master Product creation error: {}'.format(repr(e)))

    # Product creation
    try:
        product = generate_product_structure(content)
        status_code, response = shopify.create_product(product)
        if status_code != 201:
            raise ShopifyTransactionException(
                'API Call error - Product creation: {}'.format(
                    str(content['errors'])))
    except Exception as e:
        raise ShopifyTransactionException(
            'Product creation error: {}'.format(repr(e)))


def product_update(t):
    shopify = ShopifyConnect(t.store)
    content = t.content

    try:
        handle = content[0]['Handle']
        try:
            product = Product.objects.get(store=t.store, handle=handle)
        except Product.DoesNotExist:
            raise ShopifyTransactionException(
                'Product handle does not exists: {}'.format(str(content['errors'])))
        attributes = generate_product_structure(content)

        attributes.pop('images', None)
        attributes.pop('options', None)
        attributes.pop('variants', None)
        changed_metafields = attributes.pop('metafields', [])
        attributes['metafields'] = merge_metafields(product, changed_metafields)

        response = shopify.update_product(product.product_id, attributes)
        if response.status_code != 200:
            content = json.loads(response.content)
            raise ShopifyTransactionException(
                'API Call error - Product creation: {}'.format(
                    str(content['errors'])))
    except Exception as e:
        raise ShopifyTransactionException(
            'Product update error: {}'.format(repr(e)))


def load_images(t):
    return [{'position': line['Image Position'], 'src': line['Image Src']} for
            line in t if 'Image Position' in line and 'Image Src' in line]


def load_metafields(t):
    main_row = t[0]
    return [{'key': k.split('.')[2], 'value': main_row[k],
             'value_type': 'string', 'namespace': k.split('.')[1]} for k in
            main_row if
            k.split('.')[0] == 'metafield' and main_row[k]]


def load_options(t):
    main_row = t[0]
    options = []
    if 'Option1 Name' in main_row and main_row['Option1 Name']:
        option = {'name': main_row['Option1 Name'],
                  'values': [main_row['Option1 Value'], ]}
        options.append(option)
    if 'Option2 Name' in main_row and main_row['Option2 Name']:
        option = {'name': main_row['Option2 Name'],
                  'values': [main_row['Option2 Value'], ]}
        options.append(option)
    if 'Option3 Name' in main_row and main_row['Option3 Name']:
        option = {'name': main_row['Option3 Name'],
                  'values': [main_row['Option3 Value'], ]}
        options.append(option)

    return options


def load_product(t):
    main_row = t[0]
    product_mapping = {'Handle': 'handle', 'Title': 'title',
                       'Body (HTML)': 'body_html', 'Vendor': 'vendor',
                       'Type': 'product_type', 'Tags': 'tags',
                       'Published': 'published',
                       'SEO Title': 'metafields_global_title_tag',
                       'SEO Description': 'metafields_global_description_tag'}
    product = re_map_dict(main_row, product_mapping)
    return product


def load_variant(t):
    main_row = t[0]
    variant_mapping = {'Variant SKU': 'sku', 'Variant Grams': 'grams',
                       'Variant Inventory Tracker': 'inventory_management',
                       'Variant Inventory Qty': 'inventory_quantity',
                       'Variant Inventory Policy': 'inventory_policy',
                       'Variant Fulfillment Service': 'fulfillment_service',
                       'Variant Price': 'price',
                       'Variant Compare At Price': 'compare_at_price',
                       'Variant Requires Shipping': 'requires_shipping',
                       'Variant Taxable': 'taxable',
                       'Variant Barcode': 'barcode',
                       'Variant Weight Unit': 'weight_unit'}
    variant = re_map_dict(main_row, variant_mapping)
    return variant


def merge_metafields(product, changed_metafields):
    current_metafields = get_all_product_metafields(product)
    for metafield in changed_metafields:
        id = next(iter(x['id'] for x in current_metafields if x['namespace']==metafield['namespace'] and x['key']==metafield['key']), None)
        if id:
            metafield['id'] = id
    return changed_metafields


def re_map_dict(d, mapping):
    return {mapping[name]: val for name, val in d.items() if name in mapping}
