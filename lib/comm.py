import socket
import time

from ptyprocess import *

from config import ADDRESS, PORT, PASSWORD, SCRIPT_PATH

##### rcon communication #####
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.connect((ADDRESS, PORT))
server_socket.settimeout(10)

def raw_command(cmd):
    time.sleep(0.5)
    message = b"\xff\xff\xff\xff" + ("%s\n" % cmd).encode("UTF-8")
    server_socket.send(message)
    return server_socket.recv(8096).replace(b"\xff\xff\xff\xff", b"").rstrip(b"\n")

def rcon(cmd):
    return raw_command("rcon {} {}".format(PASSWORD, cmd))

##### pty communication #####
proc = PtyProcessUnicode.spawn(SCRIPT_PATH)

# pty commands are later re-read as bot input
# Skip parsing if event line is in the pty_buffer

# Last read line in the main loop isn't always the last line written by the bot
# Keep some lines in the buffer in case this happens
pty_buffer = ["" for i in range(5)]

def proc_read():
    proc_event = proc.readline()
    #print("proc_event {!r}".format(proc_event))
    if proc_event in pty_buffer:
        #print("** Ignoring line {}".format(proc_event))
        return None
    else:
        return proc_event

def proc_write(command):
    global pty_buffer
    #print("%%% Writing to proc: {}".format(command))
    proc.write("{}\n".format(command))
    pty_buffer.append("{}\r\n".format(command))
    del pty_buffer[:1] # why is this faster than pty_buffer.pop(0)

# Just in case
proc_write("\r\n")
