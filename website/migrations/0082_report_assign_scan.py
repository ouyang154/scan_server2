# Generated by Django 2.2.7 on 2022-06-14 01:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0081_report_report_process'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='assign_scan',
            field=models.BooleanField(default=False),
        ),
    ]
