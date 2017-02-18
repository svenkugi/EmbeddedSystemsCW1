import network 

ap_if = network.WLAN(network.AP_IF)
ap_if.active(True)
ap_if.config(essid="RushB", password="password123")

