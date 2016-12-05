from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol, connectWS
import json
import requests
CB_ADDRESS            = "portal.continuumbridge.com"

config = {
    "bridges": ["BID144"],
    "cid": "CID157",
    "cid_key": "e76ec5ebfLcVPGPhQUQArniEqV46lDA2YVnJwB96o3x/NkjO2A0cagGg4dvVya+R",
    "uuids": "01000002be040bc968070201",
    "buttonsURL": "http://54.76.157.10:3005/api/buttons/",
    "buttonsKey": "galvanize",
    "mail":{
        "password": "Mucht00f@r",
        "user": "bridges@continuumbridge.com",
        "from": "Bridges <bridges@continuumbridge.com>"
    },
    "buttons": [
        {"id": 1283,
         "name": "Downstairs photocopier",
         "email": "peter.claydon@continuumbridge.com"
        }
       ]
}

class MyClientProtocol(WebSocketClientProtocol):

    def onConnect(self, response):
        print("Server connected: {0}".format(response.peer))

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))

def authorise():
    reconnects = 0
    auth_url = "http://" + CB_ADDRESS + "/api/client/v1/client_auth/login/"
    auth_data = '{"key": "' + config["cid_key"] + '"}'
    print("auth_data: ", auth_data)
    auth_headers = {'content-type': 'application/json'}
    response = requests.post(auth_url, data=auth_data, headers=auth_headers)
    print("response text: ", response.text)
    cbid = json.loads(response.text)['cbid']
    sessionID = response.cookies['sessionid']
    ws_url = "ws://" + CB_ADDRESS + ":7522/"
    #ws_url = "ws://" + CB_ADDRESS +"/"
    return cbid, sessionID, ws_url

if __name__ == '__main__':

    import sys

    from twisted.python import log
    from twisted.internet import reactor

    log.startLogging(sys.stdout)
    
    cbid, sessionID, ws_url = authorise()
    print ("cbid: %s, sessionID: %s, ws_url: %s", cbid, sessionID, ws_url)
    #headers = ['sessionID: {0}'.format(sessionID)]
    headers = {'sessionID': sessionID}
    factory = WebSocketClientFactory(ws_url, headers=headers)
    #factory = WebSocketClientFactory(ws_url, headers=headers, debug=True)
    #factory = WebSocketClientFactory(ws_url, debug=True)
    factory.protocol = MyClientProtocol

    connectWS(factory)
    #reactor.connectTCP(ws_url, 7522, factory)
    #reactor.connectTCP("127.0.0.1", 9000, factory)
    reactor.run()
