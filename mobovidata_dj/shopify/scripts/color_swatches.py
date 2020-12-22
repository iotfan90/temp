from django.db import connections

from mobovidata_dj.shopify.models import (ProductExtraInfo, ProductVariant,
                                          Store)
from modjento.models import CatalogProductLink


def get_colors():
    cursor = connections['magento'].cursor()
    cursor.execute('''
        SELECT
        cpe.entity_id,
        cpe.sku,
        color_picker.value AS 'color'
        FROM catalog_product_entity AS cpe
        LEFT JOIN (SELECT  a.attribute_id, a.entity_id, b.value
                    FROM catalog_product_entity_int AS a
                    LEFT JOIN eav_attribute_option_value AS b ON b.option_id = a.value and b.store_id = 0
                    WHERE a.store_id = 0 AND a.attribute_id = 423) AS color_picker ON color_picker.entity_id = cpe.entity_id
        WHERE color_picker.value IS NOT NULL;
        ''')

    columns = cursor.description
    colors = [
        {columns[index][0]: column for index, column in enumerate(value)} for
        value in cursor.fetchall()]

    return colors


def save_colors_to_mvd_db(store, colors):
    counter = 0
    co_variants = ProductVariant.objects.filter(product__store=store).select_related('product')
    products = {}
    for variant in co_variants:
        products[variant.sku] = variant.product

    for color in colors:
        try:
            p_e = ProductExtraInfo(product=products[color['sku']], color=color['color'])
            p_e.save()
        except KeyError:
            counter += 1
            continue

        # Save m2m associated products
        associated_ps = CatalogProductLink.objects.filter(
            product__entity_id=color['entity_id'],
            link_type__link_type_id=6).values_list('linked_product__sku',
                                                   flat=True)
        p = []
        for associated_p in associated_ps:
            try:
                p.append(products[associated_p])
            except KeyError:
                continue
        p_e.associated_products.add(*p)


def generate_colors():
    try:
        try:
            store = Store.objects.get(identifier='shopify-co')
            products = get_colors()
            save_colors_to_mvd_db(store, products)
            pass
        except Store.DoesNotExist:
            pass
    except Exception as e:
        raise
