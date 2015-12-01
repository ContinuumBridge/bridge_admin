#!/usr/bin/env python
# EEW_app_post.py
# Copyright (C) ContinuumBridge Limited, 2015 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran
#

gerasurl = 'http://geras.1248.io/'
import requests
import json
import time
import click
import os, sys
import re
import time
import datetime
from itertools import cycle, groupby
import urllib
import csv

#Constants
oneHour            = 60 * 60
oneDay             = oneHour * 24
dburl = "http://onepointtwentyone-horsebrokedown-1.c.influxdb.com:8086/"
debug = 0

startNight_e = 22*oneHour
endNight_e = 8*oneHour

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

def epochTimeOfDay(date_time):
    pattern = '%H:%M:%S'
    epoch = int(time.mktime(time.strptime(date_time, pattern)))
    return epoch

@click.command()
@click.option('--bid', nargs=1, help='The bridge ID to list.')
@click.option('--debug', nargs=1, help='debug level (0-3)')
@click.option('--db', nargs=1, help='The database.')

def EEW_app_ifx(bid, db, debug):
    t_index = 0 
    v_index = 2

    if not bid:
        print "You must provide a bridge ID using the --bid option."
        exit()

    q = "select * from /" + bid + "\/.*temperature.*/" # limit 2"   
    query = urllib.urlencode ({'q':q})
    print "Debug = ", debug
    print "Requesting data from db", db
    url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query
    print "fetching from:", url
    r = requests.get(url)
    pts = r.json()
    #print "pts:", json.dumps (pts, indent=4)

    #ditch the outside series if we're using the "Bath Temps" one
    for s in list(pts):
        if "outside" in s["name"].lower():
            print "deleting:", s["name"]
            pts.remove(s)
    #print "pts after:", json.dumps (pts, indent=4)
        
    # and get the generated outside temp series
    q = "select * from /Outside Bath Temps/" # limit 2"   
    query = urllib.urlencode ({'q':q})
    print "Requesting data from db", db
    url = dburl + "db/" + db + "/series?u=root&p=27ff25609da60f2d&" + query
    print "fetching from:", url
    r = requests.get(url)
    opts = r.json()
    pts.append(opts[0])
    #print "final pts:", json.dumps (pts, indent=4)
    
    sensors = []
    # paranoid: check we're in time order! 
    for s in pts:
        prevT = 0
        for p in reversed(s["points"]): 
            if p[t_index] < prevT:
                print "Gone backwards in time on", s["name"], nicetime(p[t_index]/1000)
                exit()
            prevT = p[t_index]
    # that being the case we can go on to find start and end times
    firstD = time.time()
    print "now = ", nicetime(firstD)
    lastD = 0
    sensors = []
    for sensor in pts:
        prevTime = sensor["points"][0][t_index]
        if "temperature" in sensor["name"].lower():
            print "found:", sensor["name"]
            sensors.append(sensor["name"])
            for pt in (sensor["points"]):
                #print "checking point:", nicetime(pt[t_index]/1000), pt[v_index], "#pts=", len(sensor["points"])
                if pt[t_index]/1000 > lastD:
                    lastD = pt[t_index]/1000 
                    #print "lastD becomes", nicetime(pt[t_index]/1000), "on:", sensor["name"]
                if pt[t_index]/1000 < firstD and pt[t_index]/1000 > 1413324000: # Nothing before 2014-10-14 23:00
                    firstD = pt[t_index]/1000 
                    #print "firstD becomes", nicetime(pt[t_index]/1000), "on:", sensor["name"]

            # what to do about dead sensors?
            """
            for pt in reversed(sensor["points"]):
                if (pt[t_index]/1000 >= firstD and pt[t_index] - prevTime)/1000 > 24*oneHour:
                    print nicetime(pt[t_index]/1000), "time jump of", (pt[t_index] - prevTime)/1000/60/60, "hours on", sensor["name"]
                prevTime = pt[t_index]
            """
    firstDay = time.strftime("%Y %b %d %H:%M", time.localtime(firstD)).split()
    lastDay = time.strftime("%Y %b %d %H:%M", time.localtime(lastD)).split()
    lastDay[3] = "00:00"
    firstDay[3] = "00:00"
    fd_epoch = time.mktime(time.strptime(" ".join(firstDay), "%Y %b %d %H:%M"))
    ld_epoch = time.mktime(time.strptime(" ".join(lastDay), "%Y %b %d %H:%M"))

    # clocks go backwards and forwards so there's 1hr tolerance on these 
    t_off_window_start = oneHour * 15        # 6pm
    t_off_window_end = oneDay + oneHour * 3  # 3am
    t_on_window_start = oneDay + oneHour * 4 # 4am
    t_on_window_end = oneDay + oneHour * 9   # 9am

    # for each day
    # for each room
    # establish time_on and time_off
    # are there enough inside points between these times?
    # is the outside sensor working?
    # do the analysis
    
    print "firstD:", nicetime(firstD), "lastD:", nicetime(lastD)
    row = []
    for thisDay in range(int(fd_epoch),int(ld_epoch), oneDay):
        #print "\n"
        c ={}
        time_on = {}
        time_off = {} 
        minTemp = {}
        maxTemp = {}
        col = 0
        for sensor in pts:
            time_on[sensor["name"]] = 0
            time_off[sensor["name"]] = 0
            minTemp[sensor["name"]] = 30
            maxTemp[sensor["name"]] = 0
            prevTemp = 0
            c[sensor["name"]] =  0
            # find time_off and time_on for inside sensors
            if debug != 0:
                print "doing", nicetime(thisDay), "for:", sensor["name"], "off window is", nicetime(thisDay + t_off_window_start), "to", nicetime(thisDay + t_off_window_end)
            if "outside" not in sensor["name"].lower():
                for pt in reversed(sensor["points"]):
                    if pt[t_index]/1000 >= thisDay + t_off_window_start and pt[t_index]/1000 <=  thisDay + t_off_window_end:
                        if debug >= 2:
                            print "point in OFF window:", nicetime(pt[t_index]/1000), pt[v_index] 
                        if pt[v_index] > prevTemp: # a positive gradient so maybe the last point
                            time_off[sensor["name"]] = pt[t_index]/1000
                            maxTemp[sensor["name"]] = pt[v_index]
                            if debug >= 2:
                                print "     last +ve grad to:", pt[v_index], "at", nicetime(time_off[sensor["name"]])         
                        prevTemp = pt[v_index]
                if time_off[sensor["name"]] != 0: # otherwise it's pointless
                    if debug >= 2:
                        print "so time_off = ", maxTemp[sensor["name"]], "at", nicetime(time_off[sensor["name"]])         
                    for pt in reversed(sensor["points"]): 
                        # changed to start at time_off rather than t_on_window_start
                        if pt[t_index]/1000 >= time_off[sensor["name"]] and pt[t_index]/1000 <=  thisDay + t_on_window_end:
                            if debug >= 2:
                                print "point in ON window:", nicetime(pt[t_index]/1000), pt[v_index], "cos win from", nicetime(time_off[sensor["name"]]), "to",nicetime(thisDay + t_on_window_end)
                            if pt[v_index] < minTemp[sensor["name"]]:
                                minTemp[sensor["name"]] = pt[v_index]
                                time_on[sensor["name"]] = pt[t_index]/1000
                                if debug >= 2:
                                    print "     min so far:", pt[v_index], "at", nicetime(pt[t_index]/1000)

                if time_on[sensor["name"]] == 0:
                    if debug != 0:
                        print "*** Failed to find time_on for:", nicetime(thisDay), sensor["name"]
                    continue
                elif time_off[sensor["name"]] == 0:
                    if debug != 0:
                        print "*** Failed to find time_off for:", nicetime(thisDay), sensor["name"]
                    continue
                else:            
                    if debug >= 1:
                        print "    so for", sensor["name"]
                        print "        time_off = ", nicetime(time_off[sensor["name"]])
                        print "        time_on = ", nicetime(time_on[sensor["name"]])
                    #Count the night points
                    for x in sensor["points"]:
                        if x[t_index]/1000 >= time_off[sensor["name"]] and x[t_index]/1000 <=  time_on[sensor["name"]]:
                            c[sensor["name"]] += 1
            else: # we're outsdide - is the outside sensor working?
                outsideSeries = sensor["name"]
                for x in sensor["points"]:
                    if x[t_index]/1000 >= thisDay + t_off_window_start and x[t_index]/1000 <=  thisDay + t_on_window_end:
                        #print "Outside night points:", nicetime(x[t_index]/1000), x[v_index] 
                        c[sensor["name"]] += 1
                if c[sensor["name"]] < 4:
                    outsideGoodToGo = 0
                    if debug != 0:
                        print "outside no good:", c[sensor["name"]], "on", sensor["name"], nicetime(thisDay)
                else:
                    outsideGoodToGo = 1

        if debug != 0:
            print "finishing day", nicedate(thisDay), "with c:", json.dumps(c, indent = 4)

        #do the processing
        eff = 0

        for m in sensors:
            if outsideGoodToGo and "outside" not in m.lower():
                if c[m] < 4:
                    if debug >=1:
                        print m, "no good:", c[m]
                else:
                    #print "\n", nicetime(thisDay), "Going to process:", m
                    #find the everage outside temp between t_off and t_on
                    for sensor in pts:
                        if "outside" in sensor["name"].lower():
                            t_count = 0
                            t_sum = 0
                            for p in sensor["points"]:
                                if p[t_index]/1000 >= time_off[m] and p[t_index]/1000 <= time_on[m]:
                                    t_count += 1
                                    t_sum += p[v_index]
                            if t_count ==0:
                                print "*************** no outside points in range, aborting"
                                print "time off:", nicetime(time_off[m])
                                print "time on:", nicetime(time_on[m])
                                t_ave = -100
                            else:
                                t_ave = t_sum/t_count
                    if t_count != 0:
                        time_diff = float(time_on[m] - time_off[m])/60/60
                        temp_diff = maxTemp[m] - minTemp[m]
                        try:
                            eff = 1/(temp_diff/time_diff/(maxTemp[m] - t_ave))
                        except:
                            print "*** zero division on", m
                            print "    time off:", nicetime(time_off[m])
                            print "    time on:", nicetime(time_on[m])
                            print "    time diff = ", time_diff
                            print "    temp diff = ", temp_diff
                            print "    outside ave = ", t_ave
                            print "    in out diff = ", maxTemp[m] - t_ave 
                            exit()

                        if debug >= 1:
                            print "time off:", nicetime(time_off[m])
                            print "time on:", nicetime(time_on[m])
                            print "time diff = ", time_diff
                            print "temp diff = ", temp_diff
                            print "outside ave = ", t_ave
                            print "in out diff = ", maxTemp[m] - t_ave 
                            print "eff of", m, "=", eff
                        row.append([m, nicetime(time_off[m]), nicetime(time_on[m]), time_diff, temp_diff, eff, t_ave, (maxTemp[m]-t_ave)])
    # need to put the efficiencies for each room in a list
    # and take average, std dev etc.

    row.sort()
    #do the csv file
    headersLine = ["Room", "time_off", "time_on", "time diff", "temp drop", "eff", "T_outside", "T_diff"]
    folder = "/home/martin/Dropbox/Sync_then_delete"
    f = folder + "/" + bid + ".csv"
    if not os.path.exists(os.path.dirname(f)):
        os.makedirs(os.path.dirname(f))            
    with open(f, 'w') as outfile:
        writer = csv.writer(outfile, delimiter=",")
        writer.writerow(headersLine)
        writer.writerows(row)


if __name__ == '__main__':
    EEW_app_ifx()

