#!/usr/bin/python

# Implement a class to store the requests. (Workload and result files.)
# Class has dataMembers: VM's IP, .cu file, data files and/or request Name (for pre-defined services)
# Queue will contain objects of the above class.
# Use Multithreading: Producer accepts GPU requests and queues them,
#                     Consumer pops items from queue and processes them, sends results back. 
#                     If required, implement another queue to store results, and a third thread will do the work
#					  of sending the results. <producer-Consumer chaining>

import os
import sys
import time
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

# Class for storing individual incoming requests and generated result files.
class procRequest():
	def __init__(self, conn, vmIP, fileCount, codeFile, DataFiles, resultFile):
		self.connection = conn
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

# IMP  : Slide must contain diagram showing 2 queues.

rGPU = socket.socket()
SIZE = 1024  
HOST = "10.0.0.91"                           # IP address of the HOST
# host = "130.85.250.30"
port = 12512                                 # Port number for GPU services

# Bind the port and Address 
rGPU.bind((HOST, port))
rGPU.listen(5)

# Listener thread running continuously waiting for requests
def keepListening():
	while True:
		# Accept an incoming connection from a VM
		client, addr  = rGPU.accept()
		if (debug) : print client, addr
		# Thread invocation on connectToVM method
		t_newConnection = threading.Thread(target=connectToVM, args = (client, addr))
		t_newConnection.start()

# Function to connect to a single VM and accept workload from it
# create an object and add it to the requestQ
def connectToVM(clientConn, addrOfVM):	
	# Extract IP and portnum of VM from addrOfVM
	remoteMachine = addrOfVM[0]
	portNum       = str(addrOfVM[1])
	# Accept the request to process data
	print "\nGPU service requested by %s " % remoteMachine
	clientConn.send(goodToSend)
	if (debug) : print "\n[DEBUG] : Request acknowledged.\n"

	# Accept the GPU code and data
	# VM sends over number of files it will send.
	numIncomingFiles = clientConn.recv(SIZE)
	#numIncomingFiles,halfFile = numIncomingFiles.split(DELIMITER)
	numIncomingFiles =  int(numIncomingFiles)
	print "\nNumber of Incoming Files are :", numIncomingFiles

	if debug : print "[DEBUG] : Number of incoming files are ", numIncomingFiles
	# Name of source code file. If pre-defined service is requested, codeFile = serviceName
	codeFile  = "sourceCode_" + remoteMachine.split(".")[3] + "_" + portNum + ".cu"
	# TODO : add support for an array of dataFiles. Currently implementing for a single input data file 
	dataFile = "workLoad_"  + remoteMachine.split(".")[3] + "_" + portNum 
	resFile  = "result_"    + remoteMachine.split(".")[3] + "_" + portNum 

	# Create an object of class procRequest to store the incoming request.
	serviceRequest = procRequest(clientConn, remoteMachine, numIncomingFiles, codeFile, dataFile, resFile)

	iteration = 1
	while(numIncomingFiles != 0):
		# TODO : Number all files coming from a particular VM in order.
		# Separate numbering for .cu and data files.
		recvFile = serviceRequest.codeFile if(iteration == 1) else serviceRequest.DataFiles

		if (debug) : print "This is iteration number ", iteration
		f = open(recvFile, 'wb')
		#if (iteration == 1) : f.write(halfFile)
		if (debug) : print "\n[DEBUG]: File Opened for writing."
		buff = clientConn.recv(SIZE)
		clientConn.settimeout(1)
		print('Receiving data...')
		while buff:
			f.write(buff)
			try:
				buff = clientConn.recv(SIZE)
			except socket.timeout:
				break
			if (debug): print "\n[DEBUG]: ",buff
			if (debug):	print "\n[DEBUG]: ",sys.getsizeof(buff)
		f.close()
		clientConn.settimeout(None)
		iteration += 1
		numIncomingFiles -= 1
	clientConn.send(transferComplete)
	# All data from clientConn has been received. 
	# Add the object created to Queue.
	requestQ.put(serviceRequest)
	if (debug) : print "Object Enququed!"
	if (debug) : print "Request Q size : ", requestQ.qsize()

	# Below code is executing one request at a time and sending the results.
	# Need to write separate functions for this. either 1 or 2.
	# These will be implemented by consumer threads working on the queue.	

def keepProcessing():
	while True:
		if (debug) : print "[PROCESS] Current Size is ", requestQ.qsize()
		processReq = requestQ.get(True)
		print "[PROCESS] SourceFile :",processReq.codeFile	
		t_startJob = threading.Thread(target=processRequest, args=(processReq,))
		t_startJob.start()	
	
def processRequest(processJob):
	print "SOURCE CODE : ", processJob.codeFile
	print "RESULT      : ", processJob.resultFile

	cmd = "python compileAndRunCuda.py " + "-i " + processJob.codeFile + " -o " + processJob.resultFile
	os.system(cmd)
	print "Run has Completed"
	processJob.connection.send(runComplete)
	resultsQ.put(processJob)

def keepSending():
	while True:
		sendRes = resultsQ.get(True)	
		t_sendResult = threading.Thread(target=sendResults, args=(sendRes,))
		t_sendResult.start()	

def sendResults(sendObj):
	# Client acknowledges its ready to receive results
	data = sendObj.connection.recv(SIZE)
	# Code to Send result File back to client
	if data == goodToSend:
		fd = open(sendObj.resultFile, 'rb')
		buff = fd.read(SIZE)
		while buff:
			sendObj.connection.send(buff)
			buff = fd.read(SIZE)
		# sendObj.connection.send(transferComplete)
		if (debug): print "\nThis is the last client rcv\n"
		sendObj.connection.recv(SIZE)
	sendObj.connection.close()                # Close the connection
	
######################################
#	MAIN FUNCTION
######################################

# Phase I : Keep Accepting Connections
t_keepListening = threading.Thread(target=keepListening)
t_keepListening.start()

# Phase II : Keep Processing from Request Q
t_keepProcessing   = threading.Thread(target=keepProcessing)
t_keepProcessing.start()

# Phase III : Keep Sending results from Result Q
t_keepSending  = threading.Thread(target=keepSending)
t_keepSending.start()
