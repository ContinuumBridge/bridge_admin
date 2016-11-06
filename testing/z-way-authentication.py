#!/usr/bin/env python
# bridge_monotor.py
# Copyright (C) ContinuumBridge Limited, 2015 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#
import requests
import json

url = "http://192.168.0.15:8083/ZAutomation/api/v1/login"
payload = {"login": "admin", "password": "admin", "keepme": False, "default_ui": 1}
headers = {'Content-Type': 'application/json'}
status = 0
print("url: ", url)
r = requests.post(url, headers=headers, data=json.dumps(payload))
print("text: ", r.text)
print("status code: ", r.status_code)
print("cookies: ", r.cookies)
print("z-way cookie: ", r.cookies["ZWAYSession"])

cookies = {"ZWAYSession": r.cookies["ZWAYSession"]}
headers = {'Content-Type': 'application/json'}
url = "http://192.168.0.15:8083/ZWaveAPI/Data/1441838249"
r = requests.get(url, headers=headers, cookies=cookies)
#r = requests.get(url, headers=headers)
print("text: ", r.text)
print("json: ", r.json())
