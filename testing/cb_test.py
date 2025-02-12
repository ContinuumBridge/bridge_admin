#!/usr/bin/env python
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#
"""
The cb command allows a user to create and modify bridges, app and adaptors.
Eg:
cb --bridge init
cb --bridge init --user me@myself.com --password mypassword
cb --app init config.json

"""
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import json
import time
import sys
import click

def login(user, password):
    print "Logging in"
    url = "http://54.72.38.223/api/user/v1/user_auth/login/"
    headers = {'Content-Type': 'application/json'}
    data = {
            "email": user,
            "password": password
           }
    r = requests.post(url, data=json.dumps(data), headers=headers)
    print "status:    ", r.status_code
    if r.status_code == 200:
        sessionid = r.cookies['sessionid']
    else:
        sessionid = ""
    return sessionid

def logout(sessionid):
    print "Logging out"
    url = "http://54.72.38.223/api/user/v1/user_auth/logout/"
    data = {}
    headers = {'Content-Type': 'application/json'}
    cookies = {'sessionid': sessionid}
    r = requests.post(url, data=json.dumps(data), headers=headers, cookies=cookies)
    print "status:    ", r.status_code

@click.command()
@click.option('--bridge', nargs=1, help='options: init, rm')
@click.option('--app', nargs=2, help='Usage: init|rm|mod <config file name>')
@click.option('--adaptor', nargs=2, help='Two options: init|rm|mod <config file name>')
@click.option('--user', prompt='User name', help='Username')
@click.option('--password', prompt=True, hide_input=True, help='Password. If not specified a prompt will be given')

def cb(bridge, app, adaptor, user, password):
    print "bridge:    ", bridge
    print "app:       ", app
    #print "app:       ", app[0], app[1]
    print "adaptor:   ", adaptor
    print "user:      ", user
    print "password:  ", password

    if bridge == "init":
        sessionid = login(user, password) 
        if sessionid:
            print "Creating bridge"
            url = "http://54.72.38.223/api/bridge/v1/bridge/"
            data = {"name": "myname"}
            headers = {'Content-Type': 'application/json'}
            cookies = {'sessionid': sessionid}
            r = requests.post(url, data=json.dumps(data), headers=headers, cookies=cookies)
            print "status:    ", r.status_code
            print "text:      ", r.text
            print "headers:   ", r.headers
            print "content:   ", r.content
        else:
            print "Unable to create bridge"
        logout(sessionid)
    elif app[0]  == "init":
        configFile = app[1]
        try:
            with open(configFile, 'r') as configFile:
                config = json.load(configFile)
                configRead = True
                print "Read file: ", configFile
        except:
            print "No config file exists or file is corrupt: ", configFile
            success= False
        if 'description' not in config:
            print "No description found in file: ", configFile
            exit()
        elif 'exe' not in config:
            print "No exe found in file: ", configFile
            exit()
        elif 'name' not in config:
            print "No name found in file: ", configFile
            exit()
        elif 'provider' not in config:
            print "No provider found in file: ", configFile
            exit()
        elif 'url' not in config:
            print "No url found in file: ", configFile
            exit()
        elif 'version' not in config:
            print "No version found in file: ", configFile
            exit()
        else:
            print "Config OK"
        appConfig = {}
        appConfig['description'] = config['description']
        appConfig['exe'] = config['exe']
        appConfig['name'] = config['name']
        appConfig['provider'] = config['provider']
        appConfig['url'] = config['url']
        appConfig['version'] = config['version']
        sessionid = login(user, password) 
 
        print "Creating app"
        url = "http://54.72.38.223//api/bridge/v1/app/"
        data = appConfig
        headers = {'Content-Type': 'application/json'}
        cookies = {'sessionid': sessionid}
        r = requests.post(url, data=json.dumps(data), headers=headers, cookies=cookies)
        print "status:    ", r.status_code
        print "text:      ", r.text
        print "headers:   ", r.headers
        print "content:   ", r.content
        print "cookies:   ", r.cookies

        logout(sessionid)
        print "Logging out"
    elif app[0]  == "rm":
        pass

if __name__ == '__main__':
    cb()

