import RPi.GPIO as gpio
gpio.setmode(gpio.BCM)
gpio.setwarnings(False)
gpio.setup(23, gpio.OUT, initial=0)

gpio.output(23,0)
