# -*- coding: utf-8 -*-


from ynlib.dmx import DMX
from ynlib.maths import Interpolate, InterpolateMany, NormalizeMinMax
from ynlib.beziers import SplitCubicAtT, Point

import time, random, math, sys, os


	
############################################################################################################

### Main DMX class


MIN = 0.0
MAX = 1.0



class DMXXX(object):
	def __init__(self, devicePath, fps = 20):
		
		self.started = False
		
		# DMX
		self.channels = []
		for i in range(512):
			self.channels.append(deviceChannel(self, i+1))
		self.devicePath = devicePath
		try:
			self.dmxDevice = DMX(devicePath)
			self.text('DMX USB device found.')
		except:
			self.dmxDevice = None
			self.text('DMX USB device not found. Please restart application.')
		
		
		# Scenes
		self.scenes = []
		self.scene = None # Default

		# Timing
		self.fps = fps
		self.refreshRate = 1000.0 / self.fps
		self.click = 0
		self.playStatus = 'stopped'
		
		self.timer = self.dmxObserver = Timer(self)

	def text(self, string):
		print string

	def start(self):
		if not self.started:
			if self.dmxDevice:
				self.startTime = time.time()
				self.text('Loop started.')
				self.timer.start()
				self.started = True

	def stop(self):
		if self.dmxDevice:
			self.text('Loop stopped.')
			self.timer.stop()
			self.started = False
	
	def send(self):
		if self.dmxDevice:
			self.dmxDevice.send()
		else:
			raise Exception("No DMX device connected (in software)")

	def channel(self, channel):
		return self.channels[channel - 1]


# Device channel, communication channel to the DMX device

class deviceChannel(object):
	def __init__(self, dmxxx, channel, initValue = None):
		self.dmxxx = dmxxx
		self.channel = channel
		self.value = initValue
	
	def setValue(self, value):
		if value != self.value:
			self.value = value
			
#			print self.value
			
			self.dmxxx.dmxDevice.setValue(self.channel, int(self.value * 255))

# Timed execution thread

import threading
class Timer(threading.Thread): 
	def __init__(self, dmxxx): 
		threading.Thread.__init__(self) 
		self.dmxxx = dmxxx
 
	def run(self):
		
		
		while True:

			for channel in self.dmxxx.scene.channels:
				value = channel.getValue(self.dmxxx.startTime)
				self.dmxxx.channel(channel.channel).setValue(value)

			self.dmxxx.send()

			time.sleep(1.0 / self.dmxxx.fps)
			self.dmxxx.click += 1
			

	def stop(self):
		self._Thread__stop()




############################################################################################################

### Scenes


class Scene(object):
	def __init__(self, name = ''):
		self.name = name
		self.channels = []
		for i in range(512):
			self.channels.append(Channel(i+1))
	
	def channel(self, channel):
		return self.channels[channel - 1]

	def textView(self):
		print 'Scene "%s"' % self.name
		for channel in self.channels:
			if channel.value or channel.generator:
				print 'Channel %s: %s' % (str(channel.channel).rjust(3), str(channel.value).rjust(3))
		

class Channel(object):
	def __init__(self, channel, initValue = None, generator = None):
		self.channel = channel
		self.value = initValue
		self.generator = generator
		self.min = MIN
		self.max = MAX
		self.curveAdjust = 0
	
	def getValue(self, startTime):
		
		value = 0
		
		if self.generator:
			value = self.normalize(self.generator.getValue(startTime))
#			print 'generator:', value

		elif self.value:
			value = self.normalize(self.value)

#		print 'before curveAdjust:', value
		if self.curveAdjust:
			value = self.adjustCurve(value)
#		print 'after curveAdjust:', value
		return value

	def normalize(self, value):
#		print 'NormalizeMinMax', MIN, MAX, self.min, self.max, value
		return NormalizeMinMax(MIN, MAX, self.min, self.max, value)

	def adjustCurve(self, value):
		u"""\
		Adjusts value to dimming brightness curve (set in Channel.curveAdjust from 1.0 (brighter) to -1.0 (darker)
		"""

		p1 = Point(MIN, self.min)
		p4 = Point(MAX, self.max)
		p2 = Interpolate(p1, p4, .3)
		p3 = Interpolate(p1, p4, .7)

		if self.curveAdjust > 0:
			corner = Point(MIN, self.max)
			p2 = Interpolate(p2, corner, self.curveAdjust)
			p3 = Interpolate(p3, corner, self.curveAdjust)
		elif self.curveAdjust < 0:
			corner = Point(MAX, self.min)
			p2 = Interpolate(p2, corner, -1 * self.curveAdjust)
			p3 = Interpolate(p3, corner, -1 * self.curveAdjust)

		t = float(value - self.min) / float(self.max - self.min)
	
		p = SplitCubicAtT(p1, p2, p3, p4, t)

		return p[0][3].y


############################################################################################################

### Generators

class Sine(object):
	def __init__(self, duration, addDegrees = 0):
		self.duration = duration
		self.addDegrees = addDegrees

	def getValue(self, startTime):
		y = math.sin(math.radians(self.addDegrees + (float(time.time() - startTime) % (self.duration / 1000.0) / (self.duration / 1000.0) * 360.0)))
#		print 'y', (y + 1) * .5
		return (y + 1) * .5

