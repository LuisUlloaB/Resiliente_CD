import os, sys
import json
from pymodbus.server.async import StartSerialServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusBinaryFramer

from twisted.internet.task import LoopingCall

reg = [0] * 12

def updating_writer(a):
	context = a[0]
	fx = 3
	slave_id = 1
	address = 0
	values = context[slave_id].getValues(fx, address, count=11)
	#values = [v + 1 for v in values]
	print("=============================================")
	for v in values:
		print(v)
	print("=============================================")

	ipv4 = os.popen('ip addr show eth0').read().split("inet ")[1].split("/")[0]
	ipv4 = ipv4.split('.')
	for i in range(4):
		ipv4[i] = int(ipv4[i])
	context[slave_id].setValues(fx, address, ipv4)

	with open('/home/pi/Resiliente_CD/config/config.json') as f:
		sistema = json.load(f)
		srv = sistema['servidor']['ip']
	ping = os.popen('ping '+str(srv)+' -c1').read().split("received, ")[1].split(", time")[0]
	if ping == "0% packet loss":
		context[slave_id].setValues(fx, address + 4, [1])
	else:
		context[slave_id].setValues(fx, address + 4, [0])

	rtc = os.popen('sudo hwclock -r').read().split('.')[0].split(' ')
	date = rtc[0].split('-')
	hour = rtc[1].split(':')
	for i in range(3):
		date[i] = int(date[i])
		hour[i] = int(hour[i])
	date.reverse()
	context[slave_id].setValues(fx, address + 5, date)
	context[slave_id].setValues(fx, address + 8, hour)
	#print(date)
	#print(hour)


def run_server(puerto='none', slave_id=1, modo='normal'):
	global reg

	store = ModbusSlaveContext(
		hr=ModbusSequentialDataBlock(slave_id, reg))

	context = ModbusServerContext(slaves=store, single=True)

	identity = ModbusDeviceIdentification()
	identity.VendorName = 'Pymodbus'
	identity.ProductCode = 'PM'
	identity.VendorUrl = 'http://github.com/riptideio/pymodbus/'
	identity.ProductName = 'Pymodbus Server'
	identity.ModelName = 'Pymodbus Server'
	identity.MajorMinorRevision = '2.2.0'


	time = 3
	loop = LoopingCall(f=updating_writer,  a=(context,))
	loop.start(time, now=False)
	# RTU:
	StartSerialServer(context, framer=ModbusRtuFramer, identity=identity, port=puerto, timeout=1, baudrate=19200)


if __name__ == "__main__":
	try:
		with open('/home/pi/Resiliente_CD/config/config.json') as conf:
			sys = json.load(conf)
			test_port = sys['puertos']['test']['logico']
			slave = sys['pi']['test_modbus_id']
			modo = sys['pi']['modo']
		test_port = "/dev/" + test_port
		print("Puerto test: " + test_port)
		print("ID Slave [ModBus Test]: " + str(slave))
		print("Modo de operacion: "+modo)
		run_server(puerto=test_port,slave_id=slave,modo=modo)
	except KeyboardInterrupt:
		print("[!] Saliendo...")
