# RPi-central-heating-controller
Some scripts i have written to automatically control a central heating system. Measures temperature from sensors and is controlled by a web interface. Uses Google calendar for scheduling.

This is my first major project and is a work in progress. Programming is not my fortE so parts of it could do with a lot of improvement. You will need to make some modifications for it to work for you unless you copy my exact setup. For instance, the temperature sensors are arduino WiFi boards, and the Ip Address's of these sensors is hardcoded. However with some python experience it is extremely easy to modify the script yourself. I would upload the arduino program for the sensors but i unfortunately lost the file. I will write it again if i need to create another sensor. It was an extremely simple program which connected to my wifi network and published the temperature from the DS18B20 sensor over http as a string. 

You will need "at", sqlite, flask, gcalcron, and pigpio.

Hardware used:
* RPi 3 Model B (The web interface will work poorly on earlier models) running latest Raspbian with desktop gui.
* RPi 7" capacitive touch screen
* Relay board
* DS18B20 Temperature sensors
* Arduino with WiFi (or ethernet) for remote temp. sensors (Indoor and Outdoor). Alternatively you could wire these in directly to the RPi GPIO (AS i have done for the water tank)

My setup includes a solar panel controlled by a Resol Deltasol. This has a RS485 serial port for data output. You can build a circuit to connect the RS485 output to the RPi GPIO serial port. I have gathered some scripts and incorportated the data capture into this project. It is not reliant on this however and can easily be used without.



Before the scripts will run, first install the required software. I will explain breifly what each does:

* "at" - used for scheduling. You can use it in terminal to perform one-off tasks.
* sqlite - used to access the database file from python. The database stores a log of all temperatures, switch states and relays, as well as current heating/water control settings.
* flask - used to host the web interface. It is driven by Python so controls on the interface can easily run scripts.
* gcalcron - used to collect information from a google calendar for scheduling. This will require its own configuration as you will need to enable google's api on your google account and request a seperate password. My scripts will actually run without this installed but then you would be missing an essential feature of heating control! 
* pigpio - used to control the GPIO pins on the RPi for the relays.

Once the above software is installed, you simply copy the scripts to your pi's "home" folder, being sure to maintain the folder structure here.

add the following to root crontab:
```
*/2 * * * * python /home/pi/scripts/get_temps_log.py >/dev/null 2>&1
0 0 1 * * python /home/pi/scripts/db-cleanup.py >/dev/null 2>&1
```
Execute web.py as root.
