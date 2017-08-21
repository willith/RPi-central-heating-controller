# RPi-central-heating-controller
Some scripts i have written to automatically control a central heating system. Measures temperature from sensors and is controlled by a web interface. Uses Google calendar for scheduling.

This is my first major project and is a work in progress. Programming is not my fortE so parts of it could do with a lot of improvement.

You will need sqlite, flask, gcalcron, glcalcli and pigpio.

Hardware used:
RPi 3 Model B (The web interface will work poorly on earlier models)
RPi 7" capacitive touch screen
Relay board
DS18B20 Temperature sensors
Arduino with WiFi (or ethernet) for remote temp. sensors (Indoor and Outdoor). Alternatively you could wire these in directly to the RPi GPIO (AS i have done for the water tank)

My setup includes a solar panel controlled by a Resol Deltasol. This has a RS485 serial port for data output. You can build a circuit to connect the RS485 output to the RPi GPIO serial port. I have gathered some scripts and incorportated the data capture into this project. It is not reliant on this however and can easily be used without.
