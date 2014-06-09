#!/usr/bin/env python
from pprint import pformat
import time

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

#now = int(time.time())
now = 1402328172
agent = Agent(reactor)
d = agent.request(
    'POST',
    'http://192.168.0.83:8083/ZWaveAPI/Data/1402328172',
    #'http://localhost:8083/ZWaveAPI/Data/' + str(now),
    Headers({'User-Agent': ['Twisted Web Client Example']}),
    None)

def cbRequest(response):
    print 'Response version:', response.version
    print 'Response code:', response.code
    print 'Response phrase:', response.phrase
    print 'Response headers:'
    print pformat(list(response.headers.getAllRawHeaders()))
    print 'Body: ', response.body
    #print 'Body: ', readBody(response)
    #d = readBody(response)
    d.addCallback(cbBody)
    return d
d.addCallback(cbRequest)

def cbBody(body):
    print 'Response body:'
    print body

def cbShutdown(ignored):
    reactor.stop()
d.addBoth(cbShutdown)

reactor.run()
