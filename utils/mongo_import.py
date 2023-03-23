import sys

import pymongo
import requests

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client.cytolist

users = db.users
reports = db.hospitals
microscope = db.machines
cytos = db.cytos
username = "admin"
password = "123456"
url_prefix = "http://localhost:4000/api"
login_url = "{}/api-token-auth/".format(url_prefix)
user_url = '{}/users/'.format(url_prefix)
report_url = '{}/reports/'.format(url_prefix)
microscope_url = '{}/micros/'.format(url_prefix)
scan_url = '{}/scans/'.format(url_prefix)


def get_token(url, data):
    r = requests.post(url, json=data)
    if r.status_code >= 400:
        print("Login Error! status:{}, content:{}, test:{}".format(r.status_code, r.content, r.text))
        sys.exit()
    return r.json()["token"]


def get_report(url, token):
    r = requests.get(url, headers={
        'Authorization': 'Token {}'.format(token)
    })
    if r.status_code >= 400:
        print("Get Task Error! status:{}, content:{}, test:{}".format(r.status_code, r.content, r.text))
        return None
    return r.json()[0]['id'] if len(r.json()) > 0 else None

# login and get token
token = get_token(login_url, {'username': username, 'password': password})

# import user
# cur = users.find()
# for i in cur:
#     if 'admin' == i['name']:
#         continue
#     name = i['name']
#     print("processing user:{}".format(name))
#     if name is not None and name != '':
#         # 原始密码被hash了，重置123456
#         user = {
#             'username': name,
#             'password': '123456'
#         }
#         i['user'] = user
#         del i['_id']
#         # post to scan_server
#         r = requests.post(user_url, headers={
#             'Content-Type': 'application/json',
#             'Authorization': 'Token {}'.format(token)
#         }, json=i)
#         if r.status_code >= 400:
#             print("Error! status:{}, content:{}, test:{}".format(r.status_code, r.content, r.text))
#             sys.exit()

# import hospital, just for one
# cur = reports.find()
# for i in cur:
#     print("processing hospital")
#     del i['_id']
#     # find existing reprot
#     report_id = get_report(report_url, token)
#     if report_id:
#         # update report
#         r = requests.put(report_url+'{}/'.format(report_id), headers={
#             'Content-Type': 'application/json',
#             'Authorization': 'Token {}'.format(token)
#         }, json=i)
#         if r.status_code >= 400:
#             print("Error! status:{}, content:{}, test:{}".format(r.status_code, r.content, r.text))
#             sys.exit()
#     else:
#         # post new report
#         r = requests.post(report_url, headers={
#             'Content-Type': 'application/json',
#             'Authorization': 'Token {}'.format(token)
#         }, json=i)
#         if r.status_code >= 400:
#             print("Error! status:{}, content:{}, test:{}".format(r.status_code, r.content, r.text))
#             sys.exit()
#     # only process one report
#     break

# import machines
# cur = microscope.find()
# for i in cur:
#     print("processing machines")
#     del i['_id']
#     # add new microscopes
#     r = requests.post(microscope_url, headers={
#         'Content-Type': 'application/json',
#         'Authorization': 'Token {}'.format(token)
#     }, json=i)
#     if r.status_code >= 400:
#         print("Error! status:{}, content:{}, test:{}".format(r.status_code, r.content, r.text))
#         sys.exit()

# import scans,
# reviewinfo: approver author verifier
# AIdescription?
# scanpara: multi_focus, scan_date, technician
cur = cytos.find()
j = 0
for i in cur:
    print("processing specimen:{}".format(i['specimen_id']))
    i['age'] = int(i['age']) if i['age'] != '' and i['age'] is not None else None
    i['scan_folder'] = str(i['_id'])
    del i['_id']
    # add new scans
    i['approver'] = i['reviewinfo']['approver']
    i['author'] = i['reviewinfo']['author']
    i['verifier'] = i['reviewinfo']['verifier']
    del i['reviewinfo']
    i['multi_focus'] = i['scanpara']['multi_focus']
    i['scan_date'] = i['scanpara']['scan_date']
    i['technician'] = i['scanpara']['technician']
    del i['scanpara']
    if i['p_bbox_array'] is not None:
        bbox_array = i['p_bbox_array'][15:]
        bbox_array.append(i['p_bbox_array'][:15])
        i['bbox_array'] = bbox_array
    i['AIinformation'] = i['AIdescription']
    r = requests.post(scan_url, headers={
        'Content-Type': 'application/json',
        'Authorization': 'Token {}'.format(token)
    }, json=i)
    if r.status_code >= 400:
        print("Error! status:{}, content:{}, test:{}".format(r.status_code, r.content, r.text))
        sys.exit()
    j = j+1
    print("processed:{}".format(j))