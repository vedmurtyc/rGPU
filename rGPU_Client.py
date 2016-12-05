#!/usr/bin/python          
# This is client.py file
import sys
import time
import argparse
from sendfile import sendfile

import socket              # Import socket module
size = 1024

source_cu = ""
parser = argparse.ArgumentParser()
parser.add_argument("--v", "-v", "-verbose", "--verbose", action='store_true')
parser.add_argument("-i", "--input", action='store')
cmd_args = parser.parse_args()
v = cmd_args.v
print v
source_cu = cmd_args.input
print source_cu

transferComplete = "TRANSFERCOMPLETE"
runComplete = "RUNCOMPLETE"
goodToSend = "GOODTOSEND"

s = socket.socket()         # Create a socket object
host = "10.0.0.91" 			# Get local machine name
port = 12512                # Reserve a port for your service.

s.connect((host, port))

status = s.recv(size)
if (v):
	print "Status: %s" % status
if status == goodToSend:
	#Send server the number of files being sent
	#numOutgoingFiles = str(len(sys.argv)-1)
	numOutgoingFiles = 1
	#numOutgoingFiles += "~!"
	s.send(str(numOutgoingFiles))
	time.sleep(1)
	
	try:
		file1 = source_cu
		fd = open(file1, 'rb')
	except IOError:
		print "Cannot open " + file1	
	
	buff = fd.read(size)
	while buff:
		s.send(buff)
		buff = fd.read(size)
	
	#Receive ack from server on file send
	status = s.recv(1024)
	if (v):
		print "Status: " , status

	#Receive notification from server for accepting output
	status = str(s.recv(15))
	if (v):
		print "Status: " , status

	s.send(goodToSend)
	if status == runComplete:
		if (v):
			print "Status: Server is now sending output data"
		resFile = file1[:-3] + "_result"
		resFd = open(resFile, 'wb')
		if (v):
			print "Status: Writing result to output file"
		buff = s.recv(size)
		s.settimeout(1)
		while buff:
			resFd.write(buff)
			print buff
			try:
				buff = s.recv(size)
			except socket.timeout:
				break
		resFd.close()
		s.settimeout(None)

		s.send(transferComplete)
		if (v):
			print "Status: Done!"

s.close()                    # Close the socket when done
