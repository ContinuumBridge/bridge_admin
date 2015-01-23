#!/usr/bin/env python
# latest_data.py
# Copyright (C) ContinuumBridge Limited, 2015 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#

gerasurl = 'http://geras.1248.io/'
import requests
import json
import time
import click
import os, sys
import re
import smtplib
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
@click.option('--key', prompt='Geras API key', help='Your Geras API key. See http://geras.1248.io/user/apidoc.')
@click.option('--bid', nargs=1, help='The bridge ID to check.')

def latest_data (key, bid):
    allBridges = 0
    if not bid:
        print "No BID specified - checking all"
        allBridges = 1
    
    r = requests.get('http://geras.1248.io/serieslist', auth=(key,''))
    allseries = json.loads(r.content)
    serieslist = []
    if allBridges:
        for t in allseries:
            serieslist.append(t)
    else:
        for t in allseries:
            if (bid+"/") in t:
                serieslist.append(t)


    b = {}
    oneDay = 60*60*24
    t = time.localtime(time.time())
    s = time.strftime('%Y-%m-%d %H:%M:%S', t)
    now = epochtime(s)

    latest = 0
    last_ss = 0   
    for s in serieslist:
        ss = s.split('/')
        if ss[1] <> last_ss:
            age = now - int(float(latest))
            if last_ss <> 0:
                if age > 2*7*oneDay: 
                    print "****", last_ss, "not heard from since:", nicetime(float(latest)), "**** more than two weeks"
                elif age > 7*oneDay: 
                    print "*** ", last_ss, "not heard from since:", nicetime(float(latest)), "***  more than a week"          
                elif age > oneDay/2: # shoud get a couple of battery values in 12hrs
                    print "**  ", last_ss, "not heard from since:", nicetime(float(latest)), "**   more than 12 hours <-- probably the ones to check"          
                #else:
                    #print "    ", last_ss, "heard from today", nicetime(float(latest))
            last_ss = ss[1]
            latest = 0

        url = gerasurl + 'now' + s
        r = requests.get(url, auth=(key,''))
        b = json.loads(r.content)        
        b1 = b["e"][0]
        days_since_seen = (now - int(float(b1['t'])))/oneDay
        if allBridges == 0:
            if days_since_seen ==0:
                print nicetime(float(b1['t'])), "( ", days_since_seen, "days ago) is latest data for", s 
            else:
                print nicetime(float(b1['t'])), "(*", days_since_seen, "days ago) is latest data for", s 

        if b1['t'] > latest:
            latest = b1['t']
            #print "updated latest for", ss[1], "to", nicetime(float(b1['t']))
                    
if __name__ == '__main__':
    latest_data()

