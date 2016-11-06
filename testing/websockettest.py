#!/usr/bin/env python
# websockettest.py
# Copyright (C) ContinuumBridge Limited, 2015 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#
"""
Just stick actions from incoming requests into threads.
"""

import json
import requests
import time
import sys
import os.path
import signal
import smtplib
from autobahn.twisted.websocket import WebSocketClientFactory, WebSocketClientProtocol, connectWS
from twisted.internet import threads
from twisted.internet import reactor, defer
from twisted.internet import task
from twisted.internet.protocol import ReconnectingClientFactory

CB_DJANGO_CONTROLLER_ADDR="http://portal.continuumbridge.com/api/bridge/v1/bridge_auth/login/"
CB_NODE_CONTROLLER_ADDR="http://portal.continuumbridge.com"
CB_BRIDGE_KEY='2152bd84nTjDYhXHelYPuiKUXb1WOlyv/3De14IFKwOuKTmTBRJPn5L+SCz3TuC8'

def nicetime(timeStamp):
    localtime = time.localtime(timeStamp)
    milliseconds = '%03d' % int((timeStamp - int(timeStamp)) * 1000)
    now = time.strftime('%H:%M:%S, %d-%m-%Y', localtime)
    return now

def authorise():
    if True:
    #try:
        auth_url = CB_DJANGO_CONTROLLER_ADDR
        #auth_data = '{"key": "' + config["cid_key"] + '"}'
        auth_data = '{"key": "2152bd84nTjDYhXHelYPuiKUXb1WOlyv/3De14IFKwOuKTmTBRJPn5L+SCz3TuC8"}'
        auth_headers = {'content-type': 'application/json'}
        response = requests.post(auth_url, data=auth_data, headers=auth_headers)
        print("response: " + str(response))
        #cbid = json.loads(response.text)['cbid']
        sessionID = response.cookies['sessionid']
        print("sessionID: " + sessionID)
        #ws_url = "ws://" + CB_ADDRESS + ":7522/"
        ws_url = "ws://portal.continuumbridge.com:9416/"
        return sessionID, ws_url
    #except Exception as ex:
    #    print("Unable to authorise with server, type: %s, exception: %s", str(type(ex)), str(ex.args))
    
class ClientWSFactory(WebSocketClientFactory):
    def startedConnecting(self, connector):
        print('Started to connect.')

    def clientConnectionLost(self, connector, reason):
        print('Lost connection. Reason: %s', reason)

    def clientConnectionFailed(self, connector, reason):
        print('Lost reason. Reason: %s', reason)

class ClientWSProtocol(WebSocketClientProtocol):
    def __init__(self):
        print("Connection __init__")
        signal.signal(signal.SIGINT, self.signalHandler)  # For catching SIGINT
        signal.signal(signal.SIGTERM, self.signalHandler)  # For catching SIGTERM

    def signalHandler(self, signal, frame):
        print("signalHandler received signal")
        self.stopping = True
        reactor.stop()

    def onConnect(self, response):
        print("Server connected: %s", str(response.peer))

    def onOpen(self):
        print("WebSocket connection open.")

    def onClose(self, wasClean, code, reason):
        print "onClose, reason: ", reason
        print "onClose, code: ", code

    def onMessage(self, message, isBinary):
        #print("onMessage")
        try:
            msg = json.loads(message)
            print("Message received: %s", json.dumps(msg, indent=4))
        except Exception as ex:
            print("onmessage. Unable to load json, type: %s, exception: %s", str(type(ex)), str(ex.args))

if __name__ == '__main__':
    print("Hello")
    sessionID, ws_url = authorise()
    print "ws_url: ", ws_url
    #headers = {'sessionID': sessionID}
    headers = {'sessionID': sessionID}
    factory = ClientWSFactory(ws_url, headers=headers, debug=True)
    factory.protocol = ClientWSProtocol
    connectWS(factory)
    reactor.run()
