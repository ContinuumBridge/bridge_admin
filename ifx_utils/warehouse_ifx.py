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
    nightSensors = [] # not implemented yet
    night_start = " 23:00:00"
    night_end = "07:00:00"
    # For now
    night_duration = 60*60*8 # i.e. 7am.
    # Much easier with an offset rather than trying to work out day crossings
    # i.e. having converted them to epochtime
    # night_duration = (night_end + oneDay) - night_start
    
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
    else: # fetch all the night-wandering data
        # Unlike geras, Influx doesn't return a series if there are no points in the selected range
        q = "select * from /" + bid + ".*binary.*/" # limit 50"
        query = urllib.urlencode ({'q':q})
    
        print "Requesting data from BID", bid
        url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
        print "fetching from:", url
        r = requests.get(url)
        pts = r.json()     
       
    # find the earliest and latest night_start and eliminate outside data
    # assumption for now is that all binary inside sensors take part
    # N.B. data isn't in time order
    # It'll be much easier in real time!!
    earliest = today()
    latest = 0
    for i in range(0, len(pts)): # steps through the sensors
        if not (("Outside" in pts[i]["name"]) and ("Hall" in pts[i]["name"])): # Hall is just for doggie
            nightSensors.append(pts[i]["name"])
            for j in range(0, len(pts[i]["points"])):
                if (pts[i]["points"][j][0]/1000 < earliest):
                    earliest = pts[i]["points"][j][0]/1000
                if (pts[i]["points"][j][0]/1000 > latest):
                    latest = pts[i]["points"][j][0]/1000
    print "Earlist data is at:", earliest, " = ", nicetime(earliest), "on", pts[i]["name"], "latest is", nicetime(latest)           
    print "Processing data from:", json.dumps(nightSensors, indent=4)                    

    s = time.strftime('%Y-%m-%d', time.localtime(earliest))
    startDateTime = epochtime(s + night_start)
    #print "startDateTime=", nicetime(startDateTime), "until: ", nicetime(startDateTime + night_duration)
    
    # Count the wander events
    wanders = {}
    day = startDateTime
    while day <= latest:
        #print "day=", nicetime(day)
        wandercount = 0
        for i in range(0, len(pts)): # steps through the sensors
            if not (("Outside" in pts[i]["name"]) and ("Hall" in pts[i]["name"])):
                for j in range(0, len(pts[i]["points"])):
                    if pts[i]["points"][j][0]/1000 > day and pts[i]["points"][j][0]/1000 < day + night_duration: 
                        if pts[i]["points"][j][2] == 1:                
                            #print "wander= ", pts[i]["points"][j][2], " at", nicetime(pts[i]["points"][j][0]/1000), "on ", pts[i]["name"]
                            wandercount += 1
        wanders.update({nicedate(day):wandercount})
        day = day + oneDay
        
    print "Wanders:", json.dumps(wanders, indent=4)
    """
    Afraid this is as far as I got.
    Need to:-
    1. Count the hours (not days) containing a night wander
    2. Put this into the csv file with columns
      "Date"
      "bid"
      "Night Wanders" # the number of nighttime hours with >= 1 wander
    """
 
    f = "bid.csv"
    with open(f, 'w') as outfile:
        exit()
                      
if __name__ == '__main__':
    warehouse_ifx()

