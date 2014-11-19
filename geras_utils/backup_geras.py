#!/usr/bin/env python
# backup_geras.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
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
def backup_geras(key, dir):

    print "Requesting list of series"    
    r = requests.get('http://geras.1248.io/serieslist', auth=(key,''))
    allseries = json.loads(r.content)    
    
    bidlist = []    
    for s in allseries:
        ss = s.split('/')
        if not ss[1] in bidlist:
           bidlist.append(ss[1])                
    print "Backing up:"
    print (json.dumps(bidlist, indent=4))            
    
    now = time.strftime('%Y-%m-%d_', time.localtime())
                    
    for s in bidlist:
        url = 'http://geras.1248.io/series?pattern=%2F'+ s +'%2F%23'
        print "Getting:", url
        #r = requests.get(url, auth=('ea2f0e06ff8123b7f46f77a3a451731a',''))
        alldata = json.loads(r.content)    
        #print (json.dumps(alldata, indent=4))
        f = dir + "/" + now + s + ".txt"
        with open(f, 'w') as outfile:
            json.dump(alldata, outfile)
        print "Written:", f, "\n"
        time.sleep(1) # probably worth being a bit gentle with geras
                               
if __name__ == '__main__':
    backup_geras()

