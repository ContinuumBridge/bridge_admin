#!/usr/bin/env python
# backup_geras_by_series.py
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
@click.option('--folder', nargs=1, help='The absolute path')
def backup_by_series(db, folder):

    allseries=[]
    bidList = []

    q = "select * from /.*/ limit 1"
    query = urllib.urlencode ({'q':q})
    
    print "Requesting data from db", db
    url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
    print "fetching from:", url
    r = requests.get(url)
    pts = r.json()     
    for s in pts:
        ss = re.split('\W+|/|-',s["name"])                    
        if "BID" in ss[0]:
            if ss[0] not in bidList:
                bidList.append(ss[0])
        else:
            print "rejected:", ss

    print "going to do", json.dumps(bidList, indent=4)


    for bid in bidList:
        allseries = []
        q = "select * from /" + bid + ".*/" # limit 5"
        query = urllib.urlencode ({'q':q})
        print "Requesting data for", bid
        url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
        print "fetching from:", url
        r = requests.get(url)
        pts = r.json()     
        for s in pts:
            allseries.append(s["name"])
        
  
        print "Backing up:"
        print (json.dumps(allseries, indent=4))            
    
        now = time.strftime('%Y-%m-%d_', time.localtime())
    
        for s in pts:
            f = folder + "/" + now + db + "/" + s["name"] + ".txt"
            #print "writing:", json.dumps(s, indent=4), "to", f
            if not os.path.exists(os.path.dirname(f)):
                os.makedirs(os.path.dirname(f))            
            with open(f, 'w') as outfile:
                json.dump(s, outfile)
            print "    Written:", len(s["points"]), "items to", f

if __name__ == '__main__':
    backup_by_series()

