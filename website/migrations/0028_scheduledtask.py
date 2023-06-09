# Generated by Django 2.2.5 on 2020-04-15 07:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0027_auto_20200414_1210'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduledTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_name', models.CharField(blank=True, max_length=200, null=True)),
                ('data_kept_days', models.IntegerField(null=True)),
                ('minute_of_hour', models.IntegerField(null=True)),
                ('hour_of_day', models.IntegerField(null=True)),
                ('disabled', models.BooleanField(default=False)),
                ('run_at', models.DateTimeField(null=True)),
                ('last_success_at', models.DateTimeField(null=True)),
                ('last_fail_at', models.DateTimeField(null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['created'],
            },
        ),
    ]
