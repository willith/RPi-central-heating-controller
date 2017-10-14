#!/usr/bin/env python
import sys
import os.path
import os
import subprocess
import sqlite3
import re

hotwater_on = None
hotwater_onehour_jobid = 0
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
	hotwater_schedule = 0
	if hotwater_onehour == 1:
		sched_cmd = ['at', 'now + 1 hour']
		command = 'python /home/pi/scripts/hotwater_schedule.py extrahouroff'
		p = subprocess.Popen(sched_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdout, stderr) = p.communicate(command)
		jobid = re.compile('(\d+)').search(stderr)
		hotwater_onehour_jobid = jobid.group(0)
		
	elif hotwater_constant == 0:
		hotwater_on = 0
		
      
elif action == "on" :
	hotwater_schedule = 1
	hotwater_on = 1
	
	if hotwater_onehour == 1:
		hotwater_onehour = 0

elif action == "extrahouroff" :
	if not any ((hotwater_schedule, hotwater_constant)):
		hotwater_onehour = 0
		hotwater_on = 0
	
	else:
		hotwater_onehour = 0
			
conn=sqlite3.connect(dbname)
curs=conn.cursor()
curs.execute("UPDATE control SET hotwater_on = coalesce(?, hotwater_on), hotwater_schedule = ?, hotwater_onehour = ?, hotwater_onehour_jobid = ? WHERE rowid = ?", (hotwater_on, hotwater_schedule, hotwater_onehour, hotwater_onehour_jobid, 1))
conn.commit()
conn.close()			
os.system("python /home/pi/scripts/control.py")
