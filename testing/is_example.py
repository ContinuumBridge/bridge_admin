
#####
# This is a custom 'getting started' script, made with care for peter.claydon@continuumbridge.com.
# If you have any questions, please email us! support@initialstate.com
#####

# Import the ISStreamer module
from ISStreamer.Streamer import Streamer
# Import time for delays
import time

# Streamer constructor, this will create a bucket called Python Stream Example
# you'll be able to see this name in your list of logs on initialstate.com
# your access_key is a secret and is specific to you, don't share it!
streamer = Streamer(bucket_name="Python Stream Example", bucket_key="python_example", access_key="pXawt1V4L7P2kmHKlndrNJd6lfB5H3Oc")

# example data logging
streamer.log("My Messages", "Stream Starting")
for num in range(1, 10):
    time.sleep(0.1)
    streamer.log("My Numbers", num)
    if num%2 == 0:
        streamer.log("My Booleans", False)
    else: 
        streamer.log("My Booleans", True)
    if num%3 == 0:
        streamer.log("My Events", "pop")
    if num%5 == 0:
        streamer.log("My Messages", "Stream Half Done")
    if num == 5:
        streamer.log("Printers/First Floor", "Low Ink")
    elif num == 7:
        streamer.log("Printers/First Floor", "OK")
    elif num == 0:
        streamer.log("Printers/First Floor", "OK")
    time.sleep(2)
    streamer.flush()
streamer.log("My Messages", "Stream Done")

## This is just an example, try something of your own!
##   ideas:
##     - solve world hunger, one bug fix at a time
##     - create the worlds first widget
##     - build an army of bug-free robot kittens


# Once you're finished, close the stream to properly dispose
streamer.close()
