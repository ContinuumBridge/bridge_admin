
#import glob
import logging
import logging.handlers

LOG_FILENAME = 'rotate.log'

# Set up a specific logger with our desired output level
my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.DEBUG)

# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=20, backupCount=5)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)

my_logger.addHandler(handler)

#logging.basicConfig(filename=CB_LOGFILE,level=CB_LOGGING_LEVEL,format='%(asctime)s %(levelname)s: %(message)s')

# Log some messages
for i in range(20):
    my_logger.debug('i = %d' % i)

# See what files are created
#logfiles = glob.glob('%s*' % LOG_FILENAME)

#for filename in logfiles:
#    print(filename)
