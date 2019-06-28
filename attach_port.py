import os
import json

def main():
	desc = "disconnect"
	conn = "attached"
	p = ["none","none"]
	t = [0,0]
	mesg = ["(dmesg | grep '.*usb 1-1.4.*') > ports.txt","(dmesg | grep '.*usb 1-1.2.*') > ports.txt"]

	for i in range(2):
		os.system(mesg[i])
		file = open('ports.txt','r')

		for l in file:
			c = l.find(conn)
			d = l.find(desc)
			if c != -1 or d != -1:
				if float(l[1:13]) > t[i]:
					t[i] = float(l[1:13])
					if c != -1:
						p[i] = l[-8:-1]
					if d != -1:
						p[i] = "none"
		file.close()

	os.system("rm ports.txt")

	ports = {
		'puertos':{
			'monit_activ':{
				'fisico':"usb 1-1.4",
				'logico':p[0],
				'referencia':"UP - LEFT"
			},
			'test':{
				'fisico':"usb 1-1.2",
				'logico':p[1],
				'referencia':"UP - RIGHT"
			}
		}
	}

	with open("/home/pi/Resiliente_CD/config/config.json") as cfg:
		config = json.load(cfg)

	config['puertos'] = ports['puertos']

	with open("/home/pi/Resiliente_CD/config/config.json","w") as f:
		json.dump(config, f, indent=4, sort_keys=True)


if __name__ == '__main__':
	main()
