from django.db import connections

from mobovidata_dj.shopify.models import (MasterAttributeMapping,
                                          MasterAttributeSet, MasterProduct)


def get_master_attributes_set():
    cursor = connections['magento'].cursor()
    cursor.execute('''
        SELECT attribute_set_id, attribute_set_name
        FROM eav_attribute_set
        WHERE entity_type_id = 4;
        ''')

    columns = cursor.description
    rows = [
        {columns[index][0]: column for index, column in enumerate(value)} for
        value in cursor.fetchall()]

    return rows


def save_attribute_set_to_mvd_db(attributes):
    for attribute in attributes:
        obj = MasterAttributeSet(**attribute)
        obj.save()
        (MasterProduct.objects
         .filter(attribute_set_id_old=obj.attribute_set_id)
         .update(attribute_set=obj))
        (MasterAttributeMapping.objects
         .filter(attribute_set_id_old=obj.attribute_set_id)
         .update(attribute_set=obj))


def generate_attribute_set():
    try:
        attributes = get_master_attributes_set()
        save_attribute_set_to_mvd_db(attributes)
    except Exception as e:
        raise
