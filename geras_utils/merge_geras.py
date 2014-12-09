#!/usr/bin/env python
# merge_geras.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
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
from operator import itemgetter

@click.command()
@click.option('--s1', prompt='First series', help='First geras series starting with BIDnn/')
@click.option('--s2', prompt='Second series', help='Second geras series starting with BIDnn/')
@click.option('--sout', prompt='Output series to write', help='The resulting series (this can also be s1 or s2)')
@click.option('--key', prompt='Geras master (write) API key', help='Your Geras API key. See http://geras.1248.io/user/apidoc.')

def merge_geras(s1, s2, sout, key):
    
    if not s1 or not sout:
        print "You must have a first series s1 (s2 is optional), and an sout"
        exit()
          
    r = requests.get('http://geras.1248.io/series/' + s1, auth=(key,''))
    d1 = json.loads(r.content)
    # The ["e"] is the only key in the dict. Leaves a list of dicts
    series1 = d1["e"]     
    #print(json.dumps(series1, indent=4))

    if s2:
        r = requests.get('http://geras.1248.io/series/' + s2, auth=(key,''))
        d2 = json.loads(r.content)
        series2 = d2["e"]

    if not s2:
        print "You're about to rename the geras series:", s1, len(series1), "points"
        print "                                     to:", sout
    else:
        print "You're about to merge the geras series:", s1, len(series1), "points"
        print "                                  with:", s2, len(series2), "points"
        print "               And write the result to:", sout
    ip = raw_input("Continue? (y/n): ") 
    if ip == "n": 
        exit()

    series1.extend(series2)

    # Make sure it gets written to the new geras path
    for i in range(0,len(series1)):
        series1[i]['n'] = sout
    
    print "making a total of", len(series1), "data points" #(json.dumps(series1, indent=4))                      

    # dump to file for diff checking
    """
    sortedlist = sorted(series1, key=itemgetter('t'))
    with open('sortedlist.txt', 'w') as outfile:
        json.dump(sortedlist, outfile)
    """
    headers = {'Content-Type': 'application/json'}
    status = 0
    print "Sending series to: http://geras.1248.io/series/",sout, len(series1), "items" 
    r = requests.post('http://geras.1248.io/series/', auth=(key, ''), data=json.dumps({"e": series1}), headers=headers)
    status = r.status_code
    if status !=200:
        print "POSTing failed, status: ", status

    # For testing
    print "Waiting to read it back"
    time.sleep(10) # wait for it to appear on geras
    r = requests.get('http://geras.1248.io/series/' + sout, auth=(key,''))
    d1 = json.loads(r.content)
    newseries = d1["e"]            
    print "Read", len(newseries), "points" 
                  
    """with open('newseries.txt', 'w') as outfile:
        json.dump(newseries, outfile)     
    """
    for o in series1:
        found = False
        for n in newseries:
            if n["v"] == o["v"] and n["t"] == o["t"]:
                found = True
                break
        if not found:
            print "Old ", o, "not found in new"

    # pending doing the deletions automatically...
    if s2 and s1 and s1 == sout:
        print "Now remember to delete", s2
    elif s2 and s1 and s2 == sout:
        print "Now remember to delete", s1
            
if __name__ == '__main__':
    merge_geras()

