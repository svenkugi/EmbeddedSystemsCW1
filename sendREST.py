import requests
import json
#CREATE TABLE sensorData (id INT NOT NULL IDENTITY(1,1), sensorID INT, time_data TIMESTAMP, temperature INT, lux INT, presence INT);

url = "http://embeddedsystems.azurewebsites.net/api.php"
data = {"id": 100, "time": "01/11/95 12:00:32.001", "data": {"presence": 1, "lux": 300, "temperature": 22}}
data_json = json.dumps(data)
response = requests.post(url, data=data_json)
print(response.text)
