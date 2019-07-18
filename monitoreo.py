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
		with open('/home/pi/Resiliente_CD/config/config.json','r') as cfg:
			sistema = json.load(cfg)
	except FileNotFoundError:
		print("[!] NO EXISTE FICHERO DE CONFIGURACION")
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
			try:
				with open('/home/pi/Resiliente_CD/config/config.json') as cfg:
					sys = json.load(cfg)
					modo = sys['pi']['modo']
			except FileNotFoundError:
				print("[!] NO EXISTE FICHERO DE CONFIGURACION")
				return -1
			if modo != "normal":
				print("[!] RPi no configurado en modo normal")
				client.close()
				return 1

			for mod in sorted(modulos.items()):
				reg = client.read_holding_registers(0,mod[1]['monit_tamanio'],unit=int(mod[0]))
				if not reg.isError():
					print("|-[+] Registros Monitoreo ",mod[1]['nombre'],": ",reg.registers)
					try:
						print("\t└-[+] Conectando a la base de datos: resiliente.db")
						conn = sqlite3.connect('/home/pi/Resiliente_CD/resiliente.db')
					except sqlite3.Error as e:
						print("\t└-[!] Sqlite3 error, ID: ",e.args[0])
					else:
						if mod[0] == '1':	# Gabinete
							reg.registers[1] /= 10.0
							reg.registers[2] /= 10.0
							reg.registers[3] /= 10.0
							try:
								print("\t└-[+] Insertando registros en tabla: ",mod[1]['nombre'])
								conn.execute('''INSERT INTO gabinete (sensor_puerta,temperatura,battery_current,battery_voltage) VALUES (?,?,?,?)''',reg.registers)
								conn.commit()
							except sqlite3.Error as e:
								print("\t└-[!] Sqlite3 error, ID: ",e.args[0])
							conn.close()

						elif mod[0] == '2':	# Controlador-Digital
							for r in reg.registers:
								r /= 10.0
							try:
								print("\t└-[+] Insertando registros en tabla: ",mod[1]['nombre'])
								conn.execute('''INSERT INTO controlador_digital (Temperatura,C_Fuente,V_Fuente,C_PoE,V_PoE,C_PreAmpli,V_PreAmpli,C_MUX,V_MUX,C_Raspberry,V_Raspberry,C_Rele,V_Rele,C_Switch,V_Switch,C_Ampli,V_Ampli) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',reg.registers)
								conn.commit()
							except sqlite3.Error as e:
								print("\t└-[!] Sqlite3 error, ID: ",e.args[0])
							conn.close()

						elif mod[0] == '3':	# Ampli-Izquierdo
							for i in range(7):
								reg.registers[i] /= 10.0
							try:
								print("\t└-[+] Insertando registros en tabla: ",mod[1]['nombre'])
								conn.execute('''INSERT INTO amp_izquierdo (temperatura,C_Sensor,V_Sensor,C_Entrada,V_Entrada,C_Ampli_Bocina,V_Rele,enable_ampli) VALUES (?,?,?,?,?,?,?,?)''',reg.registers)
								conn.commit()
							except sqlite3.Error as e:
								print("\t└-[!] Sqlite3 error, ID: ",e.args[0])
							conn.close()

						elif mod[0] == '4':	# RDS
							reg.registers[0] /= 10.0
							try:
								print("\t└-[+] Insertando registros en tabla: ",mod[1]['nombre'])
								conn.execute('''INSERT INTO rds (frequency,lock,rds_state,state_2a,state_9a,state_11a,general_state) VALUES (?,?,?,?,?,?,?)''', reg.registers)
								conn.commit()
							except sqlite3.Error as e:
								print("\t└-[!] Sqlite3 error, ID: ",e.args[0])
							else:
								conn.close()
								if reg.registers[4] == 1 or reg.registers[5] == 1:
									print("\t\t└--[!][!][!][!][!]******************** Intento de Activación - RDS ********************[!][!][!][!][!]")
									act = client.read_holding_registers(mod[1]['monit_tamanio'],74,unit=int(mod[0]))
									if not act.isError():
										print("\t\t\t└---[+] Registros Activacion via ",mod[1]['nombre'],": ",act.registers)
										if primer_act == True:
											activ.activar(act.registers,int(mod[0]),primer_intento=True)
											primer_act = False
										else:
											activ.activar(act.registers,int(mod[0]))
									else:
										print("\t\t\t└---[!] No se pudo conseguir registros de Activacion ",mod[1]['nombre'])

						elif mod[0] == '5':	# TDT
							reg.registers[3] = str(reg.registers[3]) ##<- probar esta linea
							try:
								print("\t└-[+] Insertando registros en tabla: ",mod[1]['nombre'])
								conn.execute('''INSERT INTO tdt (frequency,lock,bandwidth,area,flag_EWBS,flag_TMCC) VALUES (?,?,?,?,?,?)''',reg.registers)
								conn.commit()
							except sqlite3.Error as e:
								print("\t└-[!] Sqlite3 error, ID: ",e.args[0])
							else:
								conn.close()
								if reg.registers[4] == 1:
									print("\t\t└--[!][!][!][!][!]******************** Intento de Activación - TDT ********************[!][!][!][!][!]")
									act = client.read_holding_registers(mod[1]['monit_tamanio'],74,unit=int(mod[0]))
									if not act.isError():
										print("\t\t\t└---[+] Registros Activacion via ",mod[1]['nombre'],": ",act.registers)
										if primer_act == True:
											activ.activar(act.registers,int(mod[0]),primer_intento=True)
											primer_act = False
										else:
											activ.activar(act.registers,int(mod[0]))
									else:
										print("\t\t\t└---[!] No se pudo conseguir registros de Activacion ",mod[1]['nombre'])

						elif mod[0] == '6':	# Manual
							rtc_manual = formato_fecha(reg.registers)
							try:
								print("\t└-[+] Insertando registros en tabla: ",mod[1]['nombre'])
								conn.execute('''INSERT INTO manual (fecha,boton_activ,boton_cancel) VALUES (?,?,?)''',(rtc_manual,reg.registers[6],reg.registers[7]))
								conn.commit()
							except sqlite3.Error as e:
								print("\t└-[!] Sqlite3 error, ID: ",e.args[0])
							else:
								conn.close()
								if reg.registers[6] == 1 or reg.registers[7] == 1:
									print("\t\t└--[!][!][!][!][!]*****************Intento de Activación/Cancelador - MANUAL******************[!][!][!][!][!]")
									act = client.read_holding_registers(mod[1]['monit_tamanio'], 74, unit = int(mod[0]))
									if not act.isError():
										print("\t\t\t└---[+] Registros Activacion via ",mod[1]['nombre'],": ",act.registers)
										if primer_act == True:
											activ.activar(act.registers,int(mod[0]),primer_intento=True)
											primer_act = False
										else:
											activ.activar(act.registers,int(mod[0]))
									else:
										print("\t\t\t└---[!] No se pudo conseguir registros de Activacion ",mod[1]['nombre'])

						elif mod[0] == '7':	# Ampli-Derecho
							for i in range(7):
								reg.registers[i] /= 10.0
							try:
								print("\t└-[+] Insertando registros en tabla: ",mod[1]['nombre'])
								conn.execute('''INSERT INTO amp_izquierdo (temperatura,C_Sensor,V_Sensor,C_Entrada,V_Entrada,C_Ampli_Bocina,V_Rele,enable_ampli) VALUES (?,?,?,?,?,?,?,?)''',reg.registers)
								conn.commit()
							except sqlite3.Error as e:
								print("\t└-[!] Sqlite3 error, ID: ",e.args[0])
							conn.close()

						elif mod[0] == '8':	# Sensado-Receptores
							for r in reg.registers:
								r /= 10.0
							try:
								print("\t└-[+] Insertando registros en tabla: ",mod[1]['nombre'])
								conn.execute('''INSERT INTO sensado_receptores (temperatura,C_sensado,V_sensado,C_RDS,V_RDS,C_TDT,V_TDT,C_manual,V_manual,C_entrada,V_entrada) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',reg.registers)
								conn.commit()
							except sqlite3.Error as e:
								print("\t└-[!] Sqlite3 error, ID: ",e.args[0])
							conn.close()
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
