#---------------------- Import Modules ---------------------#

import time, machine, tsl2561
import network, ubinascii, json
from machine import I2C, Pin
from umqtt.simple import MQTTClient

#------------ I2C Initialization and Configuration ---------#

HRLV_ADDR = 0x49 	# Ultra-Sonic Radar Sensor HRLV-EZ1: 0x49 (73)
TMP007_ADDR = 0x44 	# Thermophile Temperature Sensor TMP007: 0x44 (68)
TSL2561_ADDR = 0x39 # Luminosity Sensor TSL2561: 0x39 (57)
Si7021_ADDR = 0x40	# Humidity Sensor Si7021: 0x40 (64)

# Initialise I2C Bus, SCL (Pin 5) and SDA (Pin 4)
i2c = I2C(-1, Pin(5), Pin(4))

# Configure HRLV-EZ1 Sensor
configbuf = b'\x01\x04\x83'
i2c.writeto(HRLV_ADDR, configbuf)

# Configure TMP007 Sensor
configbuf = bytearray(3)
configbuf[0] = 0x02
configbuf[1] = 0x15
configbuf[2] = 0x40
i2c.writeto(TMP007_ADDR, configbuf)

# Configure TSL2561 Sensor
configbuf = b'\x80\x03'
i2c.writeto(TSL2561_ADDR, configbuf)

# Configure Si7021 Sensor
configbuf = b'\xE6\x3E'
i2c.writeto(Si7021_ADDR, configbuf)

# Configure LED States 
led_red = Pin(0, Pin.OUT, value=1) #Active Low Red LED on GPIO Pin 0
led_blue = Pin(2, Pin.OUT, value=1)	#Active Low Blue LED on GPIO Pin 2

#-----------------------------Initialise WiFi--------------#

ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
sta_if = network.WLAN(network.STA_IF) 
sta_if.connect('EEERover', 'exhibition')

#-----------------Initialise MQTT and Time------------------#

#Default MQTT Server 
id = ubinascii.hexlify(machine.unique_id())
brokerAddr ="192.168.0.10"
client = MQTTClient(id,brokerAddr)

client.connect()
client.publish(b"esys/RushB/Status", b"Initial connection")

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

#---------------------Data Calibration and Scaling----------------#
global bias, cal
bias = 0
cal = 0

def calibrate(topic, message):
	if(message):
		cal = 1	
		led_red.value(0) 
	else:
		cal = 0

client.set_callback(calibrate)
client.subscribe(b'esys/RushB/Calibrate')

FS = 3.3
unit = FS/pow(2,15)
tempscale = 0.03125
meters_prev = 0
presence = 0
local_temp_buf = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
lux_buf = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

#-------------------------Data Collection-----------------------#

while 1:
	
	# HRLV-EZ1 (Distance) Data 
	adbuf = b'\x00' 						#Conversion Result Register 
	i2c.writeto(HRLV_ADDR, adbuf)
	readbuf = i2c.readfrom(HRLV_ADDR, 2)
	ADCv = unit*(readbuf[1] + (readbuf[0]*pow(2,8)))
	meters = ADCv/(FS/5.12)
	print("Distance to Object: %.2fm, Analog Voltage: %.2fV" % (meters, ADCv))
	#print(abs(meters_prev - meters), object_temp - local_temp)

	# TMP007 (Infrared and Local Temperature) Data 
	adbuf = b'\x03' #Infrared Object Temperature Register 
	i2c.writeto(TMP007_ADDR, adbuf) 
	tempbuf = i2c.readfrom(TMP007_ADDR, 2)
	object_temp = tempscale*((tempbuf[1]>>2) + (tempbuf[0]*pow(2,6))) #14-bit Data and 0.03125°C per LSB

	adbuf = b'\x01' #Local Temperature Register 
	i2c.writeto(TMP007_ADDR, adbuf) 
	tempbuf = i2c.readfrom(TMP007_ADDR, 2)
	local_temp = tempscale*((tempbuf[1]>>2) + (tempbuf[0]*pow(2,6))) #14-bit Data and 0.03125°C per LSB

	local_temp_buf = [local_temp] + local_temp_buf[0:9]   #10-point Moving Average for Local Temperature (Remove Random Noise)
	local_temp_avg = sum(local_temp_buf)/10
	#print("Local Temperature: %.2fC, Object Temperature: %.2fC" % (local_temp_avg, object_temp))

	# Si7021 (Relative Humidity and Temperature) Data 
	adbuf = b'\xF5' 						# Realtive Humidity Register 
	i2c.writeto(Si7021_ADDR, adbuf) 
	time.sleep(1)
	humidbuf = i2c.readfrom(Si7021_ADDR, 2)
	humidity = ((125/65536) * (humidbuf[1] + humidbuf[0]*pow(2,8))) - 6

	adbuf = b'\xE0' # Temperature Register 
	i2c.writeto(Si7021_ADDR, adbuf) 
	time.sleep(1)
	htempbuf = i2c.readfrom(Si7021_ADDR, 2)
	temperature = (175.72 * (htempbuf[1] + htempbuf[0]*pow(2,8))/65536) - 46.85

	# TSL2561 (Brightness/Luminosity) Data 
	sensor = tsl2561.TSL2561(i2c)
	lux = sensor.read()

	lux_buf = [lux] + lux_buf[0:9] #10-point Moving Average for Brightness (Remove noise)
	lux_avg = sum(lux_buf)/10 
	#print("Averaged Brightness:", lux_avg, "lux")

	# Detect Presence of Person 
	if((abs(object_temp - bias -local_temp)) < 2):		
		if((meters_prev - meters) > 0.5):
			presence = 0
			led_blue.value(1)
	else:
		presence = 1
		led_blue.value(0)

	meters_prev = meters

	# Check if Data needs to be Calibrated
	client.check_msg()

	if(cal):
		bias = object_temp-local_temp # Equate object temperature (wall/chair) to ambient temperature 
		cal = 0
		led_red.value(1)

	#-------------------------Sending Data over MQTT------------------------#

	#Character Encoding for str instances is by Default UTF-8
	#client.publish(b"esys/RushB/Data", json.dumps({"MachineId": id, "Time": rtc.datetime(), "Data": {"Presence":presence, "Brightness":lux_avg, "AmbientTemperature":local_temp}}))

	time.sleep(2)

client.disconnect()
