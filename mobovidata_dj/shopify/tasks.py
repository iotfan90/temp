import boto3
import cStringIO
import csv
import json
import pysftp
import urllib2

from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import date, timedelta
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.db import transaction
from django.utils import timezone
from ftplib import FTP

from .api_processing import (ProcessMetafields, ProcessOrders, ProcessPages,
                             ProcessProducts, ProcessSmartCollections)
from .connect import ShopifyConnect
from .exception import ShopifyTransactionException
from .models import (Customer, Feed, InventorySupplierMapping, InventoryUpdateFile,
                     InventoryUpdateLog, MasterCategory, MasterProduct,
                     MetadataCollectionAttribute, MetadataProduct,
                     MetadataProductAttribute, Model, Product, ProductVariant,
                     ShopifyTransaction, SmartCollection, Store)
from .feeds import (generate_customer_feed, generate_product_feed_mm,
                    generate_product_feed_we_co, get_brand_models,
                    get_top_brand_models, split_product_collection_tags_co,
                    split_product_collection_tags_we, generate_product_feed)
from .feed_rules import (package_customer_co, package_product_co_bing,
                         package_product_co_connexity_shopzilla,
                         package_product_co_dy, package_product_co_ebay,
                         package_product_co_fb, package_product_co_google,
                         package_product_co_master,
                         package_product_co_pepperjam,
                         package_product_co_yahoo_gemini_dpa,
                         package_product_co_zaius, package_product_we_dy,
                         package_product_we_fb, package_product_we_google,
                         package_product_mm_google_shopping,
                         package_product_mm_fb_dpa,
                         package_product_mm_fb_prospecting,
                         package_product_mm_dy)
from .transaction import process_transaction
from .utils import (ShopifyMVD, generate_brand_model_js_file,
                    generate_brand_model_images_js_file,
                    generate_collection_attrs_from_model,
                    remove_duplicates_by_store, update_collection_metafield)
from modjento.models import CataloginventoryStockItem, CatalogProductEntity

logger = get_task_logger(__name__)


@shared_task(ignore_results=True)
def update_shopify_inventory():
    """
    Updates mobovida SKU inventory on shopify.com
    """
    # Get mobovida entity_ids
    mobovida_id_skus = CatalogProductEntity.objects.filter(sku__startswith='MOB-').values('entity_id', 'sku')
    mobovida_id_skus = [r for r in mobovida_id_skus]
    mobovida_inventory = CataloginventoryStockItem.objects.filter(
        product_id__in=[s['entity_id'] for s in mobovida_id_skus]
    ).values('product_id', 'qty')
    mobovida_inventory = {r['product_id']: r['qty'] for r in mobovida_inventory}
    for r in mobovida_id_skus:
        r.update({'qty': int(mobovida_inventory.get(r['entity_id']))})
    rg_mobovida_id_skus = {r['sku']: r['qty'] for r in mobovida_id_skus}

    # Get all variant IDs from shopify (or check cache)
    all_products = cache.get('shopifySkus')
    if not all_products:
        all_products = []
        multivars = []
        for i in xrange(1, 20):
            print 'Getting page %s' % i
            products = ShopifyMVD().get_products(fields=['id', 'handle', 'variants'], page=i, limit=250)
            if len(products['products']) == 0:
                print 'done!'
                break
            for p in products['products']:
                product_info = {'id': p['id'], 'handle': p['handle']}
                if len(p['variants']) == 1:
                    product_info.update({'variant_id': p['variants'][0]['id'],
                                         'sku': p['variants'][0]['sku'],
                                         'inventory_mgmt': p['variants'][0]['inventory_management']})
                    all_products.append(product_info)
                else:
                    product_info['vars'] = p['variants']
                    multivars.append(product_info)
        cache.set('shopifySkus', all_products, 60*60*24)
    for r in all_products:
        r.update({'qty': rg_mobovida_id_skus.get(r['sku'])})

    # Pass qtys to Shopify
    for r in all_products:
        try:
            ShopifyMVD().update_inventory(r['variant_id'], r['qty'])
        except OSError as ex:
            logger.exception('Product with id %s reaches max tries',
                             r.get('id'))


@shared_task(ignore_results=True)
# @transaction.atomic
def get_shopify_products():
    stores = Store.objects.all()

    for store in stores:
        shopify = ShopifyConnect(store)

        try:
            product_qty = shopify.get_products_total_quantity(
                updated_at_min=store.product_task_run_at)['count']
            total_pages = -(-product_qty // 250)
            last_run = timezone.now()
            products = []

            for page in xrange(1, total_pages+1):
                response = shopify.get_products(page=page,
                                                updated_at_min=store.product_task_run_at)
                products.extend(response['products'])

            process = ProcessProducts(store, products)
            process.parse_products()

            store.product_task_run_at = last_run
            store.save()
        except Exception, ex:
            logger.exception('There was an error while executing shopify task %s',
                             ex)
            raise


@shared_task(ignore_results=True)
@transaction.atomic
def get_shopify_smart_collections():
    stores = Store.objects.all()

    for store in stores:
        shopify = ShopifyConnect(store)

        try:
            collection_qty = shopify.get_smart_colletions_total_quantity(
                updated_at_min=store.collection_task_run_at)['count']
            total_pages = -(-collection_qty // 250)
            last_run = timezone.now()
            collections = []

            for page in xrange(1, total_pages+1):
                response = shopify.get_smart_collections(page=page,
                                                         updated_at_min=store.collection_task_run_at)
                collections.extend(response['smart_collections'])

            process = ProcessSmartCollections(store, collections)
            process.parse_smart_collections()

            store.collection_task_run_at = last_run
            store.save()
        except Exception, ex:
            logger.exception('There was an error while executing shopify task %s',
                             ex)
            raise


@shared_task(ignore_results=True)
@transaction.atomic
def get_shopify_pages():
    stores = Store.objects.all()

    for store in stores:
        shopify = ShopifyConnect(store)

        try:
            qty = shopify.get_pages_total_quantity(
                updated_at_min=store.pages_task_run_at)['count']
            total_pages = -(-qty // 250)
            last_run = timezone.now()
            pages = []

            for page in xrange(1, total_pages+1):
                response = shopify.get_pages(page=page,
                                             updated_at_min=store.pages_task_run_at)
                pages.extend(response['pages'])

            process = ProcessPages(store, pages)
            process.parse_pages()

            store.pages_task_run_at = last_run
            store.save()
        except Exception, ex:
            logger.exception('There was an error while executing shopify task %s',
                             ex)
            raise


@shared_task(ignore_results=True)
def generate_we_product_feeds():
    try:
        unique_brand_models = get_brand_models()
        top_brand_models = get_top_brand_models()
    except Exception, ex:
        logger.exception(
            'There was an error while generating product feed task %s',
            ex)
        raise

    # Wireless Emporium
    try:
        store_we = Store.objects.get(identifier='shopify-we')
        products = Product.objects.filter(store=store_we,
                                          published_at__isnull=False)
        generate_product_feed_we_co(unique_brand_models, top_brand_models,
                                    split_product_collection_tags_we, store_we,
                                    products, 'shopify-we-dy-feed',
                                    package_product_we_dy)
        generate_product_feed_we_co(unique_brand_models, top_brand_models,
                                    split_product_collection_tags_we, store_we,
                                    products, 'shopify-we-facebook-feed',
                                    package_product_we_fb)
        generate_product_feed_we_co(unique_brand_models, top_brand_models,
                                    split_product_collection_tags_we, store_we,
                                    products, 'shopify-we-google_feed',
                                    package_product_we_google, delimiter='\t',
                                    extension='txt')
    except Store.DoesNotExist:
        pass


@shared_task(ignore_results=True)
def generate_mm_product_feeds():
    # Miss minx
    try:
        store_mm = Store.objects.get(identifier='shopify-mm')
        products = (Product.objects
                    .filter(store=store_mm, published_at__isnull=False)
                    .exclude(product_type__icontains='gift'))
        generate_product_feed_mm(store_mm, products, 'shopify-mm-google-shopping',
                                 package_product_mm_google_shopping,
                                 delimiter='\t', extension='txt')
        generate_product_feed_mm(store_mm, products, 'shopify-mm-fb-dpa',
                                 package_product_mm_fb_dpa,
                                 delimiter='\t', extension='txt')
        generate_product_feed_mm(store_mm, products, 'shopify-mm-fb-prospecting',
                                 package_product_mm_fb_prospecting,
                                 delimiter='\t', extension='txt')
        generate_product_feed_mm(store_mm, products, 'shopify-mm-dy',
                                 package_product_mm_dy)
    except Store.DoesNotExist:
        pass


@shared_task(ignore_results=True)
def generate_co_master_product_feed():
    try:
        store_co = Store.objects.get(identifier='shopify-co')
        products = Product.objects.filter(store=store_co,
                                          published_at__isnull=False)
        generate_product_feed_we_co(None, None,
                                    split_product_collection_tags_co, store_co,
                                    products, 'shopify-co-master-feed',
                                    package_product_co_master)
    except Store.DoesNotExist:
        pass

# generate_co_master_product_feed() 

@shared_task(ignore_results=True)
def generate_co_product_feeds():
    try:
        store_co = Store.objects.get(identifier='shopify-co')
        master = Feed.objects.get(store__identifier='shopify-co',
                                  name='shopify-co-master-feed')
        generate_product_feed(master, store_co, 'shopify-co-facebook-feed',
                              package_product_co_fb)
        generate_product_feed(master, store_co, 'shopify-co-google-feed',
                              package_product_co_google, compressed=True,
                              delimiter='\t', extension='txt')
        generate_product_feed(master, store_co, 'shopify-co-google-feed-txt',
                              package_product_co_google, delimiter='\t',
                              extension='txt')
        generate_product_feed(master, store_co, 'shopify-co-bing-feed',
                              package_product_co_bing,
                              delimiter='\t', extension='txt')
        generate_product_feed(master, store_co,
                              'shopify-co-connexity-shopzilla-feed',
                              package_product_co_connexity_shopzilla,
                              delimiter='\t', extension='txt')
        generate_product_feed(master, store_co, 'shopify-co-dy-feed',
                              package_product_co_dy, delimiter='\t')
        generate_product_feed(master, store_co, 'shopify-co-ebay-feed-text',
                              package_product_co_ebay, extension='txt')
        generate_product_feed(master, store_co,
                              'shopify-co-ebay-feed-compressed',
                              package_product_co_ebay, compressed=True,
                              extension='txt')
        generate_product_feed(master, store_co,
                              'shopify-co-pepperjam-feed',
                              package_product_co_pepperjam,
                              delimiter='\t', extension='txt')
        generate_product_feed(master, store_co,
                              'shopify-co-yahoo-gemini-dpa-feed',
                              package_product_co_yahoo_gemini_dpa,
                              delimiter='\t', extension='txt')
        generate_product_feed(master, store_co, 'shopify-co-zaius-feed',
                              package_product_co_zaius)
    except Store.DoesNotExist:
        pass
    except Feed.DoesNotExist:
        pass
# generate_co_product_feeds()

@shared_task(ignore_results=True)
def generate_co_customer_feed():
    try:
        store_co = Store.objects.get(identifier='shopify-co')
        customers = (Customer.objects
                     .filter(store=store_co)
                     .prefetch_related('order_set'))
        generate_customer_feed(store_co, customers, 'shopify-co-customer-feed',
                               package_customer_co, delimiter='\t',
                               extension='csv')
    except Store.DoesNotExist:
        pass


@shared_task(ignore_results=True)
def upload_customer_feed_retention_science():
    try:
        feed = Feed.objects.get(store__identifier='shopify-co',
                                name='shopify-co-customer-feed')
        filename = './users_{}.tsv'.format(timezone.now().strftime('%Y-%m-%d'))

        host = settings.RETENTIONSCIENCE['host']
        username = settings.RETENTIONSCIENCE['user']
        password = settings.RETENTIONSCIENCE['password']

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None

        with pysftp.Connection(host, username=username, password=password,
                               cnopts=cnopts) as sftp:
            sftp.put(feed.file.path, filename)

    except Exception as ex:
        logger.exception('There was an error while uploading customer feed to RetentionScience %s', ex)
        raise


@shared_task(ignore_results=True)
def upload_brand_model_js_to_shopify():
    try:
        # ##################### Wireless Emporium #####################
        try:
            store_we = Store.objects.get(identifier='shopify-we')
            shopify_we = ShopifyConnect(store_we)

            # Get theme ID
            themes = shopify_we.get_themes()
            theme_id = next((theme['id'] for theme in themes['themes'] if theme['role'] == 'main'), None)
            if not theme_id:
                raise Exception("There is not published theme on the shopify store")
            # Build asset
            attributes = {'key': 'assets/brandModelDict.js',
                          'value': generate_brand_model_js_file()
                          }
            shopify_we.create_update_asset(theme_id, attributes)
        except Store.DoesNotExist:
            pass
        # ##################### Cellular Outfitter #####################
        try:
            store_co = Store.objects.get(identifier='shopify-co')
            shopify_co = ShopifyConnect(store_co)
            # Get theme ID
            themes = shopify_co.get_themes()
            theme_id = next((theme['id'] for theme in themes['themes'] if theme['role'] == 'main'), None)
            if not theme_id:
                raise Exception("There is not published theme on the shopify store")
            # Build asset
            attributes = {'key': 'assets/brandModelDict.js',
                          'value': generate_brand_model_js_file()
                          }
            shopify_co.create_update_asset(theme_id, attributes)
        except Store.DoesNotExist:
            pass
    except Exception, ex:
        logger.exception('There was an error while uploading js file to Shopify %s',
                         ex)
        raise


def upload_brand_model_images_js_to_shopify():
    try:
        try:
            store_co = Store.objects.get(identifier='shopify-co')
            shopify_co = ShopifyConnect(store_co)
            # Get theme ID
            themes = shopify_co.get_themes()
            theme_id = next((theme['id'] for theme in themes['themes'] if theme['role'] == 'main'), None)
            if not theme_id:
                raise Exception("There is not published theme on the shopify store")
            # Build asset
            attributes = {'key': 'assets/brand_model_images.js',
                          'value': generate_brand_model_images_js_file()
                          }
            shopify_co.create_update_asset(theme_id, attributes)
        except Store.DoesNotExist:
            pass
    except Exception, ex:
        logger.exception('There was an error while uploading js file to Shopify %s',
                         ex)
        raise


@shared_task(ignore_results=True)
def update_shopify_collections():
    update_shopify_collections_by_store_we()
    update_shopify_collections_by_store_co()


def update_shopify_collections_by_store_we():
    try:
        store = Store.objects.get(identifier='shopify-we')
    except Store.DoesNotExist:
        return
    models = Model.objects.filter(synced_we=False)
    shopify = ShopifyConnect(store)

    try:
        for model in models:
            try:
                collection = SmartCollection.objects.get(store=store,
                                                         handle=model.collection_handle)
            except SmartCollection.DoesNotExist:
                model.error_we = ("It doesn't exists a Smart Collection on MVD "
                                  "DB with the collection handle '%s'. It might"
                                  " be possible due to an outdated version of "
                                  "MVD DB. Please, run Smart Collection Sync "
                                  "task." %
                                  model.collection_handle)
                model.save()
                continue

            attributes = generate_collection_attrs_from_model(collection, model)
            if attributes:
                status_code, content = shopify.update_smart_collection(collection.collection_id,
                                                       attributes)
                if status_code != 200:
                    model.synced_we = False
                    model.error_we = str(content['errors'])
                else:
                    model.synced_we = True
            else:
                model.synced_we = True
            model.save()
    except Exception, ex:
        logger.exception('There was an error while executing shopify task %s',
                         ex)
        raise
    store.update_shopify_collection_task_run_at = timezone.now()
    store.save()


def update_shopify_collections_by_store_co():
    try:
        store = Store.objects.get(identifier='shopify-co')
    except Store.DoesNotExist:
        return
    models = Model.objects.filter(synced_co=False)
    shopify = ShopifyConnect(store)

    try:
        for model in models:
            try:
                collection = SmartCollection.objects.get(store=store,
                                                         handle=model.collection_handle)
            except SmartCollection.DoesNotExist:
                model.error_co = ("It doesn't exists a Smart Collection on MVD "
                                  "DB with the collection handle '%s'. It might"
                                  " be possible due to an outdated version of "
                                  "MVD DB. Please, run Smart Collection Sync "
                                  "task." %
                                  model.collection_handle)
                model.save()
                continue

            attributes = generate_collection_attrs_from_model(collection, model)
            if attributes:
                status_code, content = shopify.update_smart_collection(collection.collection_id,
                                                                       attributes)
                if status_code != 200:
                    model.synced_co = False
                    model.error_co = str(content['errors'])
                else:
                    if 'image' in content['smart_collection']:
                        model.shopify_image = content['smart_collection']['image']['src']
                        model.save()
                    model.synced_co = True
            else:
                model.synced_co = True
            model.save()
    except Exception, ex:
        logger.exception('There was an error while executing shopify task %s',
                         ex)
        raise
    store.update_shopify_collection_task_run_at = timezone.now()
    store.save()


@shared_task(ignore_results=True)
@transaction.atomic
def get_shopify_orders():
    stores = Store.objects.all()

    for store in stores:
        shopify = ShopifyConnect(store)

        try:
            orders_qty = shopify.get_orders_total_quantity(
                updated_at_min=store.order_task_run_at, status='any')['count']
            total_pages = -(-orders_qty // 250)
            last_run = timezone.now()

            for page in xrange(1, total_pages+1):
                orders = []
                response = shopify.get_orders(page=page, status='any',
                                              updated_at_min=store.order_task_run_at)
                orders.extend(response['orders'])

                process = ProcessOrders(store, orders)
                process.parse_orders()

            store.order_task_run_at = last_run
            store.save()
        except Exception, ex:
            logger.exception('There was an error while executing shopify task %s',
                             ex)
            raise


@shared_task(ignore_results=True)
def update_product_attributes():
    product_attributes = (MetadataProductAttribute.objects
                          .filter(status=MetadataProductAttribute.UNSYNCED)
                          .select_related('product_metadata'))

    try:
        for p_attribute in product_attributes:
            product = p_attribute.product_metadata
            try:
                product_id = (Product.objects
                              .get(store=product.store,
                                   productvariant__sku=product.sku)
                              .product_id)
            except Product.DoesNotExist:
                p_attribute.error_msg = ("It doesn't exists a Product on MVD "
                                         "DB with the sku '{}'.".format(product.sku))
                p_attribute.status = MetadataProductAttribute.ERROR
                p_attribute.save()
                continue

            shopify = ShopifyConnect(product.store)
            attributes = {
                'namespace': p_attribute.namespace,
                'key': p_attribute.key,
                'description': p_attribute.description,
                'value': p_attribute.value,
                'value_type': 'string'
            }

            status_code, content = shopify.create_metafield('products',
                                                            product_id,
                                                            attributes)
            if status_code == 201:
                p_attribute.status = MetadataProductAttribute.SYNCED
            else:
                p_attribute.status = MetadataProductAttribute.ERROR
                p_attribute.error_msg = str(content['errors'])

            p_attribute.save()
    except Exception, ex:
        logger.exception('There was an error while executing shopify task %s',
                         ex)
        raise


@shared_task(ignore_results=True)
def update_collection_attributes():
    collection_attributes = (MetadataCollectionAttribute.objects
                             .filter(status=MetadataCollectionAttribute.UNSYNCED)
                             .select_related('collection_metadata'))

    try:
        for c_attribute in collection_attributes:
            collection = c_attribute.collection_metadata
            try:
                collection_id = (SmartCollection.objects
                                 .get(store=collection.store,
                                   title=collection.name)
                                 .collection_id)
            except SmartCollection.DoesNotExist:
                c_attribute.error_msg = ("It doesn't exists a Collection on MVD "
                                         "DB with the title '{}'.".format(
                    collection.name))
                c_attribute.status = MetadataCollectionAttribute.ERROR
                c_attribute.save()
                continue

            shopify = ShopifyConnect(c_attribute.collection_metadata.store)
            attributes = {
                'namespace': c_attribute.namespace,
                'key': c_attribute.key,
                'description': c_attribute.description,
                'value': c_attribute.value,
                'value_type': 'string'
            }

            status_code, content = shopify.create_metafield('collections',
                                                            collection_id,
                                                            attributes)
            if status_code == 201:
                c_attribute.status = MetadataCollectionAttribute.SYNCED
            else:
                c_attribute.status = MetadataCollectionAttribute.ERROR
                c_attribute.error_msg = str(content['errors'])

            c_attribute.save()
    except Exception, ex:
        logger.exception('There was an error while executing shopify task %s',
                         ex)
        raise


@shared_task(ignore_results=True)
def retrieve_stone_edge_inventory():
    store = Store.objects.get(identifier='shopify-we')

    try:
        ftp = FTP(settings.FTP_STONE_EDGE_DOMAIN)
        ftp.login(settings.FTP_STONE_EDGE_USER,
                  settings.FTP_STONE_EDGE_PASSWORD)
        ftp.set_pasv(False)

        ftp.cwd(settings.FTP_STONE_EDGE_FOLDER_PATH)

        yesterday = (date.today() - timedelta(1)).strftime('%m-%d-%Y')
        file_name = 'qoh{}.csv'.format(yesterday)

        # Check if file exists
        files = ftp.nlst()
        if file_name in files:
            f = cStringIO.StringIO()
            # gFile = open(file_name, 'wb')
            ftp.retrbinary('RETR {}'.format(file_name), f.write)
            # gFile.close()
            ftp.quit()

            inventory_file = InventoryUpdateFile(created_at=timezone.now(),
                                                 name=file_name, store=store,
                                                 vendor_source=InventoryUpdateFile.STONE_EDGE)
            inventory_file.save()
            inventory_file.file.save(file_name, File(f))
        else:
            error_msg = 'File {} not found'.format(file_name)
            inventory_file = InventoryUpdateFile(created_at=timezone.now(),
                                                 name=file_name,
                                                 output=error_msg, store=store,
                                                 vendor_source=InventoryUpdateFile.STONE_EDGE)
            inventory_file.save()

        # Process SKUs
        if inventory_file.file:
            reader = csv.reader(inventory_file.file)
            skus = {}
            reader.next()  # Skip headers
            for row in reader:
                sku = row[0]
                qoh_qty = row[1]
                if sku.startswith('DS-') or sku == 'STY-PEN-UNIV-02':
                    continue
                skus[sku] = qoh_qty

            variants = (ProductVariant.objects
                        .filter(product__store=store, sku__in=skus.keys())
                        .select_related('product'))
            inventory_log = []
            for variant in variants:
                qoh_qty = int(skus[variant.sku])
                previous_qty = variant.inventory_quantity
                if (previous_qty is not None) and previous_qty != qoh_qty:
                    new_qty = qoh_qty

                    log = InventoryUpdateLog(file=inventory_file,
                                             created_at=timezone.now(),
                                             new_qty=new_qty,
                                             previous_qty=previous_qty,
                                             qoh_qty=qoh_qty,
                                             sku=variant.sku)
                    inventory_log.append(log)
            InventoryUpdateLog.objects.bulk_create(inventory_log)
            inventory_file.success = True
            inventory_file.save()
    except Exception as ex:
        logger.exception('There was an error while executing shopify task %s',
                         ex)
        if inventory_file:
            inventory_file.output = repr(ex)
            inventory_file.save()
        raise


@shared_task(ignore_results=True)
def retrieve_dh_hr_inventory():
    store = Store.objects.get(identifier='shopify-we')

    try:
        ds_hr_file = urllib2.urlopen(settings.DS_HR_URL)
        f = cStringIO.StringIO()
        f.write(ds_hr_file.read())
        file_name = 'dw_hr_{}.csv'.format(timezone.now().strftime('%m_%d_%Y_%H_%M'))
        inventory_file = InventoryUpdateFile(created_at=timezone.now(),
                                             name=file_name, store=store,
                                             vendor_source=InventoryUpdateFile.DS_HR)
        inventory_file.save()
        inventory_file.file.save(file_name, File(f))

        # Get vendor code mapping for Dropship - Highest Rated
        vendor_code_map = dict(InventorySupplierMapping.objects
                               .filter(supplier__supplier_id=149)
                               .values_list('supplier_code', 'sku'))
        # Process SKUs
        reader = csv.reader(inventory_file.file)
        skus = {}
        reader.next()  # Skip headers
        for row in reader:
            vendor_code = row[0]
            qoh_qty = row[1]
            if vendor_code in vendor_code_map:
                skus[vendor_code_map[vendor_code]] = qoh_qty

        variants = (ProductVariant.objects
                    .filter(product__store=store, sku__in=skus.keys())
                    .select_related('product'))
        inventory_log = []
        for variant in variants:
            qoh_qty = int(skus[variant.sku])
            previous_qty = variant.inventory_quantity
            if (previous_qty is not None) and previous_qty != qoh_qty:
                new_qty = qoh_qty

                log = InventoryUpdateLog(file=inventory_file,
                                         created_at=timezone.now(),
                                         new_qty=new_qty,
                                         previous_qty=previous_qty,
                                         qoh_qty=qoh_qty,
                                         sku=variant.sku)
                inventory_log.append(log)
        InventoryUpdateLog.objects.bulk_create(inventory_log)
        inventory_file.success = True
        inventory_file.save()
    except Exception as ex:
        logger.exception('There was an error while executing shopify task %s',
                         ex)
        if inventory_file:
            inventory_file.output = repr(ex)
            inventory_file.save()
        raise


@shared_task(ignore_results=True)
def update_inventory():
    store = Store.objects.get(identifier='shopify-we')
    shopify = ShopifyConnect(store)

    try:
        inventory_logs = InventoryUpdateLog.objects.filter(synced=False)
        skus = {}
        for inventory_log in inventory_logs:
            skus[inventory_log.sku] = inventory_log

        products = (Product.objects
                    .filter(store=store, productvariant__sku__in=skus.keys()))

        for product in products:
            attributes = {'variants': []}
            for variant in product.productvariant_set.all().order_by('position'):
                if variant.sku in skus:
                    log = skus[variant.sku]
                    attributes['variants'].append({
                        'id': variant.variant_id,
                        'inventory_quantity': log.new_qty
                    })
                else:
                    attributes['variants'].append({
                        'id': variant.variant_id,
                    })

            resp = shopify.update_product(product.product_id,
                                          attributes)
            if resp.status_code == 200:
                log.success = True
            else:
                content = json.loads(resp.content)
                log.error = str(content['errors'])
            log.synced = True
            log.save()
    except Exception as ex:
        logger.exception('There was an error while executing shopify task %s',
                         ex)
        raise


@shared_task(ignore_results=True)
def remove_shopify_duplicated_objs():
    try:
        try:
            store = Store.objects.get(identifier='shopify-we')
            remove_duplicates_by_store(store)
        except Store.DoesNotExist:
            pass
        try:
            store = Store.objects.get(identifier='shopify-co')
            remove_duplicates_by_store(store)
        except Store.DoesNotExist:
            pass
        try:
            store = Store.objects.get(identifier='shopify-mm')
            remove_duplicates_by_store(store)
        except Store.DoesNotExist:
            pass
    except Exception as ex:
        logger.exception('There was an error while executing shopify task %s',
                         ex)
        raise


@shared_task(ignore_results=True)
def update_color_swatches_metafields_co():
    try:
        try:
            store = Store.objects.get(identifier='shopify-co')
        except Store.DoesNotExist:
            return
        products = (Product.objects
                    .filter(store=store)
                    .exclude(productextrainfo__associated_products=None)
                    .select_related('productextrainfo'))

        for product in products:
            sku = product.productvariant_set.first().sku
            try:
                associated_ps = product.productextrainfo.associated_products.all().order_by('product_id')
            except ObjectDoesNotExist:
                continue
            metafield = []
            for associated_p in associated_ps:
                try:
                    color = associated_p.productextrainfo.color
                except ObjectDoesNotExist:
                    continue
                handle = associated_p.handle
                in_stock = associated_p.productvariant_set.first().inventory_quantity > 0 and True or False
                metafield.append({
                    'productHandle': handle,
                    'productColor': color,
                    'inStock': in_stock
                })
            if metafield:
                metafield = json.dumps(metafield)
                try:
                    m = MetadataProductAttribute.objects.get(product_metadata__sku=sku,
                                                             key='variants',
                                                             m_type=MetadataProductAttribute.ASSOCIATED_PRODUCTS)
                    if m.value != metafield:
                        m.value = metafield
                        m.status = MetadataProductAttribute.UNSYNCED
                        m.save()
                except MetadataProductAttribute.DoesNotExist:
                    m_p_obj, created = MetadataProduct.objects.get_or_create(store=store, sku=sku)

                    m = MetadataProductAttribute(product_metadata=m_p_obj,
                                                 key='variants',
                                                 value=metafield,
                                                 m_type=MetadataProductAttribute.ASSOCIATED_PRODUCTS,
                                                 namespace=MetadataProductAttribute.VARIANTS)
                    m.save()
    except Exception as ex:
        logger.exception('There was an error while executing shopify task %s',
                         ex)
        raise


@shared_task(ignore_results=True)
def update_collection_metafields():
    try:
        stores = Store.objects.filter(identifier__in=['shopify-we', 'shopify-co'])
        for store in stores:
            collections = SmartCollection.objects.filter(store=store)

            for collection in collections:
                master_categories = MasterCategory.objects.filter(brand_model_name=collection.title).values_list(
                    'category_name', 'mcid')
                if master_categories:
                    metafield = json.dumps(dict(master_categories))

                    update_collection_metafield(store, collection.title,
                                                'master_categories',
                                                metafield,
                                                MetadataCollectionAttribute.MASTER_CATEGORIES,
                                                MetadataCollectionAttribute.MASTER_CATEGORIES)
    except Exception as ex:
        logger.exception('There was an error while executing shopify task %s',
                         ex)
        raise


@shared_task(ignore_results=True)
def update_collection_brand_models_metafields():
    try:
        stores = Store.objects.filter(identifier__in=['shopify-we', 'shopify-co'])
        models = Model.objects.all()
        models = {x.collection_handle: x for x in models}
        for store in stores:
            collections = SmartCollection.objects.filter(store=store)

            for collection in collections:
                try:
                    model = models[collection.handle]
                except KeyError:
                    continue

                brand = model.brand.name
                model = model.model
                brand_model = '{} {}'.format(brand, model)
                update_collection_metafield(store, collection.title, 'brand',
                                            brand, MetadataCollectionAttribute.BRAND_MODEL,
                                            MetadataCollectionAttribute.N_BRAND_MODEL)
                update_collection_metafield(store, collection.title, 'model',
                                            model, MetadataCollectionAttribute.BRAND_MODEL,
                                            MetadataCollectionAttribute.N_BRAND_MODEL)
                update_collection_metafield(store, collection.title, 'brandModel',
                                            brand_model, MetadataCollectionAttribute.BRAND_MODEL,
                                            MetadataCollectionAttribute.N_BRAND_MODEL)
    except Exception as ex:
        logger.exception('There was an error while executing shopify task %s',
                         ex)
        raise


@shared_task(ignore_results=True)
def update_collection_sku_add_on_metafields():
    try:
        store = Store.objects.get(identifier='shopify-co')
        models_lst = Model.objects.filter(sku_add_on__isnull=False).values_list('collection_handle', flat=True)
        models = Model.objects.filter(sku_add_on__isnull=False)

        models = {x.collection_handle: x for x in models}
        collections = SmartCollection.objects.filter(store=store, handle__in=models_lst)
        for collection in collections:
            try:
                model = models[collection.handle]
            except KeyError:
                continue
            try:
                mpid = MasterProduct.objects.get(sku=model.sku_add_on).mpid
            except MasterProduct.DoesNotExist:
                continue
            try:
                handle = ProductVariant.objects.get(sku=model.sku_add_on,
                                                    product__store=store).product.handle
            except ProductVariant.DoesNotExist:
                continue

            value = json.dumps({'handle': handle, 'master_product': mpid})
            update_collection_metafield(store, collection.title,
                                        'defaultAddOnProduct', value,
                                        MetadataCollectionAttribute.DEFAULT_ADD_ON,
                                        MetadataCollectionAttribute.N_DEFAULT_ADD_ON)

    except Exception as ex:
        logger.exception('There was an error while executing shopify task %s',
                         ex)
        raise


@shared_task(ignore_results=True)
def upload_feed_to_zaius_s3_bucket():
    s3 = boto3.resource('s3')
    b = s3.Bucket('zaius-incoming')
    try:
        feed = Feed.objects.get(store__identifier='shopify-co',
                                name='shopify-co-zaius-feed')
        s3_key = '5YVK2LhYpKWTjZ4G035Dlw/zaius_products_{}.csv'.format(timezone.now().strftime('%Y-%m-%d'))
        data = open(feed.file.path, 'rb')
        b.put_object(Key=s3_key, Body=data)
    except Exception as ex:
        logger.exception('There was an error while executing shopify task %s',
                         ex)
        raise


@shared_task(ignore_results=True)
def process_shopify_transactions():
    try:
        transactions = ShopifyTransaction.objects.filter(status=ShopifyTransaction.UNPROCESSED)

        for t in transactions:
            try:
                process_transaction(t)
                t.status = ShopifyTransaction.PROCESSED
            except ShopifyTransactionException as e:
                t.error_msg = repr(e)
                t.status = ShopifyTransaction.ERROR
            finally:
                t.date_processed = timezone.now()
                t.save()
    except Exception as ex:
        logger.exception('There was an error while executing shopify task %s',
                         ex)
        raise


@shared_task(ignore_results=True)
def get_metafields_co():
    try:
        store = Store.objects.get(identifier='shopify-co')
        shopify = ShopifyConnect(store)
        metafields = []
        last_run = timezone.now()

        products = Product.objects.filter(store=store)
        for product in products:
            qty = shopify.get_products_metafields_total_quantity(product.product_id,
                                                                 updated_at_min=store.metafield_task_run_at)['count']
            total_pages = -(-qty // 250)
            for page in xrange(1, total_pages + 1):

                response = shopify.get_metafields('products',
                                                  product.product_id, page=page,
                                                  updated_at_min=store.metafield_task_run_at)
                metafields.extend(response['metafields'])

        smart_collections = SmartCollection.objects.filter(store=store)
        for collection in smart_collections:
            qty = shopify.get_smart_collections_metafields_total_quantity(collection.collection_id,
                                                                          updated_at_min=store.metafield_task_run_at)['count']
            total_pages = -(-qty // 250)
            for page in xrange(1, total_pages + 1):
                response = shopify.get_metafields('collections',
                                                  collection.collection_id,
                                                  page=page,
                                                  updated_at_min=store.metafield_task_run_at)
                metafields.extend(response['metafields'])

            process = ProcessMetafields(store, metafields)
        process.parse_metafields()

        store.metafield_task_run_at = last_run
        store.save()
    except Exception as ex:
        logger.exception('There was an error while executing shopify task %s',
                         ex)
        raise
