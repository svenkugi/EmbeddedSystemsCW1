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
	client.subscribe("esys/RushB/+")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
	if msg.topic == "esys/RushB/Init":	# If we get an initialization message from our device, send the time
		print("KnockKnock connected, sending time:")
		time.sleep(2)	# Account for slight delay after device publishes message to when it can accept messages
		j = {"date":datetime.datetime.now().isoformat()}
		client.publish("esys/RushB/time", json.dumps(j))
	elif msg.topic == "esys/RushB/Data": # If it is a data message, then upload via POST to cloud API
		print(msg.topic+" "+str(msg.payload))
		jsonData = json.loads(msg.payload.decode('utf-8')) # decode from bytes to utf-8 and convert to JSON
		jsonData["MachineId"] = int(jsonData["MachineId"],16) # convert hex machineid to hex
		response = requests.post("http://embeddedsystems.azurewebsites.net/api.php", data=json.dumps(jsonData))
		print(response)
	else:
		print(msg.topic+" "+str(msg.payload))
		
client = mqtt.Client()

# Create callbacks
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)

# Send an extra time message on startup in case this script needs to restart
j = {"date":datetime.datetime.now().isoformat()}
client.publish("esys/RushB/time", json.dumps(j))

client.loop_forever()

