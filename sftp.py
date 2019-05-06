import pysftp
import json

def envio(parametros,name='datos'):
	server = "10.0.114.10"
	user = "admin"
	password = "admin123"

	sorted(parametros.items())
	print(parametros)
	with open((name+'.json'),'w') as file:
		json.dump(parametros,file,indent=4)
	#print(datos)
	with pysftp.Connection(host=server, username=user, password=password) as sftp:
		print("Connection succesfully stablished ... ")

		# cambio de directorio
		#sftp.cwd('/admin/archivos/')

		localFilePath = '/home/pi/Resiliente_CD/'+name+'.json'

		remoteFilePath = '/admin/archivos/'+name+'.json'
		sftp.put(localFilePath, remoteFilePath)

		sftp.cwd('/admin/archivos/')
		directory_structure = sftp.listdir_attr()

		#enlistar archivos
		for attr in directory_structure:
			print(attr.filename, attr)
