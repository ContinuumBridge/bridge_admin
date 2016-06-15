#!/usr/bin/env python
# warehouse_ifx.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#
# Usage:-
# ./warehouse_ifx.py --bid "BID11" "BID12" "" --db "Bridges"
# N.B. 3 bridge args so pad with "" to do fewer

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
csvPath = "WarehouseData/"  # /home/martin/Dropbox/" #/Bridge Logs/WarehouseData/"

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
@click.option('--bids', nargs=3, help='The bridge IDs in a list.')
@click.option('--db', nargs=1, help='The database to look in')
@click.option('--daysago', nargs=1, help='how many days ago to process')

def warehouse_ifx(bids, db, daysago):
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
    #daysAgo = 1 
    oneDay = 60*60*24
    startDay = today() - int(daysago)*oneDay

    if not bids or not db:
        print "You must provide a bridge ID and a database"
        exit()

    rowCount = 0
    notes = ["Unique night wanders are in 10 minute intervals.\n", "Hot drink requires kettle plus fridge/coffee cupboard.\n"]
    headers = "24 Hours from,Bridge,NightStart,NightEnd,NightWanderTime,NightWanderSensor,NightWanderCount,KettleCount,HotDrinkCount,Notes\n"
    file = csvPath + nicedate(startDay) + "_SCH.csv"
    try:
        f = open(file, 'wb')
        f.write(headers)
    except:
        print "failed to write"

    for bid in bids: 
        if not bid:
            continue
        rowCount = 0

        # Unlike geras, Influx doesn't return a series if there are no points in the selected range
        # so it's best to fetch data from before you need it. Hence minus (daysago+2) below.
        # And we're having to fetch data relative to now() so make it (daysago+3) to be sure to get all the relevant
        # data whatever time we're run.
        #q = "select * from /" + bid + "/ WHERE time > " + str(startDay*1000) # Seems to fetch everything!
        #q = "select * from /" + bid + "/ WHERE time > now() - 2d" 
        q = "select * from /" + bid + "/ WHERE time > now() - " + str(int(daysago)+3) +"d"
        query = urllib.urlencode ({'q':q})
    
        print "Doing bid:", bid, "Requesting data from", query
        url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
        #print "fetching from:", url
        r = requests.get(url)
        pts = r.json()     
        #print "We got:", json.dumps(pts, indent=4)

        cutList = []
        for p in pts:
            if "hot_drinks" in p["name"].lower() or "night_start" in p["name"].lower() or "night_end" in p["name"].lower() or "wander" in p["name"].lower() or bid.lower()+"/kettle" in p["name"].lower():
                if not "connected" in p["name"].lower() and not "power" in p["name"].lower() and not "binary" in p["name"].lower(): 
                    cutList.append(p)

        #for q in cutList:
            #print "cutList:", q["name"]                    
        #print "We got:", json.dumps(cutList, indent=4)                    

        # csv columns
        Date = nicetime(startDay)
        Bridge = bid
        NightStart = "null"
        NightEnd = "null"
        NightWanderCount = -1
        KettleCount = -1
        HotDrinkCount = -1
        wanders = []

        prevSensor = "foo" 
        prevWandertime = 0

        for series in cutList:
            #print "Looking at:", json.dumps(series, indent=4)                    
            for p in series["points"]:
                # trim it to the required times
                if p[0]/1000 >= startDay and p[0]/1000 <= startDay + oneDay:
                    if "night_end" in series["name"]:
                        #print "night_end:", nicetime(p[2]/1000)
                        NightEnd = nicehours(p[2]/1000)
                    elif "night_start" in series["name"]:
                        #print "night_start:", nicetime(p[2]/1000)
                        NightStart = nicehours(p[2]/1000)
                    elif "wander_count" in series["name"]:
                        print "wander_count =", p[2]
                        NightWanderCount = p[2]
                    elif "kettle" in series["name"].lower() and p[2] == 1:
                        if KettleCount == -1:
                            KettleCount = 1
                        else:
                            KettleCount += 1
                    elif "hot_drinks" in series["name"].lower() and p[2] == 1:
                        if HotDrinkCount == -1:
                            HotDrinkCount = 1
                        else:
                            HotDrinkCount += 1
                    elif "night_wander" in series["name"].lower():
                        ss = series["name"].split('/')
                        #print "wander at", nicetime(p[0]/1000), "on:", ss[2] # series["name"]
                        w = [p[0], ss[2]]
                        if not (ss[2] == prevSensor and abs(p[0] - prevWandertime) < 2*60*1000):
                            wanders.append(w)
                            rowCount += 1
                            prevSensor = ss[2]
                            prevWandertime = p[0]
                        #else:
                            #print "   discarding wander on:", ss[2], "because it was", (p[0] - prevWandertime)/1000, "seconds ago"

                    else:
                        print "Error: no data found for", bid

        sw = sorted(wanders, key=lambda ttt: ttt[0])
        #print "sorted Wanders:", json.dumps(sw, indent=4)
        print "KettleCount = ", KettleCount
        print "HotDrinkCount = ", HotDrinkCount
        """        
        if rowCount > len(notes):
            row = [Date, bid, NightStart, NightEnd, str(NightWanderCount), str(KettleCount), str(HotDrinkCount)]
        else:
        """         
        if rowCount == 0:
            row = [Date, bid, NightStart, NightEnd, "none", "none", str(NightWanderCount), str(KettleCount), str(HotDrinkCount), '\n']
            #print "Row:", row
            fr = ', '.join(row)
            f.write(fr)
        else:
            for i in range(0,rowCount):
                row = [Date, bid, NightStart, NightEnd, nicehours(sw[i][0]/1000), sw[i][1], str(NightWanderCount), str(KettleCount), str(HotDrinkCount), '\n']
                #print "Row:", row
                fr = ', '.join(row)
                f.write(fr)

               
if __name__ == '__main__':
    warehouse_ifx()
