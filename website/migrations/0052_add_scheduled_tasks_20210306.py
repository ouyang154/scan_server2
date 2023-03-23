from django.db import migrations
from django.utils import timezone

from website.models import ScheduledTask


def forwards_func(apps, schema_editor):
    # moved from #30
    try:
        ScheduledTask.objects.get(task_name='backup_negative_scans')
    except ScheduledTask.DoesNotExist:
        # add backup_negative_scans
        ScheduledTask.objects.create(task_name='backup_negative_scans', data_kept_days=7, minute_of_hour=0, hour_of_day=3, disabled=True, run_at=timezone.now())

    try:
        ScheduledTask.objects.get(task_name='delete_negative_scans')
    except ScheduledTask.DoesNotExist:
        # add delete_negative_scans
        ScheduledTask.objects.create(task_name='delete_negative_scans', data_kept_days=7, minute_of_hour=0, hour_of_day=4, disabled=True, run_at=timezone.now())

    try:
        ScheduledTask.objects.get(task_name='backup_positive_scans')
    except ScheduledTask.DoesNotExist:
        # add backup_positive_scans
        ScheduledTask.objects.create(task_name='backup_positive_scans', data_kept_days=30, minute_of_hour=0, hour_of_day=2, disabled=True, run_at=timezone.now())

    try:
        ScheduledTask.objects.get(task_name='autoupload')
    except ScheduledTask.DoesNotExist:
        # add autoupload
        ScheduledTask.objects.create(task_name='autoupload', data_kept_days=0, minute_of_hour=0, hour_of_day=1, disabled=True, run_at=timezone.now())

    # init scheduled tasks here
    try:
        ScheduledTask.objects.get(task_name='delete_positive_scans')
        print('here')
    except ScheduledTask.DoesNotExist:
        # add delete_negative_scans
        print('there')
        ScheduledTask.objects.create(task_name='delete_positive_scans', data_kept_days=30, keep_results=True,
                                     minute_of_hour=0, hour_of_day=4, disabled=True, run_at=timezone.now())

def reverse_func(apps, schema_editor):
    # destroy what forward_func builds
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('website', '0051_auto_20210306_1033'),
    ]
    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
