import pysftp
import json

def envio(parametros,name='datos'):
	with open('/home/pi/Resiliente_CD/config/config.json','r') as cfg:
		serv = json.load(cfg)
		ip = serv['servidor']['ip']
		user = serv['servidor']['user']
		password = serv['servidor']['password']

	sorted(parametros.items())
	#print(parametros)
	with open((name+'.json'),'w') as file:
		json.dump(parametros,file,indent=4)
	#print(datos)
	with pysftp.Connection(host=ip, username=user, password=password) as sftp:
		print("[+] Connection succesfully stablished ... ")

		# cambio de directorio
		#sftp.cwd('/admin/archivos/')

		localFilePath = '/home/pi/Resiliente_CD/'+name+'.json'

		remoteFilePath = '/admin/archivos/'+name+'.json'
		sftp.put(localFilePath, remoteFilePath)
		print("[+] Fichero "+name+".json enviado correctamente")
		#sftp.cwd('/admin/archivos/')
		#directory_structure = sftp.listdir_attr()

		#enlistar archivos
		#for attr in directory_structure:
		#	print(attr.filename, attr)
