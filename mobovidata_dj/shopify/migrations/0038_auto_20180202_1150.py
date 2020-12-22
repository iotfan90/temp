# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2018-02-02 19:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shopify', '0037_auto_20180201_1309'),
    ]

    operations = [
        migrations.CreateModel(
            name='MasterAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attribute_code', models.CharField(blank=True, db_index=True, max_length=255, null=True, unique=True)),
                ('attribute_id', models.SmallIntegerField(db_index=True, unique=True)),
                ('attribute_model', models.CharField(blank=True, max_length=255, null=True)),
                ('backend_model', models.CharField(blank=True, max_length=255, null=True)),
                ('backend_table', models.CharField(blank=True, max_length=255, null=True)),
                ('backend_type', models.CharField(max_length=8)),
                ('default_value', models.TextField(blank=True, null=True)),
                ('entity_type_id', models.SmallIntegerField()),
                ('frontend_class', models.CharField(blank=True, max_length=255, null=True)),
                ('frontend_input', models.CharField(blank=True, max_length=50, null=True)),
                ('frontend_label', models.CharField(blank=True, max_length=255, null=True)),
                ('frontend_model', models.CharField(blank=True, max_length=255, null=True)),
                ('is_required', models.BooleanField()),
                ('is_unique', models.BooleanField()),
                ('is_user_defined', models.BooleanField()),
                ('note', models.CharField(blank=True, max_length=255, null=True)),
                ('source_model', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'shopify_master_attribute',
            },
        ),
        migrations.CreateModel(
            name='MasterAttributeSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attribute_set_id', models.SmallIntegerField(db_index=True, unique=True)),
                ('attribute_set_name', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'shopify_master_attribute_set',
            },
        ),
        migrations.RenameField(
            model_name='masterattributemapping',
            old_name='attribute_set_id',
            new_name='attribute_set_id_old',
        ),
        migrations.RenameField(
            model_name='masterproduct',
            old_name='attribute_set_id',
            new_name='attribute_set_id_old',
        ),
        migrations.AddField(
            model_name='masterattributemapping',
            name='attribute',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='shopify.MasterAttribute'),
        ),
        migrations.AddField(
            model_name='masterattributemapping',
            name='attribute_set',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='shopify.MasterAttributeSet'),
        ),
        migrations.AddField(
            model_name='masterattributevalue',
            name='attribute',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='shopify.MasterAttribute'),
        ),
        migrations.AddField(
            model_name='masterproduct',
            name='attribute_set',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='shopify.MasterAttributeSet'),
        ),
    ]