#!/usr/bin/env python
# room_occupancy.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#
# Usage:-
# ./dyh.py --user bridges@continuumbridge.com --password Mucht00f@r --bid BID36 --db "SCH" --daysago 5 --to "martin.sotheran@continuumbridge.com"

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

# fake a config file for now
config = {
    #"cid": "CID164",
    #"cid_key": "3fb46d8ebcS+Klsv89yk6XgedLEqT0r8S7gqJODZFy7H0Zflj+kPxLyLpWSI4OIm",
    #"twilio_account_sid": "AC72bb42908df845e8a1996fee487215d8",
    #"twilio_auth_token": "717534e8d9e704573e65df65f6f08d54",
    #"twilio_phone_number": "+441183241580",
    #"service_providers": {
    #    "pumpco": {
    #        "url": "https://gaia.cnect.to/PumpHouse/rest/v1/devices/"
    #       }
    "dburl": "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/",
    "dbrootp": "27ff25609da60f2d",
    "mail": {
	"password": "Mucht00f@r",
	"from": " <bridges@continuumbridge.com>",
	"user": "bridges@continuumbridge.com"
    },
    "bridges":{
	"BID264": {
	    "database": "Bridges",
	    "name_in_database": "Bungalow",
            "friendly_name": "DYH",
            "email": "martin.sotheran@continuumbridge.com",
            "config": {}
	}
    }
}

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

def postInfluxDB(dat, bid):
    try:
        if "database" in config["bridges"][bid]:
            url = config["dburl"] + "db/" + config["bridges"][bid]["database"] + "/series?u=root&p=" + config["dbrootp"]
	else:
	    url = config["dburl"] + "db/Bridges/series?u=root&p=" + config["dbrootp"]
        headers = {'Content-Type': 'application/json'}
	status = 0
	print "ifx url", url
        print"Posting to InfluxDB:", json.dumps(dat, indent=4)
	r = requests.post(url, data=json.dumps(dat), headers=headers)
	status = r.status_code
        if status !=200:
	    print "warning - POSTing failed, status:", status
    except Exception as ex:
        print "warning - postInfluxDB problem, type:", type(ex), "exception:", str(ex.args)


@click.command()
@click.option('--user', nargs=1, help='User name of email account.')
@click.option('--password', prompt='Password', help='Password of email account.')
@click.option('--bid', nargs=1, help='The bridge ID to list.')
@click.option('--db', nargs=1, help='The database to look in')
@click.option('--to', nargs=1, help='The address to send the email to.')
@click.option('--daysago', nargs=1, help='How far back to look')
@click.option('--doors', nargs=1, help='whether to debug doors')
@click.option('--shower_mail', nargs=1, help='whether to send Pete & I a shower mail')
@click.option('--mail', nargs=1, help='whether to send a mail')
@click.option('--writetoifx', nargs=1, help='whether to write to influx')

def dyh (user, password, bid, to, db, daysago, doors, mail, shower_mail, writetoifx):
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

    Text = "Summary of " + nicedate(startTime) + " from 6am\n"
    selectedSeries = []
    allSeries = []

    # useful stuff available to everything
    bedtimeDebug = False
    doorDebug = False
    if doors:
        doorDebug = True
    uptimeDebug = False
    showerDebug = False
    wanderDebug = False
    teleOn = False
    INOUT = "fubar"
    gotUpTime = 0
    gotUp = False
    inBed = False
    rooms = []
    doors = []

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
    uptimeString = "   Can't find getting up time\n"
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
    bedtimeString = "   Can't find bedtime\n"
    #wanders
    wanderWindow = 15*oneMinute
    wanderTimes = []
    wanders = []
    wstr = "" 
    wanderStart = 0
    bStr = "bedtime"
    # tv
    teleOnTimes = []
    teleOnTime = 0
    teleString = ""
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
    prevCookerPower = -1
    kettleOnTimes = []
    kettleString = ""
    kettleOnTime = 0
    prevKettlePower = -1
    kettleOn = False
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
    hallLuma = 0
    kitchenLuma = 0
    loungeLuma = 0
    lumaWarned = False
    lumaWarning = False
    lumaStr = ""
    # random bits'n'pieces
    ifxData = []
    dupCount = 0
    sensorsFound = {}
    missingRooms = []

    f = bid + "n_activity"
    try:
	with open(f, 'r') as a:
	    A1 = json.load(a)
	print "Read activity ok", f
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
	    dupCount+=1
            continue
        prevpt = pt


	if "in_bed" in pt["name"].lower():
	    print "***** ", nicetime(pt["time"]/1000), "found inBed =", pt["value"]

    # WIP
    # collect rooms so that ultimately this can be independent of dyh
    # A bridge app would need to know which is the bedroom and the outside door.
    # It'll infer which is the bathroom by finding humidity
	if ("binary" in pt["name"].lower() or 
	    "humidity" in pt["name"].lower() or
	    "power" in pt["name"].lower() or
	    "temperature" in pt["name"].lower() or
	    "luminance" in pt["name"].lower()):
	    foo = pt["name"].split('/')
	    place = foo[1]
	    char = foo[2]
	    if place not in sensorsFound: 
		sensorsFound[place] = [char]
	        #print "new place: sensorFound:", json.dumps(sensorsFound, indent=4)
	    if char not in sensorsFound[place]:
		sensorsFound[place].append(char)
	        #print "New char: sensorFound:", json.dumps(sensorsFound, indent=4)


    # lights
        if "lum" in pt["name"].lower():
	    if "bathroom" in pt["name"].lower():
	        bathLuma = pt["value"]
	    elif "bedroom" in pt["name"].lower():
		bedLuma = pt["value"]
	    elif "lounge" in pt["name"].lower():
		loungeLuma = pt["value"]
	    elif "kitchen" in pt["name"].lower():
		kitchenLuma = pt["value"]
	    elif "hall" in pt["name"].lower():
		hallLuma = pt["value"]
	    if (inBed and pt["time"] > bedTime + 30*oneMinute*1000 
		and not lumaWarned): 
		if not (pt["time"] > wanderStart and pt["time"] < wanderStart + wanderWindow*1000):
		    lumaWarned = True
		    if bathLuma > 10:
			lumaStr = lumaStr + "bathroom "
			print nicetime(pt["time"]/1000), "bathroom lights still on",(pt["time"]-bedTime)/1000/60, "minutes after bedtime"
		    if bedLuma > 10:
			if lumaStr:
			    lumaStr = lumaStr + "& bedroom "
			else:
			    lumaStr = lumaStr + "bedroom "
		    if loungeLuma > 10:
			if lumaStr:
			    lumaStr = lumaStr + "& lounge "
			else:
			    lumaStr = lumaStr + "lounge "
		    if kitchenLuma > 10:
			if lumaStr:
			    lumaStr = lumaStr + "& kitchen "
			else:
			    lumaStr = lumaStr + "kitchen "
		    if hallLuma > 9:
			if lumaStr:
			    lumaStr = lumaStr + "& hall "
			else:
			    lumaStr = lumaStr + "hall "
		else:
		    print "Note: ", nicehours(pt["time"]/1000), "lights on but we're in a wander"

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
				if (deltaT < 360 and deltaH > 2 and 
				    ((deltaH <= 10 and deltaT <= m1*deltaH +c1) 
				    or (deltaH > 10 and deltaT < m2*deltaH + c2))):
				    if k["occ"]:
					if showerDebug:
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
	    if pt["value"] > 7 and not teleOn:
		teleOn = True
		#print "tele on at", nicehours(pt["time"]/1000), "power:", pt["value"], "on", pt["name"]
		teleOnTime = pt["time"]
	    elif pt["value"] < 4:
		if teleOn:
		    teleOnTimes.append({"ontime": nicehours(teleOnTime/1000), "offtime":nicehours(pt["time"]/1000)})
		    #print "tele off at", nicehours(pt["time"]/1000), "power:", pt["value"],\
		    #	"was on for", (pt["time"]-teleOnTime)/60/1000, "minutes"
		else:
		    print "*** Warning: tele went off twice at", nicetime(pt["time"]/1000) 
		teleOn = False
	if "oven" in pt["name"].lower() and "power" in pt["name"].lower():
	    if pt["value"] > 300:
		if pt["time"] > ovenOnTime + 10*oneMinute*1000:
		    ovenOnTimes.append(nicehours(pt["time"]/1000))
		    #print "oven on at", nicehours(pt["time"]/1000), "power:", pt["value"], "on", pt["name"]
		ovenOnTime = pt["time"]
	if "cooker" in pt["name"].lower() and "power" in pt["name"].lower()and "power" :
	    if pt["value"] == prevCookerPower:
		print "*** Cooker point", nicehours(pt["time"]/1000), "cooker point ignored. Power:", pt["value"]
	    elif pt["value"] > 300:
		if pt["time"] > cookerOnTime + 10*oneMinute*1000:
		    #print "cooker on at", nicehours(pt["time"]/1000), "power:", pt["value"]
		    cookerOnTimes.append(nicehours(pt["time"]/1000))
		cookerOnTime = pt["time"]
	    prevCookerPower = pt["value"]
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
		print "*** Kettle point", nicehours(pt["time"]/1000), "kettle point ignored. Power:", pt["value"]
	    elif pt["value"] > 1000:
		if pt["time"] > kettleOnTime + 5*oneMinute*1000:
		    if kettleOn: # Odd behaviour on the kettle - doesn't always go off in between ons, Probably due to zwave reset
			print "WARNING: Kettle already on at", nicehours(pt["time"]/1000), "power:", pt["value"], "ignoring and setting to off"
			kettleOn = False
		    else:
			kettleOnTimes.append(nicehours(pt["time"]/1000))
			kettleOn = True
			#print "Kettle on at", nicehours(pt["time"]/1000), "power:", pt["value"]
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
		if doorOpenTime == 0:
		    doorString2 =  doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed: Note - was the door open all night?\n"
		    if doorDebug:
		        print nicetime(pt["time"]/1000), "********************** Door was open all night!?!"
		elif doorCloseTime - doorOpenTime > 1000*oneMinute*10:
		    doorString2 =  doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Note - door was open for "\
			+ str((doorCloseTime - doorOpenTime)/1000/60) + " minutes\n"
		    if doorDebug:
		        print nicetime(pt["time"]/1000), "********************** Door was open for", \
			    (doorCloseTime - doorOpenTime)/1000/60, "minutes. closeTime=", nicetime(doorCloseTime/1000)
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
		    print nicetime(pt["time"]/1000), state, "io:", INOUT, pt["value"], "on", pt["name"],"..."
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
		    print nicetime(pt["time"]/1000), "WFPIR, IO:", INOUT, "Pcnt", pirCount
		if PIR and pt["time"] > doorCloseTime + 20*1000:#  and pt["time"] - doorCloseTime < 1000*30*oneMinute:
		    pirCount+=1
		if pirCount >= 1:
		    pirCount = 0
		    state = "WFDTO"
		    if INOUT == "in":
			if PIR and pt["time"] > doorCloseTime + 20*1000:#  and pt["time"] - doorCloseTime < 1000*30*oneMinute:
                            if doorDebug:
			        print nicetime(pt["time"]/1000), "** Didn't leave at", nicetime(doorCloseTime/1000),\
				    "waited ", (pt["time"] - doorCloseTime)/1000/60, "minutes for PIR\n"
			    doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, didn't leave\n"
			    doorList.append({nicehours(doorCloseTime/1000):"Door closed, didn't leave"})
			elif PIR and pt["time"] > doorCloseTime + 20*1000 and pt["time"] - doorCloseTime > 1000*oneHour*2:
                            if doorDebug:
			        print nicetime(pt["time"]/1000), "** Didn't leave at", nicetime(doorCloseTime/1000), "but no activity for", \
				    (pt["time"] - doorCloseTime)/1000/60, "minutes\n"
			    doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, didn't leave (but no activity for "\
				+ str((pt["time"]-doorCloseTime)/1000/60) + " minutes - asleep?)\n"
			    doorList.append({nicehours(doorCloseTime/1000):"Door closed, didn't leave (but no activity for " +
				str((pt["time"]-doorCloseTime)/1000/60) + " minutes - asleep?)"})
		    elif INOUT == "out" or INOUT =="maybe":
                        if doorDebug:
			    print nicetime(pt["time"]/1000), "** Came in at", nicetime(doorCloseTime/1000),\
			        "waited", (pt["time"] - doorCloseTime)/1000/60, "minutes for PIR\n"
			INOUT = "in"
			if (pt["time"] - doorCloseTime)/1000/60 > 10:
			    doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, came in  (but no activity for "\
			        + str((pt["time"] - doorCloseTime)/1000/60) + " minutes)\n"
			    doorList.append({nicehours(doorCloseTime/1000):"Door closed, came in"}) 
			else:
			    doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, came in\n"
			    doorList.append({nicehours(doorCloseTime/1000):"Door closed, came in"}) 
		    else:
			print nicetime(pt["time"]/1000), "Strange value on INOUT", INOUT
		elif doorOpened:
		    if doorDebug:
			print nicetime(pt["time"]/1000), "door opened whilst WFPIR"
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
			    doorList.append({nicehours(doorCloseTime/1000):"Door closed, went out (TV still on)"})
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
        #if (("bed" not in pt["name"].lower() and "binary" in pt["name"].lower() and pt["value"] == 1) try it including bedroom
        if (("binary" in pt["name"].lower() and pt["value"] == 1)
	    or ("front" not in pt["name"].lower() and "binary" in pt["name"].lower() and "door" in pt["name"].lower() and pt["value"] == 1)):
            if (pt["time"]/1000 > startTime 
                and pt["time"]/1000 < startTime +9*oneHour 
                and not gotUp):
                if len(upFifo) <= 10:
                    if uptimeDebug:
                        print nicetime(pt["time"]/1000), "Appending morning activity on", pt["name"]
                    gotUpTime = pt["time"]
                    upFifo.append(gotUpTime)
                else:
		    last = upFifo[-1]
		    first = upFifo.pop(0) # zero is correct!
		    #print "popped:", nicetime(first/1000)
                    #if uptimeDebug:
		    #    for i in upFifo:
		    #	    print nicetime(i/1000)
		    #print "len:", len(upFifo), "last:", nicetime(last/1000), "popped last:", nicetime(first/1000)
		    #print "last-first:", nicehours(last/1000), "-", nicehours(first/1000), "=", (last-first)/1000/60, "minutes"
		    # For the general case (any bridge), this needs to depend on a history of aggregate activity. Not just 26mins
		    if (last-first) <= 1000*oneMinute*26:
			gotUp = True
			if showerTimes:
			    for sh in showerTimes:
				print "Got up at", nicetime(gotUpTime/1000), "but showers = ", nicetime(sh/1000)
				if sh < first:
				    gotUpTime = sh
				    uptimeString = "   Got up at " + nicehours(gotUpTime/1000) + " for a shower\n"
				    D["gotUpTime"] = nicehours(gotUpTime/1000)
				    ifxData.append({"name": bid + "/In_bed", "points": [[gotUpTime, 3]]})
				    if uptimeDebug:
					print "*** Got up for shower at:", nicetime(sh/1000)
			else:    
			    gotUpTime = first
			    uptimeString = "   Got up at " + nicehours(gotUpTime/1000) + "\n"
			    D["gotUpTime"] = nicehours(gotUpTime/1000)
			    ifxData.append({"name": bid + "/In_bed", "points": [[gotUpTime, 3]]})
			    if uptimeDebug:
				print "*** Got up at:", nicetime(first/1000), "dt=", (last-first)/1000/60, "minutes"
		    else:
                        if uptimeDebug:
			    print "Rejecting:", nicetime(first/1000), "cause it's 10 items in", (last-first)/1000/60, "minutes (need 26mins)"
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
	if (("pir" in pt["name"].lower() or "movement" in pt["name"].lower())
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
	    elif pt["name"] not in missingRooms:
		missingRooms.append(pt["name"])
	        print "****************missing room:", pt["name"]

    # bedtime
    #for pt in allSeries: # main loop
        if pt["time"] > (startTime + 14*oneHour+30*oneMinute)*1000 and pt["time"] < 1000*endTime and not inBed:
            if (("pir" in pt["name"].lower() or "movement" in pt["name"].lower())
	        and "binary" in pt["name"].lower()
	        and "bedroom" not in pt["name"].lower()
	        and pt["value"] == 1):
                latestOne = pt # a potential latest non-bedroom PIR activity
                if bedtimeDebug:
		    print nicetime(pt["time"]/1000), "potential latestOne at", nicetime(pt["time"]/1000), "in", pt["name"]
	    else: # use noise from everything else to give us the time
		# print nicetime(pt["time"]/1000), "tick set by:", pt["name"] 
		if latestOne:
		    if 1000*endTime - latestOne["time"] < 1000*oneMinute*35:
                        bedtimeString = "   Can't find bedtime - still up at " + nicehours(latestOne["time"]/1000) + "\n"
                        #D["bedTime"] = nicehours(latestOne["time"]/1000)
			if bedtimeDebug:
			    print "Still up at:", nicetime(latestOne["time"]/1000), "in", latestOne["name"],\
				"delayMins=",(pt["time"] - latestOne["time"])/1000/60 
		    elif pt["time"] - latestOne["time"] > 1000*oneMinute*61:
                        bedtimeString = "   Went to bed at " + nicehours(latestOne["time"]/1000)
                        D["bedTime"] = nicehours(latestOne["time"]/1000)
			if bedtimeDebug:
			    print "Went to bed at:", nicetime(latestOne["time"]/1000), "from", latestOne["name"],\
				"delayMins=",(pt["time"] - latestOne["time"])/1000/60 
			inBed = True
			bedTime = latestOne["time"]
			ifxData.append({"name": bid + "/In_bed", "points": [[bedTime, 1]]})
			if teleOn:
			    bedtimeString = bedtimeString + "\n      TV still on"
		    elif bedtimeDebug:
		    	print "not gone to bed at", nicetime(latestOne["time"]/1000), "cause delay mins = ", (pt["time"] - latestOne["time"])/1000/60
        # wanders
        if inBed:
	    bStr = "bedtime"
	    if (pt["time"] > bedTime + 1000*oneMinute
		and "outside" not in pt["name"].lower()
		and "bedroom" not in pt["name"].lower()
		#and ("pir" in pt["name"].lower() or "door" in pt["name"].lower() or "movement" in pt["name"].lower())
		and ("pir" in pt["name"].lower() or "movement" in pt["name"].lower()) # bathroom door blows open
		and "binary" in pt["name"].lower()
		and "hall" not in pt["name"].lower()
		and pt["value"] == 1):
		if pt["time"] > wanderStart + wanderWindow*1000: # a new wander
		    wanderStart = pt["time"]
		    wanderTimes.append(nicehours(wanderStart/1000))
		    wanders.append({"wanderStart": wanderStart, "wanderSensors":[pt["name"]]})
		    if wanderDebug:
			print nicetime(pt["time"]/1000), "new wander in", json.dumps(wanders, indent=4), "bedtime:", nicetime(bedTime/1000)
		if pt["time"] > wanderStart and pt["time"] < wanderStart + wanderWindow*1000:
		    # we're in a wander
		    if pt["name"] not in wanders[-1]["wanderSensors"]:
			wanders[-1]["wanderSensors"].append(pt["name"])
	    #else:
	    #    print nicetime(w["time"]/1000), "No wander in", w["name"], "bedtime:", nicetime(bedtime/1000)

    # end of showers
    if showerTimes:
	showerString = "      Shower taken at: "
	longShowerString = bid + " showers taken at:\n"
	for x in showerTimes:
	    showerString = showerString + nicehours(x/1000) 
	    longShowerString = longShowerString + "   " + nicetime(x/1000) + "\n" 
	    if showerTimes.index(x) < len(showerTimes)-1:
		showerString = showerString + ", " 
	    else:
		showerString = showerString + "\n"
    else:
	longShowerString = "  No showers\n"
	showerString = "      No showers\n"

    # end of tv
    if teleOnTimes:
	D["tele"] = teleOnTimes
	teleString = "      Tele on at:\n"
	for i in teleOnTimes:
	    teleString = teleString + "        " + i["ontime"] + " until " + str(i["offtime"]) + "\n"
	    #print "     Tele on at", i["ontime"], "til", i["offtime"]
    elif not teleOn:
	D["tele"] = "no tele data"
	teleString = "      No tv\n"
    if teleOn:
	if not teleOnTimes:
	    teleString = "      Tele on at:\n"
        teleString = teleString + "        " + nicehours(teleOnTime/1000) + " until after 6am\n"
        print "**Tele on at", nicetime(teleOnTime/1000), "til at least 6am"

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
    else:
	D["kettle"] = "No kettle data"
	kettleString = "      No kettle data\n"
	#print "      no kettle data"
    if microOnTimes:
	D["microwave"] = microOnTimes
	microString = "      Microwave on at: "
	for i in microOnTimes:
	    microString = microString + i 
	    if microOnTimes.index(i) < len(microOnTimes)-1:
		microString = microString + ", "
	    else:
		microString = microString + "\n"
	    #print "     Microwave on at", i
    else:
	D["microwave"] = "No microwave data"
	microString = "      No microwave\n"
    if washerOnTimes:
	D["washer"] = washerOnTimes
	washerString = "      Washer on at: "
	for i in washerOnTimes:
	    washerString = washerString + i 
	    if washerOnTimes.index(i) < len(washerOnTimes)-1:
		washerString = washerString + ", "
	    else:
		washerString = washerString + "\n"
	    #print "     Washer on at", i
    else:
	D["washer"] = "no washer data"
	washerString = "      No washing\n"
	#print "      no washer"
    if ovenOnTimes:
	D["oven"] = ovenOnTimes
	ovenString = "      Oven on at: "
	for i in ovenOnTimes:
	    ovenString = ovenString + i 
	    if ovenOnTimes.index(i) < len(ovenOnTimes)-1:
		ovenString = ovenString + ", "
	    else:
		ovenString = ovenString + "\n"
	    #print "     Oven on at", i
    else:
	D["oven"] = "no oven data"
	ovenString = "      No oven\n"
	#print "      no oven"
    if cookerOnTimes:
	D["cooker"] = cookerOnTimes
	cookerString = "      Cooker on at: "
	for i in cookerOnTimes:
	    cookerString = cookerString + i
	    if cookerOnTimes.index(i) < len(cookerOnTimes)-1:
		cookerString = cookerString + ", "
	    else:
		cookerString = cookerString + "\n"
	    #print "     Cooker on at", i
    else:
	D["cooker"] = "no cooker data"
	cookerString = "      No cooker\n"
	#print "      no cooker"

    # new end of wanders - WIP
    if wanders:
        #wanders.sort(key=operator.itemgetter('time'))
	wstr = "\n      Wanders outside the bedroom after " + bStr + " at:\n"
	for x in wanders:
	    if wanderDebug:
	        print "end of wanders:", nicetime(x["wanderStart"]/1000), "in", json.dumps(x["wanderSensors"], indent=4)
	    wstr = wstr + "         " + nicehours(x["wanderStart"]/1000) + ": to the "
	    for y in x["wanderSensors"]:
		if len(x["wanderSensors"]) == 1:
		    wstr = wstr + getsensor(y) + ".\n"
		elif x["wanderSensors"].index(y) == len(x["wanderSensors"])-1:
		    wstr = wstr + "and " + getsensor(y) + ".\n"
		elif x["wanderSensors"].index(y) == len(x["wanderSensors"])-2:
		    wstr = wstr + getsensor(y) + " "
		else:
		    wstr = wstr + getsensor(y) + ", "

    elif inBed:
	D["wanders"] = "No wanders outside the bedroom after  " + bStr
	wstr = "\n   No wanders outside the bedroom after " + bStr + "\n"

    """
    # end of wanders
    if wanderTimes:
	wanderString = "Wanders outside the bedroom after " + bStr + " at: "
	for x in wanderTimes:
	    #print "wanderTimes:", x
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
    """
    #bedtimeString = bedtimeString + "\n"
    # end of bedtime
    if not inBed:
	print "Warning: Something's wrong with bedtime"

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
		busyString = busyString + "   " + i + " activity: None" + " (" + str(aTotals[i]) + ")\n"
	    elif aTotals[i] < ave + 1 and aTotals[i] > ave -1 :
	       busyString = busyString + "   " + i + " activity: Average" + " (" + str(aTotals[i]) + ")\n"
	    elif aTotals[i] <= ave:
	       busyString = busyString + "   " + i + " activity: Below average" + " (" + str(aTotals[i]) + ")\n"
	    else:
	       busyString = busyString + "   " + i + " activity: Above average" + " (" + str(aTotals[i]) + ")\n"
	else:
	    busyString = busyString + "   " + i + " activity: No average yet" + " (" + str(aTotals[i]) + ")\n"
	    
	#print i, " activity   =", aTotals[i], "ave=", ave 
	if  aTotals[i] == 0:
	    #print "      *** No movement: asleep or out or missing data"
	    busyString = busyString + "     *** No movement: asleep or out or missing data\n"
	else:
	    bathroomPercent = 100*bath[i]/(aTotals[i])
	    bedPercent = 100*bed[i]/aTotals[i]
	    loungePercent = 100*L[i]/aTotals[i]
	    kitchenPercent = 100*K[i]/aTotals[i]
	    hallPercent =  100*H[i]/aTotals[i]
	    busyString = busyString + "      Bathroom: " + str(bathroomPercent) + "%\n"
	    busyString = busyString + "      Bedroom:  " + str(bedPercent) + "%\n"
	    busyString = busyString + "      Lounge:    " + str(loungePercent) + "%\n"
	    busyString = busyString + "      Kitchen:    " + str(kitchenPercent) + "%\n"
	    busyString = busyString + "      Hall:         " + str(hallPercent) + "%\n"
	A1[i].append(aTotals[i])

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
        print "Note: not got up yet by", nicetime(pt["time"]/1000)

    # end of doors: needs to run after we've been through all the points
    if not pt:
	print "Doors: No events - quiet day!!" 
    else:
	if doorDebug:
	    print nicetime(pt["time"]/1000), "Doors: No more events - bombed out in", state, INOUT, "with", pt["value"], "on", pt["name"] 
	if state == "WFPIR" and INOUT == "maybe":
	    if doorDebug:
		print nicetime(pt["time"]/1000), "So: Came in at", nicetime(doorCloseTime/1000), "but didn't stay and not back before 6am" 
	    doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, came but didn't stay and not back before 6am\n"
	    doorList.append({nicehours(doorCloseTime/1000):"Door closed, came but didn't stay and not back before 6am"})
	elif state == "WFPIR" and INOUT == "in":
	    if doorDebug:
		print nicetime(pt["time"]/1000), "So: Went out at", nicetime(doorCloseTime/1000), "and not back before 6am"
	    doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, went out - not back before 6am\n"
	    doorList.append({nicehours(doorCloseTime/1000):"Door closed, , went out - not back before 6am"})

	elif INOUT == "out" and (state == "WFDTO" or state == "WFPIR"):
	    if doorDebug:
		print nicetime(pt["time"]/1000), "and stayed out"
	elif state == "WFDTO" and INOUT == "in":
	    if doorDebug:
		print nicetime(pt["time"]/1000), "and stayed in"
	else:
	    if doorDebug:
		print nicetime(pt["time"]/1000), "Doors: Bombed out in", state, "whilst IO=", INOUT 

    D["Front Door"] = doorList

    # end of lights
    if lumaStr and not lumaWarning:
        bedtimeString = bedtimeString +  "\n      " + lumaStr + "lights still on"
	print "Gone to bed with", lumaStr, "lights on?"
	lumaWarning = True

    print "*** ignored", dupCount, "duplicate points"
    print "*** sensorsFound:", json.dumps(sensorsFound, indent=4)

    #Text = Text + uptimeString + teleString + kettleString + microString + washerString + ovenString + cookerString + showerString + bedtimeString + wstr + busyString + doorString2 + "\n" # removed cooker 'till fixed
    Text = Text + uptimeString + teleString + kettleString + microString + washerString + ovenString + showerString + bedtimeString + wstr + busyString + doorString2 + "\n"

    nText = Text + "Missing is:\n" + cookerString
    print "\n", nText 
    
    #exit()
    #print "D:", json.dumps(D, indent=4)
    #f = bid + "_" + nicedate(startTime) + "_from_6am.txt"
    #try:
    #    with open(f, 'w') as outfile:
    #        json.dump(D, outfile, indent=4)
    #except:
    #    print "Failed to write file"

    if writetoifx:
	try:
	    dat = ifxData #body["d"]
	    for d in dat:
		d["columns"] = ["time", "value"]
		if "name_in_database" in config["bridges"][bid]:
		    s = d["name"].split("/")
		    d["name"] = config["bridges"][bid]["name_in_database"]
		    for ss in s[1:]:
			d["name"] += "/" + ss
	    dd = dat
	    print "Posting to postInfluxDB:", json.dumps(dd, indent=4)
	    postInfluxDB(dd, bid)
	except Exception as ex:
	    print "warning - Problem processing data to be posted, exception:", str(type(ex)), str(ex.args)

    """
    2017-04-05 12:41:38,611 DEBUG Posting to InfluxDB: [
        {
	    "points": [
	        [
		    1491392497658, 
		    1266
                ]
	    ], 
	    "name": "BID11/Outside_Door_PIR/luminance", 
            "columns": [
	        "time", 
	        "value"
            ]
	}
    ]   
    """

    # Create message container - the correct MIME type is multipart/alternative.
    if mail:
	try:
	    msg = MIMEMultipart('alternative')
	    msg['Subject'] = "Activity for bungalow from 6am "+nicedate(startTime)
	    #msg['Subject'] = "Event Driven Activity for bridge "+bid+" from "+nicedate(startTime)+" to "+nicedate(endTime)+" (InfluxDB/"+db+")"
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
	    print "Summary mail sent to:", to
	except Exception as ex:
	    print "sendMail problem. To:", to, "type: ", type(ex), "exception: ", str(ex.args)
    if shower_mail:
	try:
	    to = "martin.sotheran@continuumbridge.com, peter.claydon@continuumbridge.com"
	    e_txt = "Now running as part of dyh so start = 6am\nAnd unfortunately it's a mail for each bridge\n\n"
	    showerString = e_txt + bid + ":" + showerString
	    msg = MIMEMultipart('alternative')
	    msg['Subject'] = bid + ": Showers in 24hrs since 6am "+nicedate(startTime-oneDay)
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
	    part1 = MIMEText(longShowerString, 'plain')
	    #part2 = MIMEText(htmlText, 'html')
	
	    msg.attach(part1)
	    #msg.attach(part2)
	    mail = smtplib.SMTP('smtp.gmail.com', 587)
	    mail.ehlo()
	    mail.starttls()
	    mail.login(user, password)
	    mail.sendmail(user, recipients, msg.as_string())
	    mail.quit()
	    print "Shower mail sent to:", to
	except Exception as ex:
	    print "sendMail problem. To:", to, "type: ", type(ex), "exception: ", str(ex.args)
    
                  
if __name__ == '__main__':
    dyh()
