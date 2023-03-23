import gzip
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import time
import traceback
import uuid
from os import listdir, makedirs, remove
from os.path import isdir, join, exists, realpath
# from send2trash import send2trash as st
from shutil import move, rmtree
import platform
import cv2
import numpy as np
from django.conf import settings
from rest_framework.renderers import JSONRenderer
from rest_framework.utils import encoders

from website.models import Scan
from website.serializers import ScanSerializer

logger = logging.getLogger('django.utils')


# deprecated
# def send_to_trash_bin(scan_path):
#     if isdir(scan_path) or isfile(scan_path):
#         logger.info("deleting dir/file:{}".format(scan_path))
#         st(scan_path)
#     else:
#         logger.info("no dir/file {}, so skip deleting".format(scan_path))


def get_pid_by_name(process_name) -> list:
    if platform.system() == "Windows":
        # do not support windows
        return []
    try:
        pids = list(map(int, subprocess.check_output(["pgrep", process_name]).split()))
        return pids
    except:
        # no such process
        return []


# deprecated
def soft_delete_scan(instance: Scan, backup=True):
    if not instance.reserved_flag and not instance.disabled:
        # send to backup
        if backup:
            move_folder(settings.SCAN_PATH, settings.SCAN_BACKUP, instance.scan_folder)
        instance.disabled = True
        # keep scan\scout\det\post_process log 
        # instance.scan_log = None
        # instance.scout_log = None
        instance.save(update_fields=['disabled', 'scan_log', 'scout_log'])


def create_scan_db_json_gz(scan, file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
    serializer = ScanSerializer(scan)
    content_string = json.dumps(serializer.data, cls=encoders.JSONEncoder, ensure_ascii=False)
    with gzip.open(file_path, 'wb') as f:
        f.write(content_string.encode())
    

def get_checkbox_node_by_key(node_array, dot_connected_key):
    key_list = dot_connected_key.split('.')
    key = key_list[0]
    node = None
    for n in node_array:
        if n['properties']['node_key'] == key:
            node = n
    if not node:
        return None 
           
    if len(key_list) == 1:
        # return properties
        return node
    else:
        # search in children
        return get_checkbox_node_by_key(node['children'], '.'.join(key_list[1:]))


def backup_fn_scan(scan: Scan, move_origin_file=False, tag_name='fn'):
    # 假阴scan，backup all focus level 0 images
    try:
        # check origin_scan_folder
        origin_scan_folder = os.path.join(settings.SCAN_PATH, scan.scan_folder)
        if not os.path.exists(origin_scan_folder):
            logger.error("backup_fn_scan:{} scan folder not exists!".format(scan.id))
            raise RuntimeError()
        
        # create backup root folder, tile folder
        scan.backup_folder = '{}/{}'.format(tag_name, scan.scan_folder)
        backup_root_folder = os.path.join(settings.SCAN_BACKUP, scan.backup_folder)
        shutil.rmtree(backup_root_folder, ignore_errors=True)
        Path(backup_root_folder).mkdir(parents=True, exist_ok=True)
        backup_tile_folder = os.path.join(backup_root_folder, 'tile')
        Path(backup_tile_folder).mkdir(parents=True, exist_ok=True)
        
        # create db.json.gz
        db_backup_file_path = os.path.join(backup_root_folder, 'db.json.gz')
        create_scan_db_json_gz(scan, db_backup_file_path)
        
        # iterate focus folder and backup level 0
        origin_tile_folder = os.path.join(settings.SCAN_PATH, scan.scan_folder, 'tile')
        for focus_folder in os.listdir(origin_tile_folder):
            origin_focus_folder = os.path.join(origin_scan_folder, 'tile', focus_folder)
            backup_focus_folder = os.path.join(backup_tile_folder, focus_folder)
            if os.path.isdir(origin_focus_folder) and 'focus' in focus_folder:
                Path(backup_focus_folder).mkdir(parents=True, exist_ok=True)
                origin_focus_level_0_folder = os.path.join(origin_focus_folder, '0')
                backup_focus_level_0_folder = os.path.join(backup_focus_folder, '0')              
                # bakcup
                if move_origin_file:
                    # move origin file to backup folder
                    shutil.move(origin_focus_level_0_folder, backup_focus_level_0_folder)
                else:
                    # create symbolic link in backup folder
                    os.symlink(origin_focus_level_0_folder, backup_focus_level_0_folder)
        
        # update db status
        scan.backup_folder = '{}/{}'.format(tag_name, scan.scan_folder)
        scan.backup_flag = 2
    except Exception as e:
        logger.error("backup_fn_scan failed!")
        traceback.print_exc()
        scan.backup_folder = None
        scan.backup_flag = -1
        backup_root_folder = os.path.join(settings.SCAN_BACKUP, tag_name, scan.scan_folder)
        shutil.rmtree(backup_root_folder, ignore_errors=True)
    finally:
        scan.save(update_fields=['backup_flag', 'backup_folder'])
        

def backup_fp_scan(scan: Scan, move_origin_file=False, tag_name='fp'):
    # 假阳scan，backup all focus level 0 images
    try:
        # check origin_scan_folder
        origin_scan_folder = os.path.join(settings.SCAN_PATH, scan.scan_folder)
        if not os.path.exists(origin_scan_folder):
            logger.error("backup_fp_scan:{} scan folder not exists!".format(scan.id))
            raise RuntimeError()
            
        # create backup root folder, tile folder
        backup_root_folder = os.path.join(settings.SCAN_BACKUP, tag_name, scan.scan_folder)
        shutil.rmtree(backup_root_folder, ignore_errors=True)
        Path(backup_root_folder).mkdir(parents=True, exist_ok=True)
        backup_tile_folder = os.path.join(backup_root_folder, 'tile')
        Path(backup_tile_folder).mkdir(parents=True, exist_ok=True)
        
        # create db.json.gz
        db_backup_file_path = os.path.join(backup_root_folder, 'db.json.gz')
        create_scan_db_json_gz(scan, db_backup_file_path)
        
        # todo iterate detection info bboxes
        for backup_bbox_array in settings.SCAN_BACKUP_BBOX_ARRAY:
            logger.debug('start backup bbox_array:{}'.format(backup_bbox_array))
            for bbox_info in scan.detection_info['bbox_info'][backup_bbox_array]:
                focus_folder = bbox_info['focus_folder']
                image_level = bbox_info['image_level']
                image_file = bbox_info['image_file']
                # backup tile
                backup_focus_level_folder = os.path.join(backup_tile_folder, focus_folder, image_level)
                Path(backup_focus_level_folder).mkdir(parents=True, exist_ok=True)
                origin_tile_path = os.path.join(origin_scan_folder, 'tile', focus_folder, image_level, image_file)
                backup_tile_path = os.path.join(backup_focus_level_folder, image_file)
                if os.path.exists(backup_tile_path):
                    continue
                if move_origin_file:
                    shutil.move(origin_tile_path, backup_tile_path)
                else:
                    os.symlink(origin_tile_path, backup_tile_path)
                       
        # update db status
        scan.backup_folder = '{}/{}'.format(tag_name, scan.scan_folder)
        scan.backup_flag = 2
    except Exception as e:
        logger.error("backup_fp_scan failed!")
        traceback.print_exc()
        scan.backup_folder = None
        scan.backup_flag = -1
        backup_root_folder = os.path.join(settings.SCAN_BACKUP, tag_name, scan.scan_folder)
        shutil.rmtree(backup_root_folder, ignore_errors=True)
    finally:
        scan.save(update_fields=['backup_flag', 'backup_folder'])


def handle_backup_scan(scan: Scan, move_origin_file=False):
    if scan.backup_flag in [1, 2]:
        if scan.backup_tag == 'fp':
            # backup fp scans，假阳图片
            backup_fp_scan(scan, move_origin_file=move_origin_file, tag_name=scan.backup_tag)
        elif scan.backup_tag in ['fn', 'tp']:
            # backup fn/tp scans, 假阴\真阳图片
            backup_fn_scan(scan, move_origin_file=move_origin_file, tag_name=scan.backup_tag)
        # elif scan.backup_tag == 'tp':
        #     # backup tp scans, 真阳图片
        #     backup_fn_scan(scan, move_origin_file=move_origin_file, tag_name=scan.backup_tag)
        else:
            # 未知类型，使用假阴备份方式
            backup_fn_scan(scan, move_origin_file=move_origin_file, tag_name='not_recognized')
    

def update_to_be_delete_scan(instance: Scan):
    if not instance.reserved_flag and not instance.deleted:
        instance.disabled = True
        instance.to_be_deleted = True
        instance.save(update_fields=['disabled', 'to_be_deleted'])


def hard_delete_scan(instance: Scan):
    if not instance.reserved_flag and not instance.deleted:
        rm_folder(join(settings.SCAN_PATH, instance.scan_folder))
        instance.disabled = True
        instance.to_be_deleted = False
        instance.deleted = True
        # keep scan\scout\det\post_process log 
        # instance.scan_log = None
        # instance.scout_log = None
        instance.save(update_fields=['disabled', 'deleted', 'to_be_deleted'])


def delete_tile_folder(instance: Scan):
    if not instance.reserved_flag and instance.status not in ['ContextInferring', 'DetectionInferring'] and \
       not instance.deleted and not instance.disabled and not instance.tile_deleted:
        # handle fn pn exams before remove folder
        handle_backup_scan(instance, move_origin_file=True)
        rm_folder(join(settings.SCAN_PATH, instance.scan_folder, 'tile'))
        instance.tile_deleted = True
        # keep scan\scout\det\post_process log 
        # instance.scan_log = None
        # instance.scout_log = None
        instance.save(update_fields=['tile_deleted', 'scan_log', 'scout_log'])


def export_scan(scan: Scan):
    export_folder = join(settings.SCAN_EXPORT, '{}-{}-{}'.format(scan.scan_folder, scan.specimen_info.specimen_id, scan.specimen_info.name))
    if scan.disabled or scan.deleted:
        return False
    else:
        copy_folder(join(settings.SCAN_PATH, scan.scan_folder), export_folder)
    db_backup_file_path = join(export_folder, 'db.json.gz')
    create_scan_db_json_gz(scan, db_backup_file_path)
    return export_folder


def import_scan(scan_path):
    # ungzip db.json.gz
    db_gz = os.path.join(scan_path, 'db.json.gz')
    if os.path.exists(db_gz):
        with gzip.open(db_gz, 'rb') as f_in:
            with open(os.path.join(scan_path, 'db.json'), 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
                
    # load db.json and create scan
    with open(os.path.join(scan_path, 'db.json')) as f:
        db_data = json.load(f)
    scan_folder = os.path.basename(scan_path)
    db_data['scan_folder'] = scan_folder
    db_data.pop('id', None)
    if 'specimen_info' in db_data:
        db_data['specimen_info'].pop('id', None)
    serializer = ScanSerializer(data=db_data)
    serializer.is_valid(raise_exception=True)
    instance = serializer.save()
    
    # copy folder to exam folder
    shutil.copytree(scan_path, join(settings.SCAN_PATH, scan_folder))
    return instance


def copy_folder(ori_path, dst_path, symlinks=False, ignore=None):
    if not exists(dst_path):
        makedirs(dst_path, exist_ok=True)
    for item in listdir(ori_path):
        s = join(ori_path, item)
        d = join(dst_path, item)
        if isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def move_folder(src, dst, folder):
    ori_path = join(src, folder)
    dst_path = join(dst, folder)
    if isdir(ori_path):
        if not exists(dst):
            makedirs(dst, exist_ok=True)
        move(ori_path, dst_path)


def rm_folder(src):
    # use real path
    path = realpath(src)
    if isdir(path):
        rmtree(path, ignore_errors=True)


def write_file(dst_folder, dst_file, content):
    if not exists(dst_folder):
        makedirs(dst_folder, exist_ok=True)
    file_path = join(dst_folder, dst_file)
    if exists(file_path):
        remove(file_path)
    new_file = open(file_path, "wb")
    new_file.write(content)
    new_file.close()


def generate_bbox(bbox, focuses, scan_root, scan_folder, window_size, detection_folder):
    image_level = bbox['image_level']
    image_file = bbox['image_file']
    image_file_x = int(image_file[4:7])
    image_file_y = int(image_file[:3])
    label = bbox['label']
    xyxy = bbox['bbox_image']
    # read image and save bbox image
    for focus in focuses:
        # 配置，否则oss ls耗费大量时间
        image_file_per_edge = settings.IMAGE_PER_ROW[image_level]
        ori_image = cv2.imread(os.path.join(scan_root, scan_folder, 'tile', focus, image_level, image_file))
        width = ori_image.shape[1]
        height = ori_image.shape[0]
        x1, y1, x2, y2 = xyxy
        # check if out of range
        x2 = x2 if x2 <= width else width
        y2 = y2 if y2 <= height else height
        # init cutting window
        window_x1 = round((x2 + x1) / 2 - window_size[1] / 2)
        window_x2 = int((x2 + x1) / 2 + window_size[1] / 2)
        window_y1 = round((y2 + y1) / 2 - window_size[0] / 2)
        window_y2 = int((y2 + y1) / 2 + window_size[0] / 2)
        # merging images if needed
        merge_mode = 0
        if window_x1 < 0 and image_file_x > 0:
            # left side
            left_image_file = '{}x{}.jpg'.format(str(image_file_y).zfill(3), str(image_file_x - 1).zfill(3))
            left_image = cv2.imread(
                os.path.join(scan_root, scan_folder, 'tile', focus, image_level, left_image_file))
            # merge image and update window
            ori_image = np.concatenate([left_image, ori_image], axis=1)
            window_x1 = width + window_x1
            window_x2 = width + window_x2
            merge_mode = 1
        elif window_x2 > width and image_file_x < image_file_per_edge:
            # right side merge
            right_image_file = '{}x{}.jpg'.format(str(image_file_y).zfill(3),
                                                  str(image_file_x + 1).zfill(3))
            right_image = cv2.imread(
                os.path.join(scan_root, scan_folder, 'tile', focus, image_level, right_image_file))
            # merge image and update window
            ori_image = np.concatenate([ori_image, right_image], axis=1)
            merge_mode = 2

        if window_y1 < 0 and image_file_y > 0:
            # upper side merge
            window_y1 = height + window_y1
            window_y2 = height + window_y2
            upper_image_file = '{}x{}.jpg'.format(str(image_file_y - 1).zfill(3),
                                                  str(image_file_x).zfill(3))
            upper_image = cv2.imread(
                os.path.join(scan_root, scan_folder, 'tile', focus, image_level, upper_image_file))
            if merge_mode == 0:
                ori_image = np.concatenate([upper_image, ori_image], axis=0)
            elif merge_mode == 1:
                # upper left
                corner_image_file = '{}x{}.jpg'.format(str(image_file_y - 1).zfill(3),
                                                       str(image_file_x - 1).zfill(3))
                corner_image = cv2.imread(
                    os.path.join(scan_root, scan_folder, 'tile', focus, image_level, corner_image_file))
                upper_image = np.concatenate([corner_image, upper_image], axis=1)
                ori_image = np.concatenate([upper_image, ori_image], axis=0)
            elif merge_mode == 2:
                # upper right
                corner_image_file = '{}x{}.jpg'.format(str(image_file_y - 1).zfill(3),
                                                       str(image_file_x + 1).zfill(3))
                corner_image = cv2.imread(
                    os.path.join(scan_root, scan_folder, 'tile', focus, image_level, corner_image_file))
                upper_image = np.concatenate([upper_image, corner_image], axis=1)
                ori_image = np.concatenate([upper_image, ori_image], axis=0)
        elif window_y2 > height and image_file_y < image_file_per_edge:
            # lower side merge
            lower_image_file = '{}x{}.jpg'.format(str(image_file_y + 1).zfill(3),
                                                  str(image_file_x).zfill(3))
            lower_image = cv2.imread(
                os.path.join(scan_root, scan_folder, 'tile', focus, image_level, lower_image_file))
            if merge_mode == 0:
                ori_image = np.concatenate([ori_image, lower_image], axis=0)
            elif merge_mode == 1:
                # lower left
                corner_image_file = '{}x{}.jpg'.format(str(image_file_y + 1).zfill(3),
                                                       str(image_file_x - 1).zfill(3))
                corner_image = cv2.imread(
                    os.path.join(scan_root, scan_folder, 'tile', focus, image_level, corner_image_file))
                lower_image = np.concatenate([corner_image, lower_image], axis=1)
                ori_image = np.concatenate([ori_image, lower_image], axis=0)
            elif merge_mode == 2:
                # lower right
                corner_image_file = '{}x{}.jpg'.format(str(image_file_y + 1).zfill(3),
                                                       str(image_file_x + 1).zfill(3))
                corner_image = cv2.imread(
                    os.path.join(scan_root, scan_folder, 'tile', focus, image_level, corner_image_file))
                lower_image = np.concatenate([lower_image, corner_image], axis=1)
                ori_image = np.concatenate([ori_image, lower_image], axis=0)

        target_image = ori_image[window_y1:(window_y2 + 1), window_x1:(window_x2 + 1), :]
        target_image_file = '{}_{}_{}.jpg'.format(label, focus, uuid.uuid1())
        target_image_path = os.path.join(detection_folder, target_image_file)
        cv2.imwrite(target_image_path, target_image)
        bbox['file_{}'.format(focus)] = target_image_file
    return bbox


def generate_bbox_scan(scan: Scan):
    if scan.bbox_ready == 1:
        return
    # check scan completeness
    if scan.detection_info is None:
        return
    try:
        scan.bbox_ready = 1
        scan.save(update_fields=['bbox_ready'])

        tic = time.time()
        logger.info("start generating bboxes for {}".format(scan))

        scan_root = settings.SCAN_PATH
        scan_folder = scan.scan_folder
        focuses = ['focus' + str(i) for i in range(scan.multi_focus)]
        detection_info = scan.detection_info
        bbox_list = settings.BBOX_CREATION_LIST
        window_size = settings.BBOX_CUT_SHAPE

        if not os.path.isdir(os.path.join(scan_root, scan_folder)):
            raise Exception("no exam folder locally")

        # create detection folder, delete if exists
        detection_folder = os.path.join(scan_root, scan_folder, 'detection')
        if os.path.isdir(detection_folder):
            shutil.rmtree(detection_folder, ignore_errors=True)
        os.makedirs(detection_folder, exist_ok=True)

        for b in bbox_list:
            # generate for each category
            bbox_array = detection_info['bbox_info'][b]
            n_bbox_array = []
            for i, bbox in enumerate(bbox_array):
                n_bbox_array.append(generate_bbox(bbox, focuses, scan_root, scan_folder, window_size, detection_folder))
            detection_info['bbox_info'][b] = n_bbox_array

        scan.detection_info = detection_info
        scan.bbox_ready = 2
        scan.save(force_update=True, update_fields=['detection_info', 'bbox_ready'])
        logger.info("finish generating bboxes for {}, cost {}s".format(scan, time.time() - tic))
    except Exception as e:
        scan.bbox_ready = 0
        scan.save(update_fields=['bbox_ready'])
        raise e


def add_bbox_scan(scan: Scan, array_key, bbox, position):
    array = scan.detection_info['bbox_info'][array_key]
    result_bbox = {
        'generate_by': 'manual',
        'focus_folder': bbox['focus_folder'],
        'image_level': bbox['image_level'],
        'image_file': None,
        'label': bbox['label'],
        'score': 1,
        'bbox_slide': bbox['bbox_slide'],
        'bbox_image': None
    }
    # get image_file, bbox_image
    bbox_slide = result_bbox['bbox_slide']
    smear_edge_pixel = settings.SMEAR_EDGE_PIXEL
    image_edge_pixel = settings.IMAGE_EDGE_PIXEL
    image_x = str(int((bbox_slide['centerx'] * smear_edge_pixel) // image_edge_pixel))
    image_y = str(int((bbox_slide['centery'] * smear_edge_pixel) // image_edge_pixel))
    image_file = '{}x{}.jpg'.format(image_y.zfill(3), image_x.zfill(3))
    result_bbox['image_file'] = image_file

    image_centerx = int(round((bbox_slide['centerx'] * smear_edge_pixel) % image_edge_pixel))
    image_centery = int(round((bbox_slide['centery'] * smear_edge_pixel) % image_edge_pixel))
    width = int(bbox_slide['width'] * smear_edge_pixel)
    height = int(bbox_slide['height'] * smear_edge_pixel)
    x1 = round(image_centerx - width / 2)
    x2 = int(image_centerx + width / 2)
    y1 = round(image_centery - height / 2)
    y2 = int(image_centery + height / 2)
    bbox_image = [x1, y1, x2, y2]
    result_bbox['bbox_image'] = bbox_image

    # gen. bbox pic.
    scan_root = settings.SCAN_PATH
    scan_folder = scan.scan_folder
    focuses = ['focus' + str(i) for i in range(scan.multi_focus)]
    window_size = settings.BBOX_CUT_SHAPE
    detection_folder = os.path.join(scan_root, scan_folder, 'detection')
    result_bbox = generate_bbox(result_bbox, focuses, scan_root, scan_folder, window_size, detection_folder)

    array.insert(position, result_bbox)
    scan.save(update_fields=['detection_info'])
    return result_bbox


def delete_bbox_scan(scan: Scan, array_key, position):
    array = scan.detection_info['bbox_info'][array_key]
    bbox = array[position]
    scan_root = settings.SCAN_PATH
    scan_folder = scan.scan_folder
    focuses = ['focus' + str(i) for i in range(scan.multi_focus)]
    detection_folder = os.path.join(scan_root, scan_folder, 'detection')
    for i, focus in enumerate(focuses):
        bbox_file = bbox['file_focus{}'.format(i)]
        bbox_path = os.path.join(detection_folder, bbox_file)
        if os.path.exists(bbox_path):
            os.remove(bbox_path)
    del array[position]
    scan.save(update_fields=['detection_info'])


def backup_scan_to_path(target_backup_root):
    logger.info('starting backup_scan_to_path to {}...'.format(target_backup_root))
    scans = list(Scan.objects.filter(backup_flag=2))
    logger.info('total scans to backup:{}'.format(len(scans)))
    for scan in scans:
        ori_backup_folder = os.path.join(settings.SCAN_BACKUP, scan.backup_folder)
        target_path = os.path.join(target_backup_root, scan.backup_folder)
        shutil.copytree(ori_backup_folder, target_path, symlinks=False, 
                        ignore_dangling_symlinks=True, dirs_exist_ok=True)
        scan.backup_flag = 3
        scan.backup_folder = None
        scan.save(update_fields=['backup_flag', 'backup_folder'])        
        rm_folder(ori_backup_folder)
        