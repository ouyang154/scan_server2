# Generated by Django 2.2.5 on 2021-03-06 02:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0050_action'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='tile_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='scheduledtask',
            name='keep_results',
            field=models.BooleanField(default=True),
        ),
    ]
