from django.db import connections

from mobovidata_dj.shopify.models import (MasterAttribute,
                                          MasterAttributeMapping,
                                          MasterAttributeValue)


def get_master_attributes():
    cursor = connections['magento'].cursor()
    cursor.execute('''
        SELECT *
        FROM eav_attribute
        WHERE entity_type_id = 4 ;
        ''')

    columns = cursor.description
    attribute_set = [
        {columns[index][0]: column for index, column in enumerate(value)} for
        value in cursor.fetchall()]

    return attribute_set


def save_attributes_to_mvd_db(attributes):
    for attribute in attributes:
        obj = MasterAttribute(**attribute)
        obj.save()

        (MasterAttributeMapping.objects
         .filter(attribute_code=obj.attribute_code)
         .update(attribute=obj))
        (MasterAttributeValue.objects
         .filter(attribute_code=obj.attribute_code)
         .update(attribute=obj))


def generate_attributes():
    try:
        attributes = get_master_attributes()
        save_attributes_to_mvd_db(attributes)
    except Exception as e:
        raise
