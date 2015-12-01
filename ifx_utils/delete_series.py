#!/usr/bin/env python
# latest_data_ifx.py
# Copyright (C) ContinuumBridge Limited, 2015 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#
# Usage  ./delete_series.py --bid "BID101" --db "Bridges" --time_limit 120
# requires the latest latest_data_ifx.py

import requests
import json
import time
import click
import os, sys
import urllib #re
from itertools import cycle
from latest_data_ifx import latest_data

dburl = "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/"
@click.command()
@click.option('--bid', nargs=1, help='The bridge ID to check.')
@click.option('--db', nargs=1, help='The name of the influx database.')
@click.option('--time_limit', nargs=1, help='how many days since last write to series')

def delete_series (bid, db, time_limit):
    go_for_it = 0
    n = 0
    ip = "nonesense"
 
    sensorDates = latest_data(bid, db) 
    print "\nThe following are >", time_limit, "days old"
    for p in sensorDates:
        if p["days_old"] >= int(time_limit):
            n += 1
            print  "    ", p["name"], p["days_old"], "days old"
    if n ==0:
        print "    Nothing older than", time_limit, "days"
    else:
        ip = raw_input("\nDelete everything older than time_limit, confirm each one or exit? (Everything/c/e):")
    if ip == "e":
        exit()

    for p in sensorDates:
        if p["days_old"] >= int(time_limit):
            if ip == "Everything":
                print "Dropping", p["name"]
                q = 'DROP SERIES "' + p["name"] + '"'
                query = urllib.urlencode ({'q':q})    
                url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
                try:
                    r = requests.get(url)
                except:
                    print "couldn't drop", p["name"]
            else:
                print "delete:", p["name"], p["days_old"], "days old?"
                ip = raw_input("Y/n:") 
                if ip == "Y":
                    q = 'DROP SERIES "' + p["name"] + '"'
                    query = urllib.urlencode ({'q':q})    
                    url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
                    try:
                        r = requests.get(url)
                    except:
                        print "couldn't drop", p["name"]


if __name__ == '__main__':
    delete_series()

