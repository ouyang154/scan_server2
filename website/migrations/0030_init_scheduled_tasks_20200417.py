from django.db import migrations
from django.utils import timezone

from website.models import ScheduledTask


def forwards_func(apps, schema_editor):
    # init scheduled tasks here, move to #52
    pass


def reverse_func(apps, schema_editor):
    # destroy what forward_func builds
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('website', '0029_scan_upload_flag'),
    ]
    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
