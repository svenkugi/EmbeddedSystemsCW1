import network 
import ubinascii
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
sta_if = network.WLAN(network.STA_IF) 
sta_if.active(True)
sta_if.connect('EEERover', 'exhibition')
#a = sta_if.ifconfig()
#print(a)

import machine
from umqtt.simple import MQTTClient
id = ubinascii.hexlify(machine.unique_id())
BROKER_ADDRESS = "192.168.0.10"
client = MQTTClient(id,BROKER_ADDRESS)
client.connect()
a = client.ping()
print(a)
TOPIC = "esys/RushB/data"
client.publish(TOPIC, b"hello")
client.disconnect()

