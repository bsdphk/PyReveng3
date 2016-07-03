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

from __future__ import print_function

from . import job

#######################################################################

class Data(job.Leaf):
	def __init__(self, pj, lo, hi, t="data"):
		super(Data, self).__init__(pj, lo, hi, t)
		pj.insert(self)
		self.fmt = None

	def render(self, pj):
		if self.fmt == None:
			return "<Data %x-%x %s>" % (self.lo, self.hi, self.tag)
		return self.fmt

class Const(Data):
	def __init__(self, pj, lo, hi, fmt = None):
		super(Const, self).__init__(pj, lo, hi, "const")
		if fmt == None:
			fmt = "0x%x"
		l = []
		for a in range(lo, hi):
			l.append(fmt % pj.m.rd(a))
		self.fmt = ",".join(l)
		self.typ = ".CONST"
		self.val = None
		self.compact = True

	def render(self, pj):
		return self.typ + "\t" + self.fmt

class Codeptr(Data):
	def __init__(self, pj, lo, hi, dst):
		super(Codeptr, self).__init__(pj, lo, hi, "codeptr")
		self.dst = dst

	def render(self, pj):
		return ".CODE\t" + pj.render_adr(self.dst)

	def arg_render(self, pj):
		return pj.render_adr(self.dst)

class Dataptr(Data):
	def __init__(self, pj, lo, hi, dst):
		super(Dataptr, self).__init__(pj, lo, hi, "dataptr")
		self.dst = dst

	def render(self, pj):
		return ".PTR\t" + pj.render_adr(self.dst)

class Txt(Data):
	def __init__(self, pj, lo, hi=None, label=True):
		s = ""
		a = lo
		while True:
			if hi != None and a == hi:
				break
			x = pj.m.rd(a)
			a += 1
			if x >= 32 and x < 127:
				s += "%c" % x
			elif x == 10:
				s += "\\n"
			elif x == 13:
				s += "\\r"
			else:
				s += "\\x%02x" % x
			if hi == None and x == 0:
				break
		if hi == None:
			hi = a

		super(Txt, self).__init__(pj, lo, hi, "txt")
		self.txt = s
		self.fmt = "'" + s + "'"
		t = "t_"
		j = 0
		while j < len(s):
			i = s[j]
			if s[j:j+2] == "\\r":
				t += "CR"
				j += 1
			elif s[j:j+2] == "\\n":
				t += "NL"
				j += 1
			elif i.isalpha() or i.isdigit():
				t += i
			elif i.isspace() and (len(t) == 0 or t[-1] != "_"):
				t += "_"
			if len(t) > 8:
				break
			j += 1
		if label:
			pj.set_label(lo, t)

	def render(self, pj):
		return ".TXT\t'" + self.txt + "'"

	def arg_render(self, pj):
		return "'" + self.txt + "'"

