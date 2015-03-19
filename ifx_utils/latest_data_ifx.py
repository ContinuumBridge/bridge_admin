#!/usr/bin/env python
# latest_data.py
# Copyright (C) ContinuumBridge Limited, 2015 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#

dburl = "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/"
import requests
import json
import time
import click
import os, sys
import re
import smtplib
import urllib
from itertools import cycle

def nicetime(timeStamp):
    localtime = time.localtime(timeStamp)
    now = time.strftime('%Y-%m-%d %H:%M:%S', localtime)
    return now

def epochtime(date_time):
    pattern = '%Y-%m-%d %H:%M:%S'
    epoch = int(time.mktime(time.strptime(date_time, pattern)))
    return epoch

@click.command()
@click.option('--bid', nargs=1, help='The bridge ID to check.')

def latest_data (bid):
    allBridges = 0
    if not bid:
        print "No BID specified - checking all"
        allBridges = 1
        query = urllib.urlencode ({'q':'select * from /BID*/ limit 1'})
    else:
        q = "select * from /" + bid + "/ limit 1"
        query = urllib.urlencode ({'q':q})

    url = dburl + "db/Bridges/series?u=root&p=27ff25609da60f2d&" + query 
    print "fetching from:", url
    r = requests.get(url) # ,params=list+series)
    latestPoints = r.json()
    print json.dumps(r.json(), indent=4)
    #print json.dumps(r.content, indent=4)

    oneDay = 60*60*24
    t = time.localtime(time.time())
    s = time.strftime('%Y-%m-%d %H:%M:%S', t)
    now = epochtime(s)
    
    for i in range(0,len(latestPoints)):
        #print "latest for", latestPoints[i]["name"], "is", nicetime(latestPoints[i]["points"][0][0]/1000)
        latest_time = latestPoints[i]["points"][0][0]/1000
        age = now - latest_time 
        if age > 2*7*oneDay: 
            print "****", latestPoints[i]["name"], "not heard from since:", nicetime(latest_time), "****", age/oneDay,"days"
        elif age > 7*oneDay: 
            print "*** ", latestPoints[i]["name"], "not heard from since:", nicetime(latest_time), "****", age/oneDay,"days"
        elif age > oneDay/2: # shoud get a couple of battery values in 12hrs
            print "**  ", latestPoints[i]["name"], "not heard from since:", nicetime(latest_time), "**  more than 12 hours <-- probably the ones to check"
        else:
            print "    ", latestPoints[i]["name"], "heard from today"
    
                        
if __name__ == '__main__':
    latest_data()

