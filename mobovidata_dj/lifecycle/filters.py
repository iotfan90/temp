import urlparse
import uuid

from collections import defaultdict
from django.conf import settings

from modjento.models import (DatafeedMasterStore2, SalesFlatQuote,
                             SalesFlatQuoteItem)


class HasRIIDFilter(object):
    def filter(self, customers, customer_data):
        customers = [c for c in customers if c.riid]
        # Remove customers with no riid from customer_data
        updated = defaultdict(dict)
        updated.update({c.uuid: customer_data[c.uuid] for c in customers})

        for c in customers:
            updated[c.uuid]['riid'] = c.riid

        assert(len(updated.keys()) == len(customers))
        return customers, updated


class ActiveCartInfoFilter(object):
    def filter(self, customers, customer_data):
        customers, customer_data = self.get_cart_info(customers, customer_data)
        customers, customer_data = self.get_cart_details(customers, customer_data)
        return customers, customer_data

    def get_cart_info(self, customers, customer_data):
        """ Gets cart info from Mage db """

        cart_ids = [c.customerlifecycletracking.cart_id for c in customers]
        # Fetch carts and their details
        carts = SalesFlatQuote.objects.using('magento').filter(entity_id__in=cart_ids,
                                                               is_active=True)
        cart_details = {}
        for cart in carts:
            # Add additional 'cart-level' details here:
            cart_details[str(cart.entity_id)] = {'cart_value': float(cart.base_grand_total),
                                                 'cart_coupon': cart.coupon_code,
                                                 'store_id': cart.store_id,
                                                 'quote_id': str(cart.entity_id),
                                                 }

        # Limit customers to only include those with carts that were returned from Mage
        customers = [c for c in customers if c.customerlifecycletracking.cart_id in cart_details]
        updated = defaultdict(dict)
        updated.update({c.uuid: customer_data[c.uuid] for c in customers if c.uuid in customer_data})

        for customer in customers:
            updated[customer.uuid].update(cart_details[customer.customerlifecycletracking.cart_id])
        return customers, updated

    def __get_product_images(self, image_urls):
        """ Accepts a string of | separated values and returns list of complete image URLs"""

        base_img_url = settings.MAGENTO_URL_PREFIXES['img']
        return [urlparse.urljoin(base_img_url, u) for u in image_urls.split('|')]

    def get_cart_details(self, customers, customer_data):
        """ Gets products and products info related to cart IDs"""
        from collections import defaultdict

        cart_ids = [c.customerlifecycletracking.cart_id for c in customers]

        # Fetch basic info about products in cart
        cart_items = SalesFlatQuoteItem.objects.using('magento').filter(quote__in=cart_ids)

        cart_products = defaultdict(list)
        product_ids = set()
        category_ids = set()
        product_full_ids = set()  # A set because A) No duplicates, B) Hashed so iterating will be faster.
        for item in cart_items:
            cart_id = str(item.quote.entity_id)
            product_full_id = '_'.join([str(item.product_id), '2', str(item.added_from_category_id)])
            product_full_ids.add(product_full_id)
            cart_products[cart_id].append({'sku': item.sku,
                                           'name': item.name,
                                           'product_id': item.product_id,
                                           'quote_id': item.quote_id,
                                           'qty': int(item.qty),
                                           'base_price': float(item.base_price),
                                           'base_row_total': float(item.base_row_total),
                                           'base_row_total_incl_tax': float(item.base_row_total_incl_tax),
                                           'added_from_category_id': item.added_from_category_id,
                                           'product_full_id': product_full_id})
            category_ids.add(item.added_from_category_id)
            product_ids.add(item.product_id)

        # Fetch detailed info about products in cart
        product_details = DatafeedMasterStore2.objects.filter(product_id__in=product_ids,
                                                               category_id__in=category_ids).distinct()
        product_info = {}
        for p in product_details:
            if p.product_full_id in product_full_ids:
                product_info[p.product_full_id] = {'category_id': p.category_id,
                                                   'product_id': p.product_id,
                                                   'product_sku': p.product_sku,
                                                   'is_in_stock': p.is_in_stock,
                                                   'product_long_description': p.product_long_description,
                                                   'category_name': p.category_name,
                                                   'url': urlparse.urljoin(settings.MAGENTO_URL_PREFIXES['pdp'], p.url),
                                                   'images': self.__get_product_images(p.images),
                                                   'reviews': p.reviews,
                                                   'reviews_rating': float(p.reviews_rating),
                                                   'color': p.color,
                                                   'sales_velocity': p.sales_velocity}

        # Add detailed info to basic info
        for k in cart_products:
            for p in cart_products[k]:
                p.update(product_info[p['product_full_id']])

        for customer in customers:
            customer_data[customer.uuid].update(
                {'products': cart_products[customer.customerlifecycletracking.cart_id]})

        return customers, customer_data
