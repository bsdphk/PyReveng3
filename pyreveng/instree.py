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

"""
Instree -- A class for disassembling

This class turns a textual description close to what is typically used
for documenting CPUs into a skeleton disassembler.

	instree = * (
		(assypart (wordmap/bitmap) [details]) \
		('#' comment NL)
	)

	assypart = * (nonspacenonpipe WSP)

	delim	= ' ' / '|'

	wordmap = '|' *(delim (hex|field)) '|'

	bitmap = '|' bit *(delim (field|bit)) '|'

	bit = '?' / '0' / '1'

	hex = 2* ( bit / '2' / '3' / ... 'd' / 'e' / 'f' )

	details = '{' NL anything_really NL '}' NL

XXX: The details are currently unused.

XXX: wordmap has yet to be implemented

"""

from __future__ import print_function

class UsageTrouble(Exception):
	pass

class SyntaxTrouble(Exception):
	def __init__(self, last, msg):
		j = " ".join(last.split())
		super(SyntaxTrouble, self).__init__(
		    "\nAfter '%s':\n    %s" % (j, msg))

def bcount(i):
	i = i - ((i >> 1) & 0x55555555)
	i = (i & 0x33333333) + ((i >> 2) & 0x33333333)
	return (((i + (i >> 4) & 0xF0F0F0F) * 0x1010101) & 0xffffffff) >> 24

#######################################################################
# Parse a "([01x] )*[01x]" string into a mask + bits

def parse_match(fmt):
	mask = 0
	bits = 0
	width = 0
	fl = len(fmt)
	if fl & 1 == 0:
		return None
	i = 0
	while i < fl:
		mask <<= 1
		bits <<= 1
		width += 1
		if fmt[i] == "0":
			mask |= 1
		elif fmt[i] == "1":
			mask |= 1
			bits |= 1
		elif fmt[i] == "x":
			pass
		else:
			return None
		i += 1
		if i < fl and fmt[i] != " ":
			return None
		i += 1
	return (width, mask, bits)

#######################################################################
# A single entry from the specification

class Insline(object):
	def __init__(self, width, assy, bits, details=None):
		self.assy = assy.split()
		self.bits = bits
		self.details = details

		s = bits.split("|")
		s.pop(0)
		s.pop(-1)

		b = 0
		f = list()
		for i in s:
			w = len(i)
			if w & 1 == 0:
				raise SyntaxTrouble(assy,
				    "Field from bit %d has a half bit:\n" % b +
				    "\t%s\n" % bits +
				    "\t " + ("  " * b) + "^n")
			w = (w + 1) // 2
			if b // width != (b + w - 1) // width:
				raise SyntaxTrouble(assy,
				    "Field from bit %d spans words:\n" % b +
				    "\t%s\n" % bits +
				    "\t " + ("  " * b) + "^n")
			f.append((b, w, i))
			b += w

		if b % width != 0:
			raise SyntaxTrouble(assy,
			    "Missing bits to fill wordsize\n" +
			    "\t%s\n" % bits +
			    "\t " + ("  " * b) + "^n")

		self.width = b
		self.words = b // width

		self.mask = [0] * self.words
		self.bits = [0] * self.words
		self.flds = dict()

		for b, w, i in f:
			x = parse_match(i)
			j = b // width
			o = (10 * width - (b + w)) % width
			#print("B", b, "W", w, "I", i, "J", j, "O", o, "X", x)
			if x is None:
				k = i.split()
				if len(k) != 1:
					raise SyntaxTrouble(assy,
					    "Multiple words in this field:\n" +
					    "\t|" + i + "|")
				self.flds[k[0]] = (j, o, (1 << w) - 1)
			else:
				assert x[0] == w
				self.mask[j] |= x[1] << o
				self.bits[j] |= x[2] << o
				#print("==" , "J", j, "O", o, "B", b, "X", x)


	def get_field(self, fld, words):
		if fld not in self.flds:
			raise UsageTrouble(
			   "In %s:\n" % self.assy +
			   "    No field '%s'\n" % fld)
		x = self.flds[fld]
		v = (words[x[0]] >> x[1]) & x[2]
		return v

	def __repr__(self):
		s = "w%d <" % self.words
		s += " ".join(self.assy)
		s += "> <"
		t = ""
		for i in range(len(self.mask)):
			s += t + "%02x:%02x" % (self.mask[i], self.bits[i])
			t = ", "
		s += "> <"
		t = ""
		for i in self.flds:
			j = self.flds[i]
			s += t + i
			s += "@%d.%d:%x" % (j[0], j[1], j[2])
			t = ", "
		s += ">"
		return s

#######################################################################
#  Branch-point

class Insbranch(object):
	def __init__(self, lvl):
		self.lvl = lvl
		self.t = list()
		self.mask = 0
		self.wildcard = None

	def insert(self, x):
		#print("?  ", self.lvl, "%02x" % self.mask, x)
		if len(x.mask) == self.lvl:
			if self.wildcard != None:
				print("Colliding wildcards:")
				print("\t" + str(self.wildcard))
				print("\t" + str(x))
				assert self.wildcard is None
			self.wildcard = x
			return
		xm = x.mask[self.lvl]
		xb = x.bits[self.lvl]
		for i, d in self.t:
			if i != xm:
				continue
			if xb not in d:
				d[xb] = x
				return
			y = d[xb]
			if isinstance(y, Insbranch):
				y.insert(x)
				return
			z = Insbranch(self.lvl + 1)
			z.insert(x)
			z.insert(y)
			d[xb] = z
			return
		d = dict()
		d[xb] = x
		self.t.append((xm, d))
		#print("T", self.t)
		self.t.sort(key=lambda x: -bcount(x[0]))
		return

	def print(self, fmt="%x", pfx=""):
		print(pfx, "[%d]" % self.lvl)
		for i, x in self.t:
			print(pfx, "    ", "&" + fmt % i)
			a = x.keys()
			a.sort()
			for j in a:
				y = x[j]
				if isinstance(y, Insline):
					print(pfx, "      ", "=" + fmt % j, y)
				else:
					print(pfx, "      ", "=" + fmt % j, ":")
					y.print(fmt, pfx + "        ")
		if self.wildcard != None:
			print(pfx, "    ", "*", self.wildcard)

	def __repr__(self):
		return "<Branch %d>" % self.lvl

	def find(self, v):
		for i, d in self.t:
			x = v & i
			if x in d:
				yield d[x]
		if self.wildcard != None:
			yield self.wildcard


#######################################################################
#

class Insmatch(object):
	def __init__(self, up, il, adr, words):
		self.assy = il.assy
		self.adr = adr
		self.len = il.words * up.width // up.memwidth
		for i in il.flds:
			self.__dict__["F_" + i] = il.get_field(i, words)

	def __repr__(self):
		s = "<InsMatch"
		s += " @0x%x:" % self.adr
		s += "0x%x" % (self.adr + self.len)
		s += " " + " ".join(self.assy)
		for i in self.__dict__:
			if i[:2] == "F_":
				s += " | " + i + "=" + str(self.__dict__[i])
		s += ">"
		return s

#######################################################################

class Instree(object):
	def __init__(self, ins_word=8, mem_word=8, endian=None):
		self.width = ins_word
		self.memwidth = mem_word
		self.endian = endian
		assert self.width % self.memwidth == 0
		self.root = Insbranch(0)
		if self.width == self.memwidth:
			self.gw = self.gw1
		elif self.width == 16 and self.memwidth == 8:
			self.gw = self.gw16
		else:
			raise UsageTrouble(
			    "ins_word = %d, mem_word = %d not auto-supported" %
			    (self.width, self.memwidth))

	def load_string(self, s):
		i = 0
		banned = False
		s = s.expandtabs()
		last = ''
		while i < len(s):

			# Skip whitespace
			if s[i] in (' ', '\t'):
				i += 1
				continue

			# Skip comments to NL
			if s[i] == '#':
				j = s.find('\n', i)
				if j == -1:
					break
				i = j + 1
				banned = False
				continue

			# Skip NL
			if s[i] in ('\n',):
				i += 1
				banned = False
				continue

			# }-lines cannot contain anything but comments
			if banned:
				raise SyntaxTrouble(last,
				    "}-line can only contain comments")

			# Find the assy part
			j = s.find('|', i)
			if j == -1:
				raise SyntaxTrouble(last,
				    "no '|' on this line")
			last = assy = s[i:j].strip()
			i = j
			j = s.find('\n', i)
			if j == -1:
				j = len(s)

			# find the map part
			bm = s[i:j]
			i = j
			j = bm.rfind('{')
			if j == -1:
				self.root.insert(Insline(self.width, assy, bm))
				continue

			# Isolate tail-part
			tail = bm[j+1:]
			bm = bm[:j]
			if tail.strip() != "":
				raise SyntaxTrouble(last, "junk after '{'")
			j = s.find('\n}', i)
			if j == -1:
				raise SyntaxTrouble(last, "no }-line found")
			tail = s[i:j]
			i = j + 2
			banned = True

			self.root.insert(Insline(self.width, assy, bm, tail))

		assert i == len(s)

	def load_file(self, filename):
		self.load_string(open(filename).read())

	def print(self):
		m = "%0" + "%dx" % ((self.width + 3) // 4)
		self.root.print(m)

	def gw1(self, pj, adr, n):
		return pj.m.rd(adr + n)

	def gw16(self, pj, adr, n):
		if self.endian == ">":
			return pj.m.bu16(adr + n * 2)
		else:
			return pj.m.lu16(adr + n * 2)

	def dive(self, pj, adr, lvl, v, r):
		if len(v) <= lvl:
			b = self.gw(pj, adr, lvl)
			v.append(b)
		else:
			b = v[lvl]

		for i in r.find(b):
			if isinstance(i, Insbranch):
				for x in self.dive(pj, adr, lvl + 1, v, i):
					yield x
				continue
			for j in range(len(v), len(i.mask)):
				b = self.gw(pj, adr, j)
				v.append(b)
			m = True
			for j in range(lvl, len(i.mask)):
				if i.mask[j] & v[j] != i.bits[j]:
					m = False
					break
			if m:
				yield i

	def find(self, pj, adr):
		a = []
		for x in self.dive(pj, adr, 0, a, self.root):
			yield Insmatch(self, x, adr, a)

#######################################################################

if __name__ == "__main__":

	it = Instree(8)
	it.load_string("""

	# This is a comment line
Foo_00	|1 1 0 0| reg	| imm		|
Foo_02a	|1 0 0 0| reg	|x1		|0| imm		|
Foo_02b	|1 0 0 0| reg	|x1		|1| imm		|
Foo_04	|1 0 0 1| reg	| imm		| {
blabla
} # Comment
Foo_03	|0 0|aaa| reg	| imm		| {
}
Foo_01	|1 1 0 0|1 0 0 1| data		|0 0 0 0|foo	| {
}
Foo   |0 1 0 1 0 1 0 1|1 1 1 1 1 1 1 1|
#Foo_05	| ca | data		|0 0 0 0|foo	|
""")
	it.print()
