#!/usr/bin/env python
# influxdb_test.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#

dburl = "ec2-54-171-237-126.eu-west-1.compute.amazonaws.com"
import requests
import json
import time
import os, sys
import re
from influxdb import InfluxDBClient

def influxdb_test():
    
    dat = [
           {
               "measurement": "temperature",
                "tags": {
                    "bridge": "BID102",
                    "location": "Hall"
                 },
                "time": int(time.time())*1000, 
                "fields": {
                    "value": 26.0
                }
           },
           {
               "measurement": "humidity",
                "tags": {
                    "bridge": "BID102",
                    "location": "Hall"
                 },
                "time": int(time.time())*1000, 
                "fields": {
                    "value": 56.0
                }
           }
          ]
    #client = InfluxDBClient(host=dburl, port=8086, username="admin", password="admin", database="test")
    client = InfluxDBClient(host=dburl, port=8086, database="test")
    print("Created INfluxDB client")
    result = client.write_points(dat, time_precision="ms")
    print("Written points")
    print ("result: {}".format(result))
    l = client.get_list_database()
    print("Databases: {}".format(l))
    query = "SELECT \"value\" FROM \"temperature\" WHERE (\"bridge\" = 'BID101' AND \"location\" = 'Hall') AND \
        time >= 1506620248611928542 AND time <= 1506620916540732526"
    result = client.query(query, epoch=True)
    print ("temperature: {}".format(result))
    print("\n")
    query = "select value from temperature"
    result = client.query(query, epoch=True)
    print ("all temperature: {}".format(result))
    print("\n")
    query = "select value from humidity"
    result = client.query(query, epoch=True)
    print ("humidity: {}".format(result))

if __name__ == '__main__':
    influxdb_test()

