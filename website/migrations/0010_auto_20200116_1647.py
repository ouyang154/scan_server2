# Generated by Django 2.2.5 on 2020-01-16 08:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0009_auto_20200115_1720'),
    ]

    operations = [
        migrations.RenameField(
            model_name='scan',
            old_name='exam_folder',
            new_name='scan_folder',
        ),
    ]
