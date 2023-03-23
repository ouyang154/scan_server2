# Generated by Django 2.2.5 on 2020-09-17 12:33

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0035_auto_20200717_1548'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='bbox_ready',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='scan',
            name='detection_info',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True),
        ),
        migrations.AddField(
            model_name='scan',
            name='hostname',
            field=models.CharField(default='NS', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='scan',
            name='context_infer',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True),
        ),
    ]