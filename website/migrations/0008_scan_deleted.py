# Generated by Django 2.2.5 on 2019-12-31 03:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0007_auto_20191219_1135'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='deleted',
            field=models.BooleanField(default=False),
        ),
    ]
