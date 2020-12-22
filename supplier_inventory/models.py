from __future__ import unicode_literals

from django.db import models

class SupplierInventory(models.Model):
    product_id = models.CharField(max_length=100)
    supplier_id = models.IntegerField()
    supplier_sku = models.CharField(max_length=100)
    sku = models.CharField(max_length=100)
    stock = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'supplier_inventory'
