# Generated by Django 2.2.5 on 2021-05-19 03:44

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0061_spmonitor_liquid'),
    ]

    operations = [
        migrations.AddField(
            model_name='spmonitor',
            name='slide_clip',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True),
        ),
    ]
