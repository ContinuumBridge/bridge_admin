
import httplib 
import json
import requests
import websocket
import time
import signal
from twisted.internet import threads
from twisted.internet import defer
from twisted.internet import reactor

CB_ADDRESS          = "staging.continuumbridge.com"
KEY                 = "649e038do23icDEnfrtxf0BRCbLw9exPIyTDKSxJtm8EGm10jG4vMjUFRZqLmbfE"
START_DELAY         = 60
SWITCH_INTERVAL     = 60
DESTINATION         = "BID55/AID29"

class Connection(object):
    def __init__(self):
        self.boilerState = 0
        reactor.callInThread(self.connect)
        reactor.callLater(START_DELAY, self.switchBoiler)
        reactor.run()

    def connect(self) :
        auth_url = "http://" + CB_ADDRESS + "/api/client/v1/client_auth/login/"
        auth_data = '{"key": "' + KEY + '"}'
        auth_headers = {'content-type': 'application/json'}
        response = requests.post(auth_url, data=auth_data, headers=auth_headers)
        self.cbid = json.loads(response.text)['cbid']
        sessionID = response.cookies['sessionid']

        ws_url = "ws://" + CB_ADDRESS + ":7522/"
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
                        ws_url,
                        on_open   = self._onopen,
                        header = ['sessionID: {0}'.format(sessionID)],
                        on_message = self._onmessage)
        self.ws.run_forever()

    def _onopen(self, ws):
        print "on_open"

    def _onmessage(self, ws, message):
        msg = json.loads(message)
        print "Message received:"
        print(json.dumps(msg, indent=4))

    def switchBoiler(self):
        msg = {
                "source": self.cbid,
                "destination": DESTINATION,
                "body": {
                            "n": 0,
                            "d":
                                [
                                  {
                                    "i": "Boiler",
                                    "s": self.boilerState,
                                    "at": int(time.time() + 20)
                                  }
                                ]
                        }
              }
        print "Sending: ", msg
        self.ws.send(json.dumps(msg))
        print "Message sent"
        if self.boilerState == 0:
            self.boilerState = 1
        else:
            self.boilerState = 0
        reactor.callLater(SWITCH_INTERVAL, self.switchBoiler)

    def signalHandler(self, signal, frame):
        logging.debug("%s signalHandler received signal", ModuleName)
        reactor.stop()
        exit()

if __name__ == '__main__':
    connection = Connection()
