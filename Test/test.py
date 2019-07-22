import os, sys
import json
import time
from pymodbus.server.async import StartSerialServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusBinaryFramer

from twisted.internet.task import LoopingCall

sys.path.insert(0,'/home/pi/Resiliente_CD')
import activador

num_reg = 89
num_pruebas = 4
reg = [0] * num_reg
reg[85] = 0 # por defecto: eth0 enable
CAP = [0] * 74
f_creacion = [0] * 5 # Fecha de creacion del último CAP_PER recibido

def updating_writer(a):
	global num_reg, CAP, f_creacion, num_pruebas

	context = a[0]
	fx = 3
	slave_id = 1
	address = 0
	values = context[slave_id].getValues(fx, address, count=num_reg)

	# Imprime en pantalla los valores de los registros
	print("=============================================")
	for v in range(74):
	 	print(values[v + 11])
	print("Estado Prueba Activ: ", str(values[86]))
	print("=============================================")

	pruebas = context[slave_id].getValues(fx, address + 85, count=num_pruebas)

	# IPv4
	if context[slave_id].getValues(fx, address + 85, count=1)[0] == 0:
		ipv4 = os.popen('ip addr show eth0').read().split("inet ")[1].split("/")[0]
		ipv4 = ipv4.split('.')
		for i in range(4):
			ipv4[i] = int(ipv4[i])
		context[slave_id].setValues(fx, address, ipv4)

	if pruebas[0] == 1:
		"""
		Grupo de Activación : MÓDULO CONTROLADOR DIGITAL
		Prueba RTC
		"""
		# Apagar interface eth0
		os.system('sudo ifconfig eth0 down')

		# Conexión con el servidor
		with open('/home/pi/Resiliente_CD/config/config.json') as f:
			sistema = json.load(f)
			srv = sistema['servidor']['ip']
		try:
			ping = os.popen('ping '+str(srv)+' -c1').read().split("received, ")[1].split(", time")[0]
			if ping == "0% packet loss":
				context[slave_id].setValues(fx, address + 4, [1])
			else:
				context[slave_id].setValues(fx, address + 4, [0])
		except:
			context[slave_id].setValues(fx, address + 4, [0])

		# RTC
		rtc = os.popen('sudo hwclock -r').read().split('.')[0].split(' ')
		date = rtc[0].split('-')
		hour = rtc[1].split(':')
		for i in range(3):
			date[i] = int(date[i])
			hour[i] = int(hour[i])
		date.reverse()
		context[slave_id].setValues(fx, address + 5, date)
		context[slave_id].setValues(fx, address + 8, hour)
	else:
		# Encender interface eth0
		os.system('sudo ifconfig eth0 up')


	if pruebas[1] == 1:
		# CAP
		CAP = context[slave_id].getValues(fx, address + 11, count=74)
		if (CAP[12] != f_creacion[0] and CAP[13] != f_creacion[1] and
			CAP[14] != f_creacion[2] and CAP[15] != f_creacion[3] and
			CAP[16] != f_creacion[4]):
			if f_creacion[0] == 0 and f_creacion[1] == 0:
				print("primer intento exitoso!")
				# activador.activar(reg=CAP,id_slave=0,primer_intento=True)
			elif f_creacion[0] != 0 and f_creacion[1] != 0:
				print("intento exitoso!!")
				# activador.activar(reg=CAP,id_slave=0,primer_intento=False)
			for i in range(5):
				f_creacion[i] = CAP[i + 12]



def run_server(puerto='none', slave_id=1, modo='normal'):
	global reg

	store = ModbusSlaveContext(
		hr=ModbusSequentialDataBlock(slave_id, reg))

	context = ModbusServerContext(slaves=store, single=True)

	identity = ModbusDeviceIdentification()
	identity.VendorName = 'INICTEL-UNI'
	identity.ProductCode = 'MOD'
	identity.VendorUrl = 'http://github.com/riptideio/pymodbus/'
	identity.ProductName = 'CONTROLADOR DIGITAL - TEST'
	identity.ModelName = 'Pymodbus Server'
	identity.MajorMinorRevision = '1.0'


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
