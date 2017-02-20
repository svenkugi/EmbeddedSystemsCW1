# Team RushB CW1 Python Scripts

## Sensor Communication and MQTT Publishing Script

- **RushB.py**: Main Python Script File communicating with sensors and ESP8266 Wifi Board 

### Functionalities 

1. Establishes I2C communication and configures the setting and mode for the following sensors 
 + HRLV-EZ1 Ultra-Sonic Radar Sensor
 + TMP007 Infrared Thermophile Sensor
 + Si7021 Humidity Sensor
 + TSL2561 Luminosity Sensor

2. Initializes and sets up connection to the MQTT broker 
 + Connection to MQTT Broker 'EEE Rover'
 + Real Time Clock module on the EPS8266 board initialized with a subscription to 'esys/time'

3. Reading and Processing of Sensor Data 
 + All Data is read from the I2C bus 
 + Brightness and Temperature Data is filtered using Moving Average Digital Filter 
 + Distance and Infrared Data is further processed using statistical algorithm to identify presence

4. Publishing of Data to MQTT Broker
 + Presence, Temperature, Humidity, Brightness along with time stamp is formatted as a JSON object
 + Regularly published to the MQTT broker

At this point, the data can then be extracted by the GUI or the cloud server. 

## GUI Application Script

- **gui_mqtt.py**: GUI Application displaying sensor data, collecting from MQTT Broker 
- **gui_website.py**: GUI Application displaying sensor data, collecting from Cloud Website

### Functionalities

1. Displays live presence/absence and environment data
2. Alerts the user based on following criteria
 + Time spent continuously in front of the device exceeding a preset limit
 + Environmental variables around the user exceeding preset thrsholds.
 + Note that alerts can only be switched off by obeying the instructions on the warning page
 
### View Modes

1. Compact view: Minimalistic view mode relaying only the essential data
 + Displays only the live binary presence(1)/absence(0) data on the time graph 
 + Colour changing label displays the latest presence/absence status based on live data in green or red
2. Full view: Provides a detailed overview of the environment around the user.
 + Displays the live binary presence(1)/absence(0) data on the time graph
 + Displays live data on environment variables:
    + Ambient temperature
     + Humidity
      + Luminosity

## MQTT Host Scripts

- **mqttHostScripts**: Contains batch script and implementation files for cloud server side connection

## Website 

http://embeddedsystems.azurewebsites.net/#portfolio

Dashboard 
+ Username: testuser
+ Password: mypassword
