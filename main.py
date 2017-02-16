#---------------------- Import Modules ---------------------#

import time, machine, tsl2561
import network, ubinascii, json
from machine import I2C, Pin
from umqtt.simple import MQTTClient

#------------ I2C Initialization and Configuration ---------#

HRLV_ADDR = 0x49 	# Ultra-Sonic Radar Sensor HRLV-EZ1: 0x49 (73)
TMP007_ADDR = 0x44 	# Infra-Red Thermophile Sensor TMP007: 0x44 (68)
TSL2561_ADDR = 0x39 # Luminosity Sensor TSL2561: 0x39 (57)
Si7021_ADDR = 0x40	# Humidity/Temperature Sensor Si7021: 0x40 (64)

# Initialise I2C Bus, SCL (Pin 5) and SDA (Pin 4)
i2c = I2C(-1, Pin(5), Pin(4))

# Configure HRLV-EZ1 Sensor
configbuf = b'\x01\x04\x83'
i2c.writeto(HRLV_ADDR, configbuf)

# Configure TMP007 Sensor
configbuf = b'\x02\x15\x40'
i2c.writeto(TMP007_ADDR, configbuf)

# Configure TSL2561 Sensor
configbuf = b'\x80\x03'
i2c.writeto(TSL2561_ADDR, configbuf)

# Configure Si7021 Sensor
configbuf = b'\xE6\x3E'
i2c.writeto(Si7021_ADDR, configbuf)

# Configure LED States (Active Low)
led_red = Pin(0, Pin.OUT, value=1) #GPIO Pin 0
led_blue = Pin(2, Pin.OUT, value=1)	#GPIO Pin 2

#-----------------Initialise MQTT and Time------------------#

#Default MQTT Server 
id = ubinascii.hexlify(machine.unique_id())
brokerAddr ="192.168.4.2"
client = MQTTClient(id,brokerAddr)

client.connect()
client.publish(b"esys/RushB/Status", b"Initial connection")

#Setting time using subscribe method, alternative method using ntptime 
#Note Micropython uses 0-6 for weekday, but RTC module uses 1-7 -> Hence off-error of 1

rtc = machine.RTC()
rtc.datetime((2017, 02, 14, 0, 18, 12, 12, 12))

#---------------------Data Calibration and Scaling----------------#
global bias
global cal
bias = 0
cal = 0

FS = 3.3
unit = FS/pow(2,15)
tempscale = 0.03125

dist_prev = 0
presence = 0

#def calibrate(topic, message):
#	if(message):
#		cal = 1	
#		led_red.value(0) 
#	else:
#		cal = 0

#client.set_callback(calibrate)
#client.subscribe(b'esys/RushB/Calibrate')

#-------------------------Data Collection-----------------------#

while 1:
	
	# HRLV-EZ1 (Distance) Data 
	adbuf = b'\x00' 
	i2c.writeto(HRLV_ADDR, adbuf)
	readbuf = i2c.readfrom(HRLV_ADDR, 2)
	ADCv = unit*(readbuf[1] + (readbuf[0]*pow(2,8)))
	dist = ADCv/(FS/5.12)
	print("Distance to Object: %.2fm, Analog Voltage: %.2fV" % (dist, ADCv))

	# TMP007 (Infrared and Ambient Temperature) Data
	adbuf = b'\x03' 
	i2c.writeto(TMP007_ADDR, adbuf) 
	tempbuf = i2c.readfrom(TMP007_ADDR, 2)
	object_temp = tempscale*((tempbuf[1]>>2) + (tempbuf[0]*pow(2,6)))  #14-bit Data & 0.03125°C per LSB

	adbuf = b'\x01' 
	i2c.writeto(TMP007_ADDR, adbuf) 
	tempbuf = i2c.readfrom(TMP007_ADDR, 2)
	amb_temp = tempscale*((tempbuf[1]>>2) + (tempbuf[0]*pow(2,6))) 

	#10-point Moving Average for Ambient Temperature (Remove Random Noise)
	try:
		amb_temp_buf
	except NameError:
		amb_temp_buf = [amb_temp]*10

	amb_temp_buf = [amb_temp] + amb_temp_buf[0:9]   
	amb_temp_avg = sum(amb_temp_buf)/10
	print("Ambient Temperature: %.2fC, Object Temperature: %.2fC" % (amb_temp_avg, object_temp))

	# Si7021 (Relative Humidity and Temperature) Data 
	adbuf = b'\xF5' 						
	i2c.writeto(Si7021_ADDR, adbuf) 
	time.sleep_ms(200)	#t_conv of ADC for temp + humidity
	humidity_buf = i2c.readfrom(Si7021_ADDR, 2)
	humidity = ((125/65536) * (humidity_buf[1] + humidity_buf[0]*pow(2,8))) - 6
    
    #Sensor also has temperature data, but deemed less accurate than TMP007 temperature
    #adbuf = b'\xE0'
    #i2c.writeto(Si7021_ADDR, adbuf)
    #htempbuf = i2c.readfrom(Si7021_ADDR, 2)
    #temperature = (175.72 * (htempbuf[1] + htempbuf[0]*pow(2,8))/65536) - 46.85

	#10-point Moving Average for Ambient Humidity (Remove Random Noise)
	try:
		humidity_buf
	except NameError:
		humidity_buf = [humidity]*10

	humidity_buf = [humidity] + humidity_buf[0:9]   
	humidity_avg = sum(humidity_buf)/10
	print("Relative Humidity: %.2fC" % (humidity_avg))

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
	print("Brightness: %.2fC" % (lux_avg))

	# Detect Presence of Person 
	if((abs(object_temp - bias - amb_temp)) < 2):		
		if((dist_prev - dist) > 0.5):
			presence = 0
			led_blue.value(1)
	else:
		presence = 1
		led_blue.value(0)

	dist_prev = dist

	# Check if Data needs to be Calibrated
	#client.check_msg()

	# Equate object temperature (wall/chair) to ambient temperature 
	#if(cal):	
	#	bias = object_temp-amb_temp 
	#	cal = 0
	#	led_red.value(1)

	#-------------------------Sending Data over MQTT------------------------#

    #Convert rtc.datetime tuple form into mysql time format
	tmp = rtc.datetime()
	str_time = str(tmp[0]) + "-" + str(tmp[1]) + "-" + str(tmp[2]) + " " + str(tmp[4]) + ":" + str(tmp[5]) + ":" + str(tmp[6])

    #Character Encoding for str instances is by Default UTF-8
	client.publish(b"esys/RushB/Data", json.dumps({"MachineId": id, "Time": str_time, "Data": {"Presence":presence, "Brightness":lux_avg, "AmbientTemperature":amb_temp_avg, "Humidity":humidity_avg}}))
	
	#Debug Statement: Message Sent if Blue LED turns off
	led_blue.value(1)
	time.sleep(4)
	led_blue.value(0)

#client.disconnect()
