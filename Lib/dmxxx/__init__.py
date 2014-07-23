# -*- coding: utf-8 -*-


from ynlib.dmx import DMX
from ynlib.maths import Interpolate, InterpolateMany, NormalizeMinMax

import time, random, math, sys, os


	
############################################################################################################

### Main DMX class

class DMXXX(object):
	def __init__(self, devicePath, fps = 20):
		
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
		if self.dmxDevice:
			self.startTime = time.time()
			self.text('Loop started.')
			self.timer.start()

	def stop(self):
		if self.dmxDevice:
			self.text('Loop stopped.')
			self.timer.stop()
	
	def send(self):
		if self.dmxDevice:
			self.dmxDevice.send()

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
			self.dmxxx.dmxDevice.setValue(self.channel, self.value)

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
		self.min = 0.0
		self.max = 255.0
	
	def getValue(self, startTime):
		if self.generator:
			return self.normalize(self.generator.getValue(startTime))
		elif self.value:
			return self.normalize(self.value)
		else:
			return 0

	def normalize(self, value):
		return NormalizeMinMax(0.0, 255.0, self.min, self.max, value)


############################################################################################################

### Generators

class Sine(object):
	def __init__(self, duration, addDegrees = 0):
		self.duration = duration
		self.addDegrees = addDegrees

	def getValue(self, startTime):
		y = math.sin(math.radians(self.addDegrees + (float(time.time() - startTime) % (self.duration / 1000.0) / (self.duration / 1000.0) * 360.0)))
		return (y + 1) * .5 * 255.0

