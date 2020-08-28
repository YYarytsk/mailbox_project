#!/usr/bin/env python3
import mysql.connector
from evdev import InputDevice
from select import select
import RPi.GPIO as GPIO
import time
import nexmo


#Nexmo service login and text massage defenition
client = nexmo.Client(key='*******', secret='*******************')
receiver = '1203260****'
message = '''Alert!!! Mailbox Has been accessed!!!'''
message2 = '''Warning!!! Unauthorized access attempt to the Mailbox!!!''' 


#Raspberry Pi Pin utilization / i have chossen pin #19
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(19,GPIO.OUT)


#Input of USB devices interpreted as keyboard input / in this can USB-RFID Reader and USB-Barcoad Scanner
#bouth devices support keyboard input
keys = "X^1234567890XXXXqwertzuiopXXXXasdfghjklXXXXXyxcvbnmXXXXXXXXXXXXXXXXXXXXXXX"
devices = map(InputDevice, ('/dev/input/event0','/dev/input/event1'))
devices = {dev.fd: dev for dev in devices}
id_presented = "" #device defined


# Function to send sms when access was granted
def send_sms():
    response = client.send_message({'from' : '16286660020', 'to' : receiver, 'text' : message})
    response = response['messages'][0]
    
    if response['status'] == '0':
        print ('sending SMS')
    else:
        print ('Error')


# Function to send sms when access was denied
def send_sms_access_denied():
    response = client.send_message({'from' : '16286660020', 'to' : receiver, 'text' : message2})
    response = response['messages'][0]
    
    if response['status'] == '0':
        print ('sending SMS')
    else:
        print ('Error')



#Main 
while True:
        r,w,x = select(devices, [], [])
        for fd in r:
            for event in devices[fd].read():
                if event.type==1 and event.value==1:
                        if event.code==28:
                            
                                #DATABASE login authentification and user authentification
                                mydb = mysql.connector.connect(host="localhost", user="root", password="**************", database="mailbox_db")
                                mycursor=mydb.cursor(dictionary=True)
                                mycursor.execute("SELECT * FROM user_list WHERE id_code = '%s'" % (id_presented))
                                
                                #Loop to check access permision
                                for (id_code) in mycursor:
                                        #Mailbox access granted/mailbox unlocked for 4 second
                                        #sending sms
                                        print("Mailbox is unlocked for 4-sec")
                                        GPIO.output(19,GPIO.HIGH)
                                        send_sms()
                                        time.sleep(4)

                                        # Mailbox locked
                                        print("Mailbox is locked")
                                        GPIO.output(19,GPIO.LOW)
                                        #Access log created and inserted into a database        
                                        mycursor.execute("INSERT INTO access_log SET user_name = '%s', id_granted = 'granted', id_presented_datetime = NOW()" % (id_presented))
                                        mydb.commit()
                                        break
                                else:
                                        #Unathorized acces attemped/access denied/access log created and inserted into a database
                                        #sending sms 
                                        print("Access Denied.")
                                        mycursor.execute("INSERT INTO access_log SET user_name = '%s', id_granted = 'denied', id_presented_datetime = NOW()" % (id_presented))
                                        mydb.commit()
                                        send_sms_access_denied()
                                       
                                id_presented = ""
                        else:
                                id_presented += keys[ event.code ]
