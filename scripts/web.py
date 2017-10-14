
from flask import Flask, render_template, request, jsonify
import RPi.GPIO as GPIO
import time
import os
import subprocess
import json
import sqlite3
import re
import sys
from datetime import datetime, date
app = Flask(__name__)
GPIO.setwarnings(False)

dbname='/home/pi/database/centralheating.db'

var = (time.strftime("%m/%d/%Y %H:%M"))

avg = 0
latest = 0
figures = 0
heating_on = 0


# Identify which pin controls the relays
HEATING_RELAY_PIN = 24
HOTWATER_RELAY_PIN = 23

# Set pins as outputs
GPIO.setmode(GPIO.BCM)
GPIO.setup(HEATING_RELAY_PIN, GPIO.OUT)
GPIO.setup(HOTWATER_RELAY_PIN, GPIO.OUT)


# return index page when IP address of RPi is typed in the browser
@app.route("/")
def Index():
	
	return render_template("index.html")
	
@app.route("/data.json")
def data():
    connection = sqlite3.connect(dbname)
    cursor = connection.cursor()
    cursor.execute("SELECT ttime, outdoortemp FROM temps WHERE tdate>=date('now') ORDER BY ttime")
    results = cursor.fetchall()
    
    return json.dumps(results)
	
@app.route("/graph")
def graph():
    return render_template("graph.html")	
	
def database(figures):
	conn=sqlite3.connect(dbname)
	curs=conn.cursor()
	for row in curs.execute("SELECT * FROM temps ORDER BY tdate DESC, ttime DESC LIMIT 1"):
		latest = row
	for row2 in curs.execute("SELECT SUM(boilertemp) FROM (SELECT boilertemp FROM temps ORDER BY tdate DESC, ttime DESC LIMIT 6)"):
		avg = row2
	for row3 in curs.execute("SELECT solar_kwh FROM temps WHERE tdate>=date('now','-1 day') ORDER BY tdate DESC, ttime DESC LIMIT 1"):	
		daily_kwh = row3
	for row4 in curs.execute("SELECT heating_schedule, hotwater_schedule FROM control WHERE rowid=1"):
		schedule = row4
	figures = latest[2],latest[3],latest[4],latest[11],latest[12],avg[0],daily_kwh[0],schedule[0],schedule[1]
		
		
	conn.close()
	return (figures)
	




# ajax GET call this function to set heating relay state
# depeding on the GET parameter sent
@app.route("/_led")
def _led():
    state = request.args.get('state')
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT heating_on, heating_constant, heating_onehour FROM control WHERE rowid=1"):
        heating_on = row[0]	
        heating_constant = row[1]
        heating_onehour = row[2]
    conn.close()
    if state=="armed":
        heating_on = 1   
    elif state=="disarmed":
        heating_on = 0
        if heating_constant == 1:
            heating_constant = 0
        elif heating_onehour == 1:
            heating_onehour = 0 
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    curs.execute("UPDATE control SET heating_on = ?, heating_constant = ?, heating_onehour = ? WHERE rowid = ?", (heating_on, heating_onehour, heating_constant, 1))
    conn.commit()
    conn.close()
    os.system("python /home/pi/scripts/control.py")
    return ""
	
# ajax GET call this function periodically to read button state
# the state is sent back as json data
@app.route("/_button")
def _button():
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT heating_on, heating_constant, heating_onehour FROM control WHERE rowid=1"):
        if row[0] == 1:
            state = "armed"
        else:
            state = "disarmed"
    conn.close()
    return jsonify(buttonState=state)

# +1 hour for heating
@app.route("/_heatingonehour")
def _heatingonehour():
    heating_on = None
    state = request.args.get('state')
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT heating_constant, heating_schedule, heating_onehour_jobid FROM control WHERE rowid=1"):
        heating_constant = row[0]
        heating_schedule = row[1]
        heating_onehour_jobid = row[2]		
    conn.close()
    if state=="armed":
        if not any ((heating_constant, heating_schedule)): 
            heating_on = 1
            heating_onehour = 1
            sched_cmd = ['at', 'now + 1 hour']
            command = 'python /home/pi/scripts/heating_schedule.py extrahouroff'
            p = subprocess.Popen(sched_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdout, stderr) = p.communicate(command)
            jobid = re.compile('(\d+)').search(stderr)
            heating_onehour_jobid = jobid.group(0)
        elif heating_schedule == 1:
            heating_onehour = 1 			
    elif state=="disarmed":
        heating_onehour = 0	
        sched_cmd = ['atrm', str(heating_onehour_jobid)]
        command = '%s %s '	
        p = subprocess.Popen(sched_cmd, stdin=subprocess.PIPE)
        p.communicate(command)		
        if not any ((heating_constant, heating_schedule)):       
            heating_on = 0
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    curs.execute("UPDATE control SET heating_on = coalesce(?, heating_on), heating_onehour = ?, heating_onehour_jobid = ? WHERE rowid = ?", (heating_on, heating_onehour, heating_onehour_jobid, 1))
    conn.commit()
    conn.close()			
    os.system("python /home/pi/scripts/control.py")
    return ""
	
# Heating constant on. Only user intervention will turn it off.
@app.route("/_heatingconstant")
def _heatingconstant():
    state = request.args.get('state')
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT heating_on, heating_constant, heating_onehour, heating_schedule FROM control WHERE rowid=1"):
        heating_on = row[0]	
        heating_constant = row[1]
        heating_onehour = row[2]
        heating_schedule = row[3]		
    conn.close()
    if state=="armed":
        heating_constant = 1
        heating_on = 1
        if heating_onehour == 1:
		    heating_onehour = 0
    elif state=="disarmed":
        heating_constant = 0
        if heating_schedule == 0 and heating_onehour == 0:
            heating_on = 0
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    curs.execute("UPDATE control SET heating_constant = ?, heating_on = ?, heating_onehour = ? WHERE rowid = ?", (heating_constant, heating_on, heating_onehour, 1))
    conn.commit()
    conn.close()
    os.system("python /home/pi/scripts/control.py")
    return ""
	
# get heat temp slider state
@app.route("/_setheatingtemp")
def _setheatingtemp():
    state = request.args.get('state')
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    curs.execute("UPDATE control SET heating_temp_set = ? WHERE rowid = ?", (state, 1))
    conn.commit()
    conn.close()
    os.system("python /home/pi/scripts/control.py")
    return ""	
	
	
	

	
	

	
# ajax GET call this function periodically to read button state
# the state is sent back as json data
@app.route("/_extrahourbutton")
def _extrahourbutton():
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT heating_on, heating_constant, heating_onehour FROM control WHERE rowid=1"):
        if row[2] == 1:
            state = "armed"
        else:
            state = "disarmed"
    conn.close()
    return jsonify(buttonState=state)

# ajax GET call this function periodically to read button state
# the state is sent back as json data
@app.route("/_heatingconstantbutton")
def _heatingconstantbutton():
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT heating_constant FROM control WHERE rowid=1"):
        if row[0] == 1:	
            state = "armed"
        else:
            state = "disarmed"
    conn.close()
    return jsonify(buttonState=state)


	

# ajax GET call this function to set water relay state
# depeding on the GET parameter sent
@app.route("/_hotwater")
def _hotwater():
    state = request.args.get('state')
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT hotwater_on, hotwater_constant, hotwater_onehour FROM control WHERE rowid=1"):
        hotwater_on = row[0]	
        hotwater_constant = row[1]
        hotwater_onehour = row[2]
    conn.close()
    if state=="armed":
        hotwater_on = 1
    elif state=="disarmed":
        hotwater_on = 0
        if hotwater_constant == 1:
            hotwater_constant = 0
        elif hotwater_onehour == 1:
            hotwater_onehour = 0		
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    curs.execute("UPDATE control SET hotwater_on = ?, hotwater_constant = ?, hotwater_onehour = ? WHERE rowid = ?", (hotwater_on, hotwater_constant, hotwater_onehour, 1))
    conn.commit()
    conn.close()
    os.system("python /home/pi/scripts/control.py")
    return ""

# +1 hour for hot water. Hot water relay is closed and file is created.
@app.route("/_hotwateronehour")
def _hotwateronehour():
    hotwater_on = None
    state = request.args.get('state')
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT hotwater_constant, hotwater_schedule, hotwater_onehour_jobid FROM control WHERE rowid=1"):
        hotwater_constant = row[0]
        hotwater_schedule = row[1]
        hotwater_onehour_jobid = row[2]		
    conn.close()
    if state=="armed":
        if not any ((hotwater_constant, hotwater_schedule)): 
            hotwater_on = 1
            hotwater_onehour = 1
            sched_cmd = ['at', 'now + 1 hour']
            command = 'python /home/pi/scripts/hotwater_schedule.py extrahouroff'
            p = subprocess.Popen(sched_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdout, stderr) = p.communicate(command)
            jobid = re.compile('(\d+)').search(stderr)
            hotwater_onehour_jobid = jobid.group(0)
        elif hotwater_schedule == 1:
            hotwater_onehour = 1 	
    elif state=="disarmed":
        hotwater_onehour = 0	
        sched_cmd = ['atrm', str(hotwater_onehour_jobid)]
        command = '%s %s '	
        p = subprocess.Popen(sched_cmd, stdin=subprocess.PIPE)
        p.communicate(command)		
        if not any ((hotwater_constant, hotwater_schedule)):       
            hotwater_on = 0
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    curs.execute("UPDATE control SET hotwater_on = coalesce(?, hotwater_on), hotwater_onehour = ?, hotwater_onehour_jobid = ? WHERE rowid = ?", (hotwater_on, hotwater_onehour, hotwater_onehour_jobid, 1))
    conn.commit()
    conn.close()				
    os.system("python /home/pi/scripts/control.py")
    return ""

# Hot water constant on. Only user intervention will turn it off.
@app.route("/_hotwaterconstant")
def _hotwaterconstant():
    state = request.args.get('state')
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT hotwater_on, hotwater_constant, hotwater_onehour, hotwater_schedule FROM control WHERE rowid=1"):
        hotwater_on = row[0]	
        hotwater_constant = row[1]
        hotwater_onehour = row[2]
        hotwater_schedule = row[3]		
    conn.close()
    if state=="armed":
        hotwater_constant = 1
        hotwater_on = 1
        if hotwater_onehour == 1:
		    hotwater_onehour = 0
    elif state=="disarmed":
        hotwater_constant = 0
        if hotwater_schedule == 0 and hotwater_onehour == 0:
            hotwater_on = 0
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    curs.execute("UPDATE control SET hotwater_constant = ?, hotwater_on = ?, hotwater_onehour = ? WHERE rowid = ?", (hotwater_constant, hotwater_on, hotwater_onehour, 1))
    conn.commit()
    conn.close()
    os.system("python /home/pi/scripts/control.py")
    return ""

	# get water temp slider state
@app.route("/_setwatertemp")
def _setwatertemp():
    state = request.args.get('state')
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    curs.execute("UPDATE control SET hotwater_temp_set = ? WHERE rowid = ?", (state, 1))
    conn.commit()
    conn.close()
    os.system("python /home/pi/scripts/control.py")
    return ""	
	
@app.route("/_setwatertempmax")
def _setwatertempmax():
    state = request.args.get('state')
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    curs.execute("UPDATE control SET hotwater_temp_set_max = ? WHERE rowid = ?", (state, 1))
    conn.commit()
    conn.close()
    os.system("python /home/pi/scripts/control.py")
    return ""		

# ajax GET call this function periodically to read button state
# the state is sent back as json data
@app.route("/_hotwaterbutton")
def _hotwaterbutton():
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT hotwater_on FROM control WHERE rowid=1"):
        if row[0] == 1:
            state = "armed"
        else:
            state = "disarmed"
    conn.close()
    return jsonify(buttonState=state)

# ajax GET call this function periodically to read button state
# the state is sent back as json data
@app.route("/_hotwaterextrahourbutton")
def _hotwaterextrahourbutton():
    
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT hotwater_onehour FROM control WHERE rowid=1"):
        if row[0] == 1:
            state = "armed"
        else:
            state = "disarmed"
    conn.close()
    return jsonify(buttonState=state)
	
# ajax GET call this function periodically to read button state
# the state is sent back as json data
@app.route("/_hotwaterconstantbutton")
def _hotwaterconstantbutton():
    
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT hotwater_constant FROM control WHERE rowid=1"):
        if row[0] == 1:
            state = "armed"
        else:
            state = "disarmed"
    conn.close()
    return jsonify(buttonState=state)

	# read water temp slider
@app.route("/_setslider")
def _setslider():
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT hotwater_temp_set, hotwater_temp_set_max, heating_temp_set FROM control WHERE rowid=1"):
        state = row[0]
        state1 = row[1]
        state2 = row[2]
    conn.close()    		
    return jsonify(buttonState=state, buttonState1=state1, buttonState2=state2)	
	

@app.route("/_boileroverride")
def _boileroverride():
    state = request.args.get('state')
    if state=="armed":
        boiler_override = 1	
    elif state=="disarmed":
        boiler_override = 0
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    curs.execute("UPDATE control SET boiler_override = ? WHERE rowid = ?", (boiler_override, 1))
    conn.commit()
    conn.close()
    os.system("python /home/pi/scripts/control.py")    
    return ""



	
@app.route("/_boileroverridebutton")
def _boileroverridebutton():
    
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT boiler_override FROM control WHERE rowid=1"):
        if row[0] == 1:
            state = "armed"
        else:
            state = "disarmed"
    conn.close()
    return jsonify(buttonState=state)	
	
###########################################SENSORS/EXTERNAL################################################	
	
# read variables
@app.route("/_readtemp")
def _readtemp():
	pumprunningbool = database(figures)[3]
	if database(figures)[1] < 14:
		readindoortemp = """
		<font color = "blue">%s</font>
		""" %(database(figures)[1])
	else:
		readindoortemp = database(figures)[1]
	if database(figures)[0] < 14:
			readoutdoortemp = """
		<font color = "blue">%s</font>
		""" %(database(figures)[0])
	else: 
		readoutdoortemp = database(figures)[0] 
	if database(figures)[2] < 35:
		readboilertemp = """
		<font color = "blue">%s</font>
		""" %(database(figures)[2])
	else:
		readboilertemp = database(figures)[2]	
	readsolarkwh = database(figures)[4] - database(figures)[6]
	if database(figures)[5]/6 >= database(figures)[2]+0.3: 
		boilertemprate='<img src="/static/down_arrow.png" width="20" height="20" />'
	elif database(figures)[5]/6 <= database(figures)[2]-0.3:
		boilertemprate='<img src="/static/up_arrow.png" width="20" height="20" />'
	else:
		boilertemprate='--'
	if GPIO.input(24) == GPIO.input(23) == True:
		boilerstatus='<img src="/static/boiler_off.png" width="100" height="100" />'
	else:
		boilerstatus='<img src="/static/boiler_on.png" width="100" height="100" />'
	if bool(pumprunningbool) == True:
			solarstatus='<img src="/static/solarpump_on.png" width="100" height="100" />'
	else:
			solarstatus='<img src="/static/solarpump_off.png" width="100" height="100" />'
	if database(figures)[7] == 1:
		heatingscheduleindicator='<img src="/static/schedule_on.png" width="30" height="30" />'
	else:
		heatingscheduleindicator='<img src="/static/schedule_off.png" width="30" height="30" />'
	if database(figures)[8] == 1:
		waterscheduleindicator='<img src="/static/schedule_on.png" width="30" height="30" />'
	else:
		waterscheduleindicator='<img src="/static/schedule_off.png" width="30" height="30" />'
	return jsonify(readindoortemp=readindoortemp, readoutdoortemp=readoutdoortemp, readboilertemp=readboilertemp, readsolarkwh=readsolarkwh, boilertemprate=boilertemprate, boilerstatus=boilerstatus, solarstatus=solarstatus, heatingscheduleindicator=heatingscheduleindicator, waterscheduleindicator=waterscheduleindicator)	
	

	
# run the webserver on standard port 80, requires sudo
if __name__ == "__main__":
    
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)

