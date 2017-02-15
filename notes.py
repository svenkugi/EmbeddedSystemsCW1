Code Formatting
    Use uheapq (items in heap and retrieve in priority order)
    Think of memory overhead and efficient coding
    Coding Formatting: Use define, good variable, split it up so use functions "(def)"

Further
    Encryption (AES or ssl)

To-Do

Time Subscribe
Interrupt in MQTT Publish and Presence=0]
Trigger/Interrupt (Brightness, Temperature, Distance): LEDS, GUI Warning(MsgBox), Threshold

________________________________________________________
def rtc_time(topic, message):
	global date
	time = json.loads(message)
	date = time['date']
	print(date)

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
