#!/usr/bin/env python
# Bath_temps.py
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
import time
import datetime
from itertools import cycle, groupby
import urllib

#Constants
oneHour            = 60 * 60
oneDay             = oneHour * 24
dburl = "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/"
debug = False

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
@click.option('--bids', nargs=1, help='List of bridges to work with.')
@click.option('--db', nargs=1, help='The database.')
@click.option('--sout', nargs=1, help='The series name to write.')

def Bath_temps(bids, db, sout):
    t_index = 0 
    v_index = 2

    if not bids:
        print "You must provide at least two bridges using the --bid option."
        exit()

    bidList = bids.split(',')
    bid_count = len(bidList)
    pts = []
    pts_all = []
    first_pass = True
    
    for bid in bidList:
        print "doing bid:", bid
        q = "select * from /" + bid + "\/.*Outside.*temperature.*/" # limit 2"   
        query = urllib.urlencode ({'q':q})
        print "Requesting data from db", db
        url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query
        print "fetching from:", url
        r = requests.get(url)
        pts = r.json()
        #print "pts:", json.dumps (pts, indent=4)
        if first_pass:
            pts_all = pts
            pts_all[0]["name"] = sout
            first_pass = False
        else:
            pts_all[0]["points"].extend(pts[0]["points"])
    #print "pts_all:", json.dumps (pts_all, indent=4)        
    pts_all[0]["points"].sort()
    #print "pts_all sorted:", json.dumps (pts_all, indent=4)        

    len_before = len(pts_all[0]["points"])
    for s in list(pts_all[0]["points"]):
        if s[v_index] >= 20: # it's either gone inside or it's daytime & we don't care
            pts_all[0]["points"].remove(s)
    print "removed:", len_before - len(pts_all[0]["points"]), "points over 15"
  
    # remove wild values
    for i in range(0,3,1):
        prevprevTemp = pts_all[0]["points"][-1][v_index]    
        prevTemp = pts_all[0]["points"][-1][v_index]
        prevTime = pts_all[0]["points"][0][t_index]
        t_ave = (prevprevTemp + prevTemp + s[v_index])/3                  
        
        print "pass", i
        for s in pts_all[0]["points"]:
            if (s[t_index] - prevTime)/1000 > 24*oneHour:
                print nicetime(s[t_index]/1000), "time jump of", (s[t_index] - prevTime)/1000/60/60, "hours on", pts_all[0]["name"]
            prevTime = s[t_index]


            if s[v_index] - prevTemp > 10-i: # if it's a big jump then and don't include it in the ave
                print nicetime(s[t_index]/1000), "removing big jump from:", prevTemp, "to", s[v_index] # , "on", s["name"]
                s[v_index] = t_ave
                t_ave = (prevprevTemp + prevTemp)/2            
            elif s[v_index] - t_ave > 5-i: # favour the low ones:
                print nicetime(s[t_index]/1000), "removing temp jump from ave:", t_ave, "to", s[v_index] # , "on", s["name"]
                t_ave = (prevprevTemp + prevTemp + s[v_index])/3            
                s[v_index] = t_ave
            else:
                if s[v_index] - prevTemp > 5: 
                    print nicetime(s[t_index]/1000), "jump >5 from:", prevTemp, "to", s[v_index], "but ave =", t_ave # , "on", s["name"]
                t_ave = (prevprevTemp + prevTemp + s[v_index])/3            
            prevprevTemp = prevTemp
            prevTemp = s[v_index]

    # delete old series first
    q = 'DROP SERIES "' + sout + '"'
    query = urllib.urlencode ({'q':q})    
    url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
    try:
        r = requests.get(url)
    except:
        print "couldn't drop", sout    

    # write it back to influx
    # yuk... influx can't handle big POSTs - going to have to split it up!
    pts_segment = [{"points":[], "name":pts_all[0]["name"], "columns":pts_all[0]["columns"]}]
    print "all pts", len(pts_all[0]["points"])

    chunkSize = 1000
    segments = len(pts_all[0]["points"]) // chunkSize
    print "segments", segments

    for i in range(0, segments+1):
        pts_segment[0]["points"] = []
        if i != segments:
            print "i=", i, "doing:", i*chunkSize, ":", (i+1)*chunkSize-1
            pts_segment[0]["points"] = pts_all[0]["points"][i*chunkSize:(i+1)*chunkSize-1]
        else:
            print "finishing with i=", i, "doing:", i*chunkSize, ":", len(pts_all[0]["points"])
            pts_segment[0]["points"] = pts_all[0]["points"][(i)*chunkSize:len(pts_all[0]["points"])]
        try:
            url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" 
            headers = {'Content-Type': 'application/json'}
            status = 0
            print "write url: %s", url
            r = requests.post(url, data=json.dumps(pts_segment), headers=headers)
            status = r.status_code
            if status !=200:
                print ("POSTing failed, status: %s", status)
        except Exception as ex:
            print "Exit - postInfluxDB problem, type:", type(ex), "exception:", str(ex.args)
            exit()

if __name__ == '__main__':
    Bath_temps()

