# flasktest2.py
from flask import Flask, jsonify, request
import os
import sys
import json
import time
from subprocess import check_output
import ssl
from MeteorClient import MeteorClient


HOME                    = os.getcwd()
buttonID                = ""
config                  = {}
mc = None

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

def readConfig():
    try:
        global config
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except Exception as ex:
        print("Problem reading button_client.config, type: %s, exception: %s", str(type(ex)), str(ex.args))

def onButtonChange(buttonID, fields):
    print("onButtonChange, id: {}, fields: {}".format(buttonID, fields))

def onScreenChange(id, fields):
    try:
        pass
    except Exception as ex:
        print("onScreenChange exception, type: {}, exception: {}".format(type(ex), ex.args))

def onConnectionChange(id, fields):
    connection = mc.find_one('nodeConnections', selector={"_id": id})
    buttons = mc.find('buttons', selector={"screensetId": connection["screensetId"]})

def mcConnected():
    print("Meteor client connected, logging in")
    mc.login("peter.claydon@continuumbridge.com", "Mucht00f@r", callback=mcCheck)

def mcLoggedIn(data):
    print("Logged in, subscribing")
    try:
        mc.subscribe("lists", callback=mcSubscribeCallback)
        mc.subscribe("buttons", callback=mcSubscribeCallback)
        mc.subscribe("screensets", callback=mcSubscribeCallback)
        mc.subscribe("organisations", callback=mcSubscribeCallback)
    except Exception as ex:
        print("mcLoggedIn. Already subscribed, exception type {}, exception: {}".format(type(ex), ex.args))

def mcFailed(collection, data):
    print("Failed: ")
    print(json.dumps(data, indent=4))

def mcClosed(code, reason):
    print("Closed, reason: " + str(reason))

def mcLoggingIn():
    print("Logging in")

def mcLoggedOut():
    print("Logged out")

def mcCheck(error, login):
    print("Meteor client check. Error: " + str(error) + ", login: " + str(login))

def mcSubscribed(subscription):
    pass
    #print("Meteor client subscribed: " + str(subscription))

def mcSubscribeCallback(error):
    if error != None:
        print("Meteor client subscribe error: " + str(error))

def mcInsertCallback(error, data):
    print("Inserted data: {}, error: {}".format(data, error))

def mcUpdateCallback(error, data):
    if error != None:
        print("Meteor client update error: " + str(error))
        print("Meteor client update data: " + str(data))

def mcAdded(collection, id, fields):
    pass

def mcChanged(collection, id, fields, cleared):
    pass

def mcRemoved(collection, id):
    print('* REMOVED {} {}'.format(collection, id))

def registerButton(params):
    status = ""
    print("registerButton, params: {}".format(params))
    organisation = mc.find_one('organisations', selector={"name": params["org"]})
    print("organisation: {}".format(organisation))
    if organisation == None:
        status += "organisation, "
    listName = mc.find_one('lists', selector={"name": params["list"]})
    print("list: {}".format(listName))
    if listName == None:
        status += "list name, "
    screenset = mc.find_one('screensets', selector={"name": params["screenset"]})
    print("screenset: {}".format(screenset))
    if screenSet == None:
        status += "screenset, "
    button = mc.find_one('buttons', selector={"id": params["id"]})
    if button == None:
        print("button {} does not exist".format(params["id"]))
        status = "button {} does not exist".format(params["id"])
        mc.insert("buttons", {
            "organisationId": organisation["_id"],
            "screensetId": screenset["_id"], 
            "listId": listName["_id"],
            "name": params["name"],
            "id": params["id"],
            "enabled": True,
            "listDefault": True
            #"createdAt": {
            #    "$date": "2017-11-17T17:55:47.704Z"
            #}
        }, callback=mcInsertCallback)
    else:
        print("button: {}".format(button))
    return

@app.route('/')
def index():
    return 'Flask is running!'

@app.route('/data')
def names():
    data = {"names": ["John", "Jacob", "Julie", "Jennifer"]}
    return jsonify(data)

@app.route('/api/v1.0/watson', methods=['POST'])
def doPost():
    if not request.json:
        abort(400)
    params = request.json
    print("Post request: {}".format(params))
    responseString = ""
    if not "id" in params:
        responseString += "id, "
    if not "name" in params:
        responseString += "name, "
    if not "screenset" in params:
        responseString += "screenset, "
    if not "org" in params:
        responseString += "org, "
    if not "list" in params:
        responseString += "list, "
    if responseString != "":
    	responseString = "Error: no " + responseString[:-2] + " in request. No action taken"
    else:
        responseString = "OK"
        registerButton(params)
    response = {"status": responseString}
    return jsonify(response), 201

if __name__ == '__main__':
    try:
        s = check_output(["git", "status"])
        if "master" in s:
            CONFIG_FILE = HOME + "/production.config"
        else:
            CONFIG_FILE = HOME + "/staging.config"
        print("Using config: {}".format(CONFIG_FILE))
        readConfig()
    except Exception as e:
        print("Problem setting config file: {}, {}".format(type(e), e.args))
        sys.exit()
    meteor_websocket = config["meteor_websocket"]
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
    mc.connect()
    #context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    #context.load_cert_chain('/home/ubuntu/bridge_admin/flask/cbclient.pem', '/home/ubuntu/bridge_admin/flask/cbclient.key')
    #app.run(host = '0.0.0.0', port=5005, ssl_context=context)
    #app.run(debug=True)
    app.run()
