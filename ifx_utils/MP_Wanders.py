#!/usr/bin/env python
# warehouse_ifx.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#
# Usage:-
# ./warehouse_ifx.py --bid "BID11" --db "Bridges"

import requests
import json
import time
import click
import os, sys
import re
import smtplib
from itertools import cycle
import urllib

#Constants
oneHour            = 60 * 60
oneDay             = oneHour * 24
dburl = "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/"

def nicetime(timeStamp):
    localtime = time.localtime(timeStamp)
    now = time.strftime('%Y-%m-%d %H:%M:%S', localtime)
    return now

def nicedate(timeStamp):
    localtime = time.localtime(timeStamp)
    now = time.strftime('%Y-%m-%d', localtime)
    return now

def nicehours(timeStamp):
    localtime = time.localtime(timeStamp)
    now = time.strftime('%H:%M:%S', localtime)
    return now

def stepHourMin(timeStamp):
    localtime = time.localtime(timeStamp)
    now = time.strftime('%H%M', localtime)
    return now

def epochtime(date_time):
    pattern = '%Y-%m-%d %H:%M:%S'
    epoch = int(time.mktime(time.strptime(date_time, pattern)))
    return epoch

def today():
    t = time.localtime(time.time())
    now = time.strftime('%Y-%m-%d', t)
    s = now + " 12:00:00"    
    return epochtime(s)

@click.command()
@click.option('--bid', nargs=1, help='The bridge ID.')
@click.option('--db', nargs=1, help='The database to look in')

def MP_Wanders(bid, db):
    night_start = 23 # i.e. 23:00
    night_end = 6 # i.e. 6am.
    night_ignore_time = 10*60 # 10mins
    """ 
    We get:-
    [
    {
        "points": [
            [
                1427193906669, 
                15927010001, 
                50
            ], 
            [
                1427116355288, 
                15798620001, 
                0
            ]
        ], 
        "name": "BID36/Back_Door/answered_door", 
        "columns": [
            "time", 
            "sequence_number", 
            "value"
        ]
    }           

    """

    if not bid or not db:
        print "You must provide a bridge ID and a database"
        exit()
    else: 
        q = "select * from /" + bid + ".*binary/" # limit 5000"
        query = urllib.urlencode ({'q':q})
    
        print "Requesting data from BID", bid
        url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
        print "fetching from:", url
        r = requests.get(url)
        pts = r.json()     
        
    time_index = 0
    value_index = 2
    wanderTimes = []
    realWanderTimes = []
    for t in pts:
        if ("outside" not in t["name"].lower()): # and "kitchen_pir" in t["name"].lower()):
            for p in t["points"]:
                ti = time.localtime(p[time_index]/1000)
                #print "ti[3]:", ti[3]
                if p[value_index] == 1 and (ti[3] == night_start or ti[3] < night_end):
                    wanderTimes.append(p[time_index]/1000)
                    #print "***Wander on", t["name"], "at",nicetime(p[time_index]/1000) #, "on",nicedate(p[time_index]/1000)

    # ug, now we need them in time order to implement night_ignore_time
    wanderTimes.sort()
    firstWanderTime = wanderTimes[0]
    firstWanderDate = time.strftime("%Y %b %d %H:%M", time.localtime(wanderTimes[0])).split()
    firstWanderDate[3] = "00:00"
    firstWanderDate_epoch = time.mktime(time.strptime(" ".join(firstWanderDate), "%Y %b %d %H:%M"))

    print "firstWander is:", nicetime(firstWanderTime)

    # implement night_ignore_time
    for wt in wanderTimes: # hopefully sequential!
        #print "next wt:", nicetime(wt)
        if wt == firstWanderTime:
            realWanderTimes.append(wt)
        elif wt > firstWanderTime + night_ignore_time:
            firstWanderTime = wt # it's a new wander
            realWanderTimes.append(wt)
            #print "**new wander at:", nicetime(wt)
        # else: part of same wander       

    #for wt in realWanderTimes: # hopefully sequential!
    #    print "sorted real wandertimes:", nicetime(wt)

    # debounce the switches back into the original list
    wanderTimes = []
    prev_wt = 0
    for wt in realWanderTimes: # hopefully sequential!
        if wt != prev_wt:
            wanderTimes.append(wt)
            prev_wt = wt
        
    #for wt in wanderTimes: # hopefully sequential!
    #    print "remaining wandertimes:", nicetime(wt)

  
    day = firstWanderDate_epoch
    wc = 0
    wander_counts = []
    headers = "Time, Wanders"
    f = bid + ".csv"
    with open(f, 'w') as outfile:
        outfile.write(headers + '\n')   
        while day <= today():
            for wt in wanderTimes:
                if wt > day and wt < (day + oneDay):
                    wc += 1
                    #print "adding", nicetime(wt), "to wander counts on", nicetime(day)
            wander_counts.append({"date":nicetime(day),"count":wc})
            day += oneDay
            wc = 0

        for j in wander_counts:
            print "adding Wander counts to file:", j
            line = str(j["date"]) + "," + str(j["count"]) + "\n"
            outfile.write(line)

    #print "wander_counts:", json.dumps(wander_counts, indent=4)            

                     
if __name__ == '__main__':
    MP_Wanders()

