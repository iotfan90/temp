# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2018-01-29 18:38
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shopify', '0032_auto_20180126_1728'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='productoptionvalue',
            table='shopify_product_option_value',
        ),
    ]