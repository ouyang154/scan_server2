# Generated by Django 2.2.5 on 2020-04-21 02:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0030_init_scheduled_tasks_20200417'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='reserved_flag',
            field=models.BooleanField(default=False, null=True),
        ),
    ]
