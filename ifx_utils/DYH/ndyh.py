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
    print "start time:", nicetime(startTime)
    print "end time:", nicetime(endTime)
    D["BID"] = bid
    D["start time:"] = nicetime(startTime)
    D["end time"] = nicetime(endTime)
 
    if not bid:
        print "You must provide a bridge ID using the --bid option."
        exit()
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

    Text = "Event Driven Version\nSummary of " + nicedate(startTime) + " from 6am\n"
    selectedSeries = []
    allSeries = []

    # useful stuff available to everything
    doorDebug = False
    if doors:
        doorDebug = True
    uptimeDebug = False
    showerDebug = False
    INOUT = "fubar"
    gotUpTime = 0
    gotUp = False
    bedtime = -1
    teleOn = False

    for series in pts:
        #if ("power" in series["name"].lower() 
        #    or ("pir" in series["name"].lower() and "binary" in series["name"].lower())
        #    or "tv" in series["name"].lower() 
        #    or ("door" in series["name"].lower() and "binary" in series["name"].lower())): 
        # and not "outside" in series["name"].lower():
        selectedSeries.append(series)
    for item in selectedSeries:
        #if not "connected" in item["name"].lower():
        for point in item["points"]:
            if point[i_time] >= startTime*1000 and point[i_time]/1000 <=startTime + oneDay:
                allSeries.append({"time":point[i_time], "name": item["name"], "value": point[i_data]})
    allSeries.sort(key=operator.itemgetter('time'))

    prevpt = {}

    state = "WFDTO_U"
    prevState = "foo"
    prevEvent = {}
    event = {}
    doorOpenTime = 0
    doorCloseTime = 0
    doorString2 = "\nFront Door\n"
    pirCount = 0
    doorList = []
    prevBedroomOccTime = 0
    # uptime
    uptimeString = ""
    upFifo = []
    # busyness
    K = {"Morning":0, "Afternoon":0, "Evening":0, "Night":0}
    H = {"Morning":0, "Afternoon":0, "Evening":0, "Night":0}
    L = {"Morning":0, "Afternoon":0, "Evening":0, "Night":0}
    bed = {"Morning":0, "Afternoon":0, "Evening":0, "Night":0}
    bath = {"Morning":0, "Afternoon":0, "Evening":0, "Night":0}
    busyString = "\nActivity levels\n"
    A1 = {}
    #bedtime
    latestOne = {} 
    inBed = False
    bedtimeString = "   Can't find bedtime"
    #wanders
    wanderWindow = 15*oneMinute
    wanderTimes = []
    wanderString = ""
    wanderStart = 0
    bStr = "weeble" #"bedtime"
    # tv
    teleOnTimes = []
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
    #teleOnFor = []
    teleOnTime = 0
    teleOn = False
    teleString = ""
    microOnTimes = []
    microOnTime = 0
    microString = ""
    toasterOnTimes = []
    toasterOnTime = 0
    toasterString = ""
    # showers
    bathroomSeries =[] 
    showerTimes = []
    prevK = []
    prevH = 0
    prevT = 0
    prevjH = 0
    prevjT = 0
    noMoreShowersTillItFalls = False
    showerString = "No showers found"
    occupied = False
    occStart = 0
    #occWindow = 1000*oneMinute*20 # cause there can be a lag between occupancy and rising H
    occWindow = 1000*oneMinute*158 # cause there can be a lag between occupancy and rising H
    # lights
    bathLuma = 0
    bedLuma = 0
    loungeLuma = 0
    lumaWarning = False
    lumaStr = ""

    f = bid + "n_activity"
    try:
	with open(f, 'r') as a:
	    A1 = json.load(a)
	#print "Got activity: file", json.dumps(A1, indent=4)
    except:
	print "No activity: file"
    if not A1:
	A1["Morning"] = []
	A1["Afternoon"] = []
	A1["Night"] = []
	A1["Evening"] = []

    for pt in allSeries: # main loop
        #print nicetime(pt["time"]/1000), "next event is", pt["value"], "on", pt["name"]
        if pt == prevpt:
            #print nicetime(pt["time"]/1000), "*** Ignoring duplicate event", pt["value"], "on", pt["name"]
            continue
        prevpt = pt

    # lights
        if "lum" in pt["name"].lower():
	    if "bathroom" in pt["name"].lower():
	        bathLuma = pt["value"]
	    elif "bedroom" in pt["name"].lower():
		bedLuma = pt["value"]
	    elif "lounge" in pt["name"].lower():
		loungeLuma = pt["value"]
	    if inBed and pt["time"] > bedtime + oneHour*1000: 
		if bathLuma > 10:
		    lumaStr = lumaStr + "bathroom "
	        if loungeLuma > 10:
		    lumaStr = lumaStr + "lounge "


    # showers
    #for pt in allSeries: # main loop
	if (("bathroom" in pt["name"].lower() or "shower" in pt["name"].lower())
	    and "binary" in pt["name"].lower()
	    and pt["value"] == 1): # reset occStart for every p 
	    #if not occupied:
	    #	print nicetime(pt["time"]/1000), "occStart set by:",  pt["name"] 
	    occupied = True
	    occStart = pt["time"]
	elif pt["time"] > occStart + occWindow: # noise from everything else as a clock
	    #if occupied:
	    #	print nicetime(pt["time"]/1000), "empty set by:",  pt["name"] 
	    occupied = False

	if (("bathroom" in pt["name"].lower() or "shower" in pt["name"].lower())
	    and "humidity" in pt["name"].lower()):
            if prevH <> 0 and pt["value"] > prevH: 
		bathroomSeries.append({"time": pt["time"], "value": pt["value"], "occ":occupied})
		if showerDebug:
		    print nicetime(pt["time"]/1000), "H risen from", prevH, "to", pt["value"], "occ:", occupied
	    else: # p H fell
		if len(bathroomSeries) > 1 and not noMoreShowersTillItFalls:
		    if showerDebug:
			for i in bathroomSeries:
			    print nicetime(i["time"]/1000), "i", i["value"]
		    for j in bathroomSeries:
			if showerDebug:
			    print nicetime(j["time"]/1000), "j", j["value"], "nmstif:",noMoreShowersTillItFalls 
			#if (j["value"] - prevjH < 2  this is in the wrong place
			#    and (j["time"] - prevjT) > 18*oneMinute*1000 
			#    and noMoreShowersTillItFalls):
			#    #and pt["time"]>occStart):
			#    print nicetime(j["time"]/1000), "nmstif:", noMoreShowersTillItFalls, "h rose by",\
		        #	j["value"] - prevjH, "at", nicetime(prevjT/1000), "in", (j["time"] - prevjT)/1000/60, "minutes - so pretending it fell"   
			#    noMoreShowersTillItFalls = False
			#else:
			#    print "not pretending dh:",j["value"] - prevH, "dt:",(j["time"] - prevT)/1000/60, "mins"  
			prevjH = j["value"]
			prevjT = j["time"]
		        for k in bathroomSeries: 
			    if k["time"] > j["time"] and not noMoreShowersTillItFalls:
				if showerDebug:
				    print "                    k", k["value"], "at", nicetime(k["time"]/1000), "with occStart at",\
					nicetime(occStart/1000), "k_occ:", k["occ"]
				deltaT = (k["time"] - j["time"])/1000/60
				deltaH = k["value"] - j["value"] 
				# two gradients
				# for dh under 10, we require shorter times (dt = m1*dh + c1)
				# for dh >10 we allow more time to capture the sudden jumps after a long time
				m1 = 10
				c1 = -19
				m2 = 54
				c2 = -429
				if (deltaT < 360 and deltaH > 1 and 
				    ((deltaH <= 10 and deltaT <= m1*deltaH +c1) 
				    or (deltaH > 10 and deltaT < m2*deltaH + c2))):
				    if k["occ"]:
				        print "**nSHOWER at :", nicetime(prevT/1000),\
					    "k_time:", nicetime(k["time"]/1000),\
  					    "dh:", k["value"] - j["value"], \
					    "dt:",(k["time"] - j["time"])/1000/60
				        noMoreShowersTillItFalls = True
				        showerTimes.append(k["time"])
				    else:
					if showerDebug:
					    print "No show shower at j:", nicetime(j["time"]/1000), "k:", nicetime(k["time"]/1000),\
						"cause dt=", deltaT, "dh=", deltaH
				else:
				    if showerDebug:
					print "No shower at j:", nicetime(j["time"]/1000), "k:", nicetime(k["time"]/1000),\
					"cause dt=", deltaT, "dh=", deltaH
	        noMoreShowersTillItFalls = False
	        bathroomSeries = [{"time": pt["time"], "value": pt["value"]}]
       	        #if showerDebug:
	        #    print nicetime(pt["time"]/1000), "H fell from", prevH, "to", pt["value"]
	    prevT = pt["time"]
	    prevH = pt["value"]



    # tv and appliances
    #for pt in allSeries: # main loop
	if "tv" in pt["name"].lower() and "power" in pt["name"].lower():
	    if pt["value"] > 10 and not teleOn:
		teleOn = True
		print "tele on at", nicehours(pt["time"]/1000), "power:", pt["value"], "on", pt["name"]
		teleOnTime = pt["time"]
	    elif pt["value"] < 10:
		if teleOn:
		    teleOnTimes.append({"ontime": nicehours(teleOnTime/1000), "offtime":nicehours(pt["time"]/1000)})
		    print "tele off at", nicehours(pt["time"]/1000), "power:", pt["value"],\
			"was on for", (pt["time"]-teleOnTime)/60/1000, "minutes"
		else:
		    print "Warning: tele went off twice"
		teleOn = False
	if "oven" in pt["name"].lower() and "power" in pt["name"].lower():
	    if pt["value"] > 300:
		if pt["time"] > ovenOnTime + 10*oneMinute*1000:
		    ovenOnTimes.append(nicehours(pt["time"]/1000))
		    print "oven on at", nicehours(pt["time"]/1000), "power:", pt["value"], "on", pt["name"]
		ovenOnTime = pt["time"]
	if "cooker" in pt["name"].lower() and "power" in pt["name"].lower()and "power" :
	    if pt["value"] > 300:
		if pt["time"] > cookerOnTime + 10*oneMinute*1000:
		    #print "cooker on at", nicehours(pt["time"]/1000), "power:", pt["value"]
		    cookerOnTimes.append(nicehours(pt["time"]/1000))
		cookerOnTime = pt["time"]
	if "washer" in pt["name"].lower() and "power" in pt["name"].lower()and "power" :
	    if pt["value"] > 200:
		if pt["time"] > washerOnTime + 15*oneMinute*1000:
		    washerOnTimes.append(nicehours(pt["time"]/1000))
		    #print "washer on at", nicehours(pt["time"]/1000), "power:", pt["value"]
		washerOnTime = pt["time"]
	if "microwave" in pt["name"].lower()and "power" in pt["name"].lower():
	    if pt["value"] > 1000:
		if pt["time"] > microOnTime + 5*oneMinute*1000:
		    microOnTimes.append(nicehours(pt["time"]/1000))
		    #print "microwave on at", nicehours(pt["time"]/1000), "power:", pt["value"]
		microOnTime = pt["time"]
	if "kettle"  in pt["name"].lower()and "power" in pt["name"].lower():
	    if pt["value"] == prevKettlePower:
		print "Kettle point", nicehours(pt["time"]/1000), "kettle point ignored. Power:", pt["value"]
	    elif pt["value"] > 1000:
		if pt["time"] > kettleOnTime + 5*oneMinute*1000:
		    if kettleOn: # Odd behaviour on the kettle - doesn't always go off in between ons, Probably due to zwave reset
			print "WARNING: Kettle already on at", nicehours(pt["time"]/1000), "power:", pt["value"], "ignoring and setting to off"
			kettleOn = False
		    else:
			kettleOnTimes.append(nicehours(pt["time"]/1000))
			kettleOn = True
			print "Kettle on at", nicehours(pt["time"]/1000), "power:", pt["value"]
		kettleOnTime = pt["time"]
	    else:
		kettleOn = False
	    prevKettlePower = pt["value"]
	if "toaster"  in pt["name"].lower()and "power" in pt["name"].lower():
	    if pt["value"] > 1000:
		if pt["time"] > toasterOnTime + 5*oneMinute*1000:
		    toasterOnTimes.append(nicehours(pt["time"]/1000))
		    #print "toaster on at", nicehours(pt["time"]/1000), "power:", pt["value"]
		toasterOnTime = pt["time"]

    # Front door
    #for pt in allSeries: # main loop
        if ("entry_exit" not in pt["name"].lower() 
	    and "binary" in pt["name"].lower() 
	    and ("door" in pt["name"].lower() or "pir" in pt["name"].lower() or "movement" in pt["name"].lower())):
            if ("pir" in pt["name"].lower()  or "movement" in pt["name"].lower()) and pt["value"] == 0:
                continue
	    PIR = False
	    doorClosed = False
	    doorOpened = False
	    if ("front" in pt["name"].lower() and pt["value"] == 1 or
		("utility" in pt["name"].lower() and "door" in pt["name"].lower()) and pt["value"] == 1):
		doorOpened = True
		doorOpenTime = pt["time"]
		if doorDebug:
		    print nicetime(pt["time"]/1000), pt["name"], " - Door opened, state=", state, "io:", INOUT
	    elif ("front" in pt["name"].lower() and pt["value"] == 0 or
		("utility" in pt["name"].lower() and "door" in pt["name"].lower()) and pt["value"] == 0):
		doorClosed = True
		doorCloseTime = pt["time"]
		if doorDebug:
		    print nicetime(pt["time"]/1000), pt["name"], " - Door closed, state=", state, "io:", INOUT
		if doorCloseTime - doorOpenTime > 1000*oneMinute*10:
		    doorString2 =  doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Note - door was open for "\
			+ str((doorCloseTime - doorOpenTime)/1000/60) + " minutes\n"
		    if doorDebug:
		        print nicetime(pt["time"]/1000), "********************** Door was open for", \
			    (doorCloseTime - doorOpenTime)/1000/60, "minutes"
	    elif ((("pir" in pt["name"].lower() or "movement" in pt["name"].lower()) 
		and "binary" in pt["name"].lower() 
		and "outside" not in pt["name"].lower() 
		and pt["value"] == 1)
		or "door" in pt["name"].lower()):
		PIR = True # PIR or non-front doors
		if doorDebug:
		    print nicetime(pt["time"]/1000), "PIR set by:", pt["name"]
            #else:
            #	print nicetime(pt["time"]/1000), "mystery point on:", pt["name"]
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
		#    print nicetime(pt["time"]/1000), state, pt["value"], "on", pt["name"]
		if INOUT == "in":
		    state = "WFDTC" if doorOpened else "WFDTO"
		    #print nicetime(pt["time"]/1000), state, INOUT, "with", pt["value"], "on", pt["name"]
		elif INOUT == "out":
		    if doorOpened:
			state = "WFDTC"
		    elif PIR:
			state = "ERROR"
		else:
		    print nicetime(pt["time"]/1000), "unknown IO", state, pt["value"], "on", pt["name"]
		    state = "ERROR"
	    elif state == "WFDTC":
		if doorDebug:
		    print nicetime(pt["time"]/1000), state, INOUT, pt["value"], "on", pt["name"],"..."
		if doorClosed:
		    state = "WFPIR" 
		elif PIR and INOUT == "out":
		    state = "WFDTC"
		    INOUT = "maybe"
		#else:
		#    print nicetime(pt["time"]/1000), state, pt["value"], "on", pt["name"],"dropped through"
		#print "WFDTC - door closed, IO:", INOUT, "next state = ", state

	    elif state == "WFPIR":
		if doorDebug:
		    print "WFPIR, IO:", INOUT, "Pcnt", pirCount
		if PIR and pt["time"] > doorCloseTime + 20*1000:#  and pt["time"] - doorCloseTime < 1000*30*oneMinute:
		    pirCount+=1
		if pirCount >= 1:
		    pirCount = 0
		    state = "WFDTO"
		    if INOUT == "in":
			if PIR and pt["time"] > doorCloseTime + 20*1000:#  and pt["time"] - doorCloseTime < 1000*30*oneMinute:
                            if doorDebug:
			        print nicetime(doorCloseTime/1000), "** Didn't leave at", nicetime(doorCloseTime/1000),\
				    "waited ", (pt["time"] - doorCloseTime)/1000/60, "minutes for PIR\n"
			    doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, didn't leave\n"
			    doorList.append({nicehours(doorCloseTime/1000):"Door closed, didn't leave"})
			elif PIR and pt["time"] > doorCloseTime + 20*1000 and pt["time"] - doorCloseTime > 1000*oneHour*2:
                            if doorDebug:
			        print nicetime(doorCloseTime/1000), "** Didn't leave at", nicetime(doorCloseTime/1000), "but no activity for", \
				    (pt["time"] - doorCloseTime)/1000/60, "minutes\n"
			    doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, didn't leave (but no activity for "\
				+ str((pt["time"]-doorCloseTime)/1000/60) + " minutes - asleep?)\n"
			    doorList.append({nicehours(doorCloseTime/1000):"Door closed, didn't leave (but no activity for " +
				str((pt["time"]-doorCloseTime)/1000/60) + " minutes - asleep?)"})
		    elif INOUT == "out" or INOUT =="maybe":
                        if doorDebug:
			    print nicetime(doorCloseTime/1000), "** Came in at", nicetime(doorCloseTime/1000),\
			        "waited", (pt["time"] - doorCloseTime)/1000/60, "minutes for PIR\n"
			doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, came in\n"
			doorList.append({nicehours(doorCloseTime/1000):"Door closed, came in"}) 
			INOUT = "in"
		    else:
			print nicetime(pt["time"]/1000), "Strange value on INOUT", INOUT
		elif doorOpened:
		    if doorDebug:
			print "door opened whilst WFPIR"
		    state = "WFDTC"
		    if doorOpenTime - doorCloseTime < 1000*121:
			if doorDebug:
			    print nicetime(doorCloseTime/1000), "door opened again too soon:", \
				(pt["time"]-doorCloseTime)/1000, "seconds later - not concluding"
		    elif INOUT == "in":
			if doorDebug:
			    print nicetime(doorCloseTime/1000), "** Went out at", nicetime(doorCloseTime/1000), "cause door opened again", \
			        (pt["time"]-doorCloseTime)/1000, "seconds later\n"
			if teleOn:
			    doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, went out (TV still on)\n"
			else:
			    doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, went out\n"
			doorList.append({nicehours(doorCloseTime/1000):"Door closed, went out"})
			INOUT = "out"
		    elif INOUT == "maybe": 
			if doorDebug:
			    print nicetime(doorCloseTime/1000), "** In and out at", nicetime(doorCloseTime/1000), "cause door opened again", \
			        (pt["time"]-doorCloseTime)/1000/60, "minutes later\n"
			doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, in and out\n"
			doorList.append({nicehours(doorCloseTime/1000):"Door closed, in and out"}) 
			INOUT = "out"
		    elif INOUT == "out":
			if doorDebug:
			    print nicetime(doorCloseTime/1000), "** Didn't come in at", nicetime(doorCloseTime/1000), "cause door opened again", \
			        (pt["time"]-doorCloseTime)/1000/60, "minutes later\n"
			#doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, came in but didn't stay\n"
			doorList.append({nicehours(doorCloseTime/1000):"Door closed, came in but didn't stay"}) 
			INOUT = "out"
		    else:
			print nicetime(pt["time"]/1000), "Strange value in WFPIR. INOUT:", INOUT
	    elif state == "ERROR":
		print nicetime(pt["time"]/1000), state, "Somethings wrong!"
		print nicetime(pt["time"]/1000), state, pt["value"], "on", pt["name"]
		
	    else:
		print nicetime(pt["time"]/1000), "Unknown state", state, "on", pt["name"]
    # uptime
    #for pt in allSeries: # main loop
        if "bed" not in pt["name"].lower() and "binary" in pt["name"].lower() and pt["value"] == 1:
            if (pt["time"]/1000 > startTime 
                and pt["time"]/1000 < startTime +6*oneHour 
                and not gotUp):
                if len(upFifo) <= 10:
                    if uptimeDebug:
                        print nicetime(pt["time"]/1000), "Appending morning activity x in", pt["name"]
                    gotUpTime = pt["time"]
                    upFifo.append(gotUpTime)
                else:
		    last = upFifo[-1]
		    first = upFifo.pop(0) # zero is correct!
		    #print "popped:", nicetime(first/1000)
                    if uptimeDebug:
		        for i in upFifo:
			    print nicetime(i/1000)
		    #print "len:", len(upFifo), "last:", nicetime(last/1000), "popped last:", nicetime(first/1000)
		    #print "last-first:", nicehours(last/1000), "-", nicehours(first/1000), "=", (last-first)/1000/60, "minutes"
		    if (last-first) <= 1000*oneMinute*26:
			gotUp = True
			gotUpTime = first
			uptimeString = "   Got up at " + nicehours(gotUpTime/1000) + "\n"
			D["gotUpTime"] = nicehours(gotUpTime/1000)
			print "*** Got up at:", nicetime(first/1000), "dt=", (last-first)/1000/60, "minutes"
		    else:
                        if uptimeDebug:
			    print "Rejecting:", nicetime(first/1000), "cause it's 10 items in", (last-first)/1000/60, "minutes"
    #busyness - just count the ones 
    #for pt in allSeries: # main loop
        if pt["time"] > startTime*1000 and pt["time"] <= 1000*(startTime + 6*oneHour):
	    slot = "Morning"
        elif pt["time"] >= 1000*(startTime + 6*oneHour)  and pt["time"] <= 1000*(startTime + 12*oneHour):
	    slot = "Afternoon"
        elif pt["time"] >= 1000*(startTime + 12*oneHour) and pt["time"] <= 1000*(startTime + 18*oneHour):
	    slot = "Evening"
        elif pt["time"] >= 1000*(startTime + 18*oneHour) and pt["time"] <= 1000*(startTime + 24*oneHour):
	    slot = "Night"
	else:
	    print "**** business: something's wrong with the time"
	if ("pir" in pt["name"].lower()
	    and "binary" in pt["name"].lower()
	    and pt["value"] == 1):
            if "bedroom" in pt["name"].lower():
		bed[slot]+=1
	    elif "kitchen" in pt["name"].lower():
	        K[slot]+=1
	    elif "hall" in pt["name"].lower():
		H[slot]+=1
	    elif "lounge" in pt["name"].lower():
		L[slot]+=1
	    elif "bathroom" in pt["name"].lower():
		bath[slot]+=1
	    else:
	        print "****************missing room:", pt["name"]

    # bedtime and wanders
    #for pt in allSeries: # main loop
        #if pt["time"] > (startTime + 15*oneHour)*1000 and pt["time"] < 1000*(startTime + 20*oneHour) and not inBed:
        if pt["time"] > (startTime + 15*oneHour)*1000 and pt["time"] < 1000*endTime and not inBed:
            if (("pir" in pt["name"].lower() or "movement" in pt["name"].lower())
	        and "binary" in pt["name"].lower()
	        and "bedroom" not in pt["name"].lower()
	        and pt["value"] == 1):
                latestOne = pt # the latest non-bedroom PIR activity
                # print nicetime(pt["time"]/1000), "potential latestOne at", nicetime(pt["time"]/1000), "in", pt["name"]
	    else: # use noise from everything else to give us the time
		# print nicetime(pt["time"]/1000), "tick set by:", pt["name"] 
		if latestOne:
		    if pt["time"] - latestOne["time"] > 1000*oneMinute*61:
                        bedtimeString = "   Went to bed at " + nicehours(latestOne["time"]/1000)
                        D["bedTime"] = nicehours(latestOne["time"]/1000)
                        print "Went to bed at:", nicetime(latestOne["time"]/1000), "from", latestOne["name"],\
			    "delayMins=",(pt["time"] - latestOne["time"])/1000/60 
			inBed = True
			bedTime = latestOne["time"]
			if teleOn:
			    bedtimeString = bedtimeString + " (but TV still on)"
		    #else:
		    #	print "not gone to bed at", nicetime(latestOne["time"]/1000), "cause delay mins = ", (pt["time"] - latestOne["time"])/1000/60
        # wanders
        if inBed:
	    bStr = "bedtime"
	    if (pt["time"] > bedTime + 1000*oneMinute
		and "bedroom" not in pt["name"].lower()
		and ("pir" in pt["name"].lower() or "door" in pt["name"].lower())
		and "binary" in pt["name"].lower()
		and pt["value"] == 1 
		and pt["time"] > wanderStart + wanderWindow*1000):
		wanderStart = pt["time"]
		wanderTimes.append(nicehours(wanderStart/1000))
		print nicetime(pt["time"]/1000), "new wander in", pt["name"], "bedtime:", nicetime(bedTime/1000)
	    #else:
	    #    print nicetime(w["time"]/1000), "No wander in", w["name"], "bedtime:", nicetime(bedtime/1000)
        """
	else:
	    bStr = "1am"
	    if (pt["time"] > (startTime + oneHour*19)*1000 # look after 1am if no bedtime
		and "bedroom" not in pt["name"].lower()
		and ("pir" in pt["name"].lower() or "door" in pt["name"].lower())
		and "binary" in pt["name"].lower()
		and pt["value"] == 1 
		and pt["time"] > wanderStart + wanderWindow*1000):
		wanderStart = pt["time"]
		wanderTimes.append(nicehours(wanderStart/1000))
		print nicetime(pt["time"]/1000), "new wander in", pt["name"], "no bedtime:"
	"""
    # end of showers
    if showerTimes:
	showerString = "      Shower taken at: "
	for x in showerTimes:
	    showerString = showerString + nicehours(x/1000) 
	    if showerTimes.index(x) < len(showerTimes)-1:
		showerString = showerString + ", " 
	    else:
		showerString = showerString + "\n"
    else:
	showerString = "      No showers found\n"

    # end of tv
    if teleOnTimes:
	D["tele"] = teleOnTimes
	teleString = "      Tele on at:\n"
	for i in teleOnTimes:
	    teleString = teleString + "        " + i["ontime"] + " until " + str(i["offtime"]) + "\n"
	    print "     Tele on at", i["ontime"], "til", i["offtime"]
    else:
	D["tele"] = "no tele data"
	teleString = "      No tele data\n"
	print "no tele"
    if teleOn:
	print "Looks like tele was on all night from:", nicetime(teleOnTime/1000)
    # end of appliances
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

    # end of bedtime and wanders
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
    elif inBed:
	D["wanders"] = "No wanders outside the bedroom after  " + bStr
	wanderString = "No wanders outside the bedroom after " + bStr + "\n"
    #bedtimeString = bedtimeString + "\n"
    # end of bedtime
    if not inBed:
	print "Something's wrong with bedtime"

    # end of busyness
    aTotals = {}
    for i in ["Morning", "Afternoon", "Evening", "Night"]:
        #print "i:", json.dumps(i, indent=4)
        levelStr = "No average yet"
        ave = -2
        aTotals[i] = bed[i]+K[i]+H[i]+L[i]+bath[i] 
	if len(A1[i])>0:
	    ave = sum(A1[i])/len(A1[i]) 
	    if  aTotals[i] == 0:
		busyString = busyString + i + " activity: None" + " (" + str(aTotals[i]) + ")\n"
	    elif aTotals[i] < ave + 1 and aTotals[i] > ave -1 :
	       busyString = busyString + "   " + i + " activity: Average" + " (" + str(aTotals[i]) + ")\n"
	    elif aTotals[i] <= ave:
	       busyString = busyString + "   " + i + " activity: Below average" + " (" + str(aTotals[i]) + ")\n"
	    else:
	       busyString = busyString + "   " + i + " activity: Above average" + " (" + str(aTotals[i]) + ")\n"
	else:
	    busyString = busyString + "   " + i + " activity: No average yet" + " (" + str(aTotals[i]) + ")\n"
	    
	print i, " activity   =", aTotals[i], "ave=", ave 
	if  aTotals[i] == 0:
	    print "      *** No movement: asleep or out or missing data"
	    busyString = busyString + "     *** No movement: asleep or out or missing data\n"
	else:
	    bathroomPercent = 100*bath[i]/(aTotals[i])
	    bedPercent = 100*bed[i]/aTotals[i]
	    loungePercent = 100*L[i]/aTotals[i]
	    kitchenPercent = 100*K[i]/aTotals[i]
	    hallPercent =  100*H[i]/aTotals[i]
	    busyString = busyString + "      Bathroom: " + str(bathroomPercent) + "%\n"
	    busyString = busyString + "      Bedroom:  " + str(bedPercent) + "%\n"
	    busyString = busyString + "      Lounge:   " + str(loungePercent) + "%\n"
	    busyString = busyString + "      Kitchen:  " + str(kitchenPercent) + "%\n"
	    busyString = busyString + "      Hall:     " + str(hallPercent) + "%\n"
	A1[i].append(aTotals[i])

	"""
	if slotCount == 1:
	    A["Morning"] = [{"activity":bedOnes+K+H+L+b},{"bedPercent":bedPercent},{"loungePercent":loungePercent},
		{"kitchenPercent":kitchenPercent},{"hallPercent":hallPercent},{"bathroomPercent":bathroomPercent}]
	if slotCount == 2:
	    A["Afternoon"] = [{"activity":bedOnes+K+H+L+b},{"bedPercent":bedPercent},{"loungePercent":loungePercent},
		{"kitchenPercent":kitchenPercent},{"hallPercent":hallPercent},{"bathroomPercent":bathroomPercent}]
	if slotCount == 3:
	    A["Evening"] = [{"activity":bedOnes+K+H+L+b},{"bedPercent":bedPercent},{"loungePercent":loungePercent},
		{"kitchenPercent":kitchenPercent},{"hallPercent":hallPercent},{"bathroomPercent":bathroomPercent}]
	if slotCount == 4:
	    A["Night"] = [{"activity":bedOnes+K+H+L+b},{"bedPercent":bedPercent},{"loungePercent":loungePercent},
		{"kitchenPercent":kitchenPercent},{"hallPercent":hallPercent},{"bathroomPercent":bathroomPercent}]
        """

    try:
	with open(f, 'w') as outfile:
	    json.dump(A1, outfile, indent=4)
    except:
	print "Failed to write activity file"

    #D["activity"] = A


    # end of uptime: needs to run after we've been through all the points
    if allSeries and not gotUp:   
        uptimeString = "   Can't find getting up time\n"
        D["gotUpTime"] = "Can't find getting up time"
        print "not got up yet by", nicetime(pt["time"]/1000)

    # end of doors: needs to run after we've been through all the points
    if not pt:
	print "Doors: No events - quiet day!!" 
    else:
	print nicetime(pt["time"]/1000), "Doors: No more events - bombed out in", state, INOUT, "with", pt["value"], "on", pt["name"] 
	if state == "WFPIR" and INOUT == "maybe":
	    print nicetime(pt["time"]/1000), "So: Came in at", nicetime(doorCloseTime/1000), "but didn't stay and not back before 6am" 
	    doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, came but didn't stay and not back before 6am\n"
	    doorList.append({nicehours(doorCloseTime/1000):"Door closed, came but didn't stay and not back before 6am"})
	elif state == "WFPIR" and INOUT == "in":
	    print nicetime(pt["time"]/1000), "So: Went out at", nicetime(doorCloseTime/1000), "and not back before 6am"
	    doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, went out - not back before 6am\n"
	    doorList.append({nicehours(doorCloseTime/1000):"Door closed, , went out - not back before 6am"})

	elif INOUT == "out" and (state == "WFDTO" or state == "WFPIR"):
	    print nicetime(pt["time"]/1000), "and stayed out"
	elif state == "WFDTO" and INOUT == "in":
	    print nicetime(pt["time"]/1000), "and stayed in"
	else:
	    print nicetime(pt["time"]/1000), "Doors: Bombed out in", state, "whilst IO=", INOUT 

    D["Front Door"] = doorList

    # end of lights
    if not lumaWarning:
        print "Gone to bed with", lumaStr, "lights on?"
	lumaWarning = True

    #Text = Text + uptimeString + teleString + bedtimeString + busyString + wanderString + doorString2 + "\n"
    Text = Text + uptimeString + teleString + kettleString + microString + washerString + ovenString + cookerString + showerString + bedtimeString + busyString + wanderString + doorString2 + "\n"
    #+ fridgeString 
    print Text 
    
    #exit()
    #print "D:", json.dumps(D, indent=4)
    #f = bid + "_" + nicedate(startTime) + "_from_6am.txt"
    #try:
    #    with open(f, 'w') as outfile:
    #        json.dump(D, outfile, indent=4)
    #except:
    #    print "Failed to write file"


    # Create message container - the correct MIME type is multipart/alternative.
    try:
        msg = MIMEMultipart('alternative')
        #msg['Subject'] = "Event Driven Activity for bridge "+bid+" from "+nicedate(startTime)+" to "+nicedate(endTime)+" (InfluxDB/"+db+")"
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

