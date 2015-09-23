import time
import serial
import thread

exitflag = 0

def listen(name,timeout):
    global exitflag
    listen_txt = ''
    exitflag = 0
    while True:
        while ser.inWaiting()>0:
            time.sleep(0.005)
            listen_txt += ser.read(1)
        if listen_txt !='':
            print listen_txt
            listen_txt = ''
        if (exitflag == 1):
            exitflag = 0
            thread.exit()
        
            
            
# end of listen thread function
        
# configure the serial connections (the parameters differs on the device you are connecting to)
ser = serial.Serial(
    port='/dev/ttyUSB1',       # Either something COM1 for Windows or /dev/ttyUSB0 fir Linux/RasPi
    baudrate= 19200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout = 0.5
)


print('.................................\n')
print('... LPRS easyRadio Connect2Pi ...\n')
print('.................................\n')

print('Please enter your commands below. Text other than a command will be transmitted.\r\nType "exit" to leave the application.')

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
