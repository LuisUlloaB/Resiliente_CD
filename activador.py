"""Descripción del Script:
	Script desarrollado para procesar y validar los registros de activación.
"""
import json
import sqlite3
from time import strptime, mktime, sleep

last_f_creacion = 0
last_f_inicio = 0
last_f_final = 0

def datetime_converter(datetime_string):
	"""Descripción de la función:
		Función encargada de obtener el valor de la fecha y hora en formato Unix
		Epoch time (Cantidad de segundos transcurridos desde 01 enero de 1970).

		Parámetros:
			datetime_string (string): Fecha y hora en texto plano con el formato
						  Año-mes-día Hora:minuto:segundo

		Return:
			epoch (int): Fecha y hora en formato Epoch.
	"""
	# Da formato a la variable datetime
	target_timestamp = strptime(datetime_string, '%Y-%m-%d %H:%M:%S')

	# mktime crea el formato epoch
	mktime_epoch = mktime(target_timestamp)
	epoch = int(mktime_epoch) - 18000
	return epoch

def activar(reg,id_slave,primer_intento = False):
	"""Descripción de la función:
		Función principal encargada de activación del sistema, es decir:
		guardado en base de datos, extracción de data, generación de audio
		y encendido de relés de amplificación.

		Parámetros:
			reg (lista<int>): Registros de activación, mayor información
					  en 'Distribución de registros.xls'.

		Return:
			Estado_act (True|False): Indicador de éxito o falla en proceso
						 de activación.
	"""
	CAP = {	'identificador':['Indeci','GobiernoLocal','Prueba','Otro'],
		'estado':['actual','simulacro','prueba','alarma'],
		'tipo_mensaje':['alerta','actualiza','cancela','confirmado','error'],
		'ambito':['Publico','Privado'],
		'idioma':['Espanol','Quechua','Ingles','Otro'],
		'categoria':['GeodinamicaInterna','GeodinamicaExterna','Hidrometeorologico','Biologico','Humano','Seguridad','Otro'],
		'evento':['actividadVolcanica','sismo','tsunami','alud','aluvion','derrumbeCerro','deslizamiento','crecidaRio','granizada','helada','huayco','inundacion','lluviaIntensa','marejada','nevada','sequia','tormenta','vientoFuerte','colapsoConstruccion','contaminacionAgua','contaminacionSuelo','explosion','derrameSustNocivas','incendioForestal','incendioUrbano','epidemia','plaga','otro'],
		'tipo_respuesta':['abrigarse','evacuar','preparar','ejecutar','monitorear','evaluar','otro','ninguno'],
		'urgencia':['inmediato','esperado','futura','pasada','desconocida'],
		'severidad':['extremo','severo','moderado','menor','desconocido'],
		'certeza':['Confirmado','Probable','Improbable','Desconocido'],
		'color':['Rojo','Ambar','Verde']}

	#extraer data
	var_audio = {
			'estado':CAP["estado"][reg[6]],
			'evento':CAP["evento"][reg[11]],
			'severidad':CAP["severidad"][reg[14]],
			'respuesta':CAP["tipo_respuesta"][reg[12]],
			'urgencia':CAP["urgencia"][reg[13]],
			'mensaje':CAP["tipo_mensaje"][reg[7]]}
	print("\t\t\t└---",var_audio)

	area = str(reg[32]) + str(reg[33])
	texto = ""
	for i in reg[34:74]:
		texto += str(chr(i))
	print("\t\t\t└---Texto: ",texto)

	fecha_hora = mjd_inversor(reg[1:3])
	fecha_hora += " " + str(reg[3]) + ":" + str(reg[4]) + ":" + str(reg[5])
	epoch_fecha_hora = datetime_converter(fecha_hora)
	print("\t\t\t└---Fecha_Hora: ",fecha_hora)

	efectivo = mjd_inversor(reg[17:19])
	efectivo += " " + str(reg[19]) + ":" + str(reg[20]) + ":" + str(reg[21])
	epoch_efectivo = datetime_converter(efectivo)
	print("\t\t\t└---efectivo: ",efectivo)

	inicio = mjd_inversor(reg[22:24])
	inicio += " " + str(reg[24]) + ":" + str(reg[25]) + ":" + str(reg[26])
	epoch_inicio = datetime_converter(inicio)
	print("\t\t\t└---inicio: ",inicio)

	final = mjd_inversor(reg[27:29])
	final += " " + str(reg[29]) + ":" + str(reg[30]) + ":" + str(reg[31])
	epoch_final = datetime_converter(final)
	print("\t\t\t└---final: ",final)

	interval = epoch_final - epoch_inicio
	print("\t\t\t└---Duracion: ",str(interval)," segs")

	global last_f_creacion
	global last_f_inicio
	global last_f_final
	if primer_intento == True:
		last_f_creacion = epoch_fecha_hora
		last_f_inicio = epoch_inicio
		last_f_final = epoch_final
		print("\t\t\t└---[+] Primer intento: OK")
	else:
		if last_f_creacion == epoch_fecha_hora or last_f_inicio == epoch_inicio or last_f_final == epoch_final:
			print("\t\t\t└---[!] Activacion no valido: Error")
			print("\t\t└--[!][!][!][!][!]*****************************END*****************************[!][!][!][!][!]")
			return -1
		else:
			last_f_creacion = epoch_fecha_hora
			last_f_inicio = epoch_inicio
			last_f_final = epoch_final
			print("\t\t\t└---[+] Activacion Valida: OK")

	#ingresar a base de datos
	try:
		print("\t\t\t└---[+] Conectando a la base de datos: resiliente.db")
		conn = sqlite3.connect('resiliente.db')
		print("\t\t\t└---[+] Insertando data en tabla: activacion")
		conn.execute('''INSERT INTO activacion (slave,identificador,fecha_hora,estado,tipo_mensaje,ambito,idioma,categoria,evento,tipo_respuesta,urgencia,severidad,certeza,color_alerta,fecha_efectivo,fecha_inicio,fecha_fin,area,texto) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(id_slave,CAP["identificador"][reg[0]],str(epoch_fecha_hora),CAP["estado"][reg[6]],CAP["tipo_mensaje"][reg[7]],CAP["ambito"][reg[8]],CAP["idioma"][reg[9]],CAP["categoria"][reg[10]],CAP["evento"][reg[11]],CAP["tipo_respuesta"][reg[12]],CAP["urgencia"][reg[13]],CAP["severidad"][reg[14]],CAP["certeza"][reg[15]],CAP["color"][reg[16]],str(epoch_efectivo),str(epoch_inicio),str(epoch_final),area,texto))
		conn.commit()
	except sqlite3.Error as e:
		print("\t\t\t└---[!] Sqlite3 error, ID: ",e.args[0])
	conn.close()

	#parámetros para audio
	with open('audio_param.json','w') as file:
		json.dump(var_audio,file,indent=4)

	print("\t\t└--[!][!][!][!][!]*****************************END*****************************[!][!][!][!][!]")


	#enviar señal de encendido a sub módulo de potencia
	#gpio.output(23,1)
	#while interval>0:
	#	print("[!] Tiempo Restante: " + str(interval))
	#	interval -= 1
	#	sleep(1)
	#generar y enviar audio

	#condicionales para generar audio

	#enviar señal de apagado a sub módulo de potencia
	#gpio.output(23,0)
	#print("falta")
	return 1

def mjd_inversor(fecha):
	"""Descripción de la función:
		Función encargada de invertir el algoritmo MJD utilizado para
		comprimir la fecha (Año-Mes-Día) en el vector CAP-PER.

		Parámetros:
			fecha (lista<int>): MJD dividido en dos valores.

		Return:
			Año-Mes-Día: Formato de fecha en texto plano.
	"""
	mjd = 0
	mjd = mjd | fecha[0]
	mjd = mjd << 8
	mjd = mjd | fecha[1]
	j = mjd + 2400001 + 68569
	c = 4 * j // 146097
	j = j - (146097 * c + 3) // 4
	y = 4000 * (j + 1) // 1461001
	j = j - 1461 * y // 4 + 31
	m = 80 * j // 2447
	day = j - 2447 * m // 80
	j = m // 11
	month = int(m + 2 - (12 * j))
	year = int(100 * (c - 49) + y + j)
	return (str(year) + "-" + str(month) + "-" + str(day))

if __name__ == '__main__':
	print("Función: Procesar y ejecutar la activación")
