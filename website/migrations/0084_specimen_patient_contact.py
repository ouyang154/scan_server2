# Generated by Django 2.2.7 on 2022-07-01 00:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0083_auto_20220623_0950'),
    ]

    operations = [
        migrations.AddField(
            model_name='specimen',
            name='patient_contact',
            field=models.CharField(blank=True, max_length=2000, null=True),
        ),
    ]
