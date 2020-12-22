from django.db import models


class DailyAvgWeights(models.Model):
    """
    Define fields for each weight in different days
    """
    day_1 = models.FloatField()
    day_3 = models.FloatField()
    day_7 = models.FloatField()
    day_14 = models.FloatField()
    day_30 = models.FloatField()
    day_90 = models.FloatField()


class ProductQuarantine(models.Model):
    """
    A table of quarantine process, can be updated by csv files uploaded
    """
    product_id = models.IntegerField()
    sku = models.CharField(max_length=255, blank=True, null=True)
    pre_quarantine_price = models.DecimalField(max_digits=12, decimal_places=4,
                                               blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=4,
                                        blank=True, null=True)
    quarantine_level = models.CharField(max_length=128)
    quarantine_level_updated_at = models.DateTimeField(blank=True)

    def __init__(self, *args, **kwargs):
        super(ProductQuarantine, self).__init__(*args, **kwargs)
        self.__original_current_price = self.current_price
        self.__original_quarantine_level_updated_at = self.quarantine_level_updated_at
        self.__original_pre_quarantine_price = self.pre_quarantine_price

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if abs(self.current_price - self.__original_current_price) < 1e-4:
            self.quarantine_level_updated_at = self.__original_quarantine_level_updated_at
        self.pre_quarantine_price = self.__original_pre_quarantine_price
        super(ProductQuarantine, self).save(force_insert, force_update, *args,
                                            **kwargs)


class AgingInventory(models.Model):
    """
    Sku level for sales report
    """
    product_id = models.IntegerField(blank=True, null=True)
    sku = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    brand_model = models.CharField(max_length=255, blank=True, null=True)
    qty = models.DecimalField(max_digits=12, decimal_places=4, blank=True,
                              null=True)
    is_in_stock = models.IntegerField(blank=True, null=True)
    back_orders = models.IntegerField(blank=True, null=True)
    base_cost = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    margin = models.CharField(max_length=128, blank=True)
    image = models.TextField(blank=True, null=True)
    vendor_sku = models.TextField(blank=True, null=True)
    vendor_name = models.TextField(blank=True, null=True)
    attribute_set = models.CharField(max_length=128, blank=True, null=True)
    category = models.CharField(max_length=128, blank=True, null=True)
    day_1 = models.DecimalField(max_digits=12, decimal_places=4, blank=True,
                                null=True)
    day_3 = models.DecimalField(max_digits=12, decimal_places=4, blank=True,
                                null=True)
    day_7 = models.DecimalField(max_digits=12, decimal_places=4, blank=True,
                                null=True)
    day_14 = models.DecimalField(max_digits=12, decimal_places=4, blank=True,
                                 null=True)
    day_30 = models.DecimalField(max_digits=12, decimal_places=4, blank=True,
                                 null=True)
    day_90 = models.DecimalField(max_digits=12, decimal_places=4, blank=True,
                                 null=True)
    po_day1_avg = models.DecimalField(max_digits=12, decimal_places=4,
                                      blank=True, null=True)
    po_day3_avg = models.DecimalField(max_digits=12, decimal_places=4,
                                      blank=True, null=True)
    po_day7_avg = models.DecimalField(max_digits=12, decimal_places=4,
                                      blank=True, null=True)
    po_day14_avg = models.DecimalField(max_digits=12, decimal_places=4,
                                       blank=True, null=True)
    po_day30_avg = models.DecimalField(max_digits=12, decimal_places=4,
                                       blank=True, null=True)
    po_day90_avg = models.DecimalField(max_digits=12, decimal_places=4,
                                       blank=True, null=True)
    po_run_rate = models.DecimalField(max_digits=12, decimal_places=4,
                                      blank=True, null=True)
    forecast_daily_demand = models.DecimalField(max_digits=12, decimal_places=4,
                                                blank=True, null=True)
    inventory_days_remain = models.DecimalField(max_digits=12, decimal_places=4,
                                                blank=True, null=True)
    pending_po_id = models.TextField(blank=True, null=True)
    pending_po_qty = models.TextField(blank=True, null=True)
    pending_po_date = models.TextField(blank=True, null=True)
    pending_po_len = models.TextField(blank=True, null=True)
    last_received_date = models.DateTimeField(blank=True, null=True)
    last_received_qty = models.DecimalField(max_digits=12, decimal_places=4,
                                            blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
