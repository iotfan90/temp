from django.db import connections

from mobovidata_dj.shopify.models import MasterAttributeMapping


def get_master_attributes_mapping():
    cursor = connections['magento'].cursor()
    cursor.execute('''
        SELECT
        s.attribute_set_id as 'attribute_set_id_old',
        s.attribute_set_name,
        g.attribute_group_name,
        a.attribute_code,
        a.frontend_label,
        ea.sort_order
        FROM eav_attribute_set s
        LEFT JOIN eav_attribute_group g   ON s.attribute_set_id   = g.attribute_set_id
        LEFT JOIN eav_entity_attribute ea ON g.attribute_group_id = ea.attribute_group_id
        LEFT JOIN eav_attribute a         ON ea.attribute_id      = a.attribute_id
        WHERE s.entity_type_id = 4
        AND s.attribute_set_name != 'Default'
        AND g.attribute_group_name !='General'
        ORDER BY s.attribute_set_name, g.sort_order, ea.sort_order;
        ''')

    columns = cursor.description
    attribute_set = [
        {columns[index][0]: column for index, column in enumerate(value)} for
        value in cursor.fetchall()]

    return attribute_set


def save_attribute_mapping_to_mvd_db(attributes):
    c = []
    for attribute in attributes:
        if 'material' in attribute['frontend_label'].lower():
            attribute['attribute_code'] = 'material'
        c.append(MasterAttributeMapping(**attribute))

    MasterAttributeMapping.objects.bulk_create(c)


def generate_attribute_mapping():
    try:
        attributes = get_master_attributes_mapping()
        save_attribute_mapping_to_mvd_db(attributes)
    except Exception as e:
        raise


def merge_form_factor_attribute_mapping():
    try:
        (MasterAttributeMapping.objects
         .filter(attribute_code__icontains='form_factor')
         .update(attribute_code='form_factor', frontend_label='Form Factor'))
    except Exception as e:
        raise
