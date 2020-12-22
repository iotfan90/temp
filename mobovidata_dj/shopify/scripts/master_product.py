from django.db import connections

from mobovidata_dj.shopify.models import (MasterProduct, MetadataProduct,
                                          MetadataProductAttribute, Store)


def get_master_products():
    cursor = connections['magento'].cursor()
    cursor.execute('''
        SELECT
        entity_id as 'mpid',
        attribute_set_id,
        sku,
        DATE(CONVERT_TZ(created_at ,'UTC','America/Los_Angeles')) AS created_at
        FROM catalog_product_entity;
        ''')

    columns = cursor.description
    products = [
        {columns[index][0]: column for index, column in enumerate(value)} for
        value in cursor.fetchall()]

    return products


def save_products_to_mvd_db(products):
    c = []
    for product in products:
        c.append(MasterProduct(**product))

    MasterProduct.objects.bulk_create(c)


def generate_products():
    try:
        products = get_master_products()
        save_products_to_mvd_db(products)
    except Exception as e:
        raise


def generate_master_product_metafields():
    try:
        stores = Store.objects.filter(identifier__in=['shopify-we', 'shopify-co'])
        for store in stores:
            master_products = MasterProduct.objects.all().values_list('sku',
                                                                      'mpid')
            bulk_m_a = []
            m_ps = dict(MetadataProduct.objects.filter(store=store).values_list('sku', 'id'))
            for product in master_products:
                sku = product[0]

                if sku in m_ps:
                    m_p_obj = m_ps[sku]
                else:
                    m_p_obj = MetadataProduct(store=store, sku=sku)
                    m_p_obj.save()
                    m_p_obj = m_p_obj.id

                m = MetadataProductAttribute(product_metadata_id=m_p_obj,
                                             key='master_product',
                                             value=product[1],
                                             m_type=MetadataProductAttribute.MASTER_PRODUCT,
                                             namespace=MetadataProductAttribute.MASTER_PRODUCT)
                bulk_m_a.append(m)
            chunks = [bulk_m_a[i:i + 1000] for i in xrange(0, len(bulk_m_a), 1000)]
            for chunk in chunks:
                MetadataProductAttribute.objects.bulk_create(chunk)
    except Exception as ex:
        raise
