# Generated by Django 2.2.5 on 2020-10-31 06:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0040_spalert_read'),
    ]

    operations = [
        migrations.AddField(
            model_name='spsample',
            name='sample_folder',
            field=models.CharField(max_length=2000, null=True),
        ),
    ]
