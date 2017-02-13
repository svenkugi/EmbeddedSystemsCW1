import requests
import json
import paho.mqtt.client as mqtt

#CREATE TABLE sensorData (id INT NOT NULL IDENTITY(1,1), sensorID INT, time_data TIMESTAMP, temperature INT, lux INT, presence INT, humidity INT);

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("esys/RushB/Data")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
	#data = json.loads(msg.payload)
	#data = {"id": 100, "time": "01/11/95 12:00:32.001", "data": {"presence": 1, "lux": 300, "temperature": 22}}
	#data_json = json.dumps(data)
	response = requests.post("http://embeddedsystems.azurewebsites.net/api.php", data=msg.payload)
	print(msg.topic+" "+str(msg.payload))
	print(response.text)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("", 1883, 60)

