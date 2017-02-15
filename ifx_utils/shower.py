#!/usr/bin/env python
# room_occupancy.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#
# Usage:-
# ./shower.py --user bridges@continuumbridge.com --bid BID36 --db "SCH" --daysago 5 

import requests
import json
import time
import click
import os, sys
import re
import smtplib
import operator
import operator
from itertools import cycle
import urllib

#Constants
oneMinute          = 60
oneHour            = 60 * oneMinute
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
    #now = time.strftime('%H:%M:%S', localtime)
    now = time.strftime('%H:%M', localtime)
    return now

def epochtime(date_time):
    pattern = '%Y-%m-%d %H:%M:%S'
    epoch = int(time.mktime(time.strptime(date_time, pattern)))
    return epoch

def start():
    t = time.localtime(time.time() - oneDay)
    yesterday = time.strftime('%Y-%m-%d', t)
    s = yesterday + " 05:00:00" # 5am for early risers!
    return epochtime(s)

def getwander (ss):
    ss = ss.split("/")            
    jj = ss[2].replace("_PIR","")
    jj = jj.replace("_"," ")
    return jj
def getsensor (ss):
    ss = ss.split("/")            
    jj = ss[1].replace("_PIR","")
    return jj

@click.command()
@click.option('--bid', nargs=1, help='The bridge ID to list.')
@click.option('--db', nargs=1, help='The database to look in')
@click.option('--daysago', nargs=1, help='How far back to look')

def shower (bid, db, daysago):
    daysAgo = int(daysago)*60*60*24 
    startTime = start() - daysAgo
    endTime = startTime + daysAgo + oneDay

    print "start time:", nicetime(startTime)
    print "end time:", nicetime(endTime)
 
    if not bid:
        print "You must provide a bridge ID using the --bid option."
        exit()
    else:
        # Unlike geras, Influx doesn't return a series if there are no points in the selected range
        # So we'd miss dead sensors
        # So we'll ask for 1 day before startTime on the grounds that we'd always change a battery in that time      
        # select * from /BID11/ where time > 1427025600s and time < 1427112000s
        earlyStartTime = startTime - oneDay
        q = "select * from /" + bid + "/ where time >" + str(earlyStartTime) + "s and time <" + str(endTime) + "s"
        query = urllib.urlencode ({'q':q})
        print "Requesting list of series from", nicetime(earlyStartTime), "to", nicetime(endTime)
        url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
        print "fetching from:", url
        try:
            r = requests.get(url)
            pts = r.json()
        except:
            print "Fetch failed"
            exit()
    
        sensorList = []
        selectedSeries = []
        bathroomSeries = []
        prevItem = 0
        for series in pts:
            if "humidity" in series["name"].lower(): 
                if getsensor(series["name"]) not in sensorList:
                   sensorList.append(getsensor(series["name"]))
        print "sensorlist:", sensorList

        for s in sensorList:
            for series in pts:
                if s in series["name"]: 
                    selectedSeries.append(series)
        for item in selectedSeries:
            for pt in item["points"]:
                if pt[0] >= startTime*1000 and pt[0] <= endTime*1000:
                    bathroomSeries.append({"time":pt[0],  "name": item["name"], "value": pt[2]})
        bathroomSeries.sort(key=operator.itemgetter('time'))
        #print "bS:", json.dumps(bathroomSeries,indent=4)
	
        showerWindow = 41*oneMinute*1000
        shortShowerWindow = 13*oneMinute*1000
        for s in sensorList:
            print "next s", s
            prevJ = 0
            prevK = []
            prevH = 0
            prevT = 0
            noMoreShowersTillItFalls = False
            showerDebug = False
            for j in bathroomSeries:
                if s in j["name"]:
                    if j <> prevJ:
                        #if "binary" in j["name"].lower() and j["value"] == 1:

                        if "humidity" in j["name"]: 
                            if prevH <> 0 and j["value"] > prevH: 
                                #if showerDebug:
                                #    print nicetime(j["time"]/1000), "H Gone up by", j["value"]-prevH, "to", j["value"], "in", (j["time"] - prevT)/1000/60, "minutes" 
                                # every time it goes up, look ahead to see how far and how long
                                for k in bathroomSeries:
                                    if s in k["name"] and "humidity" in k["name"]:
                                        #print k["name"], k["value"]
                                        if (k <> prevK and k["time"] >= j["time"] 
                                            and k["time"] <= j["time"] + showerWindow 
                                            and k["value"] > prevK["value"]):
                                            #if showerDebug:
                                            #    print "   ", nicetime(k["time"]/1000), "K risen from", prevK["value"], "to", k["value"]
                                            # no good just looking at the end point 'cause that could be a long time in the future.
                                            # So if at any time during this process we get dh high enough and dt small enough...
                                            if k["value"] - prevH >= 8 and k["time"] - prevT < showerWindow and not noMoreShowersTillItFalls:
                                                print nicetime(prevT/1000), "** SHOWER1, dh:", k["value"] - prevH, "dt:",\
                                                    (k["time"] - prevT)/1000/60, "minutes"
                                                noMoreShowersTillItFalls = True
                                            elif k["value"] - prevH >= 6 and k["time"] - prevT <= shortShowerWindow and not noMoreShowersTillItFalls:
                                                print nicetime(prevT/1000), "** SHOWER2, dh:", k["value"] - prevH, "dt:",\
                                                    (k["time"] - prevT)/1000/60, "minutes"
                                                noMoreShowersTillItFalls = True
                                            elif k["value"] - prevH > 1 and showerDebug and not noMoreShowersTillItFalls and showerDebug:
                                                print nicetime(prevT/1000), "No shower. dh:", k["value"] - prevH, "dt:", (k["time"] - prevT)/1000/60, \
                                                    "minutes, nms:",noMoreShowersTillItFalls
                                    prevK = k
                            else: # it fell
                                noMoreShowersTillItFalls = False
                                #if showerDebug:
                                #    print nicetime(j["time"]/1000), "It fell to", j["value"]
                            prevT = j["time"]
                            prevH = j["value"]

                                
                  
if __name__ == '__main__':
    shower()

