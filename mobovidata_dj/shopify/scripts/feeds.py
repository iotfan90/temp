import csv
import pandas as pd

from mobovidata_dj.shopify.models import (Product, ProductVariant, Model,
                                          MasterCategory)


def check_missing_skus(master_file_path, output_folder, shopify_report_path=None):
    master_feed = pd.read_csv(master_file_path,
                              sep='\t')
    # Stick only with SKU column
    master_feed = master_feed[['mpn', ]]
    skus_on_feed = set(master_feed['mpn'].tolist())
    if not shopify_report_path:
        total_skus = ProductVariant.objects.filter(product__store__identifier='shopify-co').exclude(sku='').values_list('sku', flat=True)
    else:
        shopify_report = pd.read_csv(shopify_report_path)
        # Stick only with SKU column
        shopify_report = shopify_report[['Variant SKU', ]]
        total_skus = set(shopify_report['Variant SKU'].tolist())

    missing_skus = set(total_skus).difference(skus_on_feed)
    resolved = []
    unresolved = []

    for sku in missing_skus:
        item = {'sku': sku}

        # Check if product exists
        if not Product.objects.filter(store__identifier='shopify-co', productvariant__sku=sku).exists():
            item['error'] = 'sku not found on MVD DB'
            resolved.append(item)
            continue

        # Check not published
        if not Product.objects.filter(store__identifier='shopify-co', published_at__isnull=False, productvariant__sku=sku).exists():
            item['error'] = 'sku not published (published_at attribute is None)'
            resolved.append(item)
            continue

        # Check if there is a interesction of collections
        product = Product.objects.get(store__identifier='shopify-co', published_at__isnull=False, productvariant__sku=sku)
        tags = [o.name for o in product.producttag_set.all()]
        unique_brand_models = Model.objects.all().values_list('collection_handle', flat=True)
        unique_brand_models = ['bm--{}'.format(x) for x in unique_brand_models]
        if 'universal-products' in tags:
            collections = unique_brand_models
        elif product.product_type in ['Audio', 'Bluetooth & Audio', 'Phone Cables', 'Phone Chargers', 'Cables']:
            adaptor_types = set([x[0] for x in Model.ADAPTOR_TYPE_CHOICES])
            adaptor_types = set(tags).intersection(adaptor_types)
            unique_brand_models = (Model.objects
                                   .filter(adaptor_type__in=adaptor_types)
                                   .values_list('collection_handle', flat=True))
            collections = ['bm--{}'.format(x) for x in unique_brand_models]
        else:
            collections = set(tags).intersection(unique_brand_models)
        if not collections:
            if product.product_type in ['Audio', 'Bluetooth & Audio', 'Phone Cables', 'Phone Chargers', 'Cables']:
                item['error'] = 'no collections found (No adaptor type inside tags). Product Type:{}. Tags:{}'.format(product.product_type, tags)
            else:
                item['error'] = 'no collections found. Product Type:{}. Tags:{}'.format(product.product_type, tags)
            resolved.append(item)
            continue

        # Check if variant is not excluded
        variant = product.productvariant_set.all().exclude(feed_excluded=True).first()
        if not variant:
            item['error'] = 'variant excluded'
            resolved.append(item)
            continue

        # Check if sku has an image
        image = variant.image or product.productimage_set.all().order_by('position').first()
        if not image:
            item['error'] = 'no sku image provided'
            resolved.append(item)
            continue

        # Check if master category exists
        m_categories = MasterCategory.objects.filter(category_name=product.product_type)
        m_categories = {x.hyphenated_brand_model_name: x for x in m_categories}
        at_least_one_category = False
        collections = [x.replace('bm--', '') for x in collections]
        for collection in collections:
            try:
                m_categories[collection]
                at_least_one_category = True
            except KeyError:
                continue
        if not at_least_one_category:
            item['error'] = 'no hyphenated_brand_model_name matches any of the collections. PROCEDURE: We get all master categories for this product filtering (master_category.category_name=product.product_type). Then we match hyphenated_brand_model_name with the collections. Product Type:{}. Collections:{}'.format(product.product_type, collections)
            resolved.append(item)
            continue
        item['error'] = 'still unresolved'
        unresolved.append(item)

    # Write resolved SKUs
    output_file = output_folder + 'missing_skus_resolved.csv'
    with open(output_file, 'wb') as csvfile:
        fieldnames = ['sku', 'error']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in resolved:
            writer.writerow(r)

    # Write unresolved SKUs
    output_file = output_folder + 'missing_skus_unresolved.csv'
    with open(output_file, 'wb') as csvfile:
        fieldnames = ['sku', 'error']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in unresolved:
            writer.writerow(r)
