#!/usr/bin/env python
import sys
import os.path
import os
import subprocess
import sqlite3




dbname='/home/pi/database/centralheating.db'

# connection to db. select values from db and hand over variables. 
conn=sqlite3.connect(dbname)
curs=conn.cursor()
for row in curs.execute("SELECT heating_constant, heating_onehour, heating_schedule FROM control WHERE rowid=1"):
	heating_constant = row[0]
	heating_onehour = row[1]
	heating_schedule = row[2]
conn.close()

# Get what action to take
action = sys.argv.pop()

if action == "off" :
	if heating_constant == 1:
		heating_schedule = 0
		if heating_onehour == 1:
			os.system("gcalcli --calendar 'central heating' --title 'Heating extra hour set' --when '" + var + "' --where '.' --duration '60' --description 'end: /usr/bin/python /home/pi/scripts/heating_schedule.py extrahouroff' --reminder '1' add")
	else:
		heating_schedule = 0
		heating_on = 0
		
      
elif action == "on" :
	heating_schedule = 1
	heating_on = 1
	
	if heating_onehour == 1:
		heating_onehour = 0

elif action == "extrahouroff" :
	if heating_schedule == 1:
		heating_onehour = 0
	
	else:
		heating_onehour = 0
		if heating_constant == 0:
			heating_on = 0
			
conn=sqlite3.connect(dbname)
curs=conn.cursor()
curs.execute("UPDATE control SET heating_on = ?, heating_schedule = ?, heating_onehour = ? WHERE rowid = ?", (heating_on, heating_schedule, heating_onehour, 1))
conn.commit()
conn.close()			
os.system("python /home/pi/scripts/control.py")
