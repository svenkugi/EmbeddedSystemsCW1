import machine, time, json, mqtt.simple, pyb
import network 
import ubinascii

i2c = machine.I2C(machine.Pin(5), machine.Pin(4), freq=100000)

#initialise i2c
configbuf = bytearray(3)
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

FS = 3.3
unit = FS/pow(2,15)
rtc = pyb.RTC()

# data stream
while 1:
    readbuf = i2c.readfrom(73, 2)
    ADCv = unit*(readbuf[1] + (readbuf[0]*pow(2,8)))
    meters = ADCv/(FS/5.12)
    client.publish(b"esys/RushB/data", json.dumps([{"time": rtc.datetime, "voltage":ADCv, "distance",meters}]).encode(encoding='UTF-8'))
    print("%.2fV, %.2fm" % (ADCv, meters))
    time.sleep(1)

client.disconnect()