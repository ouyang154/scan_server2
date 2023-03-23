import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.db.models import CharField, IntegerField


class SPMonitor(models.Model):
    # 耗材相关
    scheduler = JSONField(blank=False, null=True)
    settling_wheel = JSONField(null=True, blank=False)
    tip_tray = ArrayField(JSONField(), blank=False, null=True)
    tip_deposit = ArrayField(IntegerField(null=True, blank=False), blank=False, null=True)
    filtration = JSONField(blank=False, null=True)
    liquid = JSONField(blank=False, null=True)
    slide_clip = JSONField(blank=False, null=True)
    sample_slot = ArrayField(JSONField(), blank=False, null=True)
    slide_supply = models.BooleanField(default=False)
    slide_charger_grip = models.BooleanField(default=False)
    slide_cartridge = JSONField(null=True, blank=False)
    tris_supply = models.BooleanField(default=False)
    he_supply = models.FloatField(null=True, blank=True)
    ea_supply = models.FloatField(null=True, blank=True)
    ethanol_supply = models.BooleanField(default=False)
    water_supply = models.BooleanField(default=False)
    detergent_supply = models.BooleanField(default=False)
    acrylate_supply = models.FloatField(null=True, blank=True)
    resin_supply = models.FloatField(null=True, blank=True)
    finished_drawer = models.BooleanField(default=False)
    waste_bucket = models.BooleanField(default=False)
    waste_tank = models.BooleanField(default=False)
    vacuum_tank = models.BooleanField(default=False)
    # 设备状态相关
    today_launch_count = models.IntegerField(null=True)
    today_processing_batch = models.IntegerField(null=True)
    last_launch_timestamp = models.DateTimeField(null=True)
    last_offduty_timestamp = models.DateTimeField(null=True)
    last_factory_reset_timestamp = models.DateTimeField(null=True)
    machine_status = models.CharField(null=True, max_length=500, blank=True)
    cleaning_status = models.CharField(null=True, max_length=500, blank=True)
    component_reset = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created']
        db_table = 'sp_monitor'

    def __str__(self):
        return f"sp_monitor-{self.name}-{self.created}"


class SPMachine(models.Model):
    name = models.CharField(null=True, max_length=2000, blank=True)
    hostname = models.CharField(null=True, max_length=500, default='NS')
    ip = models.CharField(null=True, max_length=2000, blank=True)
    mac = models.CharField(null=True, max_length=2000, blank=True)
    comment = models.CharField(null=True, max_length=2000, blank=True)
    monitor = models.OneToOneField(SPMonitor, on_delete=models.PROTECT, default=None, null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created']
        db_table = 'sp_machine'

    def __str__(self):
        return f"sp_machine-{self.name}-{self.ip}"

    def save(self, *args, **kwargs):
        # if creating, create monitor
        if self._state.adding:
            monitor = SPMonitor()
            monitor.save()
            self.monitor_id = monitor.id
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # delete related monitor
        monitor = SPMonitor.objects.get(id = self.monitor_id)
        super().delete(*args, **kwargs)
        monitor.delete()


class SPSample(models.Model):
    barcode_scan = models.CharField(null=True, max_length=2000, blank=True)
    # barcode scan related images
    barcode_img = ArrayField(CharField(null=False, max_length=2000, blank=False), null=True)
    sample_folder = models.CharField(null=True, max_length=2000, blank=False)
    name_print = models.CharField(null=True, max_length=2000, blank=True)
    barcode_print = models.CharField(null=True, max_length=2000, blank=True)
    hostname = models.CharField(null=True, max_length=500, default='NS')
    process_status = models.CharField(null=True, max_length=500, blank=True)
    timestamps = JSONField(null=True, blank=False)
    finish_status = models.CharField(null=True, max_length=500, blank=True)
    start_time = models.DateTimeField(default=datetime.datetime.now)
    finish_time = models.DateTimeField(null=True)

    # reserve related
    reserve_tip = JSONField(null=True, blank=False)
    reserve_filtration = JSONField(null=True, blank=False)
    reserve_wheel = JSONField(null=True, blank=False)
    reserve_slide = JSONField(null=True, blank=False)
    reserve_clip = JSONField(null=True, blank=False)
    reserve_liquid = JSONField(null=True, blank=False)

    # time related
    settling_time = models.FloatField(null=True, blank=False)
    pre_staining_ethanol_time = models.FloatField(null=True, blank=False)
    staining_HE_time = models.FloatField(null=True, blank=False)
    staining_buffer_time = models.FloatField(null=True, blank=False)
    staining_EA_time = models.FloatField(null=True, blank=False)
    post_staining_ethanol_time = models.FloatField(null=True, blank=False)
    # config related
    staining_config = JSONField(null=True, blank=False)

    user = models.ForeignKey(User, on_delete=models.PROTECT, default=None, null=True)
    sp_machine = models.ForeignKey(SPMachine, on_delete=models.PROTECT, default=None, null=True)

    today_launch_count_id = models.IntegerField(null=True)
    today_processing_batch_id = models.IntegerField(null=True)
    last_launch_timestamp = models.DateTimeField(null=True)

    created = models.DateTimeField(default=datetime.datetime.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created']
        db_table = 'sp_sample'

    def __str__(self):
        return f"sp_sample-{self.id}-{self.barcode_print}"

    def save(self, *args, **kwargs):
        # if creating, save hostname
        if self._state.adding:
            self.hostname = settings.HOSTNAME
        super().save(*args, **kwargs)


# log of monitoring values, like: temperature
class SPLog(models.Model):
    value = models.FloatField(null=False, blank=False)
    position = models.CharField(null=False, max_length=2000, blank=False)
    type = models.CharField(null=False, max_length=2000, blank=False)
    sp_machine = models.ForeignKey(SPMachine, on_delete=models.PROTECT, default=None, null=True)

    created = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        ordering = ['created']
        db_table = 'sp_log'

    def __str__(self):
        return f"sp_log-{self.id}-{self.type}-{self.position}-{self.value}"


class SPAlert(models.Model):
    code = models.CharField(null=True, max_length=2000, blank=True)
    brief = models.CharField(null=True, max_length=2000, blank=True)
    description = models.TextField(null=True, blank=True)
    level = models.CharField(null=True, max_length=500, blank=True)
    source = models.CharField(null=True, max_length=500, blank=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, default=None, null=True)
    sp_machine = models.ForeignKey(SPMachine, on_delete=models.PROTECT, default=None, null=True)
    related_sample = ArrayField(IntegerField(null=False, blank=False), null=True)
    read = models.BooleanField(default=False)

    today_launch_count_id = models.IntegerField(null=True)
    today_processing_batch_id = models.IntegerField(null=True)
    last_launch_timestamp = models.DateTimeField(null=True)

    created = models.DateTimeField(default=datetime.datetime.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created']
        db_table = 'sp_alert'

    def __str__(self):
        return f"sp_alert-{self.id}-{self.brief}"
