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
"""

from __future__ import print_function

def bcount(i):
	i = i - ((i >> 1) & 0x55555555)
	i = (i & 0x33333333) + ((i >> 2) & 0x33333333)
	return (((i + (i >> 4) & 0xF0F0F0F) * 0x1010101) & 0xffffffff) >> 24

class InsTreeError(Exception):
	def __init__(self, reason, diag=None):
		super(InsTreeError, self).__init__()
		self.value = reason
		self.diag = diag

	def __str__(self):
		s = "InsTree Error:\n"
		s += self.value
		if self.diag != None:
			s += "\n\t" + self.diag
		return s

#######################################################################
# Parse a "([01x] )*[01x]" string into a mask + bits

def parse_match(f):
	mask = 0
	bits = 0
	width = 0
	l = len(f)
	if l & 1 == 0:
		return None
	i = 0
	while i < l:
		mask <<= 1
		bits <<= 1
		width += 1
		if f[i] == "0":
			mask |= 1
		elif f[i] == "1":
			mask |= 1
			bits |= 1
		elif f[i] == "x":
			pass
		else:
			return None
		i += 1
		if i < l and f[i] != " ":
			return None
		i += 1
	return (width, mask, bits)

#######################################################################
# A single line from the specification

class insline(object):
	def __init__(self, line, width):
		self.line = line

		# print("\nLINE", line)
		s = line.expandtabs().split("|")
		s.pop(-1)
		self.spec = s.pop(0).rstrip()
		#print("SPEC", self.spec)

		b = 0
		l = list()
		for i in s:
			w = len(i)
			if w & 1 == 0:
				raise InsTreeError(
				    "Error: Field at bit %d has half bit:\n" % b +
				    "  %s\n" % line,
				    "  '%s'" % i)
			w = (w + 1) // 2
			if b // width != (b + w - 1) // width:
				raise InsTreeError(
				    "Error: Field at bit %d spans words:\n" % b +
				    "  %s\n" % line,
				    "  '%s'" % i)
			l.append((b, w, i))
			b += w

		if b % width != 0:
			raise InsTreeError(
			    "Error: line not an multiple of width (%d) bits.\n" +
			    "  %s") % (b, width, str(line))

		self.width = b
		self.words = b // width

		self.mask = [0] * self.words
		self.bits = [0] * self.words
		self.flds = dict()

		for b, w, i in l:
			x = parse_match(i)
			j = b // width
			o = (10 * width - (b + w)) % width
			#print("B", b, "W", w, "I", i, "J", j, "O", o, "X", x)
			if x == None:
				k = i.split()
				if len(k) != 1:
					raise InsTreeError(
					    "Error: multiple words in field: '%s'\n  %s"
					    % (i, line))
				self.flds[k[0]] = (j, o, (1 << w) - 1)
			else:
				assert x[0] == w
				self.mask[j] |= x[1] << o
				self.bits[j] |= x[2] << o
				#print("==" , "J", j, "O", o, "B", b, "X", x)


	def get_field(self, fld, words):
		if fld not in self.flds:
			raise InsTreeError("No such field '%s'\n  %s" % (fld, str(self)))
		x = self.flds[fld]
		v = (words[x[0]] >> x[1]) & x[2]
		return v

	def __repr__(self):
		s = "w%d <" % self.words
		s += self.spec
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

class insbranch(object):
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
				assert self.wildcard == None
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
			if type(y) == type(self):
				y.insert(x)
				return
			z = insbranch(self.lvl + 1)
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
			l = x.keys()
			l.sort()
			for j in l:
				y = x[j]
				if type(y) != type(self):
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

class insmatch(object):
	def __init__(self, it, il, adr, words):
		self.spec = il.spec
		self.adr = adr
		self.len = il.words * it.width // it.memwidth
		for i in il.flds:
			self.__dict__["F_" + i] = il.get_field(i, words)

	def __repr__(self):
		s = "<InsMatch"
		s += " @0x%x:" % self.adr
		s += "0x%x" % (self.adr + self.len)
		s += " " + self.spec
		for i in self.__dict__:
			if i[:2] == "F_":
				s += " | " + i + "=" + str(self.__dict__[i])
		s += ">"
		return s

class instree(object):
	def __init__(self, ins_word=8, mem_word=8, endian=None):
		self.width = ins_word
		self.memwidth = mem_word
		self.endian = endian
		assert self.width % self.memwidth == 0
		self.root = insbranch(0)
		if self.width == self.memwidth:
			self.gw = self.gw1
		elif self.width == 16 and self.memwidth == 8:
			self.gw = self.gw16
		else:
			raise InsTreeError(
			    "ins_word = %d, mem_word = %d not auto-supported" %
			    (self.width, self.memwidth))

	def load_file(self, filename):
		fi = open(filename, "r")
		for i in fi.readlines():
			i = i.strip()
			if i == "" or i[0] == "#":
				continue
			self.root.insert(insline(i, self.width))
		fi.close()

	def load_string(self, s):
		for i in s.split("\n"):
			i = i.strip()
			if i == "" or i[0] == "#":
				continue
			x = insline(i, self.width)
			self.root.insert(x)

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

	def findx(self, pj, adr, lvl, l, r):
		if len(l) <= lvl:
			b = self.gw(pj, adr, lvl)
			l.append(b)
		else:
			b = l[lvl]

		for i in r.find(b):
			if type(i) == insbranch:
				x = self.findx(pj, adr, lvl + 1, l, i)
				if x != None:
					return x
				continue
			for j in range(len(l), len(i.mask)):
				b = self.gw(pj, adr, j)
				l.append(b)
			m = True
			for j in range(lvl, len(i.mask)):
				if i.mask[j] & l[j] != i.bits[j]:
					m = False
					break
			if m:
				return i

	def find(self, pj, adr):
		l = []
		x = self.findx(pj, adr, 0, l, self.root)
		if x == None:
			return None
		return insmatch(self, x, adr, l)

if __name__ == "__main__":
	it = instree(8)
	it.load_string("""
Foo_00	|1 1 0 0| reg	| imm		|
Foo_02a	|1 0 0 0| reg	|x1		|0| imm		|
Foo_02b	|1 0 0 0| reg	|x1		|1| imm		|
Foo_04	|1 0 0 1| reg	| imm		|
Foo_03	|0 0|aaa| reg	| imm		|
Foo_01	|1 1 0 0|1 0 0 0| data		|0 0 0 0|foo	|
""")
	it.print()

	#it = instree(16)
	#it.load_file("/home/phk/Proj/PyRevEng/PyRevEng/cpus/m68000_instructions.txt")
	#it.print()

	print("-" * 72)
	it = instree(8)
	it.load_string("LJMP pgadr |1 1 0 0 1 0 0 0|0 0 1 1 0| pgno|1 0 0 0|0| ahi | alo           |")
	it.print()
	it.load_string("Lc8  bx    |1 1 0 0 1 0 0 0| bx            |")
	it.print()
	it.load_string("PGNO bx    |1 1 0 0 1 0 0 0|0 0 1 1 0| bx  |")
	it.print()
