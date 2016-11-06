#!/usr/bin/env python
# app_client.py
# Copyright (C) ContinuumBridge Limited, 2015 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#
"""
"""

import json
import requests
import time
import sys
import os.path
import signal
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage
import logging
import logging.handlers
import twilio
import twilio.rest
from autobahn.twisted.websocket import WebSocketClientFactory, WebSocketClientProtocol, connectWS
from twisted.internet import threads
from twisted.internet import reactor, defer
from twisted.internet.protocol import ReconnectingClientFactory

HOME                  = os.path.expanduser("~")
KEY                   = "7925d041v92J1xbwf41xMyVZOScjfB2xOWfq+iCtRw+l5LJH3S+7oauMlcwIjFzv"
CB_LOGFILE            = "twisted_bridge.log"
# Address: 054.076.145.070
CB_ADDRESS            = "portal.continuumbridge.com"
CB_LOGGING_LEVEL      = "DEBUG"
 
logger = logging.getLogger('Logger')
logger.setLevel(CB_LOGGING_LEVEL)
handler = logging.handlers.RotatingFileHandler(CB_LOGFILE, maxBytes=10000000, backupCount=5)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def nicetime(timeStamp):
    localtime = time.localtime(timeStamp)
    milliseconds = '%03d' % int((timeStamp - int(timeStamp)) * 1000)
    now = time.strftime('%H:%M:%S, %d-%m-%Y', localtime)
    return now

def authorise():
    auth_url = "http://" + CB_ADDRESS + "/api/client/v1/client_auth/login/"
    auth_data = '{"key": "' + KEY + '"}'
    auth_headers = {'content-type': 'application/json'}
    response = requests.post(auth_url, data=auth_data, headers=auth_headers)
    resp = json.loads(response.text)
    sessionID = response.cookies['sessionid']
    ws_url = "ws://" + CB_ADDRESS + ":7522/"
    return sessionID, ws_url
    
class ClientWSFactory(ReconnectingClientFactory, WebSocketClientFactory):
    maxDelay = 60
    maxRetries = 200
    def startedConnecting(self, connector):
        print('Started to connect.')
        ReconnectingClientFactory.resetDelay

    def clientConnectionLost(self, connector, reason):
        print 'Lost connection. Reason: ', reason
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print 'Lost reason. Reason: ', reason
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

class ClientWSProtocol(WebSocketClientProtocol):
    def __init__(self):
        print "Connection __init__"
        signal.signal(signal.SIGINT, self.signalHandler)  # For catching SIGINT
        signal.signal(signal.SIGTERM, self.signalHandler)  # For catching SIGTERM
        self.stopping = False
        self.buttonStates = {}
        self.reconnects = 0
        self.reauthorise = 0
        self.sendCount = 0

    def signalHandler(self, signal, frame):
        print "signalHandler received signal"
        self.stopping = True
        reactor.stop()

    def sendAck(self, ack):
        self.sendMessage(json.dumps(ack))

    def onConnect(self, response):
        print "Server connected: ", str(response.peer)

    def onOpen(self):
        print "WebSocket connection open."

    def onClose(self, wasClean, code, reason):
        print "onClose, reason:: %s", reason

    def onMessage(self, message, isBinary):
        print "onMessage"
        try:
            msg = json.loads(message)
            print "Message received: ", json.dumps(msg, indent=4)
        except Exception as ex:
            print "onmessage. Unable to load json: ", str(type(ex)), str(ex.args)

if __name__ == '__main__':
    sessionID, ws_url = authorise()
    print "sessionID: ", sessionID, ", ws_url: ", ws_url
    headers = {'sessionID': sessionID}
    factory = ClientWSFactory(ws_url, headers=headers, debug=False)
    factory.protocol = ClientWSProtocol
    connectWS(factory)
    reactor.run()
