'''Disparador.py:
			- Error en Monitoreo		[x]
			- Notificacion de Activacion	[ ]
			- Request/response Monitoreo	[ ]
'''
import time
import RPi.GPIO as gpio
import sqlite3
import sftp as sftp
import json
import os
gpio.setmode(gpio.BCM)
gpio.setwarnings(False)
gpio.setup(23, gpio.OUT, initial=0)

#Activacion
inicio = 0
final = 0
audio_param = 0
t_mensaje = 0

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
			'boton_activ':0,
			'boton_cancel':0,
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
		monit_request_response() #Funcion para verificar solicitud-monit de web
		activ_request(conn) #Funcion para atender Activacion via web
		global inicio,final
		print("--> Epoch actual: " + str(int(time.time())-18000))
		print("--> Epoch de inicio: "+str(inicio))
		print("--> Epoch de fin: "+str(final))
		if (int(time.time()) - 18000) >= int(inicio) and (int(time.time()) - 18000) <= int(final) and t_mensaje != "cancela":
			gpio.output(23,1)
			d = int(final) - (int(time.time()) - 18000)
			print("Duración: "+str(d)+" segundos")
		else:
			gpio.output(23,0)
		conn.close()
		time.sleep(1)

def activ_request(conn):
	try:
		with open('/home/pi/Resiliente_CD/Activation.json','r') as f_act:
			print("[+] Existe Activacion via web")
			p_act = json.load(f_act)
			try:
				print("[+] Insertando a DB: resiliente.db")
				conn.execute('''INSERT INTO activacion (slave,identificador,fecha_hora,estado,tipo_mensaje,ambito,idioma,categoria,evento,tipo_respuesta,urgencia,severidad,certeza,color_alerta,fecha_efectivo,fecha_inicio,fecha_fin,
					area,texto) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (p_act["data"]["slave"],p_act["data"]["identificador"],p_act["data"]["fecha_hora"],p_act["data"]["estado"],p_act["data"]["tipo_mensaje"],
					p_act["data"]["ambito"],p_act["data"]["idioma"],p_act["data"]["categoria"],p_act["data"]["evento"],p_act["data"]["tipo_respuesta"],p_act["data"]["urgencia"],p_act["data"]["severidad"],
					p_act["data"]["certeza"],p_act["data"]["color_alerta"],p_act["data"]["fecha_efectivo"],p_act["data"]["fecha_inicio"],p_act["data"]["fecha_fin"],p_act["data"]["area"],p_act["data"]["texto"]))
				conn.commit()
			except sqlite3.Error as e:
				print("[!] Sqlite3 error, ID: ",e.args[0])
			print("[+] Extrayendo parámetros de audio")
			var_audio = {
				'estado':p_act["data"]["estado"],
				'evento':p_act["data"]["evento"],
				'severidad':p_act["data"]["severidad"],
				'respuesta':p_act["data"]["tipo_respuesta"],
				'urgencia':p_act["data"]["urgencia"],
				'mensaje':p_act["data"]["tipo_mensaje"],
			}
			print("[+] Generando fichero de audio 'audio_param.json' ")
			with open('audio_param.json','w') as file:
				json.dump(var_audio,file,indent=4)
			os.system('rm Activation.json')
	except FileNotFoundError:
		print("[!] No existe activacion via web")

def monit_request_response():
	#verificar request de monitoreo y responder
	try:
		with open('/home/pi/Resiliente_CD/Request.json','r') as f_rq:
			print("[+] Existe solicitud de monitoreo")
			rq = json.load(f_rq)
			flag = {
				'gabinete':False,
				'controlador_digital':False,
				'amplificador_izq':False,
				'rds':False,
				'tdt':False,
				'manual':False,
				'amplificador_der':False
			}
			if rq['type'] == "Request":
				for m in rq['modules']:
					flag[m] = True
				re = {
					'type':"Response"
				}
				for f in flag.items():
					if f[1] == True:
						re[f[0]] = p_sistema[f[0]]['data']
				sftp.envio(re,name="Response")
			else:
				print("[!] Request.json no válido: Error")
			os.system('rm Response.json Request.json')
	except FileNotFoundError:
		print("[!] No existe solicitud de monitoreo")

def get_activ(conn):
	global inicio, final, t_mensaje
	print("[+] Extrayendo parámetros tiempo de inicio - final  del ultimo registro de activación")
	cur = conn.cursor()
	cur.execute('''SELECT fecha_inicio,fecha_fin,tipo_mensaje FROM activacion WHERE ID=(SELECT MAX(ID) FROM activacion)''')
	tiempos = cur.fetchall()
	for x in tiempos:
		inicio = x[0]
		final = x[1]
		t_mensaje = x[2]

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
	cur.execute('''SELECT fecha,boton_activ,boton_cancel,temperature,current1,voltage1,current2,voltage2 FROM manual WHERE ID=(SELECT MAX(ID) FROM manual)''')
	pManual_monit = cur.fetchall()
	for x in pManual_monit:
		p_sistema['manual']['data']['fecha'] = x[0]
		p_sistema['manual']['data']['boton_activ'] = x[1]
		p_sistema['manual']['data']['boton_cancel'] = x[2]
		p_sistema['manual']['data']['temperature'] = x[3]
		p_sistema['manual']['data']['current1'] = x[4]
		p_sistema['manual']['data']['voltage1'] = x[5]
		p_sistema['manual']['data']['current2'] = x[6]
		p_sistema['manual']['data']['voltage2'] = x[7]
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
			p_sistema['rds']['type'] = "Error"
			print("[!] Enviando reporte JSON a servidor web...")
			sftp.envio(p_sistema['rds'],name="Error")
			os.system("rm Error.json")
	elif mod == 'manual':
		if p_sistema['manual']['data']['fecha'] > (int(time.time()) -18010):
			print("[+] Parámetros ",mod,": OK")
		else:
			print("[!] Parámetros ",mod,": Error")
			p_sistema['manual']['type'] = "Error"
			print(p_sistema['manual']['data']['fecha'])
			print("[!] Enviando reporte JSON a servidor web...")
			sftp.envio(p_sistema['manual'],name="Error")
			os.system("rm Error.json")

if __name__ == '__main__':
	print("[+] Script controlador de activacion")
	main()
