from mobovidata_dj.shopify.connect import ShopifyConnect
from mobovidata_dj.shopify.models import Store


def flat_co_products():
    store = Store.objects.get(identifier='shopify-co')

    shopify = ShopifyConnect(store)

    try:
        product_qty = shopify.get_products_total_quantity(
            updated_at_min=store.product_task_run_at)['count']
        total_pages = -(-product_qty // 250)

        products = []

        for page in xrange(1, total_pages + 1):
            response = shopify.get_products(page=page)
            products.extend(response['products'])
        counter = 0
        for product in products:
            if len(product['variants']) > 1:
                # Remove product
                status_code, content = shopify.delete_product(product['id'])
                if status_code == 200:
                    counter += 1
                else:
                    print str(content['errors'])
        print 'Products deleted: ', counter
    except Exception, ex:
        print repr(ex)
        raise
