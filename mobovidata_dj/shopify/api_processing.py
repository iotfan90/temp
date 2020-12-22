import dateutil.parser

from .models import (Customer, Metafield, Order, Page, Product, ProductImage,
                     ProductOption, ProductOptionValue, ProductTag,
                     ProductVariant, SmartCollection, SmartCollectionImage,
                     SmartCollectionRule)


class ProcessProducts(object):

    def __init__(self, store, products=[]):
        self._store = store
        self._products = products
        self._date_time = store.product_task_run_at

        # Load existent tags
        self._product_tags = {}
        tags = ProductTag.objects.all()
        for tag in tags:
            self._product_tags[tag.name] = {'tag': tag, 'products': []}

        # Load existent values
        self._product_option_values = {}
        values = ProductOptionValue.objects.all()
        for value in values:
            self._product_option_values[value.name] = {'value': value,
                                                        'options': []}

    def parse_products(self):
        for product in self._products:
            images = {}
            variants = {}

            # Parse Product
            prod_obj, created_prod = (Product.objects
                .filter(store=self._store)
                .update_or_create(
                product_id=product['id'],
                defaults={
                    'store': self._store,
                    'title': product.get('title', None),
                    'body_html': product.get('body_html', None),
                    'vendor': product.get('vendor', None),
                    'product_type': product.get('product_type', None),
                    'handle': product.get('handle', None),
                    'created_at': product.get('created_at', None),
                    'updated_at': product.get('updated_at', None),
                    'published_at': product.get('published_at', None),
                    'template_suffix': product.get('template_suffix', None),
                    'published_scope': product.get('published_scope', None),
                },
            ))

            # Parse Tags
            self._parse_tags(product, prod_obj, created_prod)

            # Parse Options
            self._parse_options(product, prod_obj, created_prod)

            # Parse Images
            self._parse_images(product, prod_obj, created_prod, images)

            # Parse Variants
            self._parse_variants(product, prod_obj, created_prod, variants)

            # Add m2m Image - Variants
            self._add_m2m_variants_images(product, created_prod, images,
                                           variants)

        # Create m2m Tags
        self._add_m2m_tags()

        # Create m2m ProductOptionValues
        self._add_m2m_option_values()

    def delete_products(self, product_ids):
        Product.objects.filter(store=self._store,
                               product_id__in=product_ids).delete()

    def _parse_tags(self, product, prod_obj, created_prod):
        if not created_prod:
            old_tag_names = set(
                prod_obj.producttag_set.all().values_list('name', flat=True))
        new_tag_names = set()
        for tag in product['tags'].split(','):
            tag = tag.strip().lower()
            new_tag_names.add(tag)
            if created_prod or tag not in old_tag_names:
                if tag in self._product_tags:
                    self._product_tags[tag]['products'].append(prod_obj)
                else:
                    self._product_tags[tag] = {'tag': ProductTag(name=tag),
                                                'products': [prod_obj]}
        if not created_prod:
            deleted_tags = old_tag_names - new_tag_names
            if deleted_tags:
                deleted_tags = (ProductTag.objects
                                .filter(name__in=deleted_tags)
                                .values_list('id', flat=True))
                (ProductTag.products.through.objects
                 .filter(producttag_id__in=deleted_tags,
                         product_id=prod_obj).delete())

    def _parse_options(self, product, prod_obj, created_prod):
        if not created_prod:
            old_option_ids = set(
                prod_obj.productoption_set.all().values_list('option_id',
                                                             flat=True))
        new_option_ids = set()
        for option in product['options']:
            new_option_ids.add(str(option['id']))
            opt_obj, created_opt = (ProductOption.objects
                .filter(product__store=self._store)
                .update_or_create(
                option_id=option['id'],
                defaults={
                    'product': prod_obj,
                    'name': option.get('name', None),
                    'position': option.get('position', None)
                }
            ))

            if not created_prod:
                old_option_values = set(
                    opt_obj.productoptionvalue_set.all().values_list('name',
                                                                     flat=True))
            new_option_values = set()
            for value in option['values']:
                value = value.strip().lower()
                new_option_values.add(value)
                if created_prod or value not in old_option_values:
                    if value in self._product_option_values:
                        self._product_option_values[value]['options'].append(
                            opt_obj)
                    else:
                        self._product_option_values[value] = {
                            'value': ProductOptionValue(name=value),
                            'options': [opt_obj]}
            if not created_prod:
                deleted_option_values = old_option_values - new_option_values
                if deleted_option_values:
                    deleted_option_values = (ProductOptionValue.objects
                                             .filter(name__in=deleted_option_values)
                                             .values_list('id', flat=True))
                    (ProductOptionValue.options.through.objects
                     .filter(productoptionvalue_id__in=deleted_option_values,
                             productoption_id=opt_obj).delete())

        if not created_prod:
            deleted_options = old_option_ids - new_option_ids
            ProductOption.objects.filter(
                option_id__in=deleted_options).delete()

    def _parse_images(self, product, prod_obj, created_prod, images):
        if not created_prod:
            old_image_ids = set(
                prod_obj.productimage_set.all().values_list('image_id',
                                                            flat=True))
            for img in prod_obj.productimage_set.all():
                images[int(img.image_id)] = img
        new_image_ids = set()
        for image in product['images']:
            new_image_ids.add(str(image['id']))
            updated_at = dateutil.parser.parse(image.get('updated_at', None))
            if created_prod or updated_at > self._date_time:
                img_obj, created_img = (ProductImage.objects
                    .filter(product__store=self._store)
                    .update_or_create(
                    image_id=image['id'],
                    defaults={
                        'product': prod_obj,
                        'position': image.get('position', None),
                        'created_at': image.get('created_at', None),
                        'updated_at': image.get('updated_at', None),
                        'width': image.get('width', None),
                        'height': image.get('height', None),
                        'src': image.get('src', None)
                    }
                ))
                images[int(img_obj.image_id)] = img_obj
        if not created_prod:
            deleted_images = old_image_ids - new_image_ids
            ProductImage.objects.filter(image_id__in=deleted_images).delete()

    def _parse_variants(self, product, prod_obj, created_prod, variants):
        if not created_prod:
            old_variant_ids = set(
                prod_obj.productvariant_set.all().values_list('variant_id',
                                                              flat=True))
            for var in prod_obj.productvariant_set.all():
                variants[int(var.variant_id)] = var
        new_variant_ids = set()
        for variant in product['variants']:
            new_variant_ids.add(str(variant['id']))
            updated_at = dateutil.parser.parse(variant.get('updated_at', None))
            if created_prod or updated_at > self._date_time:
                var_obj, created_var = (ProductVariant.objects
                    .filter(product__store=self._store)
                    .update_or_create(
                    variant_id=variant['id'],
                    defaults={
                        'product': prod_obj,
                        'title': variant.get('title', None),
                        'price': variant.get('price', None),
                        'sku': variant.get('sku', None),
                        'position': variant.get('position', None),
                        'grams': variant.get('grams', None),
                        'inventory_policy': variant.get('inventory_policy',
                                                        None),
                        'compare_at_price': variant.get('compare_at_price',
                                                        None),
                        'fulfillment_service': variant.get(
                            'fulfillment_service',
                            None),
                        'inventory_management': variant.get(
                            'inventory_management',
                            None),
                        'option1': variant.get('option1', None),
                        'option2': variant.get('option2', None),
                        'option3': variant.get('option3', None),
                        'created_at': variant.get('created_at', None),
                        'updated_at': variant.get('updated_at', None),
                        'taxable': variant.get('taxable', False),
                        'barcode': variant.get('barcode', None),
                        'inventory_quantity': variant.get('inventory_quantity',
                                                          None),
                        'weight': variant.get('weight', None),
                        'weight_unit': variant.get('weight_unit', None),
                        'old_inventory_quantity': variant.get(
                            'old_inventory_quantity',
                            None),
                        'requires_shipping': variant.get('requires_shipping',
                                                         False),
                        'available': variant.get('available', True)
                    }
                ))
                variants[int(var_obj.variant_id)] = var_obj
        if not created_prod:
            deleted_images = old_variant_ids - new_variant_ids
            ProductVariant.objects.filter(
                variant_id__in=deleted_images).delete()

    def _add_m2m_variants_images(self, product, created_prod, images, variants):
        for image in product['images']:
            updated_at = dateutil.parser.parse(image.get('updated_at', None))
            if created_prod or updated_at > self._date_time:
                variants_bulk = []
                for variant_id in image['variant_ids']:
                    variants_bulk.append(variants[variant_id])
                if variants_bulk:
                    img_obj = images[image['id']]
                    img_obj.variants.clear()
                    img_obj.variants.add(*variants_bulk)

        for variant in product['variants']:
            if 'image_id' in variant and variant['image_id']:
                updated_at = dateutil.parser.parse(
                    variant.get('updated_at', None))
                if created_prod or updated_at > self._date_time:
                    var_obj = variants[variant['id']]
                    var_obj.image = images[variant['image_id']]
                    var_obj.save()

    def _add_m2m_tags(self):
        for tag in self._product_tags.values():
            obj = tag['tag']
            m2m = tag['products']
            if m2m:
                obj.save()
                obj.products.add(*m2m)
        # Clear empty tags
        ProductTag.objects.filter(products=None).delete()

    def _add_m2m_option_values(self):
        for value in self._product_option_values.values():
            obj = value['value']
            m2m = value['options']
            if m2m:
                obj.save()
                obj.options.add(*m2m)
        # Clear empty option values
        ProductOptionValue.objects.filter(options=None).delete()


class ProcessSmartCollections(object):

    def __init__(self, store, collections=[]):
        self._store = store
        self._collections = collections
        self._collection_images = []
        self._collection_rules = []

    def parse_smart_collections(self):
        for collection in self._collections:
            # Collection
            if collection.get('body_html', None):
                body_html = collection.get('body_html', '').encode('unicode_escape')
            else:
                body_html = None
            coll_obj, created_coll = (SmartCollection.objects
                .filter(store=self._store)
                .update_or_create(
                collection_id=collection['id'],
                defaults={
                    'store': self._store,
                    'handle': collection.get('handle', None),
                    'title': collection.get('title', None),
                    'updated_at': collection.get('updated_at', None),
                    'body_html': body_html,
                    'published_at': collection.get('published_at', None),
                    'sort_order': collection.get('sort_order', None),
                    'template_suffix': collection.get('template_suffix', None),
                    'published_scope': collection.get('published_scope', None),
                    'disjunctive': collection.get('disjunctive', False),
                }
            ))

            # Parse Rules
            self._parse_rules(collection, coll_obj, created_coll)

            # Parse Image
            self._parse_image(collection, coll_obj, created_coll)

        # Add Rules and Image
        SmartCollectionRule.objects.bulk_create(self._collection_rules)
        SmartCollectionImage.objects.bulk_create(self._collection_images)

    def delete_collections(self, collection_ids):
        (SmartCollection.objects
         .filter(store=self._store, collection_id__in=collection_ids)
         .delete())

    def _parse_rules(self, collection, coll_obj, created_coll):
        # Clear rules
        if not created_coll:
            coll_obj.smartcollectionrule_set.all().delete()
        # Add rules again
        for rule in collection['rules']:
            rule_obj = SmartCollectionRule(
                smart_collection=coll_obj,
                relation=rule.get('relation', None),
                condition=rule.get('condition', None),
                column=rule.get('column', None)
            )
            self._collection_rules.append(rule_obj)

    def _parse_image(self, collection, coll_obj, created_coll):
        if 'image' in collection and collection['image']:
            # Clear image
            if not created_coll:
                (SmartCollectionImage.objects
                    .filter(smart_collection=coll_obj).delete())
            # Add image again
            image = collection['image']
            img_obj = SmartCollectionImage(
                smart_collection=coll_obj,
                created_at=image.get('created_at', None),
                width=image.get('width', None),
                height=image.get('height', None),
                src=image.get('src', None),
            )
            self._collection_images.append(img_obj)


class ProcessOrders(object):

    def __init__(self, store, orders=[]):
        self._store = store
        self._orders = orders

    def parse_orders(self):
        for order in self._orders:
            # Customer
            customer = order.get('customer', None)
            cust_obj = None
            if customer:
                cust_obj, created_cust = (Customer.objects
                    .filter(store=self._store)
                    .update_or_create(
                        customer_id=customer['id'],
                        defaults={
                            'store': self._store,
                            'accepts_marketing': customer.get('accepts_marketing',
                                                              False),
                            'created_at': customer.get('created_at', None),
                            'email': customer.get('email', None),
                            'phone': customer.get('phone', None),
                            'first_name': customer.get('first_name', None),
                            'last_name': customer.get('last_name', None),
                            'note': customer.get('note', None),
                            'orders_count': customer.get('orders_count', None),
                            'state': customer.get('state', None),
                            'total_spent': customer.get('total_spent', None),
                            'updated_at': customer.get('updated_at', None),
                            'tags': customer.get('tags', None),
                        }))

            # Order
            shipping_address = order.get('shipping_address', {})
            shipping_lines = order.get('shipping_lines', None)
            shipping_type = None
            if shipping_lines:
                shipping_type = next(iter([x['title'] for x in shipping_lines]),
                                     None)
            ord_obj, created_ord = (Order.objects
                .filter(store=self._store)
                .update_or_create(
                    order_id=order['id'],
                    defaults={
                        'store': self._store,
                        'customer': cust_obj,
                        'created_at': order.get('created_at', None),
                        'email': order.get('email', None),
                        'financial_status': order.get('financial_status', None),
                        'landing_site': order.get('landing_site', None),
                        'name': order.get('name', None),
                        'order_number': order.get('order_number', None),
                        'referring_site': order.get('referring_site', None),
                        'source_name': order.get('source_name', None),
                        'subtotal_price': order.get('subtotal_price', None),
                        'total_discounts': order.get('total_discounts', None),
                        'total_price': order.get('total_price', None),
                        'total_tax': order.get('total_tax', None),
                        'cancel_reason': order.get('cancel_reason', None),
                        'cancelled_at': order.get('cancelled_at', None),
                        'closed_at': order.get('closed_at', None),
                        'shipping_address_address1': shipping_address.get('address1', None),
                        'shipping_address_address2': shipping_address.get('address2', None),
                        'shipping_address_city': shipping_address.get('city', None),
                        'shipping_address_company': shipping_address.get('company', None),
                        'shipping_address_country': shipping_address.get('country', None),
                        'shipping_address_first_name': shipping_address.get('first_name', None),
                        'shipping_address_last_name': shipping_address.get('last_name', None),
                        'shipping_address_latitude': shipping_address.get('latitude', None),
                        'shipping_address_longitude': shipping_address.get('longitude', None),
                        'shipping_address_phone': shipping_address.get('phone', None),
                        'shipping_address_province': shipping_address.get('province', None),
                        'shipping_address_zip': shipping_address.get('zip', None),
                        'shipping_address_name': shipping_address.get('name', None),
                        'shipping_address_country_code': shipping_address.get('country_code', None),
                        'shipping_address_province_code': shipping_address.get('province_code', None),
                        'shipping_type': shipping_type,
                    }))

            # Order line items
            line_items = order['line_items']

            for line in line_items:
                brand_model = next((p['value'] for p in line.get('properties', None)
                                    if p['name'] == 'collectionHandle'), None)
                p = line.get('properties', None)
                collection = None
                collection_handle = None
                product_full_id = None
                if p:
                    collection = next(iter([x['value'] for x in p if x['name'] == 'collection']), None)
                    collection_handle = next(iter([x['value'] for x in p if x['name'] == 'collection_handle']), None)
                    product_full_id = next(iter([x['value'] for x in p if x['name'] == 'product_full_id']), None)

                ord_l_obj, created_ord_l = (ord_obj.orderline_set
                    .update_or_create(
                        line_id=line['id'],
                        defaults={
                            'order': ord_obj,
                            'price': line.get('price', None),
                            'quantity': line.get('quantity', None),
                            'sku': line.get('sku', None),
                            'title': line.get('title', None),
                            'variant_title': line.get('variant_title', None),
                            'name': line.get('name', None),
                            'product_id': line.get('product_id', None),
                            'variant_id': line.get('variant_id', None),
                            'total_discount': line.get('total_discount', None),
                            'brand_model': brand_model,
                            'collection': collection,
                            'collection_handle': collection_handle,
                            'product_full_id': product_full_id
                        }))

    def delete_orders(self, order_ids):
        (Order.objects
         .filter(store=self._store, order_id__in=order_ids)
         .delete())


class ProcessPages(object):

    def __init__(self, store, pages=[]):
        self._store = store
        self._pages = pages

    def parse_pages(self):
        for page in self._pages:
            Page.objects.update_or_create(
                shopify_id=page['id'], store=self._store,
                defaults={
                    'author': page['author'],
                    'body_html': page['body_html'].encode('unicode_escape') if page['body_html'] else '',
                    'created_at': page['created_at'],
                    'handle': page['handle'],
                    'published_at': page.get('published_at', None),
                    'shop_id': page['shop_id'],
                    'template_suffix': page.get('template_suffix', None),
                    'title': page['title'],
                    'shop_id': page['shop_id'],
                    'updated_at': page['updated_at'],
                })


class ProcessMetafields(object):

    def __init__(self, store, metafields=[]):
        self._store = store
        self._metafields = metafields

    def parse_metafields(self):
        for metafield in self._metafields:
            Metafield.objects.update_or_create(
                shopify_id=metafield['id'], store=self._store,
                owner_id=metafield['owner_id'],
                owner_resource=metafield['owner_resource'],
                defaults={
                    'created_at': metafield['created_at'],
                    'description': metafield.get('description', None),
                    'key': metafield['key'],
                    'namespace': metafield['namespace'],
                    'value': metafield['value'],
                    'value_type': metafield['value_type'],
                    'updated_at': metafield['updated_at'],
                })
