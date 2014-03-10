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
from utilities import niceTime

class CheckEEW():
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
        self.process()
    
    def matrix_to_string(self,matrix, header=None):
        """
        Return a pretty, aligned string representation of a nxm matrix.
    
        This representation can be used to print any tabular data, such as
        database results. It works by scanning the lengths of each element
        in each column, and determining the format string dynamically.
    
        @param matrix: Matrix representation (list with n rows of m elements).
        @param header: Optional tuple or list with header elements to be displayed.
        """
        if type(header) is list:
            header = tuple(header)
        lengths = []
        if header:
            for column in header:
                lengths.append(len(column))
        for row in matrix:
            for column in row:
                i = row.index(column)
                column = str(column)
                cl = len(column)
                try:
                    ml = lengths[i]
                    if cl > ml:
                        lengths[i] = cl
                except IndexError:
                    lengths.append(cl)
    
        lengths = tuple(lengths)
        format_string = ""
        for length in lengths:
            format_string += "%-" + str(length) + "s "
        format_string += "\n"
    
        matrix_str = ""
        if header:
            matrix_str += format_string % header
        for row in matrix:
            matrix_str += format_string % tuple(row)
    
        return matrix_str
    
    def process(self):
        for bridge in self.bridges:
            print bridge
            fileName = bridge + ".csv"
            self.f = open(fileName, "w", 0)
            rows = []
            ds = self.manager.open_or_create_datastore(bridge)
            t = ds.get_table('config')
            devices = t.query(type='idtoname')
            values = []
            commas = ""
            heads = "Time,"
            for d in devices:
                devHandle = d.get('device')
                devName =  d.get('name')
                self.f.write(devHandle + ',' +  devName + '\n')
                t = ds.get_table(devHandle)
                for sensor in SENSORS:
                    heads = heads + devName + ' ' + sensor + ','
                    readings = t.query(Type=sensor)
                    max = 0
                    for r in readings:
                        timeStamp = float(r.get('Date'))
                        if timeStamp > max:
                            max = timeStamp
                        dat = r.get('Data')
                        line = commas + str("%2.1f" %dat)
                        values.append([timeStamp, line])
                    commas += ","
                    rows.append([devHandle, devName, sensor, niceTime(max)])
            values.sort(key=lambda tup: tup[0])
            self.f.write(heads + '\n')
            for v in values:
                line = niceTime(v[0]) + "," + v[1] + "\n"
                self.f.write(line)

if __name__ == '__main__':
    c = CheckEEW(sys.argv)
