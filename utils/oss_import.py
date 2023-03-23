import json
import os
import sys
import time

import oss2
import requests

# scan_server info
username = "admin"
password = "123456"
url_prefix = "http://localhost:4000/api"
login_url = "{}/api-token-auth/".format(url_prefix)
scan_url = '{}/scans/'.format(url_prefix)
# oss info
REGION = 'oss-cn-beijing'
REGION_URL = 'http://oss-cn-beijing.aliyuncs.com'
ACCESS_KEY_ID = 'test'
ACCESS_KEY_SECRET = 'test'
OSS_BUCKET = 'image-labeling-huabei2'
# 对该目录下做单层的扫描上传，不支持多级
AUTOUPLOAD_PATH = 'autoupload_task'
scan_path = 'test_import_scan'
auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, REGION_URL, OSS_BUCKET)
wait_time = 3600  # wait time in seconds


def get_token(url, data):
    r = requests.post(url, json=data)
    if r.status_code >= 400:
        print("Login Error! status:{}, content:{}, test:{}".format(r.status_code, r.content, r.text))
        sys.exit()
    return r.json()["token"]


# login and get token
token = get_token(login_url, {'username': username, 'password': password})

while True:
    # get all scans
    for obj in oss2.ObjectIterator(bucket, prefix=AUTOUPLOAD_PATH + '/', delimiter='/'):
        # 通过is_prefix方法判断obj是否为文件夹。
        if obj.is_prefix():  # 文件夹
            print('directory: ' + obj.key)
            # check is finish_flag.log exists
            scan_folder = obj.key
            exist_finish = bucket.object_exists('{}finish_flag.log'.format(scan_folder))
            json_file = os.path.basename(scan_folder.rstrip('/')) + '.json'
            exist_json = bucket.object_exists('{}{}'.format(scan_folder, json_file))
            if exist_finish & exist_json:
                print("starting import {}".format(scan_folder))
                # add scan, change upload flag to 2
                object_stream = bucket.get_object('{}{}'.format(scan_folder, json_file))
                object_b = object_stream.read()
                scan = json.loads(object_b)
                scan["upload_flag"] = 2
                r = requests.post(scan_url, headers={
                    'Content-Type': 'application/json',
                    'Authorization': 'Token {}'.format(token)
                }, json=scan)
                if r.status_code >= 400:
                    print("Error! status:{}, content:{}, test:{}".format(r.status_code, r.content, r.text))
                    sys.exit()
                # move scan folder to scan path
                ori_scan_folder = obj.key
                dest_scan_folder = ori_scan_folder.replace(AUTOUPLOAD_PATH, scan_path)
                print("moving {} to {}".format(ori_scan_folder, dest_scan_folder))
                for obj in oss2.ObjectIterator(bucket, prefix=ori_scan_folder):
                    bucket.copy_object(OSS_BUCKET, obj.key, obj.key.replace(AUTOUPLOAD_PATH, scan_path))
                for obj in oss2.ObjectIterator(bucket, prefix=ori_scan_folder):
                    bucket.delete_object(obj.key)
                print("import finished:{}".format(scan_folder))
        else:  # 文件
            print('file: ' + obj.key)
    print("wait for next round:{}s".format(wait_time))
    time.sleep(wait_time)
