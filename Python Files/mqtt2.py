import network 
import ubinascii
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
sta_if = network.WLAN(network.STA_IF) 
sta_if.active(True)
sta_if.connect('EEERover', 'exhibition')

import machine
from umqtt.simple import MQTTClient
id = ubinascii.hexlify(machine.unique_id())
BROKER_ADDRESS = "192.168.0.61"
client = MQTTClient(id,BROKER_ADDRESS)
a = client.connect()
print(a)
#client.ping()
#TOPIC = "esys/RushB/data"
#client.publish(b"foo_topic", b"hello")
client.disconnect()

