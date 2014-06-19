from vanilla import *
from vanilla.test.testTools import executeVanillaTest
from AppKit import *
from ynlib.colors import *
from ynlib.dmx import DMX
from ynlib.maths import Interpolate, InterpolateMany, NormalizeMinMax
from ynlib.preferences import Preferences
import time, random, math, sys, os


#sys.stderr = sys.stdout

APPNAME = 'DMXXX'
#AUPFILE = '/Users/yanone/Projekte/Antithesis/11 - Produktion/DMX Light Show/Neon Natives.aup'


class YN_NSImageView(NSImageView):
	def scrollWheel_(self, event):
		self.vanillaWrapper().scrollWheel_(event)
		
	def mouseEntered_(self, event):
		self.vanillaWrapper().mouseEntered_(event)

	def mouseExited_(self, event):
		self.vanillaWrapper().mouseExited_(event)

	def mouseUp_(self, event):
		self.vanillaWrapper().mouseUp_(event)
		

class DMXChannelImageView(ImageView):
	nsImageViewClass = YN_NSImageView

	def scrollWheel_(self, event):
#		print event.deltaY()
		if event.deltaY() > 0:
#			print '+1'
			self.setValue(self.value + 1, saveToPreferences = True, normalize = False, informAboutValue = True)
		else:
#			print '-1'
			self.setValue(self.value - 1, saveToPreferences = True, normalize = False, informAboutValue = True)

	def mouseEntered_(self, event):
		self.mouseEntered = True
		self.drawValue()

	def mouseExited_(self, event):
		self.mouseEntered = False
		self.drawValue()

	def mouseUp_(self, event):
#		wtop = self.window.w.getPosSize()[1]
#		wheight = self.window.w.getPosSize()[3]
		selftop = self.getNSImageView().frame().origin.y
#		selfheight = self.getNSImageView().frame().size.height
#		screenheight = self.window.w.getNSWindow().screen().frame().size.height
		mouselocation = self.window.w.getNSWindow().mouseLocationOutsideOfEventStream().y
		y = int(math.ceil(mouselocation - selftop) - 1)
		self.setValue(y, saveToPreferences = True, normalize = False, informAboutValue = True)

	def setInitValues(self, window, channel, value):
		self.window = window
		self.mouseEntered = False
		self.channel = channel
		self.value = value
		self.width = self.getPosSize()[2]
		self.height = self.getPosSize()[3]
		self.min = 0
		self.max = 255

		# Priority
		self.attack = 200
		self.release = 2000
		self.priorityValue = None
		self.priorityValueTime = None

	def setPriorityValue():

	def drawOnWindow(self):
		
		if self.channel % 10 == 0:

			# Label
			if self.channel > 0:
				exec('self.window.w.dmxChannelNavigationTextBox' + str(self.channel) + ' = TextBox((' + str(self.getPosSize()[0]-14) + ', ' + str(self.getPosSize()[1]-15) + ', 30, 17), "' + str(self.channel) + '", sizeStyle="mini", alignment="center")')
		
		self.foregroundcolor = HextoRGB('e3004f')

		exec('self.window.w.dmxChannelSlider%s = self' % (self.channel))
		self.drawValue()
		
		
	def setValue(self, value, saveToPreferences = False, informAboutValue = False, normalize = True):
		
		# normaliuze
		if value < 0:
			value = 0
		elif value > 255:
			value = 255
		
		if self.value != value:
			self.value = value
			
			
			#NormalizeMinMax(source_floor, source_ceiling, target_floor, target_ceiling, value):
			
			if normalize:
				self.value = int(NormalizeMinMax(0, 255, self.min, self.max, self.value))

			if self.window.w.dmx:
				self.window.w.dmx.setValue(self.channel, self.value)
			self.drawValue()
			
			if informAboutValue:
				self.window.text('Channel %s Value %s' % (self.channel, self.value))

			if saveToPreferences:
				if self.value > 0:
					self.window.preferences.put('DMX Channel %s' % (self.channel), self.value)
				elif self.value == 0:
					self.window.preferences.delete('DMX Channel %s' % (self.channel))



	def drawValue(self, message = None):

		if message:
			print message
		
		if self.mouseEntered:
			self.setImage(imageObject=self.window.channelImages[1][self.value])
		else:
			if self.channel % 10 == 0:
				self.setImage(imageObject=self.window.channelImages[2][self.value])
			elif self.channel % 5 == 0:
				self.setImage(imageObject=self.window.channelImages[1][self.value])
			else:
				self.setImage(imageObject=self.window.channelImages[0][self.value])
		



################################################################################################################

class AUPWaveTrack(object):
	def __init__(self, node):
		self.node = node
		self.sampleRate = self.node._attrs['rate'].nodeValue
		self.lengthInSamples = self.node.childNodes[1].childNodes[1]._attrs['numsamples'].nodeValue
		self.audioTrack = self.node.childNodes[1].childNodes[1].childNodes[1].childNodes[1]._attrs['aliasfile'].nodeValue
		self.lengthInSeconds = float(self.lengthInSamples) / float(self.sampleRate)

class AUPDMXChannel(object):
	def __init__(self, node):
		self.node = node
		self.name = self.node._attrs['name'].nodeValue
		self.minValue = 0
		self.maxValue = 255
		self.channel = int(self.name.split(' ')[1])
		self.commands = []
		for child in self.node.childNodes:
			if child.nodeName == u'label':
				self.commands.append(AUPDMXCommand(self, child))
		
		# DIM
		if 'DIM' in self.name:
			_list = self.name.split(' ')
			self.maxValue = _list[_list.index('DIM') + 1]


	def dim(self, value):
		return int(NormalizeMinMax(0, 255, self.minValue, self.maxValue, value))

	def startValue(self):
		
		for command in self.commands:
			if float(command.startTime) == 0.0:
				return self.dim(command.values[0])
		
		return self.dim(self.minValue)

	def __repr__(self):
		return '<AUP DMX Channel %s>' % (self.channel)
		
class AUPDMXCommand(object):
	def __init__(self, parent, node):
		self.parent = parent
		self.node = node
		self.valueString = self.node._attrs['title'].nodeValue
		if '>' in self.valueString:
			self.values = self.valueString.split('>')
			self.values = map(float, self.values)
		elif self.valueString == 'blink':
			self.values = [0.0, 255.0, 0.0]
		elif self.valueString == 'on':
			self.values = [255.0]
		elif self.valueString == 'fade in':
			self.values = [0.0, 255.0]
		elif self.valueString == 'fade out':
			self.values = [255.0, 0.0]
		else:
			self.values = [float(self.valueString)]
		self.startTime = float(self.node._attrs['t'].nodeValue)
		self.endTime = float(self.node._attrs['t1'].nodeValue)
		
		self.currentValue = 0
		
	def valueAtT(self, t):
		t = float(t)
		
		p = float(t - self.startTime) / float(self.endTime-self.startTime)
		
		if self.startTime <= t <= self.endTime:

			newValue = InterpolateMany(self.values, p)[0]

		elif self.endTime <= t <= self.endTime + 1 * self.refreshRate / 1000.0:
			newValue = self.values[-1]

		elif self.startTime - 1 * self.refreshRate / 1000.0 <= t <= self.startTime:
			newValue = self.values[0]


		else:
			newValue = 0
		
		if newValue != self.currentValue:
			self.currentValue = newValue
			return self.parent.dim(newValue)
			
#		else:
#			return 0

	def __repr__(self):
		return '<AUP DMX Command value %s on channel %s>' % (self.value, self.parent.channel)


class AUP(object):
	def __init__(self, path):
		from xml.dom.minidom import parse
		self.path = path
		self.dom = parse(self.path)

		self.waveTracks = []
		self.dmxChannels = []

		for node in self.dom.childNodes[1].childNodes:
			if node.nodeName == u'wavetrack':
				self.waveTracks.append(AUPWaveTrack(node))
			elif node.nodeName == u'labeltrack' and node._attrs['name'].nodeValue.startswith('DMX'):
				self.dmxChannels.append(AUPDMXChannel(node))


class sound:
	def __init__(self, file):
		self._sound = NSSound.alloc()
		self._sound.initWithContentsOfFile_byReference_(file, True)
	def play(self): self._sound.play()
	def stop(self):
		if self.is_playing():
			self._sound.stop()
	def is_playing(self): return self._sound.isPlaying()
	def currentTime(self): return self._sound.currentTime()
	def setCurrentTime(self, time): return self._sound.setCurrentTime_(time)


####################################################################################################

import threading
class DMXObserver(threading.Thread): 
	def __init__(self, window): 
		threading.Thread.__init__(self) 
		self.window = window
 
	def run(self): 
		
		
		while True:


			if self.window.playStatus == 'playing':
				
				for generator in self.window.generators:
					generator.act(self.window)
				
			if self.window.sound:
				if self.window.sound.is_playing():

					pool = NSAutoreleasePool.alloc().init()
					t = self.window.sound.currentTime()
			
					if t > 0.0:
				
						for channel in self.window.aup.dmxChannels:
							for command in channel.commands:
								level = command.valueAtT(t)
								if level != None:
		#							print command.parent.channel, level
									self.window.channels[command.parent.channel - 1].setValue(level)
					

						self.window.w.musicSlider.set(t)
				
						timecode = str(t).split('.')[0] + ':' + str(t).split('.')[1][:2]
						self.window.w.timeCode.set(timecode)
					else:
						self.window.stopMusicButtonCallback()

					del pool

			#if self.window.w.dmx:
			self.window.w.dmx.send()

			time.sleep(self.window.refreshRate / 1000.0)
			self.window.increment += 1
			

	def stop(self):
		self._Thread__stop()


####################################################################################################


class Sine(object):
	def __init__(self, channel, duration):
		import math
		self.channel = channel
		self.duration = duration
	
	def act(self, window):
		
		
		y = math.sin(math.radians(window.increment * window.fps * 1 / (float(self.duration) / 1000.0)))# * window.refreshRate / self.duration))# * self.duration / window.refreshRate))
		level = int((y + 1) * .5 * 255)
		window.channels[self.channel - 1].setValue(level)
		
#		print window.increment



class DMXXXWindow(object):

	def __init__(self, refreshRate):
		self.refreshRate = refreshRate
		self.fps = 1000.0 / self.refreshRate
		self.w = Window((1280, 700), "DMXXX", closable=True)
		#self.w.myButton = Button((10, 10, -10, 20), "My Button")
		#self.w.myTextBox = TextBox((10, 40, -10, 17), "My Text Box")

		self.w.textBox = TextBox((10, 670, -10, 17), "")

		self.preferences = Preferences('de.yanone.DMXXX')

		self.playStatus = 'stopped'
		self.aupFilePath = ''
		self.aup = None
		self.sound = None
		
		self.generators = []

		self.increment = 0

		# Set up channels
		self.channels = []
#		for i in range(512):
#			newChannel = DMXChannelImageView((x+1, y, self.width, self.height))
#			newChannel.setInitValues(i+1, 0)
#			self.channels.append(newChannel)


		width = 4
		height = 256
		self.channelImages = [[], [], []]
		backgroundColors = [HextoRGB('D5D5D5'), HextoRGB('A5A5A5'), HextoRGB('858585')]
		foregroundcolor = HextoRGB('e3004f')

		for t in range(3):
			for i in range(256):
				image = NSImage.alloc().initWithSize_((width, height))
				image.lockFocus()

				NSColor.colorWithCalibratedRed_green_blue_alpha_(backgroundColors[t][0], backgroundColors[t][1], backgroundColors[t][2], 1.0).set()
				path = NSBezierPath.bezierPath()
				path.moveToPoint_((0, 0))
				path.lineToPoint_((0, height))
				path.lineToPoint_((width, height))
				path.lineToPoint_((width, 0))
				path.lineToPoint_((0, 0))
				path.fill()

				NSColor.colorWithCalibratedRed_green_blue_alpha_(foregroundcolor[0], foregroundcolor[1], foregroundcolor[2], 1.0).set()
				path = NSBezierPath.bezierPath()
				path.moveToPoint_((0, 1))
				path.lineToPoint_((0, i + 1))
				path.lineToPoint_((width, i + 1))
				path.lineToPoint_((width, 1))
				path.lineToPoint_((0, 1))
				path.fill()
		
				image.unlockFocus()
				self.channelImages[t].append(image)



		
		for i in range(512):
			if i < 256:
				x = i*5
				y = 20
			else:
				x = (i-256)*5
				y = 300

			newChannel = DMXChannelImageView((x+1, y, 4, 256))
			newChannel.setInitValues(self, i+1, 0)
			self.channels.append(newChannel)
			self.channels[i].drawOnWindow()
			

		# Precalculate DMX values
		self.dmxInitValues = {}
		for i in range(512):
			valueFromPreferences = self.preferences.get('DMX Channel %s' % (i+1))
			if valueFromPreferences:
				self.dmxInitValues[i+1] = valueFromPreferences

		
		
		try:
			self.w.dmx = DMX('/dev/cu.usbserial-ENVVVCOF', self.dmxInitValues)
			self.text('DMX USB device found')
		except:
			self.w.dmx = None
			self.text('DMX USB device not found. Please restart application.')


		# Apply initial DMX values
		for i in range(512):
			valueFromPreferences = self.preferences.get('DMX Channel %s' % (i+1))
			if valueFromPreferences:
				#print valueFromPreferences, type(valueFromPreferences)
				self.channels[i].setValue(valueFromPreferences)
		
		if self.w.dmx:
			self.w.dmx.send()


			
		self.w.playMusicButton = Button((10, 630, 100, 20), "Play", callback=self.playMusicButtonCallback)
		self.w.stopMusicButton = Button((120, 630, 100, 20), "Stop", callback=self.stopMusicButtonCallback)
		self.w.timeCode = TextBox((10, 575, 50, 17), "0:00", alignment='right')
		self.w.musicSlider = Slider((10, 600, -10, 23), callback = self.musicSliderCallBack)
		
		self.w.bind('became main', self.windowBecameMainCallback)
		self.w.bind('close', self.windowCloseCallback)
		self.w.open()
		
		self.loadMusicButtonCallback()

		self.dmxObserver = DMXObserver(self)
		self.dmxObserver.start()

	def loadAUPFile(self, filePath):
		self.aupFilePath = filePath
		self.aup = AUP(self.aupFilePath)
		for channel in self.aup.dmxChannels:
			self.dmxInitValues[channel.channel] = channel.startValue()

	def loadMusicButtonCallback(self, sender = None):
		
		self.playStatus = 'stopped'
		if self.aupFilePath:
			self.w.setTitle(APPNAME + ' - ' + os.path.basename(self.aupFilePath))

			self.aup = AUP(self.aupFilePath)
			self.sound = sound(self.aup.waveTracks[0].audioTrack)

		self.stopMusicButtonCallback()
		self.w.musicSlider.setMinValue(0)
		if self.aup:
			self.w.musicSlider.setMaxValue(self.aup.waveTracks[0].lengthInSeconds)
		self.resetAllChannels()

	def text(self, string):
		self.w.textBox.set(str(string))
	
	def playMusicButtonCallback(self, sender = None):
		self.loadMusicButtonCallback()
		if self.sound:
			self.sound.play()
		self.playStatus = 'playing'

	def musicSliderCallBack(self, sender):
		if self.sound:
			self.sound.setCurrentTime(sender.get())

	def pauseMusicButtonCallback(self, sender = None):
		pass

	def stopMusicButtonCallback(self, sender = None):
		if self.playStatus == 'playing':
			if self.sound:
				self.sound.stop()
			self.playStatus = 'stopped'
		self.w.timeCode.set('0:00')
		self.resetAllChannels()
		self.w.musicSlider.set(0)

	def windowBecameMainCallback(self, sender = None):
		pass
		
	def windowCloseCallback(self, sender = None):
		self.dmxObserver.stop()

	def zeroAllButtonCallback(self, sender = None):
		self.resetAllChannels()

	def resetAllChannels(self):
		if self.aup:
			for channel in self.aup.dmxChannels:
				#print channel.channel, channel.startValue()
				self.channels[channel.channel-1].setValue(channel.startValue())

	def eventHandler(self, event):
		loc = NSEvent.mouseLocation()
		print NSScreen.mainScreen.visibleFrame
		
		print event
#		if event.type() == NSLeftMouseUp:
#			print self.window.getPosSize()
		print loc.x, loc.y
		
#		for dmxChannel in self.channels:
#			
#			in_x = loc.x > dmxChannel.window.getPosSize()[0] + dmxChannel.dmxChannelSlider.getPosSize()[0] and loc.x < dmxChannel.window.getPosSize()[0] + dmxChannel.dmxChannelSlider.getPosSize()[0] + dmxChannel.width + 1
#			in_y = dmxChannel.window.getPosSize()[1] + dmxChannel.dmxChannelSlider.getPosSize()[1] < loc.y and loc.y < dmxChannel.window.getPosSize()[1] + dmxChannel.dmxChannelSlider.getPosSize()[1] + dmxChannel.height + 1
#			if in_x and in_y:
#				print dmxChannel.channel, loc.x, loc.y
			
#			if self.window.getPosSize()[0] + self.windochannelslider%s



class DMXXX(object):
	def __init__(self, refreshRate = 50):
		self.refreshRate = 50
		self.dmx = DMXXXWindow(refreshRate = self.refreshRate)
		self.userInit()
		

	def userInit(self):
		pass
		
