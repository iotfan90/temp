import json

from collections import defaultdict
from django.db import connections
from mobovidata_dj.shopify.connect import ShopifyConnect
from mobovidata_dj.shopify.models import (MasterAttributeValue, Model, Product,
                                          Store)


def remove_ctg_prefix():
    store = Store.objects.get(identifier='shopify-co')
    shopify = ShopifyConnect(store)

    product_qty = shopify.get_products_total_quantity()['count']
    total_pages = -(-product_qty // 250)

    products = []
    counter = 0

    for page in xrange(1, total_pages + 1):
        response = shopify.get_products(page=page)
        products.extend(response['products'])

    for product in products:
        has_prefix = False
        tags = []
        for tag in product['tags'].split(','):
            if tag.strip().startswith('ctg--'):
                tags.append(tag.strip()[len('ctg--'):])
                has_prefix = True
            else:
                tags.append(tag.strip())
        if has_prefix:
            counter += 1
            print 'has prefix, ', counter
            attributes = {'tags': ','.join(tags)}
            resp = shopify.update_product(product['id'], attributes)
            if resp.status_code != 200:
                print 'Error updating product id {}. Message: {}'.format(product['id'],
                                                                         json.loads(resp.content))


def get_categories():
    cursor = connections['magento'].cursor()
    cursor.execute('''
        select
        cpe.entity_id as entity_id,
        cpe.sku,
        GROUP_CONCAT(DISTINCT ccev.value) as 'category'

        from catalog_product_entity as cpe
        left JOIN catalog_category_product as ccp ON cpe.entity_id = ccp.product_id
        left JOIN catalog_category_entity as cce ON ccp.category_id = cce.entity_id

        left JOIN catalog_category_entity_varchar as ccev ON ccev.entity_id = substring_index(substring_index(cce.path,'/',5),'/',-1) and ccev.attribute_id = 43 and ccev.value !='default-category'
        left JOIN catalog_product_entity_int as cpei on ccp.product_id = cpei.entity_id and cpei.entity_type_id = 4 and cpei.attribute_id = 96 and cpei.store_id = 0
        where cce.path != '1/2'
        group by 1
        order by cpe.entity_id
        ''')

    columns = cursor.description
    query = [
        {columns[index][0]: column for index, column in enumerate(value)} for
        value in cursor.fetchall()]

    return query


def get_brand_models():
    cursor = connections['magento'].cursor()
    cursor.execute('''
        select
        cpe.entity_id as entity_id,
        cpe.sku,

        #Check if / >= 2 to concat brand and model, otherwise its not an actual bm related
        if(
        (LENGTH(REPLACE(cce.path,left(cce.path,4),'')) - LENGTH(replace(REPLACE(cce.path,left(cce.path,4),''),'/','')) +1)>=2,
        concat('bm--',ccev.value,'-',ccev2.value),'') as 'brand-model'

        from catalog_product_entity as cpe
        left JOIN catalog_category_product as ccp ON cpe.entity_id = ccp.product_id
        left JOIN catalog_category_entity as cce ON ccp.category_id = cce.entity_id

        left JOIN catalog_category_entity_varchar as ccev ON ccev.entity_id = substring_index(substring_index(cce.path,'/',3),'/',-1) and ccev.attribute_id = 43 and ccev.value !='default-category'
        left JOIN catalog_category_entity_varchar as ccev2 ON ccev2.entity_id = substring_index(substring_index(cce.path,'/',4),'/',-1) and ccev2.attribute_id = 43 and ccev.value !='default-category'

        left JOIN eav_attribute_set as eas ON cpe.attribute_set_id = eas.attribute_set_id
        left JOIN catalog_product_entity_int as cpei on ccp.product_id = cpei.entity_id and cpei.entity_type_id = 4 and cpei.attribute_id = 96 and cpei.store_id = 0


        where cce.path != '1/2'

        group by 1, 3
        order by cpe.entity_id
        ''')

    columns = cursor.description
    query = [
        {columns[index][0]: column for index, column in enumerate(value)} for
        value in cursor.fetchall()]

    return query


# https://trello.com/c/0N4abEei/57-co-shopify-product-tags
def update_co_product_tags():
    store = Store.objects.get(identifier='shopify-co')
    shopify = ShopifyConnect(store)
    products = Product.objects.filter(store=store)
    categories = get_categories()
    categories = {x['sku']: x['category'] for x in categories}
    b_m = get_brand_models()
    brand_models = defaultdict(list)
    for b_m in b_m:
        if b_m['brand-model']:
            brand_models[b_m['sku']].append(b_m['brand-model'])
    for product in products:
        sku = product.productvariant_set.first().sku
        tags = list(product.producttag_set.all().values_list('name', flat=True))
        attrs = dict(MasterAttributeValue.objects
                     .filter(product__sku=sku)
                     .values_list('attribute_code', 'value'))

        # Remove old tags
        connector_types = tuple([x[0] for x in Model.ADAPTOR_TYPE_CHOICES])
        prefixes = ('price:', 'product type:', 'color:', 'material:',
                    'oem manufacturer', 'bm--', 'universal-products', )
        prefixes = prefixes + connector_types
        tags = filter(lambda x: not x.lower().startswith(prefixes), tags)

        # Add new tags
        # Price Range
        # 'Price:under-10'
        # 'Price:10-20'
        # 'Price:20-30'
        # 'Price:30-40'
        # 'Price:40-50'
        try:
            value = float(attrs['special_price'])
            if value < 10:
                value = 'under-10'
            elif value < 20:
                value = '10-20'
            elif value < 30:
                value = '20-30'
            elif value < 40:
                value = '30-40'
            else:
                value = '40-50'

            tag = 'Price:{}'.format(value)
            tags.append(tag)
        except KeyError:
            pass
        except ValueError:
            pass

        # Product Type - Format --> Product Type:PRODUCT_TYPE
        try:
            value = attrs['product_type']
            tag = 'Product Type:{}'.format(value)
            tags.append(tag)
        except KeyError:
            pass

        # Color - Format --> Color:COLOR_NAME
        try:
            value = attrs['primary_color']
            tag = 'Color:{}'.format(value)
            tags.append(tag)
        except KeyError:
            pass
        try:
            value = attrs['color_picker']
            tag = 'Color:{}'.format(value)
            tags.append(tag)
        except KeyError:
            pass

        # Material - Format --> Material:MATERIAL_NAME
        try:
            value = attrs['material']
            for value in value.split(','):
                tag = 'Material:{}'.format(value)
                tags.append(tag)
        except KeyError:
            pass

        # OEM Manufacturer - Format --> OEM Manufacturer:MANUFACTURER_NAME
        try:
            value = attrs['oem_manufacturer']
            tag = 'OEM Manufacturer:{}'.format(value)
            tags.append(tag)
        except KeyError:
            pass

        # For all products excluding 'Bluetooth & Audio', 'Phone Cables' and 'Phone Chargers':
        if product.product_type not in ['Bluetooth & Audio', 'Phone Cables', 'Phone Chargers']:
            # Brand Model compatibility tags. Tag format: bm--BRAND_MODEL_NAME
            try:
                brands = brand_models[sku]
                tag = len(brands) > 2 and 'universal-products' or brands
                tags.extend(tag)
            except KeyError:
                pass

            #  Category. Tag format: CATEGORY_NAME_HANDLE_FORMAT
            try:
                tag = categories[sku]
                tags.append(tag)
            except KeyError:
                pass

        # For 'Phone Cables' and 'Phone Chargers':
        if product.product_type in ['Phone Cables', 'Phone Chargers']:
            try:
                value = attrs['connector_types']
                tag = value.lower().replace(' ', '-')
                tags.append(tag)
            except KeyError:
                pass

        attributes = {'tags': ','.join(tags)}
        resp = shopify.update_product(product.product_id, attributes)
        if resp.status_code != 200:
            print 'Error updating product id {}. Message: {}'.format(product.product_id, json.loads(resp.content))


# https://trello.com/c/0N4abEei/57-co-shopify-product-tags - Remove tags
def remove_co_product_tags(store_identifier, prefixes):
    store = Store.objects.get(identifier=store_identifier)
    shopify = ShopifyConnect(store)
    products = Product.objects.filter(store=store)

    for product in products:
        sku = product.productvariant_set.first().sku
        old_tags = list(product.producttag_set.all().values_list('name', flat=True))
        old_length = len(old_tags)

        # Remove tags
        new_tags = filter(lambda x: not x.lower().startswith(prefixes), old_tags)
        new_length = len(new_tags)
        if old_length != new_length:
            manufacturer = filter(lambda x: x.lower().startswith('oem manufaturer:'), old_tags)
            if manufacturer:
                manufacturer = manufacturer[0].replace('oem manufaturer:', 'OEM Manufacturer:')
                new_tags.append(manufacturer)
            attributes = {'tags': ','.join(new_tags)}
            resp = shopify.update_product(product.product_id, attributes)
            if resp.status_code != 200:
                print 'Error updating product id {}. Message: {}'.format(product.product_id, json.loads(resp.content))
