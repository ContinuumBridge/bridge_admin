#!/usr/bin/env python
# room_occupancy.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#
# Usage:-
# ./shower.py --user bridges@continuumbridge.com --bid BID36 --db "SCH" --daysago 5 

import requests
import json
import time
import click
import os, sys
import re
import smtplib
import operator
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
    s = yesterday + " 12:00:00" # 1am for the sudden jumps
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

def shower (sensorList, bathroomSeries, bid):
    showerTimes = []
    longShowerWindow = 320*oneMinute*1000
    for s in sensorList:
	print "next s", s
	prevJ = 0
	prevK = []
	prevH = 0
	prevT = 0
	noMoreShowersTillItFalls = False
	showerDebug = True
	showerString = "No showers found"
	occStart = 0
	occWindow = 1000*oneMinute*20 # cause there can be a lag between occupancy and rising H
	kFell = False
	g1 = 10
	c1 = -21
	for j in bathroomSeries:
	    if s in j["name"]:
		if j <> prevJ:
		    if "binary" in j["name"].lower():
			if j["value"] == 1: # reset occStart for every j cause k takes it to the end of longShowerWindow
			    #print nicetime(j["time"]/1000), "j occStart set by:",  j["name"] 
			    occStart = j["time"]

		    if "humidity" in j["name"]: 
			if prevH <> 0 and j["value"] > prevH: 
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
			    #if showerDebug:
			    #    print "j", nicetime(j["time"]/1000), "H Gone up by", j["value"]-prevH, "to", j["value"],\
			    #        "in", (j["time"] - prevT)/1000/60, "minutes\n"
			    # every time j` goes up, look ahead to see how far and how long and whether occupied
			    kFell = False
			    for k in bathroomSeries:
				if "binary" in k["name"].lower() and s in k["name"]:
				    if k["value"] == 1:# and k["time"] > occStart + occWindow:
					#print nicetime(k["time"]/1000), "k occStart set by:",  k["name"] 
					occStart = k["time"]
				if s in k["name"] and "humidity" in k["name"] and not kFell:
				    if (k <> prevK and k["time"] >= j["time"] 
					and k["time"] <= j["time"] + 2*longShowerWindow # restrict k forwards otherwise it
					and not noMoreShowersTillItFalls):              # may find a shower miles away based on j
					if k["value"] > prevK["value"]: # whilst kH is rising...
					    if showerDebug:
						print "pj:", nicetime(prevT/1000), "k:", nicetime(k["time"]/1000), "next k:", k["value"]
					    if abs(k["time"] - occStart) < occWindow: #  and we're occupied
						#print "occstart:", nicehours(occStart/1000), "kt:", nicehours(k["time"]/1000), "so we're",\
						# attempt at gradients
						deltaT = (k["time"] - prevT)/1000/60
						deltaH = k["value"] - prevH 
						# two gradients
						# for dh under 10, we require shorter times (dt = m1*dh + c1)
						# for dh >10 we allow more time to capture the sudden jumps after a long time
						m1 = 10
						c1 = -19
						m2 = 54
						c2 = -429
						if (deltaT < 360 and 
						    ((deltaH <= 10 and deltaT < m1*deltaH +c1) 
						    or (deltaH > 10 and deltaT < m2*deltaH + c2))):
						    #if showerDebug:
						    print "**SHOWER_new at pj:", nicetime(prevT/1000),\
							"occStart:", nicetime(occStart/1000),\
							"dh:", float(k["value"] - prevH), \
							"dt:",float((k["time"] - prevT)/1000/60)
						    noMoreShowersTillItFalls = True
						    showerTimes.append(nicetime(occStart/1000))
						else:
						    #if showerDebug:
						    print "No shower at j:", nicetime(prevT/1000), "k:", nicetime(k["time"]/1000),\
							"cause dt=", deltaT, "dh=", deltaH
					    elif k["value"] > prevH and occStart <> 0:
						if showerDebug:
						    print "No show shower at k:", nicetime(k["time"]/1000), \
							"cause abs Kt-OS=", abs(k["time"] - occStart)/60/1000, "minutes and occStart:", nicetime(occStart/1000)
					    #else:
					    #    print "Fallen through occupancy at k:", nicetime(k["time"]/1000)

					else: #kH fell
					    #print nicetime(prevT/1000), "k fell at:", nicehours(k["time"]/1000), "we should reset here"
					    kFell = True
				    prevK = k
			else: # jH fell
			    noMoreShowersTillItFalls = False
			    #if showerDebug:
			    #    print nicetime(j["time"]/1000), "It fell from", prevH, "to", j["value"]
			prevT = j["time"]
			prevH = j["value"]
		else:
		    print nicetime(j["time"]/1000), "****************** Skipped duplicate j on", j["name"]
		prevJ = j

    if showerTimes:
	showerString = "\nShowers found on " + bid + " at: \n"
	for x in showerTimes:
	    showerString = showerString + "   " + str(x) + "\n"
    else:
	showerString = "\nNo showers found on " + bid + "\n"


    return {"showerString":showerString, "showerTimes": showerTimes}                                

@click.command()
@click.option('--user', nargs=1, help='User name of email account.')
@click.option('--password', prompt='Password', help='Password of email account.')
@click.option('--to', nargs=1, help='The address to send the email to.')
@click.option('--bid', nargs=1, help='The bridge ID to list.')
@click.option('--db', nargs=1, help='The database to look in')
@click.option('--daysago', nargs=1, help='How far back to look')

def shower_loop(user, password, to, db, bid, daysago):
    daysAgo = int(daysago)*60*60*24 
    startTime = start() - daysAgo
    endTime = startTime + oneDay # + daysAgo

    if not bid:
        bidList = ["BID11", "BID267", "BID264"]
        #bidList = ["BID267"]
    else:
        bidList = [bid]

    print "\nBID:", bid, "start time:", nicetime(startTime)
    print "BID:", bid, "end time:", nicetime(endTime)
 
    for b in bidList:
        q = "select * from /" + b + "/ where time >" + str(startTime) + "s and time <" + str(endTime) + "s"
        query = urllib.urlencode ({'q':q})
        print "Requesting list of series from", nicetime(startTime), "to", nicetime(endTime)
        url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
        print "fetching from:", url
        try:
            r = requests.get(url)
            pts = r.json()
        except:
            print "Fetch failed"
            exit()
    
        sensorList = []
        selectedSeries = []
        bathroomSeries = []
        prevItem = 0
        for series in pts:
            if "humidity" in series["name"].lower(): 
                if getsensor(series["name"]) not in sensorList:
                   sensorList.append(getsensor(series["name"]))
        print "sensorlist:", sensorList

        for s in sensorList:
            for series in pts:
                if s in series["name"]: 
                    selectedSeries.append(series)
        for item in selectedSeries:
            for pt in item["points"]:
                if pt[0] >= startTime*1000 and pt[0] <= endTime*1000:
                    bathroomSeries.append({"time":pt[0],  "name": item["name"], "value": pt[2]})
        bathroomSeries.sort(key=operator.itemgetter('time'))
        #print "bS:", json.dumps(bathroomSeries,indent=4)

        showerString = ""
        foo = shower(sensorList, bathroomSeries, b)
	print "foo:", json.dumps(foo,indent=4)
        showerString = showerString + foo["showerString"]

    print showerString

    exit()
    # Create message container - the correct MIME type is multipart/alternative.
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Showers found in 24hrs since midday yesterday"
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
        part1 = MIMEText(showerString, 'plain')
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
    shower_loop()

