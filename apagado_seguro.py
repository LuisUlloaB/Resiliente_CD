import RPi.GPIO as gpio
from time import sleep
import os
import logging

logging.basicConfig(filename='/home/pi/Resiliente_CD/logs/apagado.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%d/%m/%Y %H:%M:%S')

gpio.setmode(gpio.BCM)
gpio.setwarnings(False)
gpio.setup(18, gpio.IN)

try:
	#logging.info("[+] Script de apagado seguro")
	while True:
		if gpio.input(18):
			logging.warning("[!] Apagando sub modulo de controlador central (Raspberry Pi)")
			result = os.popen("sudo shutdown -h now").read()
		#sleep(3)
except KeyboardInterrupt:
	logging.info("[!] Deteniendo...")
	gpio.cleanup()
