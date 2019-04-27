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
estado = False
audio_param = 0

#RDS
p_rds = {
	'rds':{
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
}
sorted(p_rds.items())

def main():
	while True:
		try:
			print("[+] Conectando a la base de datos: resiliente.db")
			conn = sqlite3.connect('resiliente.db')
			get_activ(conn)
			get_monit_rds(conn)
		except sqlite3.Error as e:
			print("[!] Sqlite3 error, ID: ",e.args[0])
		conn.close()
		global inicio,final,estado
		print("--> Epoch actual: " + str(int(time.time())-18000))
		print("--> Epoch de inicio: "+inicio)
		print("--> Epoch de fin: "+final)
		if (int(time.time()) - 18000) >= int(inicio) and (int(time.time()) - 18000) <= int(final):
			gpio.output(23,1)
			estado = True
			d = int(final) - (int(time.time()) - 18000)
			print("Duración: "+str(d)+" segundos")
		else:
			gpio.output(23,0)
			estado = False
		time.sleep(1)

def get_activ(conn):
	print("[+] Extrayendo parámetros tiempo de inicio - final  del ultimo registro de activación")
	cur = conn.cursor()
	p_activ = cur.execute('''SELECT fecha_inicio,fecha_fin FROM activacion WHERE ID=(SELECT MAX(ID) FROM activacion)''')
	global inicio,final,estado
	for x in p_activ:
		inicio = x[0]
		final = x[1]
	#with open('audio_param-json') as f:
	#	audio_param = json.load(f)

def get_monit_rds(conn):
	print("[+] Extrayendo parámetros de monitoreo rds")
	cur = conn.cursor()
	pRDS_monit = cur.execute('''SELECT frequency,lock,rds_state,state_2a,state_9a,state_11a,general_state,temperature,current1,voltage1,current2,voltage2 FROM rds WHERE ID=(SELECT MAX(ID) FROM rds)''')
	global p_rds
	for x in pRDS_monit:
		p_rds['rds']['frequency'] = x[0]
		p_rds['rds']['lock'] = x[1]
		p_rds['rds']['rds_state'] = x[2]
		p_rds['rds']['state_2a'] = x[3]
		p_rds['rds']['state_9a'] = x[4]
		p_rds['rds']['state_11a'] = x[5]
		p_rds['rds']['general_state'] = x[6]
		p_rds['rds']['temperature'] = x[7]
		p_rds['rds']['current1'] = x[8]
		p_rds['rds']['voltage1'] = x[9]
		p_rds['rds']['current2'] = x[10]
		p_rds['rds']['voltage2'] = x[11]
	verificar_patron(mod = 'rds')

def verificar_patron(mod):
	print('[*] Verificando datos: monitoreo ',mod)
	if mod == 'rds':
		global p_rds
		#p_rds['rds']['frequency']=99.9 # Error (para fines de prueba)
		if (p_rds['rds']['frequency'] == 107.9 or p_rds['rds']['frequency'] == 92.5) and p_rds['rds']['lock'] == 1:
			print("[+] Parámetros ",mod,": OK")
		else:
			print("[!] Parámetros ",mod,": Error")
			print("[!] Enviando reporte JSON a servidor web...")
			sftp.envio(p_rds)

if __name__ == '__main__':
	print("[+] Script controlador de activacion")
	main()
