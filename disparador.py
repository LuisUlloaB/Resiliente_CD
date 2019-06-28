'''Disparador.py:
			- Error en Monitoreo		[x]
			- Notificacion de Activacion	[x]
			- Request/response Monitoreo	[x]
			- Adaptar a todos los modulos	[x]
'''
import time
import RPi.GPIO as gpio
import sqlite3
import sftp as sftp
import json
import os
gpio.setmode(gpio.BCM)
gpio.setwarnings(False)
gpio.setup(13, gpio.OUT, initial=0)
gpio.setup(12, gpio.OUT, initial=0)

#Indicadores-LED
Leds = {
	'L_Encendido': [ 6 , 5 , 11 ],
	'L_Temp': [ 9 , 25 , 10 ],
	'L_Volt': [ 24 , 22 , 23 ],
	'L_Amp': [ 27 , 4 , 17 ]
}
for l in Leds.items():
	for x in l[1]:
		gpio.setup(x, gpio.OUT, initial=0)

#Activacion
last_slave = 0
inicio = 0
final = 0
audio_param = 0
t_mensaje = 0
ip_controlador = 0
tablas = 0

#Notificacion
flag_notif = False
notif = {
	'type':"Notification",
	'ip': "",
	"enabled_alert": "",
	"alert_way": ""
}

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
			'C_Sensor':0,
			'V_Sensor':0,
			'C_Entrada':0,
			'V_Entrada':0,
			'C_Ampli_Bocina':0,
			'V_Rele':0,
			'enable_ampli':0
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
			'flag_TMCC':0,
			'power':0
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
			'C_Sensor':0,
			'V_Sensor':0,
			'C_Entrada':0,
			'V_Entrada':0,
			'C_Ampli_Bocina':0,
			'V_Rele':0,
			'enable_ampli':0
		}
	},
	'sensado_receptores':{
		'idname':"sensado_receptores",
		'type':"",
		'data':{
			'temperatura':0,
			'C_sensado':0,
			'V_sensado':0,
			'C_RDS':0,
			'V_RDS':0,
			'C_TDT':0,
			'V_TDT':0,
			'C_manual':0,
			'V_manual':0,
			'C_entrada':0,
			'V_entrada':0
		}
	}
}
#sorted(p_sistema.items())

def main():
	global ip_controlador, tablas, notif, flag_notif, last_slave
	while True:
		try:
			with open('/home/pi/Resiliente_CD/config/config.json','r') as cfg:
				conf = json.load(cfg)
				ip_controlador = conf['pi']['ip']
				tablas = conf['pi']['tablas']
			print("[+] Conectando a la base de datos: resiliente.db")
			conn = sqlite3.connect('resiliente.db')
			get_activ(conn)
			#get_monit_gabinete(conn)
			#get_monit_controlador_digital(conn)
			#get_monit_amp_izquierdo(conn)
			get_monit_rds(conn)
			#get_monit_tdt(conn)
			get_monit_manual(conn)
			#get_monit_amp_derecho(conn)
			#get_monit_sensado_receptores(conn)
			get_activ(conn)
			if int( time.strftime("%H", time.localtime()) ) % 4 == 0 and int( time.strftime("%M", time.localtime()) ) == 0:
				backup_db(conn)
		except sqlite3.Error as e:
			print("[!] Sqlite3 error, ID: ",e.args[0])
		monit_request_response() #Funcion para verificar solicitud-monit de web
		activ_request(conn) #Funcion para atender Activacion via web
		global inicio,final
		print("--> Epoch actual: " + str(int(time.time())-18000))
		print("--> Epoch de inicio: "+str(inicio))
		print("--> Epoch de fin: "+str(final))
		if (int(time.time()) - 18000) >= int(inicio) and (int(time.time()) - 18000) <= int(final) and t_mensaje != "cancela" and t_mensaje != "Cancela":
			gpio.output(13,1)
			gpio.output(12,1)
			d = int(final) - (int(time.time()) - 18000)
			print("Duración: "+str(d)+" segundos")
			if flag_notif == False:
				flag_notif = True
				notif['ip'] = conf['pi']['ip']
				notif['enabled_alert'] = True
				notif['alert_way'] = conf['modulos'][str(last_slave)]['nombre']
				sftp.envio(notif,name='Notification')
				os.system("rm Notification.json")
		else:
			gpio.output(13,0)
			gpio.output(12,0)
			if flag_notif == True:
				flag_notif = False
				notif['ip'] = conf['pi']['ip']
				notif['enabled_alert'] = False
				notif['alert_way'] = conf['modulos'][str(last_slave)]['nombre']
				sftp.envio(notif,name='Notification')
				os.system("rm Notification.json")
		conn.close()
		time.sleep(1)

def backup_db(conn):
	global tablas
	cursor = conn.cursor()
	for t in tablas:
		with open(("./csv/"+t+".csv"),"wb") as f:
			for row in cursor.execute("SELECT * FROM "+t):
				writeRow = ",".join([str(i) for i in row])
				writeRow += "\n"
				f.write(writeRow.encode())
	for t in tablas:
		sftp.bck_db(t)
	for t in tablas:
		conn.execute("DELETE FROM "+t)
		conn.execute("""UPDATE sqlite_sequence SET seq = 0 WHERE name= ? """, t)
		conn.commit()

def activ_request(conn):
	global last_slave
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
			last_slave = 0
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
	global ip_controlador
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
				'sensado_receptores':False
			}
			if rq['type'] == "Request":
				for m in rq['modules']:
					flag[m] = True
				re = {
					'type':"Response",
					'ip':ip_controlador
				}
				for f in flag.items():
					if f[1] == True:
						re[f[0]] = p_sistema[f[0]]['data']
				sftp.envio(re,name="Response")
			else:
				print("[!] Request.json no válido: Error de formato")
			os.system('rm Response.json Request.json')
	except FileNotFoundError:
		print("[!] No existe solicitud de monitoreo")

def get_activ(conn):
	global inicio, final, t_mensaje, last_slave
	print("[+] Extrayendo parámetros tiempo de inicio - final  del ultimo registro de activación")
	cur = conn.cursor()
	cur.execute('''SELECT fecha_inicio,fecha_fin,tipo_mensaje,slave FROM activacion WHERE ID=(SELECT MAX(ID) FROM activacion)''')
	tiempos = cur.fetchall()
	for x in tiempos:
		inicio = x[0]
		final = x[1]
		t_mensaje = x[2]
		last_slave = x[3]

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
	cur.execute('''SELECT frequency,lock,bandwidth,area,flag_EWBS,flag_TMCC,power FROM tdt WHERE ID=(SELECT MAX(ID) FROM tdt)''')
	pTDT_monit = cur.fetchall()
	for x in pTDT_monit:
		p_sistema['tdt']['data']['frequency'] = x[0]
		p_sistema['tdt']['data']['lock'] = x[1]
		p_sistema['tdt']['data']['bandwidth'] = x[2]
		p_sistema['tdt']['data']['area'] = x[3]
		p_sistema['tdt']['data']['flag_EWBS'] = x[4]
		p_sistema['tdt']['data']['flag_TMCC'] = x[5]
		p_sistema['tdt']['data']['power'] = x[6]
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
	cur.execute('''SELECT temperatura,C_Sensor,V_Sensor,C_Entrada,V_Entrada,C_Ampli_Bocina,V_Rele,enable_ampli FROM amp_derecho WHERE ID=(SELECT MAX(ID) FROM amp_derecho)''')
	pAmp_derecho_monit = cur.fetchall()
	for x in pAmp_derecho_monit:
		p_sistema['amp_derecho']['data']['temperatura'] = x[0]
		p_sistema['amp_derecho']['data']['C_Sensor'] = x[1]
		p_sistema['amp_derecho']['data']['V_Sensor'] = x[2]
		p_sistema['amp_derecho']['data']['C_Entrada'] = x[3]
		p_sistema['amp_derecho']['data']['V_Entrada'] = x[4]
		p_sistema['amp_derecho']['data']['C_Ampli_Bocina'] = x[5]
		p_sistema['amp_derecho']['data']['V_Rele'] = x[6]
		p_sistema['amp_derecho']['data']['enable_ampli'] = x[7]
	verificar_patron(mod = 'amp_derecho')

def get_monit_amp_izquierdo(conn):
	global p_sistema
	print("[+] Extrayendo parámetros de monitoreo 'amp_izquierdo'")
	cur = conn.cursor()
	cur.execute('''SELECT temperatura,C_Sensor,V_Sensor,C_Entrada,V_Entrada,C_Ampli_Bocina,V_Rele,enable_ampli FROM amp_izquierdo WHERE ID=(SELECT MAX(ID) FROM amp_izquierdo)''')
	pAmp_izquierdo_monit = cur.fetchall()
	for x in pAmp_izquierdo_monit:
		p_sistema['amp_izquierdo']['data']['temperatura'] = x[0]
		p_sistema['amp_izquierdo']['data']['C_Sensor'] = x[1]
		p_sistema['amp_izquierdo']['data']['V_Sensor'] = x[2]
		p_sistema['amp_izquierdo']['data']['C_Entrada'] = x[3]
		p_sistema['amp_izquierdo']['data']['V_Entrada'] = x[4]
		p_sistema['amp_izquierdo']['data']['C_Ampli_Bocina'] = x[5]
		p_sistema['amp_izquierdo']['data']['V_Rele'] = x[6]
		p_sistema['amp_izquierdo']['data']['enable_ampli'] = x[7]
	verificar_patron(mod = 'amp_izquierdo')

def get_monit_sensado_receptores(conn):
	global p_sistema
	print("[+] Extrayendo parámetros de monitoreo 'sensado_receptores'")
	cur = conn.cursor()
	cur.execute('''SELECT temperatura,C_sensado,V_sensado,C_RDS,V_RDS,C_TDT,V_TDT,C_manual,V_manual,C_entrada,V_entrada FROM sensado_receptores WHERE ID=(SELECT MAX(ID) FROM sensado_receptores)''')
	pRDS_sensores_monit = cur.fetchall()
	for x in pRDS_sensores_monit:
		p_sistema['sensado_receptores']['data']['temperatura'] = x[0]
		p_sistema['sensado_receptores']['data']['C_sensado'] = x[1]
		p_sistema['sensado_receptores']['data']['V_sensado'] = x[2]
		p_sistema['sensado_receptores']['data']['C_RDS'] = x[3]
		p_sistema['sensado_receptores']['data']['V_RDS'] = x[4]
		p_sistema['sensado_receptores']['data']['C_TDT'] = x[5]
		p_sistema['sensado_receptores']['data']['V_TDT'] = x[6]
		p_sistema['sensado_receptores']['data']['C_manual'] = x[7]
		p_sistema['sensado_receptores']['data']['V_manual'] = x[8]
		p_sistema['sensado_receptores']['data']['C_entrada'] = x[9]
		p_sistema['sensado_receptores']['data']['V_entrada'] = x[10]
	verificar_patron(mod = 'sensado_receptores')

def verificar_patron(mod):
	global p_sistema, ip_controlador

	with open('config/config.json','r') as cmp:
		config = json.load(cmp)
		modulos = config["modulos"]
		err = {}
		for m in sorted(modulos.items()):
			err[m[1]["nombre"]] = m[1]["error"]

	print('[*] Verificando datos: monitoreo ',mod)

	if mod == 'rds':
		#p_rds['rds']['frequency']=99.9 # Error (para fines de prueba)
		if ((p_sistema['rds']['data']['frequency'] == err["rds"]["first_freq"]
			or p_sistema['rds']['data']['frequency'] == err["rds"]["second_freq"])
			and p_sistema['rds']['data']['lock'] == err["rds"]["lock_ok"]
			and p_sistema['rds']['data']['rds_state'] == err["rds"]["rds_state_ok"]):
			print("[+] Parámetros ",mod,": OK")
		else:
			print("[!] Parámetros ",mod,": Error")
			p_sistema['rds']['type'] = "Error"
			p_sistema['rds']['ip'] = ip_controlador
			print("[!] Enviando reporte JSON a servidor web...")
			sftp.envio(p_sistema['rds'],name="Error")
			os.system("rm Error.json")

	elif mod == 'manual':
		if int(p_sistema['manual']['data']['fecha']) > int(time.time()) - 18000 - err["manual"]["timestamp"]:
			print("[+] Parámetros ",mod,": OK")
		else:
			print("[!] Parámetros ",mod,": Error")
			p_sistema['manual']['type'] = "Error"
			p_sistema['manual']['ip'] = ip_controlador
			print(p_sistema['manual']['data']['fecha'])
			print("[!] Enviando reporte JSON a servidor web...")
			sftp.envio(p_sistema['manual'],name="Error")
			os.system("rm Error.json")

	elif mod == 'tdt':
		if (p_sistema['tdt']['data']['frequency'] == err["tdt"]["freq"]
			and p_sistema['tdt']['data']['lock'] == err["tdt"]["lock_ok"]
			and p_sistema['tdt']['data']['bandwidth'] == err["tdt"]["bandwidth"]
			and p_sistema['tdt']['data']['power'] == err["tdt"]["power"]):
			print("[+] Parámetros ",mod,": OK")
		else:
			print("[!] Parámetros ",mod,": Error")
			p_sistema['tdt']['type'] = "Error"
			p_sistema['tdt']['ip'] = ip_controlador
			print("[!] Enviando reporte JSON a servidor web...")
			sftp.envio(p_sistema['tdt'],name="Error")
			os.system("rm Error.json")

	elif mod == 'gabinete':
		if (p_sistema['gabinete']['data']['sensor_puerta'] == err["gabinete"]["close_door"]
			and p_sistema['gabinete']['data']['temperatura'] < err["gabinete"]["max_temp"]
			and p_sistema['gabinete']['data']['temperatura'] > err["gabinete"]["min_temp"]
			and p_sistema['gabinete']['data']['battery_current'] > err["gabinete"]["min_curr_battery"]
			and p_sistema['gabinete']['data']['battery_voltage'] < err["gabinete"]["max_volt_battery"]
			and p_sistema['gabinete']['data']['battery_voltage'] > err["gabinete"]["min_volt_battery"]):
			print("[+] Parámetros ",mod,": OK")
		else:
			print("[!] Parámetros ",mod,": Error")
			p_sistema['gabinete']['type'] = "Error"
			p_sistema['gabinete']['ip'] = ip_controlador
			print("[!] Enviando reporte JSON a servidor web...")
			sftp.envio(p_sistema['gabinete'],name="Error")
			os.system("rm Error.json")

	elif mod == 'amp_izquierdo':
		if (p_sistema['amp_izquierdo']['data']['temperatura'] < err["amp_izquierdo"]["max_temp"]
			and p_sistema['amp_izquierdo']['data']['temperatura'] > err["amp_izquierdo"]["min_temp"]
			and p_sistema['amp_izquierdo']['data']['C_Sensor'] < err["amp_izquierdo"]["max_curr_sensor"]
			and p_sistema['amp_izquierdo']['data']['C_Sensor'] > err["amp_izquierdo"]["min_curr_sensor"]
			and p_sistema['amp_izquierdo']['data']['V_Sensor'] < err["amp_izquierdo"]["max_volt_sensor"]
			and p_sistema['amp_izquierdo']['data']['V_Sensor'] > err["amp_izquierdo"]["min_volt_sensor"]
			and p_sistema['amp_izquierdo']['data']['C_Entrada'] < err["amp_izquierdo"]["max_curr_entrada"]
			and p_sistema['amp_izquierdo']['data']['C_Entrada'] > err["amp_izquierdo"]["min_curr_entrada"]
			and p_sistema['amp_izquierdo']['data']['V_Entrada'] < err["amp_izquierdo"]["max_volt_entrada"]
			and p_sistema['amp_izquierdo']['data']['V_Entrada'] > err["amp_izquierdo"]["min_volt_entrada"]
			and p_sistema['amp_izquierdo']['data']['C_Ampli_Bocina'] < err["amp_izquierdo"]["max_curr_ampli_bocina"]
			and p_sistema['amp_izquierdo']['data']['C_Ampli_Bocina'] > err["amp_izquierdo"]["min_curr_ampli_bocina"]
			and p_sistema['amp_izquierdo']['data']['V_Rele'] < err["amp_izquierdo"]["max_volt_rele"]
			and p_sistema['amp_izquierdo']['data']['V_Rele'] > err["amp_izquierdo"]["min_volt_rele"]):
			print("[+] Parámetros ",mod,": OK")
		else:
			print("[!] Parámetros ",mod,": Error")
			p_sistema['amp_izquierdo']['type'] = "Error"
			p_sistema['amp_izquierdo']['ip'] = ip_controlador
			print("[!] Enviando reporte JSON a servidor web...")
			sftp.envio(p_sistema['amp_izquierdo'],name="Error")
			os.system("rm Error.json")

	elif mod == 'amp_derecho':
		if (p_sistema['amp_derecho']['data']['temperatura'] < err["amp_derecho"]["max_temp"]
			and p_sistema['amp_derecho']['data']['temperatura'] > err["amp_derecho"]["min_temp"]
			and p_sistema['amp_derecho']['data']['C_Sensor'] < err["amp_derecho"]["max_curr_sensor"]
			and p_sistema['amp_derecho']['data']['C_Sensor'] > err["amp_derecho"]["min_curr_sensor"]
			and p_sistema['amp_derecho']['data']['V_Sensor'] < err["amp_derecho"]["max_volt_sensor"]
			and p_sistema['amp_derecho']['data']['V_Sensor'] > err["amp_derecho"]["min_volt_sensor"]
			and p_sistema['amp_derecho']['data']['C_Entrada'] < err["amp_derecho"]["max_curr_entrada"]
			and p_sistema['amp_derecho']['data']['C_Entrada'] > err["amp_derecho"]["min_curr_entrada"]
			and p_sistema['amp_derecho']['data']['V_Entrada'] < err["amp_derecho"]["max_volt_entrada"]
			and p_sistema['amp_derecho']['data']['V_Entrada'] > err["amp_derecho"]["min_volt_entrada"]
			and p_sistema['amp_derecho']['data']['C_Ampli_Bocina'] < err["amp_derecho"]["max_curr_ampli_bocina"]
			and p_sistema['amp_derecho']['data']['C_Ampli_Bocina'] > err["amp_derecho"]["min_curr_ampli_bocina"]
			and p_sistema['amp_derecho']['data']['V_Rele'] < err["amp_derecho"]["max_volt_rele"]
			and p_sistema['amp_derecho']['data']['V_Rele'] > err["amp_derecho"]["min_volt_rele"]):
			print("[+] Parámetros ",mod,": OK")
		else:
			print("[!] Parámetros ",mod,": Error")
			p_sistema['amp_derecho']['type'] = "Error"
			p_sistema['amp_derecho']['ip'] = ip_controlador
			print("[!] Enviando reporte JSON a servidor web...")
			sftp.envio(p_sistema['amp_derecho'],name="Error")
			os.system("rm Error.json")

	elif mod == 'sensado_receptores':
		if (p_sistema['sensado_receptores']['data']['temperatura'] < err["sensado_receptores"]["max_temp"]
			and p_sistema['sensado_receptores']['data']['temperatura'] > err["sensado_receptores"]["min_temp"]
			and p_sistema['sensado_receptores']['data']['C_sensado'] < err["sensado_receptores"]["max_curr_sensado"]
			and p_sistema['sensado_receptores']['data']['C_sensado'] > err["sensado_receptores"]["min_curr_sensado"]
			and p_sistema['sensado_receptores']['data']['V_sensado'] < err["sensado_receptores"]["max_volt_sensado"]
			and p_sistema['sensado_receptores']['data']['V_sensado'] > err["sensado_receptores"]["min_volt_sensado"]
			and p_sistema['sensado_receptores']['data']['C_RDS'] < err["sensado_receptores"]["max_curr_rds"]
			and p_sistema['sensado_receptores']['data']['C_RDS'] > err["sensado_receptores"]["min_curr_rds"]
			and p_sistema['sensado_receptores']['data']['V_RDS'] < err["sensado_receptores"]["max_volt_rds"]
			and p_sistema['sensado_receptores']['data']['V_RDS'] > err["sensado_receptores"]["min_volt_rds"]
			and p_sistema['sensado_receptores']['data']['C_TDT'] < err["sensado_receptores"]["max_curr_tdt"]
			and p_sistema['sensado_receptores']['data']['C_TDT'] > err["sensado_receptores"]["min_curr_tdt"]
			and p_sistema['sensado_receptores']['data']['V_TDT'] < err["sensado_receptores"]["max_volt_tdt"]
			and p_sistema['sensado_receptores']['data']['V_TDT'] > err["sensado_receptores"]["min_volt_tdt"]
			and p_sistema['sensado_receptores']['data']['C_manual'] < err["sensado_receptores"]["max_curr_manual"]
			and p_sistema['sensado_receptores']['data']['C_manual'] > err["sensado_receptores"]["min_curr_manual"]
			and p_sistema['sensado_receptores']['data']['V_manual'] < err["sensado_receptores"]["max_volt_manual"]
			and p_sistema['sensado_receptores']['data']['V_manual'] > err["sensado_receptores"]["min_volt_manual"]
			and p_sistema['sensado_receptores']['data']['C_entrada'] < err["sensado_receptores"]["max_curr_entrada"]
			and p_sistema['sensado_receptores']['data']['C_entrada'] > err["sensado_receptores"]["min_curr_entrada"]
			and p_sistema['sensado_receptores']['data']['V_entrada'] < err["sensado_receptores"]["max_volt_entrada"]
			and p_sistema['sensado_receptores']['data']['V_entrada'] > err["sensado_receptores"]["min_volt_entrada"]):
			print("[+] Parámetros ",mod,": OK")
		else:
			print("[!] Parámetros ",mod,": Error")
			p_sistema['sensado_receptores']['type'] = "Error"
			p_sistema['sensado_receptores']['ip'] = ip_controlador
			print("[!] Enviando reporte JSON a servidor web...")
			sftp.envio(p_sistema['sensado_receptores'],name="Error")
			os.system("rm Error.json")

	elif mod == 'controlador_digital':
		if (p_sistema['controlador_digital']['data']['Temperatura'] < err["controlador_digital"]["max_temp"]
			and p_sistema['controlador_digital']['data']['Temperatura'] > err["controlador_digital"]["min_temp"]
			and p_sistema['controlador_digital']['data']['C_Fuente'] < err["controlador_digital"]["max_curr_fuente"]
			and p_sistema['controlador_digital']['data']['C_Fuente'] > err["controlador_digital"]["min_curr_fuente"]
			and p_sistema['controlador_digital']['data']['V_Fuente'] < err["controlador_digital"]["max_volt_fuente"]
			and p_sistema['controlador_digital']['data']['V_Fuente'] > err["controlador_digital"]["min_volt_fuente"]
			and p_sistema['controlador_digital']['data']['C_PoE'] < err["controlador_digital"]["max_curr_poe"]
			and p_sistema['controlador_digital']['data']['C_PoE'] > err["controlador_digital"]["min_curr_poe"]
			and p_sistema['controlador_digital']['data']['V_PoE'] < err["controlador_digital"]["max_volt_poe"]
			and p_sistema['controlador_digital']['data']['V_PoE'] > err["controlador_digital"]["min_volt_poe"]
			and p_sistema['controlador_digital']['data']['C_PreAmpli'] < err["controlador_digital"]["max_curr_preampli"]
			and p_sistema['controlador_digital']['data']['C_PreAmpli'] > err["controlador_digital"]["min_curr_preampli"]
			and p_sistema['controlador_digital']['data']['V_PreAmpli'] < err["controlador_digital"]["max_volt_preampli"]
			and p_sistema['controlador_digital']['data']['V_PreAmpli'] > err["controlador_digital"]["min_volt_preampli"]
			and p_sistema['controlador_digital']['data']['C_MUX'] < err["controlador_digital"]["max_curr_mux"]
			and p_sistema['controlador_digital']['data']['C_MUX'] > err["controlador_digital"]["min_curr_mux"]
			and p_sistema['controlador_digital']['data']['V_MUX'] < err["controlador_digital"]["max_volt_mux"]
			and p_sistema['controlador_digital']['data']['V_MUX'] > err["controlador_digital"]["min_volt_mux"]
			and p_sistema['controlador_digital']['data']['C_Raspberry'] < err["controlador_digital"]["max_curr_raspi"]
			and p_sistema['controlador_digital']['data']['C_Raspberry'] > err["controlador_digital"]["min_curr_raspi"]
			and p_sistema['controlador_digital']['data']['V_Raspberry'] < err["controlador_digital"]["max_volt_raspi"]
			and p_sistema['controlador_digital']['data']['V_Raspberry'] > err["controlador_digital"]["min_volt_raspi"]
			and p_sistema['controlador_digital']['data']['C_Rele'] < err["controlador_digital"]["max_curr_rele"]
			and p_sistema['controlador_digital']['data']['C_Rele'] > err["controlador_digital"]["min_curr_rele"]
			and p_sistema['controlador_digital']['data']['V_Rele'] < err["controlador_digital"]["max_volt_rele"]
			and p_sistema['controlador_digital']['data']['V_Rele'] > err["controlador_digital"]["min_volt_rele"]
			and p_sistema['controlador_digital']['data']['C_Switch'] < err["controlador_digital"]["max_curr_switch"]
			and p_sistema['controlador_digital']['data']['C_Switch'] > err["controlador_digital"]["min_curr_switch"]
			and p_sistema['controlador_digital']['data']['V_Switch'] < err["controlador_digital"]["max_volt_switch"]
			and p_sistema['controlador_digital']['data']['V_Switch'] > err["controlador_digital"]["min_volt_switch"]
			and p_sistema['controlador_digital']['data']['C_Ampli'] < err["controlador_digital"]["max_curr_ampli"]
			and p_sistema['controlador_digital']['data']['C_Ampli'] > err["controlador_digital"]["min_curr_ampli"]
			and p_sistema['controlador_digital']['data']['V_Ampli'] < err["controlador_digital"]["max_volt_ampli"]
			and p_sistema['controlador_digital']['data']['V_Ampli'] > err["controlador_digital"]["min_volt_ampli"]):
			print("[+] Parámetros ",mod,": OK")
		else:
			print("[!] Parámetros ",mod,": Error")
			p_sistema['controlador_digital']['type'] = "Error"
			p_sistema['controlador_digital']['ip'] = ip_controlador
			print("[!] Enviando reporte JSON a servidor web...")
			sftp.envio(p_sistema['controlador_digital'],name="Error")
			os.system("rm Error.json")

if __name__ == '__main__':
	print("[+] Script controlador de activacion")
	main()
