# flasktest2.py
from flask import Flask, jsonify, request
import os
import sys
import json
import time
from subprocess import check_output
import ssl
from MeteorClient import MeteorClient
import datetime

buttonID                = ""
config                  = {}
mc = None
loginError		= None
HOME                    = os.getcwd()

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

def readConfig():
    try:
        global config
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except Exception as ex:
        print("Problem reading button_client.config, type: %s, exception: %s", str(type(ex)), str(ex.args))

def nicetime(timeStamp):
    localtime = time.localtime(timeStamp)
    milliseconds = '%03d' % int((timeStamp - int(timeStamp)) * 1000)
    now = time.strftime('%d-%m-%Y, %H:%M:%S', localtime)
    return now

def onButtonChange(buttonID, fields):
    print("onButtonChange, id: {}, fields: {}".format(buttonID, fields))

def mcConnected():
    print("{}: Meteor client connected".format(nicetime(time.time())))

def mcLoggedIn(data):
    pass
    """
    print("{}: Subscribing".format(nicetime(time.time())))
    try:
        mc.subscribe("buttons", callback=mcSubscribeCallback)
        mc.subscribe("screensets", callback=mcSubscribeCallback)
        mc.subscribe("organisations", callback=mcSubscribeCallback)
    	print("{}: Subscribied".format(nicetime(time.time())))
    except Exception as ex:
        print("mcLoggedIn. Already subscribed, exception type {}, exception: {}".format(type(ex), ex.args))
    """

def subscribe():
    try:
        mc.subscribe("lists", callback=mcSubscribeCallback)
        mc.subscribe("buttons", callback=mcSubscribeCallback)
        mc.subscribe("screensets", callback=mcSubscribeCallback)
        mc.subscribe("organisations", callback=mcSubscribeCallback)
    	print("{}: Subscribied".format(nicetime(time.time())))
        return True
    except Exception as ex:
        print("mcLoggedIn. Already subscribed, exception type {}, exception: {}".format(type(ex), ex.args))
        return  False

def unsubscribe():
    mc.unsubscribe('lists')
    mc.unsubscribe('buttons')
    mc.unsubscribe('screensets')
    mc.unsubscribe('organisations')
    print("{}: Unsubscribed".format(nicetime(time.time())))

def mcFailed(collection, data):
    print("Failed: ")
    print(json.dumps(data, indent=4))

def mcClosed(code, reason):
    print("{}: Closed, reason: {}".format(nicetime(time.time()), reason))

def mcLoggingIn():
    print("{}: Logging in".format(nicetime(time.time())))

def mcLoggedOut():
    print("{}: Logged out".format(nicetime(time.time())))

def mcLoginCheck(error, login):
    global loginError
    loginError = error
    print("{}: mcLoginCheck. Error: {}, login: {}".format(nicetime(time.time()), error, login))

def mcSubscribed(subscription):
    print("{}: Subscribed: ".format(subscription))

def mcSubscribeCallback(error):
    if error != None:
        print("{}: Meteor client subscribe error: {}".format(nicetime(time.time()), error))

def mcInsertCallback(error, data):
    if error:
        print("{}: Insert error,  data: {}, error: {}".format(nicetime(time.time()), data, error))

def mcUpdateCallback(error, data):
    if error != None:
        print("{}: Update error: {}".format(nicetime(time.time()), error))
        print("{}: Update error data: {}".format(nicetime(time.time()), data))

def mcRemoveCallback(error, data):
    if error != None:
        print("{}: Update error: {}".format(nicetime(time.time()), error))
        print("{}: Update error data: {}".format(nicetime(time.time()), data))

def mcAdded(collection, id, fields):
    pass

def mcChanged(collection, id, fields, cleared):
    pass

def mcRemoved(collection, id):
    pass
    #print('* REMOVED {} {}'.format(collection, id))

def checkAuthorised(params):
    global loginError
    loginError = None
    mc.login(params["user"], params["password"], callback=mcLoginCheck)
    time.sleep(1)
    print("{}: loginError: {}".format(nicetime(time.time()), loginError))
    if loginError:
        status = "Login error: {}".format(loginError)
        return (status, None)
    time.sleep(0.2)
    buttons = mc.find('buttons')
    print("{}: buttons with user login: {}".format(nicetime(time.time()), buttons))
    users = mc.find('users')
    print("{}: user with user login: {}".format(nicetime(time.time()), users))
    if users[0]["emails"][0]["address"] != params["user"]:
        print("{}: wrong user: {}".format(nicetime(time.time()), params["user"]))
        status = "Error, user not authorised"
        return (status, None)
    orgs = mc.find('organisations')
    print("{}: orgs with user login: {}".format(nicetime(time.time()), orgs))
    org = orgs[0]["name"]
    if orgs[0]["name"] != params["org"]:
        print("{}: Unauthorised organisation: {}".format(nicetime(time.time()), params["org"]))
        status = "Error, user not in organisation"
        return (status, None)
    mc.logout()
    time.sleep(0.5)
    return (None, org)

def registerButton(params):
    global loginError
    loginError = None
    status = ""
    print("{}: registerButton, params: {}".format(nicetime(time.time()), params))
    status, org =  checkAuthorised(params)
    if status:
        return status
    mc.login("peter.claydon@continuumbridge.com",  "Mucht00f@r", callback=mcLoginCheck)
    time.sleep(1)
    mc.login(params["user"], params["password"], callback=mcLoginCheck)
    time.sleep(1)
    print("{}: loginError: {}".format(nicetime(time.time()), loginError))
    if loginError:
        status = "Login error: {}".format(loginError)
        return status
    mc.logout()
    time.sleep(0.5)
    mc.login("peter.claydon@continuumbridge.com",  "Mucht00f@r", callback=mcLoginCheck)
    time.sleep(1)
    print("{}: loginError 2: {}".format(nicetime(time.time()), loginError))
    if loginError:
        status = "Authorization problem"
        return status
    time.sleep(1)
    organisation = mc.find_one('organisations', selector={"name": params["org"]})
    print("{}: organisation: {}".format(nicetime(time.time()), organisation))
    if organisation == None:
        status += "organisation, "
    listName = mc.find_one('lists', selector={"name": params["list"]})
    print("{}: list: {}".format(nicetime(time.time()), listName))
    if listName == None:
        status += "list name, "
    screenset = mc.find_one('screensets', selector={"name": params["screenset"]})
    print("{}: screenset: {}".format(nicetime(time.time()), screenset))
    if screenset == None:
        status += "screenset, "
    print("{}: status: {}".format(nicetime(time.time()), status))
    if status:
    	status = "Error with " + status[:-2] + " . No action taken"
        return status
    button = mc.find_one('buttons', selector={"id": params["id"]})
    print("{}: registerButton, find_one, button: {}".format(nicetime(time.time()), button))
    if button == None:
        print("{}: button {} does not exist, creating".format(nicetime(time.time()), params["id"]))
        status = "button {} does not exist".format(params["id"])
        mc.insert("buttons", {
            #"organisationId": organisation["_id"],
            "screensetId": screenset["_id"], 
            "listId": listName["_id"],
            "name": params["name"],
            "id": params["id"],
            "enabled": False,
            "listDefault": True,
            "createdAt": datetime.datetime.utcnow() 
        }, callback=mcInsertCallback)
        status = "OK - Created new button"
    else:
        print("{}: Button exists, updating: {}".format(nicetime(time.time()), button))
        mc.update("buttons", {"_id": button["_id"]}, \
            {"$set": {
                #"organisationId": organisation["_id"],
                "screensetId": screenset["_id"], 
                "listId": listName["_id"],
                "name": params["name"],
                "id": params["id"],
                "enabled": False,
                "listDefault": True
            }}, callback=mcUpdateCallback)
        status = "OK - Updated existing button"
    return status

def deleteButton(params):
    global loginError
    loginError = None
    status = ""
    print("{}: deleteButton, params: {}".format(nicetime(time.time()), params))
    status, org =  checkAuthorised(params)
    print("{}: deleteButton authorised org: {}".format(nicetime(time.time()), org))
    if status:
        return status
    mc.login("peter.claydon@continuumbridge.com",  "Mucht00f@r", callback=mcLoginCheck)
    time.sleep(1)
    print("{}: loginError 2: {}".format(nicetime(time.time()), loginError))
    if loginError:
        status = "Authorization problem"
        return status
    time.sleep(1)
    button = mc.find_one('buttons', selector={"id": params["id"]})
    print("{}: button {}".format(nicetime(time.time()), button))
    if button == None:
        print("{}: button {} does not exist, unable to delete".format(nicetime(time.time()), params["id"]))
        status = "Button {} does not exist, unable to delete".format(params["id"])
        return status
    else:
        listName = mc.find_one('lists', selector={"_id": button["listId"]})
        print("{}: list: {}".format(nicetime(time.time()), listName))
        buttonOrg = mc.find_one('organisations', selector={"_id": listName["organisationId"]})
        print("{}: org: {}".format(nicetime(time.time()), buttonOrg["name"]))
        if buttonOrg["name"] != org:
            status = "Error, the button does not belong to your organisation"
            return status
        mc.remove('buttons', selector={"_id": button["_id"]}, callback=mcRemoveCallback)
        print("{}: removed button {}".format(nicetime(time.time()), params["id"]))
        status = "OK - Removed button"
    return status


@app.route('/api/watson/v1.0', methods=['POST'])
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
    if not "user" in params:
        responseString += "user, "
    if not "password" in params:
        responseString += "password, "
    print("{}: responseString: {}".format(nicetime(time.time()), responseString))
    if responseString != "":
    	responseString = "Error: no " + responseString[:-2] + " in request. No action taken"
    else:
        responseString = registerButton(params)
    time.sleep(1)
    mc.logout()
    response = {"status": responseString}
    return jsonify(response), 201

@app.route('/api/watson/v1.0', methods=['DELETE'])
def doDelete():
    if not request.json:
        abort(400)
    params = request.json
    print("Post request: {}".format(params))
    responseString = ""
    if not "id" in params:
        responseString += "id, "
    if not "user" in params:
        responseString += "user, "
    if not "password" in params:
        responseString += "password, "
    print("{}: responseString: {}".format(nicetime(time.time()), responseString))
    if responseString != "":
    	responseString = "Error: no " + responseString[:-2] + " in request. No action taken"
    else:
        responseString = deleteButton(params)
    time.sleep(1)
    mc.logout()
    response = {"status": responseString}
    return jsonify(response), 201

    responseString = ""
if __name__ == '__main__':
    try:
        s = check_output(["git", "status"])
        if "master" in s:
            CONFIG_FILE = HOME + "/production.config"
        else:
            CONFIG_FILE = HOME + "/staging.config"
        print("{}: Using config: {}".format(nicetime(time.time()), CONFIG_FILE))
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
    print("{}: Connecting".format(nicetime(time.time())))
    mc.connect()
    subscribe()
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('/home/petec/bridge_admin/flask/cbclient.pem', '/home/petec/bridge_admin/flask/cbclient.key')
    app.run(host = '0.0.0.0', port=5005, ssl_context=context)
    app.run()
