Supplier Inventory
==================

Enables download, processing, and upload of supplier feed to mobovidata DB.

===============

**MODEL NAME**:
    ``SupplierInventory``

**TABLE NAME**:
    ``supplier_inventory``


**FIELDS**:
    ``product_id``

    ``supplier_id``

    ``supplier_sku``

    ``sku``

    ``stock``

    ``created_at``

    ``updated_at``

==============

**OPERATION**

Run following function passing it the supplier feed URL & the supplier's ID, which can be found in common.py in the ``SUPPLIER_IDS`` dictionary.

    ``update_supplier_inventory_table(url, supplier_id)``

This will return a boolean:

    ``True``

if database is correctly populated.

    ``False``

if there was an error during the DB population step.
