import pysftp
from pysftp.exceptions import ConnectionException
from paramiko import SSHException
import json

def envio(parametros,name='datos'):
	with open('/home/pi/Resiliente_CD/config/config.json','r') as cfg:
		serv = json.load(cfg)
		ip = serv['servidor']['ip']
		user = serv['servidor']['user']
		password = serv['servidor']['password']
		path = serv['servidor']['path']

	sorted(parametros.items())
	with open((name+'.json'),'w') as file:
		json.dump(parametros,file,indent=4)
	try:
		with pysftp.Connection(host=ip, username=user, password=password) as sftp:
			print("[+] Connection succesfully stablished ... ")

			# cambio de directorio
			#sftp.cwd('/admin/archivos/')

			localFilePath = '/home/pi/Resiliente_CD/'+name+'.json'
			#remoteFilePath = '/admin/archivos/'+name+'.json'
			remoteFilePath = path + name + '.json'
			sftp.put(localFilePath, remoteFilePath)
			print("[+] Fichero "+name+".json enviado correctamente")
			#sftp.cwd('/admin/archivos/')
			#directory_structure = sftp.listdir_attr()
			#enlistar archivos
			#for attr in directory_structure:
			#	print(attr.filename, attr)
	except (ConnectionException, SSHException) as e:
		print("[!] Error: Server no conectado")

def bck_db(name):
	#ip = "10.0.114.14"
	#user = "usuario"
	#password = "inicteluni"
	with open('/home/pi/Resiliente_CD/config/config.json','r') as cfg:
		serv = json.load(cfg)
		ip = serv['servidor']['ip']
		user = serv['servidor']['user']
		password = serv['servidor']['password']
		path = serv['servidor']['path']
	try:
		with pysftp.Connection(host=ip, username=user, password=password) as sftp:
			localFilePath = '/home/pi/Resiliente_CD/csv/'+name+'.csv'
			remoteFilePath = path + name + '.csv'
			#remoteFilePath = '/home/usuario/Escritorio/'+name+'.csv'
			sftp.put(localFilePath, remoteFilePath)
	except (ConnectionException, SSHException) as e:
		print("[!] Error: "+e)
