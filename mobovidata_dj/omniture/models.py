from django.db import models

from model_managers import SiteCatDataManager


class SiteCatProductData(models.Model):
    product_id_date = models.BigIntegerField(primary_key=True)
    product_id = models.IntegerField(db_index=True)
    visits = models.IntegerField(default=0, null=True)
    page_views = models.IntegerField(default=0)
    date = models.DateField(max_length=128, db_index=True)
    sku = models.CharField(max_length=64, db_index=True)
    cart_additions = models.IntegerField(default=0, null=True)
    cart_removals = models.IntegerField(default=0, null=True)
    price = models.DecimalField(default=0.0, null=True, decimal_places=2,
                                max_digits=4)
    orders = models.IntegerField(default=0, null=True)
    unit_orders = models.IntegerField(default=0, null=True)
    objects = SiteCatDataManager()

    class Meta:
        db_table = 'sitecat_product_data'
        unique_together = (("product_id", "date"),)
