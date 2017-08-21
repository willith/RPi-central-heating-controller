from flask import Flask, render_template, request, jsonify
import RPi.GPIO as GPIO
import time
import os
import subprocess

import sqlite3

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
	figures = latest[2],latest[3],latest[4],latest[10],latest[11],avg[0],daily_kwh[0],schedule[0],schedule[1]
		
		
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
 #       fo = open("/home/pi/switches/heating_switch_on", "wb")
 
        
    elif state=="disarmed":
        heating_on = 0
 
#        os.remove("/home/pi/switches/heating_switch_on")
#        if os.path.isfile("/home/pi/switches/heating_constant") == True:
        if heating_constant == 1:
            heating_constant = 0
#            os.remove("/home/pi/switches/heating_constant")
#        elif os.path.isfile("/home/pi/switches/heating_extrahour") == True:
#            os.remove("/home/pi/switches/heating_extrahour")
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
#         if os.path.isfile("/home/pi/switches/heating_switch_on") == True:
            state = "armed"
        else:
            state = "disarmed"
    conn.close()
    return jsonify(buttonState=state)

# +1 hour for heating. Heating relay is closed and file is created.
@app.route("/_heatingonehour")
def _heatingonehour():
    state = request.args.get('state')
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT heating_constant, heating_schedule FROM control WHERE rowid=1"):
        heating_constant = row[0]
        heating_schedule = row[1]	
    conn.close()
    if state=="armed":
        if heating_constant == 0:
            heating_on = 1
            heating_onehour = 1
            if heating_schedule == 0:
			
#        if os.path.isfile("/home/pi/switches/heating_constant") == False:
#             fo = open("/home/pi/switches/heating_switch_on", "wb")
#             fo = open("/home/pi/switches/heating_extrahour", "wb")    
#             if os.path.isfile("/home/pi/schedule/heating_schedule_on") == False:
                os.system("gcalcli --calendar 'central heating' --title 'Heating extra hour set' --when '" + var + "' --where '.' --duration '60' --description 'end: /usr/bin/python /home/pi/scripts/heating_schedule.py extrahouroff' --reminder '1' add")
        
        
    elif state=="disarmed":
        heating_onehour = 0		
        if heating_schedule == 0:
            heating_on = 0
#        if os.path.isfile("/home/pi/switches/heating_extrahour") == True:
#            os.remove("/home/pi/switches/heating_extrahour")
#            if os.path.isfile("/home/pi/schedule/heating_schedule_on") == False:
#                os.remove("/home/pi/switches/heating_switch_on")	
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    curs.execute("UPDATE control SET heating_on = ?, heating_onehour = ? WHERE rowid = ?", (heating_on, heating_onehour, 1))
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
        if heating_onehour == 1:
		    heating_onehour = 0
#         fo = open("/home/pi/switches/heating_constant", "wb")
 #        if os.path.isfile("/home/pi/switches/heating_extrahour") == True:
#             os.remove("/home/pi/switches/heating_extrahour")
    elif state=="disarmed":
        heating_constant = 0
        if heating_schedule == 0 and heating_onehour == 0:
            heating_on = 0
#         os.remove("/home/pi/switches/heating_constant")
#         if os.path.isfile("/home/pi/schedule/heating_schedule_on") == False and os.path.isfile("/home/pi/switches/heating_extrahour") == False:
# 		os.remove("/home/pi/switches/heating_switch_on")
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
#    f = open('/home/pi/switches/set_heating_temp', "w")
#    f.write(state)
#    f.close()
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
#         if os.path.isfile("/home/pi/switches/heating_switch_on") == True:
            state = "armed"
        else:
            state = "disarmed"
    conn.close()
    return jsonify(buttonState=state)
	
#    if os.path.isfile("/home/pi/switches/heating_extrahour") == True:
#        state = "armed"
#    else:
#        state = "disarmed"
#    return jsonify(buttonState=state)

# ajax GET call this function periodically to read button state
# the state is sent back as json data
@app.route("/_heatingconstantbutton")
def _heatingconstantbutton():
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT heating_constant FROM control WHERE rowid=1"):
        if row[0] == 1:	
 #       if os.path.isfile("/home/pi/switches/heating_constant") == True:
            state = "armed"
        else:
            state = "disarmed"
    conn.close()
    return jsonify(buttonState=state)

# set heating temp slider state
@app.route("/_setheatingtempslider")
def _setheatingtempslider():
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT heating_temp_set FROM control WHERE rowid=1"):
        state = row[0]
        		
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
#        fo = open("/home/pi/switches/hotwater_switch_on", "wb")
       	
        
    elif state=="disarmed":
        hotwater_on = 0
        if hotwater_constant == 1:
            hotwater_constant = 0
        elif hotwater_onehour == 1:
            hotwater_onehour = 0		
#        os.remove("/home/pi/switches/hotwater_switch_on")
#        if os.path.isfile("/home/pi/switches/hotwater_constant") == True:
#            os.remove("/home/pi/switches/hotwater_constant")
#        elif os.path.isfile("/home/pi/switches/hotwater_extrahour") == True:
#            os.remove("/home/pi/switches/hotwater_extrahour")
    
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
    state = request.args.get('state')
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT hotwater_constant, hotwater_schedule FROM control WHERE rowid=1"):
        hotwater_constant = row[0]
        hotwater_schedule = row[1]	
    conn.close()
    if state=="armed":
        if hotwater_constant == 0:
            hotwater_on = 1
            hotwater_onehour = 1
            if hotwater_schedule == 0:
                os.system("gcalcli --calendar 'central heating' --title 'Hotwater extra hour set' --when '" + var + "' --where '.' --duration '60' --description 'end: /usr/bin/python /home/pi/scripts/hotwater_schedule.py extrahouroff' --reminder '1' add")
        
        
    elif state=="disarmed":
        hotwater_onehour = 0		
        if hotwater_schedule == 0:
            hotwater_on = 0
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    curs.execute("UPDATE control SET hotwater_on = ?, hotwater_onehour = ? WHERE rowid = ?", (hotwater_on, hotwater_onehour, 1))
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
    f = open('/home/pi/switches/set_hotwater_temp', "w")
    f.write(state)
    f.close()
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    curs.execute("UPDATE control SET hotwater_temp_set = ? WHERE rowid = ?", (state, 1))
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
@app.route("/_setwatertempslider")
def _setwatertempslider():
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT hotwater_temp_set FROM control WHERE rowid=1"):
        state = row[0]
        		
    return jsonify(buttonState=state)	
	
	

@app.route("/_boileroverride")
def _boileroverride():
    state = request.args.get('state')
    if state=="armed":
        boiler_override = 1	
#        fo = open("/home/pi/switches/boiler_override", "wb")
	
        
    elif state=="disarmed":
        boiler_override = 0
#        os.remove("/home/pi/switches/boiler_override")
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
	
# read indoor temperature
@app.route("/_readindoortemp")
def _readindoortemp():
    readindoortemp = database(figures)[1]
        		
    return jsonify(readindoortemp=readindoortemp)	
	
# read outdoor temperature
@app.route("/_readoutdoortemp")
def _readoutdoortemp():
    readoutdoortemp = database(figures)[0]
        		
    return jsonify(readoutdoortemp=readoutdoortemp)

# read boiler temperature
@app.route("/_readboilertemp")
def _readboilertemp():
	
	if database(figures)[2] < 35:
		readboilertemp = """
		<font color = "blue">%s</font>
		""" %(database(figures)[2])
	else:
		readboilertemp = database(figures)[2]   		
	return jsonify(readboilertemp=readboilertemp)	

# read solar kwh
@app.route("/_readsolarkwh")
def _readsolarkwh():
    readsolarkwh = database(figures)[4] - database(figures)[6]
        		
    return jsonify(readsolarkwh=readsolarkwh)
	
# boiler temp increasing/decreasing
@app.route("/_boilertemprate")
def _boilertemprate():
	if database(figures)[5]/6 >= database(figures)[2]+0.5: 
		boilertemprate='<img src="/static/down_arrow.png" width="20" height="20" />'
	elif database(figures)[5]/6 <= database(figures)[2]-0.5:
		boilertemprate='<img src="/static/up_arrow.png" width="20" height="20" />'
	else:
		boilertemprate='--'
	return jsonify(boilertemprate=boilertemprate)

	# boiler status
@app.route("/_boilerstatus")
def _boilerstatus():
    if GPIO.input(24) == GPIO.input(23) == True:
        boilerstatus='<img src="/static/boiler_off.png" width="100" height="100" />'
    else:
        boilerstatus='<img src="/static/boiler_on.png" width="100" height="100" />'
    return jsonify(boilerstatus=boilerstatus)
	
# solar status
@app.route("/_solarstatus")
def _solarstatus():
    pumprunningbool = database(figures)[3]
    if bool(pumprunningbool) == True:
            solarstatus='<img src="/static/solarpump_on.png" width="100" height="100" />'
    else:
            solarstatus='<img src="/static/solarpump_off.png" width="100" height="100" />'
    return jsonify(solarstatus=solarstatus)
	
# heating schedule indicator
@app.route("/_heatingscheduleindicator")
def _heatingscheduleindicator():
    if database(figures)[7] == 1:
#    if os.path.isfile("/home/pi/schedule/heating_schedule_on") == True:
        heatingscheduleindicator='<img src="/static/schedule_on.png" width="30" height="30" />'
    else:
        heatingscheduleindicator='<img src="/static/schedule_off.png" width="30" height="30" />'
    return jsonify(heatingscheduleindicator=heatingscheduleindicator)

# water schedule indicator
@app.route("/_waterscheduleindicator")
def _waterscheduleindicator():
    if database(figures)[8] == 1:
#    if os.path.isfile("/home/pi/schedule/hotwater_schedule_on") == True:
        waterscheduleindicator='<img src="/static/schedule_on.png" width="30" height="30" />'
    else:
        waterscheduleindicator='<img src="/static/schedule_off.png" width="30" height="30" />'
    return jsonify(waterscheduleindicator=waterscheduleindicator)	

	
# run the webserver on standard port 80, requires sudo
if __name__ == "__main__":
    
    app.run(host='0.0.0.0', port=80, debug=False, threaded=True)
