from __future__ import unicode_literals

import json

from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
from logging import getLogger

log = getLogger(__name__)


class FacebookAd(models.Model):
    account_id = models.CharField(max_length=100, null=True)
    campaign_id = models.CharField(max_length=100, null=True)
    ad_set_id = models.CharField(max_length=100, null=True)
    ad_id = models.CharField(max_length=128, null=True, unique=True)
    campaign_name = models.CharField(max_length=200, null=True)
    ad_set_name = models.CharField(max_length=200, null=True)
    ad_name = models.CharField(max_length=200, null=True)
    message = models.CharField(max_length=200, null=True)
    products = models.TextField(null=True)
    bmc_url = models.CharField(max_length=400, null=True)
    handle_url = models.CharField(max_length=400, null=True)
    created_dt = models.DateTimeField(auto_now_add=True)
    created_date = models.DateField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)
    modified_date = models.DateField(auto_now=True)

    def parse_products(self):
        try:
            return json.loads(self.products) or []
        except:
            return []

    def save(self, *args, **kwargs):
        super(FacebookAd, self).save(*args, **kwargs)
        self.associate_products()

    def associate_products(self):
        for entity in self.parse_products():
            product_id = entity.get('entity_id')
            product_json = json.dumps(entity)
            product, _new = AdvertisedProduct.objects.get_or_create(
                product_id=product_id,
                defaults={'product_json': product_json}
            )
            product.ad_objs.add(self)
        return self.product_objs.all()


class AdvertisedProduct(models.Model):
    ad_objs = models.ManyToManyField('FacebookAd', related_name='product_objs')
    product_id = models.CharField(max_length=128)
    product_json = models.TextField()

    def get_stat_windows(self):
        return AdStatWindow.objects.filter(ad_obj__product_objs=self)


class ProductReport(models.Model):
    ad_obj = models.ForeignKey('FacebookAd', null=True)
    ad_id = models.CharField(max_length=128)
    ad_name = models.CharField(max_length=256)
    ad_set_name = models.CharField(max_length=256)
    category_id = models.IntegerField(null=True, blank=True)
    handle = models.CharField(max_length=200, null=True, blank=True)
    product_ids = models.TextField()
    campaign_name = models.CharField(max_length=256)
    status = models.CharField(max_length=128)
    status_updated_at = models.DateTimeField()


class AdStatWindowQueryset(models.QuerySet):
    def for_date(self, date):
        return self.filter(date_start=date, date_stop=date)

    def days_ago(self, n):
        date = (timezone.now() - timedelta(days=n)).date()
        return self.for_date(date)

    def today(self):
        return self.days_ago(0)

    def yesterday(self):
        return self.days_ago(1)


class AdStatWindow(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    ad_obj = models.ForeignKey('FacebookAd', null=True)

    ad_id = models.CharField(max_length=128)

    date_start = models.DateField()
    date_stop = models.DateField()

    add_payment_info = models.PositiveIntegerField(default=0)
    add_to_cart = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    impressions = models.PositiveIntegerField(default=0)
    reach = models.PositiveIntegerField(default=0)
    sales = models.PositiveIntegerField(default=0)

    spend = models.FloatField(default=0)
    sales_revenue = models.FloatField(default=0)
    total_revenue = models.FloatField(default=0)
    profit = models.FloatField(default=0)

    ctr = models.FloatField(default=0)

    cost_per_like = models.FloatField(default=0)
    cost_per_click = models.FloatField(default=0)
    cost_per_sale = models.FloatField(default=0)

    unique_together = ("ad_id", "date_start")

    objects = AdStatWindowQueryset.as_manager()

    def __str__(self):
        return '%s (%s)' % (self.ad_id, self.date_string)

    @property
    def date_string(self):
        if self.date_start == self.date_stop:
            return self.date_start
        return '%s - %s' % (self.date_start, self.date_stop)

    @classmethod
    def from_data(cls, data):
        lookup_info = {'ad_id': data['ad_id'],
                       'date_start': data['date_start'],
                       'date_stop': data['date_stop']}

        lookup = cls.objects.filter(**lookup_info)

        meta = {'campaign_name': data['campaign_name']}
        if 'adset_name' in data:
            meta['ad_set_name'] = data['adset_name']
        if 'ad_name' in data:
            meta['ad_name'] = data['ad_name']

        data['ad_obj'], _new = FacebookAd.objects.update_or_create(ad_id=data['ad_id'],
                                                                   ad_set_id=data['adset_id'],
                                                                   campaign_id=data['campaign_id'],
                                                                   defaults=meta)

        build_info = {field.name: data[field.name]
                      for field in cls._meta.get_fields()
                      if field.name in data}

        if lookup.count():
            lookup.update(**build_info)
            return lookup.first()

        return cls.objects.create(**build_info)

    @classmethod
    def build_stats(cls, date=None):
        from .connect import FacebookConnect
        if not date:
            date = str(timezone.now().date())
        cnx = FacebookConnect()
        returned_info = {}
        for adid, d in cnx.get_ad_insights(start=date, end=date).items():
            returned_info[adid] = cls.from_data(d)
        return returned_info


ACTION_CHOICES = [
      ('activate', 'Activate'),
      ('pause', 'Pause')]


class AdAction(models.Model):
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    ad = models.ForeignKey(FacebookAd)
    performing_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                        blank=True)  # null means an Optimizer did it
    reason = models.TextField(null=True, blank=True)
    # Let a user type in a reason, or populate it with the name of the OptimizeRule that caused this action


OPTIMIZER_STATUS = [
  ('disabled', 'Disabled'),
  ('manual', 'Manual - Notify, but dont make changes'),
  ('automatic', 'Automatic'),
]


class AdOptimizer(models.Model):
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=16, choices=OPTIMIZER_STATUS,
                              default='manual')
    rules = models.ManyToManyField('OptimizeRule')

    def __str__(self):
        return '[%s] %s - %s rules' % (self.status, self.title,
                                       self.rules.count())

    def describe(self):
        build = str(self)
        for rule in self.rules.all():
            build += "\n\t%s" % rule
        return build

    def get_windows(self):
        # For now, look at all ads. Soon, this will be scoped to
        # only include ads in the current Queue
        valid_adsets = [ad.ad_set_id for ad in FacebookAd.objects.all()]
        return AdStatWindow.today().filter(adset_id__in=valid_adsets)

    def apply(self, windows=None, dry_run=False, manual=False):
        return {
            window.ad_id: self.apply(window, self, dry_run=False, manual=False)
            for window in (windows or self.get_windows())
        }

    def apply_to_window(self, window, dry_run=False, manual=False):
        log.info('EVALUATE: %s -> %s' % (self, window))
        for rule in self.rules.all():
            if rule.apply(window, self, dry_run=dry_run, manual=manual):
                return rule
        return None


CHECK_FIELDS = [
                ('clicks', 'Clicks'),
                ('add_to_cart', 'Add To Cart'),
                ('add_payment_info', 'Add Payment Info'),
                ('spend', 'Spend'),
                ('sales', 'Conversions'),
                ('cost_per_sale', 'Cost Per Sale')]
CHECK_TYPES = [('eq', '='), ('gt', '>'), ('gte', '>='), ('lt', '<'), ('lte', '<=')]
MATCH_CHOICES = [('all', 'Match all rules'), ('any', 'Match any rules')]


class OptimizeRule(models.Model):
    title = models.CharField(max_length=255)

    status = models.CharField(max_length=16, choices=OPTIMIZER_STATUS,
                              default='manual')
    # Status appears at both Optimizer level, and for each rule

    APPLIES_TO_CHOICES = [('all', 'All ads'), ('today', 'Ads started today'),
                          ('not_today', 'Ads not started today')]
    applies_to = models.CharField(max_length=16, choices=APPLIES_TO_CHOICES)

    action = models.CharField(max_length=16, choices=ACTION_CHOICES)

    match_rules = models.CharField(max_length=16, choices=MATCH_CHOICES,
                                   default='all')
    checks = models.ManyToManyField('OptimizeCheck')  # AND checks

    def __str__(self):
        return '[%s] %s: %s' % (self.status, self.title, self.action)

    def evaluate_stats(self, window):
        log.debug('  Checking rule %s against %s'%(self, window))
        if self.applies_to != 'all':
            if not window.ad_obj:
                log.debug('  Skipping ad not managed by MVD')
                return False

            created_today = window.ad_obj.created_dt.date() == timezone.now().date()

            if self.applies_to == 'today' and not created_today:
                log.debug('  Skipping ad not created today, rule applies to "today"')
                return False

            if self.applies_to == 'not_today' and created_today:
                log.debug('  Skipping ad created today, rule applies to "not_today"')
                return False

        if not self.checks.count():
            log.warning('No checks for rule %s' % self)
            return False
        for rule in self.checks.all():
            result = rule.evaluate(window)
            log.debug('     Check: %s ? %s' % (rule, result))
            if self.match_rules == 'any' and result:
                log.debug('     ANY rule passed')
                return True
            if self.match_rules == 'all' and not result:
                log.debug('     ALL rules not passed')
                return False
        if self.match_rules == 'all':
            log.debug('     ALL rules passed')
            return True
        else:
            log.debug('     ANY rule not passed')
            return False

    def apply(self, window, optimizer, dry_run=None, manual=None):
        # You can pass dry_run=True to suppress notifications
        # or manual=True to avoid automatic behavior
        if self.status == 'disabled':
            return
        if self.status == 'manual':
            manual = True
        if optimizer.status == 'manual':
            manual = True

        automatic = not manual and not dry_run

        result = self.evaluate_stats(window)

        if result and not dry_run:
            OptimizeNotification.notify(window, optimizer, self, self.action)
        if result and automatic:
            self.perform(window, optimizer)

        return result

    def perform(self, window, optimizer):
        # Perform the actual pausing here
        raise NotImplementedError('Perform not implemented yet')


def get_check(operand):
    if operand in 'eq':
        def equality_check(a, b): return a == b
        return equality_check
    if operand == 'gt':
        def equality_check(a, b): return a > b
        return equality_check
    if operand == 'gte':
        def equality_check(a, b): return a >= b
        return equality_check
    if operand == 'lt':
        def equality_check(a, b): return a < b
        return equality_check
    if operand == 'lte':
        def equality_check(a, b): return a <= b
        return equality_check


class OptimizeCheck(models.Model):
    if_the = models.CharField(max_length=16, choices=CHECK_FIELDS)
    check_type = models.CharField(max_length=16, choices=CHECK_TYPES)
    value = models.PositiveIntegerField()

    @classmethod
    def do_check(cls, operand, a, b):
        return get_check(operand)(a, b)

    def evaluate(self, window):
        stat_value = float(getattr(window, self.if_the, 0))
        return self.do_check(self.check_type, stat_value, self.value)

    def __str__(self):
        return '%s %s %s' % (self.if_the, self.check_type, self.value)


class OptimizeNotification(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    ad = models.ForeignKey(FacebookAd, on_delete=models.DO_NOTHING)
    window = models.ForeignKey(AdStatWindow, on_delete=models.DO_NOTHING)
    optimizer = models.ForeignKey(AdOptimizer, on_delete=models.DO_NOTHING)
    rule = models.ForeignKey(OptimizeRule, on_delete=models.DO_NOTHING)
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)

    automatic = models.BooleanField(default=False)
    performed = models.BooleanField(default=False)

    @classmethod
    def notify(cls, window, optimizer, rule, action):
        # Perform mail users here -- what users are we mailing?
        return cls.objects.create(
            ad=window.ad_obj,
            window=window,
            optimizer=optimizer,
            rule=rule,
            action=action)

    @property
    def action_taken(self):
        if not self.automatic:
            return 'MANUAL'
        if not self.performed:
            return 'ERROR'
        return 'OK'

    def __str__(self):
        # "[pause] High CPA on a new ad - MyAd1 passed rule CPA>20 AND CONVERSIONS>0"
        return '[%s - %s] %s - ad %s passed rule %s' % (
            self.rule.action,
            self.action_taken,
            self.optimizer.title,
            self.ad,
            self.rule,
        )


class FacebookAPISettings(models.Model):
    name = models.CharField(max_length=100)
    app_id = models.CharField(max_length=50, db_index=True)
    account_id = models.CharField(max_length=50, unique=True, db_index=True)
    app_secret = models.CharField(max_length=50)
    user_token = models.CharField(max_length=300)
    page_id = models.CharField(max_length=50)
    instagram_actor_id = models.CharField(max_length=50)
    version = models.CharField(max_length=50)
    comments = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    def get_model_dict(self):
        return self.__dict__
