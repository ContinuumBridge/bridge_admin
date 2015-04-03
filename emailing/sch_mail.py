#!/usr/bin/env python
# sch_email.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#
# Modified MWS 11th Nov 2014

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
fileName           = "Sirona table template.htm"

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

"""
def powerInTenMinutes(series, time):
    This used to return the first value found
    It now returns the final value as a frig for Richard's radio (and anything else continuous).
    Flip side is that we'll miss most kettle On->Offs
    Proper solution is to read the series in the main code & do something sensible
    Don't check in until this is fixed!!!

    finalValue = ""
    for s in series:
        if s["t"] >= time and s["t"] < time + tenMinutes:
            finalValue = s['v']
    if finalValue == "":
        return ""
    else:
        return finalValue
"""
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

def shc_email(user, password, bid, to, key):
    h1 = ""
    h2 = ""
    working = ""
    if not bid:
        print "You must provide a bridge ID using the --bid option."
        exit()
    else:
        print "Requesting list"
        try:
            r = requests.get('http://geras.1248.io/serieslist', auth=(key,''))
            allseries = json.loads(r.content)
        except Exception as inst:
            logging.warning("%s Failed to get list of time series", ModuleName)
            logging.warning("%s Exception: %s %s", ModuleName, type(inst), str(inst.args))
            exit()
        serieslist = []
        for t in allseries:
            if bid in t:
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
    for s in serieslist:
        if not("magnet_y" in s or "magnet_z" in s or "battery" in s or "connected" in s or "luminance" in s  or ("tbk" in s.lower() and "binary" in s.lower()) or "lounge-light" in s.lower()): 
            url = gerasurl + 'series/' + s +'?start=' + str(startTime) + '&end=' + str(endTime)
            print "url:", url
            r = requests.get(url, auth=(key,''))
            timeseries[s] = json.loads(r.content)
            series = timeseries[s]["e"]
            ss = s.split('/')

            if "PIR" in ss[2]:
                ss[3] = ss[3].replace("binary", "Activity")
            if "magnet" in ss[3]:
                ss[3] = ss[3].replace("magnet_x", "Movement")
            # one more case
            if "TBK" in ss[2]:
                ss[3] = ss[3].replace("binary", "Switch")
            ss[3] = ss[3].replace("binary", "")
            ss[2] = ss[2].replace("Fib_PIR-", "")
            ss[2] = ss[2].replace("Fib_PIR_", "")
            ss[2] = ss[2].replace("PIR_Fib-", "")
            ss[2] = ss[2].replace("PIR_Fib_", "")            
            ss[2] = ss[2].replace("MagSW_ES-", "")
            ss[2] = ss[2].replace("MagSW_ES_", "")
            ss[2] = ss[2].replace("TBK_SW_curr-", "")
            ss[2] = ss[2].replace("TBK_SW_curr_", "")
            ss[2] = ss[2].replace("SW_TBK_curr-", "")
            ss[2] = ss[2].replace("SW_TBK_curr_", "")
            ss[2] = ss[2].replace("Tag", "")            
            # another two to get rid of
            ss[2] = ss[2].replace("PIR_AEON-", "")
            ss[2] = ss[2].replace("SW_TBK-", "")
                        
            # some hyphens were left
            ss[2] = ss[2].replace("-", " ")
            
            ss[2] = ss[2].replace("_", " ")            
            ss[1] = ""
                     
            for value in (ss[1], ss[2], ss[3]): 
                holder = "S_" + str(col) + "_name" + str(ss.index(value))
                print "holder:", holder, " value:", value
                if working == "h1":
                    h2 = h1.replace(holder, value)
                    working = "h2"
                else:
                    h1 = h2.replace(holder, value)
                    working = "h1"

            if series and ((("door" in s.lower() and "magsw" in s.lower()) or "cupboard" in s.lower()) and "binary" in s.lower()):
                for stepTime in range(startTime, startTime + oneDay, tenMinutes):
                    holder = "S_" + str(col) + "_" + stepHourMin(stepTime)
                    #print "stepTime:", nicetime(stepTime), " holder:", holder
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
            elif series and "power" in s.lower():
                prevPower = "" 
                if "toaster" in s.lower() or "kettle" in s.lower():
                    threshold = 1000
                elif "coffee_maker" in s.lower():
                    threshold = 50
                else:
                    threshold = 3.5
                    
                for stepTime in range(startTime, startTime + oneDay, tenMinutes):
                    op = prevPower
                    finalValue = -12                    
                    for ss in series:
                        #print "n:", ss['n'], "t:", nicetime(ss['t']), "v:", ss['v']
                        holder = "S_" + str(col) + "_" + stepHourMin(stepTime)
                        """
                        If any point is over the threshold, the answer, op, is ON. 
                        Otherwise it's prevPower (which starts at OFF and then is always 
                        the last value found in the slot)
                        """
                        if ss["t"] >= stepTime and ss["t"] < stepTime + tenMinutes:
                            #print "   found", s['v'], "on", s['n'], "at", nicetime(s['t'])
                            finalValue = ss['v'] # always the last value found
                            if ss['v'] > threshold:
                                op = "On"
                                #print "***Found a high point:", ss['v'], "at", nicetime(ss['t'])
                                    
                    #print "      final value for", ss['n'], nicetime(stepTime), "was:", finalValue
                    if finalValue > threshold:
                        prevPower = "On"           
                    elif finalValue > 0:
                        prevPower = ""  
                    # else it was -12 : there were no points    
                                            
                    #print "         So op = ", op, " and prevPower = ", prevPower, "for", nicetime(stepTime), "on", ss['n']
                    if working == "h1":
                        h2 = h1.replace(holder, op)
                        working = "h2"
                    else:
                        h1 = h2.replace(holder, op)
                        working = "h1"
                        
            elif series and "temperature" in s.lower():
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
            elif series and "pir" in s.lower() and "binary" in s.lower():
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
            elif series and "magnet" in s.lower():
                for stepTime in range(startTime, startTime + oneDay, tenMinutes):
                    holder = "S_" + str(col) + "_" + stepHourMin(stepTime)
                    if activeInTenMinutes(series, stepTime):
                        value = "Moved"
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
    print "Sent mail"
    mail.quit()
       
if __name__ == '__main__':
    shc_email()

