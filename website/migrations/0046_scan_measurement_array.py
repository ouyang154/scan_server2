# Generated by Django 2.2.5 on 2020-11-19 00:59

import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0045_auto_20201119_0842'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='measurement_array',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.jsonb.JSONField(), null=True, size=None),
        ),
    ]
