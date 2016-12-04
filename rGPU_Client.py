#!/usr/bin/python          
# This is client.py file
import sys
import time

import socket              # Import socket module
size = 1024
transferComplete = "TRANSFERCOMPLETE"
runComplete = "RUNCOMPLETE"
goodToSend = "GOODTOSEND"

s = socket.socket()         # Create a socket object
host = "10.0.0.91" 			# Get local machine name
port = 12512                # Reserve a port for your service.

s.connect((host, port))

serverReady = s.recv(size)
print "Status: %s" % serverReady
if serverReady == goodToSend:
	#Send server the number of files being sent
	numOutgoingFiles = str(len(sys.argv)-1)
	#numOutgoingFiles += "~!"
	s.send(str(numOutgoingFiles))
	time.sleep(2)
	
	try:
		file1 = sys.argv[1]
		fd = open(file1, 'rb')
	except IOError:
		print "Cannot open " + file1	
	
	buff = fd.read(size)
	while buff:
		s.send(buff)
		buff = fd.read(size)
	
	#Receive ack from server on file send
	print "Status: %s" % s.recv(1024)

	#Receive notification from server for accepting output
	data = str(s.recv(15))
	print "Status:" + data

	s.send(goodToSend)
	if data == runComplete:
		print "Status: Server is now sending output data"
		resFile = file1[:-3] + "_result"
		resFd = open(resFile, 'wb')
		print "Status: Writing result to output file"
		while True:
			buff = s.recv(size)
			if buff == transferComplete: 
				break			
			resFd.write(buff)

		s.send(transferComplete)
		print "Status: Done!"

s.close()                    # Close the socket when done
