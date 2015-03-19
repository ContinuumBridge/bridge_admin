#!/usr/bin/env python
# find_big_values.py
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
from itertools import cycle
import urllib

def nicedate(timeStamp):
    localtime = time.localtime(timeStamp)
    now = time.strftime('%Y-%m-%d', localtime)
    return now

def nicetime(timeStamp):
    localtime = time.localtime(timeStamp)
    now = time.strftime('%Y-%m-%d %H:%M:%S', localtime)
    return now
    
def epochtime(date_time):
    pattern = '%Y-%m-%d %H:%M:%S'
    epoch = int(time.mktime(time.strptime(date_time, pattern)))
    return epoch    
    
@click.command()
@click.option('--key', prompt='Geras master (write) API key', help='Your Geras API key. See http://geras.1248.io/user/apidoc.')
@click.option('--bid', nargs=1, help='The bridge ID to backup ("" does them all)')

def find_big_values(key, bid):

    serieslist = []
    allBridges = 0
    if not bid:
        print "No BID specified - checking all"
        allBridges = 1

    print "Requesting list of series"    
    try:
        r = requests.get('http://geras.1248.io/serieslist', auth=(key,''))
        allseries = json.loads(r.content)    
        r.raise_for_status()
    except:
        print "** Series list request failed - no point in continuing"
        exit() 

    if allBridges:
        for t in allseries:
            if 'power' in t:
                serieslist.append(t)
    else:
        for t in allseries:
            if (bid+"/") in t and 'power' in t:
                serieslist.append(t)


    print "Checking:"
    print (json.dumps(serieslist, indent=4))            
    
    t = time.localtime(time.time())
    st = time.strftime('%Y-%m-%d %H:%M:%S', t)
    now = epochtime(st)
    firstList = []    
    for s in serieslist:
        url = gerasurl + 'series' + s
        r = requests.get(url, auth=(key,''))
        t = json.loads(r.content)
        powerData = t['e']
        first = now
        foundOne = 0
        for i in range(0,len(powerData)):
            if powerData[i]['v'] > 50000 or powerData[i]['v'] < -50000:
                if powerData[i]['t'] < first:
                    first = powerData[i]['t']
                    foundOne = 1
                    #print "power=", powerData[i]['v'], "at", nicetime(powerData[i]['t']), "on", s
        if foundOne:
            firstList.append({'s':s, 'f':first})
    for t in range(len(firstList)):
        print "first bogus reading was at", nicetime(firstList[t]['f']), "on", firstList[t]['s'] 

if __name__ == '__main__':
    find_big_values()

