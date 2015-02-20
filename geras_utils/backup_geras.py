#!/usr/bin/env python
# backup_geras.py
# Copyright (C) ContinuumBridge Limited, 2015 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#
# Worth making incremental at some point

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

def backup_geras(key, dir, bid):

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
    
    bidlist = []    
    if allBridges:
        for s in allseries:
            ss = s.split('/')
            if not ss[1] in bidlist:
                bidlist.append(ss[1])                
    else:
        for s in allseries:
            ss = s.split('/')
            if not ss[1] in bidlist and (bid+"/") in s:
                bidlist.append(ss[1])                
    
    print "Backing up:"
    print (json.dumps(bidlist, indent=4))            
    
    now = time.strftime('%Y-%m-%d_', time.localtime())
    failures = []                
    for s in bidlist:
        url = 'http://geras.1248.io/series?pattern=%2F'+ s +'%2F%23'
        retry = 0
        max_retries = 5
        waitTime = 60
       
        while retry < max_retries:
            retry += 1
            try:
                print s, "Getting:", url, "try:", retry
                r = requests.get(url, auth=(key,''))
                alldata = json.loads(r.content)
                f = dir + "/" + now + s + ".txt"
                with open(f, 'w') as outfile:
                    json.dump(alldata, outfile)
                print "    Written:", len(r.text), "items to", f, "\n"
                if allBridges:
                    time.sleep(waitTime) # I'm sure they're throttling heavy users
                break    
            except:
                r.raise_for_status()
                # Wrong - this will print status of the previous request!!
                # It won't work if the first one fails
                print "     ",s,"Failed: Status code:", r.status_code, r.reason, "Got approx", len(r.text), "points, r.raise_for_status():", r.raise_for_status()
                if retry == max_retries:
                    print "      ****",s, "Failed completely, moving on\n"
                    failures.append(s)
                    continue # exit()
                print "      Waiting", retry*waitTime/60, "minutes"
                time.sleep(retry*waitTime) # I'm sure they're throttling heavy users             
            
    print "the following backups failed:", failures                        
                               
if __name__ == '__main__':
    backup_geras()

