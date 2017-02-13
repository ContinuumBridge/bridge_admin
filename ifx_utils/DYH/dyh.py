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

def dyh (user, password, bid, to, db, daysago):
    daysAgo = int(daysago) #0 # 0 means yesterday
    startTime = start() - daysAgo*60*60*24
    endTime = startTime + oneDay
    #indeces
    i_time = 0
    i_data = 2

    print "start time:", nicetime(startTime)
    print "end time:", nicetime(endTime)
 
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
        print "Requesting list of series from", nicetime(startTime), "to", nicetime(endTime)
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
            if "wander" in series["name"].lower() or "power" in series["name"].lower() or "pir" in series["name"].lower() and "binary" in series["name"].lower() or "tv" in series["name"].lower() or ("door" in series["name"].lower() and "binary" in series["name"].lower()): 
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
                    if pt[i_time] > startTime*1000 + 18*oneHour*1000 and pt[i_time] <= endTime*1000: # night only
                        wanderSeries.append({"time":pt[i_time],  "name": item["name"], "value": pt[i_data]})
            if not "wander" in item["name"].lower() and ("front" in item["name"].lower() or "pir" in item["name"].lower()):
                for pt in item["points"]:
                    if pt[i_time] > startTime*1000 and pt[i_time]/1000 <=startTime + oneDay:
                        inOutSeries.append({"time":pt[i_time],  "name": item["name"], "value": pt[i_data]})
        allPIRSeries.sort(key=operator.itemgetter('time'))
        tvSeries.sort(key=operator.itemgetter('time'))
        doorSeries.sort(key=operator.itemgetter('time'))
        powerSeries.sort(key=operator.itemgetter('time'))
        wanderSeries.sort(key=operator.itemgetter('time'))
        inOutSeries.sort(key=operator.itemgetter('time'))

        # New doors - solving the magically re-appearing resident!
        doorString1 = "\nFront Door\n"
        INOUT = "unknown"
        doorCloseTime = 0
        doorOpen = False
        windowAfter  = 1000*35*oneMinute 
        lastActivityTime = 0
        waiting = False
        prevEvent = {}
        openings = False
        doorDebug = False
        for event in inOutSeries:
            if event == prevEvent:
                print nicetime(event["time"]/1000), "*** ignoring duplicate event on", event["name"]
            else:
                prevEvent = event
                if "door" in event["name"].lower() and event["value"] == 0:
                    if not doorOpen:
                        print nicetime(event["time"]/1000), "WARNING: door gone from closed to closed"
                    if doorDebug:
                        print nicetime(event["time"]/1000), "Door closed, IO:", INOUT
                    if event["time"] - doorOpenTime > 10*oneMinute*1000:
                        print "   Warning, door opened for > 10mins"
                        doorString =  doorString + "   " + nicehours(doorOpenTime/1000) + ": Warning door was open for " + str((doorCloseTime - doorOpenTime)/1000/60) + " minutes\n"
                    doorOpen = False
                    waiting = True
                    doorCloseTime = event["time"]

                elif "door" in event["name"].lower() and event["value"] == 1:
                    if doorDebug:
                        print nicetime(event["time"]/1000), "Door Opened, IO:", INOUT
                    if doorOpen:
                        print nicetime(event["time"]/1000), "WARNING: door gone from open to open"
                    openings = True
                    doorOpen = True
                    doorOpenTime = event["time"]
                    if doorCloseTime <> 0:
                        if INOUT == "in" and waiting:
                            waiting = False
                            if event["time"] <= doorCloseTime + windowAfter: # Door opened in window
                                if doorDebug:
                                    print nicetime(event["time"]/1000), "IN: Door opened in window    -> stayed 1 in at", nicetime(doorCloseTime/1000)
                                doorString1 = doorString1 + "   " + nicehours(doorCloseTime/1000) + ": Door open, didn't leave\n"
                            elif event["time"] >= doorCloseTime + windowAfter:
                                if doorDebug:
                                    print nicetime(event["time"]/1000), "IN: Door opened after window -> went out at", nicetime(doorCloseTime/1000), "waited", (event["time"]-doorCloseTime)/1000/60, "minutes"
                                doorString1 = doorString1 + "   " + nicehours(doorCloseTime/1000) + ": Door open, went out\n"
                                INOUT = "out"
                            else:
                                print "IN: Door opened sometime"
                        elif INOUT == "out" and waiting:
                            waiting = False
                            if event["time"] <= doorCloseTime + windowAfter: # Door opened in window
                                if doorDebug:
                                    print nicetime(event["time"]/1000), "OUT: Door opened in window - stop waiting"
                            elif event["time"] >= doorCloseTime + windowAfter:
                                if doorDebug:
                                    print nicetime(event["time"]/1000), "OUT: Door opened after window -> didn't come in at", nicetime(doorCloseTime/1000), "waited", (event["time"]-doorCloseTime)/1000/60, "mins"
                                doorString1 = doorString1 + "   " + nicehours(doorCloesTime/1000) + ": Door open, didn't come in\n"
                                INOUT = "out"
                            else:
                                print "OUT: Door opened sometime"
                        elif INOUT == "unknown" and waiting:
                            print "unknown IO and waiting: Door opened sometime"
                        elif INOUT == "unknown":
                            print "unknown IO: Door opened, came in? "
                    elif INOUT == "unknown": # first door opening of the day. If unknown IO then probably out all night
                        if doorDebug:
                            print nicetime(event["time"]/1000), "First door opening of the day, unknown IO - setting it to out"
                            print nicetime(event["time"]/1000), "PIR events will determine in or out all night"
                        INOUT = "out"





                elif "pir" in event["name"].lower() and event["value"] == 1:
                    lastActivityTime = event["time"]
                    if doorCloseTime <> 0:
                        if INOUT == "in" and waiting:
                            waiting = False
                            if event["time"] <= doorCloseTime + windowAfter: # Activity in window
                                if doorDebug:
                                    print nicetime(event["time"]/1000), "PIR event in windowAfter     -> stayed in 2 at", nicetime(doorCloseTime/1000) 
                                doorString1 = doorString1 + "   " + nicehours(doorCloseTime/1000) + ": Door open, didn't leave\n"
                            if event["time"] >= doorCloseTime + windowAfter:
                                if doorDebug:
                                    print nicetime(event["time"]/1000), "PIR event after windowAfter  -> stayed in 3 at", nicetime(doorCloseTime/1000), "but... waited", (event["time"]-doorCloseTime)/1000/60, "mins"
                                doorString1 = doorString1 + "   " + nicehours(doorCloseTime/1000) + ": Door open, didn't leave (but no activity for " + str((event["time"]-doorCloseTime)/1000/60) + " minutes - asleep?)\n"
                        elif INOUT == "out" and waiting:
                            waiting = False
                            if doorDebug:
                                print nicetime(event["time"]/1000), "PIR event in windowAfter     -> came in at", nicetime(doorCloseTime/1000), "waited", (event["time"]-doorCloseTime)/1000/60, "mins"
                            doorString1 = doorString1 + "   " + nicehours(doorCloseTime/1000) + ": Door open, came in\n"
                            INOUT = "in"
                        elif INOUT == "unknown" and waiting:
                            waiting = False
                            if doorDebug:
                                print nicetime(event["time"]/1000), "PIR event in windowAfter     -> came in at", nicetime(doorCloseTime/1000), "waited", (event["time"]-doorCloseTime)/1000/60, "mins - unknown IO"
                            doorString1 = doorString1 + "   " + nicehours(doorCloseTime/1000) + ": Door open, came in\n"
                            INOUT = "in"
                    elif INOUT == "unknown":
                        if doorDebug:
                            print nicetime(event["time"]/1000), "unknown IO - PIR event setting it"
                        INOUT = "in"

        if waiting:
            if doorDebug:
                print nicetime(doorCloseTime/1000), "went out, not back before 6am"
            doorString1 = doorString1 + "   " + nicehours(doorCloseTime/1000) + ": Door open, went out - not back before 6am\n"
        if not openings:
            doorString1 = doorString1 + "   " + "No door openings found\n"

        
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
                            fridgeString = fridgeString + "   Was the fridge open for " + str((fridgeCloseTime - fridgeOpenTime)/1000/60) + " minutes from " + nicehours(fridgeOpenTime/1000) + "?\n" 
                        if not fridgeDoorOpen:
                            print nicetime(fridgeCloseTime/1000), "Fridge gone from closed to closed"
                        fridgeDoorOpen = False
        if fridgeDoorOpen:
            print "Fridge door still open from", nicetime(fridgeOpenTime/1000), "?"
            fridgeString = fridgeString + "   Was the fridge door left open at " +  nicehours(fridgeOpenTime/1000) + "?\n" 


        # uptime
        upCount = 0
        doorCount = 0
        gotUpTime = 0
        gotUp = False
        uptimeString = ""
        uptimeDebug = False
        for ptx in allPIRSeries:
            if ptx["value"] == 1:
                if ptx["time"]/1000 > startTime and ptx["time"]/1000 < startTime +6*oneHour and "bed" not in ptx["room"].lower() and not gotUp:
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
                        print "Got up at", nicehours(gotUpTime/1000), "35min PIR count = ", upCount, "door=", doorCount
                        gotUp = True
                    else:
                        print "not got up at", nicetime(gotUpTime/1000), "35min PIR count = ", upCount, "door=", doorCount
                        upCount = 0
                        doorCount = 0
        if not gotUp:   
            uptimeString = "   Can't find getting up time\n"
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
        inBed = False
        prevprString = "foo"
        bedtimeString = "   Can't find bedtime"
        busyString = "\nActivity levels\n"
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
                            if pt1["time"] > (startTime + 14*oneHour)*1000 and pt1["time"] < (startTime + 19*oneHour)*1000: #slotCount == 3: #startTime + 11*oneHour:
                                latestOne = pt1 # finding the latest non-bedroom activity
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

                print "     ", "Bedroom: ", 100*bedOnes/(bedOnes+K+H+L+b), "%"
                print "     ", "Lounge:  ", 100*L/(bedOnes+K+H+L+b), "%"
                print "     ", "Kitchen: ", 100*K/(bedOnes+K+H+L+b), "%"
                print "     ", "Hall:    ", 100*H/(bedOnes+K+H+L+b), "%"
                print "     ", "Bathroom:", 100*b/(bedOnes+K+H+L+b), "%"
                
            slot = slot + slotSize

        print "Ignored", dupCount, "duplicate values and", repCount, "non-transitions"

        # bedtime
        light = False
        if latestOne and not inBed: # and no more activity for >30mins
            bedtimeString = "   Went to bed at " + nicehours(latestOne["time"]/1000)
            inBed = True
            print "Went to bed at:", nicehours(latestOne["time"]/1000), "from", latestOne["room"]
        else:
            print "Went to bed from nowhere!?!"
            #else:
        for latestuff in allPIRSeries:
            if latestOne:
                if latestuff["time"]>latestOne["time"] and latestuff["time"]-latestOne["time"]<oneHour*1000/2 and "Bed" not in latestuff["room"] and latestuff["value"]==1:
                    print "Bedtime may be wrong: activity after bedtime:", nicetime(latestuff["time"]/1000), "in", latestuff["room"]


        wanderWindow = 15*oneMinute
        firstEventTime = 0
        wanderTimes = []
        wanderString = ""
        if wanderSeries:
            for w in wanderSeries:
                if firstEventTime == 0 and w["value"] == 1 and w["time"] > latestOne["time"] + wanderWindow*1000 and "bedroom" not in w["name"].lower():
                    firstEventTime = w["time"]
                    wanderTimes.append(firstEventTime)
                    #print "frst:", nicetime(firstEventTime/1000), "value:", w["value"], "this:", nicetime(w["time"]/1000), "bedtime:", nicetime(latestOne["time"]/1000)
                #else:
                #    print "missed", w["name"], "value:", w["value"], "at:", nicetime(w["time"]/1000), "bedtime:", nicetime(latestOne["time"]/1000)

        if firstEventTime == 0:
            wanderString = "No wanders outside the bedroom after bedtime\n"
            print "didn't find any wanders"
        else:
            print "First wander  :", nicetime(firstEventTime/1000)
            wanderString = "Wanders outside the bedroom at: "

            for w in wanderSeries:
                if "bedroom" not in w["name"].lower() and w["time"] >= firstEventTime and w["time"] > latestOne["time"]:
                    if w["time"] >= firstEventTime + wanderWindow*1000: 
                        firstEventTime = w["time"]
                        wanderTimes.append(w["time"])
                        #print "New wander  :", nicetime(w["time"]/1000), "in", getsensor(w["name"])
                    #else:
                        #print "Other sensors:", nicetime(w["time"]/1000), "in", getsensor(w["name"])
                        #if "bathroom" in w["name"].lower():
                        #    print "found bathroom:", nicetime(w["time"]/1000), "in", getsensor(w["name"])

            for x in wanderTimes:
                print "wanderTimes:", nicetime(x/1000)
                if len(wanderTimes) == 1:
                    wanderString = wanderString + nicehours(x/1000) + ".\n"
                elif wanderTimes.index(x) == len(wanderTimes)-1:
                    wanderString = wanderString + "and " + nicehours(x/1000) + ".\n"
                elif wanderTimes.index(x) == len(wanderTimes)-2:
                    wanderString = wanderString + nicehours(x/1000) + " "
                else:
                    wanderString = wanderString + nicehours(x/1000) + ", "
                
        bedtimeString = bedtimeString + "\n"
        

        # Appliances
        # this first set go "on" multiple times during use
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
        kettleOn = True # just for the 14th

        microOnTimes = []
        microOnTime = 0
        microString = ""

        toasterOnTimes = []
        toasterOnTime = 0
        toasterString = ""
        for app in powerSeries:
            if "toaster" in app["name"].lower():
                if app["power"] > 1000:
                    if app["time"] > toasterOnTime + 5*oneMinute*1000:
                        toasterOnTimes.append(app["time"])
                        #print "toaster on at", nicehours(app["time"]/1000), "power:", app["power"]
                    toasterOnTime = app["time"]
            if "washer" in app["name"].lower():
                if app["power"] > 200:
                    if app["time"] > washerOnTime + 15*oneMinute*1000:
                        washerOnTimes.append(app["time"])
                        #print "washer on at", nicehours(app["time"]/1000), "power:", app["power"]
                    washerOnTime = app["time"]
            if "microwave" in app["name"].lower():
                if app["power"] > 1000:
                    if app["time"] > microOnTime + 5*oneMinute*1000:
                        microOnTimes.append(app["time"])
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
                            kettleOnTimes.append(app["time"])
                            kettleOn = True
                            print "Kettle on at", nicehours(app["time"]/1000), "power:", app["power"]
                    kettleOnTime = app["time"]
                else:
                    kettleOn = False
                prevKettlePower = app["power"]
            if "oven" in app["name"].lower():
                if app["power"] > 300:
                    if app["time"] > ovenOnTime + 10*oneMinute*1000:
                        ovenOnTimes.append(app["time"])
                        #print "oven on at", nicehours(app["time"]/1000), "power:", app["power"]
                    ovenOnTime = app["time"]
            if "cooker" in app["name"].lower():
                if app["power"] > 300:
                    if app["time"] > cookerOnTime + 10*oneMinute*1000:
                        #print "cooker on at", nicehours(app["time"]/1000), "power:", app["power"]
                        cookerOnTimes.append(app["time"])
                    cookerOnTime = app["time"]

        if kettleOnTimes:
            kettleString = "   Kettle on at: "
            for i in kettleOnTimes:
                kettleString = kettleString + nicehours(i/1000)
                if kettleOnTimes.index(i) < len(kettleOnTimes)-1:
                    kettleString = kettleString + ", "
                else:
                    kettleString = kettleString + "\n"
                print "  Kettle on at", nicehours(i/1000)
            #kettleString = kettleString + "\n"
        else:
            kettleString = "   No kettle data\n"
            print "no kettle data"
        if microOnTimes:
            microString = "   Microwave on at: "
            for i in microOnTimes:
                microString = microString + nicehours(i/1000) + " "
                if microOnTimes.index(i) < len(microOnTimes)-1:
                    microString = microString + ", "
                else:
                    microString = microString + "\n"
                print "  Microwave on at", nicehours(i/1000)
        else:
            microString = "   No microwave\n"
            print "no microwave"
        if washerOnTimes:
            washerString = "   Washer on at: "
            for i in washerOnTimes:
                washerString = washerString + nicehours(i/1000) + " "
                if washerOnTimes.index(i) < len(washerOnTimes)-1:
                    washerString = washerString + ", "
                else:
                    washerString = washerString + "\n"
                print "  Washer on at", nicehours(i/1000)
        else:
            washerString = "   No washer\n"
            print "no washer"
        if ovenOnTimes:
            ovenString = "   Oven on at: "
            for i in ovenOnTimes:
                ovenString = ovenString + nicehours(i/1000) + " "
                if ovenOnTimes.index(i) < len(ovenOnTimes)-1:
                    ovenString = ovenString + ", "
                else:
                    ovenString = ovenString + "\n"
                print "  Oven on at", nicehours(i/1000)
        else:
            ovenString = "   No oven\n"
            print "no oven"
        if cookerOnTimes:
            cookerString = "   Cooker on at: "
            for i in cookerOnTimes:
                cookerString = cookerString + nicehours(i/1000) + " "
                if cookerOnTimes.index(i) < len(cookerOnTimes)-1:
                    cookerString = cookerString + ", "
                else:
                    cookerString = cookerString + "\n"
                print "  Cooker on at", nicehours(i/1000)
        else:
            cookerString = "   No cooker\n"
            print "no cooker"
        
        # TV
        teleOn = "off"
        watched = False
        teleString = ""
        for tele in tvSeries:
            if tele["power"] >= 9:
                if teleOn <> "on":
                    #print "Tele  switched on at", nicetime(tele["time"]/1000), tele["power"], "watts"
                    teleOn = "on"
                    watched = True
                    teleOnTime = tele["time"]
            elif teleOn == "on" and tele["power"] <= 9:
                #print "Tele switched off at", nicetime(tele["time"]/1000), tele["power"], "watts"
                if (tele["time"] - teleOnTime)/1000 < 60:
                    print "Tele was on at", nicehours(teleOnTime/1000), "for", (tele["time"] - teleOnTime)/1000, "seconds"
                    teleString = teleString + "   Tele on at " + nicehours(teleOnTime/1000) + " for " + str((tele["time"] - teleOnTime)/1000) + " seconds\n" 
                else:
                    print "Tele was on at", nicehours(teleOnTime/1000), "for", (tele["time"] - teleOnTime)/1000/60, "minutes"
                    teleString = teleString + "   Tele on at " + nicehours(teleOnTime/1000) + " for " + str((tele["time"] - teleOnTime)/1000) + " minutes\n" 
                teleOn = "off"
        if not watched:
            teleString =  "   No tele data\n"




    Text = Text + uptimeString + teleString + kettleString + microString + washerString + ovenString + cookerString + fridgeString + bedtimeString + busyString + wanderString + doorString1 + "\n"
    #Text = Text + uptimeString + teleString + microString + washerString + ovenString + cookerString + fridgeString + bedtimeString + busyString + wanderString + doorString1 + "\n"
    #Text = Text + doorString + doorString1 + "\n"
    print Text
    
    #exit()
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

