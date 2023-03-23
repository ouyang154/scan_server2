from .common import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# LIS related
LIS_HEARTBEAT = False
LIS_CHECK_URL = "http://localhost:8080"

# scan server settings
SCAN_ON = True
SCAN_PATH = "/media/cw/data/exam"  # scan root path
SCAN_MEDIA_PATH = "/media/cw/data/scan_media"  # scan root path
SCAN_BACKUP = "/media/cw/data/data_backup"  # scan backup folder
SCAN_EXPORT = "/media/cw/data/data_export"  # scan export folder
SCAN_SERVER_STATIC_ROOT = "/root/.local/server/static" # scan server static root
SCAN_SERVER_CONFIG_ROOT = "/media/cw/data/.config"  # scan server report config folder
SCAN_CONFIG_ROOT = "/usr/local/etc/scan"  # scan config folder

# backup and autoupload
SCAN_BACKUP_ON = True
SCAN_BACKUP_BBOX_ARRAY = ['h_bbox_array', 'l_bbox_array', 'agc_bbox_array', 'microbe_bbox_array']
SCAN_BACKUP_NILM_KEY = 'squamous_cell_analysis.NILM'
# full list 'fp', 'fn', 'tp', 'not_recognized', default only fp tag
SCAN_BACKUP_TAG = ['fp']
# oss settings
REGION = 'oss-cn-beijing'
REGION_URL = 'http://oss-cn-beijing.aliyuncs.com'
ACCESS_KEY_ID = 'LTAI4Fjc6u8nSup1DN3L6qtP'
ACCESS_KEY_SECRET = '79O3Ia4HWznlpfCj1Bp1kAyrfiR5Dt'
OSS_BUCKET = 'cytowiz-public'
AUTOUPLOAD_PATH = 'inbox/autoupload_task'

# inference related
AI_FINISH_STATUS = "predicted"
SMEAR_EDGE_PIXEL = 54720
IMAGE_EDGE_PIXEL = 1024
# 每个level每行的图片数
IMAGE_PER_ROW = {
    '0': 54,
    '1': 27
}
BBOX_CREATION_LIST = ['h_bbox_array', 'l_bbox_array', 'agc_bbox_array', 'microbe_bbox_array', 'bbox_array']
BBOX_CUT_SHAPE = [350, 350]
CONTEXT_INFERENCE = False

# sp related settings
SP_ON = True
SP_FILE_PATH = "/media/cw/data/sp"
SP_ALERT_LEVEL = ["Error", "Warning"]

# Log dir setting
BASE_LOG_DIR = "/root/.local/scan_server_log"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'default': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件，自动切
            'filename': os.path.join(BASE_LOG_DIR, "all.log"),  # 日志文件路径
            'maxBytes': 1024 * 1024 * 50,  # 日志大小 100M
            'backupCount': 2,  # 日志文件备份的数量
            'formatter': 'verbose',  # 日志输出格式
            'encoding': 'utf-8',
        },
        # 日志处理级别warn
        'warn': {
            'level': 'WARN',
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件，自动切
            'filename': os.path.join(BASE_LOG_DIR, "warn.log"),  # 日志文件路径
            'maxBytes': 1024 * 1024 * 50,  # 日志大小 50M
            'backupCount': 2,  # 日志文件备份的数量
            'formatter': 'verbose',  # 日志格式
            'encoding': 'utf-8',
        },
        # 日志级别error
        'error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件，自动切
            'filename': os.path.join(BASE_LOG_DIR, "error.log"),  # 日志文件路径
            'maxBytes': 1024 * 1024 * 50,  # 日志大小 50M
            'backupCount': 2,
            'formatter': 'verbose',  # 日志格式
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        # 默认的logger应用如下配置
        'django': {
            'handlers': ['console', 'default', 'warn', 'error'],
            'level': 'DEBUG',
            'propagate': True,  # 如果有父级的logger示例，表示不要向上传递日志流
        },
        'gunicorn.errors': {
            'level': 'DEBUG',
            'handlers': ['console', 'default', 'warn', 'error'],
            'propagate': False,
        },
        'gunicorn.access': {
            'level': 'DEBUG',
            'handlers': ['console', 'default', 'warn', 'error'],
            'propagate': False,
        },
        'scheduled_task': {
            'level': 'DEBUG',
            'handlers': ['console', 'default', 'warn', 'error'],
            'propagate': False,
        }
    }
}
