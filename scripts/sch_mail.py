#!/usr/bin/env python
# sch_email.py
# Copyright (C) ContinuumBridge Limited, 2013-14 - All Rights Reserved
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
import smtplib
from itertools import cycle
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


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

def epochtime(date_time):
    pattern = '%Y-%m-%d %H:%M:%S'
    epoch = int(time.mktime(time.strptime(date_time, pattern)))
    return epoch

@click.command()
@click.option('--user', nargs=1, help='User name of email account.')
@click.option('--password', prompt='Password', help='Password of email account.')
@click.option('--start', nargs=1, help='Start time for getting time series in the format: 18-10-2014 11:05:02.')
@click.option('--end', nargs=1, help='End time for getting time series in the format: 18-10-2014 11:05:02.')
@click.option('--bid', nargs=1, help='The bridge ID to list.')
@click.option('--to', nargs=1, help='The address to send the email to.')
@click.option('--key', prompt='Geras API key', help='Your Geras API key. See http://geras.1248.io/user/apidoc.')

def shc_email(user, password, start, end, bid, to, key):
    me = "Sirona Care and Health <sch@continuumbridge.com>"
    if not bid:
        print "You must provide a bridge ID using the --bid option."
        exit()
    else:
        r = requests.get('http://geras.1248.io/serieslist', auth=(key,''))
        allseries = json.loads(r.content)
        serieslist = []
        for t in allseries:
            if bid in t:
                print t
                if "binary" in t.lower():
                    serieslist.append(t)
        print "Processing:", serieslist
    if start:
        startTime = epochtime(start)
        if end:
            endTime = epochtime(end)
        else:
            endTime = time.time()
        timed = True
    elif end:
        print "If you specify an end time, you must also specify a start time"
        exit()
    else:
        timed = False

    timeseries = {}
    html = "<span style=i\"font-family:Cursive;font-size:12px;font-style:normal;font-weight:normal;"
    html += "text-decoration:none;text-transform:none;color:000000;\">"
    html += "Here is the activity for the 24 hours ending 23:59 on " + nicedate(endTime)
    html += " for bridge " + bid + ".</span>"
    html += """ \
        <style type="text/css">
        .tg  {border-collapse:collapse;border-spacing:0;border-color:#aabcfe;}
        .tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:#aabcfe;color:#669;background-color:#e8edff;}
        .tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:#aabcfe;color:#039;background-color:#b9c9fe;}
        .tg .tg-s6z2{text-align:center}
        .tg .tg-214n{font-size:11px;text-align:center}
        .tg .tg-5hgy{background-color:#D2E4FC;text-align:center}
        </style>
        """
    for s in serieslist:
        if timed:
            #url = gerasurl + 'series/' + s +'?start=' + str(startTime) + '&end=' + str(endTime) +'&rollup=avg&interval=1h'
            url = gerasurl + 'series/' + s +'?start=' + str(startTime) + '&end=' + str(endTime)
        else:
            url = gerasurl + 'series' + s
        print "url:", url
        r = requests.get(url, auth=(key,''))
        timeseries[s] = json.loads(r.content)

        html += "<table class=\"tg\"><tr>"
        html += "<th class=\"tg-s6z2\" colspan=\"2\">Activity for " + s + "</th>"
        html +=  "<th class=\"tg-s6z2\"></th></tr>"
        html += "<td class=\"tg-s6z2\">Time</td>"
        html += "<td class=\"tg-s6z2\">" + "Sensor" + "</td></tr>"

        t = timeseries[s]["e"]
        previous_v = 0
        for s in t:
            if s["v"] == 1 and previous_v == 0:
                action = "activated"
                previous_v = 1
            else:
                previous_v = 0
                action = "deactivated"
            if action == "activated":
                html += "<tr><td class=\"tg-s6z2\">"+nicehours(s["t"]) + "</td>" 
                html += "<td class=\"tg-s6z2\">" + action + "</td></tr>"
                #html += "<tr>\n" + "<td>" + nicetime(s["t"]) + "</td>\n" + "<td>" + action + "</td>" + "</tr>\n"
        html += "</table>\n"
    
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Activity for bridge " + bid
    msg['From'] = "Sirona Care and Health <sch@continuumbridge.com>"
    msg['To'] = to
    
    # Create the body of the message (a plain-text and an HTML version).
    text = "Content only available with HTML email clients\n"
    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    
    msg.attach(part1)
    msg.attach(part2)
    mail = smtplib.SMTP('smtp.gmail.com', 587)
    mail.ehlo()
    mail.starttls()
    mail.login('sch@continuumbridge.com', 'scht00f@r')
    mail.sendmail(me, to, msg.as_string())
    mail.quit()

if __name__ == '__main__':
    shc_email()

