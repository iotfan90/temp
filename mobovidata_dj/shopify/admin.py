from django.contrib import admin
from rangefilter.filter import DateTimeRangeFilter

from .forms import ModelForm
from .models import (Brand, Customer, Feed, InventorySupplier,
                     InventorySupplierMapping, InventoryUpdateFile,
                     InventoryUpdateLog, MasterAttribute,
                     MasterAttributeMapping, MasterAttributeSet,
                     MasterAttributeValue, MasterCategory, MasterProduct,
                     MetadataCollection, MetadataCollectionAttribute,
                     MetadataProduct, MetadataProductAttribute, Metafield,
                     Model, Order, OrderLine, Page, Product, ProductExtraInfo,
                     ProductImage, ProductOption, ProductOptionValue,
                     ProductTag, ProductVariant, ShopifyTransaction,
                     SmartCollection, SmartCollectionImage, SmartCollectionRule,
                     Store)


# ################### STORE ###################

class StoreAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'name', 'description', 'api_key', 'password',
                    'api_url', 'shop_url')
    search_fields = ('identifier', 'name', 'description', 'api_key', 'password',
                     'api_url', 'shop_url')


# ################### PRODUCT ###################

class ProductAdmin(admin.ModelAdmin):
    list_display = ('store', 'product_id', 'title', 'vendor', 'product_type',
                    'handle', 'tag_list', 'created_at', 'updated_at',
                    'published_at')
    search_fields = ('product_id', 'title', 'vendor',
                     'product_type', 'handle')
    list_filter = ('store', 'created_at', 'updated_at', 'published_at')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.producttag_set.all())[:200]


class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('image_id', 'product', 'position', 'src', 'created_at',
                    'updated_at')
    search_fields = ('image_id', 'position', 'src', 'product__product_id')
    list_filter = ('product__store', 'position', 'created_at', 'updated_at')


class ProductOptionAdmin(admin.ModelAdmin):
    list_display = ('option_id', 'product', 'name', 'position',
                    'values_list')
    search_fields = ('option_id', 'name', 'position', 'product__product_id')
    list_filter = ('product__store', 'position',)

    def values_list(self, obj):
        return u", ".join(o.name for o in obj.productoptionvalue_set.all())


class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('variant_id', 'sku', 'product', 'title', 'price',
                    'position', 'inventory_quantity', 'option1', 'option2',
                    'option3', 'created_at', 'updated_at', 'feed_excluded')
    search_fields = ('variant_id', 'sku', 'title', 'price', 'position',
                    'inventory_quantity', 'created_at', 'updated_at',
                     'product__product_id')
    list_filter = ('product__store', 'position', 'feed_excluded', 'created_at',
                   'updated_at')


class ProductTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_list')
    search_fields = ('name', 'products__product_id')
    # filter_horizontal = ('products',)

    def product_list(self, obj):
        return u", ".join(o.product_id for o in obj.products.all())


class ProductOptionValueAdmin(admin.ModelAdmin):
    list_display = ('name', 'option_list')
    search_fields = ('name', 'options__product__product_id')

    def option_list(self, obj):
        return u", ".join(o.option_id for o in obj.options.all())


class ProductExtraInfoAdmin(admin.ModelAdmin):
    list_display = ('product', 'color')
    search_fields = ('product__product_id', 'product__handle', 'color')

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            self.store = obj.product.store
        return super(ProductExtraInfoAdmin, self).get_form(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'associated_products' and self.store:
            kwargs['queryset'] = Product.objects.filter(store=self.store)
        return super(ProductExtraInfoAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)


# ################### SMART COLLECTION ###################

class SmartCollectionAdmin(admin.ModelAdmin):
    list_display = ('store', 'collection_id', 'title', 'handle', 'sort_order',
                    'published_scope', 'disjunctive', 'updated_at',
                    'published_at')
    search_fields = ('collection_id', 'title', 'handle',
                     'updated_at', 'published_at')
    list_filter = ('store', 'sort_order', 'published_scope', 'disjunctive',
                   'updated_at', 'published_at')


class SmartCollectionRuleAdmin(admin.ModelAdmin):
    list_display = ('smart_collection', 'relation', 'condition', 'column')
    search_fields = ('smart_collection__collection_id', 'relation', 'condition',
                     'column')
    list_filter = ('smart_collection__store', 'relation', 'column')


class SmartCollectionImageAdmin(admin.ModelAdmin):
    list_display = ('smart_collection', 'width', 'height', 'src', 'created_at')
    search_fields = ('smart_collection__collection_id', 'width', 'height',
                     'src', 'created_at')
    list_filter = ('smart_collection__store', 'created_at',)


# ################### METAFIELD ###################

class MetafieldAdmin(admin.ModelAdmin):
    list_display = ('shopify_id', 'store', 'owner_id', 'owner_resource',
                    'namespace', 'key', 'short_value', 'short_description',
                    'value_type', 'created_at', 'updated_at')
    search_fields = ('shopify_id', 'owner_id', 'key', 'value', 'description')
    list_filter = ('store', 'owner_resource', 'namespace', 'value_type',
                   ('created_at', DateTimeRangeFilter),
                   ('updated_at', DateTimeRangeFilter))

    def short_description(self, obj):
        return obj.description[:200] if obj.description else None

    def short_value(self, obj):
        return obj.value[:200]


# ################### BRAND / MODEL ###################

class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', )
    search_fields = ('name',)


class ModelAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'collection_handle', 'sku_add_on',
                    'top_model', 'image', 'adaptor_type', 'synced_we',
                    'synced_co', 'error_msg_we', 'error_msg_co')
    search_fields = ('brand__name', 'model', 'collection_handle', 'sku_add_on')
    list_filter = ('synced_we', 'synced_co', 'top_model', 'brand')
    filter_horizontal = ('categories',)
    fields = ('brand', 'model', 'collection_handle', 'top_model', 'image',
              'shopify_image', 'sku_add_on', 'categories', 'height', 'width',
              'depth', 'bluetooth', 'headset_type', 'adaptor_type',
              'wireless_charger', 'device_type', 'pouch_size',
              'bluetooth_version', 'removable_battery', 'synced_we',
              'synced_co', 'error_we', 'error_co', 'collection_description')
    readonly_fields = ('synced_we', 'synced_co', 'error_we', 'error_co')
    form = ModelForm

    def error_msg_we(self, obj):
        return obj.error_we[:100] if obj.error_we else None

    def error_msg_co(self, obj):
        return obj.error_co[:100] if obj.error_co else None


# ################### METADATA/ATTRIBUTES ###################

class MetadataCollectionAdmin(admin.ModelAdmin):
    list_display = ('store', 'name')
    search_fields = ('name',)
    list_filter = ('store',)


class MetadataCollectionAttributeAdmin(admin.ModelAdmin):
    list_display = ('store', 'collection_metadata', 'key', 'description',
                    'short_value', 'short_error_msg', 'm_type', 'namespace',
                    'status')
    search_fields = ('collection_metadata__sku', 'key', 'description', 'value')
    list_filter = ('collection_metadata__store', 'm_type', 'namespace',
                   'status')

    def store(self, obj):
        return obj.collection_metadata.store

    def short_value(self, obj):
        return obj.value[:200] if obj.value else None

    def short_error_msg(self, obj):
        return obj.error_msg[:200] if obj.error_msg else None


class MetadataProductAdmin(admin.ModelAdmin):
    list_display = ('store', 'sku')
    search_fields = ('sku',)
    list_filter = ('store',)


class MetadataProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('store', 'product_metadata', 'key', 'description',
                    'short_value', 'short_error_msg', 'm_type', 'namespace',
                    'status')
    search_fields = ('product_metadata__sku', 'key', 'description', 'value')
    list_filter = ('product_metadata__store', 'm_type', 'namespace', 'status')

    def store(self, obj):
        return obj.product_metadata.store

    def short_value(self, obj):
        return obj.value[:200] if obj.value else None

    def short_error_msg(self, obj):
        return obj.error_msg[:200] if obj.error_msg else None


# ################### CUSTOMER / ORDER / ORDER LINE ###################

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'store', 'email', 'first_name', 'last_name',
                    'created_at')
    search_fields = ('customer_id', 'email', 'first_name', 'last_name', 'tags')
    list_filter = ('store', 'created_at', 'accepts_marketing')


class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'order_number', 'store', 'name', 'email',
                    'customer', 'financial_status', 'total_price', 'created_at',
                    'cancelled_at', 'closed_at')
    search_fields = ('order_id', 'order_number', 'name', 'email')
    list_filter = ('store', 'financial_status', 'created_at', 'cancelled_at',
                   'closed_at')


class OrderLineAdmin(admin.ModelAdmin):
    list_display = ('order', 'line_id', 'name', 'product_id', 'variant_id',
                    'sku', 'title', 'variant_title', 'brand_model', 'price',
                    'quantity')
    search_fields = ('line_id', 'order__order_id', 'name', 'order__name',
                     'sku', 'title', 'variant_title', 'product_id',
                     'variant_id', 'brand_model')
    list_filter = ('order__store',)


# ################### INVENTORY SUPPLIER ###################

class InventorySupplierAdmin(admin.ModelAdmin):
    list_display = ('store', 'supplier_id', 'name', 'contact_name', 'email',
                    'description', 'total_order', 'is_dropship', 'is_regular')
    search_fields = ('supplier_id', 'name', 'contact_name', 'email',
                     'description')
    list_filter = ('store', 'is_dropship', 'is_regular')


class InventorySupplierMappingAdmin(admin.ModelAdmin):
    list_display = ('store', 'supplier', 'supplier_code', 'sku', 'cost')
    search_fields = ('supplier__name', 'supplier_code', 'sku', 'cost')
    list_filter = ('supplier__store',)

    def store(self, obj):
        return obj.supplier.store.name


class InventoryUpdateFileAdmin(admin.ModelAdmin):
    list_display = ('store', 'vendor_source', 'name', 'file', 'created_at',
                    'short_output_msg',
                    'success')
    search_fields = ('store__name', 'name', 'created_at', 'output')
    list_filter = ('store', 'success', 'vendor_source',
                   ('created_at', DateTimeRangeFilter))

    def short_output_msg(self, obj):
        return obj.output[:200] if obj.output else None


class InventoryUpdateLogAdmin(admin.ModelAdmin):
    list_display = ('store', 'vendor_source', 'file', 'sku', 'previous_qty',
                    'qoh_qty', 'new_qty', 'created_at', 'short_error_msg',
                    'success', 'synced')
    search_fields = ('file__store__name', 'file__name', 'sku', 'created_at',
                     'error')
    list_filter = ('file__store', 'file__vendor_source', 'success', 'synced',
                   ('created_at', DateTimeRangeFilter))

    def store(self, obj):
        return obj.file.store.name

    def vendor_source(self, obj):
        return obj.file.get_vendor_source_display()

    def short_error_msg(self, obj):
        return obj.error[:200] if obj.error else None


# ################### FEED ###################

class FeedAdmin(admin.ModelAdmin):
    list_display = ('store', 'name', 'file', 'created_at', 'error')
    search_fields = ('store__name', 'name', 'created_at', 'error')
    list_filter = ('store', 'created_at')


# ################### PAGE ###################

class PageAdmin(admin.ModelAdmin):
    list_display = ('store', 'shopify_id', 'title', 'handle', 'author',
                    'created_at', 'updated_at', 'published_at')
    search_fields = ('store__name', 'shopify_id', 'title', 'handle', 'author')
    list_filter = ('store', ('created_at', DateTimeRangeFilter),
                   ('updated_at', DateTimeRangeFilter),
                   ('published_at', DateTimeRangeFilter), )


# ################### MATER TABLES ###################

class MasterAttributeAdmin(admin.ModelAdmin):
    list_display = ('attribute_id', 'attribute_code', 'frontend_label',
                    'frontend_input')
    search_fields = ('attribute_id', 'attribute_code', 'frontend_label')
    list_filter = ('frontend_input', 'is_required', 'is_unique',
                   'is_user_defined')


class MasterAttributeMappingAdmin(admin.ModelAdmin):
    list_display = ('attribute_set_ID', 'attribute_set_name',
                    'attribute_group_name', 'attribute_code', 'frontend_label',
                    'sort_order')
    search_fields = ('attribute_set__attribute_set_id',
                     'attribute_set__attribute_set_name',
                     'attribute_group_name', 'attribute__attribute_code',
                     'attribute__frontend_label', 'sort_order')
    list_filter = ('attribute_set',)

    def attribute_set_ID(self, obj):
        return obj.attribute_set.attribute_set_id

    def attribute_set_name(self, obj):
        return obj.attribute_set.attribute_set_name

    def attribute_code(self, obj):
        return obj.attribute.attribute_code

    def frontend_label(self, obj):
        return obj.attribute.frontend_label


class MasterAttributeSetAdmin(admin.ModelAdmin):
    list_display = ('attribute_set_id', 'attribute_set_name',
                    'attribute_set_url')
    search_fields = ('attribute_set_id', 'attribute_set_name',
                     'attribute_set_url')


class MasterAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('product', 'product_sku', 'frontend_label',
                    'attribute_code', 'short_value', 'frontend_input')
    search_fields = ('product__sku', 'attribute__attribute_code', 'value')
    list_filter = ('attribute__frontend_input',)

    def product_sku(self, obj):
        return obj.product.sku

    def short_value(self, obj):
        return obj.value[:200]

    def attribute_code(self, obj):
        return obj.attribute.attribute_code

    def frontend_label(self, obj):
        return obj.attribute.frontend_label

    def frontend_input(self, obj):
        return obj.attribute.frontend_input


class MasterCategoryAdmin(admin.ModelAdmin):
    list_display = ('mcid', 'category_name', 'brand_model_name',
                    'brand_model_url')
    search_fields = ('mcid', 'category_name', 'brand_model_name',
                    'brand_model_url')


class MasterProductAdmin(admin.ModelAdmin):
    list_display = ('mpid', 'sku', 'attribute_set_ID', 'attribute_set_name',
                    'created_at')
    search_fields = ('mpid', 'sku', 'attribute_set__attribute_set_id',
                     'attribute_set__attribute_set_name')
    list_filter = (('created_at', DateTimeRangeFilter),
                   'attribute_set__attribute_set_name')

    def attribute_set_ID(self, obj):
        return obj.attribute_set.attribute_set_id

    def attribute_set_name(self, obj):
        return obj.attribute_set.attribute_set_name


# ################### SHOPIFY TRANSACTION ###################

class ShopifyTransactionAdmin(admin.ModelAdmin):
    list_display = ('store', 'transaction_type', 'title', 'date_received',
                    'date_processed', 'short_error_msg', 'status')
    search_fields = ('title', 'content', 'error_msg')
    list_filter = ('store', 'status', 'transaction_type',
                   ('date_received', DateTimeRangeFilter),
                   ('date_processed', DateTimeRangeFilter))

    def short_error_msg(self, obj):
        return obj.error_msg[:200] if obj.error_msg else None


admin.site.register(Brand, BrandAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Feed, FeedAdmin)
admin.site.register(InventorySupplier, InventorySupplierAdmin)
admin.site.register(InventorySupplierMapping, InventorySupplierMappingAdmin)
admin.site.register(InventoryUpdateFile, InventoryUpdateFileAdmin)
admin.site.register(InventoryUpdateLog, InventoryUpdateLogAdmin)
admin.site.register(MasterAttribute, MasterAttributeAdmin)
admin.site.register(MasterAttributeMapping, MasterAttributeMappingAdmin)
admin.site.register(MasterAttributeSet, MasterAttributeSetAdmin)
admin.site.register(MasterAttributeValue, MasterAttributeValueAdmin)
admin.site.register(MasterCategory, MasterCategoryAdmin)
admin.site.register(MasterProduct, MasterProductAdmin)
admin.site.register(MetadataCollection, MetadataCollectionAdmin)
admin.site.register(MetadataCollectionAttribute, MetadataCollectionAttributeAdmin)
admin.site.register(MetadataProduct, MetadataProductAdmin)
admin.site.register(MetadataProductAttribute, MetadataProductAttributeAdmin)
admin.site.register(Metafield, MetafieldAdmin)
admin.site.register(Model, ModelAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderLine, OrderLineAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductExtraInfo, ProductExtraInfoAdmin)
admin.site.register(ProductImage, ProductImageAdmin)
admin.site.register(ProductOption, ProductOptionAdmin)
admin.site.register(ProductTag, ProductTagAdmin)
admin.site.register(ProductVariant, ProductVariantAdmin)
admin.site.register(ProductOptionValue, ProductOptionValueAdmin)
admin.site.register(ShopifyTransaction, ShopifyTransactionAdmin)
admin.site.register(SmartCollection, SmartCollectionAdmin)
admin.site.register(SmartCollectionImage, SmartCollectionImageAdmin)
admin.site.register(SmartCollectionRule, SmartCollectionRuleAdmin)
admin.site.register(Store, StoreAdmin)
