import time
import serial
from twisted.internet import threads
from twisted.internet import reactor, defer

exitflag = 0

class Adaptor:
    def __init__(self):
        self.stop = False
        self.ser = serial.Serial(
            port='/dev/ttyUSB0',
            baudrate= 19200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout = 0.5
        )
        reactor.callInThread(self.listen)

    def setState(self, action):
        #self.cbLog("debug", "setting state to: " + action)
        # error is only ever set from the running state, so set back to running if error is cleared
        if action == "error":
            self.state == "error"
        elif action == "clear_error":
            self.state = "running"
        else:
            self.state = action
        msg = {"id": self.id,
               "status": "state",
               "state": self.state}
        self.sendManagerMessage(msg)

    def sendCharacteristic(self, characteristic, data, timeStamp):
        msg = {"id": self.id,
               "content": "characteristic",
               "characteristic": characteristic,
               "data": data,
               "timeStamp": timeStamp}
        for a in self.apps[characteristic]:
            self.sendMessage(msg, a)

    def listen(self):
        global exitflag
        listen_txt = ''
        exitflag = 0
        while not self.doStop:
            while ser.inWaiting()>0 and not self.doStop:
                time.sleep(0.005)
                listen_txt += ser.read(1)
            if not self.doStop:
                if listen_txt !='':
                    self.cbLog("debug",  listen_txt)
                    listen_txt = ''

input=1

exitflag = 0
thread.start_new_thread( listen ,("Listen",2,))


while 1 :
    # get keyboard input
    input = raw_input(">>")
        # Python 3 users
    #input = input(">> ")
    if input == 'flush':
        numbytes = ser.inWaiting()
        out = ''
        if numbytes>0:
            out = ser.read(numbytes)
            if out != '':
                print(out)
        else:
            print("Nothing in Buffer")
    if input == 'exit':
        ser.close()
        print("exiting...")
        exitflag = 1
        while exitflag > 0:
            time.sleep(0.5)
        exit()
    else:
        # send the character to the device
        # (note that I happend a \r\n carriage return and line feed to the characters - this is requested by my device)
        ser.write(input)

        out = ''

        out += ser.read(1)
        time.sleep(0.005)
        while ser.inWaiting() > 0:
            time.sleep(0.005)
            out += ser.read(1)
                 
        if out != '':
            if input == out:
                time.sleep(0.05)
                ser.write("ACK")
#                while ser.outWaiting()>0:
#                    pass

 #               print(input + "\nSending ACK...")
                #time.sleep(2)
                out = ''
                out += ser.read(1)
                time.sleep(0.005)
                if ser.inWaiting() == 0:
                    print("Nothing to read")
                while ser.inWaiting() > 0:
                    time.sleep(0.01)
                    out += ser.read(1)
                if out != '':
                    print(">>" + out)
            else:
                print(">>" + out)

if __name__ == '__main__':
    Adaptor()
