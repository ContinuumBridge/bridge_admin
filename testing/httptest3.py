#!/usr/bin/env python

from pprint import pformat
import time

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

class BeginningPrinter(Protocol):
    def __init__(self, finished):
        self.finished = finished
        self.remaining = 1024 * 10

    def dataReceived(self, bytes):
        if self.remaining:
            display = bytes[:self.remaining]
            print 'Some data received:'
            print display
            self.remaining -= len(display)

    def connectionLost(self, reason):
        print 'Finished receiving body:', reason.getErrorMessage()
        self.finished.callback(None)

class onReceived(Protocol):
    def __init__(self, finished):
        self.finished = finished

    def dataReceived(self, bytes):
        print bytes

    def connectionLost(self, reason):
        print 'Finished receiving body:', reason.getErrorMessage()
        self.finished.callback(None)

def cbRequest(response):
    print 'Response version:', response.version
    print 'Response code:', response.code
    print 'Response phrase:', response.phrase
    print 'Response headers:'
    print pformat(list(response.headers.getAllRawHeaders()))
    finished = Deferred()
    #response.deliverBody(BeginningPrinter(finished))
    response.deliverBody(onReceived(finished))
    return finished

startTime = str(int(time.time() - 1))
agent = Agent(reactor)
d = agent.request(
    'POST',
    'http://localhost:8083/ZWaveAPI/Data/' + startTime,
    #'http://example.com/',
    Headers({'User-Agent': ['Twisted Web Client Example']}),
    None)

d.addCallback(cbRequest)

time.sleep(1)

d = agent.request(
    'POST',
    'http://localhost:8083/ZWaveAPI/Data/' + startTime,
    #'http://example.com/',
    Headers({'User-Agent': ['Twisted Web Client Example']}),
    None)

d.addCallback(cbRequest)


#def cbShutdown(ignored):
#    reactor.stop()
#d.addBoth(cbShutdown)

reactor.run()
