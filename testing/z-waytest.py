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

lookAt = [{"device": "15",
           "commandClass": "48"}]

doStop = False
include = False
exclude = False
including = False
excluding = False

print "Commands: "
print "    start include: i"
print "    stop inc:lude: s"
print "    start exclude: e"
print "    stop exclude:  x"
print "    quit:          q"
def getCmd():
    global doStop, include, exclude
    while not doStop:
        cmd = raw_input("> ")
        if cmd == "q":
            doStop = True
        elif cmd == "i":
            include = True
        elif cmd == "s":
            include - False
        elif cmd == "e":
            exclude = True
        elif cmd == "x":
            exclude = False
        else:
            print "Unrecognised command: ", cmd

thread.start_new_thread(getCmd, ())

baseUrl = "http://" + ipAddress + ":" + port +"/"
dataUrl = baseUrl + 'ZWaveAPI/Data/'
startIncludeUrl = baseUrl + "/ZWaveAPI/Run/controller.AddNodeToNetwork(1)"
stopIncludeUrl = baseUrl + "/ZWaveAPI/Run/controller.AddNodeToNetwork(0)"
startExcludeUrl = baseUrl + "/ZWaveAPI/Run/controller.RemoveNodeFromNetwork(1)"
stopExcludeUrl = baseUrl + "/ZWaveAPI/Run/controller.RemoveNodeFromNetwork(0)"

fromTime = str(int(time.time()) - 1)
h = httplib2.Http()

while not doStop:
    URL = dataUrl + fromTime
    if include:
        if not including:
            including = True
            URL = startIncludeUrl
    elif including:
        including = False
        URL - stopIncludeUrl
    if exclude:
        if not excluding:
            excluding = True
            URL = startExcludeUrl
    elif excluding:
        excluding = False
        URL = stopExcludeUrl
    resp, content = h.request(URL,
                              'POST',
                              headers={'Content-Type': 'application/json'})

    #pprint(resp)
    dat = json.loads(content)
    #pprint(dat)
    if dat:
        if "controller.data.lastIncludedDevice" in dat:
            print "Include value: ", dat["controller.data.lastIncludedDevice"]["value"]
        if "controller.data.lastExcludedDevice" in dat:
            print "Exclude value: ", dat["controller.data.lastExcludedDevice"]["value"]
        if "updateTime" in dat:
            fromTime = str(dat["updateTime"])
            print "New fromTime: ", fromTime
        if "devices" in dat:
            print "Devices: "
            for d in dat["devices"].keys():
                print d
                if d != "1":
                    for k in dat["devices"][d].keys():
                        print "    key: ", k
                        for j in dat["devices"][d][k].keys():
                            print "        key: ", j
                            if j == "nodeInfoFrame":
                                print "            ", dat["devices"][d][k][j]
                            elif j == "genericType":
                                print "            ", dat["devices"][d][k][j]
                            elif j == "specificType":
                                print "            ", dat["devices"][d][k][j]
                            elif j == "manufacturerId":
                                print "            ", dat["devices"][d][k][j]
                            elif j == "deviceTypeString":
                                print "            ", dat["devices"][d][k][j]
                            elif j == "manufacturerProductType":
                                print "            ", dat["devices"][d][k][j]
    time.sleep(2)

