# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-10 05:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lifecycle', '0014_activecartinfofilter2_hasriidfilter_responsys'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filter',
            name='order',
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
    ]