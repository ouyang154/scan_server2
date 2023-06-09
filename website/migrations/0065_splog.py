# Generated by Django 2.2.5 on 2021-06-17 01:42

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0064_spsample_staining_config'),
    ]

    operations = [
        migrations.CreateModel(
            name='SPLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField()),
                ('position', models.CharField(max_length=2000)),
                ('type', models.CharField(max_length=2000)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
            ],
            options={
                'db_table': 'sp_log',
                'ordering': ['created'],
            },
        ),
    ]
