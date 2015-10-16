#!/usr/bin/env python

import requests
url = "http://192.168.1.1/html/deviceinformation.html"
headers = {'Content-Type': 'application/json'}
status = 0
r = requests.get(url)
print "status: ", r.status_code
print "text: ", r.text

