#!/usr/bin/env python
# uwe_example.py
# Copyright (C) ContinuumBridge Limited, 2013 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#
import httplib2
from datetime import datetime
import json
import time
from pprint import pprint
import sys
import thread

ipAddress = 'localhost'
port = "8083"

doStop = False

def getCmd():
    global doStop
    cmd = raw_input("Press return to stop")
    doStop = True
    return True

thread.start_new_thread(getCmd, ())

baseUrl = "http://" + ipAddress + ":" + port +"/"
dataUrl = baseUrl + 'ZWaveAPI/Data/'

while not doStop:
    now = int(time.time())
    fromTime = str(now - 1)
    URL = dataUrl + fromTime
    start = time.time()
    h = httplib2.Http()
    resp, content = h.request(URL,
                              'POST',
                              headers={'Content-Type': 'application/json'})

    #print "Time taken: ", start - time.time()
    #pprint(resp)
    dat = json.loads(content)
    #pprint(dat)
    time.sleep(1)

