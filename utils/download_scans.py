import math
import sys
import json
import requests

username = "admin"
password = "123456"
url_prefix = "http://localhost:4000/api"
login_url = "{}/api-token-auth/".format(url_prefix)
scan_url = '{}/scans/'.format(url_prefix)
page_size = 20
scans_url = '{}/scans/?page=1&page_size={}&created_range_after=2021-07-01&excluding=scan_log,scout_log'.format(url_prefix, page_size)


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
print('total scan:{}'.format(count))
pages = int(math.ceil(count / page_size))
scans = result['results']

all_scans = []
for page in range(pages):
    scans_url = '{}/scans/?page={}&page_size={}&created_range_after=2021-07-01&excluding=scan_log,scout_log'.format(url_prefix, page + 1, page_size)
    r = requests.get(scans_url, headers={'Authorization': 'Token {}'.format(token)})
    scans = r.json()['results']
    all_scans.extend(scans)
    
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(all_scans, f, ensure_ascii=False, indent=4)
        