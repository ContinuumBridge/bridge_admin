#!/usr/bin/env python
# sch_email.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#

gerasurl = 'http://geras.1248.io/'
import requests
import json
import time
import click
import os, sys
import re
import smtplib
from itertools import cycle
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage

#Constants
tenMinutes         = 10 * 60
oneHour            = 60 * 60
oneDay             = oneHour * 24
fileName           = "CBr_table_template.htm"

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

def powerInTenMinutes(series, time):
    for s in series:
        if s["t"] >= time and s["t"] < time + tenMinutes:
            if s["v"] > 10:
                return True
    return False

def tempInTenMinutes(series, time):
    for s in series:
        if s["t"] >= time and s["t"] < time + tenMinutes:
            return "%2.1f" %s["v"]
    return ""

def readHTML(fileName):
    with open(fileName, "r") as f:
        h1 = f.read()
    # Because there can be "illigal" ASCII characters in the HTML file:
    i = 0
    for c in h1:
        if ord(c) > 127:
            #print "Replaced:", c, ord(c)
            h2 += " "
        else:
            h2 += c
    working = "h2"

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
@click.option('--to', nargs=1, help='The address to send the email to.')
@click.option('--key', prompt='Geras API key', help='Your Geras API key. See http://geras.1248.io/user/apidoc.')

def cbr_email(user, password, bid, to, key):
    h1 = ""
    h2 = ""
    working = ""
    if not bid:
        print "You must provide a bridge ID using the --bid option."
        exit()
    else:
        print "Requesting list"
        r = requests.get('http://geras.1248.io/serieslist', auth=(key,''))
        allseries = json.loads(r.content)
        serieslist = []
        for t in allseries:
            if (bid+"/") in t:
                print t
                serieslist.append(t)
    startTime = start()
    endTime = startTime + oneDay
    print "startTime:", nicetime(startTime), " endTime:", nicetime(endTime)
    # Read HTML file
    with open(fileName, "r") as f:
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
    h1 = h2.replace("&lt;date2&gt;", nicedate(endTime))
    working = "h1"

    timeseries = {}
    col = 1
    for gerasPath in serieslist:
        if not("Light-Mesh" in gerasPath or "battery" in gerasPath or "connected" in gerasPath or "luminance" in gerasPath or "magnet" in gerasPath or "button" in gerasPath or "ir_temperature" in gerasPath or ("tag_ti" in gerasPath.lower() and "temperature" in gerasPath) or ("tbk" in gerasPath.lower() and "binary" in gerasPath.lower())):

              
#        ("binary" in gerasPath.lower() and "coffee" in gerasPath.lower()) or        
#        ("binary" in gerasPath.lower() and "coffee_cupboard" in gerasPath.lower())):                
                    
            url = gerasurl + 'series/' + gerasPath +'?start=' + str(startTime) + '&end=' + str(endTime)
            #print "\nurl:", url
            r = requests.get(url, auth=(key,''))
            timeseries[gerasPath] = json.loads(r.content)
            #print "timeseries:", json.dumps(timeseries, indent=4)
            series = timeseries[gerasPath]["e"]

            # split it into BID, Name, Type (_ is a sledgehammer - see below)
            #ss = re.split('\W+|/|-|_',gerasPath)
            ss = re.split('\W+|/|-',gerasPath)            
            print "First ss:",ss

            #exit()

            # Change some "types" according to sensor type
            length = len(ss)
            for i in range(0,len(ss)):
                if "pir" in ss[i].lower():
                    ss[length-1] = ss[length-1].replace("binary", "Activity")
                if "tbk" in ss[i].lower():
                    ss[length-1] = ss[length-1].replace("binary", "Switch")           
                            
            if "binary" in ss:
                if "Kettle" or "Door" in ss: 
                    del ss[ss.index("binary")]            
            #print "What's left?:",ss            
            
            # get rid of blank field, BID & sensor type unless it's a KM
            if "KM" in ss:
                del ss[0:2]
            else:
                del ss[0:3]
               
            # squash it down to three lines for the template
            if len(ss) > 4:
                ss[0] = ss[0] + " " + ss[1]
                del ss[1]
                ss[1] = ss[1] + " " + ss[2]
                del ss[2]
            elif len(ss) > 3:                
                ss[1] = ss[1] + " " + ss[2]
                del ss[2]
                        
            # There are four possible fields plus the type. 
            # And there should only be underscores left
            for i in range(0,len(ss)):
                ss[i] = ss[i].replace("_", " ")
                #print "ss[",i,"]:", ss[i], "\n"            
            #print "What's left now?:",ss            

            for value in ss[0:len(ss)]:
                holder = "S_" + str(col) + "_name" + str(ss.index(value)+1)
                print "holder:", holder, " value:", value
                if working == "h1":
                    h2 = h1.replace(holder, value)
                    working = "h2"
                else:
                    h1 = h2.replace(holder, value)
                    working = "h1"

            
            # build table entries
            if series and "magsw" in gerasPath.lower():  # Always on doors & drawers for now
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
            elif series and "power" in gerasPath.lower():
                for stepTime in range(startTime, startTime + oneDay, tenMinutes):
                    holder = "S_" + str(col) + "_" + stepHourMin(stepTime)
                    if powerInTenMinutes(series, stepTime):
                        value = "On"
                    else:
                        value = ""
                    if working == "h1":
                        h2 = h1.replace(holder, value)
                        working = "h2"
                    else:
                        h1 = h2.replace(holder, value)
                        working = "h1"
            elif series and "temperature" in gerasPath.lower():
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
            elif series and "pir" in gerasPath.lower() and "binary" in gerasPath.lower():
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

        
    
    
    
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Activity for bridge " + bid + " from " + nicedate(startTime) + " to " + nicedate(endTime)
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
    
    fp = open('image001.png', 'rb')
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
              
if __name__ == '__main__':
    cbr_email()

