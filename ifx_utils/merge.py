#!/usr/bin/env python
# merge_geras.py
# Copyright (C) ContinuumBridge Limited, 2015 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#

# usage
# ./merge.py --db "Testing" --s1 "BID101/MagSW_ES-Front-Door/binary" --s2 "BID101/MagSW_ES-Front-Door/binary" --sout "foo"

# May be worth enhancing to convert an entire sensor (all associated 
# series) but probably not worth it.

dburl = "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/"
import requests
import json
import time
import click
import os, sys
import re
from itertools import cycle
from operator import itemgetter
import urllib

@click.command()
@click.option('--db', nargs=1, help='The database')
@click.option('--s1', prompt='First series', help='First series starting with BIDnn/')
@click.option('--s2', prompt='Second series', help='Second series starting with BIDnn/')
@click.option('--sout', prompt='Output series to write', help='The resulting series (this can also be s1 or s2)')

def merge(db, s1, s2, sout):
    d1 = []
    d2 = []
    
    if not s1 or not sout:
        print "You must have a first series s1 (s2 is optional), and an sout"
        exit()

    q = 'select * from "' + s1 + '"'# limit 5'
    query = urllib.urlencode ({'q':q})    
    url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
    print "fetching from:", url
    try:
        r = requests.get(url)
        d1 = json.loads(r.content)
    except:
        print "nothing in s1"
        exit()
    #print "d1:", json.dumps(d1, indent=4)    



    if s2:
        q = 'select * from "' + s2 + '"'# limit 5'
        query = urllib.urlencode ({'q':q})    
        url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
        #print "fetching from:", url
        try:
            r = requests.get(url)
            d2 = json.loads(r.content)
        except:
            print "nothing in s2"
            exit()

        r = requests.get(url)
        d2 = json.loads(r.content)
        #print "d2:", json.dumps(d2, indent=4)

    if not s2:
        print "You're about to rename the series:", s1, len(d1[0]["points"]), "points"
        print "                               to:", sout
    else:
        print "You're about to merge the series:", s1, len(d1[0]["points"]), "points"
        print "                            with:", s2, len(d2[0]["points"]), "points"
        print "         And write the result to:", sout
    ip = raw_input("Continue? (y/n): ") 
    if ip == "n": 
        exit()

    """
    if either list is >1 i.e. more than one set of points
    then we need to decide which sets to merge.
    Unlikely to happen with our data so we ignore it for now
    and assume they both have one list of points
    """
    if (s2 and len(d2) > 1) or len(d1) > 1:
        print "Bombing out 'cause d1 or d2 have multiple lists len(d1, d2): ", len(d1), len(d2)
        exit()

    if s2:
        d1[0]["points"].extend(d2[0]["points"])
        d1[0]['name'] = sout
        try:
            url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" 
            headers = {'Content-Type': 'application/json'}
            status = 0
            print "write url: %s", url
            r = requests.post(url, data=json.dumps(d1), headers=headers)
            status = r.status_code
            if status !=200:
                print ("POSTing failed, status: %s", status)
        except Exception as ex:
            print "Exit - postInfluxDB problem, type:", type(ex), "exception:", str(ex.args)
            exit()

        
    else: # just rename s1 to sout
    print "making a total of", len(d1[0]["points"]), "data points"                      
    #print "d1 merged:", json.dumps(d1, indent=4)
    
    # make sure it all goes to the right series



    #write d1 to db/sout  
    
    """
    # For testing
    print "Waiting to read it back"
    time.sleep(10) # wait for it to appear
    # get sout goes here
    dx = json.loads(r.content)
    print "Read", len(dx[0]), "points" 
                  
    for o in dx:
        found = False
        for n in newseries:
            if n["v"] == o["v"] and n["t"] == o["t"]:
                found = True
                break
        if not found:
            print "Old ", o, "not found in new"

    """
    drop = "weeble"
    if not s2:
        print "Renamed", s1, "to", sout, "Do you want to delete", s1,"?"
        ip = raw_input("Delete? (y/n): ") 
        if ip == "n":
            exit()
        else:
            drop = s1 
    else:
        if s1 == sout:
            drop = s2
            print "Merged s1 and s2 into", sout, "Do you want to delete", s2, "?"
            ip = raw_input("Delete? (y/n): ") 
            if ip == "n":
                exit()
        elif s2 == sout:
            drop = s1
            print "Merged s1 and s2 into", sout, "Do you want to delete", s1, "?"
            ip = raw_input("Delete? (y/n): ") 
            if ip == "n":
                exit()
        else:
            drop = "foo"
            print "Merged s1 and s2 into", sout, "Do you want to delete", s1, "and", s2, "?"
            ip = raw_input("Delete? (y/n): ") 
            if ip == "n":
                exit()
             
        if drop != "foo":
            q = 'DROP SERIES "' + drop + '"'
            query = urllib.urlencode ({'q':q})    
            url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
            try:
                r = requests.get(url)
            except:
                print "couldn't drop", drop
        else:
            q = 'DROP SERIES "' + s1 + '"'
            query = urllib.urlencode ({'q':q})    
            url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
            try:
                r = requests.get(url)
            except:
                print "couldn't drop", drop
            q = 'DROP SERIES "' + s2 + '"'
            query = urllib.urlencode ({'q':q})    
            url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
            try:
                r = requests.get(url)
            except:
                print "couldn't drop", drop                
                    
if __name__ == '__main__':
    merge()

