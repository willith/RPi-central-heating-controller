#!/usr/bin/env python
import csv
import os
import sqlite3
from datetime import datetime, date
import urllib2
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
HEATING_RELAY_PIN = 24
HOTWATER_RELAY_PIN = 23
GPIO.setup(HEATING_RELAY_PIN, GPIO.OUT)
GPIO.setup(HOTWATER_RELAY_PIN, GPIO.OUT)
# global variables

dbname='/home/pi/database/centralheating.db'

# connection to db. select values from db and hand over variables. 
conn=sqlite3.connect(dbname)
curs=conn.cursor()
for row0 in curs.execute("SELECT * FROM control WHERE rowid=1"):
	heatingset = row0[4]
	hotwaterset = row0[9]
	hotwatersetmax = row0[10]
	heating_on = row0[0]
	hotwater_on = row0[5]
conn.close()

temp = 0
switch_state = 0
relay_state = 0
solar_data = 0  	
solar_time = 0
solar_collector_temp = 0
solar_tank_temp = 0
solar_pump_running = 0
solar_pump_hrs = 0
solar_kwh = 0
empty = 0
# get boiler temp avg from tank sensors
def boilertemp(temp):	
	tfile = open("/sys/bus/w1/devices/28-011564c4c5ff/w1_slave") 
	text = tfile.read() 
	tfile.close()
	secondline = text.split("\n")[1] 
	temperaturedata = secondline.split(" ")[9]
	temperature = float(temperaturedata[2:])
	temp0 = temperature / 1000
	print temp0
	tfile = open("/sys/bus/w1/devices/28-0115649c2fff/w1_slave") 
	text = tfile.read() 
	tfile.close()
	secondline = text.split("\n")[1] 
	temperaturedata = secondline.split(" ")[9]
	temperature = float(temperaturedata[2:])
	temp1 = temperature / 1000
	print temp1
	temp = round((temp0 + temp1) /2, 2)
	return (float(temp))
	
def boilertemp_tanktop(temp):	
	tfile2 = open("/sys/bus/w1/devices/28-0115649c2fff/w1_slave") 
	text = tfile.read() 
	tfile.close()
	secondline = text.split("\n")[1] 
	temperaturedata = secondline.split(" ")[9]
	temperature = float(temperaturedata[2:])
	temp = temperature / 1000
	return (float(temp))

# get wifi sensor temps
def outdoortemp(temp):
	data = urllib2.urlopen("http://192.168.1.202")
	text = data.read()
	temp = text
	return (float(temp))
	
def indoortemp(temp):
	data = urllib2.urlopen("http://192.168.1.203")
	text = data.read()
	temp = text
	return (float(temp))	

# is boiler relay closed?

def boiler_relay(relay_state):
	if GPIO.input(24) == GPIO.input(23) == True:
		relay_state = 0
	else:
		relay_state = 1
	return (relay_state)

# is solar pump running?
	
def process_solar(solar_data):
	tmp = ""
	attempts = 0
	while tmp == "" and attempts < 6:
		os.system("python /home/pi/scripts/solar/get.py")
		tmp = os.popen("cat /home/pi/tmp/datafile | /home/pi/scripts/solar/vbusdecode3 -c 1 22,15,1,t 0,15,0.1 2,15,0.1 8,8,1 10,16,1 28,32,1").read()	
		attempts += 1
		print "getting vbus data"
	if attempts == 6:	
		print "vbus data failed"
		with open('/home/pi/tmp/solar_output.csv') as f:
			solar_data = f.read()
	else:
		f = open('/home/pi/tmp/solar_output.csv', 'w')
		f.write(tmp)
		solar_data = tmp
		print "vbus success!"
	return (solar_data)

# store everything in the database

print boiler_relay(relay_state)


solar_time, solar_collector_temp, solar_tank_temp, solar_pump_running, solar_pump_hrs, solar_kwh, empty = process_solar(solar_data).split(',')




conn=sqlite3.connect(dbname)
curs=conn.cursor()

curs.execute("INSERT INTO temps(tdate, ttime, outdoortemp, indoortemp, boilertemp, hotwater_set_temp, hotwater_set_temp_max, heating_set_temp, heating_on, hotwater_on, boiler_relay, solar_pump_running, solar_kwh, solar_tank_temp, solar_collector_temp, solar_pump_hrs) values(date('now','localtime'), time('now','localtime'), ?, ?, ?, ?, ?, ?, ?, ? ,? ,? ,? ,? ,? ,?)", (outdoortemp(temp), indoortemp(temp), boilertemp(temp), hotwaterset, hotwatersetmax, heatingset, heating_on, hotwater_on, boiler_relay(relay_state), solar_pump_running, solar_kwh, solar_tank_temp, solar_collector_temp, solar_pump_hrs))

    # commit the changes
conn.commit()

conn.close()


# run control script to reflect changes

os.system("python /home/pi/scripts/control.py")
