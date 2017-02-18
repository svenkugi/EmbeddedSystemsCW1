import requests
import json
import paho.mqtt.client as mqtt
from datetime import datetime
import json, datetime
import time

#CREATE TABLE sensorData (id INT NOT NULL IDENTITY(1,1), machine_id INT, time_data datetime, temperature float, brightness float, presence INT, humidity float);

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	print("Connected to broker with result code "+str(rc))
	client.subscribe("esys/RushB/Data")
	client.subscribe("esys/RushB/Bias")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
	global bias
	if msg.topic == "esys/RushB/Data":
		jsonData = json.loads(msg.payload.decode('utf-8')) #decode from bytes to utf-8 and convert to JSON
		prevDist = jsonData["Data"]["Distance"]["Previous"]
		curDist = jsonData["Data"]["Distance"]["Current"]
		sqDiff = jsonData["Data"]["Distance"]["SqDiff"]
		tempDiff = jsonData["Data"]["Point Temperature"]-jsonData["Data"]["AmbientTemperature"]
		print("Diff: " + str(abs(curDist-prevDist)) + " SqDiff: " + str(sqDiff) + " Temp Diff: " + str(tempDiff) + " Bias Diff: " + str(tempDiff-bias) + " Presence: " + str(jsonData["Data"]["Presence"]))
	elif msg.topic == "esys/RushB/Bias":
		bias = float(msg.payload)
		
global bias
bias = 0
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
client.loop_forever()

