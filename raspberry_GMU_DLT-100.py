import sys
#import spidev
#import smbus
import time
import os
import threading
import string
import serial

import RPi.GPIO as GPIO
from datetime import datetime, date
from PyQt4 import QtCore, QtGui
from IFS2 import Ui_Dialog as Dlg


class responds(QtCore.QThread):
    def __init__(self,parent):
        QtCore.QThread.__init__(self,parent)
        #self.a=MCP3204(self)
        #self.a.start()
        try:
            self.port = serial.Serial("/dev/ttyAMA0", 9600, timeout=0)

            self.spi0=spidev.SpiDev()
            self.spi0.open(0,0)
            self.spi0.max_speed_hz =(4000000)

            self.spi=spidev.SpiDev()
            self.spi.open(0,1)
            self.spi.max_speed_hz =(4000000)

        except SyntaxError:
            print "Connection cant be established"

    def setOutput(self,channel,val):
        val=int(val)
        lowbyte=val&0xff
        highbyte=((val>>8) &0xff) | channel <<7 | 0x1 << 5 | 1 <<4;
        self.spi.xfer2([highbyte, lowbyte])


    def convertOutput(self,data):
        val=data*5/float(4096)
        output=round(val,1)
        return output

    def ReadChannel(self,channel):
        d=[0x00,0x00,0x00]
        d[0]|=1<<2
        d[0]|=(True)<<1
        d[0]|=(channel>>2) & 0x01
        d[1]|=((channel>>1)&0x01)<<7
        d[1]|=((channel>>0)&0x01)<<6
        adc=self.spi0.xfer2(d)

        resolution=12
        data=(adc[1] & 2**(resolution-8)-1) <<8 | adc[2]

        return data

    def ConvertVolts(self,data,places):
        volts = (data * 5)/ float(4096)
        volts = round(volts,places)
        return volts

    def ConvertFlow(self,data,places):
        flow = (data * 200)/ float(4096)
        flow = round(flow,places)
        return flow

    def lesen(self):
        datei=open("ratio.txt","r")
        dilute=datei.readlines()
        datei.close()
        dilute.reverse()
        dilute=float(dilute.pop(0))
        #print "Dilute" + str(dilute)
        light_channel=0

        light_level = self.ReadChannel(light_channel)
        light_volts = self.ConvertVolts(light_level,1)
        flow_level = self.ConvertFlow(light_level,1)

        self.limit=self.limit+float(flow_level)
        self.emit(QtCore.SIGNAL("diot(QString,QString)"),str(light_volts),str(flow_level))

        mixit=float(light_level)*(dilute)
        #print "Ratio " + str(light_level) + " * " + str(dilute) + " =  " + str(mixit)
        self.setOutput(0,mixit)
        #utself.convertOutput(mixit)
        self.emit(QtCore.SIGNAL("mixing(QString)"),str(mixit))

    def communication(self):

        self.emit(QtCore.SIGNAL("update(QString)"),"Waiting for Signal.....")
        #print "\n Waiting for Signal....."

        while self.port.inWaiting() <= 8:
            time.sleep(0.001)
            continue

        self.emit(QtCore.SIGNAL("update(QString)"),"Reading Query.....\n")
        #print "Reading Query......."
        time.sleep(0.1)
        tmp=self.port.readlines()
        query=string.split(tmp[0],"\r")
        self.workload(query)

    def itsBusy(self):

        self.emit(QtCore.SIGNAL("update(QString)"),"Busy!")

        while self.port.inWaiting() <= 8:
            continue

        time.sleep(0.1)
        tmp=self.port.readlines()
        query=string.split(tmp[0],"\r")

        while True:
            try:
                com=query.pop(0)
                self.port.write("BUSY\r")
            except ValueError:
                self.emit(QtCore.SIGNAL("update(QString)"),"Buffer cleaned!")
            finally:
                break

    def getSam(self,id):

        self.emit(QtCore.SIGNAL("update(QString)"),"Getting Sample!")

        #print "Getting Sample!"

        datei=open("sample.txt","w")
        datei.write(str(id)+"\n")
        datei.close()

    def injectSam(self,timer):

        self.emit(QtCore.SIGNAL("update(QString)"),"Valve open!")
        #print "\n Opening Valve...."
        self.itsBusy()

        datei=open("sample.txt","r")
        samples=datei.readlines()
        samples.reverse()
        datei.close()

        sample=int(float(samples.pop(0)))

        cnt=round(time.time())+timer
        cnt1=round(time.time())

        self.emit(QtCore.SIGNAL("update(QString)"),"Injecting Sample Nr. " + str(sample))
        self.emit(QtCore.SIGNAL("setValve(QString)"),str(sample))

        self.limit=0

        datei=open("limit.txt","r")
        limes=datei.readlines()
        limes.reverse()
        datei.close()
        limes=int(float(limes.pop(0)))

        while float(self.limit) < limes:

            self.itsBusy()
            self.lesen()

        self.setOutput(0,0)
        self.emit(QtCore.SIGNAL("update(QString)"),"Valve Closed!")
        self.emit(QtCore.SIGNAL("setValve(QString)"),"off")

    def workload(self,comList):

        def stdRply(com):
            #self.emit(QtCore.SIGNAL("update(QString)"),"Sampler Ready.")
            #print "Report Ready!!!!!!!!!\n"
            self.port.write("|/r")
            #workload(comList)

        def position(com):
            #print "Sending Position.\n"
            self.port.write("0\r0\r0\r0\r0\r0\r|\r")

            datei=open("sample.txt","r")
            samples=datei.readlines()
            samples.reverse()
            datei.close()

            sample=int(float(samples.pop(0)))
            self.emit(QtCore.SIGNAL("setBank(QString)"),str(sample))
            #workload(comList)

        def cruise(com):
            #self.emit(QtCore.SIGNAL("update(QString)"),"...")
            #print "Moving to Home\n"
            self.port.write("|\r")
            #workload(comList)

        def status(com):
            #self.emit(QtCore.SIGNAL("update(QString)"),"Status: Ready!")
            #print "Status: READY."
            self.port.write("READY\r")
            #workload(comList)

        def motStatus(com):
            #print "System Status: Ready\n"
            self.port.write("|\r")
            #workload(comList)

        def getSample(com):
            self.port.write("|\r\x13\x11\x13\x11\r")
            sampAttrib=string.split(com,",")
            sampId=float(sampAttrib[1])
            self.getSam(sampId)

        def injSample(com):
            self.port.write("|\r")
            # hier ist der fehler falsche variable
            injAttrib=string.split(com,",")
            #print "Injecting " + str(injAttrib[5]) + " milliseconds."
            tmp=float(injAttrib[5])/1000
            #print str(tmp)
            self.injectSam(tmp)

        commands={"REP_RDY" : stdRply,
                  "POS_STA" : position,
                  "MOVETO_" : cruise,
                  "GET_STA" : status,
                  "MOT_REF" : motStatus,
                  "GET_SAM" : getSample,
                  "INJ_SAM" : injSample}
        try:
            com=comList.pop(0)
            commands[com[0:7]](com)

            ts= time.time()
            prot=[datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),"Logfile.dat"]
            protokol=open("_".join(prot),"a")
            protokol.write(com+"\n")
            protokol.close()

        except:
            pass

    def run(self):
        self.limit=0
        while True:

            #print "In run"
            self.communication()


class MyApp(QtGui.QDialog,Dlg):
    def __init__(self, parent=None):
        #QtGui.QDialog.__init__(self)
        super(QtGui.QDialog,self).__init__(parent)
        self.setupUi(self)
        self.initial()
        #self.threadPool = []

    def initial(self):

        self.x=0
        self.y=0
        self.lim=0
        self.measure=False

        self.doit.setText("Set flow limit.")
        self.connect(self.SetFlowLimit,QtCore.SIGNAL("clicked()"),self.setFlow)
        self.connect(self.SetRatio,QtCore.SIGNAL("clicked()"),self.setRatio)
        self.connect(self.StartButton,QtCore.SIGNAL("clicked()"),self.workThread)

        datei=open("ratio.txt","w")
        datei.write("50"+"\n")
        datei.close()

        datei=open("limit.txt","w")
        datei.write(str(1000)+"\n")
        datei.close()

        self.initI2C()

    def workThread(self):

        self.StartButton.setText("Running")
        self.StartButton.setEnabled(False)
        self.doit.clear()
        self.doit.setText("Main started")

        self.connect(self.clearScreenButton,QtCore.SIGNAL("clicked()"),self.ServiceInfo.clear)

        self.connect(self.ResetButton,QtCore.SIGNAL("clicked()"),self.initI2C)

        self.talk=responds(self)
        self.talk.start()
        self.connect(self.talk,QtCore.SIGNAL("setValve(QString)"),self.MCP_23017)
        self.connect(self.talk,QtCore.SIGNAL("setBank(QString)"),self.Bank_23017)

        self.connect(self.talk, QtCore.SIGNAL("update(QString)"), self.writeVal)
        self.connect(self.talk, QtCore.SIGNAL("update2(QString)"), self.report)
        self.connect(self.talk, QtCore.SIGNAL("diot(QString,QString)"),self.MFC_in)
        self.connect(self.talk, QtCore.SIGNAL("mixing(QString)"),self.MFC_out)

    def MFC_in(self,i,ii):
        #print "MFC IN"
        #print self.measure
        if self.measure==True:
            self.x=self.x+float(ii)
            self.y=float(ii)

            self.repInflow.setText(i)
            self.label_10.setText(ii)

            #self.repFlowSum.setText("")
            self.label_11.setText(str(self.x))


        else:
            self.repInflow.setText(i)

    def MFC_out(self,x):

        val=(float(x)/5)*100

        val=float(x)*5/float(4096)
        output=round(val,1)
        self.lRepRatio.setText(str(output))

        flow = (float(x) * 200)/ float(4096)
        flow = round(flow,1)
        self.label_12.setText(str(flow))

        #self.y=flow

        #if float(x) != 0:
        #    val=(float(x)/5)*100
        #    self.MixProgress.setValue(int(val))
        #else:
        #    self.MixProgress.setValue(0)

    def readVals(self):
        self.repSend.setText("Nothing to do.")

    def report(self,answer):
        ts= time.time()
        stemp=datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        self.repSend.append(stemp + ": " + answer)

    def writeVal(self,output):
        #ts= time.time()
        #stemp=datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        self.doit.clear()
        self.doit.setText(output)
        time.sleep(0.1)
        #self.repRecieve.append(output)

    def setFlow(self):
        self.lim=self.spinBoxFlow.value()
        self.setFlowsum.setText(str(self.lim))

        datei=open("limit.txt","w")
        datei.write(str(self.lim)+"\n")
        datei.close()

    def setRatio(self):
        r=self.spinBoxRatio.value()
        self.SetRatio_2.setText(str(r))
        r=float(r)/100
        datei=open("ratio.txt","w")
        datei.write(str(r)+"\n")
        datei.close()

    def Bank_23017(self,nr):

        address2 = 0x21

        PinDic3={"0":0x40,
            "all":0xff,
            "off":0x00}

        nr = int(nr)-1
        if int(nr) <= 5:
            self.mcp23017.write_byte_data(address2,0x15,PinDic3[str(0)])
            #print "Switched to 1" + str(nr)
        else:
            self.mcp23017.write_byte_data(address2,0x15,PinDic3["off"])
            print "Bank 2"


    def MCP_23017(self,nr):

        address = 0x20
        address2 = 0x21

        PinDic={"7":0x80,
            "6":0x40,
            "5":0x20,
            "4":0x10,
            "3":0x08,
            "2":0x04,
            "1":0x02,
            "0":0x01,
            "all":0xff,
            "off":0x00}

        PinDic2={"7":0x80,
            "6":0x80,
            "5":0x60,
            "4":0x50,
            "3":0x48,
            "2":0x44,
            "1":0x42,
            "0":0x41,
            "all":0xff,
            "off":0x00}

        PinDic3={"0":0x40,
            "all":0xff,
            "off":0x00}

        start= time.time()

        while True:
            try:

                if nr == "off":
                    ts= time.time()
                    st=datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

                    datei=open("sample.txt","r")
                    samples=datei.readlines()
                    samples.reverse()
                    datei.close()

                    sample=int(float(samples.pop(0)))
                    #nr = int(nr)-1
                    #print nr
                    if sample < 7:
                     #   print "bank 1 aus"
                        self.mcp23017.write_byte_data(address2,0x15,PinDic3["0"])
                        self.mcp23017.write_byte_data(address,0x15,PinDic["off"])
                    else:
                      #  print "bank 2 aus"
                        self.mcp23017.write_byte_data(address2,0x14,PinDic["off"])
                        self.mcp23017.write_byte_data(address,0x14,PinDic["off"])

                    ts= time.time()
                    prot=[datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),"logfile_off_vol.dat"]
                    #mixR=self.lRepRatio.value()
                    f=open("_".join(prot),"a")
                    f.write(" (" + str(self.x) + " ml) " + "\n")
                    f.close()

                    self.repSend.append(" (" + str(self.x) + " ml) \n")
                    self.x=0
                    self.label_10.setText(str(self.x))
                    self.label_11.setText(str(self.x))
                    self.measure=False
                else:
                    ts= time.time()
                    prot=[datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),"logfile_off_vol.dat"]
                    st=datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

                    f=open("_".join(prot),"a")
                    f.write(st + ": Sample Nr:  " + str (nr))
                    f.close()


                    self.repSend.append(st + ": \n Sample Nr:  " + str (nr))

                    nr = int(nr)-1
                    self.measure=True

                    if  nr < 6:
                        print "Valve nr" + str(nr)
                        self.mcp23017.write_byte_data(address2,0x15,PinDic2[str(nr)])
                        self.mcp23017.write_byte_data(address,0x15,PinDic[str(nr)])

                    if  nr >= 6:

                        nr=nr-4
                        self.mcp23017.write_byte_data(address2,0x15,PinDic2["off"])
                        self.mcp23017.write_byte_data(address2,0x14,PinDic[str(nr)])
                        self.mcp23017.write_byte_data(address,0x14,PinDic[str(nr)])


            except IOError as (errno, strerror):
                ts= time.time()
                st=datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                self.ServiceInfo.append(st+ " I/O error({0})".format(errno,strerror))
                self.initI2C()
                continue

            except:
                ts= time.time()
                st=datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                #self.ServiceInfo.append(st+ "Unexpected error",sys.exc_info()[0])
                self.initI2C()
                continue

            break

    def initI2C(self):

        x=21
        y=20
        HIGH=1
        LOW=0

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(x,GPIO.OUT)
        GPIO.setup(y,GPIO.OUT)
        GPIO.output(x,LOW)
        GPIO.output(y,LOW)

        time.sleep(1)
        GPIO.output(x,HIGH)
        GPIO.output(y,HIGH)

        self.mcp23017 = smbus.SMBus(1)
        address = 0x20
        address2 = 0x21

        while True:
            try:
                self.mcp23017.write_byte_data(address2,0x00,0x00)
                self.mcp23017.write_byte_data(address2,0x01,0x00)

                self.mcp23017.write_byte_data(address,0x00,0x00)
                self.mcp23017.write_byte_data(address,0x01,0x00)


                self.mcp23017.write_byte_data(address,0x14,0x00)
                self.mcp23017.write_byte_data(address,0x15,0x00)
                self.mcp23017.write_byte_data(address2,0x14,0x00)
                self.mcp23017.write_byte_data(address2,0x15,0x00)

                ts= time.time()
                st=datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                self.ServiceInfo.append(st+"   I2C reset!")

            except IOError as (errno, strerror):
                ts= time.time()
                st=datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                self.ServiceInfo.append(st+ " I/O error({0})".format(errno,strerror))
                self.initI2C()
                continue

            except:
                self.ServiceInfo.append(st+ "Unexpected error",sys.exc_info()[0])
                self.initI2C()
                continue
            break

# run
app = QtGui.QApplication(sys.argv)
test = MyApp()
test.show()
app.exec_()
