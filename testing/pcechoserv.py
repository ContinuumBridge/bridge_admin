#!/usr/bin/env python

# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

### Protocol Implementation

# This is just about the simplest possible protocol
class Echo(Protocol):
    def dataReceived(self, data):
        """
        As soon as any data is received, write it back.
        """
        print "Data received: ", data
        self.transport.write(data)
    def connectionMade(self):
        print "Connection made to ", self.transport.getPeer()
    def connectionLost(self, reason):
        print "Disconnected"


def main():
    f = Factory()
    f.protocol = Echo
    reactor.listenUNIX("/tmp/pcsocket", f, backlog=10)
    reactor.run()

if __name__ == '__main__':
    main()
