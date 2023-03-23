# Generated by Django 2.2.5 on 2021-06-17 01:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0065_splog'),
    ]

    operations = [
        migrations.AddField(
            model_name='splog',
            name='sp_machine',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='website.SPMachine'),
        ),
    ]