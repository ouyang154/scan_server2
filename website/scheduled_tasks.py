import datetime
import logging
import os
import traceback
from itertools import islice

import oss2
import requests
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import make_aware
from redis import StrictRedis

from website.models import ScheduledTask, Scan, Report
from website.utils import hard_delete_scan, rm_folder, generate_bbox_scan, delete_tile_folder, get_pid_by_name, update_to_be_delete_scan, handle_backup_scan, get_checkbox_node_by_key
from django_redis import get_redis_connection

logger = logging.getLogger('django.scheduled_task')


def upload_file(bucket, oss_path, ori_parent, file_name, dst_path):
    ori_path = os.path.join(ori_parent, file_name)
    remote_name = oss_path + dst_path + '/{}'.format(file_name)
    # logger.debug('uploading..{} to remote {}'.format(ori_path, remote_name))
    result = bucket.put_object_from_file(remote_name, ori_path)
    # logger.debug('http status: {0}'.format(result.status))


def upload_backup_folder(bucket, oss_path, backup_path, dst_path):
    for file_name in os.listdir(backup_path):
        path = os.path.join(backup_path, file_name)
        if os.path.islink(path):
            path = os.readlink(path)
        if os.path.isdir(path):
            # is folder
            upload_backup_folder(bucket, oss_path, path,
                                 dst_path+'/{}'.format(file_name))
        else:
            # is file
            upload_file(bucket, oss_path, backup_path, file_name, dst_path)


def update_task_success(task):
    # update next run, next day
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    time_of_day = datetime.time(
        hour=task.hour_of_day, minute=task.minute_of_hour)
    run_at = datetime.datetime.combine(tomorrow, time_of_day)
    aware_datetime = make_aware(run_at)
    task.run_at = aware_datetime
    task.last_success_at = timezone.now()
    task.save()


def update_task_fail(task):
    task.last_fail_at = timezone.now()
    task.save()


# deprecated
def delete_backup_scans(task_name):
    logger.debug(
        "starting delete_backup_scans task at {}".format(timezone.now()))
    try:
        task = ScheduledTask.objects.get(task_name=task_name)
    except ScheduledTask.DoesNotExist:
        task = None
    if not task or task.disabled:
        logger.debug("task {} disabled, {}, so skip".format(task_name, task))
        return
    try:
        now = timezone.now()
        run_at = task.run_at
        if not run_at or now >= run_at:
            backup_scan_list = os.listdir(settings.SCAN_BACKUP)
            logger.debug("delete backup scans job starting, total scans:{}".format(
                len(backup_scan_list)))
            for scan_folder in backup_scan_list:
                if len(get_pid_by_name('scan_app')) > 0:
                    logger.info(
                        'scan_app is running, so skip delete_backup_scans and wait!')
                    return
                scan_full_path = os.path.join(
                    settings.SCAN_BACKUP, scan_folder)
                rm_folder(scan_full_path)
            # update next run, next day
            update_task_success(task)
    except Exception as e:
        logger.debug(
            "delete backup scans job fail at {}".format(timezone.now()))
        traceback.print_exc()
        update_task_fail(task)
    logger.debug('delete_scans task finished')


# handle to be deleted scans, this task can not be configured
def handle_to_be_deleted_scans(task_name='handle_to_be_deleted_scans'):
    logger.debug(
        "starting handle_to_be_deleted_scans task at {}".format(timezone.now()))
    task = ScheduledTask.objects.get_or_create(task_name=task_name)[0]
    try:
        # get all to be deleted scans
        scans = Scan.objects.filter(
            to_be_deleted=True, deleted=False, reserved_flag=False)
        logger.info("total to_be_deleted scans:{}".format(len(scans)))
        for scan in scans:
            # if scan is running skip task
            if len(get_pid_by_name('scan_app')) > 0:
                logger.info(
                    'scan_app is running, so skip handle_to_be_deleted_scans and wait!')
                update_task_fail(task)
                return
            # handle fn pn scans, if backup_flag == 2, move origin file to backup folder
            if scan.backup_flag == 1 or scan.backup_flag == 2:
                handle_backup_scan(scan, move_origin_file=True)
            # delete exam folder
            hard_delete_scan(scan)
        update_task_success(task)
    except Exception as e:
        logger.debug(
            "handle_to_be_deleted_scans job fail at {}".format(timezone.now()))
        traceback.print_exc()
        update_task_fail(task)
    logger.debug('handle_to_be_deleted_scans task finished')


# autoupload backup scans to oss
def autoupload_scans(task_name):
    logger.info("start {} task at {}".format(task_name, timezone.now()))
    task = ScheduledTask.objects.get_or_create(task_name=task_name)[0]
    if not task or task.disabled:
        logger.info("task {} disabled, {}, so skip".format(task_name, task))
        return

    try:
        report = Report.objects.all().order_by('id').first()
        hospital_name = report.name
    except Report.DoesNotExist:
        hospital_name = 'NotSpecified'
    # repeat running task
    try:
        auth = oss2.AnonymousAuth()
        bucket = oss2.Bucket(auth, settings.REGION_URL, settings.OSS_BUCKET)

        # test connection by sending one request, disable test no right to do action except put
        # bucket.object_exists(settings.AUTOUPLOAD_PATH + '/')

        while(True):
            # if scan app is running skip task
            if len(get_pid_by_name('scan_app')) > 0:
                logger.warn(
                    'scan_app is running, so skip autoupload_scans and wait!')
                update_task_fail(task)
                return

            # get one upload task
            scan = None
            # get task in fp fn tp order
            for backup_tag in settings.SCAN_BACKUP_TAG:
                if backup_tag == 'not_recognized':
                    # 上传完fp,fn,tp后剩下的tag
                    scans = list(Scan.objects.filter(backup_flag=2))
                else:
                    scans = list(Scan.objects.filter(
                        backup_flag=2, backup_tag=backup_tag))
                if len(scans) > 0:
                    logger.info("got autoupload_scans({}):{}, get one task to upload".format(
                        backup_tag, len(scans)))
                    scan = scans[0]
                    break
            if not scan:
                logger.info("No autoupload_scans task found, so finish task.")
                break
            # upload 1 scan to oss
            logger.info("start autoupload scan:{}".format(scan.id))
            backup_folder = os.path.join(
                settings.SCAN_BACKUP, scan.backup_folder)
            backup_tag = scan.backup_folder.split('/')[0]
            backup_scan_folder = scan.backup_folder.split('/')[1]
            autoupload_folder = '/{}/{}-{}'.format(
                backup_tag, hospital_name, backup_scan_folder)
            try:
                upload_backup_folder(
                    bucket, settings.AUTOUPLOAD_PATH, backup_folder, autoupload_folder)
            except FileNotFoundError:
                logger.error(
                    "backup file not found! just skip this backup task...")
                scan.backup_flag = -1
                scan.backup_folder = None
                scan.save(update_fields=['backup_flag', 'backup_folder'])
                rm_folder(backup_folder)
                continue
            bucket.put_object(settings.AUTOUPLOAD_PATH +
                              '{}/finish_flag.log'.format(autoupload_folder), 'finish upload!')
            scan.backup_flag = 3
            scan.backup_folder = None
            scan.save(update_fields=['backup_flag', 'backup_folder'])
            rm_folder(backup_folder)
            logger.info("finish autoupload scan:{}".format(scan.id))
        update_task_success(task)
    except Exception:
        traceback.print_exc()
        logger.error("oss connection failed at {}, skip upload task and try later...".format(
            timezone.now()))
        update_task_fail(task)
    logger.info("finish autoupload exam task at {}".format(timezone.now()))


# backup fp/fn
def backup_scans(task_name='backup_scans'):
    logger.info("starting backup_scans task at {}".format(timezone.now()))
    task = ScheduledTask.objects.get_or_create(task_name=task_name)[0]
    try:
        # 通过report结果，update backup_flag, find fp/fn scans
        scans = Scan.objects.filter(status__in=['approved', 'printing', 'printed'],
                                    detection_info__isnull=False,
                                    diagnosisValue__isnull=False,
                                    backup_flag=0, deleted=False, tile_deleted=False)
        for scan in scans:
            # get report NILM result
            try:
                node = get_checkbox_node_by_key(
                    scan.diagnosisValue['checkbox'], settings.SCAN_BACKUP_NILM_KEY)
            except Exception:
                # could not get result
                logger.error(
                    'could not get report diagnosisValue NILM checkbox value! scan id:{}'.format(scan.id))
                scan.backup_flag = -1
                scan.save(update_fields=['backup_flag'])
                continue
            NILM_flag = False if node['properties']['value'] == 'unchecked' else True
            AIdiagnosis = False if scan.detection_info['AIdiagnosis'] == 0 else True
            if AIdiagnosis == NILM_flag:
                # AI not agree to report
                scan.backup_flag = 1
                if NILM_flag == True:
                    scan.backup_tag = 'fp'
                else:
                    scan.backup_tag = 'fn'
                scan.save(update_fields=['backup_flag', 'backup_tag'])
            elif NILM_flag == False:
                # report Not NILM, true positives
                scan.backup_flag = 1
                scan.backup_tag = 'tp'
                scan.save(update_fields=['backup_flag', 'backup_tag'])

        # backup by backup_flag=1
        scans = Scan.objects.filter(
            backup_flag=1, deleted=False, tile_deleted=False)
        logger.info("total to be backup scans:{}".format(len(scans)))
        for scan in scans:
            if scan.detection_info and 'AIdiagnosis' in scan.detection_info:
                handle_backup_scan(scan, move_origin_file=False)
            else:
                # no detection info so just skip bakcup
                scan.backup_flag = 0
                scan.save(update_fields=['backup_flag'])
                continue
        update_task_success(task)
    except Exception as e:
        logger.error(
            "backup negative exams job fail at {}".format(timezone.now()))
        traceback.print_exc()
        update_task_fail(task)

    logger.info('backup_scans task finished')


def delete_scans(task_name, mode='negative'):
    logger.info("starting {} task at {}".format(task_name, timezone.now()))
    task = ScheduledTask.objects.get_or_create(task_name=task_name)[0]
    if not task or task.disabled:
        logger.info("task {} disabled, {}, so skip".format(task_name, task))
        return
    try:
        now = timezone.now()
        run_at = task.run_at
        if not run_at or now >= run_at:
            logger.info("delete {} exams job start at {}".format(mode, now))
            data_kept_days = task.data_kept_days
            # get scan to be backup
            date_less_than = now - datetime.timedelta(days=data_kept_days)
            if mode == 'negative':
                scans = Scan.objects.filter(
                    AIdiagnosis=0, created__lt=date_less_than, deleted=False, reserved_flag=False)
            elif mode == 'positive':
                scans = Scan.objects.filter(
                    AIdiagnosis__gte=1, created__lt=date_less_than, deleted=False, reserved_flag=False)
            else:
                logger.error("mode:{} is not supported! so skip!".format(mode))
                return
            # get all abort scans
            abort_scans = Scan.objects.filter(
                AIdiagnosis__isnull=True, created__lt=date_less_than, deleted=False, reserved_flag=False)
            scans = list(scans) + list(abort_scans)
            # delete scans
            logger.info("total delete scans:{}".format(len(scans)))
            for s in scans:
                if task.keep_results:
                    # delete only tiles/pyramid images
                    delete_tile_folder(s)
                else:
                    update_to_be_delete_scan(s)
            # update next run, next day
            update_task_success(task)
    except Exception as e:
        logger.error(
            "backup negative exams job fail at {}".format(timezone.now()))
        traceback.print_exc()
        update_task_fail(task)
    logger.info('delete_scans task finished')


def dispatch_inference_task(task_queue, status):
    logger.info("starting dispatch task:{} at {}".format(
        task_queue, timezone.now()))
    conn: StrictRedis = get_redis_connection('default')
    # get all task in working queue
    working_ids = []
    for key in conn.scan_iter("*:{}:*".format(task_queue)):
        # get working ids
        r = conn.smembers(key)
        r = [int(i) for i in [*r]]
        working_ids.extend(r)
    # get all scans, add to task queue
    tasks = Scan.objects.filter(status=status, disabled=False, deleted=False, tile_deleted=False).exclude(
        id__in=working_ids).values_list('id', 'priority', 'created')
    logger.info("dispatch task:{} total num {}".format(task_queue, len(tasks)))
    year = datetime.datetime.now().year
    for t in tasks:
        # 满足按照created顺序计算score的策略.
        # 31536000为1年的秒数, 计算规则为距离10年后的时间差, 再由priority调整
        priority = int(t[1])
        created_timestamp = round(t[2].timestamp())
        score = 31536000 * (year + 10 - 1970) - \
            created_timestamp + priority * 31536000
        conn.zadd(task_queue, {t[0]: score})


def generate_bbox_task(status):
    logger.info("starting generate bbox task at {}".format(timezone.now()))
    scans = Scan.objects.filter(disabled=False, bbox_ready=0, hostname__in=('NS', settings.HOSTNAME),
                                detection_info__isnull=False, status=status)
    for scan in scans:
        try:
            generate_bbox_scan(scan)
        except Exception as e:
            logger.error("generate bbox for {} failed ")
            logger.error(e)
            scan.bbox_ready = -1
            scan.save()


def check_LIS_heartbeat(LIS_check_url):
    logger.info("starting check_LIS_heartbeat:{}".format(LIS_check_url))
    timeout = 5
    try:
        requests.get(LIS_check_url, timeout=timeout)
        logger.info("LIS is ready.")
    except (requests.ConnectionError, requests.Timeout) as exception:
        # todo inform frontend, websocket?
        logger.error("Lose connection to LIS!")
