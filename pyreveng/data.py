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
Data of various sorts
"""

import struct

from . import job, leaf


#######################################################################

class Data(leaf.Leaf):
	def __init__(self, asp, lo, hi, t="data", fmt=None):
		super().__init__(lo, hi, t)
		asp.insert(self)
		self.fmt = fmt

	def render(self):
		if self.rendered:
			return self.rendered
		if self.fmt:
			return self.fmt
		return "<Data %x-%x %s>" % (self.lo, self.hi, self.tag)

class Const(Data):
	def __init__(self, asp, lo, hi, fmt=None, func=None, size=1):
		super().__init__(asp, lo, hi, "const")
		if func is None:
			func = asp.__getitem__
		if fmt is None:
			fmt = "0x%x"
		v = []
		for a in range(lo, hi, size):
			v.append(fmt % func(a))
		self.fmt = ",".join(v)
		self.typ = ".CONST"
		self.val = None
		self.compact = True

	def render(self):
		return self.typ + "\t" + self.fmt

class Pstruct(Data):
	''' Uses python struct.* to untangle data '''
	def __init__(self, asp, lo, spec, fmt=None, typ=".PSTRUCT"):
		bcnt = struct.calcsize(spec)
		super().__init__(asp, lo, lo + bcnt, "const")
		self.data = struct.unpack(spec, asp.bytearray(lo, bcnt))
		self.spec = spec
		self.fmt = fmt
		self.typ = typ

	def render(self):
		if self.fmt is not None:
			return self.typ + "\t" + self.fmt % self.data
		return self.typ + "\t" + self.spec + " = " + str(self.data)

class Codeptr(Data):
	def __init__(self, asp, lo, hi, dst):
		super().__init__(asp, lo, hi, "codeptr")
		self.dst = dst

	def render(self):
		return ".CODE\t" + self.aspace.adr(self.dst)

	def arg_render(self):
		return self.aspace.adr(self.dst)

class Dataptr(Data):
	def __init__(self, asp, lo, hi, dst):
		super().__init__(asp, lo, hi, "dataptr")
		self.dst = dst

	def render(self):
		return ".PTR\t" + self.aspace.adr(self.dst)

def stringify(asp, lo, length=None, term=None):
	if term is None:
		term = (0,)
	s = ""
	v = ""
	while True:
		x = asp[lo]
		lo += 1
		if length is None and x in term:
			return lo, s, v
		if x > 32 and x < 127:
			s += "%c" % x
			v += "%c" % x
		elif x == 32:
			s += " "
		elif x == 10:
			s += "\\n"
			v += "NL"
		elif x == 13:
			s += "\\r"
			v += "CR"
		else:
			s += "\\x%02x" % x
			v += "%%%02x" % x
		if length is not None:
			length -= 1
			if length == 0:
				return lo, s, v

class Txt(Data):
	def __init__(self, asp, lo, hi=None,
	    label=True, term=None, pfx=None, align=1, splitnl=False):
		self.splitnl = splitnl
		self.pre = ""
		if pfx == 1:
			x = asp[lo]
			self.pre = '%d,' % x
			hi, s, v = stringify(asp, lo + 1, length=x)
			while hi % align:
				hi += 1
		elif pfx is not None:
			raise Exception("unknown pfx")
		elif hi is None:
			hi, s, v = stringify(asp, lo, term=term)
			while hi % align:
				hi += 1
		else:
			hi, s, v = stringify(asp, lo, hi - lo, term=term)

		super().__init__(asp, lo, hi, "txt")
		self.txt = s
		self.fmt = "'" + s + "'"
		if label:
			asp.set_label(lo, "t_" + v.strip())
		self.compact = True

	def render(self):
		if not self.splitnl:
			return ".TXT\t" + self.pre + "'" + self.txt + "'"

		l = self.txt.split('\\n')
		if len(l) == 1:
			return ".TXT\t" + self.pre + "'" + self.txt + "'"

		txt = ''
		p = self.pre

		for i in l[:-1]:
			txt += '.TXT\t' + p + "'" + i + "\\n'\n"
			p = ''
		if l[-1]:
			txt += '.TXT\t' + p + "'" + l[-1] + "'"
		return txt

	def arg_render(self):
		return "'" + self.txt + "'"
