import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


# deprected, 用户自定义条目，没有业务设计
class UserDefined(models.Model):
    name = models.CharField(max_length=2000, primary_key=True)
    content = JSONField(null=True, blank=True)
    included = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return f"user_defined-{self.name}-content:{self.content}-included:{self.included}"


class ScheduledTask(models.Model):
    task_name = models.CharField(null=True, max_length=200, blank=True)
    data_kept_days = models.IntegerField(null=True)
    keep_results = models.BooleanField(default=True)  # 保留结果数据,只删除tile数据
    minute_of_hour = models.IntegerField(null=True, default=0)
    hour_of_day = models.IntegerField(null=True, default=0)

    disabled = models.BooleanField(default=True)
    run_at = models.DateTimeField(null=True, default=datetime.datetime.now)
    last_success_at = models.DateTimeField(null=True)
    last_fail_at = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return f"scheduled_task-{self.task_name}-disabled:{self.disabled}"


# deprecated, 被specimen替代
class Patient(models.Model):
    # patient info
    name = models.CharField(null=True, max_length=2000, blank=True)
    age = models.IntegerField(null=True, blank=True)
    birth = models.CharField(null=True, max_length=2000, blank=True)
    gender = models.IntegerField(null=True, blank=True)
    patient_id = models.CharField(null=True, max_length=2000, blank=True)
    patient_roomNum = models.CharField(null=True, max_length=2000, blank=True)
    patient_roomBed = models.CharField(null=True, max_length=2000, blank=True)
    patient_roomId = models.CharField(null=True, max_length=2000, blank=True)
    patient_phone = models.CharField(null=True, max_length=2000, blank=True)
    menses = models.CharField(null=True, max_length=2000, blank=True)
    menses_date = models.CharField(null=True, max_length=2000, blank=True)
    # specimen
    specimen_id = models.CharField(null=True, max_length=2000, blank=True)
    specimen_date = models.CharField(null=True, max_length=2000, blank=True)
    reference_date = models.CharField(null=True, max_length=2000, blank=True)
    reference_hospital = models.CharField(null=True, max_length=2000, blank=True)
    reference_department = models.CharField(null=True, max_length=2000, blank=True)
    reference_doctor = models.CharField(null=True, max_length=2000, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return f"patient-{self.name}-{self.created}"

# deprecated? LIS，医生信息，没有业务设计
class Doctor(models.Model):
    # patient info
    name = models.CharField(null=True, max_length=2000, blank=True)
    department = models.CharField(null=True, max_length=2000, blank=True)
    doctor_id = models.CharField(null=True, max_length=2000, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return f"doctor-{self.name}-{self.created}"


# deprecated? LIS，部门信息，没有业务设计
class Department(models.Model):
    # patient info
    name = models.CharField(null=True, max_length=2000, blank=True)
    department_id = models.CharField(null=True, max_length=2000, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return f"department-{self.name}-{self.created}"


class Specimen(models.Model):

    specimen_id = models.CharField(null=True, max_length=2000, blank=True)
    specimen_date = models.CharField(null=True, max_length=2000, blank=True)
    specimen_type = models.CharField(null=True, max_length=2000, blank=True)
    reference_date = models.CharField(null=True, max_length=2000, blank=True)
    reference_hospital = models.CharField(null=True, max_length=2000, blank=True)
    reference_department = models.CharField(null=True, max_length=2000, blank=True)
    reference_doctor = models.CharField(null=True, max_length=2000, blank=True)
    reference_specimen = models.CharField(null=True, max_length=2000, blank=True)

    # patient info
    name = models.CharField(null=True, max_length=2000, blank=True)
    age = models.IntegerField(null=True, blank=True)
    birth = models.CharField(null=True, max_length=2000, blank=True)
    gender = models.IntegerField(null=True, blank=True)
    patient_id = models.CharField(null=True, max_length=2000, blank=True)
    patient_roomNum = models.CharField(null=True, max_length=2000, blank=True)
    patient_roomBed = models.CharField(null=True, max_length=2000, blank=True)
    patient_roomId = models.CharField(null=True, max_length=2000, blank=True)
    patient_phone = models.CharField(null=True, max_length=2000, blank=True)
    patient_contact = models.CharField(null=True, max_length=2000, blank=True)
    menses = models.CharField(null=True, max_length=2000, blank=True)
    menses_date = models.CharField(null=True, max_length=2000, blank=True)
    # examine info
    examine_id = models.CharField(null=True, max_length=2000, blank=True)
    physical_examination_id = models.CharField(null=True, max_length=2000, blank=True)
    examine_type = models.CharField(null=True, max_length=2000, blank=True)
    outpatient_id = models.CharField(null=True, max_length=2000, blank=True)
    inpatient_id = models.CharField(null=True, max_length=2000, blank=True)
    inpatient_area = models.CharField(null=True, max_length=2000, blank=True)
    inpatient_bed = models.CharField(null=True, max_length=2000, blank=True)
    invoice = models.CharField(null=True, max_length=2000, blank=True)
    marriage_status = models.BooleanField(null=True)
    specimen_receiver = models.CharField(null=True, max_length=2000, blank=True)
    charge = models.FloatField(null=True, blank=True)
    clinical_diagnosis = models.CharField(null=True, max_length=2000, blank=True)
    surgery_observation = models.CharField(null=True, max_length=2000, blank=True)
    clinical_history = models.CharField(null=True, max_length=2000, blank=True)

    created = models.DateTimeField(default=datetime.datetime.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return f"specimen-{self.id}-{self.name}"


class Scan(models.Model):
    # specimen info
    specimen_info = models.ForeignKey(Specimen, on_delete=models.PROTECT, default=None, null=True)
    # review info, verifier-提交报告人，author-初审人，approver-复审人
    verifier = models.CharField(null=True, max_length=2000, blank=True)
    author = models.CharField(null=True, max_length=2000, blank=True)
    authoring_date = models.DateTimeField(null=True)  # 初审时间
    approver = models.CharField(null=True, max_length=2000, blank=True)
    approving_date = models.DateTimeField(null=True)  # 复审时间
    # scan info
    scan_folder = models.CharField(null=True, max_length=2000, blank=True)
    technician = models.CharField(null=True, max_length=2000, blank=True)
    multi_focus = models.IntegerField(null=True, blank=True)
    scan_date = models.DateField(null=True, blank=True, default=datetime.date.today)
    scout_log = JSONField(null=True, blank=True)
    scan_log = JSONField(null=True, blank=True)
    # diagnosis
    diagnosisValue = JSONField(null=True, blank=True)
    diagnosis_info = models.TextField(null=True, blank=True)
    suggestion1 = models.CharField(null=True, max_length=2000, blank=True)
    suggestion2 = models.CharField(null=True, max_length=2000, blank=True)
    det_log = JSONField(null=True, blank=True) # save raw model output
    post_process_log = JSONField(null=True, blank=True) # save post process log
    
    # AI
    # detection inference results
    detection_info = JSONField(null=True)
    # bbox pic. cutting. 0-not ready 1-generating 2-ready, -1-not able to generate bbox locally
    bbox_ready = models.IntegerField(null=False, default=0)
    # context inference
    context_infer = JSONField(null=True)
    # measurement tool
    measurement_array = ArrayField(JSONField(), blank=False, null=True)
    # for list page display
    AIdiagnosis = models.IntegerField(null=True, blank=True)
    AIgrade = models.CharField(null=True, max_length=2000, blank=True)
    AIscore = models.FloatField(null=True, blank=True)
    AIinformation = models.CharField(null=True, max_length=2000, blank=True)
    specimen_qualified = models.BooleanField(null=True)
    nucleus_count = models.IntegerField(null=True, blank=True)
    micro_flag = models.BooleanField(default=False)  # for microorganism
    micro_type = ArrayField(models.CharField(max_length=200), blank=True, null=True)
    # keep scan not to disable and delete
    reserved_flag = models.BooleanField(null=True, default=False)
    # backup flag, 0-not to backup, 1-to be backup, 2-in backup folder, 3-backuped and deleted, -1-unable to backup
    backup_flag = models.IntegerField(null=True, default=0)
    backup_folder = models.CharField(null=True, max_length=2000)
    backup_tag = models.CharField(null=True, max_length=200)

    status = models.CharField(null=True, default='scan', max_length=200, blank=True)
    priority = models.IntegerField(default=0, null=True, blank=True)
    # 占有人，正在审核
    occupied_by = models.ForeignKey(User, related_name='occupied_by_user', on_delete=models.PROTECT, default=None, null=True)
    # 被分配人
    owner = models.ForeignKey(User, to_field='username', db_column="owner", on_delete=models.PROTECT, default=None, null=True)
    created = models.DateTimeField(default=datetime.datetime.now)
    updated = models.DateTimeField(auto_now=True)

    # data related
    # where data is stored, NS for not specified
    hostname = models.CharField(null=True, max_length=500, default='NS')
    # hide from frontend
    disabled = models.BooleanField(default=False)
    # to be deleted
    to_be_deleted = models.BooleanField(default=False)    
    # if fully deleted
    deleted = models.BooleanField(default=False)
    # if tiles/pyramid deleted
    tile_deleted = models.BooleanField(default=False)

    # deprecated
    bbox_array = ArrayField(JSONField(), blank=True, null=True)
    h_bbox_array = ArrayField(JSONField(), blank=True, null=True)
    l_bbox_array = ArrayField(JSONField(), blank=True, null=True)
    agc_bbox_array = ArrayField(JSONField(), blank=True, null=True)
    p_bbox_array = ArrayField(JSONField(), blank=True, null=True)
    t_bbox_array = ArrayField(JSONField(), blank=True, null=True)
    m_bbox_array = ArrayField(JSONField(), blank=True, null=True)
    i_bbox_array = ArrayField(JSONField(), blank=True, null=True)
    lep_bbox_array = ArrayField(JSONField(), blank=True, null=True)
    actinomyces_bbox_array = ArrayField(JSONField(), blank=True, null=True)
    herpes_bbox_array = ArrayField(JSONField(), blank=True, null=True)
    report_bbox_array = ArrayField(JSONField(), blank=True, null=True)

    # deprecated
    # patient info
    name = models.CharField(null=True, max_length=2000, blank=True)
    age = models.IntegerField(null=True, blank=True)
    birth = models.CharField(null=True, max_length=2000, blank=True)
    gender = models.IntegerField(null=True, blank=True)
    patient_id = models.CharField(null=True, max_length=2000, blank=True)
    patient_roomNum = models.CharField(null=True, max_length=2000, blank=True)
    patient_roomBed = models.CharField(null=True, max_length=2000, blank=True)
    patient_roomId = models.CharField(null=True, max_length=2000, blank=True)
    patient_phone = models.CharField(null=True, max_length=2000, blank=True)
    menses = models.CharField(null=True, max_length=2000, blank=True)
    menses_date = models.CharField(null=True, max_length=2000, blank=True)
    # specimen
    specimen_id = models.CharField(null=True, max_length=2000, blank=True)
    specimen_date = models.CharField(null=True, max_length=2000, blank=True)
    specimen_type = models.CharField(null=True, max_length=2000, blank=True)
    reference_date = models.CharField(null=True, max_length=2000, blank=True)
    reference_hospital = models.CharField(null=True, max_length=2000, blank=True)
    reference_department = models.CharField(null=True, max_length=2000, blank=True)
    reference_doctor = models.CharField(null=True, max_length=2000, blank=True)
    # upload to cloud, 0-not to upload, 1-to be upload, 2-uploaded
    upload_flag = models.IntegerField(null=True, default=0)
    
    class Meta:
        ordering = ['created']

    def __str__(self):
        return f"scan-{self.name}-{self.created}"


class Physician(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # roles
    admin = models.BooleanField(default=False)
    edit = models.BooleanField(default=False)
    review = models.BooleanField(default=False)
    submit = models.BooleanField(default=False)
    operator = models.BooleanField(default=False)

    def __str__(self):
        return f'Physician id:{self.user_id}'


@receiver(post_delete, sender=Physician)
def delete_user(sender, instance, using, **kwargs):
    return User.objects.get(id=instance.user_id).delete()


# hospital and report info
class Report(models.Model):
    # scan report related
    name = models.CharField(null=True, max_length=2000, blank=True)
    hospital_logo = models.CharField(null=True, max_length=100, blank=False)
    address = models.CharField(null=True, max_length=2000, blank=True)
    telephone = models.CharField(null=True, max_length=2000, blank=True)
    poster_code = models.CharField(null=True, max_length=2000, blank=True)
    pathology_tel = models.CharField(null=True, max_length=2000, blank=True)
    consult_sel = models.CharField(null=True, max_length=2000, blank=True)
    internet_url = models.CharField(null=True, max_length=2000, blank=True)
    report_model = models.CharField(null=True, max_length=2000, blank=True)
    satisfaction_nucleus_count = models.IntegerField(null=True)
    report_zoom_level = models.IntegerField(null=True)
    # 一二级审核设置
    report_process = models.CharField(null=False, max_length=200, default='one_level')
    # 分配任务功能设置
    assign_scan = models.BooleanField(default=False)

    # sp related
    sp_barcode_hospital_name = models.CharField(max_length=2000, null=True)

    # deprecated. use json file scan_server_report_config
    report_config = JSONField(null=True, blank=True)


    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return f"report-template-{self.name}-{self.id}"


class Microscope(models.Model):
    equip_id = models.CharField(null=True, max_length=2000, blank=True)
    ip = models.CharField(null=True, max_length=2000, blank=True)
    mac = models.CharField(null=True, max_length=2000, blank=True)
    manager = models.CharField(null=True, max_length=2000, blank=True)
    room = models.CharField(null=True, max_length=2000, blank=True)
    offsetX = models.FloatField(null=True, blank=True)
    offsetY = models.FloatField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return f"microscope-{self.ip}-{self.mac}"


# rest-framework token auto generation
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
