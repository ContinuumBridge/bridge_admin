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

def warehouse_ifx(bid, db):
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
    oneDay = 60*60*24
    yesterday = today() - oneDay

    if not bid or not db:
        print "You must provide a bridge ID and a database"
        exit()
    else: 
        # Unlike geras, Influx doesn't return a series if there are no points in the selected range
        # so it's best to fetch data from before you need it.
        #q = "select * from /" + bid + "/ WHERE time > " + str(yesterday*1000) # Seems to fetch everything!
        q = "select * from /" + bid + "/ WHERE time > now() - 2d" 
        query = urllib.urlencode ({'q':q})
    
        print "Requesting data from", query
        url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
        print "fetching from:", url
        r = requests.get(url)
        pts = r.json()     
        # print "We got:", json.dumps(pts, indent=4)

        cutList = []
        for p in pts:
            if "hot_drinks" in p["name"].lower() or "night_start" in p["name"].lower() or "night_end" in p["name"].lower() or "wander_count" in p["name"].lower() or bid.lower()+"/kettle" in p["name"].lower():
                if not "connected" in p["name"].lower() and not "power" in p["name"].lower() and not "binary" in p["name"].lower(): 
                    cutList.append(p)

        for q in cutList:
            print "We got:", q["name"]                    
        #print "We got:", json.dumps(cutList, indent=4)                    
    
    if not cutList:
        print "no data. Exit..."
        exit()
    
    # csv fields
    Date = nicetime(yesterday)
    Bridge = bid
    NightStart = "null"
    NightEnd = "null"
    NightWanderCount = -1
    KettleCount = 0
    HotDrinkCount = 0
 
    for series in cutList:
        #print "Looking at:", json.dumps(series, indent=4)                    
        for p in series["points"]:
            #print "p:", p
            # trim it to the required times
            if p[0]/1000 >= yesterday and p[0]/1000 <= yesterday + oneDay:
                if "night_end" in series["name"]:
                    print "night_end:", nicetime(p[2]/1000)
                    NightEnd = nicehours(p[2]/1000)
                elif "night_start" in series["name"]:
                    print "night_start:", nicetime(p[2]/1000)
                    NightStart = nicehours(p[2]/1000)
                elif "wander_count" in series["name"]:
                    print "wander_count =", p[2]
                    NightWanderCount = p[2]
                elif "kettle" in series["name"].lower() and p[2] == 1:
                    KettleCount += 1
                elif "hot_drinks" in series["name"].lower() and p[2] == 1:
                    HotDrinkCount += 1
                else:
                    print "Error: no data found"

    print "KettleCount = ", KettleCount
    print "HotDrinkCount = ", HotDrinkCount

    notes = "Unique night wanders are in 10 minute intervals. Hot drink requires kettle plus fridge/coffee cupboard"
    headers = "24 Hours from,Bridge,NightStart,NightEnd,NightWanderCount,KettleCount,HotDrinkCount,Notes\n"
    firstRow = [Date, bid, NightStart, NightEnd, str(NightWanderCount), str(KettleCount), str(HotDrinkCount),notes]
    print "firstRow:", firstRow
    fr = ', '.join(firstRow)
    file = bid + ".csv"
    f = open(file, 'wb')
    f.write(headers)
    f.write(fr)
               
if __name__ == '__main__':
    warehouse_ifx()
