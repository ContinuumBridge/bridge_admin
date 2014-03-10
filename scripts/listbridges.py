#!/usr/bin/env python
# rmdb.py
# Copyright (C) ContinuumBridge Limited, 2013-14 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#
# Include the Dropbox SDK
from dropbox.client import DropboxClient, DropboxOAuth2Flow, DropboxOAuth2FlowNoRedirect
from dropbox.rest import ErrorResponse, RESTSocketError
from dropbox.datastore import DatastoreError, DatastoreManager, Date, Bytes
import dropbox.datastore 
from pprint import pprint
import time, sys, os
from utilities import matrix_to_string, niceTime
#
access_token = os.getenv('CB_DROPBOX_TOKEN', 'NO_TOKEN')
if access_token == "NO_TOKEN":
    print "No Dropbox access token. You must set CB_DROPBOX_TOKEN environment variable first."
    exit()
try:
    client = DropboxClient(access_token)
except:
    print "Could not access Dropbox. Wrong access token?"
    exit()
 
manager = dropbox.datastore.DatastoreManager(client)
ds = manager.list_datastores()
#print "Datastores: ", ds
rows  = []
for d in ds:
    #dat = niceTime(float(d[4]))
    rows.append([d[0], d[4]]) 
header = ['Bridge', 'Last Accessed']
txt = matrix_to_string(rows, header)
print txt
