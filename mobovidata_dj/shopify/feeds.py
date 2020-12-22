import cStringIO
import StringIO
import csv
import pandas as pd
import gzip

from celery.utils.log import get_task_logger
from django.core.files import File
from django.db import connections
from django.utils import timezone

from .models import (Feed, MasterAttributeValue, MasterCategory, MasterProduct,
                     Model)

logger = get_task_logger(__name__)


def generate_product_feed(master_feed, store, file_name, rules, delimiter=',',
                          extension='csv', compressed=False):
    # 621.feeds  
    print 'rules ', rules                        
    try:
        dataframe = pd.read_csv(master_feed.file.path,
                                dtype={'barcode': object})
        product_feed = rules(dataframe)
        f = StringIO.StringIO()
        product_feed.to_csv(f, sep=delimiter, index=False)

        obj, created = (Feed.objects
                        .update_or_create(name=file_name,
                                          defaults={
                                              'store': store,
                                              'created_at': timezone.now(),
                                              'error': ''
                                          }))
        file_name = '{}.{}'.format(file_name, extension)
        if compressed:
            f2 = cStringIO.StringIO()
            gzf = gzip.GzipFile(mode='wb', fileobj=f2)
            f.seek(0)
            gzf.write(f.read())
            gzf.close()
            file_name = '{}.gz'.format(file_name)
            obj.file.save(file_name, File(f2))
            f2.close()
        else:
            obj.file.save(file_name, File(f))

    except Exception, ex:
        logger.exception(
            'There was an error while generating product feed task %s',
            ex)
        Feed.objects.update_or_create(name=file_name,
                                      defaults={
                                          'store': store,
                                          'error': ex
                                      })
        raise


def generate_product_feed_we_co(unique_brand_models, top_brand_models,
                                split_rules, store, products, file_name, rules,
                                delimiter=',', extension='csv'):
    try:
        product_feed = []
        for product in products:
            product_rows = split_rules(rules, product, unique_brand_models,
                                       top_brand_models)
            for prod in product_rows:
                product_feed.append(prod)

        if product_feed:
            save_feed(store, product_feed, file_name, delimiter, extension)
    except Exception, ex:
        logger.exception('There was an error while generating product feed task %s',
                         ex)
        Feed.objects.update_or_create(name=file_name,
                                      defaults={
                                          'store': store,
                                          'error': ex
                                      })
        raise


def generate_customer_feed(store, items, file_name, rules,
                         delimiter=',', extension='csv'):
    try:
        feed = []
        models = Model.objects.all().select_related('brand')
        models = {x.collection_handle: x for x in models}
        for item in items:
            item_rows = rules(item, models)
            feed.extend(item_rows)

        if feed:
            save_feed(store, feed, file_name, delimiter, extension,
                      quoting=csv.QUOTE_MINIMAL)
    except Exception, ex:
        logger.exception('There was an error while generating custom feed task %s',
                         ex)
        Feed.objects.update_or_create(name=file_name,
                                      defaults={
                                          'store': store,
                                          'error': ex
                                      })
        raise


def generate_product_feed_mm(store, products, file_name, rules, delimiter=',',
                             extension='csv'):
    try:
        product_feed = []
        for product in products:
            rows = rules(product)
            product_feed.extend(rows)

        if product_feed:
            save_feed(store, product_feed, file_name, delimiter, extension)
    except Exception, ex:
        logger.exception('There was an error while generating product feed task %s',
                         ex)
        Feed.objects.update_or_create(name=file_name,
                                      defaults={
                                          'store': store,
                                          'error': ex
                                      })
        raise


def save_feed(store, feed, file_name, delimiter, extension, quoting=csv.QUOTE_ALL):
    f = cStringIO.StringIO()
    keys = feed[0].keys()

    dict_writer = csv.DictWriter(f, keys, delimiter=delimiter,
                                 quoting=quoting)
    dict_writer.writeheader()
    for row in feed:
        dict_writer.writerow(row)

    obj, created = (Feed.objects
                    .update_or_create(name=file_name,
                                      defaults={
                                          'store': store,
                                          'created_at': timezone.now(),
                                          'error': ''
                                      }))
    file_name = '{}.{}'.format(file_name, extension)
    obj.file.save(file_name, File(f))


def get_brand_models():
    # Pull list of all brand models from magento
    cursor = connections['magento'].cursor()
    cursor.execute("set time_zone='US/Pacific';")
    cursor.execute(
        '''
        select
    cpe.entity_id as entity_id,
    cpe.sku,
    if(
    (LENGTH(REPLACE(cce.path,left(cce.path,4),'')) - LENGTH(replace(REPLACE(cce.path,left(cce.path,4),''),'/','')) +1)>=2,
    concat(ccev.value,'-',ccev2.value),'') as 'brand-model',
    ccev3.value as 'Category',
    ccev4.value as 'Assinged_Category'
    from catalog_product_entity as cpe
    left JOIN catalog_category_product as ccp ON cpe.entity_id = ccp.product_id
    left JOIN catalog_category_entity as cce ON ccp.category_id = cce.entity_id
    left JOIN catalog_category_entity_varchar as ccev ON ccev.entity_id = substring_index(substring_index(cce.path,'/',3),'/',-1) and ccev.attribute_id = 43 and ccev.value !='default-category'
    left JOIN catalog_category_entity_varchar as ccev2 ON ccev2.entity_id = substring_index(substring_index(cce.path,'/',4),'/',-1) and ccev2.attribute_id = 43 and ccev.value !='default-category'
    left JOIN catalog_category_entity_varchar as ccev3 ON ccev3.entity_id = substring_index(substring_index(cce.path,'/',5),'/',-1) and ccev3.attribute_id = 43 and ccev.value !='default-category'
    left JOIN catalog_category_entity_varchar as ccev4 ON ccev4.entity_id = substring_index(substring_index(cce.path,'/',5),'/',-1) and ccev4.attribute_id = 41 and ccev.value !='default-category'
    left JOIN eav_attribute_set as eas ON cpe.attribute_set_id = eas.attribute_set_id
    left JOIN catalog_product_entity_int as cpei on ccp.product_id = cpei.entity_id and cpei.entity_type_id = 4 and cpei.attribute_id = 96 and cpei.store_id = 0
    where cce.path != '1/2'
    And cpe.sku NOT like 'DS-%'
    AND cpe.sku NOT like 'CFP%'
    AND cpe.sku NOT like 'FPA%'
    #AND cpe.sku = 'KYB-APL-AR11-CM02'
    AND cpei.`value`=1 # enabled/disabled filter
    order by cpe.entity_id;
        ''')
    tg_product_ids = [
        {'entity_id': entity_id, 'sku': sku, 'brand_model': brand_model,
         'category': category, 'assigned_category': assigned_category}
        for entity_id, sku, brand_model, category, assigned_category in
        cursor.fetchall()]
    cursor.execute("set time_zone='UTC';")

    # Get unique brand models
    unique_brand_models = set(['bm--%s' % b['brand_model'] for b in tg_product_ids])

    return unique_brand_models


def get_top_brand_models():
    # Get tag names of the top 50 best selling brand models
    cursor = connections['magento'].cursor()
    cursor.execute("set time_zone='US/Pacific';")
    cursor.execute('''
    SELECT
    replace(sales_flat_order_item.brand_model,' -','')  AS brand_model,
    replace(replace(url_path,CONCAT('/',url_key,'.html'),''),'/','-') as top_model
    FROM sales_flat_order_item  AS sales_flat_order_item
    LEFT JOIN sales_flat_order  AS sales_flat_order ON sales_flat_order_item.order_id = sales_flat_order.entity_id
    LEFT JOIN catalog_product_entity  AS catalog_product_entity ON sales_flat_order_item.product_id = catalog_product_entity.entity_id
    LEFT JOIN eav_attribute_set  AS eav_attribute_set ON catalog_product_entity.attribute_set_id = eav_attribute_set.attribute_set_id
    LEFT JOIN catalog_category_flat_store_2 cat ON sales_flat_order_item.added_from_category_id = cat.entity_id
    WHERE (NOT (sales_flat_order_item.price  = 0))
    AND ((((sales_flat_order.created_at ) >= ((CONVERT_TZ(DATE_ADD(DATE(CONVERT_TZ(NOW(),'UTC','America/Los_Angeles')),INTERVAL -29 day),'America/Los_Angeles','UTC'))) AND (sales_flat_order.created_at ) < ((CONVERT_TZ(DATE_ADD(DATE_ADD(DATE(CONVERT_TZ(NOW(),'UTC','America/Los_Angeles')),INTERVAL -29 day),INTERVAL 30 day),'America/Los_Angeles','UTC'))))))
    AND (CASE
    WHEN eav_attribute_set.attribute_set_name regexp 'batteries'  THEN 'Batteries'
    WHEN eav_attribute_set.attribute_set_name regexp 'audio'  THEN 'Bluetooth & Audio'
    WHEN eav_attribute_set.attribute_set_name regexp 'cables'  THEN 'Cables'
    WHEN eav_attribute_set.attribute_set_name regexp 'phone cases'  THEN 'Phone Cases & Covers'
    WHEN eav_attribute_set.attribute_set_name regexp 'wallets'  THEN 'Phone Wallets, Wristlets & Clutches'
    WHEN eav_attribute_set.attribute_set_name regexp 'holders|lanyards'  THEN 'Holders & Mounts'
    WHEN eav_attribute_set.attribute_set_name regexp 'chargers'  THEN 'Chargers'
    WHEN eav_attribute_set.attribute_set_name regexp 'protectors'  THEN 'Screen Protectors'
    WHEN eav_attribute_set.attribute_set_name regexp 'stylus'  THEN 'Stylus Pens'
    WHEN eav_attribute_set.attribute_set_name regexp 'fashion'  THEN 'Fashion'
    WHEN eav_attribute_set.attribute_set_name regexp 'travel'  THEN 'Travel Accessories'
    ELSE 'Other'
    END <> 'Stylus Pens'
    OR CASE
    WHEN eav_attribute_set.attribute_set_name regexp 'batteries'  THEN 'Batteries'
    WHEN eav_attribute_set.attribute_set_name regexp 'audio'  THEN 'Bluetooth & Audio'
    WHEN eav_attribute_set.attribute_set_name regexp 'cables'  THEN 'Cables'
    WHEN eav_attribute_set.attribute_set_name regexp 'phone cases'  THEN 'Phone Cases & Covers'
    WHEN eav_attribute_set.attribute_set_name regexp 'wallets'  THEN 'Phone Wallets, Wristlets & Clutches'
    WHEN eav_attribute_set.attribute_set_name regexp 'holders|lanyards'  THEN 'Holders & Mounts'
    WHEN eav_attribute_set.attribute_set_name regexp 'chargers'  THEN 'Chargers'
    WHEN eav_attribute_set.attribute_set_name regexp 'protectors'  THEN 'Screen Protectors'
    WHEN eav_attribute_set.attribute_set_name regexp 'stylus'  THEN 'Stylus Pens'
    WHEN eav_attribute_set.attribute_set_name regexp 'fashion'  THEN 'Fashion'
    WHEN eav_attribute_set.attribute_set_name regexp 'travel'  THEN 'Travel Accessories'
    ELSE 'Other'
    END IS NULL)
    AND (sales_flat_order.base_grand_total > 0)
    AND (sales_flat_order_item.brand_model is not null)
    GROUP BY 1
    ORDER BY COALESCE(SUM(if(sales_flat_order_item.post_purchase_item = 0, sales_flat_order_item.row_total-sales_flat_order_item.discount_amount, sales_flat_order_item.row_total) ), 0) DESC
    limit 50
    ''')
    top_brand_models = [
        {'top_model': top_model, 'brand_model': brand_model}
        for top_model, brand_model in cursor.fetchall()]
    cursor.execute("set time_zone='UTC';")

    top_brand_models = ['bm--%s' % r['brand_model'] for r in top_brand_models]

    return top_brand_models


# Iterate over tags in a product and return number of rows equal to matched
# collections
def split_product_collection_tags_we(package_function, product,
                                  unique_brand_models, top_brand_models):
    product_rows = []
    tags = [o.name for o in product.producttag_set.all()]
    collections = set(tags).intersection(unique_brand_models)
    # Split product data into column values and return as array of dicts.
    if len(collections) > 44:
        collections = set(tags).intersection(top_brand_models)
    for collection in collections:
        rows = package_function(product, collection.replace('bm--', ''))
        for row in rows:
            product_rows.append(row)
    return product_rows


def split_product_collection_tags_co(package_function, product,
                                  unique_brand_models, top_brand_models):
    product_rows = []
    if (product.productvariant_set.all()
            .filter(inventory_quantity__gt=0)
            .exclude(feed_excluded=True).exists()):
        tags = [o.name for o in product.producttag_set.all()]
        unique_brand_models = Model.objects.all().values_list('collection_handle',
                                                              flat=True)
        unique_brand_models = ['bm--{}'.format(x) for x in unique_brand_models]
        if 'universal-products' in tags:
            collections = unique_brand_models
        elif product.product_type in ['Audio', 'Bluetooth & Audio',
                                      'Phone Cables', 'Phone Chargers', 'Cables']:
            adaptor_types = set([x[0] for x in Model.ADAPTOR_TYPE_CHOICES])
            adaptor_types = set(tags).intersection(adaptor_types)
            unique_brand_models = (Model.objects
                                   .filter(adaptor_type__in=adaptor_types)
                                   .values_list('collection_handle', flat=True))
            collections = ['bm--{}'.format(x) for x in unique_brand_models]
        else:
            collections = set(tags).intersection(unique_brand_models)
        if collections:
            variant = product.productvariant_set.all().exclude(feed_excluded=True).first()
            image = variant.image or product.productimage_set.all().order_by(
                'position').first()
            if image:
                m_products = dict(MasterProduct.objects.all()
                                  .values_list('sku', 'mpid'))
                m_categories = MasterCategory.objects.filter(category_name=product.product_type)
                m_categories = {x.hyphenated_brand_model_name: x for x in m_categories}
                try:
                    color = MasterAttributeValue.objects.get(
                        product__sku=variant.sku, attribute__attribute_code='primary_color').value
                except MasterAttributeValue.DoesNotExist:
                    color = ''
                for collection in collections:
                    rows = package_function(product, variant,
                                            collection.replace('bm--', ''), image,
                                            m_products, m_categories, color)
                    for row in rows:
                        product_rows.append(row)
    return product_rows
