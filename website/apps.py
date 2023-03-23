import os
import platform
import shutil
import sys

from django.apps import AppConfig

class WebsiteConfig(AppConfig):
    name = 'website'

    def init_db_items(self):
        from website.models import ScheduledTask, Report
        import logging

        # init scheduled tasks
        logger = logging.getLogger('django.init_db_items')
        logger.info('init ScheduledTask items...')
        ScheduledTask.objects.get_or_create(task_name='backup_negative_scans')
        ScheduledTask.objects.get_or_create(task_name='backup_positive_scans')
        ScheduledTask.objects.get_or_create(task_name='delete_negative_scans')
        ScheduledTask.objects.get_or_create(task_name='delete_positive_scans')
        ScheduledTask.objects.get_or_create(task_name='autoupload')
        ScheduledTask.objects.get_or_create(task_name='handle_to_be_deleted_scans')
        ScheduledTask.objects.get_or_create(task_name='backup_scans')
        # disable delete backup folders
        # entity, flag = ScheduledTask.objects.get_or_create(task_name='delete_backup_scans')
        # if flag:
        #     entity.disabled = False
        #     entity.hour_of_day = 1
        #     entity.minute_of_hour = 0
        #     entity.save()

        # init scan related DB items
        Report.objects.get_or_create(name='jz', report_model="1", report_process="one_level")

        logger.info('init DB items finished.')

    def startup_job_scan(self):
        from website.models import Scan
        import logging
        from website.utils import generate_bbox_scan
        from django.conf import settings

        logger = logging.getLogger('django.startup_job')
        logger.info("Start up job...")

        # check /media/cw/data/.config folder and scan_server_report_config_default.json
        if not os.path.exists(settings.SCAN_SERVER_CONFIG_ROOT):
            os.makedirs(settings.SCAN_SERVER_CONFIG_ROOT)
        scan_server_report_config_default_template_path = os.path.join(settings.SCAN_SERVER_STATIC_ROOT, 'scan_server_report_config_default.json')
        scan_server_report_config_default_target_path = os.path.join(settings.SCAN_SERVER_CONFIG_ROOT, 'scan_server_report_config_default.json')
        if not os.path.exists(scan_server_report_config_default_target_path):
            shutil.copyfile(scan_server_report_config_default_template_path, scan_server_report_config_default_target_path)

        # collect all inferring jobs and dispatch
        logger.info("collect all inferring tasks ...")
        context_tasks = Scan.objects.filter(status="ContextInferring", disabled=False, deleted=False)
        for task in context_tasks:
            logger.info('updating task{} back to predict'.format(task.id))
            task.status = 'predict'
            task.save()
        detection_tasks = Scan.objects.filter(status="DetectionInferring", disabled=False, deleted=False)
        for task in detection_tasks:
            logger.info('updating task{} back to predict'.format(task.id))
            task.status = 'predict'
            task.save()

        logger.info("Check bbox gen. task")
        scans = Scan.objects.filter(disabled=False, bbox_ready=1, hostname__in=('NS', settings.HOSTNAME),
                                    detection_info__isnull=False)
        for scan in scans:
            try:
                scan.bbox_ready = 0
                scan.save(update_fields=['bbox_ready'])
                generate_bbox_scan(scan)
            except Exception as e:
                logger.error("generate bbox for {} failed ")
                logger.error(e)
                scan.bbox_ready = -1
                scan.save()
        logger.info("Start up job complete")

    def ready(self):
        if 'runserver' in sys.argv or 'daphne' in sys.argv[0]:
            from django.conf import settings
            import logging

            logger = logging.getLogger('django.ready')

            # init DB items
            self.init_db_items()

            from apscheduler.schedulers.background import BackgroundScheduler
            scheduler = BackgroundScheduler()
            if settings.SCAN_ON:
                from website.scheduled_tasks import backup_scans, delete_scans, autoupload_scans, \
                    dispatch_inference_task, generate_bbox_task, delete_backup_scans, handle_to_be_deleted_scans

                logger.info("Start SCAN related startup jobs")
                self.startup_job_scan()
                scheduler.add_job(delete_scans, 'interval', minutes=30, args=("delete_negative_scans", "negative"))
                scheduler.add_job(delete_scans, 'interval', minutes=30, args=("delete_positive_scans", "positive"))
                # disable clean backup folder 
                # scheduler.add_job(delete_backup_scans, 'interval', minutes=30, args=("delete_backup_scans",))
                if settings.CONTEXT_INFERENCE:
                    scheduler.add_job(dispatch_inference_task, 'interval', minutes=1, args=("context", "predict",))
                    scheduler.add_job(dispatch_inference_task, 'interval', minutes=1, args=("detection", "ContextInferred",))
                else:
                    scheduler.add_job(dispatch_inference_task, 'interval', minutes=1, args=("detection", "predict",))
                scheduler.add_job(generate_bbox_task, 'interval', minutes=1, args=("predicted",))
                scheduler.add_job(handle_to_be_deleted_scans, 'interval', minutes=1, args=())
                if settings.SCAN_BACKUP_ON:
                    scheduler.add_job(backup_scans, 'interval', minutes=10, args=())
                    scheduler.add_job(autoupload_scans, 'interval', minutes=20, args=("autoupload",))

            if settings.SP_ON:
                logger.info("Start SP related startup jobs")

            if settings.LIS_HEARTBEAT:
                logger.info("Setting up LIS heartbeat checking job...")
                from website.scheduled_tasks import check_LIS_heartbeat
                scheduler.add_job(check_LIS_heartbeat, 'interval', seconds=30, args=(settings.LIS_CHECK_URL, ))

            if len(scheduler.get_jobs()) > 0:
                logger.info("background scheduler has jobs, starting...")
                scheduler.start()

            if platform.system() == 'Linux':
                logger.info('sending systemd ready...')
                from systemd.daemon import notify
                notify('READY=1')

            logger.info('scan server ready.')
