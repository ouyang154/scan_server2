# Generated by Django 2.2.5 on 2020-10-28 00:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0039_spmonitor_sample_slot'),
    ]

    operations = [
        migrations.AddField(
            model_name='spalert',
            name='read',
            field=models.BooleanField(default=False),
        ),
    ]