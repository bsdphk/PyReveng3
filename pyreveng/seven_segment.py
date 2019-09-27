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

from . import job, mem, data

# Default driver layout (A, B, C, D, E ,F, G, RDP, LDP)
default_drive = (1, 2, 4, 8, 16, 32, 64, 128, 0)

known = {
	# Index is A-G with canonical (ie: default_drive) values
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
	0x67:	'9',
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
for iii, jjj in known.items():
	known_rev[jjj] = iii

def lcmt(segs):
	"""
	segs = [A, B, C, D, E, F, G, RDP, LDP]
	"""
	r = "  AAA\n F   B\n F   B\n  GGG\n E   C\n E   C\nL DDD R\n"
	for x, y, z in (
		('A', 0, '-'),
		('B', 1, '|'),
		('C', 2, '|'),
		('D', 3, '-'),
		('E', 4, '|'),
		('F', 5, '|'),
		('G', 6, '-'),
		('R', 7, ' '),
		('L', 8, ' '),
	):
		r = r.replace(x, '#' if segs[y] else z)
	return r

def resolve(pj, adr, drive, inv):
	assert len(drive) == 9
	x = pj.m[adr]
	if inv:
		x ^= 255
	lst = list()
	n = 0
	for i in drive:
		n >>= 1
		if x & i:
			lst.append(True)
			n |= 0x100
		else:
			lst.append(False)
	n &= 0x7f
	k = known.get(n)
	if k is None:
		print("NB! Unknown 7seg (TBL idx: 0x%x)" % n)
	return k, lst

class digit(data.Data):
	def __init__(self, pj, adr, drive=None, inv=False, verbose=False):
		"""
		drive = [A, B, C, D, E, F, G, RDP, LDP]
		"""
		if drive is None:
			drive = default_drive
		assert len(drive) == 9
		super().__init__(pj.m, adr, adr+1, "7seg")
		pj.m.insert(self)
		k, lst = resolve(pj, adr, drive, inv)
		self.resolv = k
		s = ".7SEG"
		if k is not None:
			if len(k) == 1:
				s += ' "' + k + '"'
			else:
				s += " " + k
			if lst[7]:
				s += " + RDP"
			if lst[8]:
				s += " + LDP"
		else:
			print("NB! @0x%x: Unknown 7seg (0x%x)" %
			    (adr, pj.m[adr]), "\n" + lcmt(lst))
			verbose = True
			# s += " 0x%02x" % n
		if verbose:
			self.lcmt = lcmt(lst)
		self.rendered = s

def table(pj, lo, hi, drive=None, inv=False, verbose=False):
	"""
	drive = [A, B, C, D, E, F, G, RDP, LDP]
	"""
	if drive is None:
		drive = default_drive
	assert len(drive) == 9
	pj.add(lo, hi, "7segtable")
	t = []
	for a in range(lo, hi):
		t.append(digit(pj, a, drive, inv, verbose).resolv)
	return t

#######################################################################
# Hunt for 7segment decoding tables

def hunt(pj, lo, hi, pattern="01234567", distance=1):
	def bc(a):
		return bin(a).count("1")
	print('7-segment hunt (0x%x-0x%x) for "%s"' % (lo, hi, pattern))
	lst = list()
	f = False
	for i in pattern:
		j = known_rev.get(i)
		if j is None:
			print("cannot hunt for '%s' -- no reference" % i)
			f = True
		else:
			lst.append(bc(j))
	if f:
		return
	for a in range(lo, hi - len(lst)):
		p = True
		n = True
		y = list()
		for i, z in enumerate(lst):
			try:
				x = pj.m[a + i * distance]
			except mem.MemError:
				p = False
				n = False
				break
			y.append(x)
			if bc(x) != z:
				p = False
			if bc(x ^ 255) != z:
				n = False
			if not p and not n:
				break
		if p:
			inv = False
		elif n:
			inv = True
		else:
			continue

		drive = [255] * 8
		adr = a

		# Prune drive based on recognized pattern
		for i, z in enumerate(pattern):
			j = known_rev[z]
			yy = y[i]
			if inv:
				yy ^= 0xff
			k = 1
			m = 0
			while k < 0x80:
				if j & k:
					drive[m] &= yy
				k <<= 1
				m += 1

		# Refine and validate drive:
		#    Any zeros disqualifies
		#    Any single bits filters that bit everywhere else
		f = False
		while True:
			d = True
			for i, z in enumerate(drive):
				if z == 0:
					f = True
					break
				if bc(z) != 1:
					continue
				for j, w in enumerate(drive):
					if j != i and w & z:
						w &= ~z
						d = False
			if d:
				break

		if f:
			# Had zeros, abandon
			continue

		# We don't know which DP it might be
		drive.append(drive[-1])

		# Report
		print("\tCandidate 7seg table at 0x%x" % adr)
		if inv:
			print("\t\tInverted levels")
		print("\t\tPossible drive bits:", drive)
		s = "\t\tProbable table contents:"
		while True:
			x, y = resolve(pj, adr, drive, inv)
			if x is None:
				break
			s += " " + x
			adr += distance
		print(s)
		print("\t\tProbable table end address 0x%x" % adr)
		print("")
