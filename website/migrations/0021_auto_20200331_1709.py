# Generated by Django 2.2.5 on 2020-03-31 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0020_auto_20200330_1508'),
    ]

    operations = [
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=2000, null=True)),
                ('age', models.IntegerField(blank=True, null=True)),
                ('birth', models.CharField(blank=True, max_length=2000, null=True)),
                ('gender', models.IntegerField(blank=True, null=True)),
                ('patient_id', models.CharField(blank=True, max_length=2000, null=True)),
                ('patient_roomNum', models.CharField(blank=True, max_length=2000, null=True)),
                ('patient_roomBed', models.CharField(blank=True, max_length=2000, null=True)),
                ('patient_roomId', models.CharField(blank=True, max_length=2000, null=True)),
                ('patient_phone', models.CharField(blank=True, max_length=2000, null=True)),
                ('menses', models.IntegerField(blank=True, null=True)),
                ('menses_date', models.CharField(blank=True, max_length=2000, null=True)),
                ('specimen_id', models.CharField(blank=True, max_length=2000, null=True)),
                ('specimen_date', models.CharField(blank=True, max_length=2000, null=True)),
                ('reference_date', models.CharField(blank=True, max_length=2000, null=True)),
                ('reference_hospital', models.CharField(blank=True, max_length=2000, null=True)),
                ('reference_department', models.CharField(blank=True, max_length=2000, null=True)),
                ('reference_doctor', models.CharField(blank=True, max_length=2000, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['created'],
            },
        ),
        migrations.AlterField(
            model_name='scan',
            name='reference_date',
            field=models.CharField(blank=True, max_length=2000, null=True),
        ),
    ]