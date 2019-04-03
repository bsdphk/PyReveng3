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

import ctypes

from . import tree

DEFINED = (1 << 7)

class MemError(Exception):

	def __init__(self, adr, reason):
		super().__init__()
		self.adr = adr
		self.reason = reason
		self.value = ("0x%x:" % adr + str(self.reason),)

	def __str__(self):
		return repr(self.value)

class address_space():

	"""
	A vacuous address-space and base-class for actual address-spaces
	and memory types
	"""

	def __init__(self, lo, hi, name=""):
		assert lo <= hi
		self.lo = lo
		self.hi = hi
		self.name = name
		self.labels = dict()
		self.block_comments = dict()
		l = max(len("%x" % self.lo), len("%x" % (self.hi - 1)))
		self.apct = "0x%%0%dx" % l
		self.t = tree.Tree(self.lo, self.hi)
		self.comment_prefix = "; "

	def __repr__(self):
		return "<address_space %s 0x%x-0x%x>" % (
		    self.name, self.lo, self.hi
		)

	def __getitem__(self, adr):
		b = self._off(adr)
		raise MemError(adr, "Undefined")

	def __setitem__(self, adr, data):
		b = self._off(adr)
		raise MemError(adr, "Undefined")

	def _off(self, adr):
		if adr < self.lo:
			raise MemError(adr, "Address too low")
		if adr >= self.hi:
			raise MemError(adr, "Address too high")
		return adr - self.lo

	def set_label(self, adr, lbl):
		assert type(lbl) == str
		self.labels.setdefault(adr, []).append(lbl)

	def set_block_comment(self, adr, cmt):
		self.block_comments.setdefault(adr, '')
		self.block_comments[adr] += cmt + '\n'

	def gaps(self):
		ll = self.lo
		for i in self.t:
			if i.lo > ll:
				yield ll, i.lo, self
			ll = i.hi
		if self.hi > ll:
			yield ll, self.hi, self

class word_mem(address_space):

	"""
	Word memory is characteristic for a lot of the earliest computers,
	they could access exactly one word at a time, or possibly fractions
	of a word, but the instruction set did not support any "super-size"
	data types or access spanning multiple words.

	Typical examples:  Pretty much any decendant of Von Neumans early
	computers down to most of the minicomputers from DEC and DG etc.

	Largest supported word-width is 64 bits and 8 attributes.
	"""

	def __init__(self, lo, hi, bits=8, attr=0):
		assert lo < hi
		assert bits > 0
		assert bits <= 64
		assert attr >= 0
		assert attr <= 7

		super().__init__(lo, hi)

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

	def __repr__(self):
		return "<word_mem 0x%x-0x%x, @%d bits, %d attr>" % (
		    self.lo, self.hi, self.bits, self.attr)

	def __getitem__(self, adr):
		"""Read location"""
		b = self._off(adr)
		if not self.a[b] & DEFINED:
			raise MemError(adr, "Undefined")
		return self.m[b]

	def rd(self, adr):
		return self[adr]

	def __setitem__(self, adr, dat):
		"""Write location"""
		if dat & ~self.msk:
			raise MemError(adr, "Data too wide (0x%x)" % dat)
		b = self._off(adr)
		self.m[b] = self.mt(dat)
		self.a[b] |= DEFINED

	def wr(self, adr, dat):
		self[adr] = dat

	def get_attr(self, adr):
		"""Get attributes"""
		b = self._off(adr)
		return self.a[b] & self.amsk

	def set_attr(self, adr, x):
		"""Set attributes"""
		if x & ~self.amsk:
			raise MemError(adr, "Attribute too wide (0x%x)" % x)
		b = self._off(adr)
		self.a[b] |= x

	def clr_attr(self, adr, x):
		"""Clear attributes"""
		if x & ~self.amsk:
			raise MemError(adr, "Attribute too big (0x%x)" % x)
		b = self._off(adr)
		self.a[b] &= ~x

	def do_ascii(self, w):
		"""Return an ASCII representation of a value"""
		s = " |"
		b = self.bits - 8
		while b >= 0:
			if w is None:
				s += " "
			else:
				x = (w >> b) & 0xff
				if x > 32 and x < 127:
					s += "%c" % x
				else:
					s += " "
			b -= 8
		return s + "|"

class byte_mem(word_mem):

	"""
	Byte memory is characteristic for microcomputers, which
	typically had very narrow busses, 4 or 8 bits, but instructions
	for operating on wider types than the width of the bus.

	This introduces the issue of "endianess" but this is not
	really attribute of the memory, it is an attribute of the
	CPU, instruction set or interpreted code, so we provide
	both "sexes" and leave it up to everybody else to use the
	right one.
	"""

	def __init__(self, lo, hi, attr=0):
		super().__init__(lo, hi, 8, attr)
		self.ncol = 4
		self.ascii = True

	def u8(self, a):
		"""Unsigned 8-bit byte"""
		return self[a]

	def bu16(self, a):
		"""Big Endian Unsigned 16-bit half-word"""
		b = self[a] << 8
		b |= self[a + 1]
		return b

	def bu32(self, a):
		"""Big Endian Unsigned 32-bit word"""
		b = self[a] << 24
		b |= self[a + 1] << 16
		b |= self[a + 2] << 8
		b |= self[a + 3]
		return b

	def bu64(self, a):
		"""Big Endian Unsigned 64-bit double-word"""
		b = self[a] << 56
		b |= self[a + 1] << 48
		b |= self[a + 2] << 40
		b |= self[a + 3] << 32
		b |= self[a + 4] << 24
		b |= self[a + 5] << 16
		b |= self[a + 6] << 8
		b |= self[a + 7]
		return b

	def lu16(self, a):
		"""Little Endian Unsigned 16-bit half-word"""
		b = self[a]
		b |= self[a + 1] << 8
		return b

	def lu32(self, a):
		"""Little Endian Unsigned 32-bit word"""
		b = self[a]
		b |= self[a + 1] << 8
		b |= self[a + 2] << 16
		b |= self[a + 3] << 24
		return b

	def lu64(self, a):
		"""Little Endian Unsigned 64-bit double-word"""
		b = self[a]
		b |= self[a + 1] << 8
		b |= self[a + 2] << 16
		b |= self[a + 3] << 24
		b |= self[a + 4] << 32
		b |= self[a + 5] << 40
		b |= self[a + 6] << 48
		b |= self[a + 7] << 56
		return b

	def s8(self, a):
		"""Signed 8-bit byte"""
		b = self[a]
		if b & 0x80:
			b -= 256
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
			self[first] = i
			first += step

	def load_binfile(self, first, step, filename, lo=0, hi=None):
		fi = open(filename, "rb")
		d = bytearray(fi.read())
		fi.close()
		if hi:
			self.load_data(first, step, d[lo:hi])
		else:
			self.load_data(first, step, d[lo:])

def stackup(files, lo=0, prefix=""):
	"""
	Convenience function to stack a set of eproms into byte_mem.
	'files' indicate the layout desired, and each element can be
	just a filename or an iterable of filenames:

		files = (
			"singlelane",
			("highbyte", "lowbyte"),
			("topbyte", "midhibyte", "midlobyte", "lobyte"),
		)

	'prefix' is used for all filenames.

	See also:
		examples/HP3335A
		examples/HP8568A

	"""
	l = []
	hi = lo
	for r in files:
		l.append([])
		if type(r) == str:
			b = open(prefix + r, "rb").read()
			hi += len(b)
			l[-1].append(b)
		else:
			for i in r:
				b = open(prefix + i, "rb").read()
				hi += len(b)
				l[-1].append(b)
	m = byte_mem(lo, hi)
	p = lo
	for r in l:
		stride = len(r)
		ll = len(r[0])
		o = stride
		for i in r:
			o -= 1
			pp = p + o
			for j in i:
				m[pp] = j
				pp += stride
		p += stride * ll
	print(m)
	return m


if __name__ == "__main__":
	m = word_mem(0x0000, 0x1000, bits=64, attr=3)
	print(m)
	print(type(m.m), ctypes.sizeof(m.m))
	m.wr(0x100, 0x123456789)
	print("%x" % m[0x100])
	print(m.get_attr(0x100))
	print(m.get_attr(0x101))
	print(m.set_attr(0x101, 4))
	print(m.get_attr(0x101))
