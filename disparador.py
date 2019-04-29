#!/usr/bin/python
'''Creación de variables de entorno en: /etc/profile
ejecutar con: sudo nano /etc/profile

poner:
export F_CREACION="0"
export F_INICIO="0"
export F_FINAL="0"
export F_EFECTIVO="0"
'''
import time
import RPi.GPIO as gpio
import sqlite3
import sftp as sftp
import json
gpio.setmode(gpio.BCM)
gpio.setwarnings(False)
gpio.setup(23, gpio.OUT, initial=0)

#Activacion
inicio = 0
final = 0
audio_param = 0

#parámetros del sistema
p_sistema = {
	'rds':{
		'idname': "rds",
		'type': "",
		'data':{
			'frequency':0,
			'lock':0,
			'rds_state':0,
			'state_2a':0,
			'state_9a':0,
			'state_11a':0,
			'general_state':0,
			'temperature':0,
			'current1':0,
			'voltage1':0,
			'current2':0,
			'voltage2':0
		}
	},
	'manual':{
		'idname':"manual",
		'type':"",
		'data':{
			'fecha':0,
			'boton':0,
			'temperature':0,
			'current1':0,
			'voltage1':0,
			'current2':0,
			'voltage2':0
		}
	}
}
#sorted(p_sistema.items())

def main():
	while True:
		try:
			print("[+] Conectando a la base de datos: resiliente.db")
			conn = sqlite3.connect('resiliente.db')
			get_activ(conn)
			get_monit_rds(conn)
			get_activ(conn)
			get_monit_manual(conn)
			get_activ(conn)
		except sqlite3.Error as e:
			print("[!] Sqlite3 error, ID: ",e.args[0])
		conn.close()
		global inicio,final
		print("--> Epoch actual: " + str(int(time.time())-18000))
		print("--> Epoch de inicio: "+str(inicio))
		print("--> Epoch de fin: "+str(final))
		if (int(time.time()) - 18000) >= int(inicio) and (int(time.time()) - 18000) <= int(final):
			gpio.output(23,1)
			d = int(final) - (int(time.time()) - 18000)
			print("Duración: "+str(d)+" segundos")
		else:
			gpio.output(23,0)
		#break
		time.sleep(1)

def get_activ(conn):
	global inicio, final
	print("[+] Extrayendo parámetros tiempo de inicio - final  del ultimo registro de activación")
	cur = conn.cursor()
	cur.execute('''SELECT fecha_inicio,fecha_fin FROM activacion WHERE ID=(SELECT MAX(ID) FROM activacion)''')
	tiempos = cur.fetchall()
	for x in tiempos:
		inicio = x[0]
		final = x[1]
	#with open('audio_param-json') as f:
	#	audio_param = json.load(f)

def get_monit_rds(conn):
	global p_sistema
	print("[+] Extrayendo parámetros de monitoreo 'rds'")
	cur = conn.cursor()
	cur.execute('''SELECT frequency,lock,rds_state,state_2a,state_9a,state_11a,general_state,temperature,current1,voltage1,current2,voltage2 FROM rds WHERE ID=(SELECT MAX(ID) FROM rds)''')
	pRDS_monit = cur.fetchall()
	for x in pRDS_monit:
		p_sistema['rds']['data']['frequency'] = x[0]
		p_sistema['rds']['data']['lock'] = x[1]
		p_sistema['rds']['data']['rds_state'] = x[2]
		p_sistema['rds']['data']['state_2a'] = x[3]
		p_sistema['rds']['data']['state_9a'] = x[4]
		p_sistema['rds']['data']['state_11a'] = x[5]
		p_sistema['rds']['data']['general_state'] = x[6]
		p_sistema['rds']['data']['temperature'] = x[7]
		p_sistema['rds']['data']['current1'] = x[8]
		p_sistema['rds']['data']['voltage1'] = x[9]
		p_sistema['rds']['data']['current2'] = x[10]
		p_sistema['rds']['data']['voltage2'] = x[11]
	verificar_patron(mod = 'rds')

def get_monit_manual(conn):
	global p_sistema
	print("[+] Extrayendo parámetros de monitoreo 'manual'")
	cur = conn.cursor()
	cur.execute('''SELECT fecha,boton,temperature,current1,voltage1,current2,voltage2 FROM manual WHERE ID=(SELECT MAX(ID) FROM manual)''')
	pManual_monit = cur.fetchall()
	for x in pManual_monit:
		p_sistema['manual']['data']['fecha'] = x[0]
		p_sistema['manual']['data']['boton'] = x[1]
		p_sistema['manual']['data']['temperature'] = x[2]
		p_sistema['manual']['data']['current1'] = x[3]
		p_sistema['manual']['data']['voltage1'] = x[4]
		p_sistema['manual']['data']['current2'] = x[5]
		p_sistema['manual']['data']['voltage2'] = x[6]
	verificar_patron(mod = 'manual')

def verificar_patron(mod):
	global p_sistema
	print('[*] Verificando datos: monitoreo ',mod)
	if mod == 'rds':
		#p_rds['rds']['frequency']=99.9 # Error (para fines de prueba)
		if (p_sistema['rds']['data']['frequency'] == 107.9 or p_sistema['rds']['data']['frequency'] == 92.5) and p_sistema['rds']['data']['lock'] == 1:
			print("[+] Parámetros ",mod,": OK")
		else:
			print("[!] Parámetros ",mod,": Error")
			print("[!] Enviando reporte JSON a servidor web...")
			sftp.envio(p_sistema['rds'])
	elif mod == 'manual':
		if p_sistema['manual']['data']['fecha'] > (int(time.time()) -18010):
			print("[+] Parámetros ",mod,": OK")
		else:
			print("[!] Parámetros ",mod,": Error")
			print(p_sistema['manual']['data']['fecha'])
			print("[!] Enviando reporte JSON a servidor web...")
			sftp.envio(p_sistema['manual'])

if __name__ == '__main__':
	print("[+] Script controlador de activacion")
	main()
