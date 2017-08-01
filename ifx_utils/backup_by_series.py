#!/usr/bin/env python
# backup_by_series.py
# Copyright (C) ContinuumBridge Limited, 2015 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#

import requests
import json
import time
import click
import os, sys
import re
from itertools import cycle
import urllib

def nicedate(timeStamp):
    localtime = time.localtime(timeStamp)
    now = time.strftime('%Y-%m-%d', localtime)
    return now

dburl = "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/"

@click.command()
@click.option('--db', nargs=1, help='The database')
@click.option('--bid', nargs=1, help='The bridge (all bridges if empty)')
@click.option('--folder', nargs=1, help='The absolute path')
def backup_by_series(db, folder, bid):

    allSeries=[]

    if bid:
	q = "select * from /" + bid + "/ limit 1"
    else:
	q = "select * from /.*/ limit 1"
    query = urllib.urlencode ({'q':q})
    
    print "Requesting data from db", db
    url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
    print "fetching from:", url
    r = requests.get(url)
    pts = r.json()     
    for s in pts:
        if "BID" in s["name"]:
            allSeries.append(s["name"])

    print "going to do series", json.dumps(allSeries, indent=4)
    for s in allSeries:
        q = 'select * from "' + s + '"' # limit 5'
        query = urllib.urlencode ({'q':q})
        #print "Requesting data for", query
        url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
        #print "fetching from:", url
        try:
            r = requests.get(url)
            pts = r.json()     
        except:
            print "Fetch failed"
            exit()        

        now = time.strftime('%Y-%m-%d_', time.localtime())
        for m in pts:
            f = folder + "/" + now + db + "/" + m["name"] + ".txt"
            #print "writing:", json.dumps(m, indent=4), "to", f
            if not os.path.exists(os.path.dirname(f)):
                os.makedirs(os.path.dirname(f))            
            with open(f, 'w') as outfile:
                json.dump(m, outfile)
            print "Written:", len(m["points"]), "items to", f

if __name__ == '__main__':
    backup_by_series()

