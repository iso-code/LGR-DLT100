#!/usr/bin/env python

__author__ = "Marcel Gaj"
__copyright__ = "Copyright 2018"
__credits__ = [""]
__license__ = "GPL"
__version__ = "1.0.2"
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


def itsBusy():

    while port.inWaiting() == 0:
        continue

    tmp=port.readlines()
    query=string.split(tmp[0],"\r")
    while True:
        try:
            com=query.pop(0)
            port.write("BUSY\r")
        except ValueError:
            "Nothing in Buffer"
        finally:
            break
    return com


def getSam(id):
    print "Install probe for sample nr: " + str(id)
    while port.inWaiting() == 0:
        continue

    time.sleep(0.1)
    tmp=port.readlines()
    query=string.split(tmp[0],"\r")
    while True:
        try:
            com=query.pop(0)
            port.write("BUSY\r")
        except ValueError:
            "Nothing in Buffer"
        finally:
            break
    workload(query)


def injectSam(timer):
    print "\n Opening Valve...."
    com=itsBusy()

    cnt=round(time.clock())+timer
    cnt1=round(time.clock())
    print "Timer :   " + str(timer)  + " s"
    print "Counting......"
    port.setRTS(True)

    while cnt != cnt1:
        inv=cnt1+1
        cnt1=round(time.clock())
        com=itsBusy()
        if inv == cnt1:
            print str(cnt1-cnt) + " s "
        else:
            continue
    port.setRTS(False)
    print "Closing valve...."
    communication()

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
        port.write("|\r\x13\x11\x13\x11\r")
        sampAttrib=string.split(com,",")
        sampId=float(sampAttrib[1])
        #print "Getting Sample Nr.:  " + sampAttrib[1]
        getSam(sampId)

    def injSample():
        port.write("|\r")
        injAttrib=string.split(com,",")
        #print "Injecting " + str(injAttrib[5]) + " milliseconds."
        tmp=float(injAttrib[5])/1000
        #print str(tmp)
        injectSam(tmp)

    commands={"REP_RDY" : stdRply,
              "POS_STA" : position,
              "MOVETO_" : cruise,
              "GET_STA" : status,
              "MOT_REF" : motStatus,
              "GET_SAM" : getSample,
              "INJ_SAM" : injSample}

    try:
        com=comList.pop(0)
        port.setRTS(False)
        print com
        commands[com[0:7]](comList)
    except:
        print "No Workload."
        port.setRTS(False)
        communication()

# initilize your serial port
# Figure out your serial Port and change if necessary
# here it was COM6

try:
    port = serial.Serial('COM6', 9600, timeout=0)
    port.setRTS(False)
    port.setDTR(False)
    communication()

except SyntaxError:
    pass

workload(query)

port.close()
