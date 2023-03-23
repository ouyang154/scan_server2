from django.db import migrations

def forwards_func(apps, schema_editor):
    # create report with name jz
    pass

def reverse_func(apps, schema_editor):
    # destroy what forward_func builds
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('website', '0071_report_sp_barcode_hospital_name')
    ]
    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
