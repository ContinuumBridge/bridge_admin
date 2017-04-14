#!/usr/bin/env python
# create_database.py
# Copyright (C) ContinuumBridge Limited, 2017 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran, Peter Claydon
#
# Usage  ./create_database.py --db "Bridges"
# Create a database

import requests
import json
import time
import click
import os, sys
import urllib #re
from itertools import cycle

dburl = "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/"
@click.command()
@click.option('--db', nargs=1, help='The name of the influx database.')

def create_database (db):
    if not db:
        print("You must specify a database to create with --db")
        exit()
    url = dburl + "db?u=root&p=27ff25609da60f2d&"
    print "Create at:", url
    data = {"name": db}
    r = requests.post(url, data=json.dumps(data))
    print("Respnse: {}".format(r.text))

if __name__ == '__main__':
    create_database()

