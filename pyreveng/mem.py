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
Memory classes

These classes can be configured to act as memory for images to be
analysed.

In addition to the numerical value of each location, it is also
possible to associate up to seven attributes with each location.
These can be used to record structural information in the media,
for instance relocation flags, write-ability etc.

XXX: Better test-cases needed
XXX: Need resolution of who controls rendering...

"""

from __future__ import print_function

import ctypes

DEFINED = (1 << 7)

class MemError(Exception):
	def __init__(self, adr, reason):
		super(MemError, self).__init__()
		self.adr = adr
		self.reason = reason
		self.value = ("0x%x:" % adr + str(self.reason),)
	def __str__(self):
		return repr(self.value)

class address_space(object):
	"""
	A vacuous address-space and base-class for actual address-spaces
	and memory types
	"""
	def __init__(self, lo, hi, name=""):
		assert lo <= hi
		self.lo = lo
		self.hi = hi
		self.name = name

	def __repr__(self):
		return "<address_space %s 0x%x-0x%x>" % (
		    self.name, self.lo, self.hi
		)

	def __getitem__(self, a):
		a = self._off(a)
		raise MemError(a, "Undefined")

	def __setitem__(self, a, d):
		a = self._off(a)
		raise MemError(a, "Undefined")

	def _off(self, a):
		if a < self.lo:
			raise MemError(a, "Address too low")
		if a >= self.hi:
			raise MemError(a, "Address too high")
		return a - self.lo


class word_mem(address_space):
	"""
	Word memory is characteristic for a lot of the earliest computers,
	they could access exactly one word at a time, or possibly fractions
	of a word, but the instruction set did not support any "super-size"
	data types or access spanning multiple words.

	Typical examples:  Pretty much any ancestor of Von Neumans early
	computers down to most of the minicomputers from DEC and DG.

	Largest supported word-width is 64 bits.
	"""

	def __init__(self, lo, hi, bits=8, attr=0):
		assert lo < hi
		assert bits > 0
		assert bits <= 64
		assert attr >= 0
		assert attr <= 7

		super(word_mem, self).__init__(lo, hi)

		self.bits = bits
		self.fmt = "%" + "0%dx" % ((bits + 3) // 4)
		self.undef = "-" * ((bits + 3) // 4)
		self.ascii = (bits & 7) == 0
		self.lo = lo
		self.hi = hi
		self.attr = attr
		l = hi - lo

		self.msk = (1 << bits) - 1
		self.amsk = (1 << attr) - 1

		if bits <= 8:
			self.mt = ctypes.c_uint8
		elif bits <= 16:
			self.mt = ctypes.c_uint16
		elif bits <= 32:
			self.mt = ctypes.c_uint32
		else:
			self.mt = ctypes.c_uint64

		self.m = (self.mt * l)()

		self.at = ctypes.c_uint8
		self.a = (self.at * l)()

		#self.pm = ctypes.pointer(self.m[0])
		#self.pa = ctypes.pointer(self.a[0])

	def __repr__(self):
		return "<word_mem 0x%x-0x%x, @%d bits, %d attr>" % (
		    self.lo, self.hi, self.bits, self.attr)

	def __getitem__(self, a):
		"""Read location"""
		b = self._off(a)
		if not (self.a[b] & DEFINED):
			raise MemError(a, "Undefined")
		return self.m[b]

	def rd(self, a):
		return self[a]

	def __setitem__(self, a, d):
		"""Write location"""
		if (d & ~self.msk):
			raise MemError(a, "Data too big (0x%x)" % d)
		b = self._off(a)
		self.m[b] = self.mt(d)
		self.a[b] |= DEFINED

	def wr(self, a, d):
		self[a] = d

	def get_attr(self, a):
		"""Get attributes"""
		b = self._off(a)
		return self.a[b] & self.amsk

	def set_attr(self, a, x):
		"""Set attributes"""
		if (x & ~self.amsk):
			raise MemError(a, "Attribute too big (0x%x)" % x)
		b = self._off(a)
		self.a[b] |= x

	def clr_attr(self, a, x):
		"""Clear attributes"""
		if (x & ~self.amsk):
			raise MemError(a, "Attribute too big (0x%x)" % x)
		b = self._off(a)
		self.a[b] &= ~x

	def do_ascii(self, w):
		"""Return an ASCII representation of a value"""
		s = " |"
		b = self.bits - 8
		while b >= 0:
			if w == None:
				s += " "
			else:
				x = (w >> b) & 0xff
				if x > 32 and x < 127:
					s += "%c" % x
				else:
					s += " "
			b -= 8
		return s + "|"

	def render(self, pj, lo, hi):
		"""
		Render a location

		XXX: The PJ gets to render the address, but mem
		XXX: renders the value.  Make it consistent.
		"""
		l = list()
		while lo < hi:
			s = pj.afmt(lo) + " "
			try:
				w = self.rd(lo)
				s += self.fmt % w
			except MemError:
				w = None
				s += self.undef

			if self.amsk > 0x0f:
				s += " /%02x " % self.get_attr(lo)
			elif self.amsk > 0x0:
				s += " /%x " % self.get_attr(lo)

			if self.ascii:
				s += self.do_ascii(w)
			lo += 1
			l.append(s)
		return l


class byte_mem(word_mem):
	"""
	Byte memory is characteristic of microcomputers, which typically
	had very narrow busses, 4 or 8 bits, but which had instructions
	for operating on wider types than the buswidth.

	This introduces the issue of which "endianess" but this is not
	really attribute of the memory, it is an attribute of the CPU,
	instruction set or interpreted code, so we provide both "sexes"
	and leave it up to everybody else to use the right one.
	"""

	def __init__(self, lo, hi, attr=0):
		super(byte_mem, self).__init__(lo, hi, 8, attr)
		self.ncol = 4
		self.ascii = True

	def u8(self, a):
		"""Unsigned 8-bit byte"""
		return self.rd(a)

	def s8(self, a):
		"""Signed 8-bit byte"""
		b = self.rd(a)
		if b & 0x80:
			b -= 256
		return b

	def bu16(self, a):
		"""Big Endian Unsigned 16-bit half-word"""
		b = self.rd(a) << 8
		b |= self.rd(a + 1)
		return b

	def bu32(self, a):
		"""Big Endian Unsigned 32-bit word"""
		b = self.rd(a) << 24
		b |= self.rd(a + 1) << 16
		b |= self.rd(a + 2) << 8
		b |= self.rd(a + 3)
		return b

	def bu64(self, a):
		"""Big Endian Unsigned 64-bit double-word"""
		b = self.rd(a) << 56
		b |= self.rd(a + 1) << 48
		b |= self.rd(a + 2) << 40
		b |= self.rd(a + 3) << 32
		b |= self.rd(a + 4) << 24
		b |= self.rd(a + 5) << 16
		b |= self.rd(a + 6) << 8
		b |= self.rd(a + 7)
		return b

	def lu16(self, a):
		"""Little Endian Unsigned 16-bit half-word"""
		b = self.rd(a)
		b |= self.rd(a + 1) << 8
		return b

	def lu32(self, a):
		"""Little Endian Unsigned 32-bit word"""
		b = self.rd(a)
		b |= self.rd(a + 1) << 8
		b |= self.rd(a + 2) << 16
		b |= self.rd(a + 3) << 24
		return b

	def lu64(self, a):
		"""Little Endian Unsigned 64-bit double-word"""
		b = self.rd(a)
		b |= self.rd(a + 1) << 8
		b |= self.rd(a + 2) << 16
		b |= self.rd(a + 3) << 24
		b |= self.rd(a + 4) << 32
		b |= self.rd(a + 5) << 40
		b |= self.rd(a + 6) << 48
		b |= self.rd(a + 7) << 56
		return b

	def bs16(self, a):
		"""Big Endian Signed 16-bit half-word"""
		b = self.bu16(a)
		if b & 0x8000:
			b -= 0x10000
		return b

	def ls16(self, a):
		"""Little Endian Signed 16-bit half-word"""
		b = self.lu16(a)
		if b & 0x8000:
			b -= 0x10000
		return b

	def bs32(self, a):
		"""Big Endian Signed 32-bit word"""
		b = self.bu32(a)
		if b & 0x80000000:
			b -= 0x100000000
		return b

	def ls32(self, a):
		"""Little Endian Signed 32-bit word"""
		b = self.lu32(a)
		if b & 0x80000000:
			b -= 0x100000000
		return b

	def bs64(self, a):
		"""Big Endian Signed 64-bit double-word"""
		b = self.bu64(a)
		if b & 0x8000000000000000:
			b -= 0x10000000000000000
		return b

	def ls64(self, a):
		"""Little Endian Signed 64-bit double-word"""
		b = self.lu64(a)
		if b & 0x8000000000000000:
			b -= 0x10000000000000000
		return b

	def load_data(self, first, step, data):
		for i in data:
			self.wr(first, i)
			first += step

	def load_binfile(self, first, step, filename):
		fi = open(filename, "rb")
		d = bytearray(fi.read())
		fi.close()
		self.load_data(first, step, d)

	def render(self, pj, lo, hi):
		"""
		Render 'ncol' bytes per line

		XXX: ncol should be parameterized

		XXX: The PJ gets to render the address, but mem
		XXX: renders the value.  Make it consistent.
		"""
		l = list()
		while lo < hi:
			s = ""
			t = ""
			s += pj.afmt(lo) + " "
			for i in range(self.ncol):
				if lo + i < hi:
					try:
						v = self.rd(lo + i)
						s += " %02x" % v
						if v < 32 or v > 126:
							t += " "
						else:
							t += "%c" % v
					except MemError:
						s += " --"
						t += " "
				else:
					s += "   "
					t += " "
			if self.ascii:
				s += "  |" + t + "|"
			l.append(s)
			lo += self.ncol
		return l

if __name__ == "__main__":
	m = word_mem(0x0000, 0x1000, bits=64, attr=3)
	print(m)
	print(type(m.m), ctypes.sizeof(m.m))
	m.wr(0x100, 0x123456789)
	print("%x" % m.rd(0x100))
	print(m.get_attr(0x100))
	print(m.get_attr(0x101))
	print(m.set_attr(0x101, 4))
	print(m.get_attr(0x101))

