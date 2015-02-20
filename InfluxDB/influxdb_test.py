#!/usr/bin/env python
# influxdb_test.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#

dburl = "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/"
import requests
import json
import time
import click
import os, sys
import re
from itertools import cycle
from operator import itemgetter

@click.command()
@click.option('--user', prompt='InfluxDB user name', help='Your INfluxDB user name.')
@click.option('--password', prompt='InfluxDB password', help='Your INfluxDB password.')

def influxdb_test(user, password):
    
    dat = [
           {"name": "Humidities",
            "columns": ["time", "value"],
            "points": [
                       [1424350430000, 50],
                       [1424350435000, 51],
                       [1424350440000, 52]
                      ]
           }
          ]
    url = dburl + "db/Bridges/series?u=root&p=27ff25609da60f2d"
    headers = {'Content-Type': 'application/json'}
    status = 0
    r = requests.post(url, data=json.dumps(dat), headers=headers)
    status = r.status_code
    if status !=200:
        print "POSTing failed, status: ", status

    # For testing
    print "Waiting to read it back"
    time.sleep(5) # wait for it to appear on geras
    r = requests.get(url)
    d1 = json.loads(r.content)
    print json.dumps(d1, indent=4)

if __name__ == '__main__':
    influxdb_test()

