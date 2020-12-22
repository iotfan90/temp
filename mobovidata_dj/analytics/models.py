from __future__ import unicode_literals

import json
import requests
import uuid

from datetime import timedelta
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


# Not used yet.
class ProductReviews(models.Model):
    """
    Not yet implemented.
    Will Hold product reviews placed by customers.
    """
    # All Field name made lowercase.
    riid_field = models.IntegerField(db_column='RIID_')
    order_id = models.IntegerField(db_column='ORDER_ID')
    product_id = models.CharField(db_column='PRODUCT_ID', max_length=30)
    rating = models.IntegerField(db_column='RATING')
    price_paid = models.FloatField(db_column='PRICE_PAID')
    qty = models.IntegerField(db_column='QTY')
    review_title = models.TextField(db_column='REVIEW_TITLE', blank=True,
                                    null=True)
    review_content = models.TextField(db_column='REVIEW_CONTENT', blank=True,
                                      null=True)
    nickname = models.TextField(db_column='NICKNAME', blank=True,
                                null=True)
    review_dt = models.DateTimeField(blank=True, null=True)
    review_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'product_reviews'
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"


class CustomerManager(models.Manager):
    """ Manager for handling secondary actions that must take place as a result
    of creating/updating customer model """

    def create_customer(self, riid=None):
        riid = self.int_riid(riid)
        if riid:
            customer, result = self.get_or_create(riid=riid)
        else:
            customer = self.create()
            customer.save()
        return customer

    def int_riid(self, riid):
        """
        Turns RIID value into integer.  If this can't be done
        (or if RIID is none), returns None
        :param riid: riid (can be none)
        :return: integer riid or None
        """
        try:
            riid = int(riid)
        except ValueError:
            riid = None
        except TypeError:
            riid = None
        return riid

    def update_customer(self, customer_uuid, riid):
        """
        Adds RIID to customer record. If RIID already exists in table, returns
        the UUID corresponding to that RIID.
        :param customer_uuid: UUID passed by the view. If None, a uuid is
        created.
        :param riid: Should be an integer representing the customer's ID in
        responsys
        :rtype: dict
        """

        riid = self.int_riid(riid)
        customer_uuid = Customer.objects.get_or_create(uuid=customer_uuid)[0]

        update_result = {'customer': customer_uuid}

        if riid:
            riid_filter = Customer.objects.filter(riid=riid)
            if riid_filter.exists():
                riid_customer = riid_filter.get()
                if riid_customer != customer_uuid:
                    self.change_sessions_fk(customer_uuid, riid_customer)
                update_result['customer'] = riid_customer
                update_result['action'] = 'Found existing customer with this riid'
            else:
                customer_uuid.riid = riid
                customer_uuid.save()
        return update_result

    def get_customer_from_riid(self, riid=None):
        """ Returns customer record based on riid record """
        return self.get_or_create(riid=riid)

    def change_sessions_fk(self, og_customer, new_customer):
        """ Re-associates sessions from original UUID to RIID's UUID
            :param new_customer: Customer instance for the record with RIID
            :param og_customer: Customer uuid for a record without an RIID.
            If None, this function does nothing.
        """
        try:
            sessions = og_customer.customersession_set.all()
            for sesh in sessions:
                new_customer.customersession_set.add(sesh)
        except Customer.DoesNotExist:
            # If the current UUID isn't registered in the database, do nothing
            pass

    def add_customer(self, uuid):
        """ Adds user's existing UUID to db """
        return self.create(uuid=uuid)

    def lifecycle_prospects(self, inactivity_threshold, funnel_step):
        """
        :param lifecycle_messaging_stage: Name of the lifecycle stage to use in
        filter (similar to WHERE lifecycle_messaging_stage ==
        lifecycle_messaging_stage) Default: None (str)
        :param inactivity_threshold: Users having an inactivity time greater
        than this, will be included (minutes).
        :type inactivity_threshold: int
        :param funnel_step: The funnel step to use as a filter (similar to
        WHERE funnel_step == funnel_step) (int)
        :return: Queryset object for all customers and related data that meet
        the param criteria
        """
        last_active = timezone.now() - timedelta(minutes=inactivity_threshold)

        return Customer.objects.filter(
            customerlifecycletracking__funnel_step=funnel_step,
            # riid__isnull=False,
            # customerlifecycletracking__lifecycle_messaging_stage_link__like=lifecycle_messaging_stage,
            customerlifecycletracking__modified_dt__lte=last_active
        ).select_related('customerlifecycletracking')


class Customer(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, db_index=True)
    riid = models.IntegerField(null=True, unique=True, db_index=True)

    created_dt = models.DateTimeField(auto_now_add=True)
    created_date = models.DateField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)
    modified_date = models.DateField(auto_now=True)

    objects = CustomerManager()

    class Meta:
        db_table = "customer"

    def __repr__(self):
        return '%s' % self.uuid


class CustomerSession(models.Model):
    session_id = models.CharField(max_length=100, primary_key=True)
    customer = models.ForeignKey(Customer)
    device_headers = models.CharField(max_length=200)
    num_page_views = models.IntegerField(default=0)

    created_dt = models.DateTimeField(auto_now_add=True)
    created_date = models.DateField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)
    modified_date = models.DateField(auto_now=True)

    def first_visit(self):
        try:
            return self.customerpageview_set.order_by('created_dt')[0]
        except IndexError, CustomerSession.DoesNotExist:
            return None

    class Meta:
        db_table = "customer_session"

    def __repr__(self):
        return '%s' % self.session_id


class CustomerCartManager(models.Manager):
    """ Manager for handling customer cart creations and edits """

    def process_cart(self, cart_id, *args, **kwargs):
        if cart_id != 0 and cart_id != '0':  # Avoid logging empty carts
            """ Creates cart for this sessionID if it doesn't exist already. """
            if 'customer' in kwargs:
                CustomerLifecycleTracking.objects.set_lifecycle_stage_to_cart(
                    cart_id=cart_id,
                    customer=kwargs['customer']
                )
            elif 'session' in kwargs:
                CustomerLifecycleTracking.objects.set_lifecycle_stage_to_cart(
                    cart_id=cart_id,
                    session=kwargs['session']
                )
            try:
                with transaction.atomic():
                    cart = self.create(cart_id=cart_id,
                                       session=kwargs['session'])
                    cart.save()
            except:
                pass


class CustomerCart(models.Model):
    cart_id = models.CharField(max_length=100, primary_key=True)
    session = models.ForeignKey(CustomerSession)

    created_dt = models.DateTimeField(auto_now_add=True)
    created_date = models.DateField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)
    modified_date = models.DateField(auto_now=True)

    objects = CustomerCartManager()

    class Meta:
        db_table = "customer_cart"

    def __unicode__(self):
        return self.cart_id


class CustomerOrderManager(models.Manager):
    """ Manager for handling customer orders """

    def process_order(self, order_id, session):
        CustomerLifecycleTracking.objects.set_lifecycle_stage_to_order(
            order_id=order_id, session=session)
        order_data = {'session': session}

        # Keep the first_visit fields denormalized here
        # for quick lookups on order queries
        copy_first_denormalized = ['url_path', 'product_fullid',
                                   'url_parameters', 'created_dt']
        first_visit = session.first_visit()

        for field in copy_first_denormalized:
            order_data['first_visit_%s' % field] = getattr(first_visit, field,
                                                           None)

        """ Creates order for this sessionID if it doesn't exist already """
        self.get_or_create(order_id=order_id, defaults=order_data)


class CustomerOrder(models.Model):
    order_id = models.CharField(max_length=100, primary_key=True)

    session = models.ForeignKey(CustomerSession)

    created_dt = models.DateTimeField(auto_now_add=True)
    created_date = models.DateField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)
    modified_date = models.DateField(auto_now=True)

    first_visit_url_path = models.CharField(max_length=255, null=True,
                                            blank=True)
    first_visit_product_fullid = models.CharField(max_length=100, blank=True,
                                                  null=True)
    first_visit_url_parameters = models.CharField(max_length=1000, blank=True,
                                                  null=True)
    first_visit_created_dt = models.DateTimeField(null=True, blank=True)

    objects = CustomerOrderManager()

    class Meta:
        db_table = "customer_order"

    def __unicode__(self):
        return self.order_id


class CustomerPageViewManager(models.Manager):
    """ Manager for handling secondary actions that must take place as a result
    of recording pageviews """

    def new(self, session, url_path, product_fullid='', url_parameters=''):
        """ Log new pageview, increase session pageview count by 1 """
        pageview = self.create(session=session, url_path=url_path,
                               product_fullid=product_fullid,
                               url_parameters=url_parameters)
        pageview.save()
        session.num_page_views += 1
        session.save()
        return pageview


class CustomerPageView(models.Model):
    session = models.ForeignKey(CustomerSession)
    url_path = models.CharField(max_length=255)
    product_fullid = models.CharField(max_length=100, blank=True, null=True)
    url_parameters = models.CharField(max_length=1000, blank=True, null=True)

    created_dt = models.DateTimeField(auto_now_add=True)
    created_date = models.DateField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)
    modified_date = models.DateField(auto_now=True)

    objects = CustomerPageViewManager()

    class Meta:
        db_table = "customer_pageview"

    def __unicode__(self):
        return self.url_path


class CustomerLifecycleTrackingManager(models.Manager):
    """ Adds/updates managed table """
    def set_lifecycle_stage_to_browse(self, pageview_id, *args, **kwargs):
        """
        Sets customers' lifecycle_messaging_stage to no product browse (700).
        :param args:
        :param kwargs:
        :return:
        """
        funnel_step = 500
        if 'customer' in kwargs:
            customer = kwargs['customer']
        elif 'session' in kwargs:
            customer = kwargs['session'].customer
        else:
            return 'Customer Not Found'
        record = self.get_or_create(customer=customer,
                                    defaults={'funnel_step': funnel_step,
                                              'lifecycle_messaging_data': json.dumps({'PAGES': [pageview_id]})})
        if not record[1]:
            # If customerlifecycletracking record already exists
            record = record[0]
            if record.funnel_step < funnel_step:
                record.funnel_step = funnel_step
                record.lifecycle_messaging_data = json.dumps({'PAGES': [pageview_id]})
                record.lifecycle_messaging_stage = 0
                record.save()
            elif record.funnel_step == funnel_step:
                messaging_data = record.messaging_data
                if not messaging_data.get('PAGES'):
                    messaging_data['PAGES'] = []
                if pageview_id not in messaging_data['PAGES']:
                    try:
                        messaging_data['PAGES'].append(pageview_id)
                    except KeyError:
                        messaging_data['PAGES'] = [pageview_id]
                    record.lifecycle_messaging_data = json.dumps(messaging_data)
                    record.lifecycle_messaging_stage = 0
                    record.save()
            elif record.funnel_step > funnel_step:
                record.lifecycle_messaging_stage = 0
                record.funnel_step = funnel_step
                messaging_data = record.messaging_data
                messaging_data['PAGES'] = [pageview_id]
                record.lifecycle_messaging_data = json.dumps(messaging_data)
                record.save()

    def set_lifecycle_stage_to_search(self, pageview, search_term, *args,
                                      **kwargs):
        """
        Sets customers' lifecycle_messaging_stage to search abandon(600)
        :param search_term:
        :param pageview:
        :param args:
        :param kwargs:
        :return:
        """
        funnel_step = 600
        if 'customer' in kwargs:
            customer = kwargs['customer']
        elif 'session' in kwargs:
            customer = kwargs['session'].customer
        else:
            return 'Customer Not Found'
        record = self.get_or_create(
            customer=customer,
            defaults={
                'funnel_step': funnel_step,
                'lifecycle_messaging_data': json.dumps({'SEARCH': [search_term]})})

        # Customer lifecycle data already exists
        if not record[1]:
            record = record[0]
            if record.funnel_step != funnel_step:
                record.funnel_step = funnel_step
                record.lifecycle_messaging_stage = 0
            record.lifecycle_messaging_data = json.dumps({'SEARCH': [search_term]})
            record.save()

    def set_lifecycle_stage_to_product(self, pageview_id, *args, **kwargs):
        """
        Sets customers' lifecycle_messaging_stage to Product (700), and adds the
         product pageview unique ID to a list of PDP unique ids associated with
         that customer.
        :type pageview_id: CustomerPageView record id
        :return: Nothing
        """
        funnel_step = 700
        if 'customer' in kwargs:
            customer = kwargs['customer']
        elif 'session' in kwargs:
            customer = kwargs['session'].customer
        else:
            return 'Customer Not Found'

        record = self.get_or_create(customer=customer,
                                    defaults={'funnel_step': funnel_step,
                                              'lifecycle_messaging_data': json.dumps({'PRODUCTS': [pageview_id]}), })
        if not record[1]:
            # If customerlifecycletracking record already exists
            record = record[0]
            if record.funnel_step < funnel_step:
                record.funnel_step = funnel_step
                record.lifecycle_messaging_data = json.dumps({'PRODUCTS': [pageview_id]})
                record.lifecycle_messaging_stage = 0
                record.save()
            elif record.funnel_step == funnel_step:
                messaging_data = record.messaging_data
                if not messaging_data.get('PRODUCTS'):
                    messaging_data['PRODUCTS'] = []
                if pageview_id not in messaging_data['PRODUCTS']:
                    try:
                        messaging_data['PRODUCTS'].append(pageview_id)
                    except KeyError:
                        messaging_data['PRODUCTS'] = [pageview_id]
                    record.lifecycle_messaging_data = json.dumps(messaging_data)
                    record.lifecycle_messaging_stage = 0
                    record.save()
            elif record.funnel_step > funnel_step:
                record.lifecycle_messaging_stage = 0
                record.funnel_step = funnel_step
                messaging_data = record.messaging_data
                messaging_data['PRODUCTS'] = [pageview_id]
                record.lifecycle_messaging_data = json.dumps(messaging_data)
                record.save()

    def set_lifecycle_stage_to_cart(self, cart_id, *args, **kwargs):
        """
        Sets customers' lifecycle_messaging_stage to Cart (1000), and adds the
        cart ID to the messaging_data value
        :rtype cart_id: int()
        :return: Nothing
        """
        funnel_step = 1000
        if 'customer' in kwargs:
            customer = kwargs['customer']
        elif 'session' in kwargs:
            customer = kwargs['session'].customer
        else:
            return 'Customer Not Found'
        msging_data = json.dumps({'QUOTE_ID': cart_id})
        self.update_or_create(
            customer=customer,
            defaults={'funnel_step': funnel_step,
                      'lifecycle_messaging_data': msging_data,
                      'lifecycle_messaging_stage': 0})

    def set_lifecycle_stage_to_order(self, order_id, *args, **kwargs):
        funnel_step = -1
        if 'customer' in kwargs:
            customer = kwargs['customer']
        elif 'session' in kwargs:
            customer = kwargs['session'].customer
        else:
            return 'Customer not found'
        msging_data = json.dumps({'ORDER_ID': order_id})
        self.update_or_create(
            customer=customer,
            defaults={'funnel_step': funnel_step,
                      'lifecycle_messaging_stage': 0,
                      'lifecycle_messaging_data': msging_data})


class CustomerLifecycleTracking(models.Model):
    """
    Used to track customer's progression through our funnel steps, from
    homepagevisit -> pdp visit -> cart -> order.

    Funnel step order is:
        0:  Inactive - either ran through all available lifecycle campaigns or
            was set to inactive for some one-off reason. To find out when a
            customer went Inactive, check the lifecycle_messaging_data to see
            if it includes cart data, browse data, etc.
        -1: Completed order.
        500: Browse abandon (no pdp)
        700: Browse abandon (with PDP)
        1000: Cart

        Other steps to be defined in the future.
    """
    # A one-to-one field is a design smell (can't be implemented in a relational
    # db!). This probably belongs to the Customer. Could add
    # related_name=lifecycle_tracking (or just lifecycle) to make life easier.
    customer = models.OneToOneField(Customer)
    funnel_step = models.IntegerField(default=0)
    lifecycle_messaging_stage = models.IntegerField(default=0)
    lifecycle_messaging_data = models.TextField(null=True, blank=True)
    created_dt = models.DateTimeField(auto_now_add=True)
    created_date = models.DateField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)
    modified_date = models.DateField(auto_now=True)

    objects = CustomerLifecycleTrackingManager()

    # TODO: Update @property to Django cached property
    @property
    def messaging_data(self):
        if not hasattr(self, '__messaging_data'):
            self.__messaging_data = self.lifecycle_messaging_data
        if not self.__messaging_data:
            self.__messaging_data = {}
        else:
            self.__messaging_data = json.loads(self.__messaging_data)
        return self.__messaging_data

    @property
    def cart_id(self):
        if 'QUOTE_ID' not in self.messaging_data:
            return None
        return int(self.messaging_data['QUOTE_ID'])

    @property
    def noproduct_pageviews(self):
        if 'PAGES' not in self.messaging_data:
            return None
        return self.messaging_data['PAGES']

    @property
    def product_pageviews(self):
        if 'PRODUCTS' not in self.messaging_data:
            return None
        return self.messaging_data['PRODUCTS']

    def get_packaged_row(self):
        """
        :return: A python dict representing record rows
        :rtype: dict
        """
        return {'customer': self.customer,
                'funnel_step': self.funnel_step,
                'lifecycle_messaging_stage': self.lifecycle_messaging_stage,
                'lifecycle_messaging_data': json.loads(self.lifecycle_messaging_data),
                'created_dt': self.created_dt,
                'created_date': self.created_date,
                'modified_dt': self.modified_dt,
                'modified_date': self.modified_date, }

    class Meta:
        db_table = "customer_lifecycle_tracking"

    def __repr__(self):
        return self.lifecycle_messaging_data


class GmailAdEmails(models.Model):
    """
    Records email address and RIID received from Gmail Ads
    """
    # A one-to-one field is a design smell (can't be implemented in a relational
    # db!). This probably belongs to the Customer.
    email = models.CharField(max_length=100)
    riid = models.IntegerField()
    created_dt = models.DateTimeField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)


class CustomerStrandsIdManager(models.Manager):

    def append_strands_products(self, rg_orders):
        # Run through rg_orders and check for strands_id in
        # map_order_id_strands_id
        map_order_id_strands_id = self.map_order_ids_strands_ids(rg_orders)
        for r in rg_orders:
            if map_order_id_strands_id.get(r['order_id'], False):
                strands_products = self.get_strands_products(map_order_id_strands_id[r['order_id']])
                if len(strands_products) > 0:
                    r['includes_strands'] = 'yes'
                    r['strands_products'] = strands_products
        return rg_orders

    def map_order_ids_strands_ids(self, rg_orders):
        customer_orders = CustomerOrder.objects.filter(order_id__in=[r['order_id'] for r in rg_orders])
        map_order_id_strands_id = {}
        if customer_orders.exists():
            for o in customer_orders:
                session = o.session
                customer = session.customer
                if not hasattr(customer, 'customerstrandsid'):
                    continue
                map_order_id_strands_id[o.order_id] = customer.customerstrandsid.strands_id
        return map_order_id_strands_id

    def get_strands_products(self, strands_id):
        params = {
            'apid': settings.STRANDS_APID,
            'tpl': 'conf_3',
            'format': 'json',
            'user': strands_id,
            'amount': 6,
        }
        response = requests.get(settings.STRANDS_ENDPOINT, params=params)
        strands_products = []
        if response.status_code == 200:
            results = json.loads(response.content)
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
        return strands_products


class CustomerStrandsId(models.Model):
    """
    Maps strands ID to customer IDs
    """
    customer = models.OneToOneField(Customer)
    strands_id = models.CharField(max_length=50)

    created_dt = models.DateTimeField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)

    objects = CustomerStrandsIdManager()

    class Meta:
        db_table = "customer_strands_id"


class FacebookAdEmails(models.Model):
    """
    Store the customer email addresss and  from Facebook Leadgen
    """
    email = models.CharField(max_length=100)
    riid = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class MobovidaCustomerEmails(models.Model):
    """
    Store email addresses and md5s associated w/ customer email addresses
    """
    email = models.EmailField()
    email_md5 = models.CharField(max_length=128)
    created_dt = models.DateTimeField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "mobovida_customer_email"


class EmailSignUpTrack(models.Model):
    """
    Track the following metrics on a daily basis
    1.New email sign ups
    2.Email unsubscribes
    3.Calculated metric: new email sign ups - email unsubs = Total net change
    """
    day = models.CharField(blank=True, primary_key=True, max_length=100,
                           help_text='date for email sign up and unsubscribe')
    new_email = models.IntegerField(help_text='The count of new email sign ups')
    unsubscribe_email = models.IntegerField(help_text='The count of email unsubscribes')
    analysis_date = models.DateTimeField(blank=True, null=True,
                                         help_text='analysis date')

    class Meta:
        db_table = "track_email_signup"


class CustomerDevice(models.Model):
    """
    Collection of customer devices mapped to Responsys unique identifier (RIID)
    """
    riid = models.CharField(primary_key=True, max_length=15)
    device = models.CharField(max_length=128)
    uploaded = models.BooleanField(default=False)
    created_dt = models.DateTimeField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customer_device'
