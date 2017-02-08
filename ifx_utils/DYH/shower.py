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
                bathroomSeries.append({"time":pt[0],  "name": item["name"], "value": pt[2]})
        bathroomSeries.sort(key=operator.itemgetter('time'))
        #print "bS:", json.dumps(bathroomSeries,indent=4)
	
        showerStart = 0
        showerWindow = 30*oneMinute*1000
        for s in sensorList:
            print "next s", s
            prevJ = 0
            prevH = 0
            prevT = 0
            startT = 0
            checking = False
            startH = 0
            deltaT = 1
            deltaJ = 0.0
            gradH = 0.0
            prevG = 0.0
            showerDebug = False
            for j in bathroomSeries:
                if s in j["name"]:
                    if j <> prevJ:
                        if "binary" in j["name"].lower() and j["value"] == 1:
                            showerStart = j["time"]
                            #print nicetime(j["time"]/1000), s, "is occupied", "on", j["name"]
                
                        if "humidity" in j["name"]: # and j["time"] < showerStart + showerWindow:
                            if prevH <> 0:
                                if showerDebug:
                                    print nicetime(j["time"]/1000),"H:", j["value"] 
                                deltaT = (j["time"] - prevT)
                                deltaH = j["value"] - prevH
                                gradH = 100000.0*deltaH/deltaT
                                if gradH>0.02:
                                    if showerDebug:
                                        print "grad=", gradH
                                #if gradH > 0.5: 
                                    #print nicetime(j["time"]/1000),"Humidity gone up by", j["value"] - prevH, "to", j["value"], "in", (j["time"]-prevT)/1000, "seconds, G:", gradH 
                                    prevG = gradH
                                    if not checking:
                                        startT = prevT 
                                        startH = prevH
                                        if showerDebug:
                                            print nicetime(j["time"]/1000),"   Started Checking from", nicetime(startT/1000), "thisH:", j["value"], "prev:", prevH
                                    checking = True
                                else:
                                    #print s, nicetime(j["time"]/1000),"Humidity gone down by", j["value"] - prevH, "in", (j["time"]-prevT)/1000, "seconds"
                                    if checking:
                                        if showerDebug:
                                            print nicetime(j["time"]/1000), "   end of checking - humidity went up by", prevH - startH, "in", (prevT - startT)/1000/60, "minutes"
                                        if prevG>1.1 or ((prevH-startH) >= 9 and (prevT-startT) < 45*oneMinute*1000):
                                            print  nicetime(j["time"]/1000), "*** Shower at", nicetime(startT/1000)
                                    checking = False
                                """
                                if j["value"] > prevH: # less than 2 is noise
                                    if j["value"] - prevH <=2 and j["time"]-prevT > 10*oneMinute*1000:
                                        print s, nicetime(j["time"]/1000),"Humidity only gone up by", j["value"] - prevH, "to", j["value"], "in", (j["time"]-prevT)/1000, "seconds - ignoring"
                                    else:
                                        if not checking:
                                            startT = prevT 
                                            startH = prevH
                                            print s, nicetime(j["time"]/1000), "startH:", startH, "startT", nicetime(startT/1000)
                                        checking = True
                                """
                            prevH = j["value"]
                            prevT = j["time"]

                prevJ = j
            #else:
            #    print "ignoring duplicate at:", nicetime(j["time"]/1000), j["time"], j["value"], j["name"]
           

                  
if __name__ == '__main__':
    shower()

