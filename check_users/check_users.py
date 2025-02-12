#!/usr/bin/env python
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#
"""
The cb command allows a user to create and modify bridges, app and devices.
"""

THISBRIDGE = "/opt/cbridge/thisbridge/thisbridge.sh"
ADDRESS = "http://portal.continuumbridge.com/"
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import json
import time
import sys
import click
from os import rename
from os.path import expanduser

def login(user, password):
    print "Logging in"
    url = ADDRESS + "/api/user/v1/user_auth/login/"
    headers = {'Content-Type': 'application/json'}
    data = {
            "email": user,
            "password": password
           }
    r = requests.post(url, data=json.dumps(data), headers=headers)
    if r.status_code == 200:
        sessionid = r.cookies['sessionid']
    else:
        print "Could not log in, get: ", r.status_code, " Please check user name and password"
        exit()
    return sessionid

def logout(sessionid):
    print "Logging out"
    url = ADDRESS + "/api/user/v1/user_auth/logout/"
    data = {}
    headers = {'Content-Type': 'application/json'}
    cookies = {'sessionid': sessionid}
    r = requests.post(url, data=json.dumps(data), headers=headers, cookies=cookies)
    if r.status_code != 200:
        print "Problem logging out, get: ", r.status_code

def changeLine(key, value):
    tmpfile = "thisbridge.tmp"
    newline = "export " + key + "='" + value + "'\n"
    replaced = False
    with open(THISBRIDGE, "r") as fi:
        with open(tmpfile, "w") as fo:
            for line in fi:
                if line[0] != "#":
                    if key in line:
                        line = newline
                        replaced = True
                    fo.write(line)
            if not replaced:
                fo.write(newline)
    rename(tmpfile, THISBRIDGE)

def keyExists(key):
    found = False
    with open(THISBRIDGE, "r") as fi:
        for line in fi:
            if line[0] != "#":
                if key in line:
                    found = True
                    break
    return found

def getBridgeEnv(key):
    with open(THISBRIDGE, "r") as fi:
        for line in fi:
            if key in line:
                key, value = line.split("=", 1)
                val = value.replace('"', '')
                value = val.replace("'", "")
                break
    return value

def checkConfig(config, keys):
    data = {}
    for key in keys:
        if key not in config:
            print "Error. No", key, "found in config file"
            exit()
        else:
            data[key] = config[key]
    return data

def loadJSON(fileName):
    try:
        with open(fileName, 'r') as f:
            config = json.load(f)
            print "Read file:", fileName
            return config
    except Exception as inst:
        print "Error. Failed to load file:", fileName
        print "Exception type:", type(inst)
        print "Exception args:", str(inst.args)
        exit()

def checkget(get, expected, action, obj, sessionid, doExit):
     if get != expected:
         print "Failed to", action, obj, "get code:", get
         if doExit:
             logout(sessionid)
             exit()

@click.command()
@click.option('--bridge', nargs=1, help='Options: post|patch|get.')
@click.option('--name', nargs=1, help='The name to give a bridge.')
@click.option('--app', nargs=2, help='Usage: post|patch|get|delete <config file name>.')
@click.option('--device', nargs=2, help='Usage: post|patch|get|delete <config file name>.')
@click.option('--staging', nargs=1, help='Options: True|False.')
@click.option('--user', prompt='User name', help='Username. If not specified a prompt will be given.')
@click.option('--password', prompt=True, hide_input=True, help='Password. If not specified a prompt will be given.')

def cb(bridge, app, device, user, staging, password, name):

    global ADDRESS
    if bridge:
        if not user or not password:
            print "Usage: cb --bridge [post|rm] --user <user_name> --password <password>"
            exit()
    if app:
        if not user or not password:
            print "Usage: cb --app [post|patch|rm] --user <user_name> --password <password>"
            exit()
    if device:
        if not user or not password:
            print "Usage: cb --device [post|patch|rm] --user <user_name> --password <password>"
            exit()
    if staging:
        ADDRESS = "http://staging.continuumbridge.com/"
    if bridge:
        action = bridge
        if action == "post" or action == "patch":
            if name:
                data = {"name": name}
            else:
                data = {}
        elif action == "get":
            data = {}
        else:
            print "Unrecognised action:", action
            exit()
        sessionid = login(user, password) 
        print "Bridge:", action
        headers = {'Content-Type': 'application/json'}
        cookies = {'sessionid': sessionid}
        if action == "post":
            if keyExists("CB_BRIDGE_KEY"):
                print "Bridge already initialised. Command ignored"
                exit()
            else:
                url = ADDRESS + "/api/bridge/v1/bridge/"
                r = requests.post(url, data=json.dumps(data), headers=headers, cookies=cookies)
                checkget(r.status_code, 201, action, "bridge", sessionid, True)
                content = json.loads(r.content)
                changeLine("CB_BRIDGE_KEY", content["key"])
                changeLine("CB_BRIDGE_URI", content["resource_uri"])
                changeLine("CB_BRIDGE_NAME", content["name"])
                changeLine("CB_BID", content["cbid"])
                print "Created new bridge, ID:", content["cbid"]
        elif action == "patch":
            url = ADDRESS + getBridgeEnv("CB_BRIDGE_URI")
            r = requests.patch(url, data=json.dumps(data), headers=headers, cookies=cookies)
            checkget(r.status_code, 202, action, "bridge", sessionid, True)
            content = json.loads(r.content)
            changeLine("CB_BRIDGE_NAME", content["name"])
        elif action == "get":
            url = ADDRESS + getBridgeEnv("CB_BRIDGE_URI")
            r = requests.get(url, data=json.dumps(data), headers=headers, cookies=cookies)
            checkget(r.status_code, 200, action, "bridge", sessionid, True)
            text = json.loads(r.text)
            print(json.dumps(text, indent=4))
        logout(sessionid)

    if app:
        action = app[0]
        configFile = app[1]
        config = loadJSON(configFile)
        if action == "post":
            appData = checkConfig(config, ['description', 'exe', 'name', 'provider', 'url', 'version'])
            if "app_resource" in config:
                print "App already exists. Use cb --app patch to modify."
                exit()
        elif action == "patch":
            appData = checkConfig(config, ['description', 'exe', 'name', 'provider', 'url', 'version', 'app_resource'])
        elif action == "delete" or action == "get":
            appData = checkConfig(config, ['app_resource'])
        else:
            print "Unrecognised action:", action
            exit()
        sessionid = login(user, password) 
        print "App:", action
        data = appData
        headers = {'Content-Type': 'application/json'}
        cookies = {'sessionid': sessionid}
        if action == "post":
            url = ADDRESS + "/api/bridge/v1/app/"
            r = requests.post(url, data=json.dumps(data), headers=headers, cookies=cookies)
            checkget(r.status_code, 201, action, "app", sessionid, True)
        elif action == "patch":
            url = ADDRESS + config["app_resource"]
            r = requests.patch(url, data=json.dumps(data), headers=headers, cookies=cookies)
            checkget(r.status_code, 202, action, "app", sessionid, True)
        elif action == "get":
            url = ADDRESS + config["app_resource"]
            r = requests.get(url, data=json.dumps(data), headers=headers, cookies=cookies)
            checkget(r.status_code, 200, action, "app", sessionid, True)
            text = json.loads(r.text)
            print(json.dumps(text, indent=4))
        elif action == "delete":
            url = ADDRESS + config["app_resource"]
            r = requests.delete(url, data=json.dumps(data), headers=headers, cookies=cookies)
            checkget(r.status_code, 204, action, "app", sessionid, True)
        if action == "post" or action == "patch":
            text = json.loads(r.text)
            if "resource_uri" in text:
                app_resource = text["resource_uri"]
            else:
                print "No app resouce_uri returned by server"
                logout(sessionid)
                exit()
        # patch config file with resource URLs
        if action == "post" or action == "patch":
            config["app_resource"] = app_resource
        elif action == "delete":
            del config["app_resource"]
        try:
            with open(configFile, 'w') as f:
                f.write(json.dumps(config, indent=4))
        except Exception as inst:
            print "Error. Failed to patch config file"
            print "Exception type: ", type(inst)
            print "Exception args: ", str(inst.args)
        logout(sessionid)

    if device:
        action = device[0]
        configFile = device[1]
        config = loadJSON(configFile)
        if action == "post":
            deviceData = checkConfig(config, ['description', 'name', 'protocol'])
            if "device_resource" in config:
                print "Device already exists. Use cb --device patch to modify."
                exit()
            adaptorData = checkConfig(config, ['description', 'exe', 'name', 'provider', 'url', 'version', 'protocol'])
        elif action == "patch":
            deviceData = checkConfig(config, ['description', 'name', 'protocol', 'device_resource'])
            adaptorData = checkConfig(config, ['description', 'exe', 'name', 'provider', 'url', 'version', \
                                               'protocol', 'adaptor_resource'])
        elif action == "delete":
            deviceData = checkConfig(config, ['device_resource'])
            adaptorData = checkConfig(config, ['adaptor_resource'])
        elif action == "get":
            deviceData = checkConfig(config, ['device_resource'])
        else:
            print "Unrecognised action:", action
            exit()
        sessionid = login(user, password) 
 
        print "Device", action
        data = deviceData
        headers = {'Content-Type': 'application/json'}
        cookies = {'sessionid': sessionid}
        if action == "post":
            url = ADDRESS + "/api/bridge/v1/device/"
            r = requests.post(url, data=json.dumps(data), headers=headers, cookies=cookies)
            checkget(r.status_code, 201, action, "device", sessionid, True)
        elif action == "patch":
            url = ADDRESS + config["device_resource"]
            r = requests.patch(url, data=json.dumps(data), headers=headers, cookies=cookies)
            checkget(r.status_code, 202, action, "device", sessionid, True)
        elif action == "get":
            url = ADDRESS + config["device_resource"]
            r = requests.get(url, data=json.dumps(data), headers=headers, cookies=cookies)
            checkget(r.status_code, 200, action, "device", sessionid, True)
            text = json.loads(r.text)
            print(json.dumps(text, indent=4))
            exit()
        elif action == "delete":
            url = ADDRESS + config["device_resource"]
            r = requests.delete(url, data=json.dumps(data), headers=headers, cookies=cookies)
            checkget(r.status_code, 204, action, "device", sessionid, False)
        if action == "post" or action == "patch":
            text = json.loads(r.text)
            if "resource_uri" in text:
                device_resource = text["resource_uri"]
            else:
                print "No device resouce_uri returned by server"
                logout(sessionid)
                exit()

        print "Adaptor", action
        data = adaptorData
        if action == "post":
            url = ADDRESS + "/api/bridge/v1/adaptor/"
            r = requests.post(url, data=json.dumps(data), headers=headers, cookies=cookies)
            checkget(r.status_code, 201, action, "adaptor", sessionid, True)
        elif action == "patch":
            url = ADDRESS + config["adaptor_resource"]
            r = requests.patch(url, data=json.dumps(data), headers=headers, cookies=cookies)
            checkget(r.status_code, 202, action, "adaptor", sessionid, True)
        elif action == "delete":
            url = ADDRESS + config["adaptor_resource"]
            r = requests.delete(url, data=json.dumps(data), headers=headers, cookies=cookies)
            checkget(r.status_code, 204, action, "adaptor", sessionid, False)
        #print "get:    ", r.status_code
        #print "text:      ", r.text
        #print "headers:   ", r.headers
        #print "content:   ", r.content
        #print "cookies:   ", r.cookies
        if action == "post" or action == "patch":
            text = json.loads(r.text)
            if "resource_uri" in text:
                adaptor_resource = text["resource_uri"]
            else:
                print "No adaptor resource_url returned by server"
                logout(sessionid)
                exit()

        if action == "post":
            print "Creating adaptor_compatibility"
            url = ADDRESS + "/api/bridge/v1/adaptor_compatibility/"
            data = {"device": device_resource,
                    "adaptor": adaptor_resource}
            r = requests.post(url, data=json.dumps(data), headers=headers, cookies=cookies)
            checkget(r.status_code, 201, action, "adaptor_compatibility", sessionid, True)

        # patch config file with resource URLs
        if action == "post" or action == "patch":
            config["device_resource"] = device_resource
            config["adaptor_resource"] = adaptor_resource
        elif action == "delete":
            del config["device_resource"]
            del config["adaptor_resource"]
        try:
            with open(configFile, 'w') as f:
                f.write(json.dumps(config, indent=4))
        except Exception as inst:
            print "Error. Failed to patch config file"
            print "Exception type: ", type(inst)
            print "Exception args: ", str(inst.args)
        logout(sessionid)

if __name__ == '__main__':
    cb()

