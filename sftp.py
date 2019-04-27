import pysftp
import json

def envio(parametros):
	server = "10.0.114.10"
	user = "admin"
	password = "admin123"

	datos = parametros
	with open('datos.json','w') as file:
		json.dump(datos,file,indent=4)
	#print(datos)
	with pysftp.Connection(host=server, username=user, password=password) as sftp:
		print("Connection succesfully stablished ... ")

		# cambio de directorio
		#sftp.cwd('/admin/archivos/')

		localFilePath = '/home/pi/resiliente/datos.json'

		remoteFilePath = '/admin/archivos/datos.json'
		sftp.put(localFilePath, remoteFilePath)

		sftp.cwd('/admin/archivos/')
		directory_structure = sftp.listdir_attr()

		#enlistar archivos
		for attr in directory_structure:
			print(attr.filename, attr)
