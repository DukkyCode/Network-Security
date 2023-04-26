import random
import socket
import threading
import signal
import sys
import select

HOST = 'localhost'
SOCKET_LIST = []
threads = []

def clean_exit(signum,frame):
    """ handle a SIGINT (ctrl-C) keypress """
    
    for s in SOCKET_LIST:                 #close all sockets
        s.close()
    sys.exit(0)

signal.signal(signal.SIGINT,clean_exit)

ports = random.sample(range(2048,65535), 10)
sys.stdout.write(str(ports))
sys.stdout.flush()
out = open("opener.txt","w")
for port in ports:
    out.write(str(port)+ "\n")

out.close()

for port in ports:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, port))
    SOCKET_LIST.append(s)
    s.listen(1)

wlist = []
xlist = []

while True:
    (r, w, x) = select.select(SOCKET_LIST,wlist,xlist)
    for s in r:
        conn, addr = s.accept()
