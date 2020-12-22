import json

from django.db import connections

from mobovidata_dj.shopify.models import (MasterCategory, MetadataCollection,
                                          MetadataCollectionAttribute, Store)


def get_master_categories():
    cursor = connections['magento'].cursor()
    cursor.execute('''
        SELECT
        Cat.entity_id as 'mcid',
        Brand.name as 'brand_name',
        Model.name as 'model_name',
        concat(Brand.name,' ',Model.name) as 'brand_model_name',
        Cat.name as 'category_name',
        Brand.url_key 'brand_url',
        Model.url_key 'model_url',
        concat(Brand.url_key,' ',Model.url_key) as 'brand_model_url',
        Cat.url_key as 'category_url'
        FROM catalog_category_flat_store_2 as Cat
        LEFT JOIN catalog_category_flat_store_2 as Model ON Cat.parent_id = Model.entity_id
        LEFT JOIN catalog_category_flat_store_2 as Brand ON Model.parent_id = Brand.entity_id
        WHERE Cat.level = 4
        AND Brand.name != 'Default Category'
        AND Brand.name != 'Phone Cases & Covers'
        AND Brand.name != 'Phone Wallets, Wristlets & Clutches'
        AND Brand.name != 'Screen Protectors'
        AND Brand.name != 'Phone Chargers'
        AND Brand.name != 'Cell Phones & Tablets'
        AND Brand.name != 'Phone Cables'
        AND Brand.name != 'Replacement Batteries and Power Banks'
        AND Brand.name != 'Phone Holders, Holsters & Belt Clips'
        AND Brand.name != 'Bluetooth & Audio'
        AND Brand.name != 'Custom Cases'
        AND Brand.name != 'Universal Accessories'
        AND Brand.name != 'New Products'
        AND Brand.name != 'Travel'
        AND Brand.name != 'Fitness & Wearable'
        AND Brand.name != 'Selfie, Dash Cams And Photography'
        AND Brand.name != 'Clearance'
        AND Brand.name != 'Bundles'
        AND Brand.name != 'Automotive, Marine & GPS'
        AND Brand.name != 'Portable & Personal Electronics'
        AND Brand.name != 'Computer Peripherals & Home Office'
        AND Brand.name != 'Data Storage & Memory'
        AND Brand.name != 'Handbags & Fashion Accessories'
        AND Brand.name != 'Outdoor & Recreation'
        AND Brand.name != 'Universal Products'
        AND Brand.name != 'Bluetooth'
        AND Brand.name != 'Tech Toys'
        AND Brand.name != 'Officially Licensed Products'
        AND Brand.name != 'TEST'
        AND Brand.name != 'Chargers'
        AND Brand.name != 'Cables'
        AND Brand.name != 'CLEARANCE'
        ORDER BY 2,3;
        ''')

    columns = cursor.description
    categories = [
        {columns[index][0]: column for index, column in enumerate(value)} for
        value in cursor.fetchall()]

    return categories


def save_categories_to_mvd_db(categories):
    c = []
    for category in categories:
        c.append(MasterCategory(**category))

    MasterCategory.objects.bulk_create(c)


def generate_categories():
    try:
        categories = get_master_categories()
        save_categories_to_mvd_db(categories)
    except Exception as e:
        raise


def populate_hyphenated_brand_model_field():
    categories = MasterCategory.objects.all()
    for category in categories:
        hypenated = category.brand_model_name.lower().replace(' ', '-')
        category.hyphenated_brand_model_name = hypenated
        category.save()


def generate_collection_metafields():
    try:
        stores = Store.objects.filter(identifier__in=['shopify-we', 'shopify-co'])
        for store in stores:
            master_categories = MasterCategory.objects.all().values_list(
                    'brand_model_name', 'category_name', 'mcid')
            attributes = {}
            for category in master_categories:
                if category[0] in attributes:
                    attributes[category[0]][category[1]] = category[2]
                else:
                    attributes[category[0]] = {category[1]: category[2]}
            bulk_m_a = []
            for key in attributes.keys():
                metafield_value = json.dumps(attributes[key])
                m_c_obj = MetadataCollection(store=store, name=key)
                m_c_obj.save()
                m = MetadataCollectionAttribute(collection_metadata=m_c_obj,
                                                key='master_categories',
                                                value=metafield_value,
                                                m_type=MetadataCollectionAttribute.MASTER_CATEGORIES,
                                                namespace=MetadataCollectionAttribute.MASTER_CATEGORIES)
                bulk_m_a.append(m)
            MetadataCollectionAttribute.objects.bulk_create(bulk_m_a)
    except Exception as ex:
        raise


def add_agnostic_categories():
    categories = [
        {'category_name': 'Keyboards & Keypads',
         'category_url': 'keyboards-keypads', 'mcid': 48894},
        {'category_name': 'Mice & Mouse Pads',
         'category_url': 'mice-mouse-pads', 'mcid': 48895},
        {'category_name': 'Office Supplies', 'category_url': 'office-supplies',
         'mcid': 48897},
        {'category_name': 'NBA', 'category_url': 'nba', 'mcid': 49267},
        {'category_name': 'NFL', 'category_url': 'nfl', 'mcid': 49268},
        {'category_name': 'MLB', 'category_url': 'mlb', 'mcid': 49270},
        {'category_name': 'Gaming & VR', 'category_url': 'gaming-vr',
         'mcid': 49111},
        {'category_name': 'iPads & Tablets Accessories',
        'category_url': 'ipads-tablets-accessories', 'mcid': 48883},
        {'category_name': 'Personal Audio & Video Products',
         'category_url': 'personal-a-v-components', 'mcid': 48885},
        {'category_name': 'New Products', 'category_url': 'new-products',
         'mcid': 39484},
        {'category_name': 'Travel', 'category_url': 'travel-accessories',
         'mcid': 39845},
        {'category_name': 'Fitness & Wearable',
         'category_url': 'fitness-wearable-accessories', 'mcid': 39846},
        {'category_name': 'Selfie, Dash Cams And Photography',
         'category_url': 'selfie-camera-photography-accessories',
         'mcid': 39847},
        {'category_name': 'Clearance', 'category_url': 'clearance',
         'mcid': 39848},
        {'category_name': 'Tech Toys', 'category_url': 'tech-toys',
         'mcid': 49265},
        {'category_name': 'Data Storage & Memory',
         'category_url': 'data-storage-memory', 'mcid': 48872},
        {'category_name': 'Handbags & Fashion Accessories',
         'category_url': 'handbags-fashion-accessories', 'mcid': 48873},
        {'category_name': 'Stocking Stuffers',
         'category_url': 'stocking-stuffers', 'mcid': 54651}
    ]
    for category in categories:
        obj = MasterCategory(**category)
        obj.save()
