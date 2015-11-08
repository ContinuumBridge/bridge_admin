#!/usr/bin/env python
# EEW_app_post.py
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
import time
import datetime
from itertools import cycle
import urllib

#Constants
oneHour            = 60 * 60
oneDay             = oneHour * 24
dburl = "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/"

startNight_e = 22*oneHour
endNight_e = 8*oneHour

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

def epochTimeOfDay(date_time):
    pattern = '%H:%M:%S'
    epoch = int(time.mktime(time.strptime(date_time, pattern)))
    return epoch

@click.command()
@click.option('--bid', nargs=1, help='The bridge ID to list.')
@click.option('--db', nargs=1, help='The database.')

def EEW_app_ifx(bid, db):
    t_index = 0 
    v_index = 2

    if not bid:
        print "You must provide a bridge ID using the --bid option."
        exit()

    q = "select * from /" + bid + "\/.*temperature.*/ limit 450"   
    #q = "select * from /.*/ limit 1"
    query = urllib.urlencode ({'q':q})

    bidList = []
    print "Requesting data from db", db
    url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query
    print "fetching from:", url
    r = requests.get(url)
    pts = r.json()
    #print "pts:", json.dumps (pts, indent=4)

    sensors = []
    sensorCount = 0
    # paranoid: check we're in time order! and find the sensors whilst we're at it
    for s in pts:
        prevT = 0
        sensors.append({s["name"]:-1})
        sensorCount += 1
        for p in reversed(s["points"]): 
            if p[t_index] < prevT:
                print "Gone backwards in time on", s["name"], nicetime(p[t_index]/1000)
                exit()
            prevT = p[0]

    # that being the case we can go on to find start and end times
    firstD = time.time()
    print "now = ", nicetime(firstD)
    lastD = 0
    for sensor in pts:
        if "temperature" in sensor["name"].lower():
            print "found:", sensor["name"]
            for pt in sensor["points"]:
                #print "checking point:", nicetime(pt[t_index]/1000), pt[v_index]
                if pt[t_index]/1000 > lastD:
                    lastD = pt[t_index]/1000 
                    #print "lastD becomes", nicetime(pt[t_index]/1000), "on:", sensor["name"]
                if pt[t_index]/1000 < firstD:
                    firstD = pt[t_index]/1000 
                    #print "firstD becomes", nicetime(pt[t_index]/1000), "on:", sensor["name"]
    firstDay = time.strftime("%Y %b %d %H:%M", time.localtime(firstD)).split()
    lastDay = time.strftime("%Y %b %d %H:%M", time.localtime(lastD)).split()
    lastDay[3] = "00:00"
    firstDay[3] = "00:00"
    fd_epoch = time.mktime(time.strptime(" ".join(firstDay), "%Y %b %d %H:%M"))
    ld_epoch = time.mktime(time.strptime(" ".join(lastDay), "%Y %b %d %H:%M"))
    
    t_off_window_start = oneHour * 21 # 9pm
    t_off_window_end = oneDay + oneHour * 2 # 2am
    t_on_window_start = oneDay + oneHour * 3 # 3am
    t_on_window_end = oneDay + oneHour * 9 # 9am
    # for each day
    # for each room
    # establish time_on and time_off
    # are there enough outside points between these times?
    # do the analysis
    print "firstD:", nicetime(firstD), "lastD:", nicetime(lastD)
    for thisDay in range(int(fd_epoch),int(ld_epoch), oneDay):
        for sensor in pts:
            time_on = 0
            time_off = 0
            minTemp = 30
            prevTemp = 0
            print "doing", nicetime(thisDay), "for:", sensor["name"]

            # find time_off and time_on for inside sensors
            if "outside" not in sensor["name"].lower():
                for pt in reversed(sensor["points"]):
                    if pt[t_index]/1000 >= thisDay + t_on_window_start and pt[t_index]/1000 <=  thisDay + t_on_window_end:
                        print "point in ON window:", nicetime(pt[t_index]/1000), pt[v_index] 
                        if pt[v_index] < minTemp:
                            minTemp = pt[v_index]
                            time_on = pt[t_index]/1000
                            print "     min so far:", pt[v_index], "at", nicetime(pt[t_index]/1000)
                    elif pt[t_index]/1000 >= thisDay + t_off_window_start and pt[t_index]/1000 <=  thisDay + t_off_window_end:
                        print "point in OFF window:", nicetime(pt[t_index]/1000), pt[v_index] 
                        if pt[v_index] > prevTemp: # a positive gradient so not the last point
                            time_off = pt[t_index]/1000
                            prevTemp = pt[v_index]
                            print "     last +ve grad to:", pt[v_index], "at", nicetime(pt[t_index]/1000)
            
            c = {sensor["name"]: 0}
            if time_on == 0:
                print "*** Failed to find time_on for:", nicetime(thisDay), sensor["name"]
            elif time_off == 0:
                print "*** Failed to find time_off for:", nicetime(thisDay), sensor["name"]
                #continue
            else:            
                print "    so for", nicetime(thisDay), "time_off = ", nicetime(time_off), "time_on = ", nicetime(time_on)
                #Count the night points
                for x in sensor["points"]:
                    if x[t_index]/1000 > time_off and x[t_index]/1000 <  time_on:
                        #print "--> night points:", nicetime(x[t_index]/1000), x[v_index] 
                        c[sensor["name"]] += 1
            print "        Night count for", c[sensor["name"]], "is:", json.dumps(c, indent = 4) 

if __name__ == '__main__':
    EEW_app_ifx()

