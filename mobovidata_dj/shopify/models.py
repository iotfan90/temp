# encoding: utf-8
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from jsonfield import JSONField

from mobovidata_dj.core.storages import (MultipleLevelFileSystemStorage,
                                         OverwriteFileSystemStorage)


# ################### STORE ###################

class Store(models.Model):
    api_key = models.CharField(max_length=50)
    api_url = models.CharField(max_length=400)
    description = models.TextField(null=True, blank=True)
    identifier = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    password = models.CharField(max_length=50)
    shop_url = models.CharField(max_length=400)

    collection_task_run_at = models.DateTimeField(null=True, blank=True)
    metafield_task_run_at = models.DateTimeField(null=True, blank=True)
    order_task_run_at = models.DateTimeField(null=True, blank=True)
    pages_task_run_at = models.DateTimeField(null=True, blank=True)
    product_task_run_at = models.DateTimeField(null=True, blank=True)
    update_shopify_collection_task_run_at = models.DateTimeField(null=True,
                                                                 blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'shopify_store'


# ################### PRODUCT ###################

class Product(models.Model):
    GLOBAL = 'global'
    WEB = 'web'
    PUBLISHED_SCOPE_CHOICES = (
        (GLOBAL, 'global'),
        (WEB, 'web')
    )
    store = models.ForeignKey(Store)
    product_id = models.CharField(max_length=32, db_index=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    body_html = models.TextField(null=True, blank=True)
    vendor = models.CharField(max_length=100, null=True, blank=True)
    product_type = models.CharField(max_length=200, null=True, blank=True)
    handle = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    template_suffix = models.CharField(max_length=100, null=True, blank=True)
    published_scope = models.CharField(max_length=10, null=True, blank=True,
                                       choices=PUBLISHED_SCOPE_CHOICES)

    def __unicode__(self):
        return self.product_id

    class Meta:
        db_table = 'shopify_product'


class ProductImage(models.Model):
    image_id = models.CharField(max_length=32, db_index=True, null=True,
                                blank=True)
    product = models.ForeignKey(Product)
    position = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    src = models.URLField(max_length=400, null=True, blank=True)
    variants = models.ManyToManyField('ProductVariant', blank=True)

    def __unicode__(self):
        return self.image_id

    class Meta:
        db_table = 'shopify_product_image'


class ProductOption(models.Model):
    option_id = models.CharField(max_length=32, db_index=True, null=True,
                                 blank=True)
    product = models.ForeignKey(Product)
    name = models.CharField(max_length=200, null=True, blank=True)
    position = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.option_id

    class Meta:
        db_table = 'shopify_product_option'


class ProductOptionValue(models.Model):
    options = models.ManyToManyField(ProductOption)
    name = models.CharField(max_length=200, unique=True, db_index=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'shopify_product_option_value'


class ProductVariant(models.Model):
    GRAM = 'g'
    KILOGRAM = 'kg'
    OUNCE = 'oz'
    POUND = 'lb'
    WEIGHT_UNIT_CHOICES = (
        (GRAM, 'g'),
        (KILOGRAM, 'kg'),
        (OUNCE, 'oz'),
        (POUND, 'lb')
    )
    variant_id = models.CharField(max_length=32, db_index=True, null=True, blank=True)
    product = models.ForeignKey(Product)
    title = models.CharField(max_length=200, null=True, blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, null=True,
                                blank=True)
    sku = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    position = models.IntegerField(null=True, blank=True)
    grams = models.IntegerField(null=True, blank=True)
    inventory_policy = models.CharField(max_length=50, null=True, blank=True)
    compare_at_price = models.DecimalField(max_digits=9, decimal_places=2,
                                           null=True, blank=True)
    fulfillment_service = models.CharField(max_length=50, null=True, blank=True)
    inventory_management = models.CharField(max_length=50, null=True,
                                            blank=True)
    option1 = models.CharField(max_length=100, null=True, blank=True)
    option2 = models.CharField(max_length=100, null=True, blank=True)
    option3 = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    taxable = models.BooleanField(default=False)
    barcode = models.CharField(max_length=100, null=True, blank=True)
    image = models.ForeignKey(ProductImage, null=True, blank=True)
    inventory_quantity = models.IntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=9, decimal_places=4, null=True,
                                 blank=True)
    weight_unit = models.CharField(max_length=2, null=True, blank=True,
                                   choices=WEIGHT_UNIT_CHOICES)
    old_inventory_quantity = models.IntegerField(null=True, blank=True)
    requires_shipping = models.BooleanField(default=False)
    available = models.BooleanField(default=True)
    feed_excluded = models.BooleanField(default=False)

    def __unicode__(self):
        return self.variant_id

    class Meta:
        db_table = 'shopify_product_variant'


class ProductTag(models.Model):
    products = models.ManyToManyField(Product)
    name = models.CharField(max_length=200, unique=True, db_index=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'shopify_product_tag'


class ProductExtraInfo(models.Model):
    product = models.OneToOneField(Product)
    color = models.CharField(max_length=50, blank=True, null=True)
    associated_products = models.ManyToManyField(Product,
                                                 related_name='association')

    def __unicode__(self):
        return self.product.product_id

    class Meta:
        db_table = 'shopify_product_extra_info'


# ################### SMART COLLECTION ###################

class SmartCollection(models.Model):
    APLHA_ASC = 'alpha-asc'
    APLHA_DESC = 'alpha-desc'
    BEST_SELLING = 'best-selling'
    CREATED = 'created'
    CREATED_DESC = 'created-desc'
    MANUAL = 'manual'
    PRICE = 'price-asc'
    PRICE_DESC = 'price-desc'
    SORT_ORDER_CHOICES = (
        (APLHA_ASC, 'alpha-asc'),
        (APLHA_DESC, 'alpha-desc'),
        (BEST_SELLING, 'best-selling'),
        (CREATED, 'created'),
        (CREATED_DESC, 'created-desc'),
        (MANUAL, 'manual'),
        (PRICE, 'price-asc'),
        (PRICE_DESC, 'price-desc'),
    )
    GLOBAL = 'global'
    WEB = 'web'
    PUBLISHED_SCOPE_CHOICES = (
        (GLOBAL, 'global'),
        (WEB, 'web')
    )
    store = models.ForeignKey(Store)
    collection_id = models.CharField(max_length=32, db_index=True)
    handle = models.CharField(max_length=200, null=True, blank=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    body_html = models.TextField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    sort_order = models.CharField(max_length=50, null=True, blank=True,
                                  choices=SORT_ORDER_CHOICES)
    template_suffix = models.CharField(max_length=100, null=True, blank=True)
    published_scope = models.CharField(max_length=10, null=True, blank=True,
                                       choices=PUBLISHED_SCOPE_CHOICES)
    disjunctive = models.BooleanField(default=False)

    def get_rules_dict_format(self):
        rules = [x.get_rule_dict_format() for x
                 in self.smartcollectionrule_set.all()]
        return rules

    def __unicode__(self):
        return self.collection_id

    class Meta:
        db_table = 'shopify_smart_collection'


class SmartCollectionRule(models.Model):
    GREATER_THAN = 'greater_than'
    LESS_THAN = 'less_than'
    EQUALS = 'equals'
    NOT_EQUALS = 'not_equals'
    STARTS_WITH = 'starts_with'
    ENDS_WITH = 'ends_with'
    CONTAINS = 'contains'
    NOT_CONTAINS = 'not_contains'
    RELATION_CHOICES = (
        (GREATER_THAN, 'greater_than'),
        (LESS_THAN, 'less_than'),
        (EQUALS, 'equals'),
        (NOT_EQUALS, 'not_equals'),
        (STARTS_WITH, 'starts_with'),
        (ENDS_WITH, 'ends_with'),
        (CONTAINS, 'contains'),
        (NOT_CONTAINS, 'not_contains'),
    )
    TITLE = 'title'
    TYPE = 'type'
    VENDOR = 'vendor'
    VARIANT_TITLE = 'variant_title'
    VARIANT_COMPARE_AT_PRICE = 'variant_compare_at_price'
    VARIANT_WEIGHT = 'variant_weight'
    VARIANT_INVENTORY = 'variant_inventory'
    VARIANT_PRICE = 'variant_price'
    TAG = 'tag'
    COLUMN_CHOICES = (
        (TITLE, 'title'),
        (TYPE, 'type'),
        (VENDOR, 'vendor'),
        (VARIANT_TITLE, 'variant_title'),
        (VARIANT_COMPARE_AT_PRICE, 'variant_compare_at_price'),
        (VARIANT_WEIGHT, 'variant_weight'),
        (VARIANT_INVENTORY, 'variant_inventory'),
        (VARIANT_PRICE, 'variant_price'),
        (TAG, 'tag'),

    )
    smart_collection = models.ForeignKey(SmartCollection)
    relation = models.CharField(max_length=20, null=True, blank=True,
                                choices=RELATION_CHOICES)
    condition = models.CharField(max_length=100, null=True, blank=True)
    column = models.CharField(max_length=20, null=True, blank=True,
                              choices=COLUMN_CHOICES)

    def get_rule_dict_format(self):
        rule = {
            'column': self.column,
            'relation': self.relation,
            'condition': self.condition
        }
        return rule

    def __unicode__(self):
        return self.smart_collection.handle

    class Meta:
        db_table = 'shopify_smart_collection_rule'


class SmartCollectionImage(models.Model):
    smart_collection = models.OneToOneField(SmartCollection)
    created_at = models.DateTimeField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    src = models.URLField(max_length=400, null=True, blank=True)

    def __unicode__(self):
        return self.src

    class Meta:
        db_table = 'shopify_smart_collection_image'


# ################### METAFIELD ###################

class Metafield(models.Model):
    created_at = models.DateTimeField()
    description = models.TextField(null=True, blank=True)
    key = models.CharField(max_length=30, db_index=True)
    namespace = models.CharField(max_length=20, db_index=True)
    owner_id = models.CharField(max_length=32, db_index=True)
    owner_resource = models.CharField(max_length=255, db_index=True)
    shopify_id = models.CharField(max_length=32, db_index=True)
    store = models.ForeignKey(Store)
    value = models.TextField()
    value_type = models.CharField(max_length=10)
    updated_at = models.DateTimeField()

    def __unicode__(self):
        return self.shopify_id

    class Meta:
        db_table = 'shopify_metafield'
        unique_together = ('owner_id', 'owner_resource', 'store', 'shopify_id')


# ################### BRAND / MODEL ###################

class Brand(models.Model):
    name = models.CharField(max_length=200, unique=True, db_index=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'shopify_brand'


class Model(models.Model):
    APPLE_30_PIN = 'apple-30-pin'
    APPLE_8_PIN = 'apple-8-pin'
    LG_CHOCOLATE = 'lg-chocolate'
    MICRO_USB = 'micro-usb'
    MINI_USB = 'mini-usb'
    USB_TYPE_C = 'usb-type-c'
    ADAPTOR_TYPE_CHOICES = (
        (APPLE_30_PIN, 'apple-30-pin'),
        (APPLE_8_PIN, 'apple-8-pin'),
        (LG_CHOCOLATE, 'lg-chocolate'),
        (MICRO_USB, 'micro-usb'),
        (MINI_USB, 'mini-usb'),
        (USB_TYPE_C, 'usb-type-c'),
    )
    D_T_CAMERA = 'camera'
    D_T_CELL_PHONE = 'cell-phone'
    D_T_LAPTOP = 'laptop'
    D_T_MP3_MP4_PLAYER = 'mp3-mp4-player'
    D_T_SMART_WATCH = 'smart-watch'
    D_T_TABLET = 'tablet'
    DEVICE_TYPE_CHOICES = (
        (D_T_CAMERA, 'camera'),
        (D_T_CELL_PHONE, 'cell-phone'),
        (D_T_LAPTOP, 'laptop'),
        (D_T_MP3_MP4_PLAYER, 'mp3-mp4-player'),
        (D_T_SMART_WATCH, 'smart-watch'),
        (D_T_TABLET, 'tablet'),
    )
    H_T_2_5_MM = '2.5mm'
    H_T_3_5_mm = '3.5mm'
    H_T_HTC_8525 = 'htc-8525'
    H_T_LG_CHOCOLATE = 'lg-chocolate'
    H_T_MICRO_USB = 'micro-usb'
    H_T_MINI_USB = 'mini-usb'
    H_T_NOKIA_7210 = 'nokia-7210'
    H_T_SAMSUNG_E315 = 'samsung-e315'
    H_T_SAMSUNG_M300 = 'samsung-m300'
    H_T_SAMSUNG_T809 = 'samsung-t809'
    H_T_SONY_K750 = 'sony-k750'
    HEADSET_TYPE_CHOICES = (
        (H_T_2_5_MM, '2.5mm'),
        (H_T_3_5_mm, '3.5mm'),
        (H_T_HTC_8525, 'htc-8525'),
        (H_T_LG_CHOCOLATE, 'lg-chocolate'),
        (H_T_MICRO_USB, 'micro-usb'),
        (H_T_MINI_USB, 'mini-usb'),
        (H_T_NOKIA_7210, 'nokia-7210'),
        (H_T_SAMSUNG_E315, 'samsung-e315'),
        (H_T_SAMSUNG_M300, 'samsung-m300'),
        (H_T_SAMSUNG_T809, 'samsung-t809'),
        (H_T_SONY_K750, 'sony-k750'),
    )
    P_S_SMALL = 'small'
    P_S_MEDIUM = 'medium'
    P_S_LARGE = 'large'
    P_S_XL = 'xl'
    POUCH_SIZE_CHOICES = (
        (P_S_SMALL, 'small'),
        (P_S_MEDIUM, 'medium'),
        (P_S_LARGE, 'large'),
        (P_S_XL, 'xl'),
    )

    adaptor_type = models.CharField(max_length=30, null=True, blank=True,
                                    choices=ADAPTOR_TYPE_CHOICES)
    bluetooth = models.NullBooleanField(null=True, blank=True)
    bluetooth_version = models.CharField(max_length=100, null=True, blank=True)
    brand = models.ForeignKey(Brand)
    categories = models.ManyToManyField('MasterAttributeSet', blank=True)
    depth = models.FloatField(null=True, blank=True)
    device_type = models.CharField(max_length=30, null=True, blank=True,
                                   choices=DEVICE_TYPE_CHOICES)
    collection_description = models.TextField(null=True, blank=True)
    collection_handle = models.CharField(max_length=255, unique=True,
                                         db_index=True)
    headset_type = models.CharField(max_length=30, null=True, blank=True,
                                    choices=HEADSET_TYPE_CHOICES)
    height = models.FloatField(null=True, blank=True)
    image = models.ImageField(upload_to='img_models',
                              storage=MultipleLevelFileSystemStorage(),
                              blank=True, null=True)
    model = models.CharField(max_length=255)
    pouch_size = models.CharField(max_length=30, null=True, blank=True,
                                  choices=POUCH_SIZE_CHOICES)
    removable_battery = models.NullBooleanField(null=True, blank=True)
    shopify_image = models.URLField(null=True, blank=True)
    sku_add_on = models.CharField(max_length=255, blank=True, null=True)
    top_model = models.BooleanField(default=False)
    width = models.FloatField(null=True, blank=True)
    wireless_charger = models.NullBooleanField(null=True, blank=True)

    synced_we = models.BooleanField(default=False)
    synced_co = models.BooleanField(default=False)
    error_we = models.TextField(blank=True, null=True)
    error_co = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            orig = Model.objects.get(pk=self.pk)
            obj_modified = ((orig.image != self.image) or
                            (orig.adaptor_type != self.adaptor_type) or
                            orig.collection_description != self.collection_description)
            if obj_modified:
                self.synced_we = False
                self.synced_co = False
                self.error_we = None
                self.error_co = None
            if self.synced_we:
                self.error_we = None
            if self.synced_co:
                self.error_co = None
        super(Model, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.model

    class Meta:
        db_table = 'shopify_model'


# ################### METADATA/ATTRIBUTES ###################

class MetadataCollection(models.Model):
    store = models.ForeignKey(Store)
    name = models.CharField(max_length=255, db_index=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'shopify_metadata_collection'


class MetadataCollectionAttribute(models.Model):
    MASTER_CATEGORIES = 'master_categories'
    N_BRAND_MODEL = 'brandModel'
    N_DEFAULT_ADD_ON = 'defaultAddOnProduct'
    NAMESPACE_CHOICES = (
        (MASTER_CATEGORIES, 'Master Categories'),
        (N_BRAND_MODEL, 'Brand Model'),
        (N_DEFAULT_ADD_ON, 'Default Add On Product'),
    )
    BRAND_MODEL = 'brand_model'
    DEFAULT_ADD_ON = 'defaultAddOnProduct'
    METADATA_TYPE_CHOICES = (
        (MASTER_CATEGORIES, 'Master Categories'),
        (BRAND_MODEL, 'Brand Model'),
        (DEFAULT_ADD_ON, 'Default Add On Product'),
    )
    ERROR = 'error'
    SYNCED = 'synced'
    UNSYNCED = 'unsynced'
    STATUS_CHOICES = (
        (ERROR, 'Error'),
        (SYNCED, 'Synced'),
        (UNSYNCED, 'Unsynced'),
    )

    description = models.CharField(max_length=255, null=True, blank=True)
    error_msg = models.TextField(blank=True, null=True)
    key = models.CharField(max_length=255, db_index=True)
    m_type = models.CharField(max_length=30, choices=METADATA_TYPE_CHOICES)
    namespace = models.CharField(max_length=50, choices=NAMESPACE_CHOICES)
    collection_metadata = models.ForeignKey(MetadataCollection)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES,
                              default=UNSYNCED)
    value = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            orig = MetadataCollectionAttribute.objects.get(pk=self.pk)
            obj_modified = ((orig.key != self.key) or
                            (orig.description != self.description) or
                            (orig.value != self.value))
            if obj_modified:
                self.status = MetadataCollectionAttribute.UNSYNCED
                self.error_msg = None
            if self.status == MetadataCollectionAttribute.SYNCED:
                self.error_msg = None
        super(MetadataCollectionAttribute, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.key

    class Meta:
        db_table = 'shopify_metadata_collection_attribute'
        unique_together = ('collection_metadata', 'key', 'm_type')


class MetadataProduct(models.Model):
    store = models.ForeignKey(Store)
    sku = models.CharField(max_length=255, db_index=True)

    def __unicode__(self):
        return self.sku

    class Meta:
        db_table = 'shopify_metadata_product'


class MetadataProductAttribute(models.Model):
    PRODUCT_ATTR = 'product_attributes'
    VARIANTS = 'variants'
    MASTER_PRODUCT = 'master_product'
    NAMESPACE_CHOICES = (
        (PRODUCT_ATTR, 'Product Attributes'),
        (VARIANTS, 'Variants'),
        (MASTER_PRODUCT, 'Master Product'),
    )
    DESCRIPTION = 'description'
    ASSOCIATED_PRODUCTS = 'associated_products'
    METADATA_TYPE_CHOICES = (
        (DESCRIPTION, 'Description'),
        (ASSOCIATED_PRODUCTS, 'Associated products'),
        (MASTER_PRODUCT, 'Master Product'),
    )
    ERROR = 'error'
    SYNCED = 'synced'
    UNSYNCED = 'unsynced'
    STATUS_CHOICES = (
        (ERROR, 'Error'),
        (SYNCED, 'Synced'),
        (UNSYNCED, 'Unsynced'),
    )

    description = models.CharField(max_length=255, null=True, blank=True)
    error_msg = models.TextField(blank=True, null=True)
    key = models.CharField(max_length=255, db_index=True)
    m_type = models.CharField(max_length=30, choices=METADATA_TYPE_CHOICES)
    namespace = models.CharField(max_length=50, choices=NAMESPACE_CHOICES)
    product_metadata = models.ForeignKey(MetadataProduct)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES,
                              default=UNSYNCED)
    value = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            orig = MetadataProductAttribute.objects.get(pk=self.pk)
            obj_modified = ((orig.key != self.key) or
                            (orig.description != self.description) or
                            (orig.value != self.value))
            if obj_modified:
                self.status = MetadataProductAttribute.UNSYNCED
                self.error_msg = None
            if self.status == MetadataProductAttribute.SYNCED:
                self.error_msg = None
        super(MetadataProductAttribute, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.key

    class Meta:
        db_table = 'shopify_metadata_product_attribute'
        unique_together = ('product_metadata', 'key', 'm_type')


# ################### CUSTOMER / ORDER / ORDER LINE ###################

class Customer(models.Model):
    store = models.ForeignKey(Store)
    accepts_marketing = models.BooleanField(default=False)
    created_at = models.DateTimeField()
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    customer_id = models.CharField(max_length=32, db_index=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    orders_count = models.CharField(max_length=3, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    total_spent = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField()
    tags = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return unicode(self.email)

    class Meta:
        db_table = 'shopify_customer'


class Order(models.Model):
    CUSTOMER = 'customer'
    FRAUD = 'fraud'
    INVENTORY = 'inventory'
    DECLINED = 'declined'
    OTHER = 'other'
    CANCEL_REASON_CHOICES = (
        (CUSTOMER, 'customer'),
        (FRAUD, 'fraud'),
        (INVENTORY, 'inventory'),
        (DECLINED, 'declined'),
        (OTHER, 'other'),
    )
    PENDING = 'pending'
    AUTHORIZED = 'authorized'
    PARTIALLY_PAID = 'partially_paid'
    PAID = 'paid'
    PARTIALLY_REFUNDED = 'partially_refunded'
    REFUNDED = 'refunded'
    VOIDED = 'voided'
    FINANCIAL_STATUS_CHOICES = (
        (PENDING, 'pending'),
        (AUTHORIZED, 'authorized'),
        (PARTIALLY_PAID, 'partially_paid'),
        (PAID, 'paid'),
        (PARTIALLY_REFUNDED, 'partially_refunded'),
        (REFUNDED, 'refunded'),
        (VOIDED, 'voided'),
    )
    cancel_reason = models.CharField(max_length=20, null=True, blank=True,
                                     choices=CANCEL_REASON_CHOICES)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField()
    customer = models.ForeignKey(Customer, null=True, blank=True)
    email = models.EmailField()
    financial_status = models.CharField(max_length=30,
                                        choices=FINANCIAL_STATUS_CHOICES,
                                        null=True, blank=True)
    landing_site = models.TextField(null=True, blank=True)
    name = models.CharField(max_length=32, db_index=True)
    order_id = models.CharField(max_length=32, db_index=True)
    order_number = models.CharField(max_length=32, db_index=True)
    referring_site = models.TextField(null=True, blank=True)
    shipping_address_address1 = models.CharField(max_length=255, null=True,
                                                 blank=True)
    shipping_address_address2 = models.CharField(max_length=255,
                                                 null=True, blank=True)
    shipping_address_city = models.CharField(max_length=100, null=True,
                                             blank=True)
    shipping_address_company = models.CharField(max_length=100, null=True,
                                                blank=True)
    shipping_address_country = models.CharField(max_length=100, null=True,
                                                blank=True)
    shipping_address_first_name = models.CharField(max_length=50, null=True,
                                                   blank=True)
    shipping_address_last_name = models.CharField(max_length=50, null=True,
                                                  blank=True)
    shipping_address_latitude = models.DecimalField(max_digits=8,
                                                    decimal_places=6, null=True,
                                                    blank=True)
    shipping_address_longitude = models.DecimalField(max_digits=9,
                                                     decimal_places=6,
                                                     null=True, blank=True)
    shipping_address_phone = models.CharField(max_length=50, null=True,
                                              blank=True)
    shipping_address_province = models.CharField(max_length=100, null=True,
                                                 blank=True)
    shipping_address_zip = models.CharField(max_length=20, null=True,
                                            blank=True)
    shipping_address_name = models.CharField(max_length=255, null=True,
                                             blank=True)
    shipping_address_country_code = models.CharField(max_length=2, null=True,
                                                     blank=True)
    shipping_address_province_code = models.CharField(max_length=5, null=True,
                                                      blank=True)
    shipping_type = models.CharField(max_length=255, null=True, blank=True)
    source_name = models.CharField(max_length=50, null=True, blank=True)
    subtotal_price = models.DecimalField(max_digits=9, decimal_places=2)
    total_discounts = models.DecimalField(max_digits=9, decimal_places=2)
    total_price = models.DecimalField(max_digits=9, decimal_places=2)
    total_tax = models.DecimalField(max_digits=9, decimal_places=2)
    store = models.ForeignKey(Store)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'shopify_order'


class OrderLine(models.Model):
    brand_model = models.CharField(max_length=255, null=True, blank=True)
    collection = models.CharField(max_length=255, null=True, blank=True)
    collection_handle = models.CharField(max_length=200, null=True, blank=True)
    line_id = models.CharField(max_length=32, db_index=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    order = models.ForeignKey(Order)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    product_id = models.CharField(max_length=32, null=True, blank=True)
    product_full_id = models.CharField(max_length=200, null=True, blank=True)
    quantity = models.IntegerField()
    sku = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    total_discount = models.DecimalField(max_digits=9, decimal_places=2,
                                         null=True, blank=True)
    variant_id = models.CharField(max_length=32, null=True, blank=True)
    variant_title = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'shopify_order_line'


# ################### INVENTORY SUPPLIER ###################

class InventorySupplier(models.Model):
    store = models.ForeignKey(Store)
    supplier_id = models.PositiveIntegerField(db_index=True)
    name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField()
    telephone = models.CharField(max_length=50)
    fax = models.CharField(max_length=50, null=True, blank=True)
    street = models.TextField()
    city = models.CharField(max_length=255)
    country_id = models.CharField(max_length=3)
    state = models.CharField(max_length=255)
    postcode = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    website = models.CharField(max_length=255, null=True, blank=True)
    status = models.BooleanField(default=True)
    total_order = models.IntegerField()
    purchase_order = models.DecimalField(max_digits=12, decimal_places=4)
    return_order = models.DecimalField(max_digits=12, decimal_places=4)
    last_purchase_order = models.DateField(null=True, blank=True)
    create_by = models.CharField(max_length=255, null=True, blank=True)
    password_hash = models.CharField(max_length=255, null=True, blank=True)
    is_dropship = models.BooleanField(default=False)
    is_regular = models.BooleanField(default=True)
    is_ghost_product = models.BooleanField(default=False)
    enable_promo_pen = models.BooleanField(default=True)
    enable_auto_product = models.BooleanField(default=True)
    invfeed_enable = models.BooleanField(default=False)
    invfeed_url = models.CharField(max_length=255, null=True, blank=True)
    invfeed_user = models.CharField(max_length=255, null=True, blank=True)
    invfeed_pass = models.CharField(max_length=255, null=True, blank=True)
    invfeed_cookie = models.CharField(max_length=255, null=True, blank=True)
    invfeed_prepare = models.CharField(max_length=255, null=True, blank=True)
    invfeed_delimiter = models.CharField(max_length=16, null=True, blank=True)
    invfeed_col_sku = models.CharField(max_length=16, null=True, blank=True)
    invfeed_col_qty = models.CharField(max_length=16, null=True, blank=True)
    shipstation_enable = models.BooleanField(default=False)
    shipstation_api_key = models.CharField(max_length=255, null=True,
                                           blank=True)
    shipstation_api_secret = models.CharField(max_length=255, null=True,
                                              blank=True)
    invfeed_header_start = models.IntegerField()
    invfeed_content_start = models.IntegerField()
    invfeed_user_param = models.CharField(max_length=255, null=True, blank=True)
    invfeed_pass_param = models.CharField(max_length=255, null=True, blank=True)
    invfeed_col_disc = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = ('store', 'supplier_id')
        db_table = 'shopify_inventory_supplier'


class InventorySupplierMapping(models.Model):
    cost = models.DecimalField(max_digits=9, decimal_places=2, null=True,
                                blank=True)
    sku = models.CharField(max_length=64, null=True, blank=True)
    supplier = models.ForeignKey(InventorySupplier)
    supplier_code = models.CharField(max_length=50, null=True, blank=True)

    def __unicode__(self):
        return '{} {}'.format(self.supplier_code, self.sku)

    class Meta:
        db_table = 'shopify_inventory_supplier_mapping'


class InventoryUpdateFile(models.Model):
    STONE_EDGE = 'stone_edge'
    DS_HR = 'ds_hr'
    VENDOR_SOURCE_CHOICES = (
        (STONE_EDGE, 'Stone Edge'),
        (DS_HR, 'DS - Highest Rated'),
    )
    created_at = models.DateTimeField()
    file = models.FileField(upload_to='inventory_update',
                            storage=MultipleLevelFileSystemStorage())
    name = models.CharField(max_length=255)
    output = models.TextField(blank=True, null=True)
    store = models.ForeignKey(Store)
    success = models.BooleanField(default=False)
    vendor_source = models.CharField(max_length=30,
                                     choices=VENDOR_SOURCE_CHOICES)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'shopify_inventory_update_file'


class InventoryUpdateLog(models.Model):
    error = models.TextField(blank=True, null=True)
    file = models.ForeignKey(InventoryUpdateFile)
    created_at = models.DateTimeField(null=True, blank=True)
    new_qty = models.IntegerField(null=True, blank=True)
    previous_qty = models.IntegerField(null=True, blank=True)
    qoh_qty = models.IntegerField(null=True, blank=True)
    sku = models.CharField(max_length=255)
    success = models.BooleanField(default=False)
    synced = models.BooleanField(default=False)

    def __unicode__(self):
        return self.sku

    class Meta:
        db_table = 'shopify_inventory_update_log'


# ################### FEED ###################

class Feed(models.Model):
    store = models.ForeignKey(Store)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='feeds',
                            storage=OverwriteFileSystemStorage(), blank=True,
                            null=True)
    created_at = models.DateTimeField()
    error = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'shopify_feed'


# ################### PAGE ###################

class Page(models.Model):
    author = models.CharField(max_length=255)
    body_html = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField()
    handle = models.CharField(max_length=255)
    shopify_id = models.CharField(max_length=32, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    shop_id = models.CharField(max_length=32)
    store = models.ForeignKey(Store)
    template_suffix = models.CharField(max_length=100, null=True, blank=True)
    title = models.CharField(max_length=255)
    updated_at = models.DateTimeField()

    def __unicode__(self):
        return unicode(self.title)

    class Meta:
        db_table = 'shopify_page'


# ################### MASTER TABLES ###################

class MasterAttribute(models.Model):
    attribute_code = models.CharField(max_length=255, unique=True,
                                      db_index=True, blank=True, null=True)
    attribute_id = models.SmallIntegerField(unique=True, db_index=True)
    attribute_model = models.CharField(max_length=255, blank=True, null=True)
    backend_model = models.CharField(max_length=255, blank=True, null=True)
    backend_table = models.CharField(max_length=255, blank=True, null=True)
    backend_type = models.CharField(max_length=8)
    default_value = models.TextField(blank=True, null=True)
    entity_type_id = models.SmallIntegerField()
    frontend_class = models.CharField(max_length=255, blank=True, null=True)
    frontend_input = models.CharField(max_length=50, blank=True, null=True)
    frontend_label = models.CharField(max_length=255, blank=True, null=True)
    frontend_model = models.CharField(max_length=255, blank=True, null=True)
    is_required = models.BooleanField()
    is_unique = models.BooleanField()
    is_user_defined = models.BooleanField()
    note = models.CharField(max_length=255, blank=True, null=True)
    source_model = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return self.attribute_code

    class Meta:
        db_table = 'shopify_master_attribute'


class MasterAttributeMapping(models.Model):
    attribute = models.ForeignKey(MasterAttribute, null=True, blank=True)
    attribute_group_name = models.CharField(max_length=255, null=True,
                                            blank=True)
    attribute_set = models.ForeignKey('MasterAttributeSet', null=True,
                                      blank=True)
    sort_order = models.SmallIntegerField()

    def __unicode__(self):
        return self.attribute_set_name

    class Meta:
        db_table = 'shopify_master_attribute_mapping'


class MasterAttributeSet(models.Model):
    attribute_set_id = models.SmallIntegerField(unique=True, db_index=True)
    attribute_set_name = models.CharField(max_length=255, db_index=True,
                                          null=True, blank=True)
    attribute_set_url = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.attribute_set_name

    class Meta:
        db_table = 'shopify_master_attribute_set'


class MasterAttributeValue(models.Model):
    attribute = models.ForeignKey(MasterAttribute, null=True, blank=True)
    product = models.ForeignKey('MasterProduct')
    value = models.TextField()

    def __unicode__(self):
        return self.attribute_code

    class Meta:
        db_table = 'shopify_master_attribute_value'


class MasterCategory(models.Model):
    brand_model_name = models.CharField(max_length=510, db_index=True,
                                        null=True, blank=True)
    brand_model_url = models.TextField(null=True, blank=True)
    brand_name = models.CharField(max_length=255, null=True, blank=True)
    brand_url = models.CharField(max_length=255, null=True, blank=True)
    category_name = models.CharField(max_length=255, db_index=True, null=True,
                                     blank=True)
    category_url = models.CharField(max_length=255, null=True, blank=True)
    hyphenated_brand_model_name = models.CharField(max_length=510,
                                                   db_index=True, null=True,
                                                   blank=True)
    mcid = models.PositiveIntegerField(unique=True, db_index=True)
    model_name = models.CharField(max_length=255, null=True, blank=True)
    model_url = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return str(self.mcid)

    @staticmethod
    def get_next_available_mcid():
        return MasterCategory.objects.all().aggregate(models.Max('mcid'))[
                   'mcid__max'] + 1

    class Meta:
        db_table = 'shopify_master_category'


class MasterProduct(models.Model):
    attribute_set = models.ForeignKey(MasterAttributeSet, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    mpid = models.PositiveIntegerField(unique=True, db_index=True)
    sku = models.CharField(max_length=100, db_index=True, null=True, blank=True)

    def __unicode__(self):
        return str(self.mpid)

    @staticmethod
    def get_next_available_mpid():
        return MasterProduct.objects.all().aggregate(models.Max('mpid'))['mpid__max'] + 1

    class Meta:
        db_table = 'shopify_master_product'


# ################### SHOPIFY TRANSACTION ###################


class ShopifyTransaction(models.Model):
    UNPROCESSED = 'UNPROCESSED'
    PROCESSED = 'PROCESSED'
    ERROR = 'ERROR'
    STATUS_CHOICES = (
        (UNPROCESSED, 'Unprocessed'),
        (PROCESSED, 'Processed'),
        (ERROR, 'Error'),
    )
    PRODUCT_CREATE = 'PRODUCT_CREATE'
    PRODUCT_UPDATE = 'PRODUCT_UPDATE'
    TRANSACTION_TYPE_CHOICES = (
        (PRODUCT_CREATE, 'Product creation'),
        (PRODUCT_UPDATE, 'Product update'),
    )

    content = JSONField()
    date_processed = models.DateTimeField(blank=True, null=True)
    date_received = models.DateTimeField(default=timezone.now)
    error_msg = models.TextField('Error message', blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES,
                              default=UNPROCESSED)
    store = models.ForeignKey(Store)
    title = models.CharField(max_length=255)
    transaction_type = models.CharField(max_length=40,
                                        choices=TRANSACTION_TYPE_CHOICES)

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.pk is not None:
            if self.status != ShopifyTransaction.ERROR:
                self.error_msg = None
        super(ShopifyTransaction, self).save(*args, **kwargs)

    class Meta:
        db_table = 'shopify_transaction'
