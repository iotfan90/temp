from mobovidata_dj.shopify.connect import ShopifyConnect
from mobovidata_dj.shopify.models import ProductVariant, Store


def delete_co_skus(path):
    store = Store.objects.get(identifier='shopify-co')
    shopify = ShopifyConnect(store)

    with open(path) as f:
        content = f.readlines()
    content = [x.strip() for x in content]
    products = dict(ProductVariant.objects.filter(product__store=store).values_list('sku', 'product__product_id'))
    for line in content:
        try:
            product_id = products[line]
            try:
                status_code, content = shopify.delete_product(product_id)
                if status_code != 200:
                    print 'Delete error:', line, str(content['errors'])
            except Exception:
                print 'Error:', line

        except KeyError:
            print 'Key error:', line

