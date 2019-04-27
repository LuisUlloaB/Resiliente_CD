import vlc
import os
from time import sleep

path = '/home/pi/resiliente/audios_mp3/simulacro.mp3'

def main():
	#path = os.path.dirname(os.path.realpath(__file__))
	#file = '0001.mp3'
	for x in 
	#p = vlc.MediaPlayer(path + '/audios_mp3/' + file)
	p = vlc.MediaPlayer(path)

	#print(p.get_state())
	#print(type(p.get_state()))
	p.play()
	#print(p.get_state())
	#while p.get_state():
	#	pass
	sleep(5)
	#print(p.get_state())
	#while p.is_playing():
	#	pass
	p.stop()
	return 1

if __name__ == "__main__":
	main()
