import serial

port = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=3.0)

rcv = port.read(10)
print "Read"
port.write("ER_CMD#U?")
print "Parameter written"
rcv = port.read(10)
print "Received: ", rcv
