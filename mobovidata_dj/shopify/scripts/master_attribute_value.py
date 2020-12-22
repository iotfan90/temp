from django.db import connections

from mobovidata_dj.shopify.models import MasterAttributeValue, MasterProduct
from mobovidata_dj.shopify.scripts.metafields import (get_product_attrs,
                                                      construct_query)


def save_attributes_values_to_mvd_db(query, products, frontend_input):
    attrs_bulk = []
    cursor = connections['magento'].cursor()
    cursor.execute(query)

    columns = cursor.description
    skus = [{columns[index][0]: column for index, column in enumerate(value)}
            for value in cursor.fetchall()]
    for sku in skus:
        sku_value = sku.pop('sku')
        product = products[sku_value]
        for key, value in sku.iteritems():
            if value:
                attrs_bulk.append(MasterAttributeValue(attribute_code=key,
                                                       product_id=product,
                                                       frontend_input=frontend_input[key],
                                                       value=value))

    # Bulk create for MasterAttributeMapping done in chunks of 1,000 objects.
    chunks = [attrs_bulk[i:i + 1000] for i in
              xrange(0, len(attrs_bulk), 1000)]
    for chunk in chunks:
        MasterAttributeValue.objects.bulk_create(chunk)


def generate_attribute_values():
    try:
        products = dict(MasterProduct.objects.all().values_list('sku', 'id'))
        product_attrs = get_product_attrs()
        frontend_input = {x['attribute_code']: x['frontend_input'] for x in product_attrs}
        # It's allowed up to 60 joins per sql query
        chunks = [product_attrs[i:i + 10] for i in
                  xrange(0, len(product_attrs), 10)]
        for chunk in chunks:
            query = construct_query(chunk)
            save_attributes_values_to_mvd_db(query, products, frontend_input)
    except Exception as e:
        raise


def merge_material_attribute_values():
    try:
        materials = MasterAttributeValue.objects.filter(attribute_code='material').values_list('id', flat=True)
        materials_to_merge = MasterAttributeValue.objects.filter(attribute_code__icontains='material').exclude(id__in=materials)
        for material in materials_to_merge:
            obj, created = (MasterAttributeValue.objects
                          .get_or_create(product=material.product,
                                         attribute_code='material',
                                         defaults={'value': material.value,
                                                   'frontend_input': 'multiselect'}))
            if not created:
                obj.value = '{},{}'.format(obj.value, material.value)
                obj.save()
            material.delete()
    except Exception as e:
        raise


def merge_form_factor_attribute_values():
    try:
        form_factor = MasterAttributeValue.objects.filter(attribute_code='form_factor').values_list('id', flat=True)
        form_factor_to_merge = MasterAttributeValue.objects.filter(attribute_code__icontains='form_factor').exclude(id__in=form_factor)
        for form_factor in form_factor_to_merge:
            obj, created = (MasterAttributeValue.objects
                            .get_or_create(product=form_factor.product,
                                           attribute_code='form_factor',
                                           defaults={'value': form_factor.value,
                                                     'frontend_input': 'multiselect'}))
            if not created:
                obj.value = '{},{}'.format(obj.value, form_factor.value)
                obj.save()
            form_factor.delete()
    except Exception as e:
        raise
