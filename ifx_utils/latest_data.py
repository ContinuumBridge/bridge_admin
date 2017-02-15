#!/usr/bin/env python
# latest_data_ifx.py
# Copyright (C) ContinuumBridge Limited, 2017 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#
# Checks for the latest data from bridges in databases.
# Parameters are bid and db
#
import requests
import json
import time
import click
import os, sys
import re
import smtplib
import operator
import urllib
from itertools import cycle

def nicetime(timeStamp):
    localtime = time.localtime(timeStamp)
    now = time.strftime('%Y-%m-%d %H:%M:%S', localtime)
    return now

def nicedate(timeStamp):
    localtime = time.localtime(timeStamp)
    now = time.strftime('%Y-%m-%d', localtime)
    return now

def epochtime(date_time):
    pattern = '%Y-%m-%d %H:%M:%S'
    epoch = int(time.mktime(time.strptime(date_time, pattern)))
    return epoch

dburl = "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/"
@click.command()
@click.option('--bid', nargs=1, help='The bridge ID to check.')
@click.option('--db', nargs=1, help='The name of the influx database.')

def batteries (bid, db):
    if not bid:
        print "No BID specified - can't continue"
        exit()
        #query = urllib.urlencode ({'q':'select * from /BID*/ limit 1'})
    else:
        q = "select * from /" + bid + "/ limit 1"
        query = urllib.urlencode ({'q':q})

    oneDay = 60*60*24
    t = time.localtime(time.time())
    s = time.strftime('%Y-%m-%d %H:%M:%S', t)
    now = epochtime(s)
    latestPoints = []
    
    url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
    print "fetching from:", url
    try:
        r = requests.get(url) # ,params=list+series)
        latestPoints = r.json()
    except:
        print "****No data found in the", db, "database. Probably", bid, "isn't in there****"
        return #exit()
    #print json.dumps(r.json(), indent=4)
    #print json.dumps(latestPoints, indent=4)    
    #print json.dumps(r.content, indent=4)
    latestTime = 0
    latestValue = 0
    values = []
    for i in latestPoints:
        #if "battery" in i["name"]:
        latestTime = i["points"][0][0]
        latestValue = i["points"][0][2]
        values.append({"time":latestTime, "value":latestValue, "name":i["name"]})

    values.sort(key=operator.itemgetter('time'))
    line = ""
    for j in values:
        line = '{:<15} {:<15} {:<16} {:<2} {:<15}'.format(nicetime(j["time"]/1000), "latest data was", j["value"], "on", j["name"]) 
        print line
        #print "On", nicetime(j["time"]/1000), "latest data was", j["value"], "on", j["name"] 


    
if __name__ == '__main__':
    batteries()

