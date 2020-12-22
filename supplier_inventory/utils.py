import urllib2

from modjento.models import CatalogProductEntity, ErpInventorySupplierProduct
from supplier_inventory.models import SupplierInventory


def update_supplier_inventory_table(url, supplier_id):
    """
    Pulls supplier feed from given url, matches supplier SKUs to our SKUs and
    updates table with supplier_id, supplier_sku, sku, product_id, stock
    @param url: str, feed_url to fetch data from
    @param supplier_id: str, supplier code in all caps
    @return: bool representing success or failure of table population
    """

    # Fetch and process data from supplier's feed
    response = urllib2.urlopen(url)
    data = map(lambda entry: entry.replace(' ', '').split(','),
               response.read().split('\r\n'))

    # Fetch supplier data from Magento DB
    hr_table = ErpInventorySupplierProduct.objects.all()
    hr_sku_inv = {r[0]: r[1] for r in data if len(r) > 1}
    # Isolate SKUs from data fetched from supplier feed
    data_hr_skus = [each[0] for each in data[1:]]
    product_ids = {x.product_id:[
        x.product_id, x.supplier_sku, hr_sku_inv.get(x.supplier_sku)
    ] for x in hr_table if x.supplier_sku in data_hr_skus and x.supplier_id == supplier_id}
    catalog_table = CatalogProductEntity.objects.filter(entity_id__in=[k for k in product_ids])
    for x in catalog_table:
        p = product_ids.get(x.entity_id)
        p.append(x.sku)
    entries = [v for v in product_ids.values()]
    # Create or update entries in database
    try:
        for row in entries:
            SupplierInventory.objects.update_or_create(
                product_id=row[0],
                supplier_id=supplier_id,
                supplier_sku=row[1],
                sku=row[3],
                stock=row[2]
            )
        return True
    except Exception as ex:
        print ex
        return False
