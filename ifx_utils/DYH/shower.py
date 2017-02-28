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

def shower (bid, db, startTime, endTime, daysago):
    #startTime = start() - daysAgo
    #endTime = startTime + oneDay

    print "\nBID:", bid, "start time:", nicetime(startTime)
    print "BID:", bid, "end time:", nicetime(endTime)
 
    if not bid:
        print "You must provide a bridge ID using the --bid option."
        exit()
    else:
        q = "select * from /" + bid + "/ where time >" + str(startTime) + "s and time <" + str(endTime) + "s"
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
	
        showerTimes = []
        veryShortShowerWindow = 11*oneMinute*1000
        veryShortShowerThresh = 3.0
        shortShowerWindow = 13*oneMinute*1000
        shortShowerThresh = 6
        showerWindow = 41*oneMinute*1000
        showerThresh = 6
        longShowerWindow = 320*oneMinute*1000
        longShowerThresh = 14
        for s in sensorList:
            print "next s", s
            prevJ = 0
            prevK = []
            prevH = 0
            prevT = 0
            noMoreShowersTillItFalls = False
            showerDebug = False
            showerString = "No showers found"
            occStart = 0
            occWindow = 1000*oneMinute*30
            kFell = False
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
                                    print nicetime(j["time"]/1000), "nmstif:", noMoreShowersTillItFalls, "j rose by",\
                                        j["value"] - prevH, "in", (j["time"] - prevT)/1000/60, "minutes - so pretending it fell"   
                                    noMoreShowersTillItFalls = False
                                if showerDebug:
                                    print nicetime(j["time"]/1000), "H Gone up by", j["value"]-prevH, "to", j["value"],\
                                        "in", (j["time"] - prevT)/1000/60, "minutes\n"
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
                                                if abs(k["time"] - occStart) < occWindow: #  and we're occupied
                                                    # If at any time during this process we get dh high enough and dt small enough...
                                                    if (k["value"] - prevH >= shortShowerThresh and k["time"] - prevT <= shortShowerWindow):
                                                        showerTimes.append(nicetime(occStart/1000))
                                                        print nicetime(prevT/1000), "** SHOWER_s",\
                                                            "at occStart:", nicehours(occStart/1000),\
                                                            "dh:", k["value"] - prevH, \
                                                            "dt:",(k["time"] - prevT)/1000/60
                                                        noMoreShowersTillItFalls = True
                                                    elif (k["value"] - prevH >= showerThresh and k["time"] - prevT < showerWindow):
                                                        print nicetime(prevT/1000), "** SHOWER_n",\
                                                            "at occStart:", nicehours(occStart/1000),\
                                                            "dh:", k["value"] - prevH, \
                                                            "dt:",(k["time"] - prevT)/1000/60
                                                        #"prevJ:", nicehours(prevT/1000), "thisK:", nicehours(k["time"]/1000),\
                                                        #"occStart:", nicehours(occStart/1000),\
                                                        noMoreShowersTillItFalls = True
                                                        showerTimes.append(nicetime(occStart/1000))
                                                    elif (k["value"] - prevH >= longShowerThresh and k["time"] - prevT < longShowerWindow):
                                                        print nicetime(prevT/1000), "** SHOWER_l",\
                                                            "at occStart:", nicehours(occStart/1000),\
                                                            "dh:", k["value"] - prevH, \
                                                            "dt:",(k["time"] - prevT)/1000/60
                                                        #"prevJ:", nicehours(prevT/1000), "thisK:", nicehours(k["time"]/1000),\
                                                        #"occStart:", nicehours(occStart/1000),\
                                                        noMoreShowersTillItFalls = True
                                                        showerTimes.append(nicetime(occStart/1000))
                                                    elif (float((k["value"] - prevH) >= veryShortShowerThresh 
                                                        and k["time"] - prevT < veryShortShowerWindow)):
                                                        print nicetime(prevT/1000), "** SHOWER_vs",\
                                                            "prevJ:", nicehours(prevT/1000), "thisK:", nicehours(k["time"]/1000),\
                                                            "occStart:", nicehours(occStart/1000),\
                                                            "dh:", float(k["value"] - prevH), \
                                                            "dt:",float((k["time"] - prevT)/1000/60)
                                                        noMoreShowersTillItFalls = True
                                                        showerTimes.append(nicetime(occStart/1000))
                                                    elif k["value"] > prevH and showerDebug:
                                                        print nicetime(prevT/1000), "No shower at k:",nicehours(k["time"]/1000), "dh:", \
                                                            float(k["value"]) - float(prevH), "dt:", float((k["time"] - prevT)/1000.0/60.0), \
                                                            "occStart:", nicetime(occStart/1000)
                                                elif k["value"] > prevH and occStart <> 0 and showerDebug:
                                                    print nicetime(prevT/1000), "No show shower at k:", nicehours(k["time"]/1000), \
                                                        "cause abs Kt-OS=", abs(k["time"] - occStart)/60/1000, "minutes and occStart:", nicetime(occStart/1000)
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

        if showerTimes:
            showerString = "\nShowers found on " + bid + " at: \n"
            for x in showerTimes:
                showerString = showerString + "   " + str(x) + "\n"
        else:
            showerString = "\nNo showers found on " + bid + "\n"


    return showerString                                

@click.command()
@click.option('--user', nargs=1, help='User name of email account.')
@click.option('--password', prompt='Password', help='Password of email account.')
@click.option('--to', nargs=1, help='The address to send the email to.')
#@click.option('--bid', nargs=1, help='The bridge ID to list.')
@click.option('--db', nargs=1, help='The database to look in')
@click.option('--daysago', nargs=1, help='How far back to look')

def shower_loop(user, password, to, db, daysago):
    daysAgo = int(daysago)*60*60*24 
    startTime = start() - daysAgo
    endTime = startTime + oneDay # + daysAgo

    #bidList = ["BID267"]
    bidList = ["BID11", "BID267", "BID264"]
    showerString = ""
    for b in bidList:
        showerString = showerString + shower(b, db, startTime, endTime, daysAgo)

    showerString = "\nTries a bit harder to find 2nd showers - let's see!\n" + showerString 
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

