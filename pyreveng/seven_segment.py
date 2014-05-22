#!/usr/bin/env python
#
# Copyright (c) 2012-2014 Poul-Henning Kamp <phk@phk.freebsd.dk>
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
# Render 7-segment decoding tables
#

from __future__ import print_function

from . import job, mem

default_map = (1, 2, 4, 8, 16, 32, 64, 128, 0)

known = {
	# Index is A-G with canonical (ie: default_map) values
	# DPs are handled separately
	0x00:	"blank",
	0x40:	'-',
	0x48:	'=',
	0x08:	'_',
	0x3f:	'0',
	0x06:	'1',
	0x5b:	'2',
	0x4f:	'3',
	0x66:	'4',
	0x6d:	'5',
	0x7d:	'6',
	0x07:	'7',
	0x7f:	'8',
	0x6f:	'9',
	0x77:	'A',
	0x7c:	'b',
	0x39:	'C',
	0x58:	'c',
	0x5e:	'd',
	0x79:	'E',
	0x71:	'F',
	0x3d:	'G',
	0x74:	'h',
	0x76:	'H',
	0x10:	'i',
	0x38:	'L',
	0x54:	'n',
	0x37:	'N',
	0x5c:	'o',
	0x73:	'P',
	0x50:	'r',
	0x31:	'R',
	0x78:	't',
	0x3e:	'U',
	0x1c:	'u',
	0x6e:	'Y',
}

known_rev = {}
for i, j in known.items():
	known_rev[j] = i

def lcmt(segs):
	"""
	segs = [A, B, C, D, E, F, G, RDP, LDP]
	"""
	r = ""
	if segs[0]:
		r += "  ###\n"
	else:
		r += "  ---\n"

	if segs[5]:
		s = " #"
	else:
		s = " |"
	if segs[1]:
		r += s + "   #\n"
		r += s + "   #\n"
	else:
		r += s + "   |\n"
		r += s + "   |\n"

	if segs[6]:
		r += "  ###\n"
	else:
		r += "  ---\n"

	if segs[4]:
		s = " #"
	else:
		s = " |"
	if segs[2]:
		r += s + "   #\n"
		r += s + "   #\n"
	else:
		r += s + "   |\n"
		r += s + "   |\n"

	if segs[8]:
		s = "."
	else:
		s = " "
	if segs[3]:
		s += " ### "
	else:
		s += " --- "
	if segs[7]:
		r += s + ".\n"
	else:
		r += s + "\n"
	r += " "
	return r

def resolve(pj, adr, map, inv):
	assert len(map) == 9
	x = pj.m.rd(adr)
	if inv:
		x ^= 255
	l = list()
	n = 0
	for i in map:
		n >>= 1
		if x & i:
			l.append(True)
			n |= 0x100
		else:
			l.append(False)
	n &= 0x7f
	k = known.get(n)
	if k == None:
		print("NB! Unknown 7seg (TBL idx: 0x%x)" % n)
	return k, l

class digit(job.Leaf):
	def __init__(self, pj, adr, map=None, inv=False, verbose=False):
		"""
		map = [A, B, C, D, E, F, G, RDP, LDP]
		"""
		if map == None:
			map = default_map
		assert len(map) == 9
		super(digit, self).__init__(pj, adr, adr+1, "7seg")
		k, l = resolve(pj, adr, map, inv)
		self.resolv = k
		s = ".7SEG"
		if k != None:
			if len(k) == 1:
				s += ' "' + k + '"'
			else:
				s += " " + k
			if l[7]:
				s += " + RDP"
			if l[8]:
				s += " + LDP"
		else:
			print("NB! @0x%x: Unknown 7seg (0x%x)" %
			    (adr, pj.m.rd(adr)), "\n" + lcmt(l))
			verbose = True
			# s += " 0x%02x" % n
		if verbose:
			self.lcmt = lcmt(l)
		self.rendered = s
		pj.insert(self)

def table(pj, lo, hi, map=None, inv=False, verbose=False):
	"""
	map = [A, B, C, D, E, F, G, RDP, LDP]
	"""
	if map == None:
		map = default_map
	assert len(map) == 9
	c = pj.add(lo, hi, "7segtable")
	t = []
	for a in range(lo, hi):
		t.append(digit(pj, a, map, inv, verbose).resolv)
	return t

#######################################################################
# Hunt for 7segment decoding tables

def hunt(pj, lo, hi, pattern="01234567", distance=1):
	def bc(a):
		return bin(a).count("1")
	print('7-segment hunt (0x%x-0x%x) for "%s"' % (lo, hi, pattern))
	l = list()
	f = False
	for i in pattern:
		j = known_rev.get(i)
		if j == None:
			print("cannot hunt for '%s' -- no reference" % i)
			f = True
		else:
			l.append(bc(j))
	if f:
		return
	for a in range(lo, hi - len(l)):
		p = True
		n = True
		y = list()
		for i in range(len(l)):
			try:
				x = pj.m.rd(a + i * distance)
			except mem.MemError:
				p = False
				n = False
				break
			y.append(x)
			if bc(x) != l[i]:
				p = False
			if bc(x ^ 255) != l[i]:
				n = False
			if not p and not n:
				break
		if p:
			inv = False
		elif n:
			inv = True
		else:
			continue

		map = [255] * 8
		adr = a

		# Prune map based on recognized pattern
		for i in range(len(pattern)):
			j = known_rev[pattern[i]]
			yy = y[i]
			if inv:
				yy ^= 0xff
			k = 1
			m = 0
			while k < 0x80:
				if j & k:
					map[m] &= yy
				k <<= 1
				m += 1

		# Refine and validate map:
		#    Any zeros disqualifies
		#    Any single bits filters that bit everywhere else
		f = False
		while True:
			d = True
			for i in range(len(map)):
				if map[i] == 0:
					f = True
					break
				if bc(map[i]) != 1:
					continue
				for j in range(len(map)):
					if j != i and map[j] & map[i]:
						map[j] &= ~map[i]
						d = False
			if d:
				break

		if f:
			# Had zeros, abandon
			continue

		# We don't know which DP it might be
		map.append(map[-1])

		# Report
		print("\tCandidate 7seg table at 0x%x" % adr)
		if inv:
			print("\t\tInverted levels")
		print("\t\tPossible map bits:", map)
		s = "\t\tProbable table contents:"
		while True:
			x, y = resolve(pj, adr, map, inv)
			if x == None:
				break
			s += " " + x
			adr += distance
		print(s)
		print("\t\tProbable table end address 0x%x" % adr)
		print("")
