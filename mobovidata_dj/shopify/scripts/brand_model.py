from django.db import connections

from mobovidata_dj.shopify.models import Model


def get_sku_add_on():
    cursor = connections['magento'].cursor()
    cursor.execute('''
        select
        cpe.entity_id as entity_id,
        cpe.sku,

        if(
        (LENGTH(REPLACE(cce.path,left(cce.path,4),'')) - LENGTH(replace(REPLACE(cce.path,left(cce.path,4),''),'/','')) +1)>=2,
        concat(ccev.value,'-',ccev2.value),'') as 'brand-model'


        from catalog_product_entity as cpe
        left JOIN catalog_category_product as ccp ON cpe.entity_id = ccp.product_id
        left JOIN catalog_category_entity as cce ON ccp.category_id = cce.entity_id
        left JOIN catalog_category_entity_varchar as ccev ON ccev.entity_id = substring_index(substring_index(cce.path,'/',3),'/',-1) and ccev.attribute_id = 43 and ccev.value !='default-category'
        left JOIN catalog_category_entity_varchar as ccev2 ON ccev2.entity_id = substring_index(substring_index(cce.path,'/',4),'/',-1) and ccev2.attribute_id = 43 and ccev.value !='default-category'
        left JOIN catalog_category_entity_varchar as ccev3 ON ccev3.entity_id = substring_index(substring_index(cce.path,'/',5),'/',-1) and ccev3.attribute_id = 43 and ccev.value !='default-category'
        left JOIN catalog_category_entity_varchar as ccev4 ON ccev4.entity_id = substring_index(substring_index(cce.path,'/',5),'/',-1) and ccev4.attribute_id = 41 and ccev.value !='default-category'
        left JOIN eav_attribute_set as eas ON cpe.attribute_set_id = eas.attribute_set_id
        left JOIN catalog_product_entity_int as cpei on ccp.product_id = cpei.entity_id and cpei.entity_type_id = 4 and cpei.attribute_id = 96 and cpei.store_id = 0

        where eas.attribute_set_name = 'Screen Protectors'
        AND ccev4.value = 'Screen Protectors'
        AND cce.path != '1/2'
        AND (cpe.sku REGEXP '^SCR-' and cpe.sku REGEXP '-01$')
        ''')

    columns = cursor.description
    query = [
        {columns[index][0]: column for index, column in enumerate(value)} for
        value in cursor.fetchall()]

    return query


def save_sku_add_on_to_mvd_db(skus):
    models = Model.objects.all()
    models = {x.collection_handle: x for x in models}

    for sku in skus:
        try:
            model = models[sku['brand-model']]
        except KeyError:
            print sku['brand-model']
            continue
        model.sku_add_on = sku['sku']
        model.save()


def generate_sku_add_on():
    try:
        skus = get_sku_add_on()
        save_sku_add_on_to_mvd_db(skus)
    except Exception as e:
        raise
