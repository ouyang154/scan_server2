import math
import sys

import requests

username = "admin"
password = "123456"
url_prefix = "http://localhost:4000/api"
login_url = "{}/api-token-auth/".format(url_prefix)
scan_url = '{}/scans/'.format(url_prefix)
page_size = 20
scans_url = '{}/scans/?page=1&page_size={}'.format(url_prefix, page_size)
transfer_keys = ['name', 'age', 'birth', 'gender', 'patient_id', 'patient_roomNum', 'patient_roomBed', 'patient_roomId',
                 'patient_phone', 'menses', 'menses_date', 'specimen_id', 'specimen_date', 'specimen_type',
                 'reference_date', 'reference_hospital', 'reference_department', 'reference_doctor']


def get_token(url, data):
    r = requests.post(url, json=data)
    if r.status_code >= 400:
        print("Login Error! status:{}, content:{}, test:{}".format(r.status_code, r.content, r.text))
        sys.exit()
    return r.json()["token"]


token = get_token(login_url, {'username': username, 'password': password})

# get all scans
r = requests.get(scans_url, headers={'Authorization': 'Token {}'.format(token)})
result = r.json()
count = result['count']
pages = int(math.ceil(count / page_size))
scans = result['results']

for page in range(pages):
    scans_url = '{}/scans/?page={}&page_size={}'.format(url_prefix, page + 1, page_size)
    r = requests.get(scans_url, headers={'Authorization': 'Token {}'.format(token)})
    scans = r.json()['results']
    for scan in scans:
        if scan['specimen_info'] is not None:
            continue
        print('processing {}'.format(scan['id']))
        specimen_info = {}
        for key in transfer_keys:
            specimen_info[key] = scan[key]

        # post scan
        body = {
            'specimen_info': specimen_info
        }
        r = requests.put(scan_url + '{}/'.format(scan['id']).format(), headers={
            'Content-Type': 'application/json',
            'Authorization': 'Token {}'.format(token)
        }, json=body)
        if r.status_code >= 400:
            print("Error! status:{}, content:{}, test:{}".format(r.status_code, r.content, r.text))
            sys.exit()
