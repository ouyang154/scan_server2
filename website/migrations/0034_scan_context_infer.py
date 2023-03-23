# Generated by Django 2.2.5 on 2020-07-09 01:44

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0033_scan_diagnosis_info'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='context_infer',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
