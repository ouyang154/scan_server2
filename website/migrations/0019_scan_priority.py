# Generated by Django 2.2.5 on 2020-03-30 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0018_scan_aiscore'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='priority',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]