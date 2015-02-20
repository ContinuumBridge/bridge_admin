#!/usr/bin/env python
# backup_geras_by_series.py
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

@click.command()
@click.option('--key', prompt='Geras master (write) API key', help='Your Geras API key. See http://geras.1248.io/user/apidoc.')
@click.option('--dir', prompt='Where to write the backup files', help='Absolute path to where you want the backups.')
@click.option('--bid', nargs=1, help='The bridge ID to backup ("" does them all)')

def backup_geras_by_series(key, dir, bid):

    print "Requesting list of series"    
    try:
        r = requests.get('http://geras.1248.io/serieslist', auth=(key,''))
        allseries = json.loads(r.content)    
        r.raise_for_status()
    except:
        print "** Series list request failed - no point in continuing"
        exit() 

    allBridges = 0
    if not bid:
        print "No BID specified - doing them all"
        allBridges = 1
        
    serieslist = []
    if allBridges:
        for t in allseries:
            serieslist.append(t)
    else:
        for t in allseries:
            if (bid+"/") in t:
                serieslist.append(t)

    print "Backing up:"
    print (json.dumps(serieslist, indent=4))            
    
    now = time.strftime('%Y-%m-%d_', time.localtime())
    failures=[]
    seriesData={}
    for s in serieslist:
        url = gerasurl + 'series' + s
        retry = 0
        max_retries = 2
        waitTime = 10
        while retry < max_retries:
            retry += 1
            try:
                print "Getting:", url, "try:", retry     
                r = requests.get(url, auth=(key,''))
                seriesData = json.loads(r.content)
                if allBridges:
                    time.sleep(waitTime) # I'm sure they're throttling heavy users
                break    
            except:
                r.raise_for_status()
                # Wrong - this will print status of the previous request!!
                # It won't work if the first one fails
                print "     ",s,"Failed: code:", r.status_code, r.reason, "Got approx", len(r.text), "items, status:", r.raise_for_status()
                if retry == max_retries:
                    print "    ",s, "****Failed completely, moving on"
                    failures.append(s)
                    continue # exit()
                print "       Waiting", retry*waitTime/60, "minutes"
                time.sleep(retry*waitTime) # I'm sure they're throttling heavy users    
                
        f = dir + "/" + now + s + ".txt"
        #print "file=", f
        if not os.path.exists(os.path.dirname(f)):
            os.makedirs(os.path.dirname(f))            
        with open(f, 'w') as outfile:
            json.dump(seriesData, outfile)
        print "    Written:", len(r.text), "items to", f, "\n"
            #except:
            #    print "File write failed"
            #    exit()    
                  
    if failures:
        print "the following series failed to backup:", failures            
                      
if __name__ == '__main__':
    backup_geras_by_series()

