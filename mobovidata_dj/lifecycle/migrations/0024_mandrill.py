# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-04-26 19:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lifecycle', '0023_strandsproductrecsfilter'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mandrill',
            fields=[
                ('sender_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lifecycle.Sender')),
            ],
            options={
                'abstract': False,
            },
            bases=('lifecycle.sender',),
        ),
    ]