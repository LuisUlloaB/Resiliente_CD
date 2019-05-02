import os
import json

os.system("(dmesg | grep '.*usb 1-1.4.*ttyUSB.$') > ports.txt")
file = open('ports.txt','r')
file.read(63)
port_activ_monit = file.read(7)
file.close()

os.system("(dmesg | grep '.*usb 1-1.2.*ttyUSB.$') > ports.txt")
file = open('ports.txt','r')
file.read(63)
port_test = file.read(7)
file.close()

os.system("rm ports.txt")

ports = {
	'puertos':{
		'monit_activ':{
			'fisico':"usb 1-1.4",
			'logico':port_activ_monit,
			'referencia':"TOP - RIGHT"
		},
		'test':{
			'fisico':"usb 1-1.2",
			'logico':port_test,
			'referencia':"TOP - LEFT"
		}
	}
}

with open("config.json") as cfg:
	config = json.load(cfg)
config['puertos'] = ports['puertos']

with open("config.json","w") as f:
	json.dump(config, f, indent=4, sort_keys=True)
