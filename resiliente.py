'''resiliente.py -  PyModBus#1 - 	Raspberry pi -> Master

'''
import json
import activador as activ
import time
import sqlite3
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.register_read_message import ReadInputRegistersResponse
import pymodbus.exceptions

primer_act = True
def main():
	try:
		with open('/home/pi/Resiliente_CD/config.json','r') as cfg:
			sistema = json.load(cfg)
	except FileNotFoundError:
		print("[!] NO EXISTE EL ARCHIVO")
		return -1

	activ_monit_port = '/dev/' + sistema['puertos']['monit_activ']['logico']
	modulos = sistema['modulos']

	client = ModbusClient(method='rtu', port=activ_monit_port, stopbits=1, bytesize=8, parity='N', baudrate=19200, timeout=2)
	connection = client.connect()

	if connection == True:
		print("|-[+] ModBus Monitoreo creado!")
	else:
		print("|-[!] Error al crear ModBus Monitoreo")


	#Set RTC - Módulo Manual
	print("|-[*] Configurando RTC Módulo Manual")
	f = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
	f_rtc = [int(f[:4]),int(f[5:7]),int(f[8:10]),int(f[11:13]),int(f[14:16]),int(f[17:])]
	set = client.write_registers(0,f_rtc,unit = 6)
	global primer_act

	try:
		while True:
			for mod in sorted(modulos.items()):
				reg = client.read_holding_registers(0,mod[1]['monit_tamanio'],unit=int(mod[0]))
				if not reg.isError():
					print("|-[+] Registros Monitoreo ",mod[1]['nombre'],": ",reg.registers)
					if mod[0] == '4':
						reg.registers[0] /= 10.0
						try:
							print("\t└-[+] Conectando a la base de datos: resiliente.db")
							conn = sqlite3.connect('resiliente.db')
							print("\t└-[+] Insertando registros en tabla: ",mod[1]['nombre'])
							conn.execute('''INSERT INTO rds (frequency,lock,rds_state,state_2a,state_9a,state_11a,general_state,temperature,current1,voltage1,current2,voltage2) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', reg.registers)
							conn.commit()
						except sqlite3.Error as e:
							print("\t└-[!] Sqlite3 error, ID: ",e.args[0])
						else:
							conn.close()
							if reg.registers[4] == 1 or reg.registers[5] == 1:
								print("\t\t└--[!][!][!][!][!]******************** Intento de Activación - RDS ********************[!][!][!][!][!]")
								act = client.read_holding_registers(mod[1]['monit_tamanio'],(86-mod[1]['monit_tamanio']),unit=int(mod[0]))
								if not act.isError():
									print("\t\t\t└---[+] Registros Activacion via ",mod[1]['nombre'],": ",act.registers)
									if primer_act == True:
										activ.activar(act.registers,int(mod[0]),primer_intento=True)
										primer_act = False
									else:
										activ.activar(act.registers,int(mod[0]))
								else:
									print("\t\t\t└---[!] No se pudo conseguir registros de Activacion ",mod[1]['nombre'])
					elif mod[0] == '6':
						rtc_manual = formato_fecha(reg.registers)
						reg.registers[7] /= 10.0
						try:
							print("\t└-[+] Conectando a la base de datos: resiliente.db")
							conn = sqlite3.connect('resiliente.db')
							print("\t└-[+] Insertando registros en tabla: ",mod[1]['nombre'])
							conn.execute('''INSERT INTO manual (fecha,boton,temperature,current1,voltage1,current2,voltage2) VALUES (?,?,?,?,?,?,?)''',(rtc_manual,reg.registers[6],reg.registers[7],reg.registers[8],reg.registers[9],reg.registers[10],reg.registers[11]))
							conn.commit()
						except sqlite3.Error as e:
							print("\t└-[!] Sqlite3 error, ID: ",e.args[0])
						else:
							conn.close()
							if reg.registers[6] == 1:
								print("\t\t└--[!][!][!][!][!]*****************Intento de Activación - MANUAL******************[!][!][!][!][!]")
								act = client.read_holding_registers(mod[1]['monit_tamanio'], (86-mod[1]['monit_tamanio']), unit = int(mod[0]))
								if not act.isError():
									print("\t\t\t└---[+] Registros Activacion via ",mod[1]['nombre'],": ",act.registers)
									if primer_act == True:
										activ.activar(act.registers,int(mod[0]),primer_intento=True)
										primer_act = False
									else:
										activ.activar(act.registers,int(mod[0]))
								else:
									print("\t\t\t└---[!] No se pudo conseguir registros de Activacion ",mod[1]['nombre'])
				else:
					print("|-[!] Módulo ",mod[1]['nombre']," no responde!")
	except KeyboardInterrupt:
		print("[!] Saliendo...")
		client.close()
		return 1

def formato_fecha(r):
	f = str(r[0])+"-"+str(r[1])+"-"+str(r[2])+" "+str(r[3])+":"+str(r[4])+":"+str(r[5])
	#print(f)
	timestamp = time.strptime(f, '%Y-%m-%d %H:%M:%S')
	epoch = int(time.mktime(timestamp)) - 18000
	#print(epoch)
	return epoch

if __name__ == '__main__':
	print("|-[+] Script principal de Módulo Controlador Digital")
	main()
