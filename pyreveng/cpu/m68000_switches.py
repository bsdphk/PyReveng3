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
high0 +=	'0 0 0 0 1 1 0 0 1 0 0 0 0|1 1 1|'	# CMPI.L  #highest,D7
high0 +=	' hh				|'
high0 +=	' hl				|'

high1a =	' 6E		| j		|'	# BGT     L_range

high1b =	' 6E		| 00		|'	# BGT     L_range
high1b +=	' jj				|'

for i in (high1a, high1b):
	switches += high0 + i + '\n'

#######################################################################

low0 =		'+LOW L	8			|'
low0 +=		'0 0 0 0 1 1 0 0 1 0 0 0 0| dr0 |'	# CMPI.L  #lowest,D7
low0 +=		' lh				|'
low0 +=		' ll				|'

low1a =		' 6D		| j		|'	# BLT     L_range

low1b =		' 6D		| 00		|'	# BLT     L_range
low1b +=	' jj				|'

low2a =		'0 0 0 0 0 1 0 0 1 0 0 0 0| dr0 |'	# SUBI.L  #lowest,D7
low2a +=	' sh				|'
low2a +=	' sl				|'

low2b =		'0 1 0 1| sl  |1|1 0|0 0 0| dr0 |'	# SUBQ.L  #lowest,D7

low2c =		'0 1 0 1| al  |0|1 0|0 0 0| dr0 |'	# ADDQ.L  #lowest,D7

low2d =		''

for i in (low1a, low1b):
	for j in (low2a, low2b, low2c, low2d):
		switches += low0 + i + j + '\n'

#######################################################################

switches +=	'+DBL	L			|'
switches +=	'1 1 1 0 0 0 1 1 1 0 0 0 0| dr0 |'	# ASL.L   #0x1,D7
switches +=	'\n'

switches +=	'SWITCH	L,SW			|'
switches +=	'0 0 1 1| dr0 |0 0 0 1 1 1 0 1 1|'	# MOVE.W  (#.+8+D7.L),D7
switches +=	'0| dr1 |1 0 0 0 0 0 0 0 0 1 1 0|'
switches +=	'0 1 0 0 1 1 1 0 1 1 1 1 1 0 1 1|'	# JMP     (#.+4+D?.W)
switches +=	'0| dr2 |0 0 0 0|0 0 0 0|0 0 1 0|'
switches +=	'\n'

#######################################################################

high0a =	'+HIGH	W 6			|'
high0a +=	'0 0 0 0 1 1 0 0 0 1 0 0 0| dr0 |'	# CMPI.W  #highest,D?
high0a +=	' hl				|'

high0b =	'+HIGH	W 8			|'
high0b +=	'0 0 0 0 1 1 0 0 1 0 0 0 0| dr0 |'	# CMPI.L  #highest,D?
high0b +=	'0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0|'
high0b +=	' hl				|'

high1a =	' 62		| j		|'	# BHI     L_range

high1b =	' 62		| 00		|'	# BHI     L_range
high1b +=	' jj				|'

high1c =	' 6E		| j		|'	# BGT     L_range

high1d =	' 6E		| 00		|'	# BGT     L_range
high1d +=	' jj				|'


for j in (high0a, high0b):
	for i in (high1a, high1b, high1c, high1d):
		switches += j + i + '\n'

#######################################################################

low0 =		'+LOW	W 6			|'
low0 +=		'0 0 0 0 1 1 0 0 0 1 0 0 0| dr0 |'	# CMPI.W  #lowest,D?
low0 +=		' ll				|'

low1a =		' 65		| j		|'	# BCS     L_range

low1b =		' 65		| 00		|'	# BCS     L_range
low1b +=	' jj				|'

low1c =		' 6D		| j		|'	# BLT     L_range

low1d =		' 6D		| 00		|'	# BLT     L_range
low1d +=	' jj				|'

low2a =		'0 1 0 1| sl  |1|0 1|0 0 0| dr0 |'	# SUBQ.W  #lowest,D7

low2b =		' 0447				|'	# SUBI.W  #lowest,D7
low2b +=	' sl				|'

low2c =		'0 1 0 1| al  |0|0 1|0 0 0| dr0 |'	# ADDQ.W  #lowest,D7

low2d =		''

for i in (low1a, low1b, low1c, low1d):
	for j in (low2a, low2b, low2c, low2d):
		switches += low0 + i + j + '\n'

#######################################################################

switches +=	'+DBL	W	|'
switches +=	'1 1 1 0 0 0 1 1 0 1 0 0 0| dr0 |'	# ASL.W   #0x1,D?
switches +=	'\n'

switches +=	'+DBL	W	|'
switches +=	'1 1 0 1| dr0 |0|0 1 0 0 0| dr1 |'	# ADD.W	D?,D?
switches +=	'\n'

switches +=	'SWITCH W,SW 	|'
switches +=	'0 0 1 1| dr0 |0 0 0 1 1 1 0 1 1|'	# MOVE.W  (#.+8+D?.L),D?
switches +=	'0| dr1 |0 0 0 0 0 0 0 0 0 1 1 0|'
switches +=	' 4EFB				|' 	# JMP	  (#.+4+D?.W)
switches +=	'0| dr2 |0 0 0 0 0 0 0 0 0 0 1 0|'
switches +=	'\n'

switches +=	'SWITCH BARE	|'
switches +=	' 4EFB				|' 	# JMP	  (#.+4+D?.W)
switches +=	'0| dr0 |0 0 0 0 0 0 0 0 0 0 1 0|'
switches +=	'\n'

#######################################################################

class m68000_switch_ins(assy.Instree_ins):

	def __init__(self, pj, lim, lang):
		super().__init__(pj, lim, lang)
		if self.lo & 1:
			raise assy.Invalid("Odd Address")
		self.go_lo = None
		self.go_hi = None
		self.low = None
		self.high = None
		self.sub = 0
		self.add = 0
		self.reg = None
		self.nm = "SWITCH_%x" % self.lo
		self.sz = None

	def assy_W(self):
		if self.sz not in ('W', None):
			raise assy.Invalid("Inconsitent width in SWITCH")
		self.sz = 'W'
			
	def assy_L(self):
		if self.sz not in ('L', None):
			raise assy.Invalid("Inconsitent width in SWITCH")
		self.sz = 'L'

	def assy_BARE(self):

		assert self.lim[-1].assy[0] == "SWITCH"

		if len(self.lim) != 1:
			raise assy.Invalid("BARE switch with prefix")

		a = self.hi
		top = 128
		n = 0
		while True:
			d = pj.m.bs16(self.hi + n * 2)
			if d < 0:
				raise assy.Invalid("BARE switch with (too) negative offset")
			top = min(d, top)
			a += 2
			n += 1
			if n * 2 >= top:
				break
		self.low = 0
		self.high = n - 1
		self.wordtable(pj)
		raise assy.Invalid()

	def assy_SW(self):

		assert self.lim[-1].assy[0] == "SWITCH"

		# All dr%d must match
		rset = set()
		for i in self.lim:
			for j in i.flds:
				if j[:2] == "dr":
					rset.add(i[j])
					if len(rset) > 1:
						raise assy.Invalid("SWITCH dr# mismatch")
		self.mne = "SWITCH(D%d.%s)" % (rset.pop(), self.sz)

		if len(self.lim) < 3:
			raise assy.Invalid("SWITCH with insufficient limits")

		if self.lim[-2].assy[0] != "+DBL":
			raise assy.Invalid("SWITCH without +DBL")

		self.sz = set()
		for im in self.lim:

			def getfld(x):
				fl = im.get(x + 'l')
				if fl is not None:
					fh = im.get(x + 'h')
					if fh is not None:
						fl |= fh << 16
						if fl & 0x80000000:
							fl -= 0x100000000
					elif fl & 0x8000:
						fl -= 0x10000
				return fl

			def getjmp():
				j = im.get('j')
				if j is not None:
					if j & 0x80:
						j -= 0x100
					return im.adr + j + int(im.assy[2])
				j = im.get('jj')
				if j is not None:
					if j & 0x8000:
						j -= 0x10000
					return im.adr + j + int(im.assy[2])

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


		if self.low is None and self.high is not None:
			self.low = 0

		if self.low is None or self.high is None:
			print("XXX %x" % self.lo, self)
			for i in self.lim:
				print("--- %s" % str(i))
			print("LOW", self.low, "HIGH", self.high)
			raise assy.Invalid()

		self.nm = "SWITCH_%x" % self.lo
		pj.m.set_label(self.lo, self.nm)

		self.wordtable(pj)
		self.range(pj)
		# raise assy.Invalid()
		
	def wordtable(self, pj):
		pj.m.set_label(self.hi, self.nm + '_TAB')
		hh = self.hi
		for j in range(self.low, self.high + 1):
			o = pj.m.bs16(hh) + self.hi
			self.dst(pj, j, o)
			y = data.Data(pj, hh, hh + 2, fmt=self.nm + '_TAB[%d] = 0x%x' % (j, o))
			hh = y.hi

	def range(self, pj):
		if self.go_lo == self.go_hi:
			pj.m.set_label(self.go_lo, self.nm + "_DEFAULT")
			self.lang.disass(pj, self.go_lo)
			return
		if self.go_lo is not None:
			pj.m.set_label(self.go_lo, self.nm + "_LOW")
			self.lang.disass(pj, self.go_lo)
		if self.go_hi is not None:
			pj.m.set_label(self.go_hi, self.nm + "_HIGH")
			self.lang.disass(pj, self.go_hi)

	def dst(self, pj, no, dst):
		# XXX: Add flow
		self.lang.disass(pj, dst)
		pj.m.set_label(dst, self.nm + "_CASE_%d" % no)

def m68000_switches(disass):
	disass.add_ins(switches, m68000_switch_ins)

if __name__ == "__main__":

	from pyreveng import instree

	IT = instree.InsTree(16)
	IT.load_string(switches)
	IT.dump()
	
