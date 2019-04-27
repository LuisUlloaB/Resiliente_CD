'''Generar y enviar audio
'''

import vlc
import time
estado = False
audio_parametros = 0

def main():
	#global audio_parametros
	#with open('audio_param.json') as file:
	#	audio_parametros = json.load(file)
	#print(audio_parametros)
	x = ['audios_mp3/simulacro.mp3','audios_mp3/tsunami.mp3','audios_mp3/evacuar.mp3']
	instance = vlc.Instance()
	player = instance.media_player_new()
	player.audio_set_volume(100)
	for a in x:
        	print(a)
	        media = instance.media_new(a)
        	player.set_media(media)
	        player.play()
	        while player.get_state() != vlc.State.Ended:
        	        time.sleep(1)

if __name__ == '__main__':
	main()
