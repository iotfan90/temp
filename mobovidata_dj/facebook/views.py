# encoding: utf-8
from __future__ import unicode_literals

import carousel_ads
import csv
import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from raven.contrib.django.raven_compat.models import client
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin

from .models import FacebookAd, ProductReport, FacebookAPISettings
from .utils import get_facebook_campaign_and_ads_info
from mobovidata_dj.facebook.connect import FacebookConnect
from mobovidata_dj.shopify.connect import ShopifyConnect
from mobovidata_dj.shopify.models import (Product, ProductVariant, Store,
                                          SmartCollection)
from modjento.models import CatalogProductEntity, CatalogCategoryEntity
from modjento.models import CoreStoreGroup


logger = logging.getLogger(__name__)


# ################### MAGENTO ###################

class FacebookMultipleAdCreator(LoginRequiredMixin, TemplateResponseMixin,
                                View):
    template_name = 'multiple_ad_creator.html'
    login_url = '/accounts/login'

    def get(self, *args, **kwargs):
        credentials = FacebookAPISettings.objects.all().values('name', 'id')
        context = {
            'fb_credentials': credentials,
        }
        return self.render_to_response(context)


class FacebookMultipleAdPreview(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'multiple_ad_preview.html'
    login_url = '/accounts/login'

    def post(self, request, *args, **kwargs):
        try:
            my_uploaded_file = request.FILES['uploadedFile']
        except Exception:
            messages.add_message(request, messages.INFO,
                                 'Please upload a csv file.')
            return self.render_to_response(context={})
        reader = csv.reader(my_uploaded_file)
        facebook_ads = []

        fb_credentials = FacebookAPISettings.objects.get(
            id=request.POST['APICredentials'])
        rg_temp, mp_ad_sets = get_facebook_campaign_and_ads_info(
            fb_credentials.get_model_dict())

        next(reader, None)  # skip the headers
        for idx, row in enumerate(reader):
            try:
                ad = {
                    'campaign_name': row[0],
                    'ad_set_name': row[1],
                    'ad_name': row[2],
                    'brand_model_category_id': row[3],
                    'product_id_1': row[4],
                    'product_id_2': row[5],
                    'product_id_3': row[6],
                    'product_id_4': row[7],
                    'product_id_5': row[8],
                    'product_id_6': row[9],
                    'product_id_7': row[10],
                    'product_id_8': row[11],
                    'product_id_9': row[12],
                    'product_id_10': row[13],
                    'ad_message': row[14].decode('cp1252'),
                    'additional_url_parameters': row[15],
                    'facebook_profile_id': row[16],
                }

                campaign_id = next(iter(x['campaign_id'] for x in rg_temp if x['name'] == ad['campaign_name'] or []), None)
                ad_set_id = next(iter(x['ad_set_id'] for x in mp_ad_sets[campaign_id] if x['name'] == ad['ad_set_name'] or []), None)
                ad['campaign_id'] = campaign_id
                ad['ad_set_id'] = ad_set_id
                if not campaign_id:
                    messages.add_message(request, messages.ERROR,
                                         'Campaign ID %s not found in Facebook account ID %s' % (ad['campaign_name'], fb_credentials.account_id))
                elif not ad_set_id:
                    messages.add_message(request, messages.ERROR,
                                         'Ad set ID %s not found in Facebook account ID %s' % (
                                         ad['ad_set_name'],
                                         fb_credentials.account_id))
                else:
                    facebook_ads.append(ad)
            except Exception, ex:
                messages.add_message(request, messages.INFO, ex.message)

        context = {
            'facebook_ads': json.dumps(facebook_ads),
            'fb_credentials': fb_credentials.id
        }
        return self.render_to_response(context)


class FacebookAPICredentialsSelector(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'ad_api_selector.html'
    login_url = '/accounts/login'

    def get(self, *args, **kwargs):
        """
        Get the necessary information from FacebookConnect such as campaigns and
        ad_sets
        :return: Json response of data
        """
        credentials = FacebookAPISettings.objects.all().values('name', 'id')
        context = {
            'fb_credentials': credentials,
        }
        return self.render_to_response(context)


class FacebookAdCreator(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'ad_creator.html'
    login_url = '/accounts/login'

    def post(self, request, *args, **kwargs):
        """
            Get the necessary information from FacebookConnect such as campaigns
            and ad_sets
            :return: Json response of data
        """
        fb_credentials = FacebookAPISettings.objects.get(id=request.POST['APICredentials'])
        rg_temp, mp_ad_sets = get_facebook_campaign_and_ads_info(fb_credentials.get_model_dict())
        context = {
            'campaigns': json.dumps(rg_temp),
            'ad_sets': json.dumps(mp_ad_sets),
            'fb_credentials': fb_credentials.id
        }
        return self.render_to_response(context)


class FacebookAdPreview(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'ad_preview.html'
    login_url = '/accounts/login'

    def __init__(self):
        super(FacebookAdPreview, self).__init__()
        self.product_ids = None
        """@type: list[int]"""
        self.category_id = None
        """@type: int"""
        self.error = False
        """@type: bool"""
        self.error_message = None
        """@type: unicode | str | basestring"""

    def check_product_ids(self):
        """
        Check if product ids meet the requirements
        In order to create carousel ads, the products should meet the following
        requirements
        1.More than two products
        2.If they could be valid numbers
        3.If they exist in CatalogCategoryEntity

        :return: Nothing
        """
        if len(self.product_ids) < 2:
            self.error = True
            self.error_message = 'There must be at least two products to create a carousel ad'
        if self.error:
            return
        x = 0
        try:
            for x in xrange(0, len(self.product_ids)):
                self.product_ids[x] = int(self.product_ids[x])
        except ValueError, ex:
            logger.exception(msg='[%s] is not a valid product ID' % self.product_ids[x])
            self.error = True
            self.error_message = '[%s] is not a valid product ID' % self.product_ids[x]
        if self.error:
            return
        ms_existing = set(CatalogProductEntity.objects.filter(
            entity_id__in=self.product_ids
        ).values_list('entity_id', flat=True))
        for x in self.product_ids:
            if x not in ms_existing:
                self.error = True
                self.error_message = '[%s] does not reference an existing product ID' % x
                break

    def check_category_id(self):
        """
        Check if the category_id meet the requirements
        In order to create a carousel ad, the category id should be:
        1.Not empty
        2.Valid format: int
        3.It is in CatalogCategoryEntity.
        :return: Nothing
        """
        if not self.category_id:
            self.error = True
            self.error_message = ('Brand Model Category ID is required in order '
                                  'to generate good and wholesome product links.')
        if self.error:
            return
        try:
            self.category_id = int(self.category_id)
        except ValueError, ex:
            logger.exception(msg='%s is not a valid Brand Model Category ID' % self.category_id)
            self.error = True
            self.error_message = '%s is not a valid Brand Model Category ID.' % self.category_id
        if not CatalogCategoryEntity.objects.filter(entity_id=self.category_id).exists():
            self.error = True
            self.error_message = '%s does not reference a valid Brand Model Category ID' % self.category_id
        if self.error:
            return
        try:
            # We add children_count=0 to the following filter so we only include product-listing pages
            p = CatalogCategoryEntity.objects.get(entity_id=self.category_id, children_count=0)
            st_path = p.path
            rg_root_category_ids = CoreStoreGroup.objects.filter(
                website_id__gt=2
            ).values_list('root_category_id', flat=True)
            st_root_paths = ['/%s/' % x for x in rg_root_category_ids]
            b_valid = False
            for x in st_root_paths:
                if x in st_path:
                    b_valid = True
                    break
            if not b_valid:
                self.error = True
                self.error = 'The selected category ID references a legacy category that is no longer used'
        except CatalogCategoryEntity.DoesNotExist, ex:
            logger.exception(msg='The category is not a product listing page.' % self.category_id)
            self.error = True
            self.error_message = 'The category is not a product listing page.' % self.category_id
        if self.error:
            return

    def stars(self, n):
        n = float(n)
        if n > 4.5:
            return u'🌟🌟🌟🌟🌟(%0.1f)' % n
        if n > 3.5:
            return u'🌟🌟🌟🌟☆ (%0.1f)' % n
        if n > 2.5:
            return u'🌟🌟🌟☆☆ (%0.1f)' % n
        if n > 1.5:
            return u'🌟🌟☆☆☆ (%0.1f)' % n
        if n > 0.8:
            return u'🌟☆☆☆☆ (%0.1f)' % n
        return u'☆☆☆☆☆ (%0.1f)' % n

    def add_description_options(self, rg_products):
        for x in rg_products:
            description_options = {
                'original': 'On sale for %s ; %s off' % (
                    x['sale_price'],
                    x['percentage'][-3:]
                ),
                'star_review': '%s — %s Reviews' % (self.stars(x['rating_summary']), x['reviews_count']),
                'sale_retail': 'Sale Price %s | Retail Price %s' % (x['sale_price'], x['retail_price']),
                'sale_stars': 'On Sale %s | %s' % (x['sale_price'], self.stars(x['rating_summary'])),
                'sale_save': 'Sale Price %s | Save %s' % (x['sale_price'], x['save']),
            }
            x['description_options'] = description_options
            x['description'] = description_options['sale_retail']
            x['image_banner'] = True
            x['color'] = '#6F4AB3'
            x['star_color'] = '#FFAB00'

    def post(self, request, *args, **kwargs):
        """
        Get the products info as well as ad info
        :return:Template response of data
        """
        self.product_ids = [x.strip() for x in request.POST.getlist('products[]')]
        self.product_ids = filter(None, self.product_ids)
        self.check_product_ids()
        self.category_id = request.POST.get('category_id')
        self.check_category_id()
        context = dict()
        context['st_campaign_id'] = request.POST.get('campaign_id', '')
        context['st_ad_set_id'] = request.POST.get('ad_set_id', '')
        ad_set_name = context['st_ad_set_name'] = request.POST.get('ad_set_name', '')
        st_campaign_name = context['st_campaign_name'] = request.POST.get('campaign_name', '')
        context['rg_product_ids'] = self.product_ids
        context['ad_name'] = request.POST.get('ad_name', '')
        context['ad_message'] = request.POST.get('ad_message', '')
        context['b_error'] = self.error
        context['st_error_message'] = self.error_message
        context['fb_credentials'] = request.POST['fb_credentials']
        try:
            context['st_bmc_url'] = carousel_ads.add_tracking(carousel_ads.generate_url_prefix(self.category_id),
                                                              st_campaign_name, ad_set_name, item_id=None)
        except KeyError, ex:
            client.captureException()
            self.error = True
            self.error_message = '%s BMC ID does not map to a BMC URL. BMCID: ' % self.category_id
        if not self.error:
            rg_products = context['rg_products'] = carousel_ads.pull_product_info(
                self.product_ids, st_campaign_name, ad_set_name, category_id=self.category_id)
            self.add_description_options(rg_products)
            context['st_product_data'] = json.dumps(rg_products)
            context['st_category_id'] = json.dumps(self.category_id)
        return self.render_to_response(context)


class FacebookImageUpload(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        """
        Download images and upload images for the loaded data
        :param request:
        :param args:
        :param kwargs:
        :return: Json Response of image hash
        """
        data = json.loads(request.body)
        rg_products = [data]
        fb_credentials = rg_products[0]['fb_credentials']
        fb_credentials = FacebookAPISettings.objects.get(id=fb_credentials)
        fb_credentials = fb_credentials.get_model_dict()

        carousel_ads.download_images(rg_products)
        carousel_ads.upload_images(rg_products, fb_credentials)
        return JsonResponse({
            'success': True,
            'image_hash': rg_products[0].get('image_hash', None),
        })


class FacebookAdUpload(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'ad_finish.html'

    def post(self, request, *args, **kwargs):
        """
        Create facebook carousel ad by using the data from response
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            mp_ad_data = json.loads(request.body)
            fb_credentials = (FacebookAPISettings
                .objects
                .get(id=mp_ad_data['fb_credentials'])
                .get_model_dict())
            new_ad = carousel_ads.create_carousel_ad(
                fb_credentials,
                mp_ad_data['message'],
                mp_ad_data['products'],
                mp_ad_data['ad_set_id'],
                mp_ad_data['name'],
                mp_ad_data['is_active'],
                mp_ad_data['bmc_url']
            )
            ad_id = new_ad.get('id')

            try:
                ad_obj = FacebookAd(campaign_id=int(mp_ad_data['campaign_id']),
                                    ad_set_id=int(mp_ad_data['ad_set_id']),
                                    ad_id=int(ad_id),
                                    campaign_name=mp_ad_data['campaign_name'],
                                    ad_set_name=mp_ad_data['name'],
                                    message=mp_ad_data['message'],
                                    bmc_url=mp_ad_data['bmc_url'],
                                    products=json.dumps(mp_ad_data['products']))
                ad_obj.save()
            except Exception, ex:
                logger.exception(msg='There was an error creating a FacebookAd history record: %s' % ex)

            product_ids = ', '.join([str(x.get('entity_id')) for x in mp_ad_data['products']])
            if ad_id:
                try:
                    report = ProductReport(
                        ad_obj=ad_obj,
                        ad_id=ad_id,
                        ad_name=mp_ad_data.get('name'),
                        ad_set_name=mp_ad_data.get('ad_set_name'),
                        product_ids=product_ids,
                        category_id=int(mp_ad_data.get('category_id')),
                        campaign_name=mp_ad_data.get('campaign_name'),
                        status='created',
                        status_updated_at=timezone.now()
                    )
                    report.save()
                except Exception, ex:
                    logger.exception(msg='There was an error tracking facebook ad %s' % ex)
            return JsonResponse({
                'message': 'Ad has been uploaded!',
                'success': True,
            })
        except Exception, ex:
            logger.exception(msg='There was an error creating the carousel ad.')
            return JsonResponse({
                'message': 'We were not able to create the carousel ad: %s' % ex,
                'success': False,
            })


# ################### SHOPIFY ###################

class FacebookShopifyAPICredentialsSelector(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'shopify_ad_api_selector.html'
    login_url = '/accounts/login'

    def get(self, *args, **kwargs):
        """
        Get the necessary information from FacebookConnect such as campaigns and
        ad_sets
        :return: Json response of data
        """
        credentials = FacebookAPISettings.objects.all().values('name', 'id')
        stores = Store.objects.all().values('name', 'id')
        context = {
            'fb_credentials': credentials,
            'stores': stores
        }
        return self.render_to_response(context)


class FacebookShopifyAdCreator(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'shopify_ad_creator.html'
    login_url = '/accounts/login'

    def post(self, request, *args, **kwargs):
        """
            Get the necessary information from FacebookConnect such as campaigns
            and ad_sets
            :return: Json response of data
        """
        fb_credentials = FacebookAPISettings.objects.get(
            id=request.POST['APICredentials'])
        rg_temp, mp_ad_sets = get_facebook_campaign_and_ads_info(
            fb_credentials.get_model_dict())
        context = {
            'campaigns': json.dumps(rg_temp),
            'ad_sets': json.dumps(mp_ad_sets),
            'fb_credentials': fb_credentials.id,
            'store': request.POST['store']
        }
        return self.render_to_response(context)


class FacebookShopifyAdPreview(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'shopify_ad_preview.html'
    login_url = '/accounts/login'

    def __init__(self):
        super(FacebookShopifyAdPreview, self).__init__()
        self.store = None
        """@type: int"""
        self.error = False
        """@type: bool"""
        self.error_message = None
        """@type: unicode | str | basestring"""

    def check_skus(self):
        """
        Check if product ids meet the requirements
        In order to create carousel ads, the products should meet the following
        requirements
        1.More than two products
        2.If they could be valid numbers
        3.If they exist in CatalogCategoryEntity

        :return: Nothing
        """
        if len(self.skus) < 2:
            self.error = True
            self.error_message = 'There must be at least two products to create a carousel ad'
            return
        existing_sku = ProductVariant.objects.filter(sku__in=self.skus)\
            .values_list('sku', flat=True)
        non_existing_sku = set(self.skus) - set(existing_sku)
        if non_existing_sku:
            self.error = True
            self.error_message = '[%s] does not reference to existing variant skus' % ', '.join(non_existing_sku)

    def check_handle(self):
        """
        Check if the collection handle exists meet the requirements
        In order to create a carousel ad, the handle should be:
        1.Not empty
        2.Valid format: string
        3.It is in SmartCollection.
        :return: Nothing
        """
        if not self.handle:
            self.error = True
            self.error_message = (
            'Collection handle is required in order '
            'to generate good and wholesome product links.')
            return
        if not SmartCollection.objects.filter(handle=self.handle).exists():
            self.error = True
            self.error_message = '%s does not reference a valid collection handle' % self.handle
            return

    def check_skus_belongs_to_collection(self):
        """
        Check if the skus belongs to that collection handle
        :return: Nothing
        """
        if not self.error:
            shopify = ShopifyConnect(self.store)
            products = Product.objects.filter(productvariant__sku__in=self.skus)
            for product in products:
                collection_qty = shopify.get_smart_colletions_total_quantity(product_id=product.product_id)['count']
                total_pages = -(-collection_qty // 250)
                collections = []
                for page in xrange(1, total_pages + 1):
                    response = shopify.get_smart_collections(page=page,
                                                             product_id=product.product_id)
                    if 'errors' in response:
                        self.error = True
                        sku = product.productvariant_set.filter(
                            sku__in=self.skus).first().sku
                        self.error_message = 'SKU %s does not belong to %s collection handle' % (
                        sku, self.handle)
                        return
                    collections.extend(response['smart_collections'])

                if not next((x for x in collections if x['handle'] == self.handle), None):
                    self.error = True
                    sku = product.productvariant_set.filter(sku__in=self.skus).first().sku
                    self.error_message = 'SKU %s does not belong to %s collection handle' % (sku, self.handle)
                    return

    def post(self, request, *args, **kwargs):
        """
        Get the products info as well as ad info
        :return:Template response of data
        """
        self.store = Store.objects.get(id=request.POST['store'])
        self.skus = [x.strip() for x in request.POST.getlist('sku[]')]
        self.skus = filter(None, self.skus)
        self.check_skus()
        self.handle = request.POST.get('handle')
        self.check_handle()
        self.check_skus_belongs_to_collection()
        context = dict()
        context['st_campaign_id'] = request.POST.get('campaign_id', '')
        context['st_ad_set_id'] = request.POST.get('ad_set_id', '')
        ad_set_name = context['st_ad_set_name'] = request.POST.get(
            'ad_set_name', '')
        st_campaign_name = context['st_campaign_name'] = request.POST.get(
            'campaign_name', '')
        context['rg_skus'] = self.skus
        context['ad_name'] = request.POST.get('ad_name', '')
        context['ad_message'] = request.POST.get('ad_message', '')
        context['b_error'] = self.error
        context['st_error_message'] = self.error_message
        context['fb_credentials'] = request.POST['fb_credentials']
        try:
            context['st_handle_url'] = carousel_ads.add_tracking(
                carousel_ads.generate_collection_url_prefix_shopify(self.handle),
                st_campaign_name, ad_set_name)
        except KeyError, ex:
            client.captureException()
            self.error = True
            self.error_message = '%s BMC ID does not map to a BMC URL. BMCID: ' % self.category_id
        if not self.error:
            rg_variants = context[
                'rg_variants'] = carousel_ads.pull_product_variant_info_shopify(
                self.skus, st_campaign_name, ad_set_name,
                handle=self.handle)
            context['st_variants_data'] = json.dumps(rg_variants)
            context['st_handle'] = json.dumps(self.handle)
        return self.render_to_response(context)


class FacebookShopifyImageUpload(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        """
        Download images and upload images for the loaded data
        :param request:
        :param args:
        :param kwargs:
        :return: Json Response of image hash
        """
        data = json.loads(request.body)
        rg_products = [data]

        fb_credentials = rg_products[0]['fb_credentials']
        fb_credentials = FacebookAPISettings.objects.get(id=fb_credentials)
        fb_credentials = fb_credentials.get_model_dict()

        carousel_ads.shopify_download_images(rg_products)
        carousel_ads.upload_images(rg_products, fb_credentials)

        return JsonResponse({
            'success': True,
            'image_hash': rg_products[0].get('image_hash', None),
        })


class FacebookShopifyAdUpload(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'ad_finish.html'

    def post(self, request, *args, **kwargs):
        """
        Create facebook carousel ad by using the data from response
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        try:
            mp_ad_data = json.loads(request.body)
            fb_credentials = (FacebookAPISettings
                              .objects
                              .get(id=mp_ad_data['fb_credentials'])
                              .get_model_dict())
            new_ad = carousel_ads.create_carousel_ad(
                fb_credentials,
                mp_ad_data['message'],
                mp_ad_data['products'],
                mp_ad_data['ad_set_id'],
                mp_ad_data['name'],
                mp_ad_data['is_active'],
                mp_ad_data['handle_url'],
                mp_ad_data['handle_url']
            )
            ad_id = new_ad.get('id')

            try:
                ad_obj = FacebookAd(
                    campaign_id=int(mp_ad_data['campaign_id']),
                    ad_set_id=int(mp_ad_data['ad_set_id']),
                    ad_id=int(ad_id),
                    campaign_name=mp_ad_data['campaign_name'],
                    ad_set_name=mp_ad_data['name'],
                    message=mp_ad_data['message'],
                    handle_url=mp_ad_data['handle_url'],
                    products=json.dumps(mp_ad_data['products']))
                ad_obj.save()
            except Exception, ex:
                logger.exception(
                    msg='There was an error creating a FacebookAd history record: %s' % ex)

            product_ids = ', '.join(
                [str(x.get('entity_id')) for x in mp_ad_data['products']])
            if ad_id:
                try:
                    report = ProductReport(
                        ad_obj=ad_obj,
                        ad_id=ad_id,
                        ad_name=mp_ad_data.get('name'),
                        ad_set_name=mp_ad_data.get('ad_set_name'),
                        product_ids=product_ids,
                        handle=mp_ad_data.get('handle'),
                        campaign_name=mp_ad_data.get('campaign_name'),
                        status='created',
                        status_updated_at=timezone.now()
                    )
                    report.save()
                except Exception, ex:
                    logger.exception(
                        msg='There was an error tracking facebook ad %s' % ex)
            return JsonResponse({
                'message': 'Ad has been uploaded!',
                'success': True,
            })
        except Exception, ex:
            logger.exception(
                msg='There was an error creating the carousel ad.')
            return JsonResponse({
                'message': 'We were not able to create the carousel ad: %s' % ex,
                'success': False,
            })


# ################### OTHERS ###################

class FacebookLogin(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'ad_login.html'
    login_url = '/accounts/login'

    def __init__(self):
        super(FacebookLogin, self).__init__()

    def get(self, request, *args, **kwargs):
        context = {
            'facebook_api': {
                'app_id': settings.FACEBOOK_API['app_id'],
                'version': settings.FACEBOOK_API['version']
            }
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        login_data = json.loads(request.body)
        token = login_data.get('token')
        f = FacebookConnect()
        token = f.get_long_lived_tokens(user_token=token)
        cache.set('long_lived_token', token, 7776000)
        return JsonResponse({
            'data': token
        })
