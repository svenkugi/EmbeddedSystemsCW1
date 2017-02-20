# Main Python Script to be run on EPS8266 Board



## EPS8266 Implementation Scripts 
- RushB.py: Main Python Script File communicating with Sensors and ESP8266 Wifi Board 

## Local GUI Application
- gui_mqtt.py: GUI Application displaying sensor data, collecting from MQTT Broker 
- gui_website.py: GUI Application displaying sensor data, collecting from Cloud Website

#### View Modes:
1. Compact view: Minimalistic view mode relaying only the essential data
 + Displays only the live binary presence(1)/absence(0) data on the time graph 
 + Colour changing label displays the latest presence/absence status based on live data in green or red
2. Full view: Provides a detailed overview of the environment around the user.
 + Displays the live binary presence(1)/absence(0) data on the time graph
 + Displays live data on environment variables:
  ⋅⋅* Ambient temperature
  ⋅⋅* Humidity
  ⋅⋅* Luminosity
             
### Functionalities:
1. Displays live presence/absence and environment data
2. Alerts the user based on following criteria
 + Time spent continuously in front of the device exceeding a preset limit
 + Environmental variables around the user exceeding preset thrsholds.
 + Note that alerts can only be switched off by obeying the instructions on the warning page

## MQTT Host Scripts 
- mqttHostScripts: Contains batch script and implementation files for cloud server side connection

