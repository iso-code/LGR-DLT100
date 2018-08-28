#!/usr/bin/env python

# This script enables to use the LGR DLT-100 in automatic mode without attached Autosampler
# instead you create a connection between your serial to usb adapter and the LGR
# Things to do:
# - Configure your serial port
# - make a bridge between pin 4 and 7 of at the LGR serial plug
# - Connect the serial of your computer and the LGR
# - start the script, then start a measurement cycle with the LGR

# A applied example can be found here:
# https://doi.org/10.5194/hess-20-715-2016

__author__ = "Marcel Gaj"
__copyright__ = "Copyright 2018"
__credits__ = [""]
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Marcel Gaj"
__email__ = "marcelspost@msn.com"
__status__ = "applicable"

#------------------------------------------------------------------------------------
import string
import serial
import time

query=[]
i=0
try:
    input("Press Enter to continue...")
except SyntaxError:
    pass

# Waiting for signals from LGR
def communication():
    print "\n Waiting for Signal....."
    while port.inWaiting() == 0:
        continue
    print "Reading Query......."
    time.sleep(0.1)
    tmp=port.readlines()
    query=string.split(tmp[0],"\r")
    workload(query)

# Answers to LGR
def workload(comList):

    def stdRply(comList):
        print "Report Ready\n"
        port.write("|/r")
        return workload(comList)

    def position(comList):
        print "Sending Position.\n"
        port.write("0\r0\r0\r0\r0\r0\r|\r")
        return workload(comList)

    def cruise(comList):
        print "Moving to Home\n"
        port.write("|\r")
        return workload(comList)

    def status(comList):
        print "Status: READY."
        port.write("READY\r")
        return workload(comList)


    def motStatus(comList):
        print "System Status.\n"
        port.write("|\r")
        workload(comlist)

    def getSample(comList):
        print "Getting Sample: \n"
        port.write("|\r\x13\x11\x13\x11\r")
        return workload(comList)

    def injSample():
        print "Inject the sample....\n"
        port.write("|\r")
        time.sleep(10)
        return workload(comList)

    commands={"REP_RDY" : stdRply,
              "POS_STA" : position,
              "MOVETO_" : cruise,
              "GET_STA" : status,
              "MOT_REF" : motStatus,
              "GET_SAM" : getSample,
              "INJ_SAM" : injSample}

    try:
        com=comList.pop(0)
        print com
        commands[com[0:7]](comList)
    except:
        print "Work done. Pending..."
        communication()

# initilize your serial port
# Figure out your serial Port and change if necessary
# here it was COM6

try:
    port = serial.Serial('COM6', 9600, timeout=0)
    communication()
except SyntaxError:
    pass

workload(query)

port.close()
