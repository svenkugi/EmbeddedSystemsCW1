#---------------------- Import Modules ---------------------#

import time, machine, tsl2561, sys
import network, ubinascii, json
from machine import I2C, Pin
from umqtt.simple import MQTTClient

#------------ I2C Initialization and Configuration ---------#

HRLV_ADDR = 0x49 	# ADS 1115-Q1 [Ultra-Sonic Radar Sensor HRLV-EZ1]: 0x49 (73)
TMP007_ADDR = 0x44 	# Infra-Red Thermophile Sensor TMP007: 0x44 (68)
TSL2561_ADDR = 0x39 # Luminosity Sensor TSL2561: 0x39 (57)
Si7021_ADDR = 0x40	# Humidity/Temperature Sensor Si7021: 0x40 (64)

# Initialise I2C Bus, SCL (Pin 5) and SDA (Pin 4)
i2c = I2C(-1, Pin(5), Pin(4))

# Configure ADS-1115 Q1 ADC (Continuous Conversion Mode, Differential Mode, 128SPS)
configbuf = b'\x01\x04\x83'
i2c.writeto(HRLV_ADDR, configbuf)

# Configure TMP007 Sensor (4 Averages per Conversion, Transient Correction Enabled)
configbuf = b'\x02\x15\x40'
i2c.writeto(TMP007_ADDR, configbuf)

# Configure TSL2561 Sensor (Block Word Read, Power Up)
configbuf = b'\x80\x03'
i2c.writeto(TSL2561_ADDR, configbuf)

# Configure Si7021 Sensor (RH 12-Bit Resolution, Heater Enabled)
configbuf = b'\xE6\x3E'
i2c.writeto(Si7021_ADDR, configbuf)

# Configure LED States (Active Low)
led_red = Pin(0, Pin.OUT, value=1) #GPIO Pin 0
led_blue = Pin(2, Pin.OUT, value=1)	#GPIO Pin 2

#-----------------Initialise MQTT and Time------------------#

# Connection to MQTT Server
id = ubinascii.hexlify(machine.unique_id())
brokerAddr = b"192.168.4.65"
client = MQTTClient(id,brokerAddr)

# Send Initial Status to confirm successful connection 
client.connect()
client.publish(b"esys/RushB/Init", b"Initial connection")

# Setting time using subscribe method; Broker sends time and ESP8266 waits until time received
# Note Micropython uses 0-6 for weekday, but RTC module uses 1-7 -> Hence off-error of 1
def rtc_time(topic, message):
	global date
	time = json.loads(message)
	date = time['date']

client.set_callback(rtc_time)
client.subscribe(b'esys/RushB/time')
client.wait_msg()

# Extract strings from RCF-339 Format in order to format 
# into the tuple format required for rtc module 
year = int(date[0:4])
month = int(date[5:7])
day = int(date[8:10])
hour = int(date[11:13])
minute = int(date[14:16])
second = int(date[17:19])
microsecond = int(date[20:22])

rtc = machine.RTC()
rtc.datetime((year, month, day, 0, hour, minute, second, microsecond))

#---------------------Data Calibration and Scaling----------------#

# Declare Global variables for bias and calibrate so it can be used cross-function
global bias
global cal
bias = 0
cal = 0

# Distance Sensor Calibration 
FS = 3.3
unit = FS/pow(2,15)
tempscale = 0.03125

# Presence Detection Buffer Initialization 
dist_buf = [0]*5
global dist_prev
global dist 
dist_prev = 0
presence = 0

# Function checking whether user wants to calibrate or exit 
def user_command(topic, message):
	global cal 
	
	if(message == b"calibrate"):
		cal = 1	
		led_red.value(0) 
	elif(message == b"exit"):
		client.disconnect() 
		sys.exit("User-Triggered Exit")

client.set_callback(user_command)
client.subscribe(b'esys/RushB/User')

#-------------------------Data Collection-----------------------#

def distance_read():
	# HRLV-EZ1 (Distance) Data 
	adbuf = b'\x00' 
	i2c.writeto(HRLV_ADDR, adbuf)
	readbuf = i2c.readfrom(HRLV_ADDR, 2)
	ADCv = unit*(readbuf[1] + (readbuf[0]*pow(2,8)))
	dist = ADCv/(FS/5.12)
	#print("Distance to Object: %.2fm, Analog Voltage: %.2fV" % (dist, ADCv))

def temp_read():
	# TMP007 (Infrared and Ambient Temperature) Data
	adbuf = b'\x03' 
	i2c.writeto(TMP007_ADDR, adbuf) 
	tempbuf = i2c.readfrom(TMP007_ADDR, 2)
	object_temp = tempscale*((tempbuf[1]>>2) + (tempbuf[0]*pow(2,6)))  #14-bit Point Temperature Data & 0.03125°C per LSB

	adbuf = b'\x01' 
	i2c.writeto(TMP007_ADDR, adbuf) 
	tempbuf = i2c.readfrom(TMP007_ADDR, 2)
	amb_temp = tempscale*((tempbuf[1]>>2) + (tempbuf[0]*pow(2,6)))  #14-bit Ambient Temperature Data & 0.03125°C per LSB

	#10-point Moving Average for Ambient Temperature (Remove Random Noise)
	try:
		amb_temp_buf
	except NameError:
		amb_temp_buf = [amb_temp]*10

	amb_temp_buf = [amb_temp] + amb_temp_buf[0:9]   
	amb_temp_avg = sum(amb_temp_buf)/10
	#print("Ambient Temperature: %.2fC, Object Temperature: %.2fC" % (amb_temp_avg, object_temp))

def humidity_read():
	# Si7021 (Relative Humidity and Temperature) Data 
	adbuf = b'\xF5' 						
	i2c.writeto(Si7021_ADDR, adbuf) 
	time.sleep_ms(200)	#t_conv of ADC for temp + humidity
	humid_buf = i2c.readfrom(Si7021_ADDR, 2)
	humidity = ((125/65536) * (humid_buf[1] + humid_buf[0]*pow(2,8))) - 6

	#10-point Moving Average for Ambient Humidity (Remove Random Noise)
	try:
		humidity_buf
	except NameError:
		humidity_buf = [humidity]*10

	humidity_buf = [humidity] + humidity_buf[0:9]   
	humidity_avg = sum(humidity_buf)/10
	#print("Relative Humidity: %.2fC" % (humidity_avg))

def luminosity_read():
	# TSL2561 (Brightness/Luminosity) Data 
	sensor = tsl2561.TSL2561(i2c)
	lux = sensor.read()

	#10-point Moving Average for Brightness (Remove Random Noise)
	try:
		lux_buf
	except NameError:
		lux_buf = [lux]*10

	lux_buf = [lux] + lux_buf[0:9] 
	lux_avg = sum(lux_buf)/10 
	#print("Brightness: %.2fC" % (lux_avg))

while 1:
	
	distance_read()
	temp_read()
	humidity_read()
	luminosity_read()
	
	# Detecting Movement and Presence of Person
	# Statistical Algorithm that computes the sum of the square of distances: The resultant value is compared 
	# to a threshold (which has been calculated when there is just noise so no movement). This algorithm proved
	# very effective in confirming the presence of a human 
	diff = abs(dist_prev - dist) 
	dist_buf = [diff] + dist_buf[0:4]

	distsq_sum = sum(map(lambda x: pow(x,2), dist_buf)) 

	# Person Detected using InfraRed Sensor and Distance Sensor. Infrared sensor detects a heat source by 
	# distinguishing itself from ambient temperature. Human presence is then confirmed by regular movement, 
	# done by statistical algorithm checking whether it is above a threshold 
	try: 
		if((abs(object_temp - bias - amb_temp)) > 1):	
			if(distsq_sum > 0.0001):  
				presence = 1
				led_blue.value(1)
			else:
				presence = 0
		else:
			presence = 0
			led_blue.value(0)

	# Exception to catch errors throughout the program and identify the point of failure 
	except:
		led_red.value(0)
		print("ERROR: Brightness AVG")
		client.disconnect()
		sys.exit("ERROR: Brightness AVG")

	# Check if Data needs to be calibrated
	client.check_msg()

	# Equate object temperature (wall/chair) to ambient temperature 
	# This is done to neutralize the offset in temperature reading between ambient and 
	# point temperature, so that when a person sits in front of the device, there will  
	# be a clearer distinction of it and the environment. Calibration is also done to 
	# adjust for different environments by establishing a bias. 
	if(cal):	
		bias = object_temp - amb_temp 
		cal = 0
		led_red.value(1)
		client.publish(b'esys/RushB/Bias', str(bias))

	#-------------------------Sending Data over MQTT------------------------#

    # Convert rtc.datetime tuple form into mysql time format
    # Done so that data sent to website can then be more easily formatted
	tmp = list(map(str, rtc.datetime()))
	for i in range(1, 6):
		if (int(tmp[i]) < 9): 
			tmp[i] = "0" + tmp[i]

	str_time = tmp[0] + "-" + tmp[1] + "-" + tmp[2] + " " +  tmp[4] + ":" +  tmp[5] + ":" + tmp[6]

    # Character Encoding for str instances is by Default UTF-8
	try:
		client.publish(b"esys/RushB/Data", json.dumps({"MachineId": id, "Time": str_time, "Data": {"Presence":presence, "Distance":{"Previous": dist_prev, "Current": dist, "SqDiff": distsq_sum}  , "Brightness":lux_avg, "Point Temperature": object_temp, "AmbientTemperature":amb_temp, "Humidity":humidity_avg}}))

	# Exception placed to catch error if there is a problem with sending data to the broker
	except:
		led_red.value(0)
		print("ERROR: Send data")
		client.disconnect()
		sys.exit("ERROR: Send data")

	#Debug Statement: Message Sent if Blue LED turns off
	led_blue.value(1)
	time.sleep(3)
	led_blue.value(0)

	dist_prev = dist

client.disconnect()
