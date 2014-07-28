#!/usr/bin/env python
# gerastest.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#
import httplib2
import urllib
from datetime import datetime
import json
import time
from pprint import pprint
import sys

h = httplib2.Http(".cache")
h.add_credentials('ea2f0e06ff8123b7f46f77a3a451731a', '')

url = "http://geras.1248.io/serieslist"
response, content = h.request(url, 'GET')
pprint(response)
try:
    print content
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

response, content = h.request(url, 'POST', headers=headers, body=urllib.urlencode(body))
pprint(response)
try:
    print content
except:
    print "No data returned"

