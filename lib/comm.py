import re
import time

from ptyprocess import *

from config import SCRIPT_PATH, LOG_PATH

##### games.log #####
log = open(LOG_PATH, "r")

def log_read():
    log.seek(0, 2)
    while 1:
        line = log.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line

##### pty communication #####
proc = PtyProcessUnicode.spawn(SCRIPT_PATH)

def proc_write(command):
    #print("%%% Writing to proc: {}".format(command))
    proc.write("\n")
    proc.write("{}\r\n".format(command))

# Just in case
proc_write("\n")
