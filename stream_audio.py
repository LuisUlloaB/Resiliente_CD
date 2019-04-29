'''Generar y enviar audio
'''
import sqlite3
import json
import vlc
import time
p_audio = 0
inicio = 0
fin = 0

def main():
	global inicio,fin
	while True:
		try:
			conn = sqlite3.connect('resiliente.db')
			cur = conn.cursor()
			cur.execute('''SELECT fecha_inicio,fecha_fin FROM activacion WHERE ID=(SELECT MAX(ID) FROM activacion)''')
			tiempos = cur.fetchall()
			for t in tiempos:
				inicio = t[0]
				fin = t[1]
			print("Inicio:	"+str(inicio))
			print("Final:	"+str(fin))
		except sqlite3.Error as e:
			print("[!] Sqlite3 error, ID: ",e.args[0])
		conn.close()
		now = int(time.time()) - 18000
		print("Now:	"+str(now))
		if (int(time.time()) - 18000) >= int(inicio) and (int(time.time()) - 18000) <= int(fin):
			audio_gen(True)
		else:
			audio_gen(False)
		time.sleep(1)

def audio_gen(estado):
	global p_audio
	with open('audio_param.json') as file:
		p_audio = json.load(file)
	print(p_audio)
	#x = ['audios/'+p_audio['estado']+'.wav','audios/'+p_audio['evento']+'.wav','audios/'+p_audio['severidad']+'.wav','audios/'+p_audio['respuesta']+'.wav','audios/'+p_audio['urgencia']+'.wav']
	y = "audios/alerta_crecidaRio_evacuar_inmediata.wav"
	instance = vlc.Instance()
	player = instance.media_player_new()
	player.audio_set_volume(100)
	if estado == True:
		media = instance.media_new(y)
		player.set_media(media)
		player.play()
		while player.get_state() != vlc.State.Ended:
			time.sleep(1)
		#for a in x:
		#	print(a)
		#	media = instance.media_new(a)
		#	player.set_media(media)
		#	player.play()
		#	while player.get_state() != vlc.State.Ended:
		#		time.sleep(1)
	else:
		player.stop()

if __name__ == '__main__':
	print("Generador y Output de audio")
	main()
