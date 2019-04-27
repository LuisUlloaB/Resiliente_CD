import RPi.GPIO as gpio
from time import sleep
import os

gpio.setmode(gpio.BCM)
gpio.setwarnings(False)
gpio.setup(17, gpio.IN)

def main():
	try:
		while True:
			if gpio.input(17):
				result = os.popen("sudo shutdown -h now").read()
				return 1
			sleep(3)
	except KeyboardInterrupt:
		gpio.cleanup()

if __name__ == '__main__':
	print("script de apagado")
	main()
