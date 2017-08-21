# William Cook 2017
import sqlite3
import os
import RPi.GPIO as GPIO
GPIO.setwarnings(False)





dbname='/home/pi/database/centralheating.db'

# connection to db. select values from db and hand over variables. 
conn=sqlite3.connect(dbname)
curs=conn.cursor()
for row in curs.execute("SELECT SUM(boilertemp) FROM (SELECT boilertemp FROM temps ORDER BY tdate DESC, ttime DESC LIMIT 6)"):
	boilertemp_avg = row[0]	
for row2 in curs.execute("SELECT * FROM temps ORDER BY tdate DESC, ttime DESC LIMIT 1"):
	temps = row2
for row3 in curs.execute("SELECT * FROM control WHERE rowid=1"):
	control = row3
conn.close()

print temps
print control
### temps tuple id ###
#tdate = 0
#ttime = 1
#outdoortemp = 2
#indoortemp = 3
#boilertemp = 4
#hotwater_set_temp = 5
#heating_set_temp = 6
#heating_on = 7
#hotwater_on = 8
#boiler_relay = 9
#solar_pump_running = 10
#solar_kwh = 11

### control tuple id ###
#heating_on = 0
#heating_onehour = 1
#heating_constant = 2
#heating_schedule = 3
#heating_temp_set = 4
#hotwater_on = 5
#hotwater_onehour = 6
#hotwater_constant = 7
#hotwater_schedule = 8
#hotwater_temp_set = 9
#boiler_override = 10

# Identify which pin controls the relays
HEATING_RELAY_PIN = 24
HOTWATER_RELAY_PIN = 23

# Set pins as outputs
GPIO.setmode(GPIO.BCM)
GPIO.setup(HEATING_RELAY_PIN, GPIO.OUT)
GPIO.setup(HOTWATER_RELAY_PIN, GPIO.OUT)

	
	



	




if control[10] == 0:
	print "boiler override off"



	if control[0] == 1 :
		print "heating on"
		if temps[3] <= control[4]:
			print "indoor temp low! relay closed"
			GPIO.output(HEATING_RELAY_PIN, GPIO.LOW)
			
		elif temps[3] >= control[4]:
			print "indoor temp high"
			GPIO.output(HEATING_RELAY_PIN, GPIO.HIGH)
			
	elif control[0] == 0 :
		print "heating off"
		GPIO.output(HEATING_RELAY_PIN, GPIO.HIGH)
		
	if control[5] == 1 :
		if temps[4] < control[9]:
			GPIO.output(HOTWATER_RELAY_PIN, GPIO.LOW)
			
		elif temps[4] >= control[9]:
			GPIO.output(HOTWATER_RELAY_PIN, GPIO.HIGH)
			
	elif control[5] == 0 :
		GPIO.output(HOTWATER_RELAY_PIN, GPIO.HIGH)	
	
else:
	
	if control[0] == 1 :
		if temps[3] <= control[4]:
			GPIO.output(HEATING_RELAY_PIN, GPIO.LOW)
			
		elif temps[3] >= control[4]:
			GPIO.output(HEATING_RELAY_PIN, GPIO.HIGH)
			
	elif control[0] == 0 :
		GPIO.output(HEATING_RELAY_PIN, GPIO.HIGH)
		
	if control[5] == 1 :
		while temps[10] == 1:
			if boilertemp_avg < control[9] - 10:
				# give solar panel a helping hand 
				GPIO.output(HOTWATER_RELAY_PIN, GPIO.LOW)
			
			elif boilertemp_avg > control[9] - 10:
				GPIO.output(HOTWATER_RELAY_PIN, GPIO.HIGH)
		else: 
			if temps[4] < control[9]:
				GPIO.output(HOTWATER_RELAY_PIN, GPIO.LOW)
			
			elif temps[4] >= control[9]:
				GPIO.output(HOTWATER_RELAY_PIN, GPIO.HIGH)
		
	elif control[5] == 0 :
		GPIO.output(HOTWATER_RELAY_PIN, GPIO.HIGH)
