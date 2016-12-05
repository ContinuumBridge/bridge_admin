import ibmiotf.application
import time
import json

# Token for device 18: v6lAREIwY6P_J@qAtL
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

deviceTypeId="spur"
deviceId = "19"
status = { "alert": { "enabled": True } }
meta = {"state": "0"}
try:
    client.api.updateDevice(deviceTypeId, deviceId, metadata=meta, status=status)
    print("Updated device\n")
except Exception as e:
    print("Error updating device: {}\n".format(e.message))

t = 0
value = "off"
while t < 20:
    if value == "off":
        number = 1
        value = "on"
    else:
        number = 0
        value = "off"
    myData={'pushed' : value, "number": number}
    try:
        print("Publishing event")
        client.publishEventOverHTTP(deviceTypeId, deviceId, "status", myData)
        #client.publishEvent(deviceTypeId, deviceId, "status", "json", myData)
        print("Publisted state event from device\n")
    except Exception as e:
        print("Erro publishing event: {}\n".format(e))
    t += 1
    time.sleep(10)

