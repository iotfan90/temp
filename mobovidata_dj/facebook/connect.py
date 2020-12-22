# encoding: utf-8
import hashlib
import json
import logging
import requests

from django.conf import settings
from django.core.cache import cache
from django.forms.models import model_to_dict
from django.utils import timezone
from facebookads.adobjects import (adimage, adaccount, adcreative, adset, ad,
                                   campaign, adsinsights)
from facebookads.api import FacebookAdsApi
from facebookads.specs import ObjectStorySpec

from .models import ProductReport

logger = logging.getLogger(__name__)


class FacebookConnect(object):
    def __init__(self, *args, **kwargs):
        """
        Uploads images to Facebook and adds an 'img_hash' key:value to each row in products_images.
        products_images is a list of {'image_path': <FILEPATH>, 'product_id':<PRODUCT_ID>} dictionaries.
        """
        self.app_id = kwargs.get('app_id', settings.FACEBOOK_API['app_id'])
        self.app_secret = kwargs.get('app_secret', settings.FACEBOOK_API['app_secret'])
        self.account_id = kwargs.get('account_id', settings.FACEBOOK_API['account_id'])
        self.page_id = kwargs.get('page_id', settings.FACEBOOK_API['page_id'])
        self.instagram_actor_id = kwargs.get('instagram_actor_id', settings.FACEBOOK_API['instagram_actor_id'])
        self.version = kwargs.get('version', settings.FACEBOOK_API['version'])
        long_lived_token_cache_name = "long_lived_token_%s" % self.app_id
        self.user_token = cache.get(long_lived_token_cache_name, False)

        if not self.user_token:
            self.user_token = kwargs.get('user_token', settings.FACEBOOK_API.get('user_token'))
            if self.user_token:
                cache.set(long_lived_token_cache_name, self.user_token)
        if not self.user_token:
            logger.error('Please specify a user_token', extra=locals())
        else:
            FacebookAdsApi.init(
                self.app_id,
                self.app_secret,
                self.user_token
            )

        self.registration_failed = False

    def upload_image(self, path):
        # Create image Hash
        image = adimage.AdImage(parent_id=self.account_id)
        image[adimage.AdImage.Field.filename] = path
        image.remote_create()
        img_hash = image[adimage.AdImage.Field.hash]
        return img_hash

    def create_carousel_ad(self, link):
        """
        Creates a facebook carousel ad.
        :param link: a facebook LinkData object, complete with field and attachment data.
        :return: Facebook creative object that can be added to a FB ad set and campaign
        """
        story = ObjectStorySpec()
        story[story.Field.page_id] = self.page_id
        story[story.Field.link_data] = link
        story[story.Field.instagram_actor_id] = self.instagram_actor_id
        creative = adcreative.AdCreative(parent_id=self.account_id)
        creative[adcreative.AdCreative.Field.name] = 'Mobovida'
        creative[adcreative.AdCreative.Field.object_story_spec] = story
        creative.remote_create()
        return creative

    def create_ad(self, ad_set_id, ad_name, ad_is_active, creative):
        """
        Publishes a paused creative with the given name to the given ad set id.
        :param ad_set_id: ID of the ad set to which creative will be published
        :param ad_name: Name to give the creative
        :param creative: Facebook creative object.
        :return: Nothing
        """
        p_ad = ad.Ad(parent_id=self.account_id)
        p_ad[ad.Ad.Field.name] = ad_name
        p_ad[ad.Ad.Field.adset_id] = ad_set_id
        p_ad[ad.Ad.Field.creative] = {'creative_id': creative.get_id()}

        if ad_is_active:
            params = {'status': ad.Ad.Status.active}
        else:
            params = {'status': ad.Ad.Status.paused}

        if hasattr(settings, 'MOCK_AD_CREATION') and settings.MOCK_AD_CREATION is True:
            log_string = 'Mocking remote_create of ' + params['status'] + ' ad titled ' + ad_name + '.'
            logger.info(log_string)
        else:
            p_ad.remote_create(params=params)
        return p_ad

    def get_ad_sets(self, campaign=None, fields=None, use_cache=False):
        """
        Retrieves all ad sets in an account (limited to a specific campaign, if given)
        :param campaign: Campaign ID
        :param fields: Fields to return for the given ad sets. List. Default: [adset.AdSet.Field.name, adset.AdSet.Field.campaign_id]
        :param use_cache: Whether or not to use cached results instead of the actual FB api. If True, returned ad sets
        will not be up to date.
        Returns: List of ad sets with their name and ID.
        """
        CACHE_KEY = 'facebook.connect.ad_sets'
        if not fields:
            fields = [adset.AdSet.Field.name, adset.AdSet.Field.campaign_id,
                      adset.AdSet.Field.configured_status,
                      adset.AdSet.Field.effective_status,
                      adset.AdSet.Field.optimization_goal,
            ]
        if use_cache:
            ad_sets = cache.get(CACHE_KEY)
            if ad_sets:
                return ad_sets
        account_id = self.account_id
        params = {
            'limit': 500,
            'effective_status': ['ACTIVE'],
            'date_preset': 'last_14d',
        }
        p_parent = campaign or adaccount.AdAccount(account_id)
        rg_ad_sets = p_parent.get_ad_sets(fields, params)
        if use_cache:
            cache.set(CACHE_KEY, rg_ad_sets, 3600)
        return rg_ad_sets

    def get_campaigns(self, use_cache=False, fields=None):
        """
        Retrieves all campaigns in an account
        :param use_cache: Whether or not to use cached results instead of the actual FB api. If True, returned campaigns
        will not be up to date.
        :param fields: Fields to return for given campaigns. List. Default: [Campaign.Field.Name]
        :return: List of campaign IDs and names
        """
        CACHE_KEY = 'facebook.connect.campaigns'
        account_id = self.account_id
        account = adaccount.AdAccount(account_id)
        if not fields:
            fields = [campaign.Campaign.Field.name]
        if use_cache:
            rg_campaigns = cache.get(CACHE_KEY)
            if rg_campaigns:
                return rg_campaigns
        rg_campaigns = account.get_campaigns(fields, {
            'limit': 500,
            'effective_status': ['ACTIVE'],
        })
        if use_cache:
            cache.set(CACHE_KEY, rg_campaigns, 3600)
        return rg_campaigns

    def get_ad_insights(self, fields=None, start=None,
                        end=None, params=None, use_cache=True):
        start = start or timezone.now().strftime('%Y-%m-%d')
        end = end or timezone.now().strftime('%Y-%m-%d')

        fields = fields or [
            adsinsights.AdsInsights.Field.campaign_name,
            adsinsights.AdsInsights.Field.adset.AdSet_name,
            adsinsights.AdsInsights.Field.ad_name,
            adsinsights.AdsInsights.Field.campaign_id,
            adsinsights.AdsInsights.Field.impressions,
            adsinsights.AdsInsights.Field.ctr,
            adsinsights.AdsInsights.Field.cpm,
            adsinsights.AdsInsights.Field.cpc,
            adsinsights.AdsInsights.Field.cost_per_unique_click,
            adsinsights.AdsInsights.Field.unique_ctr,
            adsinsights.AdsInsights.Field.reach,
            adsinsights.AdsInsights.Field.actions,
            adsinsights.AdsInsights.Field.action_values,
            adsinsights.AdsInsights.Field.cost_per_action_type,
            #Insights.Field.relevance_score,
            adsinsights.AdsInsights.Field.spend,
            adsinsights.AdsInsights.Field.adset.AdSet_id,
            adsinsights.AdsInsights.Field.ad_id
        ]
        hash = hashlib.md5(str(fields) + str(params)).hexdigest()

        if not isinstance(params, dict):
            params = {
                'time_range': {'since': start, 'until': end},
                'level': 'ad',
                'limit': 1000
            }

        CACHE_KEY = 'facebook.connect.ad_insights_%s_%s_%s' % (start, end, hash)

        account_id = self.account_id
        account = adaccount.AdAccount(account_id)

        raw_insights = None

        if use_cache:
            cached = cache.get(CACHE_KEY)
            if cached:
                raw_insights = cached

        if not raw_insights:
            raw_insights = account.get_insights(fields=fields, params=params)

        if use_cache:
            if start == timezone.now().strftime('%Y-%m-%d'):
                CACHE_LEN = 600
            else:
                CACHE_LEN = 86400*3
            cache.set(CACHE_KEY, raw_insights, CACHE_LEN)

        # Turn 'offsite_conversion.fb_pixel_add_payment_info'
        # into 'pixel_add_payment_info_count'
        def clean_action_name(a, fmt):
            return fmt % (a['action_type']
                          .split('.')[-1]
                          .replace('fb_', '')
                          .replace('offsite_conversion', 'all_actions'))

        # Flatten the nested structre and give the metrics usable names

        def flatten_nested(ix):

            actions = map(dict, ix.pop('actions', None) or [])
            revenue = map(dict, ix.pop('action_values', None) or [])
            costs = map(dict, ix.pop('cost_per_action_type', None) or [])

            nums = {clean_action_name(a, 'num_%s'): a['value'] for a in actions}

            revs = {clean_action_name(a, 'revenue_from_%s'): a['value'] for a in revenue}

            costs = {clean_action_name(a, 'cost_per_%s'): a['value'] for a in costs}
            ix.update(nums)
            ix.update(revs)
            ix.update(costs)
            # Below is just casting ix as a dict()
            # But facebookads abstractobject throws key errors
            # in unusual circumstances
            return dict([(k, ix._data[str(k)]) for k in ix.keys() if k and str(k) in ix._data ])

        def prune_data(ix):
            return dict(ix,
                        # Impressions is a string for some reason
                        impressions=int(ix.get('impressions', '0')),
                        clicks=ix.get('num_link_click', 0),
                        sales=ix.get('num_pixel_purchase', 0),
                        sales_revenue=ix.get('revenue_from_pixel_purchase', 0),
                        sales_cpa=ix.get('cost_per_pixel_purchase', 0),
                        cost_per_sale=ix.pop('cost_per_pixel_purchase', 0),
                        cost_per_click=ix.pop('cost_per_link_click', 0),
                        add_to_cart=ix.get('num_pixel_add_to_cart', 0),
                        add_payment_info=ix.get('num_pixel_add_payment_info', 0),
                        total_revenue=ix.get('revenue_from_all_actions', 0),
                        )

        def complex_metrics(ix):
            return dict(ix,
                        profit=(ix['spend'] - ix['total_revenue']),

                        avg_view_content=(
                            ix['clicks'] and
                            (ix.get('num_pixel_view_content', 0) / ix['clicks']) or 0),
                        )

        return {
            ix['ad_id']: complex_metrics(prune_data(flatten_nested(ix)))
            for ix in raw_insights
        }

    # def check_token(self, token=None, app_id=None):
    #     app_id = app_id or selfapp_id
    #     token = token
    #     fb_url = 'https://graph.facebook.com/oauth/access_token_info?client_id=%s&access_token=%s' % (app_id, token)
    #     response = requests.get(fb_url, params=None)
    #     return response

    # def get_code(self, app_id=None, app_secret=None, user_token=None):
    #     app_id = app_id or selfapp_id
    #     app_secret = app_secret or selfapp_secret
    #     user_token = user_token or selfuser_token
    #     redirect_url = 'http://localhost:8000/facebook/ad-login/'
    #     fb_url = 'https://graph.facebook.com/oauth/client_code?'
    #     params = {
    #         'access_token': user_token,
    #         'client_secret': app_secret,
    #         'redirect_uri': redirect_url,
    #         'client_id': app_id
    #
    #     }
    #     response = requests.get(fb_url, params=params)
    #     return response
    #
    # def get_access_status(self, code, app_id=None, app_secret=None, user_token=None):
    #     app_id = app_id or selfapp_id
    #     app_secret = app_secret or selfapp_secret
    #     fb_url = 'https://graph.facebook.com/oauth/access_token?'
    #     redirect_url = 'http://localhost:8000/facebook/ad-login/'
    #     params = {
    #         'code': code,
    #         'client_id': app_id,
    #         'client_secret': app_secret,
    #         'redirect_uri': redirect_url
    #     }
    #     response = requests.get(fb_url, params=params)
    #     return response

    def get_long_lived_tokens(self, app_id=None, app_secret=None, user_token=None):
        """
        Get the long lived token by a short live one. The short token should be alive at this time
        :param app_id:
        :param app_secret:
        :param user_token:
        :return:
        """
        app_id = app_id or self.app_id
        app_secret = app_secret or self.app_secret
        user_token = user_token
        fb_url = '%s&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
            'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token',
            app_id, app_secret, user_token,)
        session = requests.session()
        fb_token = session.get(fb_url).content.split('&')[0].strip('access_token=')
        return fb_token

    def get_app_auth_token(self):
        app_auth_ep = (
            'https://graph.facebook.com/oauth/access_token'
            '?client_id=%s&client_secret=%s'
            '&grant_type=client_credentials'
        )
        response = requests.get(app_auth_ep % (self.app_id, self.app_secret))
        if response.status_code == 200:
            return response.content
        self.registration_failed = True
        return 'Get app auth token failed w/ status code %s: %s' % (response.status_code, json.loads(response.content))

    def register_webhook_endpoint(self, endpoint_url):
        """
        Registers an endpoint with a Facebook app so it is called when leads come in to facebook.
        Only needs to be run once for each endpoint.
        """
        app_auth_token = self.get_app_auth_token()
        if self.registration_failed:
            return app_auth_token

        params = {
            'debug': 'all',
            'object': 'page',
            'fields': 'leadgen',
            'verify_token': 'abc123',
            'callback_url': endpoint_url,
            'access_token': app_auth_token.split('=')[1]
        }
        fb_endpoint = 'https://graph.facebook.com/v2.6/%s/subscriptions' % self.app_id
        response = requests.post(fb_endpoint, data=params)
        if response.status_code == 200:
            return json.loads(response.content)
        return 'Registration with fb endpoint %s failed w/ status code %s: %s' % (fb_endpoint, response.status_code, response.content)

    def trigger_sample_leadgen(self):
        """
        Trigger the sample leadgen for testing
        :param page_id:
        :param user_token:
        :return:
        """
        params = {
            'object_id': self.page_id,
            'object': 'page',
            'field': 'leadgen',
            'access_token': self.user_token,
            'customer_fields': {'page_id': self.page_id}
        }
        stub_endpoint = 'https://graph.facebook.com/v2.6/%s/subscriptions_sample'
        result = requests.post(stub_endpoint % self.app_id, data=params)
        if result.status_code == 200:
            return json.loads(result.content)

    def get_page_access_token(self):
        """
        Used by subscribe_app_to_page to get the needed access token for subscribing an app to a page.
        :param user_token:
        :param page_id:
        :return:
        """
        response = requests.get('https://graph.facebook.com/v2.6/me/accounts?access_token=%s' % self.user_token)
        if response.status_code == 200:
            data = json.loads(response.content)['data']
            for r in data:
                if r['id'] == self.page_id:
                    return r['access_token']
            return 'page_id not found: %s' % self.page_id

    def subscribe_app_to_page(self):
        """
        Used to connect Facebook Apps to Facebook Pages. This connection is required to receive lead gens.
        :param page_id:
        :param user_token:
        :return:
        """
        page_access_token = self.get_page_access_token(self.user_token, self.page_id)
        subscription_ep = 'https://graph.facebook.com/v2.6/%s/subscribed_apps'
        result = requests.post(subscription_ep % self.page_id, data={'access_token': page_access_token})
        if result.status_code == 200:
            return json.loads(result.content)['success']

    def validate_token(self):
        """
        This function checks a token to see how much life it has left remaining
        @param token: the Facebook token of interest
        @type token: str
        Returns: True if the token is still valid, False if the token has < 30 minutes of lifetime left
        """
        return True

    def read_update_ads(self):
        account_id = self.account_id
        ad_account = adaccount.AdAccount(account_id)
        ad_iter = ad_account.get_ads(fields=[
            ad.Ad.Field.id,
            ad.Ad.Field.updated_time,
            ad.Ad.Field.status,
        ])
        ad_ids = []
        for ad in ad_iter:
            ad_ids.append(ad)
        for ad in ad_ids:
            ad_status = ad[ad.Ad.Field.status]
            ad_updated_time = ad[ad.Ad.Field.updated_time]
            ad_id = ad[ad.Ad.Field.id]
            prev_ads = ProductReport.objects.filter(ad_id=ad_id).order_by('-status_updated_at')
            if prev_ads:
                prev_ad = prev_ads[0]
                prev_ad = model_to_dict(prev_ad)
                if prev_ad.get('status') == ad_status:
                    pass
                else:
                    prev_ad.update({
                        'id': None,
                        'status': ad_status,
                        'status_updated_at': ad_updated_time
                    })
                    ProductReport.objects.create(**prev_ad)
        print ('Done')
