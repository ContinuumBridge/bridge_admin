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
    s = yesterday + " 06:00:00"
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
    daysAgo = int(daysago) #0 # 0 means yesterday
    startTime = start() - oneDay - daysAgo*60*60*24
    endTime = startTime + oneDay

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
        print "Requesting list of series from", nicetime(startTime), "to", nicetime(endTime)
        url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
        print "fetching from:", url
        r = requests.get(url)
        pts = r.json()
        #print json.dumps(r.json(), indent=4)
    
        selectedSeries = []
        bathroomSeries = []
        prevItem = 0
        for series in pts:
            if "bathroom" in series["name"].lower() and "wander" not in series["name"].lower() and "battery" not in series["name"].lower() and "connected" not in series["name"].lower(): 
               selectedSeries.append(series)
        for item in selectedSeries:
            for pt in item["points"]:
                bathroomSeries.append({"time":pt[0],  "name": item["name"], "value": pt[2]})


        bathroomSeries.sort(key=operator.itemgetter('time'))
        #print "bS:", json.dumps(bathroomSeries,indent=4)
	
        showerStart = 0
        showerWindow = 20*oneMinute
        prevJ = 0
        showerTaken = False
        showerTimes =[] 
        for j in bathroomSeries:
            if j == prevJ:
                print "ignoring duplicate at:", nicetime(j["time"]/1000), j["time"], j["value"], j["name"]
            else:
                if "binary" in j["name"] and j["value"] == 1 and j["time"] > showerStart: # + showerWindow*1000: # door or PIR
                    print "NextJ:", nicetime(j["time"]/1000), j["value"], "on", j["name"]
                    firstLoop = True
                    showerStart = j["time"]
                    prevH = 0
                    prevK = 0
                    prevT = 0
                    humGrad = 0.0
                    for k in bathroomSeries:
                        if "humidity" in k["name"] and k["time"] >= showerStart and k["time"] <= showerStart + showerWindow*1000: # and not showerTaken:
                            print "  NextHK:", nicetime(k["time"]/1000), k["value"], "on", k["name"]
                            if k <> prevK:
                                #print "   ", nicetime(k["time"]/1000),"Humidity values this:", k["value"], "prev:", prevH
                                if not firstLoop:
                                    humGrad = 100000*(k["value"] - prevH)/float(k["time"] - prevT)
                                    #print "      ", nicetime(k["time"]/1000), "change is:", k["value"] - prevH, "over", k["time"]/1000 - prevT/1000 , "seconds"
                                    if humGrad > 2.0:
                                        #showerTaken = True
                                        #print "Upgrad=", humGrad
                                        showerTimes.append(k["time"]) 
                                        print "** Shower at:", nicehours(k["time"]/1000), "moving start from", nicehours(showerStart/1000), "to", nicehours((showerStart + showerWindow*1000)/1000)
                                        showerStart = showerStart + showerWindow*1000
                                firstLoop = False
                                prevH = k["value"]
                                prevT = k["time"]
                                prevK = k
        #for m in showerTimes:
        #    print "Showers:", nicetime(m/1000)


            prevJ = j
           

                  
if __name__ == '__main__':
    shower()

