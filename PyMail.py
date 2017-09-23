#!/usr/bin/python3

import curses
import sys
from curses      import textpad
from cursProgressbar import Progressbar
from cursDialog  import *
from mailFetcher import Fetcher
from mailParser  import Parser, textwrap

messageDict = { }

EXIT     = 0
CONTINUE = 1

FOCUS    = curses.A_BOLD | curses.A_STANDOUT
NO_FOCUS = curses.A_NORMAL

tmpencode= 'utf8'

class PyMail(Fetcher):
	UP    = LEFT  = -1
	DOWN  = RIGHT = 1
	MARKING   = curses.A_STANDOUT
	NO_MARKING= curses.A_NORMAL
	def __init__(self, servername, user, password, ssl=False):
		Fetcher.__init__(self, servername, user, password, ssl)
		self.win = curses.newwin(y, x, 0, 0)
		self.Y, self.X  = self.win.getmaxyx( )
		self.WIN_LINES  = curses.LINES - 3
		self.topLineNum       = 0
		self.highlightLineNum = 0
		self.markedLineNum    = [ ]
		self.topbarFocus = 0
		self.display_pos  = [ ]
		#self.Translate( )
		self.MakeMainWindow( )
		#self.Help( )

		#self.loadAllHeaders( )
		self.loadAllMessages( )


	def MakeMainWindow(self):
		y, x = 2, 1
		self.topBar   = self.win.subwin(0, self.X, 0, 0)

		height, width = self.Y-3, int(self.X*0.3)-2
		self.indexWin = self.win.subwin(height, width, y, x)
		self.indexTextLengdth = width

		y, x = 2, int(self.X*0.3)+1
		height, width = 2, self.X-(int(self.X*0.3))-2
		self.titleWin = self.win.subwin(height, width, y, x)

		y, x = height*3, int(self.X*0.3)+1
		height, width = self.Y-y, self.X-(int(self.X*0.3))-2
		self.previewWin = self.win.subwin(height-1, width, y, x)

		self.Frame( )
		self.Topbar( )
		self.win.refresh( )

	def Frame(self):
		self.win.attrset(color_red | curses.A_BOLD)
		y, x = 2, 1
		height, width = self.Y-3, int(self.X*0.3)-2
		rectangle(self.win, y-1, x-1, height+2, width+x)

		self.win.attrset(color_blue | curses.A_BOLD)
		y, x = 2, int(self.X*0.3)+1
		height, width = 2, self.X-(int(self.X*0.3))-2
		rectangle(self.win, y-1, x-1, height+2, width+x)

		y, x = height*3, int(self.X*0.3)+1
		height, width = self.Y-y, self.X-(int(self.X*0.3))-2
		rectangle(self.win, y-1, x-1, height+(y-1), width+x)

		self.win.attrset(color_normal | curses.A_NORMAL)


	def Topbar(self):
		space = 2
		self.menufunc = ('Compose', 'Save', 'Delete', 'Find', 'Forward', 'Reply', 'Translate', 'Option', 'Help')
		self.topBar.addstr(0, 0, ' '*x, curses.A_STANDOUT | curses.A_BOLD)
		for f in self.menufunc:
			self.topBar.addstr(0, space,   f[0],  curses.A_STANDOUT | curses.A_BOLD | curses.A_UNDERLINE  )
			self.topBar.addstr(0, space+1, f[1:], curses.A_STANDOUT | curses.A_BOLD)
			self.display_pos.append(space)
			space = space + len(f) + 2
		self.topBar.addstr(0, x-10, "PyMail 0.1", curses.A_STANDOUT)
		self.topBar.addstr(0, self.display_pos[self.topbarFocus],   self.menufunc[self.topbarFocus][0],  )#curses.A_BOLD | curses.A_UNDERLINE)
		self.topBar.addstr(0, self.display_pos[self.topbarFocus]+1, self.menufunc[self.topbarFocus][1:], )#curses.A_BOLD)
		self.topBar.refresh( )


	def displayMessage(self, **kw):
		self.markLine( )

		self.win.erase( )

		y, x = 2, 1
		height, width = 4, self.X-2
		headerWin = self.win.subwin(height, width, y, x)

		y, x = height*2, 1
		height, width = self.Y-y, self.X-2
		messageWin = self.win.subwin(height-1, width, y, x)

		y, x = 2, 1
		height, width = 4, self.X-2
		self.win.attrset(color_blue | curses.A_BOLD)
		rectangle(self.win, y-1, x-1, height+2, width+x)

		y, x = height*2, 1
		height, width = self.Y-y, self.X-2
		rectangle(self.win, y-1, x-1, height+(y-1), width+x)
		self.win.attrset(color_normal | curses.A_NORMAL)

		hight, width = self.Y-9, self.X-2
		msgnum = self.topLineNum + self.highlightLineNum + 1

		if not kw:
			subj, frm, to, date, msg = messageDict.get(msgnum, 'Error')
		else:
			for value in kw.values( ):
				subj, frm, to, date, msg = value


		msg = textwrap(text=msg, width=width).split('\n')

		headerWin.addstr(0, 0, 'Subject: %s' % subj.strip( ))#[0:self.X-12])
		headerWin.addstr(1, 0, 'From   : %s' % frm.strip( ) )#[0:self.X-9])
		headerWin.addstr(2, 0, 'To     : %s' % to.strip( )  )#[0:self.X-9])
		headerWin.addstr(3, 0, 'Date   : %s' % date.strip( ))#[0:self.X-9])

		top    = 0
		bottom = hight

		self.scrollingText(textpad=messageWin, text=msg, top=0, bottom=hight-2, y=hight-1, x=width)
		self.markLine( )


	def scrollingText(self, textpad, text, top, bottom, y, x):

		lastKey   = int( )
		textlines = len(text)
		self.abort = False
		self.Topbar( )

		while True:
			textpad.erase( )
			for (i, lines) in enumerate(text[top:bottom+1]):
				textpad.addstr(i, 0, lines)
			cur_line = "%d - %d / %d" % (top+1, top+i+1, textlines)
			textpad.addstr(y, x-len(cur_line)-2, cur_line, color_green | curses.A_BOLD)
			textpad.refresh( )
			key = screen.getch( )

			if key == curses.KEY_UP and top != 0:
				top    += self.UP
				bottom += self.UP

			elif key == curses.KEY_DOWN and bottom < textlines:
				top    += self.DOWN
				bottom += self.DOWN

			elif key == curses.KEY_LEFT:
				self.left_right( -1 )
				self.Topbar( )

			elif key == curses.KEY_RIGHT:
				self.left_right( 1 )
				self.Topbar( )

			elif key == 10 and lastKey in (curses.KEY_LEFT, curses.KEY_RIGHT):
				self.callfunc( )

			if key == ord('q') or self.abort:
				break
			lastKey = key


	def scrollingRefresh(self):
		self.win.erase( )
		top    = self.topLineNum
		bottom = self.topLineNum + self.WIN_LINES

		for (index, line) in enumerate(self.indexList[top:bottom]):
			linenum = self.topLineNum + index
			if linenum in self.markedLineNum:
				marking = self.MARKING
			else:
				marking = self.NO_MARKING
			try:
				if index == self.highlightLineNum:
					subj, frm, to, date, msg = messageDict[ linenum+1 ]
					msg  = textwrap(text=msg,  width=self.X-36)
					self.indexWin.addstr(index, 0, line[:self.indexTextLengdth], marking | curses.A_BOLD | curses.A_STANDOUT)
					self.titleWin.addstr(0, 0, subj.rstrip()[0:self.X-40])
					self.titleWin.addstr(0, 0, date)
					for (i, msg) in enumerate(msg.split('\n')[:self.Y-8]):
						self.previewWin.addstr(i, 0, msg)
					cur_line = '%d / %d' % (linenum+1, len(messageDict.keys()))
					self.win.addstr(y-2, int((x-1)-len(cur_line)), cur_line, color_green | curses.A_BOLD)
				else:
					self.indexWin.addstr(index, 0, line[:self.indexTextLengdth], marking)
			except:
				self.win.addstr(0, 60, 'Error')
		self.Frame( )
		self.win.refresh( )


	def markLine(self):
		marklinenum = self.highlightLineNum + self.topLineNum
		if marklinenum in self.markedLineNum:
			self.markedLineNum.remove(marklinenum)
		else:
			self.markedLineNum.append(marklinenum)

	def getAllHeaders(self):
		msgCount = self.Stat( )[0]
		pb = Progressbar(msgCount, title="PyMail", message="Downloading headers...", clr1=color_red, clr2=color_green, y=y, x=x)
		loadfrom = 40
		limit    = None

		return self.downloadAllHeaders(loadfrom, limit, pb.progress)

	def getAllMessages(self):
		msgCount = self.Stat( )[0]
		pb = Progressbar(msgCount, title="PyMail", message="Downloading messages...", clr1=color_red, clr2=color_green, y=y, x=x)
		loadfrom = 40
		limit    = None
		return self.downloadAllMessages(loadfrom, limit, pb.progress)

	def loadAllHeaders(self):
		resp, headerList, headerSize = self.getAllHeaders( )
		parser = Parser( )
		headerList = [ parser.parseHeader ( header ) for header in headerList ]
		headerList = [ parser.splitAddrHeader( header.get('From', '<Unknow>')) for header in headerList ]
		self.headerLine = [hdr[:30].rstrip() for hdr in headerList]
		self.outputLineNum = len(self.headerLine)

	def loadAllMessages(self, num=None):
		resp, messageList, messageSize = self.getAllMessages( )
		parser = Parser( )
		headerList = [ parser.parseHeader( header ) for header in messageList]
		fromList   = [ parser.splitAddrHeader( header.get("From",    "<Unknow>") ) for header in headerList ]
		toList     = [ parser.splitAddrHeader( header.get("To",      "<Unknow>") ) for header in headerList ]
		subjList   = [ parser.decodeHeader   ( header.get("Subject", "<Unknow>") ) for header in headerList ]
		dateList   = [ header.get( "Date",   "<Unknow>" ) for header in headerList ]
		self.indexList = [hdr[:33].rstrip() for hdr in fromList]
		self.indexList.reverse( )
		self.outputLineNum = len(self.indexList)
		messageList = [ parser.parseMessage( message ) for message in messageList ]
		messageList = [ parser.findText( message )[1]  for message in messageList ]
		count = self.outputLineNum
		for (subj, frm, to, date, msg) in zip( subjList, fromList, toList, dateList, messageList ):
			messageDict[ count ]  = [subj, frm, to, date, msg]
			count -= 1

	def up_down(self, increment):

		nextlinenum = self.highlightLineNum + increment
		if increment == self.UP and ( self.topLineNum != 0 and self.highlightLineNum == 0 ):
			self.topLineNum += self.UP
			return
		elif increment == self.DOWN and ( self.topLineNum+self.WIN_LINES ) != self.outputLineNum and nextlinenum == self.WIN_LINES:
			self.topLineNum += self.DOWN
			return
		if increment == self.UP and ( self.topLineNum != 0 or self.highlightLineNum != 0 ):
			self.highlightLineNum = nextlinenum
		elif increment == self.DOWN and ( self.topLineNum+self.WIN_LINES)+1 != self.outputLineNum and nextlinenum != self.WIN_LINES:
			self.highlightLineNum = nextlinenum

	def left_right(self, increment):
		"""
		Control Topbar position
		"""
		if increment == self.LEFT and self.topbarFocus !=  0:
			self.topbarFocus += self.LEFT
		elif increment == self.RIGHT and self.topbarFocus != len(self.menufunc)-1:
			self.topbarFocus += self.RIGHT



	def composeWin(self):
		self.makeRectangle(self.win, self.Y+1, self.X)
		self.win.getch( )

	def Compose(self):
		self.composeWin( )


	def callfunc(self):
		funcdict= {1: 'Compose( )',  2: 'Save( )' ,   3: 'Delete( )',
				   4: 'Find( )',     5: 'Forward( )', 6: 'Reply( )',
				   7: 'Translate( )',8: 'Option( )',  9: 'Help( )' }
		eval('self.'+funcdict[self.topbarFocus+1])

	def Delete(self):
		deleMsg = None
		msgnumList = self.markedLineNum
		if not msgnumList:
			showmessage(title='Delete message', message='Please use space key to mark message line')
			return None
		else:
			if askyescancel(title='Delete message', message='Are you want delete message?'):
				for num in  msgnumList:
					deleMsg = self.delete(num)
		return deleMsg or None

	def Fine(self):
		pass

	def Forward(self):
		pass
		subj, frm, to, date, msg

	def Reply(self):
		linenum = self.topLineNum + self.hightlightLineNum + 1
		addr = messageDict[ linenum ]
		addr = Parser( ).getAddress(addr)


	def Save(self):
		savepath = askfilesave(title='Save message', message='Please input save path or use default directory')
		if savepath:
			try:
				msgnum   = self.topLineNum + self.highlightLineNum + 1
				subj, frm, to, date, msg = messageDict[msgnum]
				filename = os.path.join(savepath, frm)
				fullmsg  = 'Subject:%s\nFrom   :%s\nTo     :%s\nDate   :%s\n%s\n%s' % ( subj, frm, to, date, '-'*80, msg )
				file = open(filename, 'w', encoding='utf8').write(fullmsg)
			except:
				err  = sys.exc_info()[1]
				info = 'File name : %s\nError type: %s\n\n%s' % (err.filename, err.strerror, 'Please input again')
				showmessage(title='Save fail', message=info)
				self.Save( )

	def Translate(self):

		from translateParser import Translation
		msgnum  = self.topLineNum + self.highlightLineNum + 1
		message = messageDict.get(msgnum)
		text = Translation(message[-1])
		message[-1] = text
		self.displayMessage(msg=message)
		if self.abort:
			self.abort = False
		else:
			self.abort = True

	def Option(self):
		pass

	def Help(self):
		msg = """
Developer 〄 : Manish Marahatta(r68bux)
Email     ✉ : me@manishmarahatta.com.np
""".lstrip()
		msg = msg.split('\n')
		hight, width = self.Y-3, self.X-2

		top    = 0
		bottom = hight-2

		s = self.win.subwin(self.Y-3, self.X-2, 2, 1)
		rectangle(self.win, 1, 0, self.Y-1, self.X-1)
		self.scrollingText(textpad=s, text=msg, top=0, bottom=bottom, y=hight-1, x=width)

	def Exit(self):
		pass

	def textEdit(self):
		win   = self.win; Y, X = self.Y, self.X
		hight, width = Y-8, X-2
		subw  = curses.newwin(hight, width, 8, 1)


def rectangle(win, lines, cols, hight, width):
	try:
		win.vline(lines+1, cols,   curses.ACS_VLINE, hight - lines - 1)
		win.hline(lines,   cols+1, curses.ACS_HLINE, width - cols  - 1)
		win.hline(hight,   cols+1, curses.ACS_HLINE, width - cols  - 1)
		win.vline(lines+1, width,  curses.ACS_VLINE, hight - lines - 1)
		win.addch(lines,   cols,   curses.ACS_ULCORNER)
		win.addch(lines,   width,  curses.ACS_URCORNER)
		win.addch(hight,   cols,   curses.ACS_LLCORNER)
		win.addch(hight,   width,  curses.ACS_LRCORNER)
	except curses.error:
		pass



def keyHandler(mailbox, KeyRecord=[]):
	key = screen.getch( )
	if key in (258, 259, 260, 261): KeyRecord.append(key)
	try:
		RecentKey = KeyRecord[0]
	except IndexError:
		RecentKey = curses.KEY_DOWN
	if len(KeyRecord) == 2: KeyRecord.remove(RecentKey)
	if key == curses.KEY_UP:
		mailbox.up_down(-1)
	elif key == curses.KEY_DOWN:
		mailbox.up_down( 1 )
	elif key == curses.KEY_LEFT:
		mailbox.left_right(-1)
	elif key == curses.KEY_RIGHT:
		mailbox.left_right( 1 )
	if key == ord('\n') and RecentKey in (curses.KEY_UP, curses.KEY_DOWN):
		mailbox.displayMessage( )
	elif key == ord('\n') and RecentKey in (curses.KEY_LEFT, curses.KEY_RIGHT):
		mailbox.callfunc( )
	elif key == 32:
		mailbox.markLine( )
	elif key == 27:
		return False
	return True


def Main(stdscr):
	global screen, color_red, color_green, color_blue, color_normal, y, x
	screen  = stdscr

	screen.keypad(True)
	curses.noecho( )
	curses.cbreak( )
	y, x = screen.getmaxyx( )
	curses.start_color()
	curses.curs_set(0)
	curses.init_pair(1, curses.COLOR_RED,   0)
	curses.init_pair(2, curses.COLOR_GREEN, 0)
	curses.init_pair(3, curses.COLOR_BLUE,  0)
	curses.init_pair(4, 7, 0)
	color_red    = curses.color_pair(1)
	color_green  = curses.color_pair(2)
	color_blue   = curses.color_pair(3)
	color_normal = curses.color_pair(4)

	pymail = PyMail('Your mail server', 'Your email address', 'Your email password', 'SSL True or False')

	while True:
		pymail.scrollingRefresh( )
		pymail.Topbar( )
		keyHandler(mailbox=pymail)



if __name__ == '__main__':
	import os
	os.system('resize -s 32 115')
	curses.wrapper(Main)
