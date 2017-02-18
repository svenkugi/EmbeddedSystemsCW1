# MQTT scripts to be run on the host
Windows batch scripts automate the starting of the mosquitto MQTT server and the relevant python scripts.

### High-level scripts
- RUN.bat:	Starts the host by starting a mosquitto server and the python host script
- CAL.bat:	Sends a message over MQTT to device to start calibration
- EXIT.bat:	Sends a message over MQTT to device to exit program

### Implementation scripts
- mqttHost.py: 	Main host script, manages input from MQTT and uploads data to cloud
- mqttDebug.py: In the same vein, receives debug data and formats it (for test calibration)
- testREST.py: 	Allows you to fabricate a data message and uploads data to cloud