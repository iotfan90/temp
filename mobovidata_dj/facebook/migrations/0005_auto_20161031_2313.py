# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-11-01 06:13
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('facebook', '0004_auto_20161012_1229'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='adstatwindow',
            name='adset_id',
        ),
        migrations.RemoveField(
            model_name='adstatwindow',
            name='campaign_id',
        ),
    ]