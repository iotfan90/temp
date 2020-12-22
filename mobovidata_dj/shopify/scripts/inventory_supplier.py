from django.db import connections

from mobovidata_dj.shopify.models import (InventorySupplier,
                                          InventorySupplierMapping, Store)


def get_inventory_suppliers():
    cursor = connections['magento'].cursor()
    cursor.execute('''
            SELECT * FROM erp_inventory_supplier;
        ''')

    columns = cursor.description
    suppliers = [
        {columns[index][0]: column for index, column in enumerate(value)} for
        value in cursor.fetchall()]

    return suppliers


def get_inventory_suppliers_mapping():
    cursor = connections['magento'].cursor()
    cursor.execute('''
            SELECT erps.supplier_id, erp.supplier_sku, cpe.sku
            FROM erp_inventory_supplier_product as erp
            LEFT JOIN erp_inventory_supplier as erps on erps.supplier_id = erp.supplier_id
            LEFT JOIN catalog_product_entity as cpe on erp.product_id = cpe.entity_id
        ''')

    columns = cursor.description
    mapping = [
        {columns[index][0]: column for index, column in enumerate(value)} for
        value in cursor.fetchall()]

    return mapping


def save_inventory_suppliers():
    store = Store.objects.get(identifier='shopify-we')
    inventory_suppliers = get_inventory_suppliers()
    i_s_bulk = []
    for inventory_supplier in inventory_suppliers:
        obj = InventorySupplier(**inventory_supplier)
        obj.store = store
        i_s_bulk.append(obj)

    InventorySupplier.objects.bulk_create(i_s_bulk)


def save_inventory_suppliers_mapping():
    i_s = dict(InventorySupplier.objects.all().values_list('supplier_id', 'pk'))

    mapping = get_inventory_suppliers_mapping()
    i_s_m = []
    for m in mapping:
        obj = InventorySupplierMapping(supplier_id=i_s[m['supplier_id']],
                                       supplier_code=m['supplier_sku'],
                                       sku=m['sku'])
        i_s_m.append(obj)
    InventorySupplierMapping.objects.bulk_create(i_s_m)
