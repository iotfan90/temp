import csv
import json
import logging
import os
import urllib

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files import File
from django.db.models import IntegerField, Value
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView, View

from .connect import ShopifyConnect
from .models import (Brand, InventorySupplier, InventorySupplierMapping,
                     MasterAttributeSet, Model, ProductExtraInfo,
                     ProductVariant, ShopifyTransaction, SmartCollection, Store)

from .tasks import (get_shopify_products, get_shopify_smart_collections,
                    generate_we_product_feeds, upload_brand_model_js_to_shopify,
                    update_shopify_collections, get_shopify_orders)
from .utils import (check_csv_has_img, check_csv_has_variant,
                    check_mandatory_csv_file_columns_model_update,
                    check_mandatory_csv_file_columns_product_association,
                    check_mandatory_csv_file_columns_product_create,
                    check_mandatory_csv_file_columns_product_update,
                    check_mandatory_fields, generate_brand_model_js_file,
                    generate_brand_model_images_js_file,
                    update_collection_rules)

logger = logging.getLogger(__name__)
 
class Generate_co_product_feeds(View):
    http_method_names = [u'get', ]

    def get(self, request):
        from .models import (Feed, Store)
        from .tasks import generate_co_product_feeds
        from .feed_rules import package_product_co_google
        from .feeds import generate_product_feed

        store_co = Store.objects.get(identifier='shopify-co')
        master = Feed.objects.get(store__identifier='shopify-co', name='shopify-co-master-feed')
        
        generate_product_feed(master, store_co, 'shopify-co-google-feed', package_product_co_google, compressed=True, delimiter='\t', extension='txt')
        generate_product_feed(master, store_co, 'shopify-co-google-feed-txt', package_product_co_google, delimiter='\t', extension='txt')

        word = 'shopify/generate_co_product_feeds VIEW'
        return HttpResponse(word)

class Show_test_message(View):
    http_method_names = [u'get', ]
    def get(self, request):
        test = 'Show_test_message VIEW'
        return HttpResponse(test)



class InventorySupplierMappingBulkUpdate(LoginRequiredMixin, TemplateView):
    template_name = 'inventory_supplier_mapping_bulk_update.html'
    login_url = '/accounts/login'

    def get_context_data(self, **kwargs):
        context = super(InventorySupplierMappingBulkUpdate, self).get_context_data(**kwargs)
        stores = Store.objects.all().values('name', 'id')
        context['stores'] = json.dumps(list(stores))
        return context

    def post(self, request, *args, **kwargs):
        try:
            my_uploaded_file = request.FILES['file']
        except Exception, ex:
            return JsonResponse({
                'message': 'File not found',
                'success': False,
            })
        try:
            store = request.POST['store']
            store = Store.objects.get(id=store)
        except Exception, ex:
            return JsonResponse({
                'message': 'Store not found',
                'success': False,
            })

        reader = csv.DictReader(my_uploaded_file)
        processed = []

        # Check mandatory columns
        mandatory_file_columns = ['supplier', 'sku', 'supplier_code']
        columns = set(mandatory_file_columns).difference(reader.fieldnames)
        if len(columns) > 0:
            return JsonResponse({
                'message': 'Check example file. Mandatory columns were absent: {}'.format(list(columns)),
                'success': False,
            })
        non_processed = []
        suppliers = InventorySupplier.objects.filter(store=store)
        suppliers = {sup.name: sup for sup in suppliers}
        skus = ProductVariant.objects.filter(product__store=store).values_list('sku', flat=True)
        for idx, row in enumerate(reader):
            cost = row['cost']
            sku = row['sku']
            supplier = row['supplier']
            supplier_code = row['supplier_code']

            if supplier not in suppliers.keys():
                non_processed.append({'row': idx + 2,
                                      'reason': 'Supplier "{}" does not exist for store "{}"'.format(
                                          supplier, store)})
            elif sku not in skus:
                non_processed.append({'row': idx + 2,
                                      'reason': 'SKU "{}" does not exist for store "{}"'.format(
                                          sku, store)})
            else:
                processed.append({'cost': cost, 'sku': sku,
                                  'supplier': supplier,
                                  'supplier_code': supplier_code})

        if len(non_processed) == 0:
            for p in processed:
                defaults = {'supplier_code': p['supplier_code']}
                if p['cost']:
                    defaults['cost'] = p['cost']
                obj, created = (InventorySupplierMapping.objects
                    .filter(supplier__store=store)
                    .update_or_create(
                    supplier=suppliers[p['supplier']], sku=p['sku'],
                    defaults=defaults))

        return JsonResponse({
            'processed_counter': len(processed),
            'non_processed': json.dumps(non_processed),
            'success': True,
        })


class ProductBulkAssociation(LoginRequiredMixin, TemplateView):
    template_name = 'product_bulk_association.html'
    login_url = '/accounts/login'

    def get_context_data(self, **kwargs):
        context = super(ProductBulkAssociation, self).get_context_data(**kwargs)
        stores = Store.objects.all().values('name', 'id')
        context['stores'] = json.dumps(list(stores))
        return context

    def post(self, request, *args, **kwargs):
        try:
            my_uploaded_file = request.FILES['file']
        except Exception, ex:
            return JsonResponse({
                'message': 'File not found',
                'success': False,
            })
        try:
            store = request.POST['store']
            store = Store.objects.get(id=store)
        except Exception, ex:
            return JsonResponse({
                'message': 'Store not found',
                'success': False,
            })

        reader = csv.DictReader(my_uploaded_file)

        columns = check_mandatory_csv_file_columns_product_association(reader.fieldnames)
        if len(columns) > 0:
            return JsonResponse({
                'message': 'Check example file. Mandatory columns were absent: {}'.format(list(columns)),
                'success': False,
            })
        non_processed = []

        skus = set(ProductVariant.objects
                   .filter(product__store=store)
                   .values_list('sku', flat=True))
        variants = (ProductVariant.objects
                    .filter(product__store=store)
                    .select_related('product'))
        variants = {var.sku: var for var in variants}
        associations = []
        for idx, row in enumerate(reader):
            obj = {}
            sku = row['sku']
            if not row['color']:
                non_processed.append({'row': idx + 1,
                                      'reason': 'Color value cannot be blank:'})
                continue
            if sku not in skus:
                non_processed.append({'row': idx+1,
                                      'reason': 'SKU does not exists on MVD: {}'.format(sku)})
                continue

            associated_products = []
            for sku in row['associated_products'].split(','):
                if sku not in skus:
                    non_processed.append({'row': idx + 1,
                                          'reason': 'SKU does not exists on MVD: {}'.format(
                                              sku)})
                    break
                else:
                    associated_products.append(variants[sku].product)
            obj['color'] = row['color']
            obj['sku'] = variants[row['sku']].product
            obj['associated_products'] = associated_products
            associations.append(obj)

        processed_counter = 0
        if len(non_processed) == 0:
            for a in associations:
                obj, created = (ProductExtraInfo.objects
                                .update_or_create(product=a['sku'],
                                                  defaults={'color': a['color']}))
                obj.associated_products.clear()
                obj.associated_products.add(*a['associated_products'])
                processed_counter += 1

        return JsonResponse({
            'processed_counter': processed_counter,
            'non_processed': json.dumps(non_processed),
            'success': True,
        })


class ProductBulkCreate(LoginRequiredMixin, TemplateView):
    template_name = 'product_bulk_create.html'
    login_url = '/accounts/login'

    def get_context_data(self, **kwargs):
        context = super(ProductBulkCreate, self).get_context_data(**kwargs)
        stores = Store.objects.all().values('name', 'id')
        context['stores'] = json.dumps(list(stores))
        return context

    def post(self, request, *args, **kwargs):
        try:
            my_uploaded_file = request.FILES['file']
        except Exception, ex:
            return JsonResponse({
                'message': 'File not found',
                'success': False,
            })
        try:
            store = request.POST['store']
            store = Store.objects.get(id=store)
        except Exception, ex:
            return JsonResponse({
                'message': 'Store not found',
                'success': False,
            })

        reader = csv.DictReader(my_uploaded_file)
        processed = []

        columns = check_mandatory_csv_file_columns_product_create(reader.fieldnames)
        if len(columns) > 0:
            return JsonResponse({
                'message': 'Check example file. Mandatory columns were absent: {}'.format(list(columns)),
                'success': False,
            })
        non_processed = []
        handle = None
        row_idx = 2
        product = []
        for idx, row in enumerate(reader):
            if handle != row['Handle'] and len(product) > 0:
                # Process object
                self.process_product(row_idx, product, processed, non_processed)

                # Clear
                row_idx = idx + 2
                product = []
                product.append(row)
                handle = row['Handle']
            else:
                product.append(row)
                handle = row['Handle']
        self.process_product(row_idx, product, processed, non_processed)

        if len(non_processed) == 0:
            transactions = []
            for p in processed:
                obj = ShopifyTransaction(content=p, title=p[0]['Handle'],
                                         transaction_type=ShopifyTransaction.PRODUCT_CREATE,
                                         store=store)
                transactions.append(obj)
            ShopifyTransaction.objects.bulk_create(transactions)

        return JsonResponse({
            'processed_counter': len(processed),
            'non_processed': json.dumps(non_processed),
            'success': True,
        })

    def process_product(self, row_idx, product, processed, non_processed):
        success = True
        mandatory_fields = ['Handle', 'Title', 'Type', 'Published',
                            'Option1 Name', 'Option1 Value', 'Variant SKU',
                            'Variant Price']
        mandatory_img_fields = ['Handle', 'Image Src', 'Image Position']

        fields = check_mandatory_fields(product[0], mandatory_fields)
        if fields:
            non_processed.append({'row': row_idx,
                                  'reason': 'Mandatory fields were absent: {}'.format(
                                      fields)})
            success = False
        for idx, line in enumerate(product[1:]):
            idx += 1
            fields = check_mandatory_fields(line, mandatory_img_fields)
            if fields:
                non_processed.append({'row': row_idx + idx,
                                      'reason': 'Mandatory fields were absent: {}'.format(
                                          fields)})
                success = False
        if success:
            processed.append(product)


class ProductBulkUpdate(LoginRequiredMixin, TemplateView):
    template_name = 'product_bulk_update.html'
    login_url = '/accounts/login'

    def get_context_data(self, **kwargs):
        context = super(ProductBulkUpdate, self).get_context_data(**kwargs)
        stores = Store.objects.all().values('name', 'id')
        context['stores'] = json.dumps(list(stores))
        return context

    def post(self, request, *args, **kwargs):
        try:
            my_uploaded_file = request.FILES['file']
        except Exception, ex:
            return JsonResponse({
                'message': 'File not found',
                'success': False,
            })
        try:
            store = request.POST['store']
            store = Store.objects.get(id=store)
        except Exception, ex:
            return JsonResponse({
                'message': 'Store not found',
                'success': False,
            })

        reader = csv.DictReader(my_uploaded_file)
        processed = []

        columns = check_mandatory_csv_file_columns_product_update(reader.fieldnames)
        if len(columns) > 0:
            return JsonResponse({
                'message': 'Check example file. Mandatory columns were absent: {}'.format(list(columns)),
                'success': False,
            })
        non_processed = []
        handle = None
        row_idx = 2
        product = []
        for idx, row in enumerate(reader):
            if handle != row['Handle'] and len(product) > 0:
                # Process object
                self.process_product(row_idx, product, processed, non_processed)

                # Clear
                row_idx = idx + 2
                product = []
                product.append(row)
                handle = row['Handle']
            else:
                product.append(row)
                handle = row['Handle']
        self.process_product(row_idx, product, processed, non_processed)

        if len(non_processed) == 0:
            transactions = []
            for p in processed:
                obj = ShopifyTransaction(content=p, title=p[0]['Handle'],
                                         transaction_type=ShopifyTransaction.PRODUCT_UPDATE,
                                         store=store)
                transactions.append(obj)
            try:
                ShopifyTransaction.objects.bulk_create(transactions)
            except Exception, ex:
                return JsonResponse({'message': repr(ex), 'success': False})

        return JsonResponse({
            'processed_counter': len(processed),
            'non_processed': json.dumps(non_processed),
            'success': True,
        })

    def process_product(self, row_idx, product, processed, non_processed):
        success = True
        mandatory_fields = ['Handle', ]
        mandatory_img_fields = ['Handle', 'Image Src', 'Image Position']
        if check_csv_has_variant(product[0].keys()):
            mandatory_fields.append('Variant SKU')
        if check_csv_has_img(product[0].keys()):
            mandatory_fields.extend(['Image Src', 'Image Position'])

        fields = check_mandatory_fields(product[0], mandatory_fields)
        if fields:
            non_processed.append({'row': row_idx,
                                  'reason': 'Mandatory fields were absent: {}'.format(
                                      fields)})
            success = False
        for idx, line in enumerate(product[1:]):
            idx += 1
            fields = check_mandatory_fields(line, mandatory_img_fields)
            if fields:
                non_processed.append({'row': row_idx + idx,
                                      'reason': 'Mandatory fields were absent: {}'.format(
                                          fields)})
                success = False
        if success:
            processed.append(product)


class VariantUpdate(LoginRequiredMixin, TemplateView):
    template_name = 'variant_update.html'
    login_url = '/accounts/login'

    def get_context_data(self, **kwargs):
        context = super(VariantUpdate, self).get_context_data(**kwargs)
        stores = Store.objects.all().values('name', 'id')
        context['stores'] = json.dumps(list(stores))
        return context

    def post(self, request, *args, **kwargs):
        try:
            my_uploaded_file = request.FILES['file']
        except Exception, ex:
            return JsonResponse({
                'message': 'File not found',
                'success': False,
            })
        try:
            store = request.POST['store']
            store = Store.objects.get(id=store)
        except Exception, ex:
            return JsonResponse({
                'message': 'Not store found',
                'success': False,
            })

        reader = csv.reader(my_uploaded_file)
        variants = {}
        headers = reader.next()
        headers = [x.lower() for x in headers]
        for row in reader:
            obj = {}
            for idx, header in enumerate(headers[1:]):
                if row[idx+1]:
                    obj[header] = row[idx+1]
            variants[row[0]] = obj

        non_processed_variants = []

        shopify = ShopifyConnect(store)

        for sku in variants.keys():
            try:
                variant = ProductVariant.objects.get(sku=sku, product__store=store)
            except ProductVariant.DoesNotExist:
                non_processed_variants.append({'sku': sku,
                                               'reason': "Variant SKU doesn't exist in Mobovida Database"})
                variant = None
            if variant:
                variants[sku]['id'] = variant.variant_id
                variant_lst = ProductVariant.objects.filter(product=variant.product).exclude(id=variant.id).values_list('variant_id', flat=True)
                attributes = {
                    'variants': [{'id': x} for x in variant_lst]
                }
                attributes['variants'].append(variants[sku])
                try:
                    resp = shopify.update_product(variant.product.product_id, attributes)
                    if resp.status_code != 200:
                        reason = 'Status code: %s' % resp.status_code
                        non_processed_variants.append({'sku': sku,
                                                       'reason': reason})
                except Exception, ex:
                    reason = 'Error: %s' % ex
                    non_processed_variants.append({'sku': sku,
                                                   'reason': reason})

        return JsonResponse({
            'processed_variants': len(variants) - len(non_processed_variants),
            'non_processed_variants': json.dumps(non_processed_variants),
            'success': True,
        })


class ModelBulkUpdate(LoginRequiredMixin, TemplateView):
    template_name = 'model_bulk_update.html'
    login_url = '/accounts/login'

    def post(self, request, *args, **kwargs):
        try:
            my_uploaded_file = request.FILES['file']
        except Exception, ex:
            return JsonResponse({
                'message': 'File not found',
                'success': False,
            })

        reader = csv.DictReader(my_uploaded_file)
        columns = check_mandatory_csv_file_columns_model_update(reader.fieldnames)
        if len(columns) > 0:
            return JsonResponse({
                'message': 'Check example file. Mandatory columns were absent: {}'.format(
                    list(columns)),
                'success': False,
            })

        models = []
        for row in reader:
            models.append(row)

        non_processed_models = []
        try:
            for obj in models:
                handle = obj['collection_handle']
                try:
                    model = Model.objects.get(collection_handle=handle)
                except Model.DoesNotExist:
                    non_processed_models.append({'handle': handle,
                                                 'reason': 'Models handle does not exist in Mobovida Database'})
                    model = None
                if model:
                    brand = obj['brand']
                    try:
                        model.brand = Brand.objects.get(name=brand)
                    except Brand.DoesNotExist:
                        non_processed_models.append({'handle': handle,
                                                     'reason': 'Brand does not exists: {}'.format(brand)})
                        continue

                    model.categories.clear()
                    categories = obj['categories'].strip()
                    category_not_found = False
                    if categories:
                        categories = obj['categories'].split('|')
                        for category in categories:
                            category = category.strip()
                            try:
                                cat = MasterAttributeSet.objects.get(attribute_set_name=category)
                                model.categories.add(cat)
                            except MasterAttributeSet.DoesNotExist:
                                non_processed_models.append({'handle': handle,
                                                             'reason': 'Category does not exists: {}'.format(category)})
                                category_not_found = True
                                break
                    if category_not_found:
                        continue
                    headset_type = obj['headset_type']
                    if headset_type and headset_type not in dict(Model.HEADSET_TYPE_CHOICES):
                        non_processed_models.append({'handle': handle,
                                                     'reason': 'Headset type "{}" not recognized.'.format(headset_type)})
                        continue
                    adaptor_type = obj['adaptor_type']
                    if adaptor_type and adaptor_type not in dict(Model.ADAPTOR_TYPE_CHOICES):
                        non_processed_models.append({'handle': handle,
                                                     'reason': 'Adaptor type "{}" not recognized.'.format(adaptor_type)})
                        continue
                    device_type = obj['device_type']
                    if device_type and device_type not in dict(Model.DEVICE_TYPE_CHOICES):
                        non_processed_models.append({'handle': handle,
                                                     'reason': 'Device type "{}" not recognized.'.format(device_type)})
                        continue
                    pouch_size = obj['pouch_size']
                    if pouch_size and pouch_size not in dict(Model.POUCH_SIZE_CHOICES):
                        non_processed_models.append({'handle': handle,
                                                     'reason': 'Pouch size "{}" not recognized.'.format(pouch_size)})
                        continue
                    image = obj['image']
                    try:
                        img = urllib.urlretrieve(image)
                    except IOError, ex:
                        non_processed_models.append({'handle': handle,
                                                     'reason': 'Failed downloading image: {}'.format(image)})
                        continue

                    for (key, value) in obj.items():
                        if key == 'image':
                            model.image.save(os.path.basename(value), File(open(img[0])))
                        elif key == 'brand' or key == 'categories' or key == 'collection_handle':
                            pass
                        elif key == 'height' or key == 'depth' or key == 'width':
                            setattr(model, key, value or None)
                        elif key == 'bluetooth' or key == 'removable_battery' or key == 'top_model'or key == 'wireless_charger':
                            if not value:
                                setattr(model, key, None)
                            else:
                                setattr(model, key, value == '1')
                        else:
                            setattr(model, key, value)
                    model.synced_we = False
                    model.synced_co = False
                    model.save()
        except Exception as e:
            return JsonResponse({
                'message': 'Unknown error: {}'.format(repr(e)),
                'success': False,
            })

        return JsonResponse({
            'processed_models_counter': len(models) - len(non_processed_models),
            'non_processed_models': json.dumps(non_processed_models),
            'success': True,
        })


class NewModelsUploadShopifyStoreSelector(LoginRequiredMixin, TemplateView):
    template_name = 'new_models_upload_shopify_store_selector.html'
    login_url = '/accounts/login'

    def get_context_data(self, **kwargs):
        context = (super(NewModelsUploadShopifyStoreSelector, self)
                   .get_context_data(**kwargs))
        stores = Store.objects.all().values('name', 'id')
        context['stores'] = stores
        return context


class NewModelsUploadShopifyPreview(LoginRequiredMixin, TemplateView):
    template_name = 'smart_collection_sync_preview.html'
    login_url = '/accounts/login'

    def post(self, request, *args, **kwargs):
        store = Store.objects.get(id=request.POST['store'])
        context = (super(NewModelsUploadShopifyPreview, self)
                   .get_context_data(**kwargs))
        mvd_handles = Model.objects.all().values_list('collection_handle',
                                                      flat=True)

        shopify_handles = (SmartCollection.objects
                           .filter(store=store)
                           .values_list('handle', flat=True))
        new_handles = set(mvd_handles) - set(shopify_handles)
        collections = (Model.objects
                       .annotate(store=Value(store.id, IntegerField()))
                       .filter(collection_handle__in=new_handles)
                       .values('brand__name', 'model', 'collection_handle',
                               'store'))
        context['collections'] = json.dumps(list(collections))
        if store.collection_task_run_at:
            dt_diff = timezone.now() - store.collection_task_run_at
            dt_diff_mins = int(dt_diff.total_seconds()/60)
        else:
            dt_diff_mins = 'Infinite'
        context['last_sync_date'] = store.collection_task_run_at
        # context['last_smart_collections_sync_mins'] = dt_diff_mins
        context['last_smart_collections_sync_mins'] = 0  # We have webhooks now
        context['store'] = store.id
        context['store_name'] = store.name
        return self.render_to_response(context)


class NewModelUploadShopify(LoginRequiredMixin, View):
    http_method_names = [u'post', ]

    def post(self, request, *args, **kwargs):
        response = {}
        try:
            collection_data = json.loads(request.body)
            store = Store.objects.get(id=collection_data['store'])
            model = Model.objects.get(collection_handle=collection_data['collection_handle'])
            title = '{} {}'.format(model.brand.name, model.model)
            shopify = ShopifyConnect(store)

            attributes = {'title': title,
                          'disjunctive': True,
                          'published': True,
                          'rules': []}
            update_collection_rules(model, attributes)

            if model.image:
                absolute_url = '%s%s' % (settings.DOMAIN_URL, model.image.url)
                attributes['image'] = {'src': absolute_url}
            if model.collection_description:
                attributes['body_html'] = model.collection_description

            status_code, c_collection = shopify.create_smart_collection(attributes)
            if status_code != 201:
                response['success'] = False
                response['message'] = str(c_collection['errors'])
                return JsonResponse(response)

            attributes_page = {'title': title,
                               'template_suffix': 'model----select-category'}
            status_code, content = shopify.create_page(attributes_page)

            if status_code != 201:
                response['success'] = False
                response['message'] = str(content['errors'])
                return JsonResponse(response)
            else:
                if model.image:
                    model.shopify_image = c_collection['smart_collection']['image']['src']
                    model.save()
                response['success'] = True
                response['message'] = ("Collection '%s' (%s) created." %
                                       (c_collection['smart_collection']['title'],
                                        c_collection['smart_collection']['id'])
                                       )
        except Exception, ex:
            response['success'] = False
            response['message'] = repr(ex)

        return JsonResponse(response)


class ProductFeedExclusionUpdate(LoginRequiredMixin, TemplateView):
    template_name = 'product_feed_update.html'
    login_url = '/accounts/login'

    def get_context_data(self, **kwargs):
        context = super(ProductFeedExclusionUpdate, self).get_context_data(**kwargs)
        stores = Store.objects.all().values('name', 'id')
        context['stores'] = json.dumps(list(stores))
        return context

    def post(self, request, *args, **kwargs):
        try:
            my_uploaded_file = request.FILES['file']
        except Exception, ex:
            return JsonResponse({
                'message': 'File not found',
                'success': False,
            })
        try:
            store = request.POST['store']
            store = Store.objects.get(id=store)
        except Exception, ex:
            return JsonResponse({
                'message': 'Not store found',
                'success': False,
            })

        reader = csv.reader(my_uploaded_file)
        skus = []
        reader.next() # Skip headers
        for row in reader:
            skus.append(row[0])

        non_processed_variants = []

        # Clear previous excluded SKUs
        (ProductVariant.objects
         .filter(product__store=store)
         .update(feed_excluded=False))
        for sku in skus:
            try:
                variant = ProductVariant.objects.get(sku=sku,
                                                     product__store=store)
            except ProductVariant.DoesNotExist:
                non_processed_variants.append({'sku': sku,
                                               'reason': "Variant SKU doesn't exist in Mobovida Database"})
                variant = None
            if variant:
                variant.feed_excluded = True
                variant.save()

        return JsonResponse({
            'processed_variants': len(skus) - len(non_processed_variants),
            'non_processed_variants': json.dumps(non_processed_variants),
            'success': True,
        })


class ProductFeedList(LoginRequiredMixin, TemplateView):
    template_name = 'product_feed_list.html'
    login_url = '/accounts/login'

    def get_context_data(self, **kwargs):
        context = (super(ProductFeedList, self).get_context_data(**kwargs))
        stores = Store.objects.all()
        context['stores'] = stores
        return context


class MoreActions(LoginRequiredMixin, TemplateView):
    template_name = 'more_actions.html'
    login_url = '/accounts/login'

    def get_context_data(self, **kwargs):
        context = (super(MoreActions, self).get_context_data(**kwargs))
        stores = Store.objects.all()
        context['stores'] = stores
        try:
            context['we_store'] = Store.objects.get(identifier='shopify-we')
        except Store.DoesNotExist:
            pass
        return context


class MoreActionsSyncProducts(LoginRequiredMixin, View):
    http_method_names = [u'post', ]

    def post(self, request, *args, **kwargs):
        response = {}
        try:
            get_shopify_products()
            response['success'] = True
            response['message'] = 'Products updated'
        except Exception, ex:
            response['success'] = False
            response['message'] = repr(ex)

        return JsonResponse(response)


class MoreActionsSyncSmartCollections(LoginRequiredMixin, View):
    http_method_names = [u'post', ]

    def post(self, request, *args, **kwargs):
        response = {}
        try:
            get_shopify_smart_collections()
            response['success'] = True
            response['message'] = 'Smart collections updated'
        except Exception, ex:
            response['success'] = False
            response['message'] = repr(ex)

        return JsonResponse(response)


class MoreActionsSyncOrders(LoginRequiredMixin, View):
    http_method_names = [u'post', ]

    def post(self, request, *args, **kwargs):
        response = {}
        try:
            get_shopify_orders()
            response['success'] = True
            response['message'] = 'Orders updated'
        except Exception, ex:
            response['success'] = False
            response['message'] = repr(ex)

        return JsonResponse(response)


class MoreActionsGenerateWEProductFeeds(LoginRequiredMixin, View):
    http_method_names = [u'post', ]

    def post(self, request, *args, **kwargs):
        response = {}
        try:
            generate_we_product_feeds()
            response['success'] = True
            response['message'] = 'WE Product feeds generated'
        except Exception, ex:
            response['success'] = False
            response['message'] = repr(ex)

        return JsonResponse(response)


class MoreActionsUploadBrandModelsJSFile(LoginRequiredMixin, View):
    http_method_names = [u'post', ]

    def post(self, request, *args, **kwargs):
        response = {}
        try:
            upload_brand_model_js_to_shopify()
            response['success'] = True
            response['message'] = 'Javascript file uploaded'
        except Exception, ex:
            response['success'] = False
            response['message'] = repr(ex)

        return JsonResponse(response)


class MoreActionsUpdateModelsToShopify(LoginRequiredMixin, View):
    http_method_names = [u'post', ]

    def post(self, request, *args, **kwargs):
        response = {}
        try:
            update_shopify_collections()
            response['success'] = True
            response['message'] = 'Shopify collections updated'
        except Exception, ex:
            response['success'] = False
            response['message'] = repr(ex)

        return JsonResponse(response)


class BrandsModelsJS(View):
    http_method_names = [u'get', ]

    def get(self, request):
        js = generate_brand_model_js_file()
        return HttpResponse(js, content_type="application/javascript")


class BrandsModelImagesJS(View):
    http_method_names = [u'get', ]

    def get(self, request):
        js = generate_brand_model_images_js_file()
        return HttpResponse(js, content_type="application/javascript")


class DiscountCodeRedeem(View):
    http_method_names = [u'get', ]

    def get(self, request):
        if 'code' not in request.GET or 'store_url' not in request.GET:
            error = {'error': "Missing parameters. Expeting 'code' and 'store_url'."}
            return HttpResponse(json.dumps(error),
                                status=400, content_type="application/json")

        discount_code = request.GET['code']
        store_url = request.GET['store_url']
        try:
            store = Store.objects.get(shop_url__contains=store_url)
        except Store.DoesNotExist:
            error = {'error': 'Store does not exists.'}
            return HttpResponse(json.dumps(error), status=404,
                                content_type='application/json')

        shopify = ShopifyConnect(store)
        response, status_code = shopify.get_discount_code(discount_code)
        if status_code == 404:
            response = {'error': 'Discount code not found'}
        if status_code == 200:
            price_rule_id = response[u'discount_code'][u'price_rule_id']
            response2 = shopify.get_price_rule(price_rule_id)
            response.update(response2)
        return HttpResponse(json.dumps(response), status=200,
                            content_type='application/json')


class WebhookCreate(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        try:
            store = request.POST['store']
            store = Store.objects.get(id=store)
        except Exception, ex:
            return JsonResponse({
                'message': 'Not store found',
                'success': False,
            })
        topic = request.POST['topic']
        address = request.POST['address']

        shopify = ShopifyConnect(store)
        attributes = {'topic': topic, 'address': address, 'format': 'json'}
        status_code, content = shopify.create_webhook(attributes)
        response = {}
        if status_code == 201:
            response['success'] = True
        else:
            response['success'] = False
            response['message'] = str(content['errors'])
        return JsonResponse(response)


class WebhookDelete(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        try:
            store = request.POST['store']
            store = Store.objects.get(id=store)
        except Exception, ex:
            return JsonResponse({
                'message': 'Not store found',
                'success': False,
            })
        webhook_id = request.POST['webhook_id']

        shopify = ShopifyConnect(store)
        status_code, content = shopify.delete_webhook(webhook_id)
        response = {}
        if status_code == 200:
            response['success'] = True
        else:
            response['success'] = False
            response['message'] = str(content['errors'])
        return JsonResponse(response)


class WebhookStoreSelector(LoginRequiredMixin, TemplateView):
    template_name = 'webhook_store_selector.html'
    login_url = '/accounts/login'

    def get_context_data(self, **kwargs):
        context = super(WebhookStoreSelector, self).get_context_data(**kwargs)
        stores = Store.objects.all().values('name', 'id')
        context['stores'] = json.dumps(list(stores))
        context['topics'] = ['products/create', 'products/update',
                              'products/delete', 'collections/create',
                              'collections/update', 'collections/delete',
                              'orders/create', 'orders/updated', 'orders/delete',
                              'orders/cancelled', 'orders/fulfilled',
                              'orders/partially_fulfilled', 'orders/paid']
        return context

    def post(self, request, *args, **kwargs):
        try:
            store = request.POST['store']
            store = Store.objects.get(id=store)
        except Exception, ex:
            return JsonResponse({
                'message': 'Store not found',
                'success': False,
            })

        shopify = ShopifyConnect(store)
        webhooks = shopify.get_webhooks()

        return JsonResponse({
            'webhooks': json.dumps(webhooks['webhooks']),
            'success': True,
        })
