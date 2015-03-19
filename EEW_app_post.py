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
from itertools import cycle

#Constants
tenMinutes         = 10 * 60
oneHour            = 60 * 60
oneDay = 60*60*24

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

def start():
    t = time.localtime(time.time() - oneDay)
    yesterday = time.strftime('%Y-%m-%d', t)
    s = yesterday + " 12:00:00"
    return epochtime(s)

@click.command()
@click.option('--bid', nargs=1, help='The bridge ID to list.')
@click.option('--key', prompt='Geras API key', help='Your Geras API key. See http://geras.1248.io/user/apidoc.')

def EEW_app_post(bid, key):

    # Build the list of available temp sensors on bid & build inside/outside lists
    if not bid:
        print "You must provide a bridge ID using the --bid option."
        exit()

    print "Requesting list"
    r = requests.get('http://geras.1248.io/serieslist', auth=(key,''))
    allseries = json.loads(r.content)
    inside_serieslist = []
    outside_serieslist = [] 
    inside_count = 0       
    for t in allseries:
        if (bid+"/") in t and "temperature" in t.lower() and "outside" in t.lower():
            outside_serieslist.append(t)
        elif (bid+"/") in t and "temperature" in t.lower(): # it's inside
            inside_serieslist.append(t)
            inside_count += 1
     
    # Fetch all the data
    series_i = {}
    series_o = {}  
    for s in outside_serieslist:
        url = gerasurl + 'series' + s # + "?rollup=avg&interval=1h"        
        print "Fetching:", url     
        ro = requests.get(url, auth=(key,''))
        series_o[s] = json.loads(ro.content)
        outsideSeries = series_o[s]["e"] # a list of dicts
        firstD = outsideSeries[0]['t']
        lastD = outsideSeries[-1]['t']

    insideSeries = {}
    for s in inside_serieslist:
        url = gerasurl + 'series' + s # + "?rollup=avg&interval=1h"        
        print "Fetching:", url     
        ri = requests.get(url, auth=(key,''))
        series_i[s] = json.loads(ri.content)
        insideSeries[s] = series_i[s]["e"] # a list of dicts
        if firstD < insideSeries[s][0]['t']:
            firstD = insideSeries[s][0]['t']
        if lastD > insideSeries[s][-1]['t']:
            lastD = insideSeries[s][-1]['t']
                                
    firstDay = time.strftime("%Y %b %d %H:%M", time.localtime(firstD)).split()
    lastDay = time.strftime("%Y %b %d %H:%M", time.localtime(lastD)).split()
    lastDay[3] = "00:00"
    firstDay[3] = "00:00"
    fd_epoch = time.mktime(time.strptime(" ".join(firstDay), "%Y %b %d %H:%M"))
    ld_epoch = time.mktime(time.strptime(" ".join(lastDay), "%Y %b %d %H:%M"))

    daysToProcess = []                      
    minmax_list_i = []
    minmax_list_o = []        
    for day in range(int(fd_epoch),int(ld_epoch), oneDay):
        #print "\n*** Next Day *** Next Day *** Next Day *** Next Day *** Next Day *** Next Day *** Next Day"
        #for s in outside_serieslist: # For now, there's only one
        minmax = {'day':day, 's':s, 'max_t':-100, 'max_time':0, 'max_index':-1, 'min_t':100, 'min_time':-0, 'min_index':-1, 'datapoints':0}
        for p in range(0,len(outsideSeries)):
            minmax['s'] = outsideSeries[p]['n'] #remember there's only one
            if outsideSeries[p]['t'] > day+startNight_e and outsideSeries[p]['t'] < (day+oneDay+endNight_e):
                #print "outside t,v:", outsideSeries[p]['t'], ":", outsideSeries[p]['v']
                if outsideSeries[p]['v'] > minmax['max_t']:
                    minmax['max_t'] = outsideSeries[p]['v']
                    minmax['max_time'] = outsideSeries[p]['t']
                    minmax['max_index'] = p                        
                if outsideSeries[p]['v'] < minmax['min_t']:
                    minmax['min_t'] = outsideSeries[p]['v']
                    minmax['min_time'] = outsideSeries[p]['t']
                    minmax['min_index'] = p
                #print "outside minmax for day:", nicetime(day)
                #print json.dumps(minmax, indent=4)

        # Only proceed if there were enough outside points 
        if minmax['min_index'] - minmax['max_index'] > 3 and (
          # and min was after max, and they were far enough apart - say 4 hours
          minmax['min_time'] - minmax['max_time'] > 4*oneHour): 
             #print "    Adding", nicedate(day), minmax['s'], "to minmax_list_o"
            minmax_list_o.append (minmax)           
            dayAdded = 0
            for s in inside_serieslist:
                #print "Next s on", nicedate(day), "is", s 
                minmax = {'day':day, 's':s, 'max_t':-100, 'max_time':0, 'max_index':-1, 'min_t':100, 'min_time':-0, 'min_index':-1, 'datapoints':0}
                for p in range(0,len(insideSeries[s])):
                    if insideSeries[s][p]['t'] > day+startNight_e and insideSeries[s][p]['t'] < (day+oneDay+endNight_e):
                        if insideSeries[s][p]['v'] > minmax['max_t']:
                            minmax['max_t'] = insideSeries[s][p]['v']
                            minmax['max_time'] = insideSeries[s][p]['t']
                            minmax['max_index'] = p
                        if insideSeries[s][p]['v'] < minmax['min_t']:
                            minmax['min_t'] = insideSeries[s][p]['v']
                            minmax['min_time'] = insideSeries[s][p]['t']
                            minmax['min_index'] = p
                        minmax['datapoints'] = minmax['min_index'] - minmax['max_index']
                # similar conditions for inclusion as for outside
                if minmax['min_index'] - minmax['max_index'] >= 3 and (
                # and min was after max, and they were far enough apart - say 4 hours
                  minmax['min_time'] - minmax['max_time'] > 4*oneHour):
                    minmax_list_i.append(minmax)
                    if not dayAdded:
                        daysToProcess.append(day)
                        dayAdded = 1
                        #print "Adding", nicedate(day), s, "to days to process"
                """
                elif minmax['datapoints'] >1:
                    print "Eliminating", s, "on", nicetime(day), "because:", json.dumps(minmax, indent=4)
                    print "   and maxtime:", nicetime(minmax['max_time']), "mintime:", nicetime(minmax['min_time']), ":", (minmax['min_time']-minmax['max_time'])/oneHour, "hours"
                """

    # What have we got?       
    #print "inside:", json.dumps(minmax_list_i, indent=4)
    #print json.dumps(daysToProcess, indent=4)
                   
    #print "Found:" #, len(days_toProcess), "days out of", int((ld_epoch - fd_epoch)/oneDay)
    eff = 0
    for today in daysToProcess:
        print "New day:", today, nicedate(today)
        for d in minmax_list_o:
            if d['day'] == today:
                #print json.dumps(d, indent=4) # "min_out=", minmax_list_o[day]['min_t'], "max_out=", minmax_list_o[day]['max_t']
                tot = 0
                for i in range(d['max_index'], d['min_index']):
                    #print "    ", nicetime(outsideSeries[i]['t']),":",outsideSeries[i]['v']
                    tot = tot + outsideSeries[i]['v']
                outAve = tot/(d['min_index'] - d['max_index'])

        for s in inside_serieslist:
            for d in minmax_list_i:
                if d['day'] == today and d['s'] == s:
                    tFall = d['max_t'] - d['min_t']
                    timeDiff = (float(d['min_time']) - float(d['max_time']))/60/60                        
                    tdiff = d['max_t'] - outAve
                    eff = 1/(tFall/timeDiff/tdiff)
                    #minmax['eff'] = eff
                    print "     today:",nicedate(today), "eff=", eff, "for", s

    print json.dumps(minmax_list_i, indent=4) 
    
    """
    ip = raw_input("Continue? (CR): ") 
    if ip <> "": 
        exit()                                                     
    """
        
if __name__ == '__main__':
    EEW_app_post()

