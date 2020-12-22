import csv
import json
import pandas as pd

from bs4 import BeautifulSoup
from django.db import connections

from mobovidata_dj.shopify.connect import ShopifyConnect
from mobovidata_dj.shopify.models import (MetadataProduct,
                                          MetadataProductAttribute, Product,
                                          Store)


def get_products():
    cursor = connections['magento'].cursor()
    cursor.execute('''
            SELECT cpe.sku
            FROM catalog_product_entity as cpe;
        ''')

    columns = cursor.description
    products = [
        {columns[index][0]: column for index, column in enumerate(value)} for
        value in cursor.fetchall()]

    return products


def get_product_attrs():
    cursor = connections['magento'].cursor()
    cursor.execute('''
        SELECT attribute_id, attribute_code, backend_type, frontend_input
        FROM eav_attribute
        WHERE entity_type_id=4
        ORDER BY attribute_id;
    ''')

    columns = cursor.description
    product_attrs = [
        {columns[index][0]: column for index, column in enumerate(value)} for
        value in cursor.fetchall()]

    return product_attrs


def get_cpe_table_name(product_attr):
    cpe_t_n = None
    if product_attr['backend_type'] == 'int':
        cpe_t_n = 'catalog_product_entity_int'
    elif product_attr['backend_type'] == 'varchar':
        cpe_t_n = 'catalog_product_entity_varchar'
    elif product_attr['backend_type'] == 'text':
        cpe_t_n = 'catalog_product_entity_text'
    elif product_attr['backend_type'] == 'decimal':
        cpe_t_n = 'catalog_product_entity_decimal'
    elif product_attr['backend_type'] == 'datetime':
        cpe_t_n = 'catalog_product_entity_datetime'
    return cpe_t_n


def get_attr_id(product_attr):
    return product_attr['attribute_id']


def get_attr_code(product_attr):
    return product_attr['attribute_code']


def is_select(product_attr):
    return product_attr['frontend_input'] == 'select'


def is_multiselect(product_attr):
    return product_attr['frontend_input'] == 'multiselect'


def construct_attr_join(product_attr):
    cpe_table_name = get_cpe_table_name(product_attr)
    data = {'cpe_table': cpe_table_name,
            'attr_id': get_attr_id(product_attr),
            'attr_code': 'prod_{}'.format(get_attr_code(product_attr)),
            'store_id': 0}
    if is_multiselect(product_attr):
        query = """
LEFT JOIN (
SELECT entity_id, GROUP_CONCAT(DISTINCT value) as value
FROM (
    SELECT distinct a.entity_id, b.value
    FROM {cpe_table} as a
    LEFT JOIN eav_attribute_option_value as b on b.option_id = substring_index(substring_index(a.value,',',1),',',-1) and b.store_id = {store_id}
    WHERE a.attribute_id = {attr_id}

    UNION SELECT distinct a.entity_id, b.value
    FROM {cpe_table} as a
    LEFT JOIN eav_attribute_option_value as b on b.option_id = substring_index(substring_index(a.value,',',2),',',-1) and b.store_id = {store_id}
    WHERE a.attribute_id = {attr_id}
    UNION SELECT distinct a.entity_id, b.value
    FROM {cpe_table} as a
    LEFT JOIN eav_attribute_option_value as b on b.option_id = substring_index(substring_index(a.value,',',3),',',-1) and b.store_id = {store_id}
    WHERE a.attribute_id = {attr_id}
    ) as derived group by entity_id
)as {attr_code} on {attr_code}.entity_id = cpe.entity_id""".format(**data)
    elif is_select(product_attr):
        query = 'LEFT JOIN (SELECT  a.attribute_id, a.entity_id, b.value FROM {cpe_table} as a LEFT JOIN eav_attribute_option_value as b on b.option_id = a.value and b.store_id = {store_id} WHERE a.store_id = {store_id} and a.attribute_id = {attr_id}) as {attr_code} on {attr_code}.entity_id = cpe.entity_id'.format(**data)
    else:
        query = 'LEFT JOIN (SELECT a.entity_id, a.value FROM {cpe_table} as a WHERE a.store_id = {store_id} and a.attribute_id = {attr_id}) as {attr_code} on {attr_code}.entity_id = cpe.entity_id'.format(**data)

    return query


def construct_query(product_attrs):
    query = 'SELECT\ncpe.sku'
    for product_attr in product_attrs:
        if not get_cpe_table_name(product_attr):
            continue
        attr_code = get_attr_code(product_attr)
        query += ',\nprod_{0}.value as "{0}"'.format(attr_code)

    query += '\nFROM catalog_product_entity cpe'
    for product_attr in product_attrs:
        if not get_cpe_table_name(product_attr):
            continue
        join = construct_attr_join(product_attr)
        query += '\n{}'.format(join)

    query += ';'
    return query


def save_products_to_mvd_db(store, products):
    m_products = []

    for sku in products:
        m_product = MetadataProduct(store=store, sku=sku['sku'])
        m_products.append(m_product)
    MetadataProduct.objects.bulk_create(m_products)

    # Generate products dictionary {sku: product_obj}
    m_products = MetadataProduct.objects.filter(store=store)
    m_p_d = {}
    for m_product in m_products:
        m_p_d[m_product.sku] = m_product

    return m_p_d


def save_product_attributes_to_mvd_db(query, products):
    m_p_attrs = []
    cursor = connections['magento'].cursor()
    cursor.execute(query)

    columns = cursor.description
    skus = [{columns[index][0]: column for index, column in enumerate(value)}
            for value in cursor.fetchall()]
    for sku in skus:
        sku_value = sku.pop('sku')
        for key, value in sku.iteritems():
            p_metadata = products[sku_value]
            if value:
                m_p_attrs.append(MetadataProductAttribute(product_metadata=p_metadata,
                                                          namespace=MetadataProductAttribute.PRODUCT_ATTR,
                                                          m_type=MetadataProductAttribute.DESCRIPTION,
                                                          key=key,
                                                          value=value))

    # Bulk create for MetadataProductAttribute done in chunks of 1,000 objects.
    chunks = [m_p_attrs[i:i + 1000] for i in xrange(0, len(m_p_attrs), 1000)]
    for chunk in chunks:
        MetadataProductAttribute.objects.bulk_create(chunk)


def products_attr_script_we():
    try:
        try:
            store = Store.objects.get(identifier='shopify-we')
            generate_products_attrs(store)
        except Store.DoesNotExist:
            pass
    except Exception as e:
        raise


def products_attr_script_co():
    try:
        try:
            store = Store.objects.get(identifier='shopify-co')
            generate_products_attrs(store)
        except Store.DoesNotExist:
            pass
    except Exception as e:
        raise


def generate_products_attrs(store):
    products = get_products()
    product_attrs = get_product_attrs()
    products = save_products_to_mvd_db(store, products)
    # It's allowed up to 60 joins per sql query
    chunks = [product_attrs[i:i + 10] for i in
              xrange(0, len(product_attrs), 10)]
    for chunk in chunks:
        query = construct_query(chunk)
        save_product_attributes_to_mvd_db(query, products)


def bulk_update_product_attributes():
    m_products = MetadataProduct.objects.all()

    try:
        for product in m_products:
            try:
                product_id = (Product.objects
                              .get(store=product.store,
                                   productvariant__sku=product.sku)
                              .product_id)
            except Product.DoesNotExist:
                error_msg = ("It doesn't exists a Product on MVD DB with the "
                             "sku '{}'.".format(product.sku))

                product.metadataproductattribute_set.update(status=MetadataProductAttribute.ERROR,
                                                            error_msg=error_msg)
                continue
            shopify = ShopifyConnect(product.store)

            attributes = {'metafields': []}

            for p_attr in product.metadataproductattribute_set.all():
                metafield = {
                    'namespace': p_attr.namespace,
                    'key': p_attr.key,
                    'description': p_attr.description,
                    'value': p_attr.value,
                    'value_type': 'string'
                }
                attributes['metafields'].append(metafield)
            resp = shopify.update_product(product_id, attributes)
            if resp.status_code == 200:
                product.metadataproductattribute_set.update(status=MetadataProductAttribute.SYNCED)
            else:
                content = json.loads(resp.content)
                product.metadataproductattribute_set.update(status=MetadataProductAttribute.ERROR,
                                                            error_msg=str(content['errors']))

    except Exception, ex:
        raise


def remove_metafields(store_identifier, type_of_resource, namespace, key):
    store = Store.objects.get(identifier=store_identifier)
    shopify = ShopifyConnect(store)
    products = Product.objects.filter(store=store)
    metafields = []

    # Get all metafields
    for product in products:
        response = shopify.get_metafields(type_of_resource,
                                          product.product_id,
                                          namespace=namespace,
                                          key=key)
        metafields.extend(response['metafields'])

    # Delete all metafields
    for metafield in metafields:
        try:
            status_code, content = shopify.delete_metafield(metafield['id'])
            if status_code != 200:
                print 'Metafield: {} not deleted. Error: {}'.format(metafield['id'], str(content['errors']))
        except Exception as ex:
            print 'Metafield: {} not deleted. Error: {}'.format(metafield['id'],
                                                                repr(ex))


def change_image_links(mapping_file_path, output_folder):
    mapping = pd.read_csv(mapping_file_path)
    mapping = mapping.dropna()
    mapping = mapping.set_index('OldURL').T.to_dict('list')

    metadatas = MetadataProductAttribute.objects.filter(product_metadata__store__identifier='shopify-co',
                                                        key='description')
    images_changed = set()
    images_unchanged = set()
    for metadata in metadatas:
        changed = False
        metadata.value = metadata.value.replace('\n', '').replace('\r', '')
        metadata.value = metadata.value.replace('{{media url="', 'https://s4.cellularoutfitter.com/media/').replace('"}}"', '"')
        soup = BeautifulSoup(metadata.value)
        imgs = soup.findAll('img')
        for img in imgs:
            if 'src' in img.attrs:
                image = img.attrs['src']
                if image.startswith('http') and image in mapping:
                    changed = True
                    images_changed.add(image)
                    metadata.value = metadata.value.replace(image, mapping[image][0])
                else:
                    if 'cdn.shopify.com' not in image and 'wirelessemporium' not in image:
                        images_unchanged.add(img.attrs['src'])
        if changed:
            metadata.status = MetadataProductAttribute.UNSYNCED
            metadata.save()

    # Write changed images
    output_file = output_folder + 'changed_images.csv'
    with open(output_file, 'wb') as csvfile:
        fieldnames = ['images', ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in images_changed:
            writer.writerow({'images': r})

    # Write unchanged images
    output_file = output_folder + 'unchanged_images.csv'
    with open(output_file, 'wb') as csvfile:
        fieldnames = ['images']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in images_unchanged:
            writer.writerow({'images': r})
