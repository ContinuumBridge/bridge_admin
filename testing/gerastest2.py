#!/usr/bin/env python
# gerastest.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import json
import time
from pprint import pprint
import sys

user = "ea2f0e06ff8123b7f46f77a3a451731a"
url = "http://geras.1248.io/serieslist"
r = requests.get(url, auth=(user, ''))
print "Status code: ", r.status_code
print "Headers:"
print r.headers
try:
    print "Text fron response:"
    print r.text
    print "JSON fron response:"
    print r.json
except:
    print "No data returned"

url = "http://geras.1248.io/series/testbridge"
headers={'Content-Type': 'application/json'}
body= {
       "e":[
           {"n":"temperature", "v":28.5, "t":1406553258},
           {"n":"temperature", "v":29.0, "t":1406554258},
           {"n":"temperature", "v":29.5, "t":1406554528},
           {"n":"temperature", "v":30.0, "t":1406555528},
           {"n":"light", "v":150, "t":1406553258},
           {"n":"light", "v":250, "t":1406554258}
       ]
      }
r = requests.post(url, auth=(user, ''), data=json.dumps(body), headers=headers)
print "Status code: ", r.status_code
print "Headers:"
print r.headers
