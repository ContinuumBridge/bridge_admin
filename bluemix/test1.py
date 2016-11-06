import ibmiotf.application
import time
import json

def myEventCallback(myEvent):
    print("Event callback")

try:
    options = {
      "org": "mflu13",
      "id": "spur_client",
      "auth-method": "apikey",
      "auth-key": "a-mflu13-luqbrwyus4",
      "auth-token": "De36lQRygM3-p)L@f@"
    }
    client = ibmiotf.application.Client(options)
    print("Client created\n")
except ibmiotf.ConnectionException  as e:
    print("Client creation exception: {}\n".format(e))

try:
    client.api.deleteDevice("spur", "17")
    print("Devce 17 deleted\n")
except Exception as e:
    print("Error deleting device 17: {}\n".format(e.message))

try:
    success = client.api.deleteDeviceType("myDeviceType")
    print("Device tyoe deleted\n")
except Exception as e:
    print("Error deleting device type: {}\n".format(e.message))

info = {
    "serialNumber": "0",
    "manufacturer": "ContinuumBridge",
    "descriptiveLocation": "Unknown"
}
meta = {
    "state": "0",
    "customField2": "customValue2"
}
try:
    deviceType = client.api.addDeviceType("Spur", description="Spur Button", deviceInfo=info, metadata=meta)
    print("deviceType added\n")
except Exception as e:
    print("Error adding device type: {}\n".format(e.message))

try:
    updatedDeviceTypeInfo = client.api.updateDeviceType("spur", description="Spur Button", deviceInfo=info, metadata=meta)
    print("Updated device type info\n")
except Exception as e:
    print("Error updating device type info: {}\n".format(e.message))

deviceTypeInfo = client.api.getDeviceType("spur")
print("deviceTypeInfo: {}".format(deviceTypeInfo))

deviceTypeId="spur"
deviceId = "17"
metadata = {"customField1": "Bonzo", "customField2": "Dog"}
deviceInfo = {"serialNumber": "17"}

try:
    client.api.registerDevice(deviceTypeId, deviceId=deviceId)
    print("Device added\n")
except Exception as e:
    print("Error registering device: {}\n".format(e.message))

try:
   #devices = client.api.getAllDevices({'typeId' : deviceTypeId})
   device = client.api.getDevice(deviceTypeId, deviceId)
   print("Retrieved device: {}\n".format(device))
except Exception as e:
    print("Error retrieving devices, message: {} ".format(e.message))

"""
client.deviceEventCallback = myEventCallback
try:
    client.subscribeToDeviceEvents()
    print("Subscribed to all device events\n")
except Exception as e:
    print("Error subscribing to all device events: {}\n".format(e.message))

time.sleep(30)

status = { "alert": { "enabled": True } }
meta = {"state": "1"}
try:
    client.api.updateDevice(deviceTypeId, deviceId, metadata=meta, status=status)
    print("Updated device\n")
except Exception as e:
    print("Error updating device: {}\n".format(e.message))

try:
   device = client.api.getDevice(deviceTypeId, deviceId)
   print("Retrieved device after update: {}\n".format(device))
except Exception as e:
    print("Error retrieving devices, message: {} ".format(e.message))

time.sleep(30)

status = { "alert": { "enabled": True } }
meta = {"state": "2"}
try:
    client.api.updateDevice(deviceTypeId, deviceId, metadata=meta, status=status)
    print("Updated device\n")
except Exception as e:
    print("Error updating device: {}\n".format(e.message))

try:
   device = client.api.getDevice(deviceTypeId, deviceId)
   print("Retrieved device after update: {}\n".format(device))
except Exception as e:
    print("Error retrieving devices, message: {} ".format(e.message))
"""

myData={'state' : '3'}
print("Publishing event")
client.publishEvent(deviceTypeId, deviceId, "status", "json", json.dumps(myData))
print("Publisted state event from device\n")


