from dmxxx import *
import random, os


os.system('clear')

dmx = DMXXX('/dev/cu.usbserial-ENVVVCOF')

wabern = Scene('Wabern')
wabern.channel(1).generator = Sine(random.randint(7000,9000))
wabern.channel(2).generator = Sine(random.randint(7000,9000))
wabern.channel(3).generator = Sine(random.randint(7000,9000))
wabern.channel(4).generator = Sine(random.randint(7000,9000))

dagegen = Scene('Gegenlaeufig')
dagegen.channel(1).generator = Sine(2000)
dagegen.channel(2).generator = InvertedSine(2000)
dagegen.channel(3).generator = Sine(2000)
dagegen.channel(4).generator = InvertedSine(2000)


dmx.scene = wabern
dmx.start()

#time.sleep(10)

#dmx.scene = dagegen

#time.sleep(10)

#print 
d = raw_input('Press Enter to end DMX loops.')

dmx.stop()