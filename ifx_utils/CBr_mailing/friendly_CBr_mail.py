#!/usr/bin/env python
# CBr_mail_ifx.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#
# Usage:-
# ./friendly_CBr_mail.py --user bridges@continuumbridge.com --password Mucht00f@r --bid BID36 --db "SCH" --template CBr_table_template.htm --to "martin.sotheran@continuumbridge.com"

# To do
#  Merge the entry/exit series & put the right text in the boxes

gerasurl = 'http://geras.1248.io/'
import requests
import json
import time
import click
import os, sys
import re
import smtplib
from itertools import cycle
import urllib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage

#Constants
tenMinutes         = 10 * 60
oneHour            = 60 * 60
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
    now = time.strftime('%H:%M:%S', localtime)
    return now

def stepHourMin(timeStamp):
    localtime = time.localtime(timeStamp)
    now = time.strftime('%H%M', localtime)
    return now

def epochtime(date_time):
    pattern = '%Y-%m-%d %H:%M:%S'
    epoch = int(time.mktime(time.strptime(date_time, pattern)))
    return epoch

def start():
    t = time.localtime(time.time() - oneDay)
    yesterday = time.strftime('%Y-%m-%d', t)
    s = yesterday + " 12:00:00"
    return epochtime(s)

def activeInTenMinutes(series, time):
    for s in series:
        if s["t"] >= time and s["t"] < time + tenMinutes:
            return True
    return False

def tempInTenMinutes(series, time):
    for s in series:
        if s["t"] >= time and s["t"] < time + tenMinutes:
            return "%2.1f" %s["v"]
    return ""

def replace(holder, value):
    global h1, h2, working
    if working == "h1":
        h2 = h1.replace(holder, value)
        working = "h2"
    else:
        h1 = h2.replace(holder, value)
        working = "h1"

@click.command()
@click.option('--user', nargs=1, help='User name of email account.')
@click.option('--password', prompt='Password', help='Password of email account.')
@click.option('--bid', nargs=1, help='The bridge ID to list.')
@click.option('--db', nargs=1, help='The database to look in')
@click.option('--to', nargs=1, help='The address to send the email to.')
@click.option('--template', nargs=1, help='the table template file.')

def cbr_email_ifx(user, password, bid, to, db, template):
    h1 = ""
    h2 = ""
    working = ""
    startTime = start()
    endTime = startTime + oneDay
    serieslist = []
    """ 
    Expected timeseries: 
    {
    "/BID11/MagSW_ES-Kitchen-Cup_Cupboard/binary": {
        "e": [
            {
                "v": 0, 
                "t": 1427148242, 
                "n": "/BID11/MagSW_ES-Kitchen-Cup_Cupboard/binary"
            }, 
            {
                "v": 1, 
                "t": 1427148243, 
                "n": "/BID11/MagSW_ES-Kitchen-Cup_Cupboard/binary"
            }, 
    We've got:-
    [
    {
        "points": [
            [
                1427193906669, 
                15927010001, 
                50
            ], 
            [
                1427116355288, 
                15798620001, 
                0
            ]
        ], 
        "name": "BID36/Back_Door/answered_door", 
        "columns": [
            "time", 
            "sequence_number", 
            "value"
        ]
    }, 
            

    """
    timeseries = {}
    if not bid:
        print "You must provide a bridge ID using the --bid option."
        exit()
    else:
        # Unlike geras, Influx doesn't return a series if there are no points in the selected range
        # So we'd miss dead sensors
        # So we'll ask for 7 days before startTime on the grounds that we'd always change a battery in that time      
        # select * from /BID11/ where time > 1427025600s and time < 1427112000s
        earlyStartTime = startTime - 7*oneDay
        q = "select * from /" + bid + "/ where time >" + str(earlyStartTime) + "s and time <" + str(endTime) + "s"
        query = urllib.urlencode ({'q':q})

        print "Requesting list of series from", nicetime(startTime), "to", nicetime(endTime)
        url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query 
        print "fetching from:", url
        r = requests.get(url)
        pts = r.json()
        #print json.dumps(r.json(), indent=4)
        #print ("we got:", json.dumps(r.content, indent=4))
    
        for i in range(0, len(pts)):
            print "We got:", pts[i]["name"]        
    
        # This bit is horrible - a hangover. It reads influx data 
        # and converts it to geras!
        for i in range(0, len(pts)):
            #choose what we want
            if "binary" in pts[i]["name"] or "power" in pts[i]["name"] or "entry_exit" in pts[i]["name"] or "temperature" in pts[i]["name"] or "hot_drinks" in pts[i]["name"] or "Night" in pts[i]["name"]:
                # and get rid of the old names - this list can only grow...
                if not ("MagSW" in pts[i]["name"] or "Fib" in pts[i]["name"] or "test" in pts[i]["name"] or "TBK" in pts[i]["name"] or "Coffee_jar" in pts[i]["name"]):
                    # and, for Martyn's bridge
                    if not ("Fridge_Door" in pts[i]["name"] or "Coffee_Cupboard_Door" in pts[i]["name"] or "Coffee/temperature" in pts[i]["name"] or "Utility_Room_Door/binary" in pts[i]["name"] or "Utility_Room_PIR/binary" in pts[i]["name"] or "Kettle/power" in pts[i]["name"]):
                        # Merge the various night wanders
                        if "Night_Wander" in pts[i]["name"]:
                            if not "Night_Wanders" in serieslist:
                               serieslist.append("/"+bid+"/Night_Wanders")
                               wanders = []            
                            sensor = "/" + bid + "/Night_Wanders"
                            for j in range(0, len(pts[i]["points"])):
                                t = pts[i]["points"][j][0]/1000
                                v = pts[i]["points"][j][2]
                                n = sensor
                                #print "adding", nicetime(t), "to wanders"
                                wanders.append({"v":v, "t":t, "n":n}) 
                        else:
                            serieslist.append("/" + pts[i]["name"])
                            sensor = "/"+pts[i]["name"]
                            vt = []            
                            for j in range(0, len(pts[i]["points"])):
                                t = pts[i]["points"][j][0]/1000
                                v = pts[i]["points"][j][2]
                                n = sensor
                                vt.append({"v":v, "t":t, "n":n})
                            timeseries[sensor] = {"e":vt}
 
                        try:
                            if wanders:
                                timeseries["/" + bid + "/Night_Wanders"] = {"e":wanders}
                        except:
                            print "No Wanders from", pts[i]["name"]
               
        print "Processing:", json.dumps(serieslist, indent=4)
              
    # Read HTML file
    with open(template, "r") as f:  
        h1 = f.read()
    
    # Because there can be "illigal" ASCII characters in the HTML file:
    i = 0
    for c in h1:
        if ord(c) > 127:
            #print "Replaced:", c, ord(c)
            h2 += " "
        else:
            h2 += c
    # Headers
    h1 = h2.replace("nnn", bid)
    h2 = h1.replace("&lt;date1&gt;", nicedate(startTime))
    h1 = h2.replace("&lt;date2&gt;", nicedate(endTime))  #+" (InfluxDB/"+db+")")
    working = "h1"

    #print "timeseries:", json.dumps(timeseries, indent=4)
    col = 1
    prev = "fubar"
    for path in serieslist:
        series = timeseries[path]["e"]
            
        # split it into BID, Name, Type (_ is a sledgehammer - see below)
        #ss = re.split('\W+|/|-|_',path)
        ss = re.split('\W+|/|-',path)            
        #print "First ss:",ss

        # Change some "types" according to sensor type
        length = len(ss)
        for i in range(0,len(ss)):
            if "pir" in ss[i].lower():
                ss[length-1] = ss[length-1].replace("binary", "Activity")
                            
        # Tidy up - mostly specifically for Martyn's sensors
        if "binary" in ss:
            if "Kettle" or "Door" in ss: 
                del ss[ss.index("binary")]            
        if "Kettle" in ss:
            del ss[ss.index("Kettle")]            
            if "power" in ss:
                del ss[ss.index("power")]            
        if "entry_exit" in ss:
            del ss[ss.index("entry_exit")]            

        #print "1. What's left?:",ss            

        # First field is always empty, second is always BID
        del ss[0]        
        del ss[0]
        #print "2. What's left now?:",ss    

        # Remove any spurious underscores inserted by influx
        # And other leftovers
        for i in range(0,len(ss)):
            ss[i] = ss[i].replace("_", " ")
            ss[i] = ss[i].replace("PIR", "")            
            #ss[i] = ss[i].replace("Utility Room Door", "Utility Room")            
            ss[i] = ss[i].replace("hot drinks", "Hot Drinks")            
        #print "3. What's left now?:",ss            

        eeAction = ""                      
        if series and "entry_exit" in path.lower():
            eeAction = ss[-1]
            del ss[-1]
        # still leaves 4 series for entry/exit - need to merge them here    

        for value in ss[0:len(ss)]:
            holder = "S_" + str(col) + "_name" + str(ss.index(value)+1)
            print "holder: ", holder, " value:", value                
            if working == "h1":
                h2 = h1.replace(holder, value)
                working = "h2"
            else:
                h1 = h2.replace(holder, value)
                working = "h1"        

        # build table entries
        if series and "entry_exit" in path.lower():
            for stepTime in range(startTime, startTime + oneDay, tenMinutes):
                holder = "S_" + str(col) + "_" + stepHourMin(stepTime)
                if activeInTenMinutes(series, stepTime):
                    value = eeAction
                else:
                    value = ""
                if working == "h1":
                    h2 = h1.replace(holder, value)
                    working = "h2"
                else:
                    h1 = h2.replace(holder, value)
                    working = "h1"
        elif series and ("door" in path.lower() or "drawer" in path.lower()):
            for stepTime in range(startTime, startTime + oneDay, tenMinutes):
                holder = "S_" + str(col) + "_" + stepHourMin(stepTime)
                if activeInTenMinutes(series, stepTime):
                    value = "Open"
                else:
                    value = ""
                if working == "h1":
                    h2 = h1.replace(holder, value)
                    working = "h2"
                else:
                    h1 = h2.replace(holder, value)
                    working = "h1"
        elif series and ("hot_drinks" in path):
            for stepTime in range(startTime, startTime + oneDay, tenMinutes):
                holder = "S_" + str(col) + "_" + stepHourMin(stepTime)
                if activeInTenMinutes(series, stepTime):
                    value = "Hot Drink"
                else:
                    value = ""
                if working == "h1":
                    h2 = h1.replace(holder, value)
                    working = "h2"
                else:
                    h1 = h2.replace(holder, value)
                    working = "h1"
        elif series and ("/" + bid+ "/Night_Wander" in path):  
            for stepTime in range(startTime, startTime + oneDay, tenMinutes):
                holder = "S_" + str(col) + "_" + stepHourMin(stepTime)
                if activeInTenMinutes(series, stepTime):
                    value = "Wander"
                else:
                    value = ""
                if working == "h1":
                    h2 = h1.replace(holder, value)
                    working = "h2"
                else:
                    h1 = h2.replace(holder, value)
                    working = "h1"                
        elif series and "temperature" in path.lower():
            prev_temperature = "none"
            for stepTime in range(startTime, startTime + oneDay, tenMinutes):
                holder = "S_" + str(col) + "_" + stepHourMin(stepTime)
                value = tempInTenMinutes(series, stepTime)
                if value == "":
                    if prev_temperature != "none":
                        value = prev_temperature
                else:
                    prev_temperature = value
                if working == "h1":
                    h2 = h1.replace(holder, value)
                    working = "h2"
                else:
                    h1 = h2.replace(holder, value)
                    working = "h1"
        elif series and "pir" in path.lower() and "binary" in path.lower():
            for stepTime in range(startTime, startTime + oneDay, tenMinutes):
                holder = "S_" + str(col) + "_" + stepHourMin(stepTime)
                if activeInTenMinutes(series, stepTime):
                    value = "A"
                else:
                    value = ""
                if working == "h1":
                    h2 = h1.replace(holder, value)
                    working = "h2"
                else:
                    h1 = h2.replace(holder, value)
                    working = "h1"
        elif series and "power" in path.lower(): # need to get rid of power
            prevPower = "" 
            if "toaster" in path.lower() or "kettle" in path.lower():
                threshold = 1000
            elif "coffee_maker" in path.lower():
                threshold = 50
            else:
                threshold = 3.5                                 
            for stepTime in range(startTime, startTime + oneDay, tenMinutes):
                #print "doing", nicetime(stepTime)
                op = prevPower
                finalValue = -12
                latestTime = -1    
                for ss in series: # IT GOES THOUGH THEM BACKWARDS IN TIME!!!
                    holder = "S_" + str(col) + "_" + stepHourMin(stepTime)
                    #If any point is over the threshold, the answer, op, is ON. 
                    #Otherwise it's prevPower (which starts at OFF and then is always 
                    #the last value found in the 10 min slot)
                    if ss["t"] >= stepTime and ss["t"] < stepTime + tenMinutes:
                        #print "   found", ss['v'], "on", ss['n'], "at", nicetime(ss['t'])
                        if ss['t'] > latestTime:
                            latestTime = ss['t']
                            finalValue = ss['v']                            
                        if ss['v'] > threshold:
                            op = "On"
                            #print "  *Found a high point:", ss['v'], "at", nicetime(ss['t'])
      
                #print "      final value for", ss['n'], "was:", finalValue, "at", nicetime(latestTime)
                if finalValue >= threshold:
                    prevPower = "On"           
                elif finalValue >= 0:
                    prevPower = ""  
                # else it was -12; there were no points    
                                            
                if working == "h1":
                    h2 = h1.replace(holder, op)
                    working = "h2"
                else:
                    h1 = h2.replace(holder, op)
                    working = "h1"        
        else:
            for stepTime in range(startTime, startTime + oneDay, tenMinutes):
                holder = "S_" + str(col) + "_" + stepHourMin(stepTime)
                value = "-"
                if working == "h1":
                    h2 = h1.replace(holder, value)
                    working = "h2"
                else:
                    h1 = h2.replace(holder, value)
                    working = "h1"
        print "\n"
        col += 1

    # Remove any unused holders
    if working == "h1":
        h2 = re.sub("S_[0-9]+_name[0-9]+", "", h1, 0)
        h1 = re.sub("S_[0-9]+_[0-9]+", "", h2, 0)
    else:
        h1 = re.sub("S_[0-9]+_name[0-9]+", "", h2, 0)
        h2 = re.sub("S_[0-9]+_[0-9]+", "", h1, 0)
    if working == "h1":
        htmlText = h1
    else:
        htmlText = h2

    #exit()
    
    # Create message container - the correct MIME type is multipart/alternative.
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Activity for bridge "+bid+" from "+nicedate(startTime)+" to "+nicedate(endTime)+" (InfluxDB/"+db+")"
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
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(htmlText, 'html')
    
        if "sirona" in template.lower():
            fp = open('image001s.png', 'rb')
        else:
            fp = open('image001CBr.png', 'rb')

        msgImage = MIMEImage(fp.read())
        fp.close()
        # Define the image's ID as referenced above
        msgImage.add_header('Content-ID', '<image001.png>')
        msg.attach(msgImage)
        msg.attach(part1)
        msg.attach(part2)
        mail = smtplib.SMTP('smtp.gmail.com', 587)
        mail.ehlo()
        mail.starttls()
        mail.login(user, password)
        mail.sendmail(user, recipients, msg.as_string())
        mail.quit()
    except Exception as ex:
        print "sendMail problem. To:", to, "type: ", type(ex), "exception: ", str(ex.args)

                  
if __name__ == '__main__':
    cbr_email_ifx()

