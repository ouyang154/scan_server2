from django.db import migrations


def forwards_func(apps, schema_editor):
    pass

def reverse_func(apps, schema_editor):
    # destroy what forward_func builds
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('website', '0011_auto_20200201_1310'),
        ('authtoken', '0002_auto_20160226_1747')
    ]
    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]