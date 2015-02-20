#!/usr/bin/env python
# getgeras.py
# Copyright (C) ContinuumBridge Limited, 2013-14 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#
"""
get data from a Geras time-series database. 
There are two main options:

--list lists all time series in the Geras database
--get gets a specified time series

In all cases a Geras key must be given using the --key option. If no
key if given on the command line, the user will be prompted for it, in
which case it will not be visible on the screen.

--list requires one parameter:

--list all lists all time series in the database
-- list <pattern> lists all time series with a string that matches <pattern>

--get can optionally be supplied with a start and end time, using:

--start <time>
--end <time>

The time parameter must be in the format: '18-10-2014 11:05:02'. The quotes
are required.

Examples (you need to use your own key for these to work):

./getgeras.py --key c685297d8c0f710e3bd1c8e771eb8d3d --list all
./getgeras.py --key c685297d8c0f710e3bd1c8e771eb8d3d --list BID8
./getgeras.py --key c485f97d8c0f410e3bdbc8e771eb8d2d --get /BID8/Kitchen/binary
./getgeras.py --key c485f97d8c0f410e3bdbc8e771eb8d2d --get /BID8/Kitchen/binary --start '2014-10-15 09:00:00' --end '2014-10-18 09:00:00'

"""
gerasurl = 'http://geras.1248.io/'
dburl = "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/"
import requests
import json
import time
import click
import os, sys

def nicetime(timeStamp):
    localtime = time.localtime(timeStamp)
    milliseconds = '%03d' % int((timeStamp - int(timeStamp)) * 1000)
    now = time.strftime('%Y-%m-%d %H:%M:%S', localtime)
    return now

def epochtime(date_time):
    pattern = '%Y-%m-%d %H:%M:%S'
    epoch = int(time.mktime(time.strptime(date_time, pattern)))
    return epoch

@click.command()
@click.option('--list', nargs=1, help='Lists time series on Geras. --list all or --list <pattern>.')
@click.option('--get', nargs=1, help='Gets time series from Geras. --get <name of time series.')
@click.option('--start', nargs=1, help='Start time for getting time series in the format: 18-10-2014 11:05:02.')
@click.option('--end', nargs=1, help='End time for getting time series in the format: 18-10-2014 11:05:02.')
@click.option('--key', prompt='Geras API key', help='Your Geras API key. See http://geras.1248.io/user/apidoc.')

def pulldata(list, key, get, start, end):
    if list:
        r = requests.get('http://geras.1248.io/serieslist', auth=(key,''))
        timeseries = json.loads(r.content)
        if list.lower() == "all":
            print(json.dumps(timeseries, indent=4))
        else:
            for t in timeseries:
                if list in t:
                    print t
    elif get:
        if start:
            startTime = epochtime(start)
            if end:
                endTime = epochtime(end)
            else:
                endTime = time.time()
            url = gerasurl + 'series/' + get +'?start=' + str(startTime) + '&end=' + str(endTime)
        elif end:
            print "If you specify an end time, you must also specify a start time"
            exit()
        else:
            url = gerasurl + 'series/' + get
        r = requests.get(url, auth=(key,''))
        timeseries = json.loads(r.content)
        #print(json.dumps(timeseries, indent=4))
        dat = [
               {"name": get,
                "columns": ["time", "value"],
                "points": []
               }
              ]
        points = []
        for t in timeseries["e"]:
            #print nicetime(t["t"]) + '  ' +  str("%2.1f" %t["v"])
            points.append([1000*t["t"], t["v"]])
        dat[0]["points"] = points
        url = dburl + "db/Bridges/series?u=root&p=27ff25609da60f2d"
        headers = {'Content-Type': 'application/json'}
        status = 0
        r = requests.post(url, data=json.dumps(dat), headers=headers)
        status = r.status_code
        if status !=200:
            print "POSTing failed, status: ", status

    else:
        print "You must use --list, --get or --help."

if __name__ == '__main__':
    pulldata()

