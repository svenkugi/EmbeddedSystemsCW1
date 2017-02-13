#---------------------- Import Modules ---------------------#

import time, machine, tsl2561
import network, ubinascii, json
from machine import I2C, Pin
from umqtt.simple import MQTTClient

#------------ I2C Initialization and Configuration ---------#

# Ultra-Sonic Radar Sensor HRLV-EZ1: 0x49 (73)
# Thermophile Temperature Sensor TMP007: 0x40 (64)
# Luminosity Sensor TSL2561: 0x39 (57)

# Initialise I2C Bus, SCL (Pin 5) and SDA (Pin 4)
i2c = I2C(-1, Pin(5), Pin(4))

# Configure HRLV-EZ1 Sensor
configbuf = b'\x01\x04\x83'
i2c.writeto(73, configbuf)

# Configure TMP007 Sensor
configbuf = bytearray(3)
configbuf[0] = 0x02
configbuf[1] = 0x15
configbuf[2] = 0x40
i2c.writeto(64, configbuf)

# Configure TSL2561 Sensor
configbuf = b'\x80\x03'
i2c.writeto(57, configbuf)

#-----------------------------Initialise WiFi--------------#

ap_if = network.WLAN(network.AP_IF)
#ap_if.active(False)
ap_if.active(True)
ap_if.config(essid="STOP SPAMMING EEROVER", password="password123")
sta_if = network.WLAN(network.STA_IF) 
#sta_if.active(True)
#sta_if.connect('EEERover', 'exhibition')
#-----------------Initialise MQTT and Time------------------#

#Default MQTT Server 
id = ubinascii.hexlify(machine.unique_id())
brokerAddr ="192.168.4.2"
client = MQTTClient(id,brokerAddr)

#Setting time using subscribe method, alternative method using ntptime 
#Note Micropython uses 0-6 for weekday, but RTC module uses 1-7 -> Hence off-error of 1 
def rtc_time(topic, message):
	global date
	time = json.loads(message)
	date = time['date']
	#print(date)

client.set_callback(rtc_time)
client.connect()
client.publish(b"esys/RushB/Status", b"Initial connection")
client.subscribe(b'esys/time')
client.wait_msg()

year = int(date[0:4])
month = int(date[5:7])
day = int(date[8:10])
hour = int(date[11:13])
minute = int(date[14:16])
second = int(date[17:19])
microsecond = int(date[20:22])
tzinfo = int(date[23:25])
rtc = machine.RTC()
rtc.datetime((year, month, day, 0, hour, minute, second, microsecond)) 
#print(rtc.datetime())

#---------------------Data Calibration and Scaling----------------#
global bias
bias = 0

def calibrate(topic, message):
	global cal
	if(message):
		cal = 1	
	else:
		cal = 0

FS = 3.3
unit = FS/pow(2,15)
tempscale = 0.03125
meters_prev = 0

local_temp_buf = [0, 0, 0, 0]
lux_buf = [0, 0, 0, 0]

#-------------------------Data Collection-----------------------#

while 1:
	
	# HRLV-EZ1 (Distance) Data 
	adbuf = b'\x00' #Conversion Result Register 
	i2c.writeto(73, adbuf)
	readbuf = i2c.readfrom(73, 2)
	ADCv = unit*(readbuf[1] + (readbuf[0]*pow(2,8)))
	meters = ADCv/(FS/5.12)
	#print("Distance to Object: %.2fm, Analog Voltage: %.2fV" % (meters, ADCv))
	#print(abs(meters_prev - meters), object_temp - local_temp)

	# TMP007 (Infrared and Local Temperature) Data 
	adbuf = b'\x03' #Infrared Object Temperature Register 
	i2c.writeto(64, adbuf) 
	tempbuf = i2c.readfrom(64, 2)
	object_temp = tempscale*((tempbuf[1]>>2) + (tempbuf[0]*pow(2,6))) #14-bit Data and 0.03125°C per LSB
	
	adbuf = b'\x01' #Local Temperature Register 
	i2c.writeto(64, adbuf) 
	tempbuf = i2c.readfrom(64, 2)
	local_temp = tempscale*((tempbuf[1]>>2) + (tempbuf[0]*pow(2,6))) #14-bit Data and 0.03125°C per LSB
	#print("Local Temperature: %.2fC, Object Temperature: %.2fC" % (local_temp, object_temp))

	temp = local_temp_buf[0:3]
	local_temp_buf[0] =  local_temp
	local_temp_buf[1:4] = temp
	local_temp_avg = sum(local_temp_buf)/4 #4-point Moving Average for Local Temperature (Remove Random Noise)
	#print("Local Temperature: %.2fC, Object Temperature: %.2fC" % (local_temp_avg, object_temp_avg))

	# TSL2561 (Brightness/Luminosity) Data 
	sensor = tsl2561.TSL2561(i2c)
	lux = sensor.read()
	
	temp = lux_buf[0:3]
	lux_buf[0] =  lux
	lux_buf[1:4] = temp
	lux_avg = sum(lux_buf)/4 #4-point Moving Average for Brightness (Remove noise)
	#print("Averaged Brightness:", lux_avg, "lux")

	# Detect Presence of Person 

	if((abs(object_temp - bias -local_temp)) < 2):		
		if((meters_prev-meters) > 0.5):
			presence = 0
	else:
		presence = 1

	# Check if Data needs to be calibrated
	client.set_callback(calibrate)
	client.subscribe(b'esys/time')
	client.check_msg()

	if(cal):
		bias = object_temp-local_temp


#-------------------------Sending Data over MQTT------------------------#
	#Character Encoding for str instances is by Default UTF-8
	client.publish(b"esys/RushB/Data", json.dumps({"Time": rtc.datetime(), "Data": {"Occupancy":presence, "Brightness":lux_avg, "AmbientTemperature":local_temp}}))
	#client.publish(b"esys/RushB/Data", json.dumps({"Time": rtc.datetime(), "Brightness":lux_avg}))
	#client.publish(b"esys/RushB/Data/Temperature", json.dumps({"Time": rtc.datetime(), "Person Temperature":object_temp, "Local Temperature":local_temp}))
	
	time.sleep(4)

client.disconnect()