import os
import sys
import json
import time
from subprocess import check_output
from MeteorClient import MeteorClient
import datetime
import threading

def nicetime(timeStamp):
    localtime = time.localtime(timeStamp)
    milliseconds = '%03d' % int((timeStamp - int(timeStamp)) * 1000)
    now = time.strftime('%d-%m-%Y, %H:%M:%S', localtime)
    return now

def mcConnected():
    print("{}: Meteor client connected".format(nicetime(time.time())))
    event.set()

def mcLoggedIn(data):
    print("{}: Meteor client logged-in".format(nicetime(time.time())))
    event.set()

def mcFailed(collection, data):
    print("Failed: ")
    print(json.dumps(data, indent=4))

def mcClosed(code, reason):
    print("{}: Closed, reason: {}".format(nicetime(time.time()), reason))

def mcLoggingIn():
    print("{}: Logging in".format(nicetime(time.time())))

def mcLoggedOut():
    print("{}: Logged out".format(nicetime(time.time())))

def mcLoginCheck(error, login):
    print("{}: mcLoginCheck. Error: {}, login: {}".format(nicetime(time.time()), error, login))

def mcSubscribed(subscription):
    print("{}: Subscribed: ".format(subscription))

def mcSubscribeCallback(error):
    if error != None:
        print("{}: Meteor client subscribe error: {}".format(nicetime(time.time()), error))

def mcAdded(collection, id, fields):
    pass

def mcChanged(collection, id, fields, cleared):
    pass

def mcRemoved(collection, id):
    pass
    #print('* REMOVED {} {}'.format(collection, id))

def subscribe():
    try:
        mc.subscribe("lists", callback=mcSubscribeCallback)
        mc.subscribe("buttons", callback=mcSubscribeCallback)
        mc.subscribe("screensets", callback=mcSubscribeCallback)
        mc.subscribe("organisations", callback=mcSubscribeCallback)
    	print("{}: Subscribied".format(nicetime(time.time())))
        event.set()
        return True
    except Exception as ex:
        print("mcLoggedIn. Already subscribed, exception type {}, exception: {}".format(type(ex), ex.args))
        return  False

if __name__ == '__main__':
    meteor_websocket = "ws://staging.spur.site/websocket"
    mc = MeteorClient(meteor_websocket)
    mc.on('connected', mcConnected)
    mc.on('logging_in', mcLoggingIn)
    mc.on('logged_in', mcLoggedIn)
    mc.on('logged_out', mcLoggedOut)
    mc.on('failed', mcFailed)
    mc.on('closed', mcClosed)
    mc.on('subscribed', mcSubscribed)
    mc.on('added', mcAdded)
    mc.on('changed', mcChanged)
    mc.on('removed', mcRemoved)
    print("{}: Connecting".format(nicetime(time.time())))
    event = threading.Event()
    mc.connect()
    subscribe()
    event.wait()
    print("{}: Returned from subscribe".format(nicetime(time.time())))
    event.clear()
    event = threading.Event()
    mc.login("peter.claydon@continuumbridge.com", "Mucht00f@r", callback=mcLoginCheck)
    event.wait()
    print("{}: Returned from login".format(nicetime(time.time())))
    event.clear()
    sys.exit()


