#---------------------- Import Modules ---------------------#

import time, machine, tsl2561, sys
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

#ap_if = network.WLAN(network.AP_IF)
#ap_if.active(False)
#sta_if = network.WLAN(network.STA_IF) 
#sta_if.connect('EEERover', 'exhibition')

#Default MQTT Server
id = ubinascii.hexlify(machine.unique_id())
brokerAddr = b"192.168.4.65"
client = MQTTClient(id,brokerAddr)

client.connect()
client.publish(b"esys/RushB/Init", b"Initial connection")

#Setting time using subscribe method, alternative method using ntptime 
#Note Micropython uses 0-6 for weekday, but RTC module uses 1-7 -> Hence off-error of 1
def rtc_time(topic, message):
	global date
	time = json.loads(message)
	date = time['date']

client.set_callback(rtc_time)
client.subscribe(b'esys/RushB/time')
client.wait_msg()

year = int(date[0:4])
month = int(date[5:7])
day = int(date[8:10])
hour = int(date[11:13])
minute = int(date[14:16])
second = int(date[17:19])
microsecond = int(date[20:22])
#tzinfo = int(date[23:25])

rtc = machine.RTC()
rtc.datetime((year, month, day, 0, hour, minute, second, microsecond))

#---------------------Data Calibration and Scaling----------------#
global bias
global cal
bias = 0
cal = 0

FS = 3.3
unit = FS/pow(2,15)
tempscale = 0.03125

dist_buf = [0]*5
dist_prev = 0
presence = 0

def user_command(topic, message):
	global cal 
	
	#print(message)
	#sys.exit("suh dude")
	if(message == b"calibrate"):
		cal = 1	
		led_red.value(0) 
	elif(message == b"exit"):
		client.disconnect() 
		sys.exit("User-Triggered Exit")

client.set_callback(user_command)
client.subscribe(b'esys/RushB/User')

#-------------------------Data Collection-----------------------#

while 1:
	
	# HRLV-EZ1 (Distance) Data 
	adbuf = b'\x00' 
	i2c.writeto(HRLV_ADDR, adbuf)
	readbuf = i2c.readfrom(HRLV_ADDR, 2)
	ADCv = unit*(readbuf[1] + (readbuf[0]*pow(2,8)))
	dist = ADCv/(FS/5.12)
	#print("Distance to Object: %.2fm, Analog Voltage: %.2fV" % (dist, ADCv))
	
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
	#print("Ambient Temperature: %.2fC, Object Temperature: %.2fC" % (amb_temp_avg, object_temp))

	# Si7021 (Relative Humidity and Temperature) Data 
	adbuf = b'\xF5' 						
	i2c.writeto(Si7021_ADDR, adbuf) 
	time.sleep_ms(200)	#t_conv of ADC for temp + humidity
	humid_buf = i2c.readfrom(Si7021_ADDR, 2)
	humidity = ((125/65536) * (humid_buf[1] + humid_buf[0]*pow(2,8))) - 6

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
	#print("Relative Humidity: %.2fC" % (humidity_avg))

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

	#Detecting Movement and Presence of Person
	diff = abs(dist_prev - dist) 
	dist_buf = [diff] + dist_buf[0:4]

	distsq_sum = sum(map(lambda x: pow(x,2), dist_buf)) 

	try: 
		if((abs(object_temp - bias - amb_temp)) > 1):	
			#if((abs(dist_prev - dist)) < 0.5):
			if(distsq_sum > 0.0001):   # Statistical Analysis showed nits larger than noise
				presence = 1
				led_blue.value(1)
			else:
				presence = 0
		else:
			presence = 0
			led_blue.value(0)

	except:
		led_red.value(0)
		print("ERROR: Brightness AVG")
		client.disconnect()
		sys.exit("ERROR: Brightness AVG")

	# Check if Data needs to be Calibrated
	client.check_msg()

	# Equate object temperature (wall/chair) to ambient temperature 
	if(cal):	
		bias = object_temp - amb_temp 
		cal = 0
		led_red.value(1)
		client.publish(b'esys/RushB/Bias', str(bias))

	#-------------------------Sending Data over MQTT------------------------#

    #Convert rtc.datetime tuple form into mysql time format
	tmp = list(map(str, rtc.datetime()))
	for i in range(1, 6):
		if (int(tmp[i]) < 9): 
			tmp[i] = "0" + tmp[i]

	str_time = tmp[0] + "-" + tmp[1] + "-" + tmp[2] + " " +  tmp[4] + ":" +  tmp[5] + ":" + tmp[6]

    #Character Encoding for str instances is by Default UTF-8
	try:
		client.publish(b"esys/RushB/Data", json.dumps({"MachineId": id, "Time": str_time, "Data": {"Presence":presence, "Distance":{"Previous": dist_prev, "Current": dist, "SqDiff": distsq_sum}  , "Brightness":lux_avg, "Point Temperature": object_temp, "AmbientTemperature":amb_temp, "Humidity":humidity_avg}}))

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