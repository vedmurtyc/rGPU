#!/usr/bin/python
import os
import sys
import socket
import threading
from Queue import Queue

# Additional Flags
debug = 0
DELIMITER = "~!"

# Transfer Protocol
goodToSend       = "GOODTOSEND"
transferComplete = "TRANSFERCOMPLETE"
runComplete      = "RUNCOMPLETE"
transferTimeout  = "TRANSFERTIMEOUT"

# Implement a class to store the requests. (Workload and result files.)
# Class has dataMembers: VM's IP, .cu file, data files and/or request Name (for pre-defined services)
# Queue will contain objects of the above class.
# Use Multithreading: Producer accepts GPU requests and queues them,
#                     Consumer pops items from queue and processes them, sends results back. 
#                     If required, implement another queue to store results, and a third thread will do the work
#					  of sending the results. <producer-Consumer chaining>

# Class for storing individual incoming requests and generated result files.
class procRequest():
	def __init__(self, vmIP, fileCount, codeFile, DataFiles, resultFile):
		self.vmIP       = vmIP
		self.fileCount  = fileCount
		self.codeFile   = codeFile
		self.DataFiles  = DataFiles
		self.resultFile = resultFile 

# Queue for storing multiple requests from multiple VMs.
# Listening method enqueues requests to it.
# Processing method dequeues and processes the requests.
requestQ = Queue ()
resultsQ = Queue ()

# TODO : Need another queue and method just for sending data.
# IMP  : Slide must contain diagram showing 2 queues.

rGPU = socket.socket()
  # Make it a non-blocking socket
SIZE = 1024
# IP address of the HOST
HOST = "10.0.0.91"
# host = "130.85.250.30"
# Port number for GPU services
port = 12512        

# Bind the port and Address 
rGPU.bind((HOST, port))
rGPU.listen(5)

# Server running continuously waiting for requests
while True:

	# Accept an incoming connection from a VM
	client, addr  = rGPU.accept()
	remoteMachine = str(addr)[1:].split(",")[0][1:-1]

	# Accept the request to process data
	print "\n GPU service requested by %s " % remoteMachine
	client.send(goodToSend)
	print "\n Request acknowledged.\n"
	
	# Accept the GPU code and data
	# VM sends over number of files it will send.
    # TODO : on client side, send over argc of rGPU.py prior to sending any workload
    # For a single VM, server will keep accepting "numIncomingFiles" number of Files
	numIncomingFiles = client.recv(SIZE)
	#numIncomingFiles,halfFile = numIncomingFiles.split(DELIMITER)
	numIncomingFiles =  int(numIncomingFiles)
	print "Incomeing Files are :", numIncomingFiles
	# client.send(transferComplete)

	if debug : print "[DEBUG] : Number of incoming files are ", numIncomingFiles
	# Name of source code file. If pre-defined service is requested, codeFile = serviceName
	codeFile  = "sourceCode_" + remoteMachine.split(".")[3] + ".cu"
	# TODO : add support for an array of dataFiles. Currently implementing for a single input data file 
	# This means, numIncomingFiles = 2 for now.
	dataFile = "workLoad_"  + remoteMachine.split(".")[3]
	resFile  = "result_"    + remoteMachine.split(".")[3]

	# Create an object of class procRequest to store the incoming request.
	serviceRequest = procRequest(remoteMachine, numIncomingFiles, codeFile, dataFile, resFile)

	iteration = 1
	while(numIncomingFiles != 0):
		# TODO : Number all files coming from a particular VM in order.
		# Separate numbering for .cu and data files.
		recvFile = serviceRequest.codeFile if(iteration == 1) else serviceRequest.DataFiles

		if (debug) : print "This is iteration number ", iteration
		f = open(recvFile, 'wb')
		#if (iteration == 1) : f.write(halfFile)
		if (debug) : print "\n[DEBUG]: File Opened for writing."
		buff = client.recv(SIZE)
		client.settimeout(1)
		print('Receiving data...')
		while buff:
			f.write(buff)
			try:
				buff = client.recv(SIZE)
			except socket.timeout:
				break
			if (debug): print "\n[DEBUG]: ",buff
			if (debug):	print "\n[DEBUG]: ",sys.getsizeof(buff)
		f.close()
		client.settimeout(None)
		iteration += 1
		numIncomingFiles -= 1
	client.send(transferComplete)
	# All data from client has been received. 

	# Add the object created to Queue.
	requestQ.put(serviceRequest)
	# Server now waits for other GPU service requests.

	# Below code is executing one request at a time and sending the results.
	# Need to write separate functions for this. either 1 or 2.
	# These will be implemented by consumer threads working on the queue.	

# def processRequest():
	processReq = requestQ.get()
	cmd = "python compileAndRunCuda.py " + "-i " + processReq.codeFile + " -o " + processReq.resultFile
	os.system(cmd)
	print "Run has Completed"
	client.send(runComplete)

# def sendResults():
	# Client acknowledges its ready to receive results
	data = client.recv(SIZE)
	# Code to Send result File back to client
	if data == goodToSend:
		fd = open(processReq.resultFile, 'rb')
		buff = fd.read(SIZE)
		while buff:
			client.send(buff)
			buff = fd.read(SIZE)
		client.send(transferComplete)
		if (debug): print "\n This is the last client rcv\n"
		client.recv(SIZE)
	client.close()                # Close the connection
rGPU.close()
