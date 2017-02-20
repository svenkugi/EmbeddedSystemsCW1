# Team RushB CW1 Python Script

## Sensor Communication and MQTT Publishing Script
- RushB.py: Main Python Script File communicating with Sensors and ESP8266 Wifi Board 

This file contains the main code that establishes I2C communication and configures the setting and mode for the following sensors:  
+ HRLV-EZ1 Ultra-Sonic Radar Sensor
+ TMP007 Infrared Thermophile Sensor
+ Si7021 Humidity Sensor
+ TSL2561 Luminosity Sensor

It also sets up the connection to the MQTT broker, whereupon the real time clock module on the EPS8266 board is first initialized with a subscription to 'esys/time'. Thereafter, sensor data is regularly collected via I2C and either filtered or processed using the statistical algorithm. Finally, the processed data (Presence, Temperature, Humidity, Brightness) is then formatted as a JSON object and regularly published to the MQTT broker. At this point, the data can then be extracted by the GUI or the cloud server. 

## GUI Application Script
- gui_mqtt.py: GUI Application displaying sensor data, collecting from MQTT Broker 
- gui_website.py: GUI Application displaying sensor data, collecting from Cloud Website

### View Modes:
1. Compact view: Minimalistic view mode relaying only the essential data
 + Displays only the live binary presence(1)/absence(0) data on the time graph 
 + Colour changing label displays the latest presence/absence status based on live data in green or red
2. Full view: Provides a detailed overview of the environment around the user.
 + Displays the live binary presence(1)/absence(0) data on the time graph
 + Displays live data on environment variables:
    + Ambient temperature
     + Humidity
      + Luminosity
             
### Functionalities:
1. Displays live presence/absence and environment data
2. Alerts the user based on following criteria
 + Time spent continuously in front of the device exceeding a preset limit
 + Environmental variables around the user exceeding preset thrsholds.
 + Note that alerts can only be switched off by obeying the instructions on the warning page

## MQTT Host Scripts
- mqttHostScripts: Contains batch script and implementation files for cloud server side connection

