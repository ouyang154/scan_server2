# Generated by Django 2.2.5 on 2020-04-14 04:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0026_auto_20200410_1920'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='nucleus_count',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='scan',
            name='specimen_qualified',
            field=models.BooleanField(null=True),
        ),
    ]