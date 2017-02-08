import machine, time, json, mqtt.simple, pyb
import network, ubinascii

#I2C Address
#Ultra-Sonic Distance Sensor HRLV-EZ1: 0x49 (73)
#Luminosity Sensor TSL2561: 0x39 (57)
#Thermophile Temperature Sensor TMP007: 0x40 (67)
#Temperature/Barometric Sensor MPL3115A2: 0x60 (96)

#Initialise I2C Bus
i2c = machine.I2C(machine.Pin(5), machine.Pin(4), freq=100000)

#Configure I2C for Distance Sensor
configbuf = bytearray(3)
configbuf[0] = 0x01
configbuf[1] = 0x04
configbuf[2] = 0x83
i2c.writeto(73, configbuf)
adbuf = bytearray(1)
adbuf[0] = 0x00
i2c.writeto(73, adbuf)

#Configure I2C for Luminosity Sensor
configbuf[0] = 0x01
configbuf[1] = 0x04
configbuf[2] = 0x83
i2c.writeto(73, configbuf)
adbuf = bytearray(1)
adbuf[0] = 0x00
i2c.writeto(73, adbuf)

#Configure I2C for Temperature Sensor
configbuf[0] = 0x01
configbuf[1] = 0x04
configbuf[2] = 0x83
i2c.writeto(73, configbuf)
adbuf = bytearray(1)
adbuf[0] = 0x00
i2c.writeto(73, adbuf)

#initialise WiFi
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
sta_if = network.WLAN(network.STA_IF) 
sta_if.active(True)
sta_if.connect('EEERover', 'exhibition')

#initialise mqtt
id = ubinascii.hexlify(machine.unique_id())
brokerAddr ="192.168.0.61"
client = MQTTClient(id,brokerAddr)
a = client.connect()
client.publish(b"esys/RushB/status", b"Initial connection")

#Data and Time Initialization
FS = 3.3
unit = FS/pow(2,15)
rtc = pyb.RTC()

#Data stream
while 1:
    readbuf = i2c.readfrom(73, 2)
    ADCv = unit*(readbuf[1] + (readbuf[0]*pow(2,8)))
    meters = ADCv/(FS/5.12)
    client.publish(b"esys/RushB/data", json.dumps([{"time": rtc.datetime, "voltage":ADCv, "distance",meters}]).encode(encoding='UTF-8'))
    print("%.2fV, %.2fm" % (ADCv, meters))
    time.sleep(1)

client.disconnect()
