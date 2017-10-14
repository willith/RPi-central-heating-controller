#!/usr/bin/env python
from shutil import copyfile
import sqlite3
from datetime import datetime, date
import dateutil.relativedelta
now = date.today()
date2 = now + dateutil.relativedelta.relativedelta(months=-1)
copyfile("/home/pi/database/centralheating.db", "/home/pi/database/archive/centralheating-%s.db" % date2)

conn=sqlite3.connect('/home/pi/database/centralheating.db')

curs=conn.cursor()

curs.execute("DELETE FROM temps WHERE tdate >= date('now', 'start of month', '-1 month') AND tdate < date('now', 'start of month')")
conn.commit()

	


conn.close()
