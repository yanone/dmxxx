from vanilla.test.testTools import executeVanillaTest
from dmxxx import *
import random


randint = [7000, 9000]


class myDMXXX(DMXXX):
	
	def userInit(self):
		self.dmx.channels[0].min = 70
		self.dmx.channels[1].min = 90
		self.dmx.channels[2].min = 70
		self.dmx.channels[3].min = 90
		self.dmx.generators.append(Sine(1, random.randint(randint[0], randint[1])))
		self.dmx.generators.append(Sine(2, random.randint(randint[0], randint[1])))
		self.dmx.generators.append(Sine(3, random.randint(randint[0], randint[1])))
		self.dmx.generators.append(Sine(4, random.randint(randint[0], randint[1])))

		#5
		self.dmx.channels[4].min = 30
		self.dmx.channels[4].max = 50
		self.dmx.generators.append(Sine(5, random.randint(randint[0], randint[1])))

		#6 PAR recht
		self.dmx.channels[5].min = 20
		self.dmx.channels[5].max = 35
		self.dmx.generators.append(Sine(6, random.randint(randint[0], randint[1])))

		#7
		self.dmx.channels[6].min = 30
		self.dmx.channels[6].max = 60
		self.dmx.generators.append(Sine(7, random.randint(randint[0], randint[1])))

		#8
		self.dmx.channels[7].min = 30
		self.dmx.channels[7].max = 50
		self.dmx.generators.append(Sine(8, random.randint(randint[0], randint[1])))

		#9 PAR links
		self.dmx.channels[8].min = 20
		self.dmx.channels[8].max = 45
		self.dmx.generators.append(Sine(9, random.randint(randint[0], randint[1])))
		
		_min = 30
		_max = 60
		
		for i in range(10, 13):
			self.dmx.channels[i-1].min = _min
			self.dmx.channels[i-1].max = _max
			self.dmx.generators.append(Sine(i, random.randint(randint[0], randint[1])))
			


executeVanillaTest(myDMXXX)