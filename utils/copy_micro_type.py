import sys

import requests

username = "admin"
password = "123456"
url_prefix = "http://localhost:4000/api"
login_url = "{}/api-token-auth/".format(url_prefix)
scan_url = '{}/scans/'.format(url_prefix)
scans_url = '{}/scans/?page=1&page_size=99999999'.format(url_prefix)
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
scans = r.json()['results']

for scan in scans:
    if scan['detection_info'] is None or 'micro_type' not in scan['detection_info']:
        continue
    print('processing {}'.format(scan['id']))
    micro_type = scan['detection_info']['micro_type']
    # post scan
    body = {
        'micro_type': micro_type
    }
    r = requests.put(scan_url + '{}/'.format(scan['id']).format(), headers={
        'Content-Type': 'application/json',
        'Authorization': 'Token {}'.format(token)
    }, json=body)
    if r.status_code >= 400:
        print("Error! status:{}, content:{}, test:{}".format(r.status_code, r.content, r.text))
        sys.exit()
