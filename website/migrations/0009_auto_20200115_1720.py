# Generated by Django 2.2.5 on 2020-01-15 09:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0008_scan_deleted'),
    ]

    operations = [
        migrations.RenameField(
            model_name='scan',
            old_name='scan_path',
            new_name='exam_folder',
        ),
    ]
