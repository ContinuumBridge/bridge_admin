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
@click.option('--mail', nargs=1, help='whether to send a mail')
@click.option('--doors', nargs=1, help='whether to debug doors')

def dyh (user, password, bid, to, db, daysago, doors, mail):
    daysAgo = int(daysago) #0 # 0 means yesterday
    startTime = start() - daysAgo*60*60*24
    endTime = startTime + oneDay # + daysAgo*60*60*24
    midnight = startTime + 18*oneHour
    #indeces
    i_time = 0
    i_data = 2
    D = {}
    if doors:
        doorDebug = True
    else:
	doorDebug = False
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
        allSeries = []
        inOutSeries = []
        tvSeries = []
        doorSeries = []
        roomCount = 0
        roomState = "empty"
        for series in pts:
            if ("wander" in series["name"].lower() 
                or "power" in series["name"].lower() 
                or ("pir" in series["name"].lower() and "binary" in series["name"].lower())
                or "humidity" in series["name"].lower() 
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
            if not "wander" in item["name"].lower():
                for pt in item["points"]:
                    if pt[i_time] > startTime*1000 and pt[i_time]/1000 <= endTime: #startTime + oneDay:
                        allSeries.append({"time":pt[i_time],  "name": item["name"], "value": pt[i_data]})
        allPIRSeries.sort(key=operator.itemgetter('time'))
        tvSeries.sort(key=operator.itemgetter('time'))
        doorSeries.sort(key=operator.itemgetter('time'))
        powerSeries.sort(key=operator.itemgetter('time'))
        wanderSeries.sort(key=operator.itemgetter('time'))
        inOutSeries.sort(key=operator.itemgetter('time'))
        allSeries.sort(key=operator.itemgetter('time'))

        print "Showers"
	showerDebug = False
        occStart = 0
        occWindow = 1000*oneMinute*158 # cause there can be a lag between occupancy and rising H
        #occWindow = 1000*oneMinute*20 # cause there can be a lag between occupancy and rising H
        kFell = False
        prevJ = 0
        prevK = []
        prevH = 0
        prevT = 0
        noMoreShowersTillItFalls = False
        longShowerWindow = 320*oneMinute*1000
	showerTimes = []
	for j in allSeries:
	    if "connected" in j["name"].lower() or not "bathroom" in j["name"].lower():
	        #print nicetime(j["time"]/1000), "Skipping", j["name"]
		continue
	    if j == prevJ:
	        print nicetime(j["time"]/1000), "****************** Skipped duplicate j on", j["name"]
		continue
	    if "binary" in j["name"].lower() and "bathroom" in j["name"].lower():
		if j["value"] == 1: # reset occStart for every j cause k takes it to the end of longShowerWindow
	            #if showerDebug:
		    #	print nicetime(j["time"]/1000), "j occStart set by:",  j["name"] 
		    occStart = j["time"]

	    if "humidity" in j["name"].lower(): 
		if prevH <> 0 and j["value"] > prevH: 
		    """
		    # H doesn't always fall between showers so look for a small rise over 
		    # a long time and pretend it fell. 
		    # Catches some 2nd showers but not all
		    if (j["value"] - prevH < 2 
			and (j["time"] - prevT) > 18*oneMinute*1000 
			and noMoreShowersTillItFalls 
			and j["time"]>occStart):
			print "j", nicetime(j["time"]/1000), "nmstif:", noMoreShowersTillItFalls, "j rose by",\
			    j["value"] - prevH, "in", (j["time"] - prevT)/1000/60, "minutes - so pretending it fell"   
			noMoreShowersTillItFalls = False
		    """
		    if showerDebug:
		        print "j", nicetime(j["time"]/1000), "H Gone up by", j["value"]-prevH, "to", j["value"],\
		            "in", (j["time"] - prevT)/1000/60, "minutes\n"
		    # every time j` goes up, look ahead to see how far and how long and whether occupied
		    kFell = False
		    for k in allSeries:
			if "bathroom" not in k["name"].lower():
			    continue
			if "binary" in k["name"].lower() and "pir" in k["name"].lower():
			    if k["value"] == 1:# and k["time"] > occStart + occWindow:
		                #if showerDebug:
				#    print nicetime(k["time"]/1000), "k occStart set by:",  k["name"] 
				occStart = k["time"]
			if "humidity" in k["name"] and not kFell:
			    if (k <> prevK and k["time"] >= j["time"] 
				and k["time"] <= j["time"] + 2*longShowerWindow # restrict k forwards otherwise it
				and not noMoreShowersTillItFalls):              # may find a shower miles away based on j
				if k["value"] > prevK["value"]: # whilst kH is rising...
				    if showerDebug:
					print "pj:", nicetime(prevT/1000), "k:", nicetime(k["time"]/1000), "next k:", k["value"]
				    if abs(k["time"] - occStart) < occWindow: #  and we're occupied
					#print "occstart:", nicehours(occStart/1000), "kt:", nicehours(k["time"]/1000), "so we're",\
					deltaT = (k["time"] - prevT)/1000/60
					deltaH = k["value"] - prevH 
					# two gradients
					# for dh under 10, we require shorter times (dt = m1*dh + c1)
					# for dh >10 we allow more time to capture the sudden jumps after a long time
					m1 = 10
					c1 = -19
					m2 = 54
					c2 = -429
					if (deltaT < 360 and deltaH > 2 and # limit the look-ahead as the rise could last for hours
					    ((deltaH < 10 and deltaT < m1*deltaH +c1) 
					    or (deltaH >= 10 and deltaT < m2*deltaH + c2))):
					    print "**SHOWER_new at pj:", nicetime(prevT/1000),\
						"occStart:", nicetime(occStart/1000),\
						"dh:", float(k["value"] - prevH), \
						"dt:",float((k["time"] - prevT)/1000/60)
					    noMoreShowersTillItFalls = True
					    showerTimes.append(nicehours(occStart/1000))
					else:
					    if showerDebug:
					        print "No shower at j:", nicetime(prevT/1000), "k:", nicetime(k["time"]/1000),\
						    "cause dt=", deltaT, "dh=", deltaH
				    elif k["value"] > prevH and occStart <> 0:
					if showerDebug:
					    print "No show shower at k:", nicetime(k["time"]/1000), \
						"cause abs Kt-OS=", abs(k["time"] - occStart)/60/1000, "minutes and occStart:", nicetime(occStart/1000)
				    else:
				        print "Fallen through occupancy at k:", nicetime(k["time"]/1000)

				else: #kH fell
				    #print nicetime(prevT/1000), "k fell at:", nicehours(k["time"]/1000), "we should reset here"
				    kFell = True
			    prevK = k
		else: # jH fell
		    noMoreShowersTillItFalls = False
		    #if showerDebug:
		    #    print nicetime(j["time"]/1000), "jH fell from", prevH, "to", j["value"]
		prevT = j["time"]
		prevH = j["value"]
	    prevJ = j


	if showerTimes:
	    showerString = "      Shower taken at: "
            for x in showerTimes:
	        showerString = showerString + str(x) 
                if showerTimes.index(x) < len(showerTimes)-1:
		    showerString = showerString + ", " 
       	        else:
		    showerString = showerString + "\n"
	else:
	    #showerString = "      No showers found\n"
	    showerString = ""

        print showerString

        print "\nDoors as an fsm"
        state = "WFDTO_U"
        prevState = "foo"
        prevEvent = {}
        event = {}
        doorOpenTime = 0
        doorCloseTime = 0
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
                        print nicetime(event["time"]/1000), event["name"], " - Door opened, state=", state, "io:", INOUT, "PIR:", PIR
                elif ("front" in event["name"].lower() and event["value"] == 0 or
                    ("utility" in event["name"].lower() and "door" in event["name"].lower()) and event["value"] == 0):
                    doorClosed = True
                    doorCloseTime = event["time"]
                    if doorDebug:
                        print nicetime(event["time"]/1000), event["name"], " - Door closed, state=", state, "io:", INOUT, "PIR:", PIR


		    if doorOpenTime == 0:
			doorString2 =  doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed: Note - was the door open all night?\n"
			if doorDebug:
			    print nicetime(pt["time"]/1000), "********************** Door was open all night!?!"
		    elif doorCloseTime - doorOpenTime > 1000*oneMinute*10:
                    #if doorOpenTime == 0:
	            #	if doorDebug:
		    #	   print nicetime(event["time"]/1000), event["name"],\
		    #		" - Door closed before opening! \nSo we'll pretend it didn't happen and wait for it to open"
		    #elif doorCloseTime - doorOpenTime > 1000*oneMinute*10:
                        doorString2 =  doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Note - door was open for "\
                            + str((doorCloseTime - doorOpenTime)/1000/60) + " minutes from " + nicehours(doorOpenTime/1000) + "\n"
                        print nicetime(event["time"]/1000), "********************** Door was open for", \
                            (doorCloseTime - doorOpenTime)/1000/60, "minutes from", nicehours(doorOpenTime/1000)
                elif (("pir" in event["name"].lower() 
		    and "binary" in event["name"].lower() 
		    and "outside" not in event["name"].lower() 
		    and event["value"] == 1)
                    or "door" in event["name"].lower()):
                    PIR = True # PIR or non-front doors
		    if doorDebug:
			print nicetime(event["time"]/1000), "PIR set by:", event["name"]

                prevState = state
                
                if state == "WFDTO_U":
                    if PIR:
                        INOUT = "in"
                        state = "WFDTO"
                    elif doorOpened:
                        INOUT = "out"
                        state = "WFDTC"
                    elif doorClosed:
                        #state = "ERROR"
                        state = "WFDTO_U"
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
                                doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, didn't leave\n"
                                doorList.append({nicehours(doorCloseTime/1000):"Door closed, didn't leave"})
                            elif PIR and event["time"] > doorCloseTime + 20*1000 and event["time"] - doorCloseTime > 1000*oneHour*2:
                                print nicetime(doorCloseTime/1000), "** Didn't leave at", nicetime(doorCloseTime/1000), "but no activity for", \
                                    (event["time"] - doorCloseTime)/1000/60, "minutes\n"
                                doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, didn't leave (but no activity for "\
                                    + str((event["time"]-doorCloseTime)/1000/60) + " minutes - asleep?)\n"
                                doorList.append({nicehours(doorCloseTime/1000):"Door closed, didn't leave (but no activity for " +
                                    str((event["time"]-doorCloseTime)/1000/60) + " minutes - asleep?)"})
                        elif INOUT == "out" or INOUT =="maybe":
                            print nicetime(doorCloseTime/1000), "** Came in at", nicetime(doorCloseTime/1000),\
                                "waited", (event["time"] - doorCloseTime)/1000/60, "minutes for PIR\n"
                            doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, came in\n"
                            doorList.append({nicehours(doorCloseTime/1000):"Door closed, came in"}) 
                            INOUT = "in"
                        else:
                            print nicetime(event["time"]/1000), "Strange value on INOUT", INOUT
                    elif doorOpened:
                        if doorDebug:
                            print "door opened whilst WFPIR"
                        state = "WFDTC"
                        if doorOpenTime - doorCloseTime < 1000*121:
                            if doorDebug:
                                print nicetime(doorCloseTime/1000), "door opened again too soon:", \
                                    (event["time"]-doorCloseTime)/1000, "seconds later - not concluding"
                        elif INOUT == "in":
                            print nicetime(doorCloseTime/1000), "** Went out at", nicetime(doorCloseTime/1000), "cause door opened again", \
                                (event["time"]-doorCloseTime)/1000, "seconds later\n"
                            doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, went out\n"
                            doorList.append({nicehours(doorCloseTime/1000):"Door closed, went out"})
                            INOUT = "out"
                        elif INOUT == "maybe": 
                            print nicetime(doorCloseTime/1000), "** In and out at", nicetime(doorCloseTime/1000), "cause door opened again", \
                                (event["time"]-doorCloseTime)/1000/60, "minutes later\n"
                            doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, in and out\n"
                            doorList.append({nicehours(doorCloseTime/1000):"Door closed, in and out"}) 
                            INOUT = "out"
                        elif INOUT == "out":
                            print nicetime(doorCloseTime/1000), "** Didn't come in at", nicetime(doorCloseTime/1000), "cause door opened again", \
                                (event["time"]-doorCloseTime)/1000/60, "minutes later\n"
                            #doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, came in but didn't stay\n"
                            doorList.append({nicehours(doorCloseTime/1000):"Door closed, came in but didn't stay"}) 
                            INOUT = "out"
                        else:
                            print nicetime(event["time"]/1000), "Strange value in WFPIR. INOUT:", INOUT

                elif state == "ERROR":
                    print nicetime(event["time"]/1000), state, "Somethings wrong with doors!"
                    print nicetime(event["time"]/1000), state, event["value"], "on", event["name"]
                    
                else:
                    print nicetime(event["time"]/1000), "Unknown state", state, "on", event["name"]

        if not event:
            print "No events - quiet day!!" 
        else:
            print nicetime(event["time"]/1000), "No more events - bombed out in", state, INOUT, "with", event["value"], "on", event["name"] 
            if state == "WFPIR" and INOUT == "maybe":
                print nicetime(event["time"]/1000), "So: Came in at", nicetime(doorCloseTime/1000), "but didn't stay and not back before 6am" 
                doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, came in but didn't stay and not back before 6am\n"
                doorList.append({nicehours(doorCloseTime/1000):"Door closed, came but didn't stay and not back before 6am"})
            elif state == "WFPIR" and INOUT == "in":
                print nicetime(event["time"]/1000), "So: Went out at", nicetime(doorCloseTime/1000), "and not back before 6am"
                doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, went out - not back before 6am\n"
                doorList.append({nicehours(doorCloseTime/1000):"Door closed, , went out - not back before 6am"})

            elif INOUT == "out" and (state == "WFDTO" or state == "WFPIR"):
                print nicetime(event["time"]/1000), "and stayed out"
            elif state == "WFDTO" and INOUT == "in":
                print nicetime(event["time"]/1000), "and stayed in"
            else:
                print nicetime(event["time"]/1000), "Bombed out in", state, "whilst IO=", INOUT 

        D["Front Door"] = doorList


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
                            #fridgeString = fridgeString + "      Was the fridge open for " + str((fridgeCloseTime - fridgeOpenTime)/1000/60) + " minutes from " + nicehours(fridgeOpenTime/1000) + "?\n" 
                        if not fridgeDoorOpen:
                            print nicetime(fridgeCloseTime/1000), "Fridge gone from closed to closed"
                        fridgeDoorOpen = False
        if fridgeDoorOpen:
            print "Fridge door still open from", nicetime(fridgeOpenTime/1000), "?"
            #fridgeString = fridgeString + "      Was the fridge door left open at " +  nicehours(fridgeOpenTime/1000) + "?\n" 


        # uptime
        upCount = 0
        doorCount = 0
        gotUpTime = 0
        gotUp = False
        uptimeString = ""
        uptimeDebug = False
	upWindow = 20*oneMinute
        for ptx in allPIRSeries:
            if ptx["value"] == 1:
                if (ptx["time"]/1000 > startTime 
                    and ptx["time"]/1000 < startTime +8*oneHour # some late risers!!
                    and "bed" not in ptx["room"].lower() 
                    and not gotUp):
                    #if uptimeDebug:
                    #    print nicetime(ptx["time"]/1000), "Potential uptime in", ptx["room"]
                    gotUpTime = ptx["time"]
                    for pty in allPIRSeries:
                        if pty["value"] == 1:
                            if pty["time"] > gotUpTime and "bed" not in pty["room"].lower() and pty["time"] < gotUpTime + upWindow*1000:
                                upCount+=1
                                if uptimeDebug:
                                    print nicetime(pty["time"]/1000), "Getting up(?) activity in", pty["room"], "count=", upCount
                    for ptz in doorSeries:
                        if ptz["value"] == 1:
                            if ptz["time"] > gotUpTime and ptz["time"] < gotUpTime + upWindow*1000:
                                doorCount+=1
                                if uptimeDebug:
                                    print nicetime(ptz["time"]/1000), "Getting up(?) activity on", ptz["door"], "Dcount=", doorCount

                    #if upCount >= 6 or (upCount >5 and doorCount >= 2):
                    if upCount + doorCount >= 10:
                        uptimeString = "   Got up at " + nicehours(gotUpTime/1000) + "\n"
                        D["gotUpTime"] = nicehours(gotUpTime/1000)
                        print "Got up at", nicehours(gotUpTime/1000), upWindow/60, "min PIR count = ", upCount, "door=", doorCount
                        gotUp = True
                    else:
                        if uptimeDebug:
                            print "not got up at", nicetime(gotUpTime/1000), "PIR count = ", upCount, "door=", doorCount, "tot:", upCount+doorCount
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
        latestOne = {"time":endTime*1000, "room":"nowhere"}
        A1 = {}
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


        f = bid + "_activity"
        try:
	    with open(f, 'r') as a:
	        A1 = json.load(a)
            #print "Got activity: file", json.dumps(A1, indent=4)
        except:
            print "No activity: file"
        if not A1:
	    A1["morning"] = []
	    A1["afternoon"] = []
	    A1["night"] = []
	    A1["evening"] = []

        while slot < endTime:
            K = 0
            H = 0
            L = 0
            b = 0
            slotCount+=1
            prString= ""
            bedOnes = 0
            levelStr = "No average yet"
	    ave = -2
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
                            if (pt1["time"] > (startTime + 14*oneHour)*1000 and pt1["time"] <= endTime*1000 # after 8pm
                                and pt1["value"] == 1): #slotCount == 3: #startTime + 11*oneHour:
				# needs qualifying with an inactivity time otherwise the last wander becomes bedtime
                                if latestOne and pt1["time"] - latestOne["time"] > 61*oneMinute*1000:
				    print "Wander at", nicetime(pt1["time"]/1000), "in", pt1["room"]
				else:
				    #print "potential latestOne at", nicetime(pt1["time"]/1000), "in", pt1["room"], "diff from prev=",(pt1["time"] -latestOne["time"])/1000/60, "mins"
                                    latestOne = pt1 # finding the latest non-bedroom PIR activity
                            if pt1["room"] == "Kitchen":
                                K+=1
                            elif pt1["room"] == "Hall":
                                H+=1
                            elif "Lounge" in pt1["room"]:
                                L+=1
                            elif pt1["room"] == "Bathroom":
                                b+=1
                            #else:
                            #    print "****************missing room:", pt1["room"]
                prevTime = pt1["time"]
                prevValue = pt1["value"]
                prevRoom = pt1["room"]
            if slotCount == 1:
                if len(A1["morning"])>0:
		    ave = sum(A1["morning"])/len(A1["morning"]) 
        	    if bedOnes+K+H+L+b == 0:
                        levelStr = "None"
                    elif bedOnes+K+H+L+b <= ave:
                       levelStr = "Below average"
                    else:
                       levelStr = "Above average"
                busyString = busyString + "  Morning activity:   " + levelStr + " (" + str(bedOnes+K+H+L+b) + ")\n"
		A1["morning"].append(bedOnes+K+H+L+b)
                mTotal = bedOnes+K+H+L+b 
                print "   Morning activity   =", bedOnes+K+H+L+b, "ave=", ave 
            elif slotCount == 2:
                if len(A1["afternoon"])>0:
                    ave = sum(A1["afternoon"])/len(A1["afternoon"])
		    if bedOnes+K+H+L+b == 0:
                       levelStr = "None"
                    elif bedOnes+K+H+L+b <= ave:
                       levelStr = "Below average"
                    else:
                       levelStr = "Above average"
                print "   Afternoon activity =", bedOnes+K+H+L+b, "ave=", ave 
                A1["afternoon"].append(bedOnes+K+H+L+b)
                busyString = busyString + "  Afternoon activity: " + levelStr + " (" + str(bedOnes+K+H+L+b) + ")\n"
                aTotal = bedOnes+K+H+L+b 
            elif slotCount == 3:
                if len(A1["evening"])>0:
                    ave = sum(A1["evening"])/len(A1["evening"])
    		    if bedOnes+K+H+L+b == 0:
                       levelStr = "None"
                    elif bedOnes+K+H+L+b <= ave:
                       levelStr = "Below average"
                    else:
                       levelStr = "Above average"
                print "   Evening aggregate activity   =", bedOnes+K+H+L+b, "ave=", ave 
                busyString = busyString + "  Evening activity:   " + levelStr + " (" + str(bedOnes+K+H+L+b) + ")\n"
                A1["evening"].append(bedOnes+K+H+L+b)
                eTotal = bedOnes+K+H+L+b 
            elif slotCount == 4:
                if len(A1["night"])>0:
                    ave = sum(A1["night"])/len(A1["night"])
           	    if bedOnes+K+H+L+b == 0:
                       levelStr = "None"
                    elif bedOnes+K+H+L+b <= ave:
                       levelStr = "Below average"
                    else:
                       levelStr = "Above average"
                busyString = busyString + "  Night activity:     " + levelStr + " (" + str(bedOnes+K+H+L+b) + ")\n"
                A1["night"].append(bedOnes+K+H+L+b)
                nTotal = bedOnes+K+H+L+b 
                print "   Night activity     =", bedOnes+K+H+L+b, "ave=", ave 
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
        f = bid + "_activity"
        try:
            with open(f, 'w') as outfile:
                json.dump(A1, outfile, indent=4)
        except:
            print "Failed to write activity file"

        D["activity"] = A
        #print "A:", json.dumps(A, indent=4)
        print "Ignored", dupCount, "duplicate values and", repCount, "non-transitions"

        # bedtime
        lightOn = False
        lightOffTime = 0
        if endTime - latestOne["time"]/1000 < 40*oneMinute and not inBed: 
            bedtimeString = "   Can't find bedtime before 6am"
            #D["bedTime"] = nicehours(latestOne["time"]/1000)
            print "Still up at:", nicetime(latestOne["time"]/1000), "in", latestOne["room"]
        elif latestOne and not inBed: 
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
            if "tv" in app["name"].lower():
                if app["power"] > 5 and not teleOn:
                    teleOn = True
                    print "tele on at", nicehours(app["time"]/1000), "power:", app["power"], "on", app["name"]
                    teleOnTime = app["time"]
                elif app["power"] < 5:
                    if teleOn:
                        teleOnTimes.append({"ontime": nicehours(teleOnTime/1000), "offtime":nicehours(app["time"]/1000)})
			teleOn = False
                        print "tele off at", nicehours(app["time"]/1000), "power:", app["power"],\
                            "was on for", (app["time"]-teleOnTime)/60/1000, "minutes"
                    else:
                        print "Warning: tele went off twice"

        if teleOnTimes:
            D["tele"] = teleOnTimes
            teleString = "      Tele on at:\n"
            for i in teleOnTimes:
                teleString = teleString + "        " + i["ontime"] + " until " + str(i["offtime"]) + "\n"
                print "     Tele on at", i["ontime"], "til", i["offtime"]
	    if teleOn:
                teleString = teleString + "        " + nicehours(teleOnTime/1000) + " until after 6am\n"
                print "     Tele on at", nicetime(teleOnTime/1000), "til at least 6am"

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
                microString = microString + i 
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
                washerString = washerString + i 
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
                ovenString = ovenString + i 
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
                cookerString = cookerString + i
                if cookerOnTimes.index(i) < len(cookerOnTimes)-1:
                    cookerString = cookerString + ", "
                else:
                    cookerString = cookerString + "\n"
                print "     Cooker on at", i
        else:
            D["oven"] = "no cooker data"
            cookerString = "      No cooker\n"
            print "      no cooker"
        

    # this needs changing to return showerTimes
    #showerString = shower.shower("BID264", "Bridges", startTime, endTime, daysAgo)

    Text = Text + uptimeString + teleString + kettleString + microString + washerString + ovenString + cookerString + fridgeString + showerString + bedtimeString + busyString + wanderString + doorString2 + "\n"
    print Text 
    
    f = bid + "_" + nicedate(startTime) + "_from_6am.txt"
    try:
        with open(f, 'w') as outfile:
            json.dump(D, outfile, indent=4)
    except:
        print "Failed to write file"

    if mail:
	# Create message container - the correct MIME type is multipart/alternative.
	try:
	    msg = MIMEMultipart('alternative')
	    #msg['Subject'] = "Activity for bridge "+bid+" from "+nicedate(startTime)+" to "+nicedate(endTime)+" (InfluxDB/"+db+")"
	    msg['Subject'] = "Activity for bungalow from 6am "+nicedate(startTime)
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

