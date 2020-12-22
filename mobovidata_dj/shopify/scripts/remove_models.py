import csv
from django.db.models import Q

from mobovidata_dj.shopify.connect import ShopifyConnect
from mobovidata_dj.shopify.models import (MasterCategory, Model, Page,
                                          SmartCollection, Store)


def model_eviction_delete_models(model_file_path):
    with open(model_file_path, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        reader.next()  # Skip header row
        counter = 0
        for row in reader:
            brand = row[0]
            model = row[1]
            success = False
            try:
                model = Model.objects.get(brand__name__icontains=brand,
                                          model__iexact=model)
                success = True
            except Model.DoesNotExist:
                pass
            if not success:
                try:
                    model = model.replace('-', ' ')
                    model = Model.objects.get(brand__name__icontains=brand,
                                              model__iexact=model)
                    success = True
                except Model.DoesNotExist:
                    pass
            if not success:
                try:
                    model = model.replace("'", ' ')
                    model = Model.objects.get(brand__name__icontains=brand,
                                              model__iexact=model)
                    success = True
                except Model.DoesNotExist:
                    pass
            if not success:
                try:
                    brand = brand.replace('/', ' ')
                    model = Model.objects.get(brand__name__icontains=brand,
                                              model__iexact=model)
                    success = True
                except Model.DoesNotExist:
                    pass
            if not success and brand == 'UTStarcom':
                try:
                    brand = 'UT Starcom'
                    model = Model.objects.get(brand__name__icontains=brand,
                                              model__iexact=model)
                    success = True
                except Model.DoesNotExist:
                    pass

            if not success:
                print 'Brand/Model does not exists on MVD DB: ', brand, model
                counter += 1
            else:
                model.delete()
        print counter


def model_eviction_delete_collections(model_file_path, store_identifier):
    store = Store.objects.get(identifier=store_identifier)
    shopify = ShopifyConnect(store)

    with open(model_file_path, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        reader.next()  # Skip header row
        counter = 0
        for row in reader:
            brand_model = row[2]
            brand_model_options = [brand_model, brand_model.replace('-', ' '),
                                   brand_model.replace("'", ' '),
                                   brand_model.replace('/', ' '),
                                   brand_model.replace('.', ' '),
                                   brand_model.replace('UTStarcom', 'UT Starcom'),]
            queryset = SmartCollection.objects.filter(store=store)
            q = Q()
            for state in brand_model_options:
                q = q | Q(title__iexact=state)
            success = False
            try:
                collection = queryset.get(q)
                success = True
            except SmartCollection.DoesNotExist:
                pass

            if not success:
                print 'Collection does not exists on MVD DB: ', brand_model
                counter += 1
            else:
                status_code, content = shopify.delete_smart_collection(collection.collection_id)
                if status_code != 200:
                    print 'Delete error:', brand_model, str(content['errors'])
        print counter


def model_eviction_delete_pages(model_file_path, store_identifier):
    store = Store.objects.get(identifier=store_identifier)
    shopify = ShopifyConnect(store)

    with open(model_file_path, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        reader.next()  # Skip header row
        counter = 0
        for row in reader:
            brand_model = '{} Accessories'.format(row[2])
            brand_model_options = [brand_model, brand_model.replace('-', ' '),
                                   brand_model.replace("'", ' '),
                                   brand_model.replace('/', ' '),
                                   brand_model.replace('.', ' '),
                                   brand_model.replace('UTStarcom', 'UT Starcom'),]
            queryset = Page.objects.filter(store=store)
            q = Q()
            for state in brand_model_options:
                q = q | Q(title__iexact=state)
            success = False
            try:
                page = queryset.get(q)
                success = True
            except Page.DoesNotExist:
                pass

            if not success:
                print 'Page does not exists on MVD DB: ', brand_model
                counter += 1
            else:
                status_code, content = shopify.delete_page(page.shopify_id)
                if status_code != 200:
                    print 'Delete error:', brand_model, str(content['errors'])
        print counter


def model_eviction_delete_master_categories(model_file_path):
    with open(model_file_path, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        reader.next()  # Skip header row
        counter = 0
        for row in reader:
            brand_model = row[2]
            brand_model_options = [brand_model, brand_model.replace('-', ' '),
                                   brand_model.replace("'", ' '),
                                   brand_model.replace('/', ' '),
                                   brand_model.replace('.', ' '),
                                   brand_model.replace('UTStarcom', 'UT Starcom'),]
            queryset = MasterCategory.objects.all()
            q = Q()
            for state in brand_model_options:
                q = q | Q(brand_model_name__iexact=state)
            success = False
            try:
                pages = queryset.filter(q)
                success = True
            except Exception:
                pass

            if not success:
                print 'Master category does not exists on MVD DB: ', brand_model
                counter += 1
            else:
                pages.delete()
        print counter
