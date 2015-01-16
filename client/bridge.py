
import httplib 
import json
import requests
import websocket
import time
import signal
from twisted.internet import threads
from twisted.internet import defer
from twisted.internet import reactor

# Production
CB_ADDRESS          = "portal.continuumbridge.com"
KEY                 = 'd022633eV1CJiHtu6ruzzSkjFkJQPsFv5/FXfF2ONbhUehuAUuwNaVp+izqkQmjY'

class Connection(object):
    def __init__(self):
        self.boilerState = 0
        reactor.callInThread(self.connect)
        reactor.run()

    def connect(self) :
        auth_url = "http://" + CB_ADDRESS + "/api/bridge/v1/bridge_auth/login/"
        auth_data = '{"key": "' + KEY + '"}'
        auth_headers = {'content-type': 'application/json'}
        response = requests.post(auth_url, data=auth_data, headers=auth_headers)
        try:
            text = json.loads(response.text)
            print "text: ", text
            print(json.dumps(text, indent=4))
        except Exception as ex:
            print "Problem loading response"
            print "Exception: ", type(ex), str(ex.args)
        try:
            sessionID = response.cookies['sessionid']
            print "sessionID: ", sessionID
        except Exception as ex:
            print "Could not load sessionid"
            print "Exception: ", type(ex), str(ex.args)

        ws_url = "ws://" + CB_ADDRESS + ":9416/"
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

    def signalHandler(self, signal, frame):
        logging.debug("%s signalHandler received signal", ModuleName)
        reactor.stop()
        exit()

if __name__ == '__main__':
    connection = Connection()
