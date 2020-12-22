from __future__ import unicode_literals

import decimal
import json
import logging
import mandrill
import pytz
import requests
import urlparse

from adminsortable.models import SortableMixin
from collections import defaultdict
from datetime import timedelta, datetime
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.validators import MinValueValidator
from django.db import models
from django.shortcuts import render
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from polymorphic.models import PolymorphicModel
from polymorphic.showfields import ShowFieldType
from requests.exceptions import ConnectionError

from mobovidata_dj.analytics.models import (Customer, CustomerLifecycleTracking,
                                            CustomerPageView, CustomerSession)
from mobovidata_dj.facebook import carousel_ads
from mobovidata_dj.responsys.models import ResponsysCredential
from mobovidata_dj.responsys.utils import ResponsysApi
from modjento.models import (EavAttribute, SalesFlatOrder, SalesFlatQuote,
                             SalesFlatQuoteItem)

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class Campaign(models.Model):
    """
    Represents a process/a specific workflow related to customer lifecycle
    handling.(E.g. a process can be built to send email messages to users who
    have abandoned their carts at least 5 minutes ago.)

    For now processes don't support setting a specific frequency (e.g. whether
    to run them every 5 or 30 minutes). This will need some work on celery (using
    a databse scheduler) and can be added later as/if needed.
    """
    name = models.CharField(max_length=256)
    description = models.TextField()
    # For initial filtering
    funnel_step = models.IntegerField()
    lifecycle_messaging_stage = models.IntegerField(null=True)

    def run(self, preview_only=False):
        """
        Runs the campaign by sending the Customers through the pipeline and
        passing the result to the sender.
        @return:
        @rtype:
        """
        # Check to see if this campaign has already run in the past 5 minutes
        campaign_cache = 'campaign_run:%s' % self.name
        last_run = cache.get(campaign_cache)
        now = datetime.now()
        if last_run:
            time_since_last_run = now - last_run
            minutes_since = time_since_last_run.seconds / 60
            # If the process was run within 5 minutes, we should return so the caller can move on to the next campaign
            if minutes_since < 5:
                return 'continue on...'
        cache.set(campaign_cache, now, None)
        self.customers = self.initial_customer_set()
        if preview_only:
            self.customers = self.customers[:50]
        self.customer_data = {c: {} for c in self.customers}
        for f in self.filters.all():
            self.customers, self.customer_data = f.filter(self.customers, self.customer_data)
        if preview_only:
            if self.customers:
                return {'customers': self.customers,
                        'attributes': self.sender.do_send(
                            self.customers,
                            self.customer_data,
                            preview_only=True)}
            else:
                return {'customers': None,
                        'attributes': {'product_attributes': None,
                                       'product_string': None}}

        self.sender.send(self.customers, self.customer_data)

    def initial_customer_set(self):
        """
        Get initial customer set.
        For the campaign select page, we need to filter get the customers whose
        progression steps meet the requirements with customerlifecycletracking.
        @return: A list of customers
        """
        return Customer.objects.filter(
            customerlifecycletracking__funnel_step=self.funnel_step,
            customerlifecycletracking__lifecycle_messaging_stage=self.lifecycle_messaging_stage
        ).order_by('-customerlifecycletracking__modified_dt')[:999]

    def __str__(self):
        return self.name


# Child registration could be implemented with a class decorator(?) or a metaclass (on Filter)
@python_2_unicode_compatible
class Filter(ShowFieldType, PolymorphicModel, SortableMixin):
    campaign = models.ForeignKey(Campaign, related_name='filters')
    order = models.PositiveIntegerField(default=0, editable=True, db_index=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Filter'
        # Need to add a data migration that re-orders existing filters before enabling this.
        unique_together = ('campaign', 'order')

    def filter(self, customers, context):
        """
        Filter the set of customers and/or add customer related data to the context. The context
        is a dictionary containing data for each customer. The dictionary keys are the  customer
        uuids. The context will be used at the end of the processing to send out the messages
        to the customers.

        The reason we allow filtering and data gathering in one step is that some filtering
        operations will need to touch the same data to figure out which Customers to discard,
        that will be used for the Customers who we keep.

        Otherwise you should strive for making filters single purpose to keep them composable
        and reusable.

        The fact that Filters are passed and have to return a QuerySet means that in some
        cases the Customer objects will be read from the database multiple times (because
        some filtering operations will need to read the list of customers).

        An alternative solution would be to work with a list of customers, instead of a query
        set, as long as the initial number of customers is not to big (compared to the expected
        filtered down number).

        The all optimized solution would combine the above two approach: first work with QuerySets
        until we need to read the Customers and from that point on work with Customer objects.
        This would mean two different type of filters where the ones working with QuerySets
        always have to come before the ones working with Customers.

        @param customers: A QuerySet containing the Customers passed on from previous Filters in
            the filter chain.
        @type customers: django.db.models.query.QuerySet[Customer]
        @param context: A dictionary containing
        @type context: collections.defaultdict[dict]
        @return: A QuerySet of Customers who shall be processed further.
        @rtype: (django.db.models.query.QuerySet, collections.defaultdict[dict])
        """
        raise NotImplemented('You need to implement "filter" to have a working Filter subclass')

    def customers_to_queryset(self, customers):
        """
        Helper method to help turning a list of customers into a QuerySet. Only use when
        you have no better idea. An alternative solution is to take the original QuerySet
        and add an exclude(pk__in=...)
        @param customers:
        @return:
        """
        return Customer.objects.filter(pk__in=[c.pk for c in customers])

    def exclude_customers(self, customers, customers_to_exclude):
        """
        Simple helper function to exclude a list of customers from a QuerySet. Use this, if
        the customers to exclude are low (compared to the customers to include) AND if you
        have already read the customers (iterated over the QuerySet)

        @param customers:
        @type customers: django.db.models.query.QuerySet[Customer]
        @param customers_to_exclude: Iterable of Customers to exclude
        @type customers_to_exclude:
        @return:
        @rtype: django.db.models.query.QuerySet[Customer]
        """
        return customers.exclude(pk__in=[c.pk for c in customers_to_exclude])

    def __str__(self):
        return '%s [Campaign=%s]' % (self.__class__.__name__, self.campaign)

    def get_ordering_queryset(self):
        return Filter.objects.all()


class NoPDPBrowseAbandonInfoFilter(Filter):
    """
    Retrieves information related to customer's PDP-level browse abandon behavior.
    """
    def filter(self, customers, customer_data):
        if customers:
            customers, customer_data = self.get_pageview_ids(customers, customer_data)
        return customers, customer_data

    def get_pageview_ids(self, customers, customer_data):
        """
        Adds the last page viewed by the customer during their visit.
        @param customers: list(str, Customer)
        @param customer_data: dict(Customer: information about the customers
        behavior on the site that will be used in the email.
        @return:customers, customer_data
        """
        for c in customers:
            pages = CustomerPageView.objects.filter(
                id__in=c.customerlifecycletracking.noproduct_pageviews
            ).values_list('url_path', flat=True)
            customer_data[c]['url_paths'] = {p for p in pages}
            customer_data[c]['last_page_viewed'] = self.get_last_page_viewed(c)
            customer_data[c]['includes_products'] = 'no'
        return customers, customer_data

    def get_last_page_viewed(self, customer):
        """
        @param customer: Customer
        @return: complete URL of last page viewed by customer
        """
        latest_session = CustomerSession.objects.filter(customer=customer).order_by('-modified_dt').first()
        latest_pageview = CustomerPageView.objects.filter(session=latest_session).order_by('-modified_dt').first()
        if latest_pageview:
            url_path = latest_pageview.url_path
            if url_path[0] == '/':
                url_path = url_path[1:]
            return '%s%s' % (
                settings.MAGENTO_URL_PREFIXES.get('pdp', 'http://www.cellularoutfitter.com/'), url_path
            )
        else:
            return settings.MAGENTO_URL_PREFIXES.get('pdp', 'http://www.cellularoutfitter.com/')


class PDPBrowseAbandonInfoFilter(Filter):
    """
    Retrieves information related to customer's PDP-level browse abandon behavior.
    """
    def filter(self, customers, customer_data):
        if customers:
            customers, customer_data = self.verify_customer_product_pageviews(customers, customer_data)
            customers, customer_data = self.get_pageview_ids(customers, customer_data)
        return customers, customer_data

    def verify_customer_product_pageviews(self, customers, customer_data):
        """
        Removes customers from customers and customer_data if they do not have
        any product_pageviews in their messaging_data
        """
        filtered_customers = []
        for c in customers:
            if c.customerlifecycletracking.product_pageviews:
                filtered_customers.append(c)
            else:
                del customer_data[c]
        return filtered_customers, customer_data

    def get_pageview_ids(self, customers, customer_data):
        """
        Adds the full product ID of products viewed by the customer during their visit.
        @param customers: list(str, Customer)
        @param customer_data: dict(Customer: information about the customers
        behavior on the site that will be used in the email.
        @return: customers, customer_data
        """
        for c in customers:
            products = CustomerPageView.objects.filter(
                id__in=c.customerlifecycletracking.product_pageviews
            ).values_list('product_fullid', flat=True)
            customer_data[c]['product_ids'] = {(p.split('_')[0], p.split('_')[2]) for p in products}
            customer_data[c]['last_page_viewed'] = self.get_last_page_viewed(c)
            customer_data[c]['includes_products'] = 'yes'

        # Get details for unique product, category ids
        products_viewed = self.get_unique_products_viewed(customer_data)
        mp_unique = self.get_product_details(products_viewed)
        for c in customer_data.itervalues():
            c['products'] = [mp_unique.get(p, {}) for p in c['product_ids']]
        return customers, customer_data

    def get_last_page_viewed(self, customer):
        """
        @param customer: Customer
        @return: complete URL of last page viewed by customer
        """
        latest_session = CustomerSession.objects.filter(customer=customer).order_by('-modified_dt').first()
        latest_pageview = CustomerPageView.objects.filter(session=latest_session).order_by('-modified_dt').first()
        if latest_pageview:
            return '%s%s' % (
                settings.MAGENTO_URL_PREFIXES.get('pdp', 'http://www.cellularoutfitter.com'), latest_pageview.url_path
            )
        else:
            return settings.MAGENTO_URL_PREFIXES.get('pdp', 'http://www.cellularoutfitter.com')

    def get_unique_products_viewed(self, customer_data):
        """
        @param customer_data: Customer object-keyed dict containing a list with
        key 'products' and values in format (product_id, category_id).
        @return: List of unique products viewed in format (product_id, category_id)
        """
        # Fetch basic info about products in cart
        products_viewed = []
        for cd in customer_data.itervalues():
            products_viewed += cd['product_ids']
        # Return an unduplicated list of products viewed
        products_viewed = list(set(products_viewed))
        return products_viewed

    def get_product_details(self, products_viewed):
        """
        Unique list of tupled-product information. Format: [(product_id, category_id)].
        @return: dict(product_id:{rg_field_name:rg_field_value})
        """
        # Use modjento get_values to easily pull product data
        rg_fields = ['name', 'image', 'product_type',
                     'price', 'special_price',
                     'special_from_date', 'special_to_date',
                     'url_path', 'url_key']
        mp_values = EavAttribute.objects.get_values([p[0] for p in products_viewed], field_names=rg_fields)
        mp_unique = {product_id: mp_values[int(product_id[0])] for product_id in [p for p in products_viewed]}

        mp_unique = {k: v for k, v in mp_unique.iteritems() if v.get('price', False)}
        # Calculate savings information
        for p in mp_unique.keys():
            mp_unique[p]['product_full_id'] = '%s_2_%s' % (p[0], p[1])
            try:
                mp_unique[p]['save_percent'] = round(
                    (mp_unique[p]['price'] - mp_unique[p]['special_price']) / mp_unique[p]['price'],
                    4) * 100
                mp_unique[p]['save_dollars'] = int(round(mp_unique[p]['price'] - mp_unique[p]['special_price'], 0))
            except KeyError:
                mp_unique[p]['save_percent'] = 0
                mp_unique[p]['save_dollars'] = 0
                mp_unique[p]['special_price'] = mp_unique[p]['price']
        # Create image url key
        for product in mp_unique.items():
            product[1]['image_key'] = product[1]['image']

        # Add product image and URL
        for product in mp_unique.items():
            product[1]['url_path'] = '%s%s' % (
                carousel_ads.generate_url_prefix(int(product[0][1])).replace('.html', '/'),
                product[1]['url_key']
            )
            if '.html' not in product[1]['url_path'][-5:]:
                product[1]['url_path'] = '%s%s' % (product[1]['url_path'], '.html')
            product[1]['image'] = settings.MAGENTO_URL_PREFIXES['img'] + product[1]['image_key']

        return mp_unique


class ActiveCartInfoFilter(Filter):
    """
    1. Removes customers from customers and customer_data if their cart is
    associated with an order id.
    2. Adds details about the cart and the products in the cart to customer_data.
    """

    def filter(self, customers, customer_data):
        """
        @param customers: list[Customer]
        @param customer_data: dict[str, Customer]
        @return: list[Customer], dict[str, Customer]
        """
        customers, customer_data = self.get_cart_info(customers, customer_data)
        customers, customer_data = self.get_cart_details(customers, customer_data)
        return customers, customer_data

    def get_cart_info(self, customers, customer_data):
        """
        Gets aggregate cart data from Mage db
        """
        cart_ids = []
        for customer in customers:
            customer.cart_id = customer.customerlifecycletracking.cart_id
            cart_ids.append(customer.cart_id)
        # Limit carts to those that care active in the mage db.
        carts = SalesFlatQuote.objects.filter(entity_id__in=cart_ids, is_active=True)
        orders = {o.quote_id: o.increment_id for o in SalesFlatOrder.objects.filter(quote_id__in=cart_ids)}

        for customer in customers:
            if orders.get(customer.cart_id, False):
                CustomerLifecycleTracking.objects.set_lifecycle_stage_to_order(
                    orders.get(customer.cart_id, ''),
                    customer=customer
                )

        cart_details = {}
        filtered_customers = []

        for cart in carts:
            # Add additional 'cart-level' details here:
            if cart.items_count > 0:
                cart_details[cart.entity_id] = {
                    'cart_value': float(cart.base_grand_total),
                    'cart_coupon': cart.coupon_code,
                    'store_id': cart.store_id,
                    'quote_id': cart.entity_id,
                    'items_count': cart.items_count,
                    'base_subtotal': float(cart.base_subtotal),
                }
        for customer in customers:
            if customer.cart_id in cart_details:
                filtered_customers.append(customer)
                customer_data[customer].update(cart_details[customer.cart_id])
            else:
                del customer_data[customer]

        return filtered_customers, customer_data

    def __get_product_images(self, image_urls):
        """
        Accepts a string of | separated values and returns list of complete image URLs
        """
        base_img_url = settings.MAGENTO_URL_PREFIXES['img']
        return [urlparse.urljoin(base_img_url, u) for u in image_urls.split('|')]

    def get_cart_products_unique_items(self, cart_items):
        """
        Squeeze multiple items if they share the same product id
        @param cart_items: django.QuerySet
        @return: dict with keys equal to product ids and value equal to items info & list of product id and category id
        """
        cart_products = defaultdict(list)
        product_unique = set()
        for item in cart_items:
            quote_id = item.quote_id
            product_unique.add((item.product_id, item.added_from_category_id))
            cart_products[quote_id].append({'sku': item.sku,
                                            'name': item.name,
                                            'product_id': item.product_id,
                                            'quote_id': item.quote_id,
                                            'qty': int(item.qty),
                                            'base_price': float(item.base_price),
                                            'base_row_total': float(item.base_row_total),
                                            'base_row_total_incl_tax': float(item.base_row_total_incl_tax),
                                            'added_from_category_id': item.added_from_category_id,
                                            'product_full_id': '_'.join(
                                                [str(item.product_id), '2', str(item.added_from_category_id)]),
                                            'product_unique': (item.product_id, item.added_from_category_id), })
        return cart_products, product_unique

    def get_cart_details(self, customers, customer_data):
        """
        Gets products and products info related to cart IDs
        """
        cart_ids = [customer.cart_id for customer in customers]

        # Fetch basic info about products in cart
        cart_items = SalesFlatQuoteItem.objects.filter(quote_id__in=cart_ids)
        cart_products, product_unique = self.get_cart_products_unique_items(cart_items)

        # Use modjento get_values to easily pull product data
        rg_fields = ['name', 'image', 'price', 'special_price',
                     'url_path', 'url_key']
        mp_unique = EavAttribute.objects.get_values([p for p, _ in product_unique], field_names=rg_fields)
        for v in mp_unique.itervalues():
            v['image_key'] = v.get('image')
        for cart in cart_products.itervalues():
            for product in cart:
                if not product:
                    continue
                product_id, category_id = product['product_unique']
                data = mp_unique[product_id]
                if not data.get('price', False):
                    continue
                try:
                    data['save_percent'] = round(
                        (data['price'] - data['special_price']) / data['price'],
                        4) * 100
                    data['save_dollars'] = int(round(data['price'] - data['special_price'], 0))
                except KeyError:
                    data['save_percent'] = 0
                    data['save_dollars'] = 0
                    data['special_price'] = data['price']

                data['url_path'] = '%s%s.html' % (carousel_ads.generate_url_prefix(
                    category_id
                ).replace('.html', '/'), data['url_key'])
                if not data.get('image_key'):
                    continue
                data['image'] = settings.MAGENTO_URL_PREFIXES['img'] + data['image_key']
                product.update(data)

        for customer in customers:
            customer_data[customer]['products'] = cart_products[customer.cart_id]

        return customers, customer_data


class HasRIIDFilter(Filter):
    """
    Removes customers from customers and customer_data if they don't have an
    associated RIID in the db.
    """
    def filter(self, customers, customer_data):
        """
        Remove customers with no riid from customer_data and from customers
        @param customers: list[Customer]
        @param customer_data: dict[str, Customer]
        @return: list[Customer], dict[str, Customer]
        """
        filtered_customers = []
        for x in customers:
            if not x.riid:
                del customer_data[x]
            else:
                filtered_customers.append(x)
                customer_data[x]['riid'] = x.riid

        assert len(customer_data) == len(filtered_customers)
        return filtered_customers, customer_data


class Sender(PolymorphicModel):
    """
    Represents the final step in the customer lifecycle workflow, in which
    customer data is passed to an external API.

    To use, call the send method, which will call the API as described in the
    child model then log the result of the API call.
    """
    campaign = models.OneToOneField(Campaign, related_name='sender')

    def send(self, customers, context):
        # self.do_send(customers, context)
        if customers:
            response = self.do_send(customers, context)
        else:
            response = [{'Result': 'No recipients found'}]
        self.log_result(response)
        if customers:
            self.process_send_result(customers, response, context)

    def do_send(self, customers, context, preview_only=False):
        raise NotImplemented('You need to implement "filter" to have a working Filter subclass')

    def log_result(self, response):
        # Parse & log response for successful, failed, and total sends
        res = response
        if isinstance(res, list):
            sends = len(res)
            successes = len([line for line in res if line.get('success', '')])
            failures = len([line for line in res if not line.get('success', '')])
        else:
            sends = successes = failures = 0

        SenderLog.objects.create(
            response=response,
            sender=self,
            campaign=self.campaign,
            total_sends=sends,
            successful_sends=successes,
            failed_sends=failures
        )

    def process_send_result(self, customers, response, context):
        pass
        # For each customer.RIID in customers, check response status.

    def __str__(self):
        return self.campaign.name


class InactivityFilter(Filter):
    """
    Filters customers based on the number of minutes since the customer's last pageview.
    """
    inactivity_threshold = models.PositiveIntegerField(verbose_name="Inactivity threshold (minutes)",
                                                       validators=[MinValueValidator(limit_value=1)])

    def filter(self, customers, customer_data):
        """
        @param customers: list[Customer]
        @param customer_data: dict[str, Customer]
        @return: list[Customer], dict[str, Customer]
        """
        dt_now = timezone.now()
        if settings.DEBUG:
            dt_threshold = dt_now
        else:
            dt_threshold = dt_now - timedelta(minutes=self.inactivity_threshold)
        try:
            filtered = customers.filter(customerlifecycletracking__modified_dt__lt=dt_threshold)
        except (AttributeError, AssertionError):
            filtered = [c for c in customers if c.customerlifecycletracking.modified_dt < dt_threshold]
        filtered_customer_data = {c: customer_data[c] for c in filtered}
        return filtered, filtered_customer_data


class AbandonedCartCandidateFilter(Filter):
    """
    This is just a quick example to show/test the handling of multiple Filter types.
    """
    inactivity_threshold = models.PositiveIntegerField(verbose_name="Inactivity threshold (minutes)",
                                                       validators=[MinValueValidator(limit_value=1)])

    def filter(self, customers, context):
        try:
            filtered = customers.filter(
                customerlifecycletracking__modified_dt__lt=timezone.now() - timedelta(
                    minutes=self.inactivity_threshold
                )
            )
        except (AttributeError, AssertionError):
            filtered = [c for c in customers if
                        c.customerlifecycletracking.modified_dt < timezone.now() - timedelta(minutes=5)]

        return filtered, context


class StrandsProductRecsFilter(Filter):
    """
    Get strands-based product recommendations and include in customer_data
    """
    recommendation_remplate = models.CharField(max_length=50, default='prod_6')

    def filter(self, customers, customer_data):
        for customer in customers:
            if not hasattr(customer, 'customerstrandsid'):
                customer_data[customer]['includes_strands'] = 'no'
                continue
            if not customer_data[customer].get('products', False):
                products = ''
            else:
                products = self.stringify_products(customer_data[customer]['products'])
            params = {
                'apid': settings.STRANDS_APID,
                'tpl': self.recommendation_remplate,
                'item': products,
                'format': 'json',
                'user': customer.customerstrandsid.strands_id,
                'amount': 6,
            }
            response = requests.get(settings.STRANDS_ENDPOINT, params=params)
            if response.status_code == 200:
                results = json.loads(response.content)
                strands_products = []
                for r in results['result']['recommendations']:
                    product = r['metadata']
                    p = {
                        'url_path': product.get('link', ''),
                        'name': product.get('name', ''),
                        'special_price': float(product.get('price', '')),
                        'image': '%s' % product.get('picture', ''),
                        'price': float(product['properties'].get('cretail_price', [0])[0]),
                    }
                    try:
                        p['save_percent'] = round(
                            (p['price'] - p['special_price']) / p['price'], 4) * 100
                        p['save_dollars'] = int(round(p['price'] - p['special_price'], 0))
                    except KeyError:
                        p['save_percent'] = 0
                        p['save_dollars'] = 0
                        p['special_price'] = p['price']
                    strands_products.append(p)
                # customer_data[customer]['strands_product_attributes'] = ';;-;;'.join(strands_products[0].keys())
                if len(strands_products) > 0:
                    customer_data[customer]['includes_strands'] = 'yes'
                    customer_data[customer]['strands_products'] = strands_products
        return customers, customer_data

    def stringify_products(self, customer_products):
        products = []
        for p in customer_products:
            if p.get('added_from_category_id') != 32:
                if p.get('product_full_id', False):
                    products.append(p['product_full_id'])
        try:
            # return products[0]
            return '_._'.join(products)
        except IndexError:
            return ''


class Mandrill(Sender):
    """
    Sender instance for campaigns that uses mailchimp
    """
    def do_send(self, customers, customer_data, preview_only=False):
        self.campaign_name = self.campaign.name
        self.mandrill_client = mandrill.Mandrill(settings.MANDRILL_API_KEY)
        self.send_dt = datetime.now().isoformat()
        try:
            template_content = [{'content': 'campaign', 'name': self.campaign_name}]
            if settings.DEBUG:
                cnt = 0
                for user_id, cus_info in customer_data.items():
                    cnt += 1
                    if cnt == 3:
                        cus_info['riid'] = settings.USER_RIIDS[0]
                    else:
                        cus_info['riid'] = settings.USER_RIIDS[1]
            mp_email_riid, mp_riid_email = defaultdict(str), defaultdict(str)
            for user_id, cus_info in customer_data.items():
                if cus_info.get('riid'):
                    email = ResponsysApi().get_email_from_riid(cus_info['riid'])
                    # mp_email_riid[email] = cus_info['riid']
                    # mp_riid_email[cus_info['riid']] = email
                    cus_info['email'] = email
                else:
                    logger.warning('No riid found')
                    return
            merge_vars = self.format_data(customer_data, mp_riid_email)
            message = {
                'from_name': settings.MANDRILL_FROM_NAME,
                'url_strip_qs': None,
                'to': [{'email': r['rcpt'], 'type': 'to'} for r in merge_vars],
                'merge': True,
                'global_merge_vars': [
                    {
                        'name': 'merge1',
                        'content': 'merge1 content'
                    }
                ],
                # 'text': 'Example text content',
                'merge_vars': merge_vars,
                'inline_css': True,
                'track_clicks': True,
                'from_email': settings.MANDRILL_FROM_EMAIL,
                'headers': {'Reply-To': settings.MANDRILL_REPLY_TO_EMAIL},
                # 'html': '<p>Example HTML content</p>',
                'tracking_domain': None,
                'preserve_recipients': None,
                "track_opens": True,
                'signing_domain': None,
                'merge_language': 'handlebars',
                'tags': [
                    # 'cart_abandon',
                    self.campaign.name.replace(' ', '_').lower()
                ],
                'view_content_link': None,
                'important': False,
                # 'subject': 'We Found This Cart In Our Parking Lot',
                'recipient_metadata':
                    [{'rcpt': r['rcpt'], 'values': {'riid': mp_email_riid.get(r.get('rcpt'))}} for r in merge_vars],
            }
            if preview_only:
                return {'template_name': self.campaign_name,
                        'template_content': template_content,
                        'message': message}
            result = self.mandrill_client.messages.send_template(
                template_name=self.campaign_name, template_content=template_content, message=message, async=False,
                ip_pool=None, send_at=self.send_dt)
            return result
        except mandrill.Error, e:
            print 'A mandrill error occurred: %s - %s' % (e.__class__, e)
            raise

    def format_data(self, customer_data):
        merge_vars = []
        for user_id, cus_info in customer_data.items():
            content_vars = self.content_from_customer_data(cus_info)
            content_vars.append({'name': 'campaign_name', 'content': self.campaign.name.replace(' ', '_').lower()})
            content_vars.append({'name': 'campaign_strategy', 'content': 'lifecycle'})
            merge_vars.append(
                {'rcpt': cus_info['email'], 'vars': content_vars})
        return merge_vars

    def content_from_customer_data(self, mp_cus_data):
        content = []
        for key, value in mp_cus_data.items():
            content.append({'name': key, 'content': value})
        return content

    def process_send_result(self, customers, response, customer_data):
        """
        Action taken with the results from Mandrill's API response.  In this
        case, we increment customer's lifecycle messaging stage by 1 for each
        email that had a successfull API call.
        @param customers: List of Customer model objects (used in logging)
        @param response: Mandrill's API response.
        @param customer_data: dict()
        @return: Nothing
        """
        print "Logging customers and response... %s %s " % (customers, response)
        # Get email_address:riid map of customer_data
        email_riid_map = {}
        for v in customer_data.itervalues():
            email_riid_map[v['email']] = int(v['riid'])
        # Get successfully called RIIDs
        mp_successful_calls = []
        for r in response:
            if r.get('status', None) == 'sent':
                mp_successful_calls.append(email_riid_map.get(r['email']))
        CustomerLifecycleTracking.objects.filter(
            customer__riid__in=[i for i in mp_successful_calls]
        ).update(
            lifecycle_messaging_stage=models.F('lifecycle_messaging_stage') + 1
        )

class ResponsysEvent(Sender):
    """
    Sender instance for sending lifecycle campaigns at the event level.
    """

    def make_product_str(self, p, product_attributes):
        """
        Accepts a dict of product attributes and returns a ;-; sep. string of
        those product attributes
        This is the best way we know of to pass the equivalent of json objects
        to Responsys via API.
        """
        product = [u'%s' % p.get(a, '') for a in product_attributes if a not in ('images', 'product_unique')]
        return u';-;'.join(product)

    def jsonify_object(self, values):
        """
        Converts python object to string and returns it.
        @param values: Part of the data_package that isn't json-able (such as a
        list of tuples).
        @return: string
        """
        if isinstance(values, list):
            try:
                return ';-;'.join(values)
            except TypeError:
                return_list = []
                for v in values:
                    return_list.append(';-;'.join(v))
                return ';-;'.join(return_list)

    def make_request_payload(self, data_package):
        """
        @param data_package: A list of dictionaries where each row represents
        one customer's data.
        In each row, there is another list of dictionaries containing info about
        each product that we want to present to the customer via Responsys.
        @return: a JSON-able dictionary ready to be passed to the Responsys api
        via the requests package.
        """
        self.num_products = []
        self.product_attributes = {}
        # The attributes of each product that we want to send to Responsys
        if data_package[data_package.keys()[0]].get('products', False):
            self.product_attributes['products'] = [
                    k for k in data_package[data_package.keys()[0]]['products'][0].keys() if k not in (
                        'images', 'product_unique'
                    )
                ]
        for d in data_package.itervalues():
            if d.get('includes_strands', '') == 'yes':
                self.product_attributes['strands_products'] = d['strands_products'][0].keys()
            if d.get('internal_search_products'):
                self.product_attributes['internal_search_products'] = d['internal_search_products'][0].keys()
        # if data_package[data_package.keys()[0]].get('strands_products', False):
        # self.product_attributes['strands_products'] = data_package[data_package.keys()[0]]['strands_products'][0].keys()
        recipients = []
        for customer in data_package:
            opt_data = []
            customer_data = data_package[customer]
            self.product_details = ''
            if self.product_attributes.get('products', False):
                opt_data.append({
                    'name': 'product_attributes',
                    'value': ';;-;;'.join(map(str, self.product_attributes['products']))
                })
                # product_details is used when preview_only=True in the do_send method
                self.product_details = ';;-;;'.join(map(str, self.product_attributes['products']))
            if customer_data.get('includes_strands', '') == 'yes':
                self.strands_product_attributes = customer_data['strands_products'][0].keys()
                opt_data.append({'name': 'strands_product_attributes',
                                 'value': ';;-;;'.join(map(str, self.product_attributes['strands_products']))})
            if customer_data.get('internal_search_products'):
                self.internal_seach_products = customer_data['internal_search_products'][0].keys()
                opt_data.append({
                    'name': 'internal_search_product_attributes',
                    'value': ';;-;;'.join(map(str, self.product_attributes['internal_search_products']))
                })
            for k, values in customer_data.iteritems():
                if k not in ('riid', 'products', 'strands_products', 'internal_search_products'):
                    if isinstance(values, decimal.Decimal):
                        values = str(values)
                    elif isinstance(values, list) or isinstance(values, set):
                        values = self.jsonify_object(values)
                    opt_data.append({'name': k, 'value': values})
                if k in ('products', 'strands_products', 'internal_search_products'):
                    """ Each product's data will be sep by ;;-;;
                        Attributes for each product will be sep by ;;_;;"""
                    self.num_products.append(len(values))

                    opt_data_products = [self.make_product_str(p, self.product_attributes[k]) for p in values]
                    opt_data_products_s = ';;-;;'.join(opt_data_products)
                    opt_data.append({'name': k, 'value': opt_data_products_s})
                # if k == 'strands_products':
                #     opt_data_products = [self.make_product_str(p, self.strands_product_attributes) for p in values]
                #     opt_data_products_s = ';;-;;'.join(opt_data_products)
                #     opt_data.append({'name': 'strands_products', 'value': opt_data_products_s})
            self.opt_data = [k['name'] for k in opt_data]
            for r in opt_data:
                if r['name'] == 'strands_product_attributes':
                    r['name'] = 'STRANDS_ATTRIBUTES'
                elif r['name'] == 'internal_search_product_attributes':
                    r['name'] = 'PRODUCT_ATTRIBUTES'
                r['name'] = r['name'].upper()
            recip = {
                "recipient": {
                    "listName": {
                        "folderName": self.list_folder,
                        "objectName": self.list_name,
                    },
                    # "recipientId" : 274342105,
                    "recipientId": customer_data.get('riid'),
                    "emailFormat": "HTML_FORMAT"
                },
                "optionalData": opt_data
            }
            recipients.append(recip)
        return {
            "customEvent": {
                "eventNumberDataMapping" : '',
                "eventDateDataMapping" : '',
                "eventStringDataMapping" : ''
            },
            "recipientData": recipients
        }

    def do_send(self, customers, data, preview_only=False):
        """
        The primary method of this object, called from the send() method in the Sender() parent class.
        Packages data and triggers a campaign send in Responsys, then returns the result of the attempted send.

        @param customers: List of Customer model objects. Used for logging purposes after this call is complete.
        @param data: A list of dictionaries containing customer data that we will pass to Responsys.
        @param preview_only: bool
        @return: Responsys's API response. For examples of possible responses, please see the Responsys REST API docs.
        """
        # Responsys limits API calls to 999 recipients
        customers = customers[:999]
        data = {c: data[c] for c in customers}
        auth = ResponsysCredential.objects.all()[0]
        self.headers = {'Authorization': auth.token}
        self.auth = auth
        self.endpoint = self.auth.endpoint + '/rest/api/v1.1/events/' + self.campaign.name
        # self.endpoint = '%s/rest/api/v1.1/campaigns/%s/email' % (self.auth.endpoint, self.campaign.name)
        self.list_folder = '!MageData'
        self.list_name = 'CONTACT_LIST'
        self.campaign_name = self.campaign.name
        self.request_payload = self.make_request_payload(data)
        for i in self.request_payload['recipientData'][0]['optionalData']:
            i['name'] = i['name'].upper()
        if preview_only:
            try:
                recip_data = self.request_payload['recipientData'][0]['optionalData']
                for r in recip_data:
                    if r['name'] == 'products':
                        product_string = r['value']
            except IndexError:
                product_string = ("This campaign has no pending sends, so we cant "
                                  "show you a preview of the product string")
            return {'product_attributes': self.product_details,
                    'optional_data': self.opt_data,
                    'product_string': product_string}
        try:
            r = requests.post(self.endpoint, json=self.request_payload, headers=self.headers)
            if r.status_code == 200:
                r_content = json.loads(r.content)
            else:
                r_content = {'There was an error. Request status code: %s' % r.status_code}
            return r_content
        except ConnectionError, ex:
            logger.exception('Error: %s', ex)
            return {'There was a ConnectionError: %s' % ex}

    def get_profile_data(self, riid):
        """
        Used to get email address from an RIID.
        @param riid: integer representing a unique id in Responsys.
        @return: Responsys's API response.
        """
        ep = self.auth['endpoint'] + "/rest/api/v1.1/lists/" + self.list_name + "/members/" + str(riid)
        fields = {'fs': 'all'}
        r = requests.get(ep, params=fields, headers=self.headers)
        return r

    def process_send_result(self, customers, response, customer_data):
        """
        Action taken with the results from Responsys's API response.  In this
        case, we increment customer's lifecycle messaging stage by 1 for each
        RIID that had a successfull API call.
        For unsuccessful API calls we change the customer's funnel_step and
        lifecycle_messaging_stage to 0
        @param customers: List of Customer model objects (used in logging)
        @param response: Responsys's API response.
        @param customer_data: Dict of customer data
        @return: void
        """

        print "Logging customers and response... %s %s" % (customers, response)

        if isinstance(response, unicode):
            response = eval(response)
        elif isinstance(response, dict):
            raise Exception(
                'There was a problem with the API call. RESPONSE: %s  REQUEST: %s' % (response, self.request_payload))

        CustomerLifecycleTracking.objects.filter(
            customer__riid__in=[r.get('recipientId', None) for r in response if r.get('success', None)]).update(
            lifecycle_messaging_stage=models.F('lifecycle_messaging_stage') + 1)

        failed_calls = []
        for i, r in enumerate(response):
            if not r.get('success', False):
                failed_calls.append(customer_data[customers[i]]['riid'])

        CustomerLifecycleTracking.objects.filter(customer__riid__in=failed_calls).update(
            lifecycle_messaging_stage=0, funnel_step=0)


class Responsys(Sender):
    """
    Sender instance for CartAbandon campaigns. campaign.senders.send(customers, context) calls the primary method.
    """

    def make_product_str(self, p, product_attributes):
        """
        Accepts a dict of product attributes and returns a ;-; sep. string of
        those product attributes
        This is the best way we know of to pass the equivalent of json objects
        to Responsys via API.
        """
        product = [u'%s' % p.get(a, '') for a in product_attributes if a not in ('images', 'product_unique')]
        return u';-;'.join(product)

    def jsonify_object(self, values):
        """
        Converts python object to string and returns it.
        @param values: Part of the data_package that isn't json-able (such as a list of tuples).
        @return: string
        """
        if isinstance(values, list):
            try:
                return ';-;'.join(values)
            except TypeError:
                return_list = []
                for v in values:
                    return_list.append(';-;'.join(v))
                return ';-;'.join(return_list)

    def make_request_payload(self, data_package):
        """
        @param data_package: A list of dictionaries where each row represents one customer's data.
        In each row, there is another list of dictionaries containing info about
        each product that we want to present to the customer via Responsys.
        @return: a JSON-able dictionary ready to be passed to the Responsys api via the requests package.
        """
        self.num_products = []
        self.product_attributes = {}
        # The attributes of each product that we want to send to Responsys
        if data_package[data_package.keys()[0]].get('products', False):
            self.product_attributes['products'] = [
                    k for k in data_package[data_package.keys()[0]]['products'][0].keys() if k not in (
                        'images', 'product_unique'
                    )
                ]
        for d in data_package.itervalues():
            if d.get('includes_strands', '') == 'yes':
                self.product_attributes['strands_products'] = d['strands_products'][0].keys()
            if d.get('internal_search_products'):
                self.product_attributes['internal_search_products'] = d['internal_search_products'][0].keys()
        # if data_package[data_package.keys()[0]].get('strands_products', False):
        # self.product_attributes['strands_products'] = data_package[data_package.keys()[0]]['strands_products'][0].keys()
        recipients = []
        for customer in data_package:
            opt_data = []
            customer_data = data_package[customer]
            self.product_details = ''
            if self.product_attributes.get('products', False):
                opt_data.append({
                    'name': 'product_attributes',
                    'value': ';;-;;'.join(map(str, self.product_attributes['products']))
                })
                # product_details is used when preview_only=True in the do_send method
                self.product_details = ';;-;;'.join(map(str, self.product_attributes['products']))
            if customer_data.get('includes_strands', '') == 'yes':
                self.strands_product_attributes = customer_data['strands_products'][0].keys()
                opt_data.append({'name': 'strands_product_attributes',
                                 'value': ';;-;;'.join(map(str, self.product_attributes['strands_products']))})
            if customer_data.get('internal_search_products'):
                self.internal_seach_products = customer_data['internal_search_products'][0].keys()
                opt_data.append({
                    'name': 'internal_search_product_attributes',
                    'value': ';;-;;'.join(map(str, self.product_attributes['internal_search_products']))
                })
            for k, values in customer_data.iteritems():
                if k not in ('riid', 'products', 'strands_products', 'internal_search_products'):
                    if isinstance(values, decimal.Decimal):
                        values = str(values)
                    elif isinstance(values, list) or isinstance(values, set):
                        values = self.jsonify_object(values)
                    opt_data.append({'name': k, 'value': values})
                if k in ('products', 'strands_products', 'internal_search_products'):
                    """ Each product's data will be sep by ;;-;;
                        Attributes for each product will be sep by ;;_;;"""
                    self.num_products.append(len(values))

                    opt_data_products = [self.make_product_str(p, self.product_attributes[k]) for p in values]
                    opt_data_products_s = ';;-;;'.join(opt_data_products)
                    opt_data.append({'name': k, 'value': opt_data_products_s})
                # if k == 'strands_products':
                #     opt_data_products = [self.make_product_str(p, self.strands_product_attributes) for p in values]
                #     opt_data_products_s = ';;-;;'.join(opt_data_products)
                #     opt_data.append({'name': 'strands_products', 'value': opt_data_products_s})
            self.opt_data = [k['name'] for k in opt_data]
            recip = {
                "recipient": {
                    "listName": {
                        "folderName": self.list_folder,
                        "objectName": self.list_name,
                    },
                    # "recipientId" : 274342105,
                    "recipientId": customer_data.get('riid', 336723265),
                    "emailFormat": "HTML_FORMAT"
                },
                "optionalData": opt_data
            }
            recipients.append(recip)
        return {
            # "customEvent": {
            #     "eventNumberDataMapping" : '',
            #     "eventDateDataMapping" : '',
            #     "eventStringDataMapping" : ''
            # },
            "recipientData": recipients
        }

    def do_send(self, customers, data, preview_only=False):
        """
        The primary method of this object, called from the send() method in the Sender() parent class.
        Packages data and triggers a campaign send in Responsys, then returns the result of the attempted send.

        @param customers: List of Customer model objects. Used for logging purposes after this call is complete.
        @param data: A list of dictionaries containing customer data that we will pass to Responsys.
        @param preview_only: bool
        @return: Responsys's API response. For examples of possible responses, please see the Responsys REST API docs.
        """
        # Responsys limits API calls to 999 recipients
        customers = customers[:999]
        data = {c: data[c] for c in customers}
        auth = ResponsysCredential.objects.all()[0]
        self.headers = {'Authorization': auth.token}
        self.auth = auth
        # self.endpoint = self.auth.endpoint + '/rest/api/v1.1/events/' + self.campaign.name
        self.endpoint = '%s/rest/api/v1.1/campaigns/%s/email' % (self.auth.endpoint, self.campaign.name)
        self.list_folder = '!MageData'
        self.list_name = 'CONTACT_LIST'
        self.campaign_name = self.campaign.name
        self.request_payload = self.make_request_payload(data)
        for i in self.request_payload['recipientData'][0]['optionalData']:
            i['name'] = i['name'].upper()
        if preview_only:
            try:
                recip_data = self.request_payload['recipientData'][0]['optionalData']
                for r in recip_data:
                    if r['name'] == 'products':
                        product_string = r['value']
            except IndexError:
                product_string = ("This campaign has no pending sends, so we cant "
                                  "show you a preview of the product string")
            return {'product_attributes': self.product_details,
                    'optional_data': self.opt_data,
                    'product_string': product_string}
        try:
            r = requests.post(self.endpoint, json=self.request_payload, headers=self.headers)
            if r.status_code == 200:
                r_content = json.loads(r.content)
            else:
                r_content = {'There was an error. Request status code: %s' % r.status_code}
            return r_content
        except ConnectionError, ex:
            logger.exception('Error: %s', ex)
            return {'There was a ConnectionError: %s' % ex}

    def get_profile_data(self, riid):
        """
        Used to get email address from an RIID.
        @param riid: integer representing a unique id in Responsys.
        @return: Responsys's API response.
        """
        ep = self.auth['endpoint'] + "/rest/api/v1.1/lists/" + self.list_name + "/members/" + str(riid)
        fields = {'fs': 'all'}
        r = requests.get(ep, params=fields, headers=self.headers)
        return r

    def process_send_result(self, customers, response, customer_data):
        """
        Action taken with the results from Responsys's API response.  In this case, we increment customer's
        lifecycle messaging stage by 1 for each RIID that had a successfull API call.
        For unsuccessful API calls we change the customer's funnel_step and lifecycle_messaging_stage to 0
        @param customers: List of Customer model objects (used in logging)
        @param response: Responsys's API response.
        @param customer_data: Dict of customer data
        @return: void
        """

        print "Logging customers and response... %s %s" % (customers, response)

        if isinstance(response, unicode):
            response = eval(response)
        elif isinstance(response, dict):
            raise Exception(
                'There was a problem with the API call. RESPONSE: %s  REQUEST: %s' % (response, self.request_payload))

        CustomerLifecycleTracking.objects.filter(
            customer__riid__in=[r.get('recipientId', None) for r in response if r.get('success', None)]).update(
            lifecycle_messaging_stage=models.F('lifecycle_messaging_stage') + 1)

        failed_calls = []
        for i, r in enumerate(response):
            if not r.get('success', False):
                failed_calls.append(customer_data[customers[i]]['riid'])

        CustomerLifecycleTracking.objects.filter(customer__riid__in=failed_calls).update(
            lifecycle_messaging_stage=0, funnel_step=0)


class SearchAbandonFilter(Filter):
    def filter(self, customers, customer_data):
        if customers:
            customers, customer_data = self.get_top_queries(customers, customer_data)
        return customers, customer_data

    def get_top_queries(self, customers, customer_data):
        from .utils import get_internal_search_products
        for customer, data in customer_data.items():
            top_four_results = get_internal_search_products(
                eval(customer.customerlifecycletracking.lifecycle_messaging_data)['SEARCH'][0])
            customer_data[customer]['internal_search_term'] = eval(
                customer.customerlifecycletracking.lifecycle_messaging_data
            )['SEARCH'][0]
            if len(top_four_results) > 0:
                customer_data[customer]['includes_search_products'] = 'yes'
                customer_data[customer]['internal_search_products'] = top_four_results
            else:
                customer_data[customer]['includes_search_products'] = 'no'

        return customers, customer_data


class DjangoEmailBackendSender(Sender):
    """
    A quick example to show/test handling of multiple Sender types
    """
    from_email = models.EmailField()
    auth_user = models.CharField(max_length=50, null=True, blank=True)
    auth_password = models.CharField(max_length=50, null=True, blank=True)
    # Probably wise to use choices here
    connection = models.CharField(max_length=200, null=True, blank=True)

    # Could as well be a TextField or a ForeignKey to a template table (storing templates in TextFields)
    #   -> there are django apps for that
    template = models.CharField(max_length=200)
    subject = models.CharField(max_length=200)

    def send(self, customers, context):
        for customer in customers:
            # For the sake of the example. Customers don't have an email field yet
            email = getattr(customer, 'email', 'nobody@nowhere.no')
            send_mail(self.subject, render(self.template, context=context[customer.uuid]),
                      self.from_email, (email,))


class SenderLog(models.Model):
    """
    Define the fields for SenderLog
    """
    campaign = models.ForeignKey(Campaign)
    sender = models.ForeignKey(Sender)
    response = models.TextField()
    send_datetime = models.DateTimeField(auto_now_add=True)
    total_sends = models.IntegerField(default=-1)
    successful_sends = models.IntegerField(default=-1)
    failed_sends = models.IntegerField(default=-1)


class OrderConfirmationSendLog(models.Model):
    """
    Define fields to record order confirmation sends.
    response is either 0 (failure) or 1 (success)
    """
    order_id = models.IntegerField(primary_key=True)
    order_updated_at = models.DateTimeField()
    base_grand_total = models.DecimalField(max_digits=12, decimal_places=4)
    response = models.IntegerField()
    created_dt = models.DateTimeField(auto_now_add=True)


class OrderConfirmationEmailsLog(models.Model):
    """
    Fields related to tracking order confirmation emails sent for each order id
    """
    order_id = models.CharField(max_length=50)
    order_updated_at = models.DateTimeField()
    base_grand_total = models.DecimalField(max_digits=12, decimal_places=4)
    # order_grand_total_key = models.CharField(max_length=256)
    response = models.IntegerField()
    created_dt = models.DateTimeField(auto_now_add=True)
    updated_dt = models.DateTimeField(auto_now=True)

    @classmethod
    def check_order_sends(self, order_map):
        """
        Evaluates orders in orders to see if we need to send an order confirm email.
        We don't need to send an order confirm email if all of the following are true:
         order.order_id is in OrderConfirmationSendLog
         order.order_grand_total == OrderConfirmationSendLog.order.order_grand_total
         order.email_sent != 1
        @param order_map: dict[unicode, SalesFlatOrder]
        @return: QuerySet
        """
        sent_orders = OrderConfirmationEmailsLog.objects.filter(order_id__in=order_map.keys())
        sent_orders_count = defaultdict(int)
        for o in sent_orders:
            sent_orders_count[o.order_id] += 1
        for order_id, num_records in sent_orders_count.iteritems():
            if num_records >= 2:
                del order_map[order_id]
        # use order_id & base_grand_total as the key
        sent_orders = {'%s_%2.2f' % (o.order_id, o.base_grand_total): o for o in sent_orders}
        order_map = {'%s_%2.2f' % (k, v.base_grand_total): v for k, v in order_map.iteritems()}
        if not sent_orders:
            return {k.split('_')[0]: v for k, v in order_map.iteritems()}
        for order_grand_total_key, sent_order in sent_orders.iteritems():
            if order_map.get(order_grand_total_key, False):
                del order_map[order_grand_total_key]

        return {k.split('_')[0]: v for k, v in order_map.iteritems()}


class ProductReviewEntity(models.Model):
    """
    Store reviews for each product in each order
    """
    email = models.CharField(max_length=256, null=True)
    order_id = models.CharField(max_length=256)
    product_id = models.IntegerField()
    rating = models.IntegerField()
    price_paid = models.DecimalField(max_digits=12, decimal_places=4)
    review_title = models.CharField(max_length=256)
    review_content = models.TextField()
    nickname = models.CharField(max_length=256)
    created_dt = models.DateTimeField(auto_now_add=True)


class OrderReviewSendLog(models.Model):
    order_id = models.IntegerField(primary_key=True)
    customer_email = models.CharField(max_length=256)
    response = models.IntegerField()
    created_dt = models.DateTimeField(auto_now_add=True)


class BirthdaySubmission(models.Model):
    riid = models.CharField(primary_key=True, max_length=128)
    frequency = models.TextField()
    color = models.CharField(max_length=128, null=True)
    color_code = models.CharField(max_length=128, null=True)
    con_response_success = models.IntegerField()
    pet_response_success = models.IntegerField()
    con_response = models.TextField()
    pet_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ShippingStatusTracking(models.Model):
    """
    Stores updates from Aftership relating to customer tracking information
    """
    order_id = models.IntegerField(primary_key=True)
    updated_at = models.DateTimeField(auto_now=True)
    event = models.CharField(max_length=128)
    courier = models.CharField(max_length=128)
    tracking_number = models.CharField(max_length=128)
    confirmation_sent = models.BooleanField(default=False)
    nps_sent = models.BooleanField(default=False)
    product_review_sent = models.BooleanField(default=False)

    @classmethod
    def get_order_ids(self):
        # Order_ids that have status 'Delivered' and nps_email not yet sent and delivered within 5 days.
        current_time = datetime.now(timezone.utc).astimezone(pytz.timezone('US/Pacific'))
        target_date = current_time - timedelta(days=5)
        return map(int, [
            obj.order_id for obj in ShippingStatusTracking.objects.filter(
                event='Delivered', nps_sent=False, updated_at__lte=target_date, order_id__startswith='2')
            ])[:200]

    @classmethod
    def update_nps_sent(self, res, orderids):
        # Update customers who've been sent NPS email after successful Responsys email blast
        response = res['rg_response']
        for i, r in enumerate(response):
            ShippingStatusTracking.objects.filter(
                order_id=orderids[i]
            ).update(nps_sent=True)

    @classmethod
    def send_nps_emails(self):
        """
        Sends Net Promoter Score email to customer's whose order status is 'Delivered'
        """
        from mobovidata_dj.responsys.utils import ResponsysApi
        r_api = ResponsysApi()

        # Order_ids that have status 'Delivered' and nps_email not yet sent.
        rg_order_ids = self.get_order_ids()

        # Dict {order_id: email}
        # mp_orderid_emails = {
        #     oid: SalesFlatOrder.objects.get(increment_id=oid).customer_email for oid in rg_order_ids
        # }
        mp_orders = SalesFlatOrder.objects.filter(
            increment_id__in=rg_order_ids).values('customer_email', 'increment_id')
        mp_orderid_emails = {x['increment_id']: x['customer_email'] for x in mp_orders}
        # Dict {email: riid}
        if settings.DEBUG:
            mp_email_riids = r_api.get_riid_from_email(settings.RESPONSYS_EMAIL)
        else:
            mp_email_riids = r_api.get_riid_from_email(mp_orderid_emails.values())

        mp_emails_orderids = {v: k for k, v in mp_orderid_emails.items()}
        riid_orderids = {v: mp_emails_orderids[k] for k, v in mp_email_riids.items()}

        recipients = []
        orderids = []
        for riid, orderid in riid_orderids.items():
            try:
                rint = int(riid)
                recipient = {'recipient': {'recipientId': riid,
                                           'listName': {'folderName': '!MageData',
                                                        'objectName': 'CONTACT_LIST'},
                                           'emailFormat': 'HTML_FORMAT'}}
                recipients.append(recipient)
                orderids.append(orderid)
            except:
                continue

        res = r_api.send_email_campaign('CO_NPS_2_LIFE', recipients)
        if isinstance(res, dict):
            self.update_nps_sent(res, orderids)
        return False


class OopsEmailSendLog(models.Model):
    """
    Define fields to record oops email sends.
    response is either 0 (failure) or 1 (success)
    """
    order_id = models.IntegerField(primary_key=True)
    response = models.IntegerField()
    created_dt = models.DateTimeField(auto_now_add=True)
    updated_dt = models.DateTimeField(auto_now=True)
