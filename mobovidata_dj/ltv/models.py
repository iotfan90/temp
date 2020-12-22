from __future__ import unicode_literals

from django.db import models


class CustomerId(models.Model):
    email = models.EmailField(db_index=True, unique=True)
    md5 = models.CharField(db_index=True, max_length=32)
    first_order_id = models.IntegerField(unique=True, db_index=True)
    first_order_dt = models.DateTimeField()
    num_orders = models.IntegerField()

    class Meta:
        db_table = 'customer_id'


class CustomerIdOrderId(models.Model):
    order_id = models.IntegerField(primary_key=True, db_index=True)
    order_grand_total = models.DecimalField(decimal_places=2, max_digits=12)
    customer = models.ForeignKey(CustomerId)
    created_at = models.DateTimeField()
    repeat_customer = models.IntegerField()

    class Meta:
        db_table = 'customer_id_order_id'
