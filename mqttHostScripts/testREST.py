import requests
import json
from datetime import datetime

#CREATE TABLE sensorData (id INT NOT NULL IDENTITY(1,1), machine_id INT, time_data DATETIME, temperature INT, brightness INT, presence INT, humidity INT);
#	2007-05-08 12:35:29.123
jsonData = {"Data":{}}
jsonData["Time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
response = input("ID: ")
jsonData["MachineId"] = response
response = input("Temp: ")
jsonData["Data"]["AmbientTemperature"] = response
response = input("Lux: ")
jsonData["Data"]["Brightness"] = response
response = input("Presence: ")
jsonData["Data"]["Presence"] = response
response = input("Humidity: ")
jsonData["Data"]["Humidity"] = response

print(jsonData)
response = requests.post("http://embeddedsystems.azurewebsites.net/api.php", data=json.dumps(jsonData))
print(response.status_code)
print(response.text)
#{'MachineId': '1', 'Data': {'Brightness': '20', 'humidity': '72', 'Presence': '1', 'AmbientTemperature': '32'}, 'Time': '2017-02-14 12:22:42'}