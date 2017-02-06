import machine, time
i2c = machine.I2C(machine.Pin(5), machine.Pin(4), freq=100000)
out = i2c.scan()
#print(out)

#from machine import I2C, Pin
#i2c = I2C(Pin(5), Pin(4), freq=100000)
#i2c.scan()
#i2c.init(Pin(5), Pin(4), freq=100000)
#i2c.start()
#adbuf = bytearray(1)
#adbuf[0] = 0x01
#i2c.writeto(73, adbuf)
configbuf = bytearray(3)
configbuf[0] = 0x01
configbuf[1] = 0x04
configbuf[2] = 0x83
i2c.writeto(73, configbuf)
adbuf = bytearray(1)
#i2c.start()
adbuf[0] = 0x00
i2c.writeto(73, adbuf)

FS = 3.3
unit = FS/pow(2,15)

while 1:
    readbuf = i2c.readfrom(73, 2)
    ADCv = unit*(readbuf[1] + (readbuf[0]*pow(2,8)))
    scaling = ADCv/(FS/5.12)
    print("%.2fV, %.2fm" % (ADCv, scaling))
    time.sleep(1)
