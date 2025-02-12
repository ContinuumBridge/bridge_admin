#!/usr/bin/env python
# room_occupancy.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#
# Usage:-
# ./dyh.py --user bridges@continuumbridge.com --password Mucht00f@r --bid BID36 --db "SCH" --daysago 5 --to "martin.sotheran@continuumbridge.com"

# Appliances used
# Night wander trend
# In bed
# got up
# Room uccupancy

import requests
import json
import time
import click
import os, sys
import re
import smtplib
import operator
from itertools import cycle
import urllib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage

#Constants
oneMinute          = 60
oneHour            = 60 * oneMinute
oneDay             = oneHour * 24
dburl = "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/"

def nicetime(timeStamp):
    localtime = time.localtime(timeStamp)
    now = time.strftime('%Y-%m-%d %H:%M:%S', localtime)
    return now

def nicedate(timeStamp):
    localtime = time.localtime(timeStamp)
    now = time.strftime('%Y-%m-%d', localtime)
    return now

def nicehours(timeStamp):
    localtime = time.localtime(timeStamp)
    #now = time.strftime('%H:%M:%S', localtime)
    now = time.strftime('%H:%M', localtime)
    return now

def epochtime(date_time):
    pattern = '%Y-%m-%d %H:%M:%S'
    epoch = int(time.mktime(time.strptime(date_time, pattern)))
    return epoch

def start():
    t = time.localtime(time.time() - oneDay)
    yesterday = time.strftime('%Y-%m-%d', t)
    s = yesterday + " 06:00:00"
    return epochtime(s)

def getwander (ss):
    ss = ss.split("/")            
    jj = ss[2].replace("_PIR","")
    jj = jj.replace("_"," ")
    return jj
def getsensor (ss):
    ss = ss.split("/")            
    jj = ss[1].replace("_PIR","")
    return jj

@click.command()
@click.option('--user', nargs=1, help='User name of email account.')
@click.option('--password', prompt='Password', help='Password of email account.')
@click.option('--bid', nargs=1, help='The bridge ID to list.')
@click.option('--db', nargs=1, help='The database to look in')
@click.option('--to', nargs=1, help='The address to send the email to.')
@click.option('--daysago', nargs=1, help='How far back to look')
@click.option('--doors', nargs=1, help='whether to debug doors')

def dyh (user, password, bid, to, db, daysago, doors):
    daysAgo = int(daysago) #0 # 0 means yesterday
    startTime = start() - daysAgo*60*60*24
    endTime = startTime + oneDay
    midnight = startTime + 18*oneHour
    #indeces
    i_time = 0
    i_data = 2
    D = {}
    doorDebug = False
    if doors:
        doorDebug = True
    print "start time:", nicetime(startTime)
    print "end time:", nicetime(endTime)
    D["BID"] = bid
    D["start time:"] = nicetime(startTime)
    D["end time"] = nicetime(endTime)
 
    if not bid:
        print "You must provide a bridge ID using the --bid option."
        exit()
    else:
        # Unlike geras, Influx doesn't return a series if there are no points in the selected range
        # So we'd miss dead sensors
        # So we'll ask for 1 day before startTime on the grounds that we'd always change a battery in that time      
        # select * from /BID11/ where time > 1427025600s and time < 1427112000s
        earlyStartTime = startTime - oneDay
        q = "select * from /" + bid + "/ where time >" + str(earlyStartTime) + "s and time <" + str(endTime) + "s"
        query = urllib.urlencode ({'q':q})
        print "Requesting list of series from", nicetime(earlyStartTime), "to", nicetime(endTime)
        url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
        print "fetching from:", url
        r = requests.get(url)
        pts = r.json()
        #print json.dumps(r.json(), indent=4)

        Text = "\nSummary of " + nicedate(startTime) + " from 6am\n"
        selectedSeries = []
        allPIRSeries = []
        wanderSeries = []
        powerSeries = []
        inOutSeries = []
        tvSeries = []
        doorSeries = []
        roomCount = 0
        roomState = "empty"
        for series in pts:
            if ("wander" in series["name"].lower() 
                or "power" in series["name"].lower() 
                or ("pir" in series["name"].lower() and "binary" in series["name"].lower())
                or "tv" in series["name"].lower() 
                or ("door" in series["name"].lower() and "binary" in series["name"].lower())): 
            # and not "outside" in series["name"].lower():
               selectedSeries.append(series)

        for item in selectedSeries:
            if "pir" in item["name"].lower() and not "wander" in item["name"].lower():
                for pt in item["points"]:
                    if pt[i_time]/1000 > startTime and pt[i_time]/1000 <= startTime + oneDay:
                        allPIRSeries.append({"time":pt[i_time], "room": getsensor(item["name"]), "value": pt[i_data]})
                        #print "adding pir", nicetime(pt[i_time]/1000), "on", item["name"]
                    #else:
                        #print "ignoring", nicetime(pt[i_time]/1000), "on", item["name"]
            if "tv" in item["name"].lower():
                for pt in item["points"]:
                    if pt[i_time]/1000 > startTime and pt[i_time]/1000 <= startTime + oneDay:
                        #print"TV point:", json.dumps(pt, indent=4)
                        tvSeries.append({"time":pt[i_time],  "power": pt[i_data]})
                    #else:
                        #print "ignoring", nicetime(pt[i_time]/1000), "on", item["name"]
            if "door" in item["name"].lower() and not "wander" in item["name"].lower():
                for pt in item["points"]:
                    if pt[i_time]/1000 > startTime and pt[i_time]/1000 <= startTime + oneDay:
                        doorSeries.append({"time":pt[i_time],  "door": getsensor(item["name"]), "value": pt[i_data]})
                        #print "added", nicetime(pt[i_time]/1000), getsensor(item["name"]), pt[i_data], "to doors"
                    #else:
                        #print "ignoring", nicetime(pt[i_time]/1000), "on", item["name"]
            if "power" in item["name"].lower():
                for pt in item["points"]:
                    if pt[i_time]/1000 > startTime and pt[i_time]/1000 <= startTime + oneDay:
                        powerSeries.append({"time":pt[i_time],  "name": item["name"], "power": pt[i_data]})
            if not "wander" in item["name"].lower() and ("door" in item["name"].lower() or "pir" in item["name"].lower()):
                for pt in item["points"]:
                    if pt[i_time] > startTime*1000 + 13*oneHour*1000 and pt[i_time] <= endTime*1000: # bedtime may be before midnight
                        wanderSeries.append({"time":pt[i_time],  "name": item["name"], "value": pt[i_data]})
            if not "wander" in item["name"].lower() and ("door" in item["name"].lower() or "pir" in item["name"].lower()):
                for pt in item["points"]:
                    if pt[i_time] > startTime*1000 and pt[i_time]/1000 <=startTime + oneDay:
                        inOutSeries.append({"time":pt[i_time],  "name": item["name"], "value": pt[i_data]})
            #if not "wander" in item["name"].lower() and ("front" in item["name"].lower() or "pir" in item["name"].lower()):
            #    for pt in item["points"]:
            #        if pt[i_time] > startTime*1000 and pt[i_time]/1000 <=startTime + oneDay:
            #            inOutSeries.append({"time":pt[i_time],  "name": item["name"], "value": pt[i_data]})
        allPIRSeries.sort(key=operator.itemgetter('time'))
        tvSeries.sort(key=operator.itemgetter('time'))
        doorSeries.sort(key=operator.itemgetter('time'))
        powerSeries.sort(key=operator.itemgetter('time'))
        wanderSeries.sort(key=operator.itemgetter('time'))
        inOutSeries.sort(key=operator.itemgetter('time'))

        print "Doors as an fsm"
        state = "WFDTO_U"
        prevState = "foo"
        prevEvent = {}
        event = {}
        doorOpenTime = 0
        doorCloseTime = 0
        #doorDebug = True
        doorString2 = "\nFront Door\n"
        pirCount = 0
        INOUT = "fubar"
        doorList = []
        for event in inOutSeries: # NB now includes all doors!

            if "pir" in event["name"].lower() and event["value"] == 0:
                continue
            if event <> prevEvent:
                #print nicetime(event["time"]/1000), "*** ignoring duplicate event on", event["name"]
                #else:
                prevEvent = event
                PIR = False
                doorClosed = False
                doorOpened = False
                if ("front" in event["name"].lower() and event["value"] == 1 or 
                    ("utility" in event["name"].lower() and "door" in event["name"].lower()) and event["value"] == 1):
                    doorOpened = True
                    doorOpenTime = event["time"]
                    if doorDebug:
                        print nicetime(event["time"]/1000), event["name"], " - Door opened, state=", state, "io:", INOUT
                elif ("front" in event["name"].lower() and event["value"] == 0 or
                    ("utility" in event["name"].lower() and "door" in event["name"].lower()) and event["value"] == 0):
                    doorClosed = True
                    doorCloseTime = event["time"]
                    if doorDebug:
                        print nicetime(event["time"]/1000), event["name"], " - Door closed, state=", state, "io:", INOUT
                    if doorCloseTime - doorOpenTime > 1000*oneMinute*10:
                        doorString2 =  doorString2 + "   " + nicehours(doorOpenTime/1000) + ": Note - door was open for "\
                            + str((doorCloseTime - doorOpenTime)/1000/60) + " minutes\n"
                        print nicetime(event["time"]/1000), "********************** Door was open for", \
                            (doorCloseTime - doorOpenTime)/1000/60, "minutes"
                elif (("pir" in event["name"].lower() and "outside" not in event["name"].lower() and event["value"] == 1)
                    or "door" in event["name"].lower()):
                    PIR = True # PIR or non-front doors

                prevState = state
                
                if state == "WFDTO_U":
                    if PIR:
                        INOUT = "in"
                        state = "WFDTO"
                    elif doorOpened:
                        INOUT = "out"
                        state = "WFDTC"
                    elif doorClosed:
                        state = "ERROR"
                elif state == "WFDTO":
                    #if doorDebug:
                    #    print nicetime(event["time"]/1000), state, event["value"], "on", event["name"]
                    if INOUT == "in":
                        state = "WFDTC" if doorOpened else "WFDTO"
                        #print nicetime(event["time"]/1000), state, INOUT, "with", event["value"], "on", event["name"]
                    elif INOUT == "out":
                        if doorOpened:
                            state = "WFDTC"
                        elif PIR:
                            state = "ERROR"
                    else:
                        print nicetime(event["time"]/1000), "unknown IO", state, event["value"], "on", event["name"]
                        state = "ERROR"
                elif state == "WFDTC":
                    if doorDebug:
                        print nicetime(event["time"]/1000), state, INOUT, event["value"], "on", event["name"],"..."
                    if doorClosed:
                        state = "WFPIR" 
                    elif PIR and INOUT == "out":
                        state = "WFDTC"
                        INOUT = "maybe"
                    #else:
                    #    print nicetime(event["time"]/1000), state, event["value"], "on", event["name"],"dropped through"
                    #print "WFDTC - door closed, IO:", INOUT, "next state = ", state

                elif state == "WFPIR":
                    if doorDebug:
                        print "WFPIR, IO:", INOUT, "Pcnt", pirCount
                    if PIR and event["time"] > doorCloseTime + 20*1000:#  and event["time"] - doorCloseTime < 1000*30*oneMinute:
                        pirCount+=1
                    if pirCount >= 1:
                        pirCount = 0
                        state = "WFDTO"
                        if INOUT == "in":
                            if PIR and event["time"] > doorCloseTime + 20*1000:#  and event["time"] - doorCloseTime < 1000*30*oneMinute:
                                print nicetime(doorCloseTime/1000), "** Didn't leave at", nicetime(doorCloseTime/1000),\
                                    "waited ", (event["time"] - doorCloseTime)/1000/60, "minutes for PIR\n"
                                doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door open, didn't leave\n"
                                doorList.append({nicehours(doorCloseTime/1000):"Door open, didn't leave"})
                            elif PIR and event["time"] > doorCloseTime + 20*1000 and event["time"] - doorCloseTime > 1000*oneHour*2:
                                print nicetime(doorCloseTime/1000), "** Didn't leave at", nicetime(doorCloseTime/1000), "but no activity for", \
                                    (event["time"] - doorCloseTime)/1000/60, "minutes\n"
                                doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door open, didn't leave (but no activity for "\
                                    + str((event["time"]-doorCloseTime)/1000/60) + " minutes - asleep?)\n"
                                doorList.append({nicehours(doorCloseTime/1000):"Door open, didn't leave (but no activity for " +
                                    str((event["time"]-doorCloseTime)/1000/60) + " minutes - asleep?)"})
                        elif INOUT == "out" or INOUT =="maybe":
                            print nicetime(doorCloseTime/1000), "** Came in at", nicetime(doorCloseTime/1000),\
                                "waited", (event["time"] - doorCloseTime)/1000/60, "minutes for PIR\n"
                            doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door open, came in\n"
                            doorList.append({nicehours(doorCloseTime/1000):"Door open, came in"}) 
                            INOUT = "in"
                        else:
                            print nicetime(event["time"]/1000), "Strange value on INOUT", INOUT
                    elif doorOpened:
                        if doorDebug:
                            print "door opened whilst WFPIR"
                        state = "WFDTC"
                        if doorOpenTime - doorCloseTime < 1000*61:
                            if doorDebug:
                                print nicetime(doorCloseTime/1000), "door opened again too soon:", \
                                    (event["time"]-doorCloseTime)/1000, "seconds later - not concluding"
                        elif INOUT == "in":
                            print nicetime(doorCloseTime/1000), "** Went out at", nicetime(doorCloseTime/1000), "cause door opened again", \
                                (event["time"]-doorCloseTime)/1000, "seconds later\n"
                            doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door open, went out\n"
                            doorList.append({nicehours(doorCloseTime/1000):"Door open, went out"})
                            INOUT = "out"
                        elif INOUT == "maybe": 
                            print nicetime(doorCloseTime/1000), "** In and out at", nicetime(doorCloseTime/1000), "cause door opened again", \
                                (event["time"]-doorCloseTime)/1000/60, "minutes later\n"
                            #doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door open, came in but didn't stay (in and out?)\n"
                            doorList.append({nicehours(doorCloseTime/1000):"Door open, came in but didn't stay (in and out?)"}) 
                            INOUT = "out"
                        elif INOUT == "out":
                            print nicetime(doorCloseTime/1000), "** Didn't come in at", nicetime(doorCloseTime/1000), "cause door opened again", \
                                (event["time"]-doorCloseTime)/1000/60, "minutes later\n"
                            #doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door open, came in but didn't stay\n"
                            doorList.append({nicehours(doorCloseTime/1000):"Door open, came in but didn't stay"}) 
                            INOUT = "out"
                        else:
                            print nicetime(event["time"]/1000), "Strange value in WFPIR. INOUT:", INOUT

                #elif state == "WFPIR_OUT":
                #    if doorDebug:
                #        print nicetime(event["time"]/1000), state, event["value"], "on", event["name"],"..."
                #    if PIR and event["time"] > doorCloseTime + 20*1000:
                #        print nicetime(doorCloseTime/1000), "Came in - waited", (event["time"] - doorCloseTime)/1000/60, "minutes for PIR"
                #        INOUT = "in"
                #        state = "WFDTO"
                #    elif doorOpened:
                #        print nicetime(doorCloseTime/1000), "Didn't come in - cause door opened again", \
                #            (event["time"]-doorCloseTime)/1000/60, "minutes later"
                #        INOUT = "out"
                #        state = "WFDTC"
                #elif state == "WFPIR_IN":
                #    if doorDebug:
                #        print nicetime(event["time"]/1000), state, event["value"], "on", event["name"], pirCount
                #    if PIR and event["time"] > doorCloseTime + 20*1000 and event["time"] - doorCloseTime < 1000*30*oneMinute:
                #        pirCount+=1
                #    if pirCount >= 1:
                #        print nicetime(doorCloseTime/1000), "Didn't leave - waited ", (event["time"] - doorCloseTime)/1000/60, "minutes for PIR"
                #        INOUT = "in"
                #        state = "WFDTO"
                #        pirCount = 0
                #    elif doorOpened:
                #        if doorOpenTime - doorCloseTime < 1000*41:
                #            print nicetime(doorCloseTime/1000), "door opened again too soon:", \
                #                (event["time"]-doorCloseTime)/1000, "seconds later - not concluding"
                #            INOUT = "in"
                #            state = "WFDTC"
                #        else:
                #            print nicetime(doorCloseTime/1000), "Went out - cause door opened again", \
                #                (event["time"]-doorCloseTime)/1000, "seconds later"
                #            INOUT = "out"
                #            state = "WFDTC"
                #    elif PIR and event["time"] > doorCloseTime + 20*1000 and event["time"] - doorCloseTime > 1000*oneHour*2:
                #        print nicetime(doorCloseTime/1000), "Didn't leave - but no activity for", \
                #            (event["time"] - doorCloseTime)/1000/60, "minutes"
                #        INOUT = "in"
                #        state = "WFDTO"
                #elif state == "WFPIR_MaybeIN":
                #    if doorDebug:
                #        print nicetime(event["time"]/1000), state, event["value"], "on", event["name"],"..."
                #    if PIR and event["time"] > doorCloseTime + 20*1000:
                #        print nicetime(doorCloseTime/1000), "Came in - waited", (event["time"] - doorCloseTime)/1000/60, "minutes for PIR"
                #        INOUT = "in"
                #        state = "WFDTO"
                #    elif doorOpened:
                #        if doorOpenTime - doorCloseTime < 1000*41:
                #            print nicetime(doorCloseTime/1000), "door opened again too soon:", \
                #                (event["time"]-doorCloseTime)/1000, "seconds later - not concluding"
                #        else:
                #            print nicetime(doorCloseTime/1000), "Didn't come in - cause door opened again", \
                #                (event["time"]-doorCloseTime)/1000/60, "minutes later"
                #        INOUT = "out"
                #        state = "WFDTC"

                elif state == "ERROR":
                    print nicetime(event["time"]/1000), state, "Somethings wrong!"
                    print nicetime(event["time"]/1000), state, event["value"], "on", event["name"]
                    
                else:
                    print nicetime(event["time"]/1000), "Unknown state", state, "on", event["name"]

        if not event:
            print "No events - quiet day!!" 
        else:
            print nicetime(event["time"]/1000), "No more events - bombed out in", state, INOUT, "with", event["value"], "on", event["name"] 
            if state == "WFPIR" and INOUT == "maybe":
                print nicetime(event["time"]/1000), "So: Came in at", nicetime(doorCloseTime/1000), "but didn't stay and not back before 6am" 
                doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door open, came but didn't stay and not back before 6am\n"
                doorList.append({nicehours(doorCloseTime/1000):"Door open, came but didn't stay and not back before 6am"})
            elif state == "WFPIR" and INOUT == "in":
                print nicetime(event["time"]/1000), "So: Went out at", nicetime(doorCloseTime/1000), "and not back before 6am"
                doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door open, went out - not back before 6am\n"
                doorList.append({nicehours(doorCloseTime/1000):"Door open, , went out - not back before 6am"})

            elif INOUT == "out" and (state == "WFDTO" or state == "WFPIR"):
                print nicetime(event["time"]/1000), "and stayed out"
            elif state == "WFDTO" and INOUT == "in":
                print nicetime(event["time"]/1000), "and stayed in"
            else:
                print nicetime(event["time"]/1000), "Bombed out in", state, "whilst IO=", INOUT 

        """
        print "\nNew doors\n"
        # new new doors - hopefully simpler.
        doorString1 = "\nFront Door\n"
        doorOpenTime = 0
        doorCloseTime = 0
        prevEvent = {}
        doorList = []
        lastActivityTime = 0
        waitingForActivityAfter = False
        waitingForDoorToClose = False
        activityAfter = False                    
        activityBefore = False 
        activityDuring = False
        concluded = False 
        doorDebug = False
        INOUT = "unknown"
        for event in inOutSeries:
            if event <> prevEvent:
                #print nicetime(event["time"]/1000), "*** ignoring duplicate event on", event["name"]
                #else:
                prevEvent = event
                if "pir" in event["name"].lower() and event["value"] == 1:
                    lastActivityTime = event["time"]
                    lastSensor = event["name"]
                    if INOUT == "out" and event["time"] < doorOpenTime:
                        print nicetime(event["time"]/1000), "*** magically re-appeared in", event["name"]
                    if waitingForActivityAfter:
                        # Fix long inactivity
                        #if (event["time"] - doorCloseTime) < 1000*oneMinute*30: 
                        if (event["time"] - doorCloseTime) > 20*1000: # spurious firing of PIR so wait 20 sec
                            waitingForActivityAfter = False
                            activityAfter = True                    
                            if doorDebug:
                                print nicetime(event["time"]/1000), "found activity after on:", event["name"], "waited", \
                                    (event["time"] - doorCloseTime)/1000/60, "minutes"
                        else:
                            if doorDebug:
                                print nicetime(event["time"]/1000), "found activity but event too close:", event["name"], "during:", activityDuring
                        #else:
                        #    waitingForActivityAfter = False
                        #    activityAfter = False                    
                        #    if doorDebug:
                        #        print nicetime(event["time"]/1000), "Waited too long for activity after on:", event["name"]
                    elif event["time"] > doorOpenTime:
                        if not activityDuring:
                            print nicetime(event["time"]/1000), "found activity during on:", event["name"]
                        activityDuring = True
                elif "front" in event["name"].lower() and event["value"] == 1:
                    if doorDebug:
                        print nicetime(event["time"]/1000), "Door opened, waitingfAA", waitingForActivityAfter, "lastAtime:", nicetime(lastActivityTime/1000)
                    doorOpenTime = event["time"]
                    concluded = False
                    waitingForDoorToClose = True
                    if waitingForActivityAfter:
                        if doorDebug:
                            print nicetime(event["time"]/1000), "Door open, whilst waiting for activity after. A-during:", activityDuring
                        print nicetime(event["time"]/1000), "Went out at:", nicetime(doorCloseTime/1000), "last Rm:", lastSensor,"\n"
                        doorString1 = doorString1 + "   " + nicehours(doorCloseTime/1000) + ": Door open, went out\n"
                        doorList.append({nicehours(doorCloseTime/1000):"Door open, went out"}) 
                        INOUT = "out"
                        waitingForActivityAfter = False                         
                        activityAfter = False                    
                    if lastActivityTime <> 0 and lastActivityTime < doorOpenTime and lastActivityTime > doorCloseTime  :
                        activityBefore = True 
                        if doorDebug:
                            print nicetime(event["time"]/1000), "Door open, found activity before at", nicetime(lastActivityTime/1000)
                    else:
                        activityBefore = False 
                elif "front" in event["name"].lower() and event["value"] == 0:
                    if doorDebug:
                        print nicetime(event["time"]/1000), "Door closed, waiting for activity after"
                    if not waitingForDoorToClose:
                        print nicetime(event["time"]/1000), "WARNING: door gone from closed to closed"
                    if event["time"] - doorOpenTime > 10*oneMinute*1000:
                        print "   Warning, door opened for > 10mins"
                        doorString1 =  doorString1 + "   " + nicehours(doorOpenTime/1000) + ": Warning door was open for " + str((doorCloseTime - doorOpenTime)/1000/60) + " minutes\n"
                    doorCloseTime = event["time"]
                    waitingForActivityAfter = True
                    waitingForDoorToClose = False

                else:
                    if "pir" in event["name"].lower() and event["value"] <> 0:
                        print nicetime(event["time"]/1000), "*** ignoring event on", event["name"]

                if not waitingForActivityAfter and not concluded and not waitingForDoorToClose and doorOpenTime <> 0:
                    if not activityBefore and not activityAfter and activityDuring:
                        print nicetime(event["time"]/1000), "Came in but didn't stay\n"
                        doorString1 = doorString1 + "   " + nicehours(doorCloseTime/1000) + ": Door open, came in but didn't stay\n"
                        doorList.append({nicehours(doorCloseTime/1000):"Door open, came in but didn't stay"}) 
                        activityDuring = False
                    if not activityBefore and not activityAfter:
                        print nicetime(event["time"]/1000), "Nobody came in or went out, last Rm:", lastSensor, "\n"
                        doorString1 = doorString1 + "   " + nicehours(doorCloseTime/1000) + ": Door open, nobody came in or went out\n"
                        doorList.append({nicehours(doorCloseTime/1000):"Door open, nobody came in or went out"}) 
                        INOUT = "out"
                    elif not activityBefore and activityAfter:
                        concluded = True
                        print nicetime(event["time"]/1000), "Came In at", nicehours(doorCloseTime/1000), "\n"
                        doorString1 = doorString1 + "   " + nicehours(doorCloseTime/1000) + ": Door open, came in\n"
                        doorList.append({nicehours(doorCloseTime/1000):"Door open, came in"}) 
                        INOUT = "in"
                    elif activityBefore and not activityAfter:
                        concluded = True
                        print nicetime(event["time"]/1000), "Went out at", nicehours(doorCloseTime/1000), "last Rm:", lastSensor, "an"
                        doorString1 = doorString1 + "   " + nicehours(doorCloseTime/1000) + ": Door open, went out\n"
                        doorList.append({nicehours(doorCloseTime/1000):"Door open, went out"}) 
                        INOUT = "out"
                    elif activityBefore and activityAfter:
                        concluded = True
                        print nicetime(event["time"]/1000), "Stayed In at", nicehours(doorCloseTime/1000), "\n"
                        doorString1 = doorString1 + "   " + nicehours(doorCloseTime/1000) + ": Door open, didn't leave\n"
                        doorList.append({nicehours(doorCloseTime/1000):"Door open, didn't leave"}) 
                        INOUT = "in"

        if waitingForActivityAfter and not concluded and not waitingForDoorToClose:
            if activityDuring:
                doorString1 = doorString1 + "   " + nicehours(doorCloseTime/1000) + ": Door open, came in but didn't stay and didn't come back before 6am\n"
                doorList.append({nicehours(doorCloseTime/1000):"Door open, came in but didn't stay and didn't come back before 6am"}) 
                print nicetime(event["time"]/1000), "Came in at", nicehours(doorCloseTime/1000), "but didn't stay and didn't come back before 6aman"
            else:
                doorString1 = doorString1 + "   " + nicehours(doorCloseTime/1000) + ": Door open, went out and didn't come back before 6am\n"
                doorList.append({nicehours(doorCloseTime/1000):"Door open, went out and didn't come back before 6am"}) 
                print nicetime(event["time"]/1000), "Went out at", nicehours(doorCloseTime/1000), "and didn't come back before 6am, during:", activityDuring, "\n"
        #print "End of doors. waitingForActivityAfter", waitingForActivityAfter, "concluded:", concluded, "waitingForDoorToClose", waitingForDoorToClose
        

        print "old:", doorString1, "fsm:", doorString2
        D["Front Door"] = doorList
        #print "Doors:", json.dumps(doorList, indent=4)
        exit()
        """

        # fridge door
        fridgeOpenTime = 0 
        fridgeCloseTime = 0
        fridgeDoorOpen = False
        fridgeString = ""
        fridgeDebug = False
        prevDoorEvent = {}
        for doorEvent in doorSeries:
            if "fridge" in doorEvent["door"].lower():
                if doorEvent == prevDoorEvent:
                    print "Ignoring duplicate fridge door event at", nicetime(doorEvent["time"]/1000)
                else:
                    prevDoorEvent = doorEvent
                    if doorEvent["value"] == 1:
                        fridgeOpenTime = doorEvent["time"]
                        if fridgeDoorOpen:
                            print nicetime(fridgeOpenTime/1000), "Fridge gone from open to open"
                        if fridgeDebug:
                            print nicetime(fridgeOpenTime/1000), "Fridge opened"
                        fridgeDoorOpen = True
                    else:
                        if not fridgeDoorOpen:
                            print nicetime(fridgeOpenTime/1000), "Fridge gone from closed to closed"
                        fridgeCloseTime = doorEvent["time"]
                        if fridgeDebug:
                            print nicetime(fridgeCloseTime/1000), "Fridge closed - was open for", (fridgeCloseTime - fridgeOpenTime)/1000/60, "minutes" 
                        if (fridgeCloseTime - fridgeOpenTime) > 12*oneHour*1000: 
                            if fridgeDebug:
                                print nicetime(doorEvent["time"]/1000), "Was the fridge open all night? from",nicehours(fridgeOpenTime/1000) 
                        elif (fridgeCloseTime - fridgeOpenTime) > 30*oneMinute*1000:
                            if fridgeDebug:
                                print "Fridge open for", (fridgeCloseTime - fridgeOpenTime)/1000/60, "minutes at", nicehours(fridgeOpenTime/1000) 
                            fridgeString = fridgeString + "      Was the fridge open for " + str((fridgeCloseTime - fridgeOpenTime)/1000/60) + " minutes from " + nicehours(fridgeOpenTime/1000) + "?\n" 
                        if not fridgeDoorOpen:
                            print nicetime(fridgeCloseTime/1000), "Fridge gone from closed to closed"
                        fridgeDoorOpen = False
        if fridgeDoorOpen:
            print "Fridge door still open from", nicetime(fridgeOpenTime/1000), "?"
            fridgeString = fridgeString + "      Was the fridge door left open at " +  nicehours(fridgeOpenTime/1000) + "?\n" 


        # uptime
        upCount = 0
        doorCount = 0
        gotUpTime = 0
        gotUp = False
        uptimeString = ""
        uptimeDebug = False
        for ptx in allPIRSeries:
            if ptx["value"] == 1:
                if (ptx["time"]/1000 > startTime 
                    and ptx["time"]/1000 < startTime +6*oneHour 
                    and "bed" not in ptx["room"].lower() 
                    and not gotUp):
                    if uptimeDebug:
                        print nicetime(ptx["time"]/1000), "Morning activity x in", ptx["room"]
                    gotUpTime = ptx["time"]
                    for pty in allPIRSeries:
                        if pty["value"] == 1:
                            if pty["time"] > gotUpTime and "bed" not in pty["room"].lower() and pty["time"] < gotUpTime + 35*60*1000:
                                if uptimeDebug:
                                    print nicetime(pty["time"]/1000), "Morning activity y in", pty["room"]
                                upCount+=1
                    for ptz in doorSeries:
                        if ptz["value"] == 1:
                            if ptz["time"] > gotUpTime and ptz["time"] < gotUpTime + 35*60*1000:
                                if uptimeDebug:
                                    print nicetime(ptz["time"]/1000), "Morning activity y on", ptz["door"]
                                doorCount+=1
                    if upCount >= 6 or (upCount >=4 and doorCount >= 2):
                        uptimeString = "   Got up at " + nicehours(gotUpTime/1000) + "\n"
                        D["gotUpTime"] = nicehours(gotUpTime/1000)
                        print "Got up at", nicehours(gotUpTime/1000), "35min PIR count = ", upCount, "door=", doorCount
                        gotUp = True
                    else:
                        if uptimeDebug:
                            print "not got up at", nicetime(gotUpTime/1000), "35min PIR count = ", upCount, "door=", doorCount
                        upCount = 0
                        doorCount = 0
        if allPIRSeries and not gotUp:   
            uptimeString = "   Can't find getting up time\n"
            D["gotUpTime"] = "Can't find getting up time"
            print "not got up yet by", nicetime(ptx["time"]/1000)
        
        #busyness - just count the ones 
        slotSize = 6*oneHour
        slot = startTime
        slotCount = 0
        prevTime = 0
        prevRoom = "loo"
        prevValue = -1
        dupCount = 0
        repCount = 0
        nightCount = 0
        bedroomWanderCount = 0
        latestOne = {}
        A = {}
        inBed = False
        prevprString = "foo"
        bedtimeString = "   Can't find bedtime"
        busyString = "\nActivity levels\n"
        mTotal = 0
        aTotal = 0
        eTotal = 0
        nTotal = 0
        print "\n\nDay:", nicedate(slot)
        while slot < endTime:
            K = 0
            H = 0
            L = 0
            b = 0
            slotCount+=1
            prString= ""
            bedOnes = 0
            for pt1 in allPIRSeries:
                if pt1["time"]/1000 >= slot and pt1["time"]/1000 <= slot + slotSize: 
                    if pt1["time"]  <> prevTime and pt1["room"] == prevRoom and pt1["value"] == prevValue:
                        repCount+=1
                        #print "Missing data:", pt1["room"], "has gone", prevValue, "to", pt1["value"], "at", nicetime(pt1["time"]/1000)
                    elif pt1["time"] == prevTime and pt1["room"] == prevRoom:
                        dupCount+=1
                        #print "Ignoring duplicate at:", nicetime(pt1["time"]/1000), pt1["time"], pt1["value"], pt1["room"]
                    elif pt1["value"] == 1:
                        #print nicetime(pt1["time"]/1000), pt1["room"]
                        if pt1["room"] == "Bedroom":
                            bedOnes+=1
                        else:
                            if (pt1["time"] > (startTime + 13*oneHour)*1000 and pt1["time"] < (startTime + 19*oneHour)*1000 
                                and pt1["value"] == 1): #slotCount == 3: #startTime + 11*oneHour:
                                latestOne = pt1 # finding the latest non-bedroom PIR activity
                                #print "potential latestOne at", nicetime(pt1["time"]/1000), "in", pt1["room"]
                            if pt1["room"] == "Kitchen":
                                K+=1
                            elif pt1["room"] == "Hall":
                                H+=1
                            elif "Lounge" in pt1["room"]:
                                L+=1
                            elif pt1["room"] == "Bathroom":
                                b+=1
                            else:
                                print "****************missing room:", pt1["room"]
                prevTime = pt1["time"]
                prevValue = pt1["value"]
                prevRoom = pt1["room"]
            if slotCount == 1:
                mornThresh = 40
		if bedOnes+K+H+L+b == 0:
                   levelStr = "None"
                elif bedOnes+K+H+L+b < mornThresh:
                   levelStr = "Low"
                elif bedOnes+K+H+L+b < mornThresh*2:
                   levelStr = "Med"
                else:
                   levelStr = "High"
                busyString = busyString + "  Morning activity: " + levelStr + " (" + str(bedOnes+K+H+L+b) + ")\n"
                mTotal = bedOnes+K+H+L+b 
                print "   Morning activity   =", bedOnes+K+H+L+b 
            elif slotCount == 2:
                mornThresh = 40
		if bedOnes+K+H+L+b == 0:
                   levelStr = "None"
                elif bedOnes+K+H+L+b < mornThresh:
                   levelStr = "Low"
                elif bedOnes+K+H+L+b < mornThresh*2:
                   levelStr = "Med"
                else:
                   levelStr = "High"
                print "   Afternoon activity =", bedOnes+K+H+L+b 
                busyString = busyString + "  Afternoon activity: " + levelStr + " (" + str(bedOnes+K+H+L+b) + ")\n"
                A["afternoon"] = bedOnes+K+H+L+b 
                aTotal = bedOnes+K+H+L+b 
            elif slotCount == 3:
                mornThresh = 40
		if bedOnes+K+H+L+b == 0:
                   levelStr = "None"
                elif bedOnes+K+H+L+b < mornThresh:
                   levelStr = "Low"
                elif bedOnes+K+H+L+b < mornThresh*2:
                   levelStr = "Med"
                else:
                   levelStr = "High"
                print "   Evening aggregate activity   =", bedOnes+K+H+L+b 
                busyString = busyString + "  Evening activity:    " + levelStr + " (" + str(bedOnes+K+H+L+b) + ")\n"
                A["evening"] = bedOnes+K+H+L+b 
                eTotal = bedOnes+K+H+L+b 
            elif slotCount == 4:
                nightThresh = 20
		if bedOnes+K+H+L+b == 0:
                   levelStr = "None"
                elif bedOnes+K+H+L+b < nightThresh:
                   levelStr = "Low"
                elif bedOnes+K+H+L+b < nightThresh*2:
                   levelStr = "Med"
                else:
                   levelStr = "High"
                busyString = busyString + "  Night activity:      " + levelStr + " (" + str(bedOnes+K+H+L+b) + ")\n"
                A["night"] = bedOnes+K+H+L+b 
                nTotal = bedOnes+K+H+L+b 
                print "   Night activity     =", bedOnes+K+H+L+b 
                nightCount = bedOnes+K+H+L+b
                bedroomWanderCount = bedOnes
            else:
                print "Error wussisslot?", nicetime(slot) 

            if bedOnes+K+H+L+b == 0:
                print "      *** No movement: asleep or out or missing data"
                busyString = busyString + "     *** No movement: asleep or out or missing data\n"
            else:
                busyString = busyString + "     Bedroom: " + str(100*bedOnes/(bedOnes+K+H+L+b)) + "%\n"
                busyString = busyString + "     Lounge:  " + str(100*L/(bedOnes+K+H+L+b)) + "%\n"
                busyString = busyString + "     Kitchen: " + str(100*K/(bedOnes+K+H+L+b)) + "%\n"
                busyString = busyString + "     Hall:    " + str(100*H/(bedOnes+K+H+L+b)) + "%\n"
                busyString = busyString + "     Bathroom:" + str(100*b/(bedOnes+K+H+L+b)) + "%\n"

                bedPercent = 100*bedOnes/(bedOnes+K+H+L+b)
                loungePercent = 100*L/(bedOnes+K+H+L+b)
                kitchenPercent = 100*K/(bedOnes+K+H+L+b)
                hallPercent =  100*H/(bedOnes+K+H+L+b)
                bathroomPercent = 100*b/(bedOnes+K+H+L+b)
                print "     ", "Bedroom: ", bedPercent, "%"
                print "     ", "Lounge:  ", loungePercent, "%"
                print "     ", "Kitchen: ", kitchenPercent, "%"
                print "     ", "Hall:    ", hallPercent, "%"
                print "     ", "Bathroom:", bathroomPercent, "%"
                if slotCount == 1:
                    A["morning"] = [{"activity":bedOnes+K+H+L+b},{"bedPercent":bedPercent},{"loungePercent":loungePercent},
                        {"kitchenPercent":kitchenPercent},{"hallPercent":hallPercent},{"bathroomPercent":bathroomPercent}]
                if slotCount == 2:
                    A["afternoon"] = [{"activity":bedOnes+K+H+L+b},{"bedPercent":bedPercent},{"loungePercent":loungePercent},
                        {"kitchenPercent":kitchenPercent},{"hallPercent":hallPercent},{"bathroomPercent":bathroomPercent}]
                if slotCount == 3:
                    A["evening"] = [{"activity":bedOnes+K+H+L+b},{"bedPercent":bedPercent},{"loungePercent":loungePercent},
                        {"kitchenPercent":kitchenPercent},{"hallPercent":hallPercent},{"bathroomPercent":bathroomPercent}]
                if slotCount == 4:
                    A["night"] = [{"activity":bedOnes+K+H+L+b},{"bedPercent":bedPercent},{"loungePercent":loungePercent},
                        {"kitchenPercent":kitchenPercent},{"hallPercent":hallPercent},{"bathroomPercent":bathroomPercent}]
                
            slot = slot + slotSize

        D["activity"] = A
        #print "A:", json.dumps(A, indent=4)

        print "Ignored", dupCount, "duplicate values and", repCount, "non-transitions"

        # bedtime
        lightOn = False
        lightOffTime = 0
        if latestOne and not inBed: # and no more activity for >30mins
            bedtimeString = "   Went to bed at " + nicehours(latestOne["time"]/1000)
            D["bedTime"] = nicehours(latestOne["time"]/1000)
            inBed = True
            print "Went to bed at:", nicetime(latestOne["time"]/1000), "from", latestOne["room"]
            #was the light on or off?
            for p in powerSeries:
                if "bedside" in p["name"].lower(): 
                    if p["time"] <= latestOne["time"]: # before bedtime
                        if ["power"] > 3:
                            lightOn = True
                        else:
                            lightOn = False
                    elif p["time"] >= latestOne["time"]: # after bedtime
                        if p["power"] > 3:
                            lightOn = True
                            print nicehours(p["time"]/1000), "light on"
                        elif lightOn:
                            lightOffTime = p["time"]
                            lightOn = False
            if lightOffTime <> 0:
                print nicehours(latestOne["time"]/1000), "<-bedtime, light went off at ", nicetime(lightOffTime/1000)
                bedtimeString = bedtimeString + ", bedside light on 'til " + nicehours(lightOffTime/1000)
        else:
            print "Went to bed from nowhere!?!"

        for latestuff in allPIRSeries:
            if latestOne:
                if (latestuff["time"]>latestOne["time"] 
                    and latestuff["time"]-latestOne["time"]<oneHour*1000/2 
                    and "Bed" not in latestuff["room"] 
                    and latestuff["value"]==1):
                    print "Bedtime may be wrong: activity after bedtime:", nicetime(latestuff["time"]/1000), "in", latestuff["room"]

        #wanders
        wanderWindow = 15*oneMinute
        wanderTimes = []
        wanderString = ""
        wanderStart = 0
        bStr = "weeble" #"bedtime"
        if latestOne:
            bStr = "bedtime"
            bedtime = latestOne["time"]
        else:
            bStr = "midnight"
            bedtime = midnight*1000
        if wanderSeries:
            for w in wanderSeries:
                if (w["time"] > bedtime + 1000*oneMinute
                    and "bedroom" not in w["name"].lower()
                    and w["value"] == 1 
                    and w["time"] > wanderStart + wanderWindow*1000):
                    wanderStart = w["time"]
                    wanderTimes.append(nicehours(wanderStart/1000))
                    print nicetime(w["time"]/1000), "new wander in", getsensor(w["name"]), "bedtime:", nicetime(bedtime/1000)
                #else:
                #    print nicetime(w["time"]/1000), "No wander in", w["name"], "bedtime:", nicetime(bedtime/1000)
        if wanderTimes:
            wanderString = "Wanders outside the bedroom after " + bStr + " at: "
            for x in wanderTimes:
                print "wanderTimes:", x
                if len(wanderTimes) == 1:
                    wanderString = wanderString + str(x) + ".\n"
                elif wanderTimes.index(x) == len(wanderTimes)-1:
                    wanderString = wanderString + "and " + str(x) + ".\n"
                elif wanderTimes.index(x) == len(wanderTimes)-2:
                    wanderString = wanderString + str(x) + " "
                else:
                    wanderString = wanderString + str(x) + ", "
            D["wanders"] = wanderTimes
        elif latestOne:
            D["wanders"] = "No wanders outside the bedroom after  " + bStr
            wanderString = "No wanders outside the bedroom after " + bStr + "\n"

        bedtimeString = bedtimeString + "\n"
        

        # Appliances
        washerOn = False
        washerOffTime = 0
        washerOnTime = 0
        washerOnTimes = []
        appliancesString = ""

        ovenOn = False
        ovenOnTimes = []
        ovenOnTime = 0
        ovenString = ""

        cookerOn = False
        cookerOnTimes = []
        cookerOnTime = 0
        cookerString = ""

        kettleOnTimes = []
        kettleString = ""
        kettleOnTime = 0
        prevKettlePower = -1
        kettleOn = False

        teleOnTimes = []
        teleOnFor = []
        teleOnTime = 0
        teleOn = False
        teleString = ""

        microOnTimes = []
        microOnTime = 0
        microString = ""

        toasterOnTimes = []
        toasterOnTime = 0
        toasterString = ""
        for app in powerSeries:
            if "oven" in app["name"].lower():
                if app["power"] > 300:
                    if app["time"] > ovenOnTime + 10*oneMinute*1000:
                        ovenOnTimes.append(nicehours(app["time"]/1000))
                        #print "oven on at", nicehours(app["time"]/1000), "power:", app["power"]
                    ovenOnTime = app["time"]
            if "cooker" in app["name"].lower():
                if app["power"] > 300:
                    if app["time"] > cookerOnTime + 10*oneMinute*1000:
                        #print "cooker on at", nicehours(app["time"]/1000), "power:", app["power"]
                        cookerOnTimes.append(nicehours(app["time"]/1000))
                    cookerOnTime = app["time"]
            if "washer" in app["name"].lower():
                if app["power"] > 200:
                    if app["time"] > washerOnTime + 15*oneMinute*1000:
                        washerOnTimes.append(nicehours(app["time"]/1000))
                        #print "washer on at", nicehours(app["time"]/1000), "power:", app["power"]
                    washerOnTime = app["time"]
            if "microwave" in app["name"].lower():
                if app["power"] > 1000:
                    if app["time"] > microOnTime + 5*oneMinute*1000:
                        microOnTimes.append(nicehours(app["time"]/1000))
                        #print "microwave on at", nicehours(app["time"]/1000), "power:", app["power"]
                    microOnTime = app["time"]
            if "kettle" in app["name"].lower():
                if app["power"] == prevKettlePower:
                    print "Kettle point", nicehours(app["time"]/1000), "kettle point ignored. Power:", app["power"]
                elif app["power"] > 1000:
                    if app["time"] > kettleOnTime + 5*oneMinute*1000:
                        if kettleOn: # Odd behaviour on the kettle - doesn't always go off in between ons, Probably due to zwave reset
                            print "WARNING: Kettle already on at", nicehours(app["time"]/1000), "power:", app["power"], "ignoring and setting to off"
                            kettleOn = False
                        else:
                            kettleOnTimes.append(nicehours(app["time"]/1000))
                            kettleOn = True
                            print "Kettle on at", nicehours(app["time"]/1000), "power:", app["power"]
                    kettleOnTime = app["time"]
                else:
                    kettleOn = False
                prevKettlePower = app["power"]
            if "toaster" in app["name"].lower():
                if app["power"] > 1000:
                    if app["time"] > toasterOnTime + 5*oneMinute*1000:
                        toasterOnTimes.append(nicehours(app["time"]/1000))
                        #print "toaster on at", nicehours(app["time"]/1000), "power:", app["power"]
                    toasterOnTime = app["time"]
            """
            if "tv" in app["name"].lower():
                if app["power"] > 10 and not teleOn:
                    teleOn = True
                    print "tele on at", nicehours(app["time"]/1000), "power:", app["power"], "on", app["name"]
                    teleOnTimes.append(nicehours(app["time"]/1000))
                    teleOnTime = app["time"]
                elif app["power"] < 10:
                    if teleOn:
                        print "tele off at", nicehours(app["time"]/1000), "power:", app["power"],\
                            "was on for", (app["time"]-teleOnTime)/60/1000, "minutes"
                    teleOnFor.append((app["time"]-teleOnTime)/60/1000)
                    teleOn = False
            """
            if "tv" in app["name"].lower():
                if app["power"] > 10 and not teleOn:
                    teleOn = True
                    print "tele on at", nicehours(app["time"]/1000), "power:", app["power"], "on", app["name"]
                    teleOnTime = app["time"]
                elif app["power"] < 10:
                    if teleOn:
                        teleOnTimes.append({"ontime": nicehours(teleOnTime/1000), "onfor":(app["time"]-teleOnTime)/60/1000})
                        print "tele off at", nicehours(app["time"]/1000), "power:", app["power"],\
                            "was on for", (app["time"]-teleOnTime)/60/1000, "minutes"
                    else:
                        print "Warning: tele went off twice"
                    teleOn = False

        if teleOnTimes:
            D["tele"] = teleOnTimes
            teleString = "      Tele on at:\n"
            for i in teleOnTimes:
                teleString = teleString + "        " + i["ontime"] + " for " + str(i["onfor"]) + " mins\n"
                print "     Tele on at", i["ontime"], "for", i["onfor"]
        else:
            D["tele"] = "no tele data"
            teleString = "      No tele data\n"
            print "no tele"
        if kettleOnTimes:
            D["kettle"] = kettleOnTimes
            kettleString = "      Kettle on at: "
            for i in kettleOnTimes:
                kettleString = kettleString + i
                if kettleOnTimes.index(i) < len(kettleOnTimes)-1:
                    kettleString = kettleString + ", "
                else:
                    kettleString = kettleString + "\n"
                print "     Kettle on at", i
            #kettleString = kettleString + "\n"
        else:
            D["kettle"] = "No kettle data"
            kettleString = "      No kettle data\n"
            print "      no kettle data"
        if microOnTimes:
            D["microwave"] = microOnTimes
            microString = "      Microwave on at: "
            for i in microOnTimes:
                microString = microString + i + " "
                if microOnTimes.index(i) < len(microOnTimes)-1:
                    microString = microString + ", "
                else:
                    microString = microString + "\n"
                print "     Microwave on at", i
        else:
            D["microwave"] = "No microwave data"
            microString = "      No microwave\n"
            print "      no microwave"
        if washerOnTimes:
            D["washer"] = washerOnTimes
            washerString = "      Washer on at: "
            for i in washerOnTimes:
                washerString = washerString + i + " "
                if washerOnTimes.index(i) < len(washerOnTimes)-1:
                    washerString = washerString + ", "
                else:
                    washerString = washerString + "\n"
                print "     Washer on at", i
        else:
            D["washer"] = "no washer data"
            washerString = "      No washer\n"
            print "      no washer"
        if ovenOnTimes:
            D["oven"] = ovenOnTimes
            ovenString = "      Oven on at: "
            for i in ovenOnTimes:
                ovenString = ovenString + i + " "
                if ovenOnTimes.index(i) < len(ovenOnTimes)-1:
                    ovenString = ovenString + ", "
                else:
                    ovenString = ovenString + "\n"
                print "     Oven on at", i
        else:
            D["oven"] = "no oven data"
            ovenString = "      No oven\n"
            print "      no oven"
        if cookerOnTimes:
            D["cooker"] = cookerOnTimes
            cookerString = "      Cooker on at: "
            for i in cookerOnTimes:
                cookerString = cookerString + i + " "
                if cookerOnTimes.index(i) < len(cookerOnTimes)-1:
                    cookerString = cookerString + ", "
                else:
                    cookerString = cookerString + "\n"
                print "     Cooker on at", i
        else:
            D["oven"] = "no cooker data"
            cookerString = "      No cooker\n"
            print "      no cooker"
        

    #exit()

    Text = Text + uptimeString + teleString + kettleString + microString + washerString + ovenString + cookerString + fridgeString + bedtimeString + busyString + wanderString + doorString2 + "\n"
    print Text
    

    #exit()
    #print "D:", json.dumps(D, indent=4)
    f = bid + "_" + nicedate(startTime) + "_from_6am.txt"
    try:
        with open(f, 'w') as outfile:
            json.dump(D, outfile, indent=4)
    except:
        print "Failed to write file"


    # Create message container - the correct MIME type is multipart/alternative.
    try:
        msg = MIMEMultipart('alternative')
        #msg['Subject'] = "Activity for bridge "+bid+" from "+nicedate(startTime)+" to "+nicedate(endTime)+" (InfluxDB/"+db+")"
        msg['Subject'] = "Activity for DYH bungalow from 6am "+nicedate(startTime)
        msg['From'] = "Bridges <bridges@continuumbridge.com>"
        recipients = to.split(',')
        [p.strip(' ') for p in recipients]
        if len(recipients) == 1:
            msg['To'] = to
        else:
            msg['To'] = ", ".join(recipients)
        # Create the body of the message (a plain-text and an HTML version).
        text = "Content only available with HTML email clients\n"
        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(Text, 'plain')
        #part2 = MIMEText(htmlText, 'html')
    
        msg.attach(part1)
        #msg.attach(part2)
        mail = smtplib.SMTP('smtp.gmail.com', 587)
        mail.ehlo()
        mail.starttls()
        mail.login(user, password)
        mail.sendmail(user, recipients, msg.as_string())
        mail.quit()
    except Exception as ex:
        print "sendMail problem. To:", to, "type: ", type(ex), "exception: ", str(ex.args)
    
                  
if __name__ == '__main__':
    dyh()

