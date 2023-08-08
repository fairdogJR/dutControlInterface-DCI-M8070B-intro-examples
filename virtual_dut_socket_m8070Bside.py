#########################################################################################################
#
# DUT Control Interface script to integrate error counters of a virtual DUT running on a remote PC 
# into the M8070A framework.
#
# Copyright Keysight Technologies 2016
#########################################################################################################


#
# Useful sources of information
#   IronPython and .Net Framework usage
#   http://ironpython.net/
#   http://ironpython.net/documentation/dotnet/
#   https://msdn.microsoft.com/en-us/library/gg145045(v=vs.100).aspx
#
#   Python Language
#   https://www.python.org/


# Import the BitErrorCounter class from the M8070A framework
# Note: This is an example for importing and using types defined in .Net assemblies 
clr.AddReference("Keysight.SeriesM80XX.Api")
from Keysight.SeriesM80XX.Api.ModuleAbstractionLayer import BitErrorCounter

# import additional modules here
import sys


# import required .Net assemblies and types here
import System
from System import *
from System.Text import *
from System.Net import *
from System.Net.Sockets import *


# define global variables here
ipAddress = "127.0.0.1"  # Replace "127.0.0.1" with the actual IP address of your DUT
portNr = 8080

clientSocket1 = None




def sendCommandToDUTandReceiveResponse(command, parameters = None):
	stringToSend = command
	if(parameters != None):
		for element in parameters:
			stringToSend += ':' + element
	stringToSend += '\n'
	
	global clientSocket1
	try:
		sendBuffer = Text.Encoding.ASCII.GetBytes(stringToSend)
		clientSocket1.GetStream().Write(sendBuffer, 0, sendBuffer.Length)
		clientSocket1.GetStream().Flush()
		
		receiveBuffer = Array.CreateInstance(Byte, clientSocket1.ReceiveBufferSize)
		clientSocket1.GetStream().Read(receiveBuffer, 0, clientSocket1.ReceiveBufferSize)
		receivedString = System.Text.Encoding.ASCII.GetString(receiveBuffer)
		receivedString = receivedString.Substring(0, receivedString.IndexOf("\n"))
		
	except:
		raise IOError("Connection to DUT lost!")
		
	response = receivedString
	if (receivedString.Contains(":")):
		response = receivedString.Substring(0, receivedString.IndexOf(":"))
    	receivedParameters = receivedString.split(':')[1:]
		
		
	if(response != "OK"):
		raise IOError("DUT could not execute \"" + command, "\" ; " + receivedParameters[0])
	
	return receivedParameters




def OnInstall():
	"""
	Will be called right after the script code has been loaded.
	This allows to perform initialization tasks like establishing the communication with the DUT before any other function is being executed.
	
	Arguments:
		none
	
	Returns:
		nothing
	
	"""
	global clientSocket1
	try:
		clientSocket1 = TcpClient()
	except(SocketException):
		raise IOError("Could not create a TCP socket!")


def OnUninstall():
	"""
	Will be called before the script code is removed from the system.
	This allows to perform clean-up steps like releasing allocated system resources or closing opened files.
	
	Arguments:
		none
	
	Returns:
		nothing
	
	"""
	global clientSocket1
	del clientSocket1
	clientSocket1 = None


def DUT_connect():
	"""
	Connect the DUT. The actions required to connect the DUT depend on the individual DUT, 
	it's communication interface and eventually the test setup itself.
	DUT_connect needs to ensure that DUT power is applied correctly, communication interfaces are initialized when connecting.
	
	SCPI:
		:SYSTem:DCINterface:DEVice:CONNect 'identifier',<OFF|ON|0|1>
		:SYSTem:DCINterface:DEVice:CONNect? 'identifier'
		where identifier is the full location identifier as shown in the GUI (e.g. DCI.Control)
	
	Arguments:
		none
	
	Returns:
		nothing
	
	"""
	global ipAddress, portNr, clientSocket1
	try:
		clientSocket1.Connect(IPAddress.Parse(ipAddress), portNr)
	except:
		raise IOError("Could not connect to DUT!")


def DUT_disconnect():
	"""
	Disconnect the DUT. The actions required to disconnect the DUT depend on the individual DUT, 
	it's communication interface and eventually the test setup itself.
	On disconnect it needs to ensure that at least the communication interfaces become free for other applications or tools.
	
	SCPI:
		:SYSTem:DCINterface:DEVice:CONNect 'identifier',<OFF|ON|0|1>
		:SYSTem:DCINterface:DEVice:CONNect? 'identifier'
		where identifier is the full location identifier as shown in the GUI (e.g. DCI.Control)
	
	Arguments:
		none
	
	Returns:
		nothing
	
	"""
	global clientSocket1
	try:
		sendCommandToDUTandReceiveResponse("DUT_disconnect", [""])
		clientSocket1.Close()
	except:
		pass
	
	
def DUT_Init(location, initArg):
	"""
	Initialize the DUT according to the given argument. This is intended as a generalized initialization mechanism that can be executed from remote programs prior starting a particular measurement.
	The M8070A software will not call this function unless requested via the remote programming interface, or if the script is calling this internally (e.g. from a measurement plug-in specific hook function).
	
	SCPI:
		:SYSTem:DCINterface:EXECute[:INIT] 'identifier','Argument'
		where identifier is the full location identifier as shown in the GUI (e.g. DCI.Lane1)
	
	Arguments:
		location  	String    
			Addresses a particular location within the DUT and must be one of the locations that are returned by DUT_getLocations().
	
		initArg   	String    
			This argument is intended as a context specific control of the DUT initialization. The M8070A software does not use this value at all. It is up to the script implementer to decide how to interpret and use this argument.
	
	Returns:
		nothing
	
	"""
	return sendCommandToDUTandReceiveResponse("DUT_Init", (location, initArg))


def DUT_getBER(location):
	"""
	Read the bit error counters at the given location.
	
	If your function requires to do calculations with the number of compared bits or errors,
	add the following code at the top of your script to import the data type UInt64, 
	which is expected by the BitErrorCounter class.
	
		clr.AddReference("mscorlib")
		from System import UInt64
	
	Variables of type UInt64 can then be created like this:
		bits = UInt64(1000)
	
	For details consult https://msdn.microsoft.com
	
	SCPI:
		:FETCh:BCOunter? 'identifier'
		where identifier is the full location identifier as shown in the GUI (e.g. DCI.Lane1)
	
	Arguments:
		location  	String    
			Addresses a particular location within the DUT and must be one of the locations that are returned by DUT_getLocations().
	
	Returns:
		The bit error counter retrieved from the DUT as an instance of type BitErrorCounter.
		Return BitErrorCounter(0,0,0,0) if location is invalid.
		If location is valid, read the error counters of the DUT and return either
			BitErrorCounter(UInt64 comparedBits, UInt64 erroredBits)
		or
			BitErrorCounter(UInt64 comparedOnes, UInt64 comparedZeros, UInt64 erroredOnes, UInt64 erroredZeroes)
	
	"""
	receivedData = []
	receivedData = sendCommandToDUTandReceiveResponse("DUT_getBER", [location])
	if(len(receivedData) == 4):
		comparedOnes, comparedZeros, erroredOnes, erroredZeroes = receivedData
		return BitErrorCounter(UInt64(comparedOnes), UInt64(comparedZeros), UInt64(erroredOnes), UInt64(erroredZeroes))
	return BitErrorCounter(0, 0, 0, 0)


def DUT_getLocations():
	"""
	Returns a list of strings, naming the locations within the DUT, that can be controlled with the DUT Control Interface.
	The returned list must contain at least one valid string.
	
	Arguments:
		none
	
	Returns:
		List of strings that name the locations.
	
	"""
	return ["Lane1"]


def DUT_syncPattern(location):
	"""
	Synchronize the bit error counter at the given location to the received data stream.
	
	SCPI:
		:DATA:SYNC[:ONCE] 'identifier'
		where identifier is the full location identifier as shown in the GUI (e.g. DCI.Lane1)
	
	Arguments:
		location  	String    
			Addresses a particular location within the DUT and must be one of the locations that are returned by DUT_getLocations().
	
	Returns:
		nothing
	
	"""
	sendCommandToDUTandReceiveResponse("DUT_syncPattern", [location])
	
	
def DUT_getDeviceModes():
	"""
	Returns a list of strings, naming individual modes or configurations that can be applied to the device.
	The returned list must contain at least one valid string.
	
	Arguments:
		none
	
	Returns:
		List of strings that name the individual modes or configurations.
	
	"""
	return ["Mode1", "Mode2"]


def DUT_setDeviceMode(configuration):
	"""
	Configure the device according to the given mode.
	
	SCPI:
		:SYSTem:DCINterface:DEVice:MODE 'identifier','mode'
		:SYSTem:DCINterface:DEVice:MODE? 'identifier'
		where identifier is the full location identifier as shown in the GUI (e.g. DCI.Control)
	
	Arguments:
		configuration	String    
			Names the mode or configuration that shall be applied to the device. The value of 'mode' must be one of the strings that are returned by DUT_getDeviceModes().
	
	Returns:
		nothing
	
	"""
	sendCommandToDUTandReceiveResponse("DUT_setDeviceMode", [configuration])



def DUT_setSimulatedErrorRatio(errorRatio):
	sendCommandToDUTandReceiveResponse("DUT_setSimulatedErrorRatio", [errorRatio]);
	
