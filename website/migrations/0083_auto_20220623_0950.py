# Generated by Django 2.2.7 on 2022-06-23 01:50

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0082_report_assign_scan'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='det_log',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='scan',
            name='post_process_log',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
