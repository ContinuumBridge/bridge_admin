#!/usr/bin/env python
# checkeew.py
# Copyright (C) ContinuumBridge Limited, 2013-14 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#
SENSORS = ['temperature','ir_temperature', 'rel_humidity']

# Include the Dropbox SDK
from dropbox.client import DropboxClient, DropboxOAuth2Flow, DropboxOAuth2FlowNoRedirect
from dropbox.rest import ErrorResponse, RESTSocketError
from dropbox.datastore import DatastoreError, DatastoreManager, Date, Bytes
from pprint import pprint
import time
import os, sys
from utilities import matrix_to_string, niceTime

class CheckEEW():
    def __init__(self, argv):
	if len(argv) < 2:
            print "Usage: checkbridge <bridge>"
            exit()
        else:
            self.bridges = [argv[1]]
        for b in self.bridges:
            b = b.lower()
        #print "Checking ", self.bridges

        access_token = os.getenv('CB_DROPBOX_TOKEN', 'NO_TOKEN')
        if access_token == "NO_TOKEN":
            print "No Dropbox access token. You must set CB_DROPBOX_TOKEN environment variable first."
            exit()
        try:
            self.client = DropboxClient(access_token)
        except:
            print "Could not access Dropbox. Wrong access token?"
            exit()
        
        self.manager = DatastoreManager(self.client)
        self.process()
    
  
    def process(self):
        for bridge in self.bridges:
            print bridge
            rows = []
            ds = self.manager.open_or_create_datastore(bridge)
            t = ds.get_table('config')
            devices = t.query(type='idtoname')
            print ""
            for d in devices:
                devHandle = d.get('device')
                devName =  d.get('name')
                t = ds.get_table(devHandle)
                for sensor in SENSORS:
                    readings = t.query(Type=sensor)
                    values = []
                    max = 0
                    for r in readings:
                        timeStamp = float(r.get('Date'))
                        if timeStamp > max:
                            max = timeStamp
                        dat = r.get('Data')
                        values.append([timeStamp, dat])
                        #values.sort(key=lambda tup: tup[0])
                        #for v in values:
                            #line = self.niceTime(v[0]) + "," + str("%2.1f" %v[1]) + "\n"
                            #self.f.write(line)
                    rows.append([devHandle, devName, sensor, niceTime(max)])
        header = ('Handle', 'Friendly Name', 'Sensor', 'Most Recent Sample')
        txt = matrix_to_string(rows, header)
        print txt

if __name__ == '__main__':
    c = CheckEEW(sys.argv)
