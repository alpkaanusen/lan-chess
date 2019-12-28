import sys
import socket
import select
import os
import hashlib
import string
import time


os.system('clear')
# Get username
hostIp = '192.168.43.1'
port = 12345

while(True):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
	sock.sendto(str.encode("[esra,192.168,announce]"),('<broadcast>',12345))
	time.sleep(5)
