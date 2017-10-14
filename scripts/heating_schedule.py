#!/usr/bin/env python
import sys
import os.path
import os
import subprocess
import sqlite3
import re

heating_on = None
heating_onehour_jobid = 0
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
	heating_schedule = 0
	
	if heating_onehour == 1:
		sched_cmd = ['at', 'now + 1 hour']
		command = 'python /home/pi/scripts/heating_schedule.py extrahouroff %s %s'
		p = subprocess.Popen(sched_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdout, stderr) = p.communicate(command)
		jobid = re.compile('(\d+)').search(stderr)
		heating_onehour_jobid = jobid.group(0)
		
	elif heating_constant == 0:
		heating_on = 0
		
		
		
      
elif action == "on" :
	heating_schedule = 1
	heating_on = 1
	
	if heating_onehour == 1:
		heating_onehour = 0

elif action == "extrahouroff" :
	
	if not any ((heating_schedule, heating_constant)):
		heating_onehour = 0
		heating_on = 0
	
	else:
		heating_onehour = 0
			
conn=sqlite3.connect(dbname)
curs=conn.cursor()
curs.execute("UPDATE control SET heating_on = coalesce(?, heating_on), heating_schedule = ?, heating_onehour = ?, heating_onehour_jobid = ? WHERE rowid = ?", (heating_on, heating_schedule, heating_onehour, heating_onehour_jobid, 1))
conn.commit()
conn.close()			
os.system("python /home/pi/scripts/control.py")
