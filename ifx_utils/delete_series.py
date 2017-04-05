#!/usr/bin/env python
# delete_series.py
# Copyright (C) ContinuumBridge Limited, 2017 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#
# Usage  ./delete_series.py --bid "BID101" --db "Bridges" --select "string"
# Find and delete a series in influxDB

import requests
import json
import time
import click
import os, sys
import urllib #re
from itertools import cycle

dburl = "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/"
@click.command()
@click.option('--bid', nargs=1, help='The bridge ID to check.')
@click.option('--db', nargs=1, help='The name of the influx database.')
@click.option('--select', nargs=1, help='string to filter what to find')

def delete_series (bid, db, select):
    if not bid:
        print "No BID specified - can't continue"
        exit()
    else:
        q = "select * from /" + bid + "/ limit 1"
        query = urllib.urlencode ({'q':q})

    url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
    print "fetching from:", url
    try:
        r = requests.get(url) # ,params=list+series)
        latestPoints = r.json()
    except:
        print "****No data found in the", db, "database. Probably", bid, "isn't in there****"
        exit()

    ip = "nonesense"

    target = [] 
    for p in latestPoints:
	if select in p["name"]:
	    target.append(p)

    if target:
	print "targets are:"
        for xy in target:
	    print xy["name"]
    else:
	print "no matches found"
	exit()

    ip = raw_input("\nDelete ALL these, confirm each one or exit? (ALL/c/e):")
    if ip == "e":
        exit()
    elif ip == "ALL":
        for tg in target:
	    q = 'DROP SERIES "' + tg["name"] + '"'
	    query = urllib.urlencode ({'q':q})    
	    url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
	    try:
		r = requests.get(url)
		print "Dropped", tg["name"]
	    except:
		print "couldn't drop", tg["name"]
    elif ip =="c":
        for tg in target:
	    print "delete:", tg["name"], "?"
	    ip = raw_input("Yes/no/exit(Y/n/e):") 
	    if ip == "e":
		exit()
	    if ip == "Y":
		q = 'DROP SERIES "' + tg["name"] + '"'
		query = urllib.urlencode ({'q':q})    
		url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
		try:
		    r = requests.get(url)
		    print "Dropped", tg["name"]
		except:
		    print "couldn't drop", tg["name"]
    else:
	exit()

if __name__ == '__main__':
    delete_series()

