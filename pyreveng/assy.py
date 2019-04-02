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
Skeleton assembly code disassembler

Uses instree and handles canonical jumps, subroutine calls etc.

Prefix instructions are marked with mnemonic "+" and their
arguments are processed before the instruction.
"""

from . import instree, code, pil

#######################################################################

Invalid = code.Invalid

class Wrong(Exception):
	pass

class Missing(Exception):
	pass

#######################################################################

class Assy(code.Code):
	def __init__(self, pj, lo, hi, lang):
		super(Assy, self).__init__(pj, lo, hi, lang)
		self.mne = "???"
		self.oper = []
		self.pil = pil.PIL_Ins(self)

	def add_il(self, ll, ret=None):
		return self.pil.add_il(self, ll, ret)

	def pildefault(self):
		return

	def render(self, pj):
		s = self.mne + "\t"
		l = []
		for i in self.oper:
			if i is None:
				continue
			if not isinstance(i, Arg):
				print(self)
				print(self.lim)
				print(self.lang)
				print(self.mne)
				print(self.oper)
				raise Wrong("Not Arg, type '%s', str '%s'" %
				    (str(type(i)), str(i)))
			l.append(i.render(pj))
		return s + ",".join(l)

#######################################################################

class Instree_ins(Assy):
	def __init__(self, pj, lim, lang):
		lo = lim[0].adr
		hi = lim[-1].adr + len(lim[-1].words) * lang.scale
		super(Instree_ins, self).__init__(pj, lo, hi, lang)
		self.prefix = False
		self.cc = True
		self.dstadr = None
		self.lim = lim
		self.mne = lim[-1].assy[0]
		self.cache = {}
		self.verbatim = []
		self.lang = lang

	def flow_R(self, pj):
		self.add_flow(pj, "R", self.cc)

	def flow_J(self, pj):
		self.add_flow(pj, ">", True, self.dstadr)


	def flow_RC(self, pj):
		self.add_flow(pj, "R", self.cc)
		self.add_flow(pj, True, "!" + self.cc, self.hi)

	def flow_JC(self, pj):
		if self.cc == True:
			self.add_flow(pj, ">", "?", self.dstadr)
			self.add_flow(pj, True, "!?", self.hi)
		else:
			self.add_flow(pj, ">", self.cc, self.dstadr)
			self.add_flow(pj, True, "!" + self.cc, self.hi)

	def flow_C(self, pj):
		self.add_flow(pj, "C", True, self.dstadr)
		self.add_flow(pj, True, True, self.hi)

	def arg(self, pj, arg):
		if arg in self.lang.verbatim:
			self.oper.append(Arg_verbatim(pj, arg))
			return

		if arg == "-":
			return

		x = None
		if arg[0] == ">":
			try:
				x = getattr(self, "flow_" + arg[1:])
			except AttributeError:
				x = None
		if x is None:
			try:
				x = getattr(self, "assy_" + arg)
			except AttributeError:
				x = None
		if x is None:
			x = "?" + arg + "?"
			print(self.im, "ERROR: ARG <%s> not translated" % arg)
		if not isinstance(x, str):
			x = x(pj)
		if isinstance(x, str):
			x = Arg_verbatim(pj, x)
		if x is None:
			return
		if not isinstance(x, Arg):
			print(self)
			print(lim)
			print(lang)
			raise Wrong("Not Arg, type '%s', str '%s'" %
			    (str(type(x)), str(x)))
		self.oper.append(x)

	def parse(self, pj):
		if self.mne[0] == "+":
			self.prefix = True
		self.oper = list()
		for self.im in self.lim:
			i = self.im.assy
			for j in i[1].split(","):
				self.arg(pj, j)

		if len(self.flow_out) == 0:
			self.add_flow(pj, True)

	def get(self, f):
		return self.lim[-1].get(f)

	def __getitem__(self,f):
		return self.lim[-1][f]

	def __setitem__(self,f,v):
		self.lim[-1][f] = v

#######################################################################

class Instree_disass(code.Decode):
	def __init__(self, name, ins_word=8, mem_word=None, endian=None):
		super().__init__(name)
		if mem_word is None:
			mem_word = ins_word

		self.ins_word = ins_word
		self.mem_word = mem_word
		self.endian = endian
		self.scale = ins_word // mem_word

		if ins_word == mem_word:
			self.getmore = self.getmore_word
		elif ins_word == 16 and mem_word == 8 and endian == ">":
			self.getmore = self.getmore_bu16
		else:
			raise Exception("XXX: No getmore() [%d/%d/%s]" %
					(ins_word, mem_word, endian))

		self.flow_check = []
		self.verbatim = set()
		self.it = instree.InsTree(ins_word)

	def add_ins(self, desc, ins):
		assert issubclass(ins, Instree_ins)
		self.it.load_string(desc, ins)

	def getmore_word(self, pj, adr, v):
		v.append(pj.m.rd(adr + len(v)))

	def getmore_bu16(self, pj, adr, v):
		v.append(pj.m.bu16(adr + len(v) * 2))

	def decode(self, pj, adr, l=None):
		if l is None:
			l = []
		for x in self.it.find(pj, adr, getmore=self.getmore):
			assert x.handler is not None
			if l and not issubclass(x.handler, l[-1].handler):
				continue
			l.append(x)
			try:
				y = x.handler(pj, l, self)
				y.parse(pj)
			except Invalid as e:
				l.pop(-1)
				continue
			except KeyError as e:
				raise
			if y.prefix:
				try:
					y = self.decode(pj, adr + len(x.words) * self.scale, l)
				except Invalid as e:
					l.pop(-1)
					continue
				assert y is not None
				return y
				
			z = y.im.pil.pilspec
			if z is not None:
				y.add_il(z.split("\n"))
			else:
				y.pildefault()
			for i in self.flow_check:
				i(pj, y)
			return y
		raise Invalid(pj.afmt(adr) + 
		    " No matching " + self.name + " instruction")


#######################################################################

class Arg(object):
	def __init__(self, pj):
		self.pj = pj

	def render(self, pj):
		return str(self)

class Arg_verbatim(Arg):
	def __init__(self, pj, txt):
		super(Arg_verbatim, self).__init__(pj)
		self.txt = txt

	def __str__(self):
		return self.txt

class Arg_dst(Arg):
	def __init__(self, pj, dst, pfx="", sfx=""):
		super(Arg_dst, self).__init__(pj)
		self.dst = dst
		self.pfx = pfx
		self.sfx = sfx

	def __str__(self):
		l = self.pj.labels.get(self.dst)
		if l != None:
			return self.pfx + "%s" % l[0] + self.sfx
		elif self.dst is None:
			return self.pfx + "0x?" + self.sfx
		else:
			return self.pfx + "0x%x" % self.dst + self.sfx

class Arg_ref(Arg):
	def __init__(self, pj, obj):
		super(Arg_ref, self).__init__(pj)
		self.obj = obj

	def __str__(self):
		s = "(" + self.pj.render_adr(self.obj.lo) + ")"
		a = self.obj.arg_render(self.pj)
		if a != "":
			s += "=" + a
		return s

class Arg_imm(Arg):
	def __init__(self, pj, val, wid=0):
		super(Arg_imm, self).__init__(pj)
		self.val = val
		self.wid = wid
		assert wid & 3 == 0

	def __str__(self):
		s = "#0x%"
		if self.wid:
			s += "0%d" % (self.wid / 4)
		s += "x"
		return s % self.val
