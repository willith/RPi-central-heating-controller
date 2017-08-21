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
for row in curs.execute("SELECT hotwater_constant, hotwater_onehour, hotwater_schedule FROM control WHERE rowid=1"):
	hotwater_constant = row[0]
	hotwater_onehour = row[1]
	hotwater_schedule = row[2]
conn.close()

# Get what action to take
action = sys.argv.pop()

if action == "off" :
	if hotwater_constant == 1:
		hotwater_schedule = 0
		if hotwater_onehour == 1:
			os.system("gcalcli --calendar 'central heating' --title 'Hotwater extra hour set' --when '" + var + "' --where '.' --duration '60' --description 'end: /usr/bin/python /home/pi/scripts/hotwater_schedule.py extrahouroff' --reminder '1' add")
	else:
		hotwater_schedule = 0
		hotwater_on = 0
		
      
elif action == "on" :
	hotwater_schedule = 1
	hotwater_on = 1
	
	if hotwater_onehour == 1:
		hotwater_onehour = 0

elif action == "extrahouroff" :
	if hotwater_schedule == 1:
		hotwater_onehour = 0
	
	else:
		hotwater_onehour = 0
		if hotwater_constant == 0:
			hotwater_on = 0
			
conn=sqlite3.connect(dbname)
curs=conn.cursor()
curs.execute("UPDATE control SET hotwater_on = ?, hotwater_schedule = ?, hotwater_onehour = ? WHERE rowid = ?", (hotwater_on, hotwater_schedule, hotwater_onehour, 1))
conn.commit()
conn.close()			
os.system("python /home/pi/scripts/control.py")
