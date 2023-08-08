####################################################
# Demo code for Access of DUT connected to serial
# Keysight Technologies 2015
# Works with Arduino Demo board running specific DUT Gen Code
#################################################### 
import sys
 
#sys.path.append("C:\\Users\\axelw\\Documents\\Agilent\\IronPython-2.7.5\\Lib")
#sys.path.append("C:\\Users\\axelw\\Documents\\Agilent\\IronPython-2.7.5\\Dlls")
sys.path.append("C:\Program Files (x86)\IronPython 2.7\Lib")
sys.path.append("C:\Program Files (x86)\IronPython 2.7\Dlls")
  
 #sys.path.append("C:\Anaconda\Lib")
# sys.path.append("C:\Anaconda\DLLs")
 


# Import the BitErrorCounter class from the M8070A framework 
clr.AddReference("Keysight.SeriesM80XX.Api")
from Keysight.SeriesM80XX.Api.ModuleAbstractionLayer import BitErrorCounter

# import SerialPort from System assembly (.Net)
clr.AddReference("System")
import System.IO.Ports.SerialPort

# global variables
serialPort = None
berCounter = BitErrorCounter(0,0)

def DUT_connect():
	# use global serialPort variable, do not create a local version
	global serialPort
	# create an instance of SerialPort for COM port 6
	serialPort = System.IO.Ports.SerialPort("COM9")

	# configure serial port to 9600 bit/s 8N1
	serialPort.BaudRate = int (9600)
	serialPort.DataBits = int(8)

	# set read and write timeouts to 500ms
	serialPort.ReadTimeout = int(500)
	serialPort.WriteTimeout = int(500)

	# finally open the COM port
	serialPort.Open()
	
	# set target BER or choose variable BER
	serialPort.WriteLine("B4.2e-9")

	
def DUT_disconnect():
	# use global serialPort variable, do not create a local version
	global serialPort
	if (serialPort != None):
		# check if COM port is open
		if (serialPort.IsOpen):
			serialPort.Close()
			# dispose the serialPort instance
			serialPort.Dispose()
			# ensure that the disposed object is not used anymore
			serialPort = None

def DUT_getLocations():
	# this is what our channel will be called
	return ["Lane1"]


def DUT_getBER(location):
	# use global serialPort and berCounter variable,
	# do not create local versions
	global serialPort, berCounter
	
	serialPort.WriteLine("c")
	# read one line from the com port
	counters = serialPort.ReadLine()
	# split comma separated value pair into two
	deltaBits,deltaErrs = counters.split(",")
	# create a new BitErrorCounter and add the old values
	# order is important!
	berCounter = BitErrorCounter(float(deltaBits), float(deltaErrs)).Add(berCounter)
	# return the new counter to the measurement
	return berCounter
