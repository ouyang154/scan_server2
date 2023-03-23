import sys

import requests

username = "admin"
password = "123456"
url_prefix = "http://localhost:4000/api"
login_url = "{}/api-token-auth/".format(url_prefix)
scan_url = '{}/scans/'.format(url_prefix)
scans_url = '{}/scans/?page=1&page_size=99999999'.format(url_prefix)


def get_token(url, data):
    r = requests.post(url, json=data)
    if r.status_code >= 400:
        print("Login Error! status:{}, content:{}, test:{}".format(r.status_code, r.content, r.text))
        sys.exit()
    return r.json()["token"]

token = get_token(login_url, {'username': username, 'password': password})

# get all scans
r = requests.get(scans_url, headers={'Authorization': 'Token {}'.format(token)})
scans = r.json()['results']

#             'detection_info': {
#                 'model_version': model_version,
#                 'model_description': model_description,
#                 'AIdiagnosis': AIdiagnosis,
#                 'AIgrade': AIgrade,
#                 'AIscore': AIscore,
#                 "nucleus_count": nucleus_count,
#                 "specimen_qualified": specimen_qualified,
#                 "micro_flag": micro_flag,
#                 'bbox_info': {
#                     "bbox_array": bbox_array,
#                     "p_bbox_array": p_bbox_array,
#                     "h_bbox_array": h_bbox_array,
#                     "l_bbox_array": l_bbox_array,
#                     "agc_bbox_array": agc_bbox_array,
#                     "report_bbox_array": report_bbox_array,
#                     'microbe_bbox_array': microbe_bbox_array
#                 }
#             }

# bbox = {
#     'focus_folder': focusfolder,
#     'image_level': image_level,
#     'image_file': files[i],
#     'label': label,
#     'score': score,
#     'bbox_slide': {
#         'centery': (bbox[3] + bbox[1]) / 2,
#         'centerx': (bbox[0] + bbox[2]) / 2,
#         'width': bbox[2] - bbox[0],
#         'height': bbox[3] - bbox[1],
#         'xyxy': [bbox[0], bbox[1], bbox[2], bbox[3]],
#     },
#     'bbox_image': [box[0], box[1], box[2], box[3]]
# }
for scan in scans:
    if scan['detection_info'] is not None:
        continue
    print('processing {}'.format(scan['id']))
    detection_info = {
        'model_version': 'v0.1',
        'model_description': 'v0.1',
        'AIdiagnosis': scan['AIdiagnosis'],
        'AIgrade': scan['AIgrade'],
        'AIscore': scan['AIscore'],
        "nucleus_count": scan['nucleus_count'],
        "specimen_qualified": scan['specimen_qualified'],
        "micro_flag": scan['micro_flag'],
        'bbox_info': {
            "report_bbox_array": [],
            "h_bbox_array": [],
            "l_bbox_array": [],
            "agc_bbox_array": [],
            'microbe_bbox_array': []
        }
    }

    bbox_info = detection_info['bbox_info']
    # arrays = ['report_bbox_array', 'h_bbox_array', 'l_bbox_array', 'agc_bbox_array', 'microbe_bbox_array']
    array = scan['report_bbox_array']
    target_array = []
    if array is not None:
        for bbox in array:
            target_bbox = {
                'focus_folder': 'focus0',
                'image_level': '0',
                'image_file': None,
                'label': None,
                'score': None,
                'bbox_slide': None,
                'bbox_image': None
            }
            # process 1 bbox, get image_file, bbox_slide, bbox_image
            #             t_bbox_array.append({"centery": float('%.6f' % centery), "centerx": float('%.6f' % centerx),
            #                                  "height": float('%.6f' % height), "width": float('%.6f' % width),
            #                                  "score": float('%.4f' % score), "class": "parasite"})
            # i * 1024 / 54720
            bbox_slide = bbox

            image_x = str(int((bbox_slide['centerx'] * 54720) // 1024))
            image_y = str(int((bbox_slide['centery'] * 54720) // 1024))
            image_file = '{}x{}.jpg'.format(image_y.zfill(3), image_x.zfill(3))

            target_bbox['bbox_slide'] = bbox_slide
            target_bbox['image_file'] = image_file
            target_array.append(target_bbox)
    bbox_info['report_bbox_array'] = target_array

    # p_bbox_array
    array = scan['p_bbox_array']
    target_array = []
    if array is not None:
        for bbox in array:
            target_bbox = {
                'focus_folder': 'focus0',
                'image_level': '0',
                'image_file': None,
                'label': 'HSIL',
                'score': None,
                'bbox_slide': None,
                'bbox_image': None
            }
            # process 1 bbox, get image_file, bbox_slide, bbox_image
            bbox_slide = bbox

            score = bbox_slide['score']
            image_x = str(int((bbox_slide['centerx'] * 54720) // 1024))
            image_y = str(int((bbox_slide['centery'] * 54720) // 1024))
            image_file = '{}x{}.jpg'.format(image_y.zfill(3), image_x.zfill(3))

            centerx = int(round((bbox_slide['centerx'] * 54720) % 1024))
            centery = int(round((bbox_slide['centery'] * 54720) % 1024))
            width = int(bbox_slide['width'] * 54720)
            height = int(bbox_slide['height'] * 54720)
            x1 = round(centerx - width / 2)
            x2 = int(centerx + width / 2)
            y1 = round(centery - height / 2)
            y2 = int(centery + height / 2)
            bbox_image = [x1, y1, x2, y2]

            target_bbox['score'] = score
            target_bbox['bbox_slide'] = bbox_slide
            target_bbox['image_file'] = image_file
            target_bbox['bbox_image'] = bbox_image
            target_array.append(target_bbox)
    bbox_info['p_bbox_array'] = target_array

    array = scan['h_bbox_array']
    target_array = []
    if array is not None:
        for bbox in array:
            target_bbox = {
                'focus_folder': 'focus0',
                'image_level': '0',
                'image_file': None,
                'label': 'HSIL',
                'score': None,
                'bbox_slide': None,
                'bbox_image': None
            }
            # process 1 bbox, get image_file, bbox_slide, bbox_image
            bbox_slide = bbox

            score = bbox_slide['score']
            image_x = str(int((bbox_slide['centerx'] * 54720) // 1024))
            image_y = str(int((bbox_slide['centery'] * 54720) // 1024))
            image_file = '{}x{}.jpg'.format(image_y.zfill(3), image_x.zfill(3))

            centerx = int(round((bbox_slide['centerx'] * 54720) % 1024))
            centery = int(round((bbox_slide['centery'] * 54720) % 1024))
            width = int(bbox_slide['width'] * 54720)
            height = int(bbox_slide['height'] * 54720)
            x1 = round(centerx - width / 2)
            x2 = int(centerx + width / 2)
            y1 = round(centery - height / 2)
            y2 = int(centery + height / 2)
            bbox_image = [x1, y1, x2, y2]

            target_bbox['score'] = score
            target_bbox['bbox_slide'] = bbox_slide
            target_bbox['image_file'] = image_file
            target_bbox['bbox_image'] = bbox_image
            target_array.append(target_bbox)
    bbox_info['h_bbox_array'] = target_array

    array = scan['l_bbox_array']
    target_array = []
    if array is not None:
        for bbox in array:
            target_bbox = {
                'focus_folder': 'focus0',
                'image_level': '0',
                'image_file': None,
                'label': 'LSIL',
                'score': None,
                'bbox_slide': None,
                'bbox_image': None
            }
            # process 1 bbox, get image_file, bbox_slide, bbox_image
            bbox_slide = bbox

            score = bbox_slide['score']
            image_x = str(int((bbox_slide['centerx'] * 54720) // 1024))
            image_y = str(int((bbox_slide['centery'] * 54720) // 1024))
            image_file = '{}x{}.jpg'.format(image_y.zfill(3), image_x.zfill(3))

            centerx = int(round((bbox_slide['centerx'] * 54720) % 1024))
            centery = int(round((bbox_slide['centery'] * 54720) % 1024))
            width = int(bbox_slide['width'] * 54720)
            height = int(bbox_slide['height'] * 54720)
            x1 = round(centerx - width / 2)
            x2 = int(centerx + width / 2)
            y1 = round(centery - height / 2)
            y2 = int(centery + height / 2)
            bbox_image = [x1, y1, x2, y2]

            target_bbox['score'] = score
            target_bbox['bbox_slide'] = bbox_slide
            target_bbox['image_file'] = image_file
            target_bbox['bbox_image'] = bbox_image
            target_array.append(target_bbox)
    bbox_info['l_bbox_array'] = target_array

    def label_type(a):
        if a == 0:
            return "parasite"
        elif a == 1:
            return "fungal"
        elif a == 2:
            return "indicators"
        elif a == 3:
            return "leptotrichia"
        elif a == 4:
            return 'actinomyces'
        elif a == 5:
            return 'herpes'
    # microbe_bbox_array = t_bbox_array + m_bbox_array+i_bbox_array + lep_bbox_array + actinomyces_bbox_array + herpes_bbox_array
    arrays = ['t_bbox_array', 'm_bbox_array', 'i_bbox_array', 'lep_bbox_array', 'actinomyces_bbox_array', 'herpes_bbox_array']
    target_array = []
    for i, a in enumerate(arrays):
        array = scan[a]
        label = label_type(i)
        if array is None:
            continue
        for bbox in array:
            target_bbox = {
                'focus_folder': 'focus0',
                'image_level': '0',
                'image_file': None,
                'label': label,
                'score': None,
                'bbox_slide': None,
                'bbox_image': None
            }
            # process 1 bbox, get image_file, bbox_slide, bbox_image
            bbox_slide = bbox

            score = bbox_slide['score']
            image_x = str(int((bbox_slide['centerx'] * 54720) // 1024))
            image_y = str(int((bbox_slide['centery'] * 54720) // 1024))
            image_file = '{}x{}.jpg'.format(image_y.zfill(3), image_x.zfill(3))

            centerx = int(round((bbox_slide['centerx'] * 54720) % 1024))
            centery = int(round((bbox_slide['centery'] * 54720) % 1024))
            width = int(bbox_slide['width'] * 54720)
            height = int(bbox_slide['height'] * 54720)
            x1 = round(centerx - width / 2)
            x2 = int(centerx + width / 2)
            y1 = round(centery - height / 2)
            y2 = int(centery + height / 2)
            bbox_image = [x1, y1, x2, y2]

            target_bbox['score'] = score
            target_bbox['bbox_slide'] = bbox_slide
            target_bbox['image_file'] = image_file
            target_bbox['bbox_image'] = bbox_image
            target_array.append(target_bbox)
    bbox_info['microbe_bbox_array'] = target_array

    # post scan
    body = {
        'detection_info': detection_info
    }
    r = requests.put(scan_url+'{}/'.format(scan['id']).format(), headers={
            'Content-Type': 'application/json',
            'Authorization': 'Token {}'.format(token)
        }, json=body)
    if r.status_code >= 400:
        print("Error! status:{}, content:{}, test:{}".format(r.status_code, r.content, r.text))
        sys.exit()
