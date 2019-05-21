'''Disparador.py:
			- Error en Monitoreo		[x]
			- Notificacion de Activacion	[x]
			- Request/response Monitoreo	[x]
			- Adaptar a todos los modulos	[ ]
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
	'gabinete':{
		'idname':"gabinete",
		'type':"",
		'data':{
			'sensor_puerta':0,
			'temperatura':0,
			'battery_current':0,
			'battery_voltage':0
		}
	},
	'controlador_digital':{
		'idname':"controlador_digital",
		'type':"",
		'data':{
			'Temperatura':0,
			'C_Fuente':0,
			'V_Fuente':0,
			'C_PoE':0,
			'V_PoE':0,
			'C_PreAmpli':0,
			'V_PreAmpli':0,
			'C_MUX':0,
			'V_MUX':0,
			'C_Raspberry':0,
			'V_Raspberry':0,
			'C_Rele':0,
			'V_Rele':0,
			'C_Switch':0,
			'V_Switch':0,
			'C_Ampli':0,
			'V_Ampli':0
		}
	},
	'amp_izquierdo':{
		'idname':"amp_izquierdo",
		'type':"",
		'data':{
			'temperatura':0,
			'current_1':0,
			'voltage_1':0,
			'current_2':0,
			'voltage_2':0
		}
	},
	'rds':{
		'idname':"rds",
		'type': "",
		'data':{
			'frequency':0,
			'lock':0,
			'rds_state':0,
			'state_2a':0,
			'state_9a':0,
			'state_11a':0,
			'general_state':0
		}
	},
	'tdt':{
		'idname':"tdt",
		'type':"",
		'data':{
			'frequency':0,
			'lock':0,
			'bandwidth':0,
			'area':0,
			'flag_EWBS':0,
			'flag_TMCC':0
		}
	},
	'manual':{
		'idname':"manual",
		'type':"",
		'data':{
			'fecha':0,
			'boton_activ':0,
			'boton_cancel':0
		}
	},
	'amp_derecho':{
		'idname':"amp_derecho",
		'type':"",
		'data':{
			'temperatura':0,
			'current_1':0,
			'voltage_1':0,
			'current_2':0,
			'voltage_2':0
		}
	},
	'rds_sensores':{
		'idname':"rds_sensores",
		'type':"",
		'data':{
			'temperatura':0,
			'current_1':0,
			'voltage_1':0,
			'current_2':0,
			'voltage_2':0
		}
	},
	'tdt_sensores':{
		'idname':"tdt_sensores",
		'type':"",
		'data':{
			'temperatura':0,
			'current_1':0,
			'voltage_1':0,
			'current_2':0,
			'voltage_2':0
		}
	},
	'manual_sensores':{
		'idname':"manual_sensores",
		'type':"",
		'data':{
			'temperatura':0,
			'current_1':0,
			'voltage_1':0,
			'current_2':0,
			'voltage_2':0
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
			if p_act["data"]["tipo_mensaje"] != "cancela":
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
				'amp_izquierdo':False,
				'rds':False,
				'tdt':False,
				'manual':False,
				'amp_derecho':False,
				'rds_sensores':False,
				'tdt_sensores':False,
				'manual_sensores':False
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
	cur.execute('''SELECT frequency,lock,rds_state,state_2a,state_9a,state_11a,general_state FROM rds WHERE ID=(SELECT MAX(ID) FROM rds)''')
	pRDS_monit = cur.fetchall()
	for x in pRDS_monit:
		p_sistema['rds']['data']['frequency'] = x[0]
		p_sistema['rds']['data']['lock'] = x[1]
		p_sistema['rds']['data']['rds_state'] = x[2]
		p_sistema['rds']['data']['state_2a'] = x[3]
		p_sistema['rds']['data']['state_9a'] = x[4]
		p_sistema['rds']['data']['state_11a'] = x[5]
		p_sistema['rds']['data']['general_state'] = x[6]
	verificar_patron(mod = 'rds')

def get_monit_manual(conn):
	global p_sistema
	print("[+] Extrayendo parámetros de monitoreo 'manual'")
	cur = conn.cursor()
	cur.execute('''SELECT fecha,boton_activ,boton_cancel FROM manual WHERE ID=(SELECT MAX(ID) FROM manual)''')
	pManual_monit = cur.fetchall()
	for x in pManual_monit:
		p_sistema['manual']['data']['fecha'] = x[0]
		p_sistema['manual']['data']['boton_activ'] = x[1]
		p_sistema['manual']['data']['boton_cancel'] = x[2]
	verificar_patron(mod = 'manual')

def get_monit_tdt(conn):
	global p_sistema
	print("[+] Extrayendo parámetros de monitoreo 'tdt'")
	cur = conn.cursor()
	cur.execute('''SELECT frequency,lock,bandwidth,area,flag_EWBS,flag_TMCC FROM tdt WHERE ID=(SELECT MAX(ID) FROM tdt)''')
	pTDT_monit = cur.fetchall()
	for x in pTDT_monit:
		p_sistema['tdt']['data']['frequency'] = x[0]
		p_sistema['tdt']['data']['lock'] = x[1]
		p_sistema['tdt']['data']['bandwidth'] = x[2]
		p_sistema['tdt']['data']['area'] = x[3]
		p_sistema['tdt']['data']['flag_EWBS'] = x[4]
		p_sistema['tdt']['data']['flag_TMCC'] = x[5]
	verificar_patron(mod = 'tdt')

def get_monit_gabinete(conn):
	global p_sistema
	print("[+] Extrayendo parámetros de monitoreo 'gabinete'")
	cur = conn.cursor()
	cur.execute('''SELECT sensor_puerta,temperatura,battery_current,battery_voltage FROM gabinete WHERE ID=(SELECT MAX(ID) FROM gabinete)''')
	pGabinete_monit = cur.fetchall()
	for x in pGabinete_monit:
		p_sistema['gabinete']['data']['sensor_puerta'] = x[0]
		p_sistema['gabinete']['data']['temperatura'] = x[1]
		p_sistema['gabinete']['data']['battery_current'] = x[2]
		p_sistema['gabinete']['data']['battery_voltage'] = x[3]
	verificar_patron(mod = 'gabinete')

def get_monit_controlador_digital(conn):
	global p_sistema
	print("[+] Extrayendo parámetros de monitoreo 'controlador_digital'")
	cur = conn.cursor()
	cur.execute('''SELECT Temperatura,C_Fuente,V_Fuente,C_PoE,V_PoE,C_PreAmpli,V_PreAmpli,C_MUX,V_MUX,C_Raspberry,V_Raspberry,C_Rele,V_Rele,
			C_Switch,V_Switch,C_Ampli,V_Ampli FROM controlador_digital WHERE ID=(SELECT MAX(ID) FROM controlador_digital)''')
	pControlador_monit = cur.fetchall()
	for x in pControlador_monit:
		p_sistema['controlador_digital']['data']['Temperatura'] = x[0]
		p_sistema['controlador_digital']['data']['C_Fuente'] = x[1]
		p_sistema['controlador_digital']['data']['V_Fuente'] = x[2]
		p_sistema['controlador_digital']['data']['C_PoE'] = x[3]
		p_sistema['controlador_digital']['data']['V_PoE'] = x[4]
		p_sistema['controlador_digital']['data']['C_PreAmpli'] = x[5]
		p_sistema['controlador_digital']['data']['V_PreAmpli'] = x[6]
		p_sistema['controlador_digital']['data']['C_MUX'] = x[7]
		p_sistema['controlador_digital']['data']['V_MUX'] = x[8]
		p_sistema['controlador_digital']['data']['C_Raspberry'] = x[9]
		p_sistema['controlador_digital']['data']['V_Raspberry'] = x[10]
		p_sistema['controlador_digital']['data']['C_Rele'] = x[11]
		p_sistema['controlador_digital']['data']['V_Rele'] = x[12]
		p_sistema['controlador_digital']['data']['C_Switch'] = x[13]
		p_sistema['controlador_digital']['data']['V_Switch'] = x[14]
		p_sistema['controlador_digital']['data']['C_Ampli'] = x[15]
		p_sistema['controlador_digital']['data']['V_Ampli'] = x[16]
	verificar_patron(mod = 'controlador_digital')

def get_monit_amp_derecho(conn):
	global p_sistema
	print("[+] Extrayendo parámetros de monitoreo 'amp_derecho'")
	cur = conn.cursor()
	cur.execute('''SELECT temperatura,current_1,voltage_1,current_2,voltage_2 FROM amp_derecho WHERE ID=(SELECT MAX(ID) FROM amp_derecho)''')
	pAmp_derecho_monit = cur.fetchall()
	for x in pAmp_derecho_monit:
		p_sistema['amp_derecho']['data']['temperatura'] = x[0]
		p_sistema['amp_derecho']['data']['current_1'] = x[1]
		p_sistema['amp_derecho']['data']['voltage_1'] = x[2]
		p_sistema['amp_derecho']['data']['current_2'] = x[3]
		p_sistema['amp_derecho']['data']['voltage_2'] = x[4]
	verificar_patron(mod = 'amp_derecho')

def get_monit_amp_izquierdo(conn):
	global p_sistema
	print("[+] Extrayendo parámetros de monitoreo 'amp_izquierdo'")
	cur = conn.cursor()
	cur.execute('''SELECT temperatura,current_1,voltage_1,current_2,voltage_2 FROM amp_izquierdo WHERE ID=(SELECT MAX(ID) FROM amp_izquierdo)''')
	pAmp_izquierdo_monit = cur.fetchall()
	for x in pAmp_izquierdo_monit:
		p_sistema['amp_izquierdo']['data']['temperatura'] = x[0]
		p_sistema['amp_izquierdo']['data']['current_1'] = x[1]
		p_sistema['amp_izquierdo']['data']['voltage_1'] = x[2]
		p_sistema['amp_izquierdo']['data']['current_2'] = x[3]
		p_sistema['amp_izquierdo']['data']['voltage_2'] = x[4]
	verificar_patron(mod = 'amp_izquierdo')

def get_monit_rds_sensores(conn):
	global p_sistema
	print("[+] Extrayendo parámetros de monitoreo 'rds_sensores'")
	cur = conn.cursor()
	cur.execute('''SELECT temperatura,current_1,voltage_1,current_2,voltage_2 FROM rds_sensores WHERE ID=(SELECT MAX(ID) FROM rds_sensores)''')
	pRDS_sensores_monit = cur.fetchall()
	for x in pRDS_sensores_monit:
		p_sistema['rds_sensores']['data']['temperatura'] = x[0]
		p_sistema['rds_sensores']['data']['current_1'] = x[1]
		p_sistema['rds_sensores']['data']['voltage_1'] = x[2]
		p_sistema['rds_sensores']['data']['current_2'] = x[3]
		p_sistema['rds_sensores']['data']['voltage_2'] = x[4]
	verificar_patron(mod = 'rds_sensores')

def get_monit_tdt_sensores(conn):
	global p_sistema
	print("[+] Extrayendo parámetros de monitoreo 'tdt_sensores'")
	cur = conn.cursor()
	cur.execute('''SELECT temperatura,current_1,voltage_1,current_2,voltage_2 FROM tdt_sensores WHERE ID=(SELECT MAX(ID) FROM tdt_sensores)''')
	pTDT_sensores_monit = cur.fetchall()
	for x in pTDT_sensores_monit:
		p_sistema['tdt_sensores']['data']['temperatura'] = x[0]
		p_sistema['tdt_sensores']['data']['current_1'] = x[1]
		p_sistema['tdt_sensores']['data']['voltage_1'] = x[2]
		p_sistema['tdt_sensores']['data']['current_2'] = x[3]
		p_sistema['tdt_sensores']['data']['voltage_2'] = x[4]
	verificar_patron(mod = 'tdt_sensores')

def get_monit_manual_sensores(conn):
	global p_sistema
	print("[+] Extrayendo parámetros de monitoreo 'manual_sensores'")
	cur = conn.cursor()
	cur.execute('''SELECT temperatura,current_1,voltage_1,current_2,voltage_2 FROM manual_sensores WHERE ID=(SELECT MAX(ID) FROM manual_sensores)''')
	pTDT_sensores_monit = cur.fetchall()
	for x in pTDT_sensores_monit:
		p_sistema['manual_sensores']['data']['temperatura'] = x[0]
		p_sistema['manual_sensores']['data']['current_1'] = x[1]
		p_sistema['manual_sensores']['data']['voltage_1'] = x[2]
		p_sistema['manual_sensores']['data']['current_2'] = x[3]
		p_sistema['manual_sensores']['data']['voltage_2'] = x[4]
	verificar_patron(mod = 'manual_sensores')

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
		if p_sistema['manual']['data']['fecha'] > (int(time.time()) -18015):
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
