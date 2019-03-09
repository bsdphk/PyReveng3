#!/usr/bin/env python
#
# Copyright (c) 2012-2019 Poul-Henning Kamp <phk@phk.freebsd.dk>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#

'''
Recognize Switch/case constructs
'''

from pyreveng import assy, data

switches = ''

#######################################################################

high0 =		'+HIGH L 8			|'
high0 +=	' 0C87				|'	# CMPI.L  #highest,D7
high0 +=	' hh				|'
high0 +=	' hl				|'

high1a =	' 6E		| j		|'	# BGT     L_range

high1b =	' 6E		| 00		|'	# BGT     L_range
high1b +=	' jj				|'

for i in (high1a, high1b):
	switches += high0 + i + '\n'

#######################################################################

low0 =		'+LOW L	8			|'
low0 +=		' 0C87				|'	# CMPI.L  #lowest,D7
low0 +=		' lh				|'
low0 +=		' ll				|'

low1a =		' 6D		| j		|'	# BLT     L_range

low1b =		' 6D		| 00		|'	# BLT     L_range
low1b +=	' jj				|'

low2a =		' 0487				|'	# SUBI.L  #lowest,D7
low2a +=	' sh				|'
low2a +=	' sl				|'

low2b =		'0 1 0 1| sl  |1|1 0|0 0 0|1 1 1|'	# SUBQ.L  #lowest,D7

low2c =		'0 1 0 1| al  |0|1 0|0 0 0|1 1 1|'	# ADDQ.L  #lowest,D7

low2d =		''

for i in (low1a, low1b):
	for j in (low2a, low2b, low2c, low2d):
		switches += low0 + i + j + '\n'

#######################################################################

switches +=	'SWITCH	L			|'
switches +=	' E387				|'	# ASL.L   #0x1,D7
switches +=	' 3E3B				|'	# MOVE.W  (#.+8+D7.L),D7
switches +=	' 7806				|'
switches +=	' 4EFB				|'	# JMP     (#.+4+D7.W)
switches +=	' 7002				|'
switches +=	'\n'

#######################################################################

high0 =		'+HIGH	W 6			|'
high0 +=	' 0C47				|'	# CMPI.W  #highest,D7
high0 +=	' hl				|'

high1a =	' 62		| j		|'	# BHI     L_range

high1b =	' 62		| 00		|'	# BHI     L_range
high1b +=	' jj				|'

for i in (high1a, high1b):
	switches += high0 + i + '\n'

#######################################################################

low0 =		'+LOW	W 6			|'
low0 +=		' 0C47				|'	# CMPI.W  #lowest,D7
low0 +=		' ll				|'

low1a =		' 65		| j		|'	# BCS     L_range

low1b =		' 65		| 00		|'	# BCS     L_range
low1b +=	' jj				|'

low2a =		'0 1 0 1| sl  |1|0 1|0 0 0|1 1 1|'	# SUBQ.W  #lowest,D7

low2b =		' 0447				|'	# SUBI.W  #lowest,D7
low2b +=	' sl				|'

low2c =		''

for i in (low1a, low1b):
	for j in (low2a, low2b, low2c):
		switches += low0 + i + j + '\n'

#######################################################################

switches +=	'SWITCH	W			|'
switches +=	' E347				|'	# ASL.W   #0x1,D7
switches +=	' 3E3B				|'	# MOVE.W  (#.+8+D7.L),D7
switches +=	' 7006				|'
switches +=	' 4EFB				|'	# JMP     (#.+4+D7.W)
switches +=	' 7002				|'
switches +=	'\n'

#######################################################################

class m68000_switch_ins(assy.Instree_ins):

	def __init__(self, pj, lim, lang):
		super().__init__(pj, lim, lang)
		self.go_lo = None
		self.go_hi = None
		self.low = None
		self.high = None
		self.sub = 0
		self.add = 0

		# Our prefixes are only valid if the lead up to a switch
		if self.lim[-1].assy[0][0] == "+":
			self.mne = "+"
			return
		if self.lim[-1].assy[0] != "SWITCH":
			raise assy.Invalid()

		self.sz = set()
		for im in self.lim:

			def getfld(x):
				fl = im.get(x + 'l')
				if fl is not None:
					fh = im.get(x + 'h')
					if fh is not None:
						fl |= fh << 16
				return fl

			def getjmp():
				j = im.get('j')
				if j is not None:
					if j & 0x80:
						j -= 0x100
					return self.lo + j + int(im.assy[2])
				j = im.get('jj')
				if j is not None:
					if j & 0x8000:
						j -= 0x10000
					return self.lo + j + 2 + int(im.assy[2])

			self.sz.add(im.assy[1])
			if im.assy[0] == "+LOW":
				x = getfld('l')
				if x is not None:
					self.low = x
				x = getfld('s')
				if x is not None:
					self.sub = x
				x = getfld('a')
				if x is not None:
					self.add = x
				if im.assy[1] == 'L':
					m = (1<<32) - 1
				else:
					m = (1<<16) - 1
				assert self.sub == (self.low + self.add) & m

				self.go_lo = getjmp()

			elif im.assy[0] == "+HIGH":
				x = getfld('h')
				if x is not None:
					self.high = x
				self.go_hi = getjmp()

		if self.low is None or self.high is None:
			raise assy.Invalid()

		assert len(self.sz) == 1
		self.sz = self.sz.pop()

		self.nm = "SWITCH_%x" % self.lo
		pj.set_label(self.lo, self.nm)

		self.mne = "SWITCH(D7.%s)" % self.sz
		self.wordtable(pj)
		self.range(pj)

	def wordtable(self, pj):
		pj.set_label(self.hi, self.nm + '_TAB')
		hh = self.hi
		for j in range(self.low, self.high + 1):
			o = pj.m.bs16(hh) + self.hi
			self.dst(pj, j, o)
			y = data.Data(pj, hh, hh + 2, fmt=self.nm + '_TAB[%d] = 0x%x' % (j, o))
			hh = y.hi

	def range(self, pj):

		if self.go_lo == self.go_hi:
			pj.set_label(self.go_lo, self.nm + "_DEFAULT")
			pj.todo(self.go_lo, self.lang.disass)
		else:
			pj.set_label(self.go_lo, self.nm + "_LOW")
			pj.todo(self.go_lo, self.lang.disass)
			pj.set_label(self.go_hi, self.nm + "_HIGH")
			pj.todo(self.go_hi, self.lang.disass)

	def dst(self, pj, no, dst):
		# XXX: Add flow
		pj.todo(dst, self.lang.disass)
		pj.set_label(dst, self.nm + "_CASE_%d" % no)

	def render(self, pj):
		return "SWITCH(D7.%s)" % self.sz
		txt = ""
		txt += ".LOW=%s\n" % str(self.low)
		txt += ".HIGH=%s\n" % str(self.high)
		txt += ".SZ=%s\n" % str(self.sz)
		n = 0
		for i in self.lim:
			txt += '[%d]' % n + " ".join(i.assy) + "\n"
			n += 1
		return txt

def m68000_switches(disass):
	disass.it.load_string(switches, m68000_switch_ins)
