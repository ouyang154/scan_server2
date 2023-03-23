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


def get_token(url, data):
    r = requests.post(url, json=data)
    if r.status_code >= 400:
        print("Login Error! status:{}, content:{}, text:{}".format(r.status_code, r.content, r.text))
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
        print('deleting {}'.format(scan['id']))
        delete_url = '{}/scans/{}/?deleted=true'.format(url_prefix, scan['id'])
        r = requests.delete(delete_url, headers={'Authorization': 'Token {}'.format(token)})
        if r.status_code >= 400:
            print("Delete Error! status:{}, content:{}, text:{}".format(r.status_code, r.content, r.text))
            sys.exit()
