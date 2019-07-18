import pysftp
from pysftp.exceptions import ConnectionException
import paramiko
from base64 import decodebytes
import json

def envio(parametros,name='datos'):
	with open('/home/pi/Resiliente_CD/config/config.json','r') as cfg:
		serv = json.load(cfg)
		ip = serv['servidor']['ip']
		user = serv['servidor']['user']
		password = serv['servidor']['password']
		path = serv['servidor']['path']

	sorted(parametros.items())
	with open(("/home/pi/Resiliente_CD/"+name+".json"),'w') as file:
		json.dump(parametros,file,indent=4)
	try:
		keydata = b"""AAAAB3NzaC1yc2EAAAADAQABAAABAQCeRcka3HJSP2a1ZJg6yBlbOswek5XZvbVCkano4+OnrqeZXdwEf88ye1tf32s+/PnAh8fe3KOPu0Gq0+hTOxSvOWkbjiyzKGM+6d1CSVAXEMXsyKpiZ2SKWHgfNUekDlr6Xm3ppc1KYdf9NYsmwAukK9TJqVA11OOcsfKsxkmKCNI1mAnhfm/5DGfW2a8KH8dLBs8DzY8vlqFEsoRovGYVCK4EU/nm+6eyj8nFqyuacUMiAGnqe6//lGMPTcQBcol5pRio3yWbjkscToAWM/IFi6XHNgKp6JQnTHFmdIaDRyEMOxPbOo3zE1frJMD+3SUgHTwEB1BBEra2n/i6f5Pd"""
		key = paramiko.RSAKey(data=decodebytes(keydata))
		cnopts = pysftp.CnOpts()
		cnopts.hostkeys.add(ip, 'ssh-rsa', key)
		with pysftp.Connection(host=ip, username=user, password=password, cnopts=cnopts) as sftp:
			print("[+] Connection succesfully stablished ... ")
			localFilePath = '/home/pi/Resiliente_CD/'+name+'.json'
			remoteFilePath = path + name + '.json'
			sftp.put(localFilePath, remoteFilePath)
			print("[+] Fichero "+name+".json enviado correctamente")
	except (ConnectionException, paramiko.SSHException) as e:
		print("[!] Error: Server no conectado")
		print(e)

def bck_db(name):
	with open('/home/pi/Resiliente_CD/config/config.json','r') as cfg:
		serv = json.load(cfg)
		ip = serv['servidor']['ip']
		user = serv['servidor']['user']
		password = serv['servidor']['password']
		path = serv['servidor']['path']
	try:
		keydata = b"""AAAAB3NzaC1yc2EAAAADAQABAAABAQCeRcka3HJSP2a1ZJg6yBlbOswek5XZvbVCkano4+OnrqeZXdwEf88ye1tf32s+/PnAh8fe3KOPu0Gq0+hTOxSvOWkbjiyzKGM+6d1CSVAXEMXsyKpiZ2SKWHgfNUekDlr6Xm3ppc1KYdf9NYsmwAukK9TJqVA11OOcsfKsxkmKCNI1mAnhfm/5DGfW2a8KH8dLBs8DzY8vlqFEsoRovGYVCK4EU/nm+6eyj8nFqyuacUMiAGnqe6//lGMPTcQBcol5pRio3yWbjkscToAWM/IFi6XHNgKp6JQnTHFmdIaDRyEMOxPbOo3zE1frJMD+3SUgHTwEB1BBEra2n/i6f5Pd"""
		key = paramiko.RSAKey(data=decodebytes(keydata))
		cnopts = pysftp.CnOpts()
		cnopts.hostkeys.add(ip, 'ssh-rsa', key)
		with pysftp.Connection(host=ip, username=user, password=password, cnopts=cnopts) as sftp:
			localFilePath = '/home/pi/Resiliente_CD/csv/'+name+'.csv'
			remoteFilePath = path + name + '.csv'
			sftp.put(localFilePath, remoteFilePath)
	except (ConnectionException, paramiko.SSHException) as e:
		print("[!] Error: "+e)
