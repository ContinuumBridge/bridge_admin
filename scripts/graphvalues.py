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
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class AnalyseData():
    def __init__(self, argv):
	if len(argv) < 2:
            print "Usage: checkbridge <bridge>"
            exit()
        else:
            self.bridges = [argv[1]]
        for b in self.bridges:
            b = b.lower()
        print "Checking ", self.bridges

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
    
    def niceTime(self, timeStamp):
        localtime = time.localtime(timeStamp)
        milliseconds = '%03d' % int((timeStamp - int(timeStamp)) * 1000)
        now = time.strftime('%Y:%m:%d, %H:%M:%S:', localtime) + milliseconds
        return now
   
    def readData(self):
        for bridge in self.bridges:
            print "Reaading and processing data for ", bridge
            ds = self.manager.open_or_create_datastore(bridge)
            t = ds.get_table('config')
            devices = t.query(type='idtoname')
            self.values = []
            devSensors = []
            for d in devices:
                devHandle = d.get('device')
                devName =  d.get('name')
                t = ds.get_table(devHandle)
                for sensor in SENSORS:
                    devSensors.append([devName, sensor])
                    readings = t.query(Type=sensor)
                    for r in readings:
                        timeStamp = float(r.get('Date'))
                        dat = r.get('Data')
                        self.values.append([timeStamp, dat])

    def prepareData(self):
        self.df = {}
        test = pd.to_datetime([1, 2, 3])
        print "test = ", test
        self.df = pd.DataFrame(self.values)
        #self.df[t]['epochTime'] = pd.to_datetime(self.df[t]['epochTime'], unit='s')
        #self.df[t] = self.df[t].set_index('epochTime')
        #print self.df[t].head()

    def processTemp(self):
        self.temp = {}
        for t in self.tables:
            print "processTemp, table = ", t
            self.temp[t] = self.df[t]['ambT']
            #print objT.head()
            print "Mean = ", self.temp[t].mean()
            self.temp[t] = self.temp[t].resample('10Min')
            #print objT.head()
            #objT = objT.cumsum()
            #objT.plot()
            #objT = objT.cumsum()
            #plt.figure(); df.plot(); plt.legend(loc='best')
            #plt.plot(objT)
            self.temp[t].plot()
        plt.ylabel('deg C')
        plt.show(block=False)

if __name__ == '__main__':
    print "Hello"
    if len(sys.argv) < 2:
        print "App improper usage"
    a = AnalyseData(sys.argv)
    a.readData()
    a.prepareData()
    a.processTemp()
    # Wait for user input before closing all windows and finishing:
    cmd = raw_input("Press return to finish ...")
    print "Bye"
