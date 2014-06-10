#!/usr/bin/env python
# concentrator.py
# Copyright (C) ContinuumBridge Limited, 2013 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#

import sys
import time
import os
import json
from pprint import pprint
from twisted.internet.protocol import Protocol, Factory
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import task
from twisted.internet import threads
from twisted.internet import defer
from twisted.internet import reactor


class Concentrator():
    def __init__(self):
        self.doStop = False
        reactor.callLater(1, self.getValues)
        reactor.run()

    def getValues(self):
        try:
            while not self.doStop:
                reactor.callInThread(self.getValue)
        except (KeyboardInterrupt, SystemExit):
            self.doStop = True
            reactor.callLater(5, self.goodbye)

    def getValue(self):
        print "getValue"

    def goodbye(self):
        print "Goodbye"
        sys.exit()

if __name__ == '__main__':
    concentrator = Concentrator()
