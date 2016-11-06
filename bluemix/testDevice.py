import ibmiotf.device
import time
import json

# Token for device 18: v6lAREIwY6P_J@qAtL
# Token for device 25: *I*ew-!wQknTnrD1Ea
try:
    options = {
      "org": "u4gtq9",
      "type": "brexit",
      "id": "25",
      "auth-method": "token",
      "auth-token": "*I*ew-!wQknTnrD1Ea"
    }
    client = ibmiotf.device.Client(options)
    print("Device created\n")
except ibmiotf.ConnectionException  as e:
    print("Device creation exception: {}\n".format(e))

client.connect()

leave = 0
remain = 0
t = 0
while t < 20:
    data = {"leave": leave, "remain": remain}
    try:
        print("Publishing event")
        client.publishEvent("status", "json", data)
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
