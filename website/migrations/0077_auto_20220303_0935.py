# Generated by Django 2.2.7 on 2022-03-03 01:35

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0076_report_report_zoom_level'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='spmonitor',
            name='slide_cartridge',
        ),
        migrations.AddField(
            model_name='spmonitor',
            name='slide_cartridge',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True),
        ),
    ]