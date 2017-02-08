from machine import I2C, Pin
i2c = I2C(Pin(5), Pin(4), freq=100000)
i2c.scan()
i2c.init(Pin(5), Pin(4), freq=100000)
i2c.start()
adbuf = bytearray(1)
adbuf[0] = 0x01
i2c.writeto(73, adbuf)
configbuf = bytearray(2)
configbuf[0] = 0x04
configbuf[1] = 0x83
i2c.writeto(73, configbuf)
i2c.start()
readbuf = i2c.readfrom(73, 2)
print(readbuf)