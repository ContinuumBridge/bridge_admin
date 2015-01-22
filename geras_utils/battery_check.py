#!/usr/bin/env python
# battery_check.py
# Copyright (C) ContinuumBridge Limited, 2015 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Martin Sotheran

gerasurl = 'http://geras.1248.io/'
import requests
import json
import time
import click
import os, sys
import re
import smtplib
from itertools import cycle

def nicetime(timeStamp):
    localtime = time.localtime(timeStamp)
    now = time.strftime('%Y-%m-%d %H:%M:%S', localtime)
    return now

def epochtime(date_time):
    pattern = '%Y-%m-%d %H:%M:%S'
    epoch = int(time.mktime(time.strptime(date_time, pattern)))
    return epoch

def nicedate(timeStamp):
    localtime = time.localtime(timeStamp)
    now = time.strftime('%Y-%m-%d', localtime)
    return now
    
@click.command()
@click.option('--bid', nargs=1, help='The bridge ID to check.')
@click.option('--key', prompt='Geras API key', help='Your Geras API key. See http://geras.1248.io/user/apidoc.')


#Enhancements to do:-
#1. Find changed batteries - see BID6/PIR_Fib-Outside-Front_Door/battery
#2. Spot a failing battery: fall, fall, silence - see BID6/PIR_Fib-Lounge-Temp/battery

def battery_check (bid, key):
    allBridges = 0
    if not bid:
        print "No BID specified - checking all"
        allBridges = 1

    r = requests.get('http://geras.1248.io/serieslist', auth=(key,''))
    allseries = json.loads(r.content)
    serieslist = []
    if allBridges:
        for t in allseries:
            if 'battery' in t:
                serieslist.append(t)
    else:
        for t in allseries:
            if (bid+"/") in t and 'battery' in t:
                serieslist.append(t)

    bat = {}
    checkList = []
    t = time.localtime(time.time())
    s = time.strftime('%Y-%m-%d %H:%M:%S', t)
    now = epochtime(s)
    oneDay = 60*60*24
    timeseries = {}

    for gerasPath in serieslist:                
        url = gerasurl + 'now' + gerasPath
        #print "\nurl:", url
        r = requests.get(url, auth=(key,''))
        bat = json.loads(r.content)
        bat1 = bat["e"][0]
        age = (now - int(float(bat1['t'])))/oneDay
        if (age > 7):
            print "****Warning", bat1['n'], "(", bat1['v'],"%) not heard from for", age, "days"                 
        elif (now - int(float(bat1['t'])) > oneDay):
            print "**  Warning", bat1['n'], "(", bat1['v'],"%) not heard from for", age, "days"
        if int(float(bat1['v'])) < 80: 
            #print bat1['n'], "=", bat1['v'],"% reported at", nicetime(float(bat1['t']))
            checkList.append(gerasPath)

    print "Batteries to analyse are:\n", (json.dumps(checkList, indent=4))

    for s in checkList: 
        max_bat = 0
        min_bat = 100
        url = gerasurl + 'series' + s        
        print "\nAnalysing:", url     
        r = requests.get(url, auth=(key,''))
        timeseries[s] = json.loads(r.content)
        series = timeseries[s]["e"] # a list of dicts
        #print(json.dumps(series, indent=4))
        for i in range(0,len(series)):
            if series[i]['v'] >= max_bat:
                max_bat = series[i]['v']
                max_bat_time = series[i]['t']
                max_bat_index = i
                #print i, "Latest max_bat=", max_bat, "at", nicetime(float(max_bat_time)), "there are", len(series)-i, "points after this"
            if series[i]['v'] <= min_bat:
                min_bat = series[i]['v']
                min_bat_time = series[i]['t']
                min_bat_index = i
                #print i, "Latest min_bat=", min_bat, "at", nicetime(float(min_bat_time))                
                
        # Oddities
        if (now - max_bat_time) < oneDay:
            print "  Ignoring as max battery was less than 24 hours ago."
            print "  It was", series[max_bat_index]['v'], "% at", nicetime(float(series[max_bat_index]['t'])),"now", series[-1]['v'], "%"
            continue
        """
        if max_bat_index >= len(series)-1:
            print "  Ignoring as max battery at the end of the series. It was", series[-1]['v'], "% at",  nicetime(float(series[-1]['t']))
            continue
        """
        if len(series) < 2:
            print "  Ignoring as there are less than 2 data points. It was", series[-1]['v'], "% at", nicetime(float(series[-1]['t']))
            continue      
        if series[-1]['v'] < 5:
            print "  Ignoring as the battery's already dead (special case for BID8 AEON!)"
            continue              
        if min_bat_index <= max_bat_index:
            print "   min_bat occurs at", nicetime(float(min_bat_time)), "which is before max_bat. Was the battery changed or has it recovered?"
            continue
        if min_bat_index <> len(series)-1:
            print "  min_bat not at the end. This will screw up the projections - investigate"
            #continue            
        """
        print "these are:-"
        for i in range(max_bat_index,len(series)):
            print i, series[i]['v'], "at", nicetime(float(series[i]['t']))
        """
                
        #it should be downhill from here - have a stab at an average gradient
        b_diff = float(series[max_bat_index]['v'] - series[-1]['v']) # assumes the last point is the min battery (same below)
        t_diff = float(series[-1]['t'] - series[max_bat_index]['t']) # It doesn't have to be - fix this later.
        ave_grad = b_diff/t_diff
        
        #Trying to be more clever
        n = 1
        ave1_grad = 0
        for i in range(max_bat_index,len(series)-1):
            b_diff = float(series[i]['v'] - series[i+1]['v'])
            if b_diff <> 0: # only check when it actually changes
                t_diff = float(series[i+1]['t'] - series[i]['t'])
                if t_diff == 0: # seen this once for some bizzare reason
                    print "two points at the same time! t/b_diff = ", t_diff, b_diff                
                else:
                    grad = b_diff/t_diff
                ave1_grad = (ave1_grad + grad)/n
                n += 1
        
        
        """
        print "Ave fall between max and latest   =", oneDay*ave_grad,"%/day"          
        print "Ave fall over individual segments =", oneDay*ave1_grad,"%/day"
        print "min_bat was", series[-1]['v'], "at", nicetime(float(series[-1]['t']))
        """
        #summarise
        ave_grad = -ave_grad
        ave1_grad = -ave1_grad
        # From y=mx+c: zero_time = (gradient*min_bat_time - min_bat)/gradient
        if ave_grad < ave1_grad: #take the most pessimistic
            worst_grad = ave_grad
        else:
            worst_grad = ave1_grad
        zero_time = (worst_grad*series[-1]['t'] - series[-1]['v'])/worst_grad        
        age = (now - series[-1]['t'])/oneDay
        print "  Battery is/was at", series[-1]['v'], "%", age, "days ago. Projected time to 0% is:", nicedate(float(zero_time))
        if zero_time < now:
            print "  0% date is in the past"
        #print "worst_grad:", worst_grad*oneDay, "age:", age, "lastv:", series[-1]['v']
        if age > 7 and worst_grad*oneDay < -2.5 and series[-1]['v'] < 70:
            print "  Almost certainly dead, or on a dead bridge, or disconnected"               
                   
                     
if __name__ == '__main__':
    battery_check()

