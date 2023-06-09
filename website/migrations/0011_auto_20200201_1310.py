# Generated by Django 2.2.5 on 2020-02-01 05:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0010_auto_20200116_1647'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='patient_roomBed',
            field=models.CharField(blank=True, max_length=2000, null=True),
        ),
        migrations.AddField(
            model_name='scan',
            name='patient_roomId',
            field=models.CharField(blank=True, max_length=2000, null=True),
        ),
        migrations.AddField(
            model_name='scan',
            name='patient_roomNum',
            field=models.CharField(blank=True, max_length=2000, null=True),
        ),
        migrations.AddField(
            model_name='scan',
            name='reference_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
