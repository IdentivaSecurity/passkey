#Author: Victor Suarez Rovere
#Licensing: see file LICENSE.txt

import os, sys
import pygame

LEFTJUSTIFIED = 1
RIGHTJUSTIFIED = 2
CENTERJUSTIFIED = 3

import android
droid = None

class PasskeyUI:
	winsurf = None
	fontobj = None
	bkcolor1 = pygame.Color(0x40, 0x40, 0xA0)
	bkcolor2 = pygame.Color(0xA0, 0x40, 0x40)
	bkcolor = bkcolor1
	fgcolor = pygame.Color(192, 192, 192)
	fgcolor2 = pygame.Color(255, 255, 255)
	fontobj = None
	
	#displaysize = (320, 240)
	displaysize = (220, 176)
	
	
	def __init__(self):
		global droid
		try:
			droid = android.Android(('127.0.0.1',4321))
			try:
				droid.wakeLockAcquireBright()
				droid.makeToast("PASSKEY UI STARTED")
			finally:
			  	droid.wakeLockRelease()
		except:
			droid = None
			pass

		pygame.init()

		self.winsurf = pygame.display.set_mode(self.displaysize, pygame.RESIZABLE)
		self.displaysize = self.winsurf.get_size()
		#print >>sys.stderr, "Size", self.displaysize
		#pygame.display.toggle_fullscreen()
		pygame.display.set_caption(" ")
		self.fontobj = pygame.font.Font(None, self.get_ypercent(12+5))
		self.fontobj2 = pygame.font.Font("freesansbold.ttf", self.get_ypercent(18+4))
		self.fontobj3 = pygame.font.Font("freesansbold.ttf", self.get_ypercent(12+5))
		
		self.clear()
		self.display_msgbox("Confirm Login", "YourBank.com");
	
	def do_idle(self):
		event = pygame.event.poll()
		if event.type == pygame.QUIT:
			pygame.display.quit()
		elif event.type == pygame.VIDEORESIZE:
			print >>sys.stderr, "event", event
			self.displaysize= event.dict['size']
			#self.clear()
		
	def get_xcenter(self):
		return self.displaysize[0]//2

	def get_ycenter(self):
		return self.displaysize[1]//2
		
	def get_xpercent(self, percent):
		return self.displaysize[0]*percent//100

	def get_ypercent(self, percent):
		return self.displaysize[1]*percent//100

	def update(self):
		pygame.display.update()
		
	def clear(self):
		self.winsurf.fill(self.bkcolor)
		self.update()
		
	def display_text(self, msg, font, color, pos, just):
		msgsurf = font.render(msg, True, color)
		msgrect = msgsurf.get_rect()
		if just == LEFTJUSTIFIED:
			msgrect.topleft = pos
		elif just == CENTERJUSTIFIED:
			msgrect.centerx = pos[0] + self.displaysize[0]/2
			msgrect.top = pos[1]
		else:
			msgrect.left = pos[0] + self.displaysize[0] - msgrect.width
			msgrect.top = pos[1]
		self.winsurf.blit(msgsurf, msgrect)
		self.update()


	def display_msg(self, title, msg, msg2 = None):
		if droid is None:
			self.clear()
			self.display_text(title, self.fontobj, self.fgcolor, (0, self.get_ypercent(7)), CENTERJUSTIFIED)
		
			self.display_text(msg, self.fontobj2 if len(msg) <= 16 else self.fontobj3, self.fgcolor2, (0, self.get_ypercent(20)), CENTERJUSTIFIED)
			self.display_text(msg2, self.fontobj, self.fgcolor2, (0, self.get_ypercent(45)), CENTERJUSTIFIED)
			self.update()
		else:
			try:
				#droid.wakeLockAcquireBright()
				message = msg
				if msg2 is not None: message += " ("+msg2+")"
				self.currentdialog = droid.dialogCreateAlert(title, message)
			finally:
				#droid.wakeLockRelease()
				pass
		
	def display_msgbox(self, title, msg, msg2 = None):
		self.display_msg(title, msg, msg2)
		if droid is None:
			self.display_text(" Accept ", self.fontobj, self.fgcolor, (0, self.get_ypercent(85)), LEFTJUSTIFIED)
			self.display_text(" Cancel ", self.fontobj, self.fgcolor, (0, self.get_ypercent(85)), RIGHTJUSTIFIED)
			self.update()
		else:
			droid.wakeLockAcquireBright()
			try:
				droid.dialogSetPositiveButtonText('Accept')
				droid.dialogSetNegativeButtonText('Reject')
				"""
				posbutton = self.currentdialog.getButton('positive')
				if posbutton: posbutton.setTextSize(16)
				negbutton = self.currentdialog.getButton('negative')
				if negbutton: negbutton.setTextSize(16)
				"""
				droid.dialogShow()
			finally:
				#droid.wakeLockRelease()
				pass
		
	def beep(self):
		os.system("beep")

	def ask_msg(self, title, msg, msg2 = None):
		self.beep()
		self.display_msgbox(title, msg, msg2)
		response = self.ask_yesno()
		self.clear()
		self.update()
		return response

	def key_was_pressed(self, key):
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN:
				if event.key == key:
					return True
		return False
		
	def ask_yesno(self):
		response = None
		if droid is None:
			while response is None:
				for event in pygame.event.get():
					if event.type == pygame.KEYDOWN:
						if event.key == ord('a') or event.key == pygame.K_RETURN:
							response = True
							break
						if event.key == ord('c') or event.key == pygame.K_ESCAPE:
							response = False
							break
		else:
		  	droidresponse = droid.dialogGetResponse().result
		  	response = droidresponse['which'] == 'positive'

		return response

	def notify_learningmode(self, learning):
		self.bkcolor = self.bkcolor2 if learning else self.bkcolor1
		self.display_msg("Learning mode", "Enabled" if learning else "Disabled")
		
	
