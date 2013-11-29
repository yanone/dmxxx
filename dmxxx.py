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
DMXREFRESHRATE = 50 #ms
#AUPFILE = '/Users/yanone/Projekte/Antithesis/11 - Produktion/DMX Light Show/Neon Natives.aup'
AUPFILE = '/Users/yanone/Projekte/Antithesis/11 - Produktion/DMX Light Show/Pyramide.aup'


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
			self.setValue(self.value + 1, saveToPreferences = True)
		else:
#			print '-1'
			self.setValue(self.value - 1, saveToPreferences = True)

	def mouseEntered_(self, event):
		print self.channel

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
		self.setValue(y, saveToPreferences = True)

	def setInitValues(self, window, channel, value):
		self.window = window
		self.mouseEntered = False
		self.channel = channel
		self.value = value
		self.width = self.getPosSize()[2]
		self.height = self.getPosSize()[3]

	def drawOnWindow(self):
		
		if self.mouseEntered:
			self.backgroundcolor = HextoRGB('D5D5D5')
		else:
			self.backgroundcolor = HextoRGB('959595')
		
		if self.channel % 5 == 0:
			self.backgroundcolor = HextoRGB('A5A5A5')
		if self.channel % 10 == 0:
			self.backgroundcolor = HextoRGB('858585')

			# Label
			if self.channel > 0:
				exec('self.window.w.dmxChannelNavigationTextBox' + str(self.channel) + ' = TextBox((' + str(self.getPosSize()[0]-14) + ', ' + str(self.getPosSize()[1]-15) + ', 30, 17), "' + str(self.channel) + '", sizeStyle="mini", alignment="center")')
		
		self.foregroundcolor = HextoRGB('e3004f')

		exec('self.window.w.dmxChannelSlider%s = self' % (self.channel))
		self.drawValue()
		
		
	def setValue(self, value, saveToPreferences = False):
		
		# normaliuze
		if value < 0:
			value = 0
		elif value > 255:
			value = 255
		
		if self.value != value:
			self.value = value
			if self.window.w.dmx:
				self.window.w.dmx.setValue(self.channel, self.value)
			self.drawValue()
			self.window.text('Channel %s Value %s' % (self.channel, self.value))

			if saveToPreferences:
				if self.value > 0:
					self.window.preferences.set('DMX Channel %s' % (self.channel), self.value)
				elif self.value == 0:
					self.window.preferences.delete('DMX Channel %s' % (self.channel))



	def drawValue(self, message = None):

		if message:
			print message
		image = NSImage.alloc().initWithSize_((self.width, self.height))
		image.lockFocus()
		
#		NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 1.0).set()
#		image.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(self.backgroundcolor[0], self.backgroundcolor[1], self.backgroundcolor[2], 1.0))

		NSColor.colorWithCalibratedRed_green_blue_alpha_(self.backgroundcolor[0], self.backgroundcolor[1], self.backgroundcolor[2], 1.0).set()
		path = NSBezierPath.bezierPath()
		path.moveToPoint_((0, 0))
		path.lineToPoint_((0, self.height))
		path.lineToPoint_((self.width, self.height))
		path.lineToPoint_((self.width, 0))
		path.lineToPoint_((0, 0))
		path.fill()

		NSColor.colorWithCalibratedRed_green_blue_alpha_(self.foregroundcolor[0], self.foregroundcolor[1], self.foregroundcolor[2], 1.0).set()
		path = NSBezierPath.bezierPath()
		path.moveToPoint_((0, 1))
		path.lineToPoint_((0, self.value + 1))
		path.lineToPoint_((self.width, self.value + 1))
		path.lineToPoint_((self.width, 1))
		path.lineToPoint_((0, 1))
		path.fill()
		
		image.unlockFocus()
		self.setImage(imageObject=image)
		


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

		elif self.endTime <= t <= self.endTime + 1 * DMXREFRESHRATE / 1000.0:
			newValue = self.values[-1]

		elif self.startTime - 1 * DMXREFRESHRATE / 1000.0 <= t <= self.startTime:
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


			if self.window.sound.is_playing():

				pool = NSAutoreleasePool.alloc().init()
				t = self.window.sound.currentTime()
			
				if t > 0.0:
				
					for channel in self.window.aup.dmxChannels:
						for command in channel.commands:
							level = command.valueAtT(t)
							if level != None:
	#							print command.parent.channel, level
								self.window.w.dmxChannels[command.parent.channel - 1].setValue(level)
					
					if self.window.w.dmx:
						self.window.w.dmx.send()

					self.window.w.musicSlider.set(t)
				
					timecode = str(t).split('.')[0] + ':' + str(t).split('.')[1][:2]
					self.window.w.timeCode.set(timecode)
				else:
					self.window.stopMusicButtonCallback()

				del pool

			time.sleep(DMXREFRESHRATE / 1000.0)
			

	def stop(self):
		self._Thread__stop()


####################################################################################################



class DMXXXWindow(object):

	def __init__(self):
		self.w = Window((1280, 700), "DMXXX", closable=True)
		#self.w.myButton = Button((10, 10, -10, 20), "My Button")
		#self.w.myTextBox = TextBox((10, 40, -10, 17), "My Text Box")

		self.w.textBox = TextBox((10, 670, -10, 17), "")

		self.preferences = Preferences('de.yanone.DMXXX')




		# Set up channels
		self.w.dmxChannels = []
#		for i in range(512):
#			newChannel = DMXChannelImageView((x+1, y, self.width, self.height))
#			newChannel.setInitValues(i+1, 0)
#			self.w.dmxChannels.append(newChannel)
		
		for i in range(512):
			if i < 256:
				x = i*5
				y = 20
			else:
				x = (i-256)*5
				y = 300

			newChannel = DMXChannelImageView((x+1, y, 4, 256))
			newChannel.setInitValues(self, i+1, 0)
			self.w.dmxChannels.append(newChannel)
			self.w.dmxChannels[i].drawOnWindow()
			

		# Precalculate DMX values
		dmxInitValues = {}
		for i in range(512):
			valueFromPreferences = self.preferences.get('DMX Channel %s' % (i+1))
			if valueFromPreferences:
				dmxInitValues[i+1] = valueFromPreferences

		self.aup = AUP(AUPFILE)
		for channel in self.aup.dmxChannels:
			dmxInitValues[channel.channel] = channel.startValue()
		
		
		try:
			self.w.dmx = DMX('/dev/cu.usbserial-ENVVVCOF', dmxInitValues)
			self.text('DMX USB device found')
		except:
			self.w.dmx = None
			self.text('DMX USB device not found. Please restart application.')


		# Apply initial DMX values
		for i in range(512):
			valueFromPreferences = self.preferences.get('DMX Channel %s' % (i+1))
			if valueFromPreferences:
				#print valueFromPreferences, type(valueFromPreferences)
				self.w.dmxChannels[i].setValue(valueFromPreferences)
		
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

	def loadMusicButtonCallback(self, sender = None):
		
		self.playStatus = 'stopped'
		self.w.setTitle(APPNAME + ' - ' + os.path.basename(AUPFILE))
		self.aup = AUP(AUPFILE)
		self.sound = sound(self.aup.waveTracks[0].audioTrack)

		self.stopMusicButtonCallback()
		self.w.musicSlider.setMinValue(0)
		self.w.musicSlider.setMaxValue(self.aup.waveTracks[0].lengthInSeconds)
		self.resetAllChannels()

	def text(self, string):
		self.w.textBox.set(str(string))
	
	def playMusicButtonCallback(self, sender = None):
		self.loadMusicButtonCallback()
		self.sound.play()
		self.playStatus = 'playing'

	def musicSliderCallBack(self, sender):
		self.sound.setCurrentTime(sender.get())

	def pauseMusicButtonCallback(self, sender = None):
		pass

	def stopMusicButtonCallback(self, sender = None):
		if self.playStatus == 'playing':
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
		for channel in self.aup.dmxChannels:
			#print channel.channel, channel.startValue()
			self.w.dmxChannels[channel.channel-1].setValue(channel.startValue())

	def eventHandler(self, event):
		loc = NSEvent.mouseLocation()
		print NSScreen.mainScreen.visibleFrame
		
		print event
#		if event.type() == NSLeftMouseUp:
#			print self.window.getPosSize()
		print loc.x, loc.y
		
#		for dmxChannel in self.w.dmxChannels:
#			
#			in_x = loc.x > dmxChannel.window.getPosSize()[0] + dmxChannel.dmxChannelSlider.getPosSize()[0] and loc.x < dmxChannel.window.getPosSize()[0] + dmxChannel.dmxChannelSlider.getPosSize()[0] + dmxChannel.width + 1
#			in_y = dmxChannel.window.getPosSize()[1] + dmxChannel.dmxChannelSlider.getPosSize()[1] < loc.y and loc.y < dmxChannel.window.getPosSize()[1] + dmxChannel.dmxChannelSlider.getPosSize()[1] + dmxChannel.height + 1
#			if in_x and in_y:
#				print dmxChannel.channel, loc.x, loc.y
			
#			if self.window.getPosSize()[0] + self.window.dmxChannelSlider%s



executeVanillaTest(DMXXXWindow)