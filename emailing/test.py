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

def shc_email():
    # Create message container - the correct MIME type is multipart/alternative.
    to = "peter.claydon@continuumbridge.com, peterclaydon@peterclaydon.com"
    user = "bridges@continuumbridge.com"
    password = "cbridgest00f@r"
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Activity for bridge "
    msg['From'] = "Bridges <bridges@continuumbridge.com>"
    recipients = to.split(',')
    recipients = [p.strip(' ') for p in recipients]
    if len(recipients) == 1:
        msg['To'] = to
    else:
        msg['To'] = ", ".join(recipients)
    print "To:", msg['To']
    # Create the body of the message (a plain-text and an HTML version).
    text = "Content only available with HTML email clients\n"
    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText("Wot", 'plain')
    part2 = MIMEText("Where", 'html')
    
    msg.attach(part1)
    msg.attach(part2)
    mail = smtplib.SMTP('smtp.gmail.com', 587)
    mail.ehlo()
    mail.starttls()
    mail.login(user, password)
    mail.sendmail(user, recipients, msg.as_string())
    mail.quit()

if __name__ == '__main__':
    shc_email()

