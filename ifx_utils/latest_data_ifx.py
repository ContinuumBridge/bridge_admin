#!/usr/bin/env python
# latest_data_ifx.py
# Copyright (C) ContinuumBridge Limited, 2015 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#
# Checks for the latest data from bridges in databases.
# Parameters are bid and db
#
# db selects the InfluxDB database to search. 
# "" searches all
#
# If bid is specified, you get the latest time of data sent from from each app on bid to the selected db. 
# i.e. what sensors are alive
# 
# If bid is empty, you get the latest time that all bridges in the selected db sent data. 
# i.e. which bridges are alive
#
#  ./latest_data_ifx.py --bid "" --db "" | sort --key 6 # All bridges in all dbs sorted by last seen
#
#  ./latest_data_ifx.py --bid "BID11" --db "" | sort # BID11 in any database sorted by last seen
# 
#  ./latest_data_ifx.py --bid "" --db "Bridges"
#
# Note that not all bridges will be found in all databases

dburl = "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/"
import requests
import json
import time
import click
import os, sys
import re
import smtplib
import urllib
from itertools import cycle

def nicetime(timeStamp):
    localtime = time.localtime(timeStamp)
    now = time.strftime('%Y-%m-%d %H:%M:%S', localtime)
    return now

def epochtime(date_time):
    pattern = '%Y-%m-%d %H:%M:%S'
    epoch = int(time.mktime(time.strptime(date_time, pattern)))
    return epoch


def latest_data (bid, db):
    allBridges = 0
    if not bid:
        print "No BID specified - checking all"
        allBridges = 1
        query = urllib.urlencode ({'q':'select * from /BID*/ limit 1'})
    else:
        q = "select * from /" + bid + "/ limit 1"
        query = urllib.urlencode ({'q':q})

    oneDay = 60*60*24
    t = time.localtime(time.time())
    s = time.strftime('%Y-%m-%d %H:%M:%S', t)
    now = epochtime(s)
    latestPoints = []
    
    url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
    #print "fetching from:", url
    try:
        r = requests.get(url) # ,params=list+series)
        latestPoints = r.json()
    except:
        print "****No data found in the", db, "database. Probably", bid, "isn't in there****"
        return #exit()
    #print json.dumps(r.json(), indent=4)
    #print json.dumps(latestPoints, indent=4)    
    #print json.dumps(r.content, indent=4)

    currentBridge = "fubar"
    latest_time = 0
    for i in range(0,len(latestPoints)): # every sensor on every bridge
        if allBridges == 0: # then all sensors on selected bridge
            latest_time = latestPoints[i]["points"][0][0]/1000
            if (now - latest_time)/oneDay ==0:
                print nicetime(latest_time), "( ", (now-latest_time)/(60*60), "hours ago) is latest data in", db,  "for", latestPoints[i]['name'] 
            else:
                print nicetime(latest_time), "(*", (now - latest_time)/oneDay, "days ago) is latest data in", db, "for", latestPoints[i]['name'] 
        else: # looping on all sensors on all bridges
            bridge = latestPoints[i]["name"].split('/')        
            lastBridge = latestPoints[-1]["name"].split('/')        
            #print "   processing", latestPoints[i]["name"], "latest data at", nicetime(latestPoints[i]["points"][0][0]/1000)
            if currentBridge <> bridge[0] or i == len(latestPoints)-1: 
                # changed bridge so record data then reset             
                prevLatest = latest_time          
                prevBridge = currentBridge
                prevAge = now - prevLatest
                currentBridge = bridge[0]
                
                latest_time = latestPoints[i]["points"][0][0]/1000 
                              
                #print "\nLatest time for", prevBridge, "was", nicetime(prevLatest)                       
                if prevBridge <> "fubar":
                    if prevAge < oneDay: 
                        print prevBridge, "heard from today at: ", nicetime(prevLatest), "in the", db, "database"                        
                    else : 
                        print prevBridge, "not heard from since:", nicetime(prevLatest), "(", prevAge/oneDay, ") days ago in the", db, "database"                                            
            else:
            # Accumulate latest points until we change bridge
                if latestPoints[i]["points"][0][0]/1000 > latest_time:
                    latest_time = latestPoints[i]["points"][0][0]/1000

@click.command()
@click.option('--bid', nargs=1, help='The bridge ID to check.')
@click.option('--db', nargs=1, help='The name of the influx database.')

def latest_data_loop(bid, db):

    if not db:
        DBs = ["Bridges", "SCH"]
        for s in DBs:
            try:
                latest_data (bid, s)
            except:
                print bid, "not in", s, "database"
    else:
        latest_data (bid, db)
    
if __name__ == '__main__':
    latest_data_loop()

