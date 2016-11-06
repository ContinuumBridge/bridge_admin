import ibmiotf.application
import ibmiotf.device
import time
import json

def myEventCallback(myEvent):
    print("Event callback")

try:
    options = {
      "org": "u4gtq9",
      "id": "spur_client",
      "auth-method": "apikey",
      "auth-key": "a-u4gtq9-dg0170lg1x",
      "auth-token": "ujVE9&g@hEBBDhoNfo"
    }
    client = ibmiotf.application.Client(options)
    print("Client created\n")
except ibmiotf.ConnectionException  as e:
    print("Client creation exception: {}\n".format(e))

#creating deviceId: BuildingA-Room1, deviceTypeId: Rate, deviceInfo: {'Description': u'Building A - Room 1'}

deviceTypeId="Rate"
deviceId = "BuildingA-Room1"
#deviceInfo = {"serialNumber": "26"}
deviceInfo = {"description": "Building A - Room 1"}

try:
    resp = client.api.registerDevice(deviceTypeId, deviceId=deviceId, deviceInfo=deviceInfo)
    print("Device added: {}\n".format(resp))
except Exception as e:
    print("Error registering device: {}\n".format(e.message))

authToken = resp["authToken"]
print("authToken: {}".format(authToken))
try:
   device = client.api.getDevice(deviceTypeId, deviceId)
   print("Retrieved device: {}\n".format(device))
except Exception as e:
    print("Error retrieving devices, message: {} ".format(e.message))

try:
    options = {
      "org": "u4gtq9",
      "type": deviceTypeId,
      "id": deviceId,
      "auth-method": "token",
      "auth-token": authToken
    }
    device = ibmiotf.device.Client(options)
    print("Device created\n")
except ibmiotf.ConnectionException  as e:
    print("Device creation exception: {}\n".format(e))

device.connect()

leave = 0
remain = 0
t = 0
while t < 20:
    data = {"leave": leave, "remain": remain}
    try:
        print("Publishing event")
        device.publishEvent("status", "json", data)
        print("Publisted state event from device\n")
    except Exception as e:
        print("Erro publishing event: {}\n".format(e))
    t += 1
    if t%4:
        leave += 1
    else:
        remain += 1
    time.sleep(10)

while True:
    time.sleep(1)


#    {"org": "u4gtq9", "id": "spur_client", "apikey", "auth-key": "a-u4gtq9-dg0170lg1x", "auth-token": "ujVE9&g@hEBBDhoNfo"}
#    {"org": "u4gtq9", "auth-key": "a-u4gtq9-dg0170lg1x", "auth-token": "ujVE9&g@hEBBDhoNfo"}
