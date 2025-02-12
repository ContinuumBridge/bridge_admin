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
#import difflib
from itertools import cycle
import urllib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage
from influxdb import InfluxDBClient

#Constants
oneMinute          = 60
oneHour            = 60 * oneMinute
oneDay             = oneHour * 24
dburl = "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/"

# fake a config file for now
config = {
    #"twilio_account_sid": "AC72bb42908df845e8a1996fee487215d8",
    #"twilio_auth_token": "717534e8d9e704573e65df65f6f08d54",
    #"twilio_phone_number": "+441183241580",
    "dburl2": "ec2-54-171-237-126.eu-west-1.compute.amazonaws.com",
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
"""
def unidiff_output(expected, actual):
    expected=expected.splitlines(1)
    actual=actual.splitlines(1)
    diff=difflib.unified_diff(expected, actual)
    return ''.join(diff)
"""

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
    #s = yesterday + " 05:30:00"
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
@click.option('--warning_mails', nargs=1, help='whether to send Pete & I a data warning mail')
@click.option('--mail', nargs=1, help='whether to send a mail')
@click.option('--writetoifx', nargs=1, help='whether to write to influx')

def dyh (user, password, bid, to, db, daysago, doors, mail, warning_mails, writetoifx):
    daysAgo = int(daysago) #0 # 0 means yesterday
    startTime = start() - daysAgo*60*60*24
    endTime = startTime + oneDay
    #indeces
    i_time = 0
    i_data = 2
    D = {}
    pts = {}
    IOpts = []
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
    client = InfluxDBClient(host=config["dburl2"], port=8086, database=db)


    l = client.get_list_database()
    print("Databases: {}".format(l))

    #from pprint import pprint
    #pprint(dir(client))

    query = "SELECT * FROM " + bid + " where time > " + str(earlyStartTime) + "s and time <" + str(endTime) + "s"
    #query = "SELECT \"value\" FROM " + bid + " WHERE (\"characteristic\" = 'binary') AND time >= now()-2d AND time <= now()"
    #query = "SELECT * FROM " + bid + " WHERE (\"characteristic\" = 'binary') AND time >= now()-2d AND time <= now()"

    result = client.query(query, epoch="ms")
    print "Activity fetched:", len(list(result.get_points())), "points"
    print "items:", result.items()
    print "keys:", result.keys()


    res = list(result.get_points())
    #print "res:", json.dumps(res, indent=4)

    # Get the Spur data
    """
    data: [
    {
        'fields':{'value': 1}, 
        'tags': {
            'device': u'Martins_615_at_DYH', 
            'list': u'ContinuumBridge_Buttons'
             }, 
        'time': 1509272876000, 
        'measurement': 'wakeup'
    }]
    """
    client.switch_database("Spur")
    #meas = list(client.query("SHOW MEASUREMENTS").get_points())
    #print "meas:", json.dumps(meas, indent=4)

    query = "SELECT * FROM Visitor_checked_in where time > " + str(earlyStartTime) + "s and time <" + str(endTime) + "s"
    in_result = client.query(query, epoch="ms")
    print "checked_in  fetched:", len(list(in_result.get_points())), "points"
    #print "in items:", in_result.items()
    #print "in keys:", in_result.keys()
    in_res = list(in_result.get_points())
    #print "in res:", json.dumps(in_res, indent=4)

    for m in in_res:
        IOpts.append({"time":m["time"], "name":"Visitor_checked_in", "value":m["value"], "characteristic":"Visitor_checked_in"})

    # and the outs
    query = "SELECT * FROM Visitor_checked_out where time > " + str(earlyStartTime) + "s and time <" + str(endTime) + "s"
    out_result = client.query(query, epoch="ms")
    print "checked_out fetched:", len(list(out_result.get_points())), "points"
    #print "out items:", out_result.items()
    #print "out keys:", out_result.keys()
    out_res = list(out_result.get_points())
    #print "out res:", json.dumps(out_res, indent=4)


    for m in out_res:
        IOpts.append({"time":m["time"], "name":"Visitor_checked_out", "value":m["value"], "characteristic":"Visitor_checked_out"})

    #print "IOpts:", json.dumps(IOpts, indent=4)

    """
    q = "select * from /" + bid + "/ where time >" + str(earlyStartTime) + "s and time <" + str(endTime) + "s"
    query = urllib.urlencode ({'q':q})
    print "Requesting list of series from", nicetime(earlyStartTime), "to", nicetime(endTime)
    url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
    print "fetching from:", url
    r = requests.get(url)
    pts = r.json()
    #print json.dumps(r.json(), indent=4)

    db1 = "Spur"
    subString = "615"
    q1 = "select * from /" + subString + "/ where time >" + str(earlyStartTime) + "s and time <" + str(endTime) + "s"
    query = urllib.urlencode ({'q':q1})
    print "Requesting list of series from", nicetime(earlyStartTime), "to", nicetime(endTime)
    url = dburl + "db/" + db1 + "/series?u=root&p=27ff25609da60f2d&" + query
    print "fetching from:", url
    try:
        r1 = requests.get(url)
        IOpts = r1.json()
    except:
        print "Warning: no Spur points"

    print len(IOpts), "series fetched\n"
    #print "IOpts:", json.dumps(IOpts, indent=4)
    """

    Text = "Summary of " + nicedate(startTime) + " from " + nicehours(startTime) + "am\n"
    selectedSeries = []
    allSeries = []

    # useful stuff available to everything
    bedtimeDebug =   False
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
    """
    {
        "points": [
            [
                1506937771104,
                20246390001,
                30.37
            ]
        ],
        "name": "BID264/Cooker/temperature",
        "columns": [
            "time",
            "sequence_number",
            "value"
        ]
    },
    """
    for checks in IOpts:
        if checks["time"] >= startTime*1000 and checks["time"]/1000 <=startTime + oneDay and "checked" in checks["name"]:
            allSeries.append({"time":checks["time"], "name": checks["name"], "value": checks["value"], "char":checks["characteristic"]})
        else:
            print "Not appending", json.dumps(checks,indent=4)
    """
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
    """

    """ As above, we're expecting a simple time, name, value """
    appliances =[]
    door_switches = []
    PIRs = []
    PIR_states = {}
    for x in res:
        if x["characteristic"] != "connected" and x["characteristic"] != "battery":
            # for ease we'll just build the old path format
            full_name = bid + "/" + x["sensor"] + "/" + x["characteristic"]
            if x["time"] >= startTime*1000 and x["time"]/1000 <=startTime + oneDay:
                if x["value"] != None:
                    allSeries.append({"time":x["time"], "name":full_name, "sensor":x["sensor"], "value": x["value"], "char":x["characteristic"]})
                elif x["fvalue"] != None:
                    allSeries.append({"time":x["time"], "name":full_name, "sensor":x["sensor"], "value": x["fvalue"], "char":x["characteristic"]})
                else:
                    print "WARNING: point is neither float nor int", json.dumps(x, indent=4)
            # Let's see what sensors we have
            if x["characteristic"] == "power":
                if x["sensor"] not in appliances:
                    print "Found a new TKB", x["sensor"]
                    appliances.append(x["sensor"])
                if x["sensor"] in door_switches:
                    door_switches.remove(x["sensor"])
            elif x["characteristic"] == "luminance" or x["characteristic"] == "humidity":
                if x["sensor"] not in PIRs:
                    print "Found a new PIR:", x["sensor"]
                    PIRs.append(x["sensor"])
                if x["sensor"] in door_switches:
                    door_switches.remove(x["sensor"])
            elif x["characteristic"] == "binary":
                if x["sensor"] not in door_switches and x["sensor"] not in PIRs and x["sensor"] not in appliances:
                    print "Found a new ES:", x["sensor"]
                    door_switches.append(x["sensor"])
    for x in PIRs:
        PIR_states[x] = {"value":0,"time":0}

    print "Found sensors:\n  ", PIRs, "\n  ", appliances, "\n  ", door_switches

    allSeries.sort(key=operator.itemgetter('time'))

    #print "allseries:", json.dumps(allSeries, indent=4)
    pt = {}
    prevpt = {}

    # doors
    state = "WFDTO_U"
    prevState = "foo"
    prevEvent = {}
    event = {}
    doorOpenTime = 0
    doorCloseTime = 0
    doorString2 = "\nFront Door\n"
    doorString3 = "\nFront Door\n"
    pirCount = 0
    doorList = []
    prevBedroomOccTime = 0
    visitor = False
    checkInTime = 0
    checkOutTime = 0
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
    inBedroom = 0
    #wanders
    wanderWindow = 15*oneMinute
    wanderTimes = []
    wanders = []
    wstr = "" 
    b_wstr = "" 
    wanderStart = 0
    bStr = "bedtime"
    b_wanderTimes = []
    b_wanders = []
    b_wanderStart = 0
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
    bathLuma = 2 # benefit of the doubt - start the day with light on
    bedLuma = 0
    hallLuma = 0
    kitchenLuma = 0
    loungeLuma = 0
    lumaWarned = False
    lumaWarning = False
    lumaStr = ""
    # for checking if data_client is ok
    data_client_ok = False
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
	print "No activity file"
    if not A1:
	A1["Morning"] = []
	A1["Afternoon"] = []
	A1["Night"] = []
	A1["Evening"] = []

    for pt in allSeries: # main loop
        # print nicetime(pt["time"]/1000), "next event is", pt["value"], "on", pt["name"]
        if pt == prevpt:
            print nicetime(pt["time"]/1000), "*** Ignoring duplicate event", pt["value"], "on", pt["name"]
	    dupCount+=1
            continue
        prevpt = pt
        # data_client check
        if pt["time"]/1000 > endTime - 6*oneHour:
            #print nicetime(pt["time"]/1000), "Got a pt in last 6 hours so client is ok", pt["name"], pt["value"]
            data_client_ok = True

	if "in_bed" in pt["name"].lower():
	    print "***** ", nicetime(pt["time"]/1000), "found inBed =", pt["value"]

	# this needs to be up here due to the continue in doors
        if "bedroom" in pt["name"].lower() and "pir" in pt["name"].lower() and "binary" in pt["name"].lower():
            inBedroom = pt["value"]
            #print nicetime(pt["time"]/1000), "Setting inBedroom to:", inBedroom

        """
    # WIP
    # What room are we in
        if pt["sensor"] in PIRs and pt["char"] == "binary": # and pt["value"] == 1:
            if PIR_states[pt["sensor"]]["value"] != 1 and pt["value"] == 1:
                #print nicetime(pt["time"]/1000), "in", json.dumps(PIR_states, indent=4) #pt["sensor"]
                if lostAt != 0:
                    if pt["sensor"] != lostFrom:
                        print nicetime(pt["time"]/1000), "*** lost at", nicetime(lostAt/1000), "from", lostFrom, "but found in", pt["sensor"], "after", (pt["time"] - lostAt)/1000, "seconds"
                    else:
                        print nicetime(pt["time"]/1000), "lost at", nicetime(lostAt/1000), "in", lostFrom, "for", (pt["time"] - lostAt)/1000, "seconds"
                    lostAt = 0
                #else:
                #    print nicetime(pt["time"]/1000), "entered", pt["sensor"]
                otherRooms = []
                for r in PIRs:
                    if PIR_states[r]["value"] == 1:# and (pt["time"] - PIR_states[r]["time"])/1000 > oneMinute:
                        otherRooms.append(r)
                #if otherRooms:
                #    print "    but still active in", otherRooms #r, "for", (pt["time"] - PIR_states[r]["time"])/1000, "seconds?"
            else:
                otherRooms = []
                for r in PIRs:
                    if PIR_states[r]["value"] == 1 and pt["sensor"] != r: # and (pt["time"] - PIR_states[r]["time"])/1000 > oneMinute:
                        otherRooms.append(r)
                if otherRooms:
                    #print "Left", pt["name"], "but still in", otherRooms
                    lostAt = 0 
                else:
                    lostAt =  pt["time"]
                    lostFrom = pt["sensor"]
                    #print nicetime(pt["time"]/1000), "Nowhere to be seen!", pt["sensor"], "->", pt["value"]
                    #print nicetime(pt["time"]/1000), "states:", json.dumps(PIR_states, indent=4) #pt["sensor"]
            PIR_states[pt["sensor"]]["value"] = pt["value"]
            PIR_states[pt["sensor"]]["time"] = pt["time"]
        """



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
	    if (inBed and pt["time"] > bedTime + 30*oneMinute*1000 and pt["time"] < bedTime + 60*oneMinute*1000 
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
            # note that the door can set occStart here. Leaving as is whilst the PIR's out of action
            if showerDebug:
	        if not occupied:
	    	    print nicetime(pt["time"]/1000), "occStart set by:",  pt["name"] 
	    if True: # bathLuma>1: no good checking luma now - needs to be before
		if showerDebug:
                    print nicetime(pt["time"]/1000), "Bathroom occupied with light on - setting occStart to now"
                occupied = True
	        occStart = pt["time"]
            else:
		if showerDebug:
                    print nicetime(pt["time"]/1000), "Bathroom occupied but light is out - so not setting occStart"
                occupied = False
	elif pt["time"] > occStart + occWindow: # noise from everything else as a clock
	    if occupied:
		if showerDebug:
	    	    print nicetime(pt["time"]/1000), "empty set by:",  pt["name"] 
	    occupied = False

	if (("bathroom" in pt["name"].lower() or "shower" in pt["name"].lower())
	    and "humidity" in pt["name"].lower()):
            if prevH <> 0 and pt["value"] > prevH: 
		bathroomSeries.append({"time": pt["time"], "value": pt["value"], "occ":occupied, "lastOcc":occStart, "luma":bathLuma})
		if showerDebug:
		    print nicetime(pt["time"]/1000), "H risen from", prevH, "to", pt["value"], "occ:", occupied, ", bathLuma:", bathLuma
	    else: # p H fell
		if len(bathroomSeries) > 1 and not noMoreShowersTillItFalls:
		    if showerDebug:
			for i in bathroomSeries:
			    print nicetime(i["time"]/1000), "i", i["value"], "lastOcc:", nicetime(i["lastOcc"]/1000), "luma:", i["luma"]
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
				if (deltaT < 360 and deltaH > 6 and 
				    ((deltaH <= 10 and deltaT <= m1*deltaH +c1) 
				    or (deltaH > 10 and deltaT < m2*deltaH + c2))):
			            if k["occ"]: # and k["luma"]>0: # luma is a failed experiment - needs to be luma at lastOcc not k
				        if showerDebug:
				            print "**nSHOWER at :", nicetime(prevT/1000),\
					        "k_time:", nicetime(k["time"]/1000),\
						"dh:", k["value"] - j["value"], \
						"dt:",(k["time"] - j["time"])/1000/60, \
                                                "lastOcc:", nicetime(k["lastOcc"]/1000), \
                                                "bathLuma now:", k["luma"]
				        noMoreShowersTillItFalls = True
				        #showerTimes.append(k["time"])
				        showerTimes.append(k["lastOcc"])
 				    else:
				        if showerDebug:
					    print "No show shower at j:", nicetime(j["time"]/1000), "k:", nicetime(k["time"]/1000),\
					    "cause dt=", deltaT, "dh=", deltaH, "luma:", k["luma"]
				else:
				    if showerDebug:
					print "No shower at j:", nicetime(j["time"]/1000), "k:", nicetime(k["time"]/1000),\
					"cause dt=", deltaT, "dh=", deltaH
	        noMoreShowersTillItFalls = False
	        bathroomSeries = [{"time": pt["time"], "value": pt["value"], "lastOcc":0, "luma": bathLuma}]
       	        #if showerDebug:
	        #    print nicetime(pt["time"]/1000), "H fell from", prevH, "to", pt["value"]
	    prevT = pt["time"]
	    prevH = pt["value"]


    # tv and appliances
    #for pt in allSeries: # main loop
	if "tv" in pt["name"].lower() and "power" in pt["name"].lower():
	    if pt["value"] > 15 and not teleOn:
		teleOn = True
		print nicetime(pt["time"]/1000), "tele on,  power:", pt["value"]
		teleOnTime = pt["time"]
	    elif pt["value"] < 10:
		if teleOn:
		    teleOnTimes.append({"ontime":nicehours(teleOnTime/1000), "offtime":nicehours(pt["time"]/1000), "onFor":(pt["time"] - teleOnTime)/1000/60})
		    print nicetime(pt["time"]/1000), "tele off, power:", pt["value"],\
		    	"was on for", (pt["time"]-teleOnTime)/60/1000, "minutes"
		#else:
		#    print "*** Warning: tele went off twice at", nicetime(pt["time"]/1000) 
		teleOn = False
	if "oven" in pt["name"].lower() and "power" in pt["name"].lower():
	    if pt["value"] > 300:
		if pt["time"] > ovenOnTime + 10*oneMinute*1000:
		    ovenOnTimes.append(nicehours(pt["time"]/1000))
		    #print "oven on at", nicehours(pt["time"]/1000), "power:", pt["value"], "on", pt["name"]
		ovenOnTime = pt["time"]
	if "cooker" in pt["name"].lower() and "power" in pt["name"].lower()and "power" :
            # EXTRA POWER CONDITION REMOVES SPURIOUS VALUE ON BRIDGE RESTART...!!!!!
	    if pt["value"] == prevCookerPower or (pt["value"] == 1872.04 and pt["time"] < 1000*(startTime + 4*oneHour)):
		print "*** Cooker point", nicehours(pt["time"]/1000), "cooker point ignored. Power:", pt["value"]
	    elif pt["value"] > 300:
		if pt["time"] > cookerOnTime + 10*oneMinute*1000:
		    #print "cooker on at", nicehours(pt["time"]/1000), "power:", pt["value"]
		    cookerOnTimes.append(nicehours(pt["time"]/1000))
		cookerOnTime = pt["time"]
	    prevCookerPower = pt["value"]
	if "washer" in pt["name"].lower() and "power" in pt["name"].lower()and "power" :
	    if pt["value"] > 60:
		if pt["time"] > washerOnTime + 15*oneMinute*1000:
		    washerOnTimes.append(nicehours(pt["time"]/1000))
		    print "washer on at", nicehours(pt["time"]/1000), "power:", pt["value"]
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
	    if pt["value"] > 700:
		if pt["time"] > toasterOnTime + 5*oneMinute*1000:
		    toasterOnTimes.append(nicehours(pt["time"]/1000))
		    #print "toaster on at", nicehours(pt["time"]/1000), "power:", pt["value"]
		toasterOnTime = pt["time"]

    # Front door
    #for pt in allSeries: # main loop
	if "checked_in" in pt["name"].lower():
	    checkInTime = pt["time"]
	    print nicetime(pt["time"]/1000), "visitor checked in"
	    if visitor == True:
		print nicetime(pt["time"]/1000), "*** WARNING double check in"
		doorList.append({"time":checkInTime, "text":":                      visitor checked in (again)"})
		doorString2 = doorString2 + "   " + nicehours(checkInTime/1000) + ":                      visitor checked in (again)\n"
	    else:
		doorList.append({"time":checkInTime, "text":":                      visitor checked in"})
		doorString2 = doorString2 + "   " + nicehours(checkInTime/1000) + ":                      visitor checked in\n"
	    visitor = True
        elif "checked_out" in pt["name"].lower():
	    print nicetime(pt["time"]/1000), "visitor checked out"
	    checkOutTime = pt["time"]
	    if visitor == False:
		doorList.append({"time":checkOutTime, "text":":                      visitor checked out (again)"})
		doorString2 = doorString2 + "   " + nicehours(checkOutTime/1000) + ":                      visitor checked out (again)\n"
		print nicetime(pt["time"]/1000), "*** WARNING double check out"
	    else:
		doorList.append({"time":checkOutTime, "text":":                      visitor checked out"})
		doorString2 = doorString2 + "   " + nicehours(checkOutTime/1000) + ":                      visitor checked out\n"
	    visitor = False
        elif ("entry_exit" not in pt["name"].lower() 
	    and "binary" in pt["name"].lower() 
	    and ("door" in pt["name"].lower() or "pir" in pt["name"].lower() or "movement" in pt["name"].lower())):
            if ("pir" in pt["name"].lower()  or "movement" in pt["name"].lower()) and pt["value"] == 0:
                continue # Note that this causes pir zeros to be missed by all subsequent code
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
		    #doorList.append({"time":doorCloseTime, "text":": Door closed: Note - was the door open all night?"})
		    doorString2 =  doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed: Note - was the door open all night?\n"
		    if doorDebug:
		        print nicetime(pt["time"]/1000), "********************** Door was open all night!?!"
		elif doorCloseTime - doorOpenTime > 1000*oneMinute*10:
		    doorList.append({"time":doorCloseTime, "text":": Note - door was open for "	+ str((doorCloseTime - doorOpenTime)/1000/60) + " minutes"})
		    doorString2 =  doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Note - door was open for "\
			+ str((doorCloseTime - doorOpenTime)/1000/60) + " minutes\n"
		    if doorDebug:
		        print nicetime(pt["time"]/1000), "********************** Door was open for", \
			    (doorCloseTime - doorOpenTime)/1000/60, "minutes. closeTime=", nicetime(doorCloseTime/1000)
	    elif (
		    (
			("pir" in pt["name"].lower() or "movement" in pt["name"].lower()) 
			and "binary" in pt["name"].lower() 
			and "outside" not in pt["name"].lower()
		    )
		or ("door" in pt["name"].lower() and "front" not in pt["name"].lower())
		and pt["value"] == 1):
		if doorDebug and PIR == False:
		    print nicetime(pt["time"]/1000), "PIR set by:", pt["name"]
		PIR = True # PIR or non-front doors
            #else:
            #	print nicetime(pt["time"]/1000), "mystery point on:", pt["name"]
	    prevState = state

	    if state == "WFDTO_U":
		if PIR:
		    if doorDebug:
			print state, nicetime(pt["time"]/1000), "Setting INOUT to in"
		    INOUT = "in"
		    state = "WFDTO"
		elif doorOpened:
		    INOUT = "out"
		    state = "WFDTC"
		elif doorClosed:
		    """ don't expect door to close as the first event
                        so go round startup loop until something sensible happens
                    """
                    print nicetime(pt["time"]/1000), "********************** Door closed whilst waiting for it to open at start" 
		    state = "WFDTO_U"
	    elif state == "WFDTO":
		if doorOpened:
		    state = "WFDTC"
		    #print nicetime(pt["time"]/1000), state, INOUT, "with", pt["value"], "on", pt["name"]
		elif INOUT == "out" and PIR:
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
				print nicetime(pt["time"]/1000), "** didn't leave at", nicetime(doorCloseTime/1000),\
				    "waited ", (pt["time"] - doorCloseTime)/1000/60, "minutes for pir\n"
			    doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, didn't leave\n"
		    	    doorList.append({"time":doorCloseTime, "text":": Door closed, didn't leave"})
			elif PIR and pt["time"] > doorCloseTime + 20*1000 and pt["time"] - doorCloseTime > 1000*oneHour*2:
                            if doorDebug:
			        print nicetime(pt["time"]/1000), "** Didn't leave at", nicetime(doorCloseTime/1000), "but no activity for", \
				    (pt["time"] - doorCloseTime)/1000/60, "minutes\n"
			    doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, didn't leave\n"
			    doorList.append({"time":doorCloseTime, "text":": Door closed, didn't leave (but no activity for " +
				str((pt["time"]-doorCloseTime)/1000/60) + " minutes - asleep?)"})
		    elif INOUT == "out" or INOUT =="maybe":
                        if doorDebug:
			    print nicetime(pt["time"]/1000), "** Came in at", nicetime(doorCloseTime/1000),\
			        "visitor:", visitor, "waited", (pt["time"] - doorCloseTime)/1000/60, "minutes for PIR\n"
			INOUT = "in"
			doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, came in\n"
			doorList.append({"time":doorCloseTime, "text":": Door closed, came in"}) 
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
			    print nicetime(pt["time"]/1000), "** Went out at", nicetime(doorCloseTime/1000), "cause door opened again", \
			        (pt["time"]-doorCloseTime)/1000, "seconds later\n"
			ds = ""
			if abs(doorCloseTime-checkOutTime) < 5*oneMinute*1000:
			    if doorDebug:
				print nicetime(pt["time"]/1000), "** Went out and visitor checked out at", nicetime(doorCloseTime/1000),\
				    "cause door opened again", (pt["time"]-doorCloseTime)/1000, "seconds later\n"
			    # ds = ds + " and visitor checked out"
			if teleOn:
			    ds = ds + " (TV still on)"
			    if doorDebug:
				print nicetime(pt["time"]/1000), "** Went out and tele still on", nicetime(doorCloseTime/1000),\
				    "cause door opened again", (pt["time"]-doorCloseTime)/1000, "seconds later\n"
			    #doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, went out (TV still on)\n"
			    #doorList.append({nicehours(doorCloseTime/1000):"Door closed, went out (TV still on)"})
			doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, went out" + ds + "\n"
			doorList.append({"time":doorCloseTime, "text": ": Door closed, went out"+ds})
			INOUT = "out"
		    elif INOUT == "maybe": 
			if doorDebug:
			    print nicetime(pt["time"]/1000), "** In and out at", nicetime(doorCloseTime/1000), "cause door opened again", \
			        (pt["time"]-doorCloseTime)/1000/60, "minutes later\n"
			doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, in and out\n"
			doorList.append({"time":doorCloseTime,"text":": Door closed, in and out"}) 
			INOUT = "out"
		    elif INOUT == "out":
			if doorDebug:
			    print nicetime(pt["time"]/1000), "** Didn't come in at", nicetime(doorCloseTime/1000), "cause door opened again", \
			        (pt["time"]-doorCloseTime)/1000/60, "minutes later\n"
			#doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, came in but didn't stay\n"
			doorList.append({"time":doorCloseTime,"text":": Door closed, came in but didn't stay"}) 
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
            #if uptimeDebug:
            #    print nicetime(pt["time"]/1000), "New uptime point:", pt["name"], "INOUT=", INOUT
            if (pt["time"]/1000 > startTime 
                and pt["time"]/1000 < startTime +6*oneHour # was 9
                and not gotUp):
		# just forced it to be startTime+6hours as a quick fix
		# but if came in was the first event then we should cancel uptime (2017-06-05)
		# cause they were out all night
                if len(upFifo) <= 10:
                    if uptimeDebug:
                        print nicetime(pt["time"]/1000), "Appending morning activity on", pt["name"], "INOUT=", INOUT
                    gotUpTime = pt["time"]
                    upFifo.append(gotUpTime)
                else:
		    last = upFifo[-1]
		    first = upFifo.pop(0) # zero is correct!
                    gotUpTime = pt["time"]
                    upFifo.append(gotUpTime)
                    if uptimeDebug:
                        print nicetime(pt["time"]/1000), "Popped:", nicetime(first/1000)
                        print nicetime(pt["time"]/1000), "And appended:", pt["name"], "INOUT=", INOUT
		    #print "popped:", nicetime(first/1000)
                    #if uptimeDebug:
		    #    for i in upFifo:
		    #	    print nicetime(i/1000)
		    #print "len:", len(upFifo), "last:", nicetime(last/1000), "popped last:", nicetime(first/1000)
		    #print "last-first:", nicehours(last/1000), "-", nicehours(first/1000), "=", (last-first)/1000/60, "minutes"
		    # For the general case (any bridge), this needs to depend on a history of aggregate activity. Not just 26mins
		    if (last-first) <= 1000*oneMinute*30:
			if uptimeDebug:
			    print "Got up at", nicetime(gotUpTime/1000)
			gotUp = True
			if showerTimes:
			    for sh in showerTimes:
				if uptimeDebug:
				    print "Got up at", nicetime(gotUpTime/1000), "but showers = ", nicetime(sh/1000), "and first=", nicetime(first/1000)
				if sh < gotUpTime: #first:
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
			    print "    Rejecting:", nicetime(first/1000), "cause it's 10 items in", (last-first)/1000/60, "minutes (need 30mins)"

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
	    print "**** busyness: something's wrong with the time:", nicetime(pt["time"])
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
        if state == "WFPIR":
	    """
            if latestOne and bedtimeDebug:
		print nicetime(pt["time"]/1000), " WFPIR - resetting latestOne from", nicetime(latestOne["time"]/1000), "cos door opened"
	    elif bedtimeDebug:
		print nicetime(pt["time"]/1000), " WFPIR - resetting latestOne cos door opened"
	    """
            latestOne = {} # it would be better to use now (pt) rather than clearing it but WFPIR doesn't 
                           # clear immediately so we can miss came_in and wemt straight to bed. See 2018-03-12
        # changed from 20:00 to 19:30 temporarily for one service user
	elif pt["time"] > (startTime + 13.5*oneHour)*1000 and pt["time"] < 1000*endTime and not inBed:
            if (("pir" in pt["name"].lower() or "movement" in pt["name"].lower())
	        and "binary" in pt["name"].lower()
	        # and "bedroom" not in pt["name"].lower() needed this when PIR could see the bed - now trying requiring bedroom occupancey
	        and pt["value"] == 1):
                latestOne = pt # a potential latest PIR activity
                latestOne["inBedroom"] = inBedroom
		if bedtimeDebug:
		    print nicetime(pt["time"]/1000), "potential latestOne at", nicetime(pt["time"]/1000), "in", pt["name"], "with inBedroom:", inBedroom
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
			if True: # latestOne["inBedroom"] == 1: temporary as we've lost bedroom sensor
                            if bedtimeDebug:
			        print "Went to bed at:", nicetime(latestOne["time"]/1000), "from", latestOne["name"],\
				    "delayMins=",(pt["time"] - latestOne["time"])/1000/60 
			    bedtimeString = "   Went to bed at " + nicehours(latestOne["time"]/1000)
			    D["bedTime"] = nicehours(latestOne["time"]/1000)
			    inBed = True
			    bedTime = latestOne["time"]
			    ifxData.append({"name": bid + "/In_bed", "points": [[bedTime, 1]]})
			    if teleOn:
				bedtimeString = bedtimeString + "\n      TV still on"
                        else:
                            if bedtimeDebug:
                                print "Maybe went to bed but not in bedroom at", nicetime(latestOne["time"]/1000), "from", latestOne["name"],\
				    "delayMins=",(pt["time"] - latestOne["time"])/1000/60 
		    elif bedtimeDebug:
		    	print nicetime(pt["time"]/1000), "I/O=", INOUT, "doorstate:", state, "not gone to bed at", nicetime(latestOne["time"]/1000), "cause delay mins = ", (pt["time"] - latestOne["time"])/1000/60

        # wanders
        if inBed:
	    bStr = "bedtime"
	    if (pt["time"] > bedTime + 1000*oneMinute
		and "outside" not in pt["name"].lower()
		#and "bedroom" not in pt["name"].lower()
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
			print nicetime(pt["time"]/1000), "new wander in", pt["name"], "bedtime:", nicetime(bedTime/1000)
		if pt["time"] > wanderStart and pt["time"] < wanderStart + wanderWindow*1000:
		    # we're in a wander
		    if pt["name"] not in wanders[-1]["wanderSensors"]:
			wanders[-1]["wanderSensors"].append(pt["name"])

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
	teleString = "      TV on at:\n"
	for i in teleOnTimes:
	    teleString = teleString + "        " + i["ontime"] + " until " + str(i["offtime"]) + " (" + str(i["onFor"]) + " mins)\n"
	    #print "     Tele on at", i["ontime"], "til", i["offtime"]
    elif not teleOn:
	D["tele"] = "no tele data"
	teleString = "      No tv\n"
    if teleOn:
	if not teleOnTimes:
	    teleString = "      TV on at:\n"
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
    if toasterOnTimes:
	D["toaste"] = toasterOnTimes
	toasterString = "      Toaster on at: "
	for i in toasterOnTimes:
	    toasterString = toasterString + i 
	    if toasterOnTimes.index(i) < len(toasterOnTimes)-1:
		toasterString = toasterString + ", "
	    else:
		toasterString = toasterString + "\n"
    else:
	D["toaster"] = "No toaster data"
	toasterString = "      No toaster\n"
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

    # end of wanders - WIP
    if wanders:
	if wanderDebug:
	    print "EOW before:", json.dumps(wanders,indent=4)
	for x in list(wanders):
	    if wanderDebug:
		print "processing:", json.dumps(x,indent=4)
	    if len(x["wanderSensors"]) == 1 and "bedroom" in x["wanderSensors"][0].lower():
		if wanderDebug:
		    print "bedroom only wander at:", nicetime(x["wanderStart"]/1000)
		b_wanders.append(x)
		wanders.remove(x)
	    else:
		for j in list(wanders[wanders.index(x)]["wanderSensors"]):
		    if "bedroom" in j.lower():
			wanders[wanders.index(x)]["wanderSensors"].remove(j)
			if wanderDebug:
			    print "deleted bedroom from:", wanders[wanders.index(x)]["wanderSensors"]

	if wanderDebug:
	    print "EOW after:", json.dumps(wanders,indent=4)
    if wanders: # if there are any left
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
	wstr = "\n      No wanders outside the bedroom after " + bStr + "\n"
    if b_wanders:
	b_wstr = "      Wanders in the bedroom after " + bStr + " at:\n"
	for x in b_wanders:
	    if wanderDebug:
	        print "end of bedroom wanders:", nicetime(x["wanderStart"]/1000)
	    b_wstr = b_wstr + "         " + nicehours(x["wanderStart"]/1000) + "\n"
    wstr = wstr + b_wstr
    """
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
    if b_wanders:
	b_wstr = "      Wanders in the bedroom after " + bStr + " at:\n"
	for x in b_wanders:
	    if wanderDebug:
	        print "end of bedroom wanders:", nicetime(x["wanderStart"]/1000)
	    b_wstr = b_wstr + "         " + nicehours(x["wanderStart"]/1000) + "\n"
    wstr = wstr + b_wstr
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
	    doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, came in but didn't stay and not back before 6am\n"
	    doorList.append({"time":doorCloseTime, "text":": Door closed, came in but didn't stay and not back before 6am"})
	elif state == "WFPIR" and INOUT == "in":
	    if doorDebug:
		print nicetime(pt["time"]/1000), "So: Went out at", nicetime(doorCloseTime/1000), "and not back before 6am"
	    doorString2 = doorString2 + "   " + nicehours(doorCloseTime/1000) + ": Door closed, went out - not back before 6am\n"
	    doorList.append({"time":doorCloseTime, "text":": Door closed, went out - not back before 6am"})

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
    #print "*** sensorsFound:", json.dumps(sensorsFound, indent=4)

    doorList.sort(key=operator.itemgetter('time'))
    for x in doorList:
	try:
	    doorString3 = doorString3 + "   " + nicehours(x["time"]/1000) + x["text"] + "\n"
	except:
	    print "ERROR in doorList:", json.dumps(x,indent=4)
    #strDiff = _unidiff_output(doorString2, doorString3)
    #print "Diffs:", strDiff

    #Text = Text + uptimeString + teleString + kettleString + toasterString + microString + washerString + ovenString + cookerString + showerString + bedtimeString + wstr + busyString + doorString3 + "\n"
    Text = Text + uptimeString + kettleString + toasterString + microString + washerString + ovenString + cookerString + showerString + bedtimeString + wstr + busyString + doorString3 + "\n"

    print "\n", Text 

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
    if False: #shower_mail:
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
    # end of data_client checking
    if data_client_ok != True:
        if warning_mails:
	    try:
		to = "martin.sotheran@continuumbridge.com, peter.claydon@continuumbridge.com"
		e_txt = "No data from DYH for 6 hours\nSo either data_client or "+bid+" is down"
		msg = MIMEMultipart('alternative')
		msg['Subject'] = "No data from "+bid+" for 6 hours"
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
		part1 = MIMEText(e_txt, 'plain')
		#part2 = MIMEText(htmlText, 'html')
	    
		msg.attach(part1)
		#msg.attach(part2)
		mail = smtplib.SMTP('smtp.gmail.com', 587)
		mail.ehlo()
		mail.starttls()
		mail.login(user, password)
		mail.sendmail(user, recipients, msg.as_string())
		mail.quit()
		print "Data warning mail sent to:", to
	    except Exception as ex:
		print "sendMail problem. To:", to, "type: ", type(ex), "exception: ", str(ex.args)
        else:
            print (time.strftime("%d/%m/%Y")), " *** WARNING no data in last 6 hours - but not sending mails"

    
                  
if __name__ == '__main__':
    dyh()
