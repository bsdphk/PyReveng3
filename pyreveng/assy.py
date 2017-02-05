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

from __future__ import print_function

from . import instree, code

#######################################################################

class Invalid(Exception):
	pass

class Wrong(Exception):
	pass

#######################################################################

class Assy(code.Code):
	def __init__(self, pj, lo, hi, lang):
		super(Assy, self).__init__(pj, lo, hi, lang)
		self.mne = "???"
		self.oper = []
		self.il = []
		self.il_c = 0

	def il_reg(self, r, d):
		if r[0] != "%":
			return r
		# XXX Problem with instructions at loc=0
		o = self.lo * 100
		if r[1:].isdigit():
			if int(r[1:]) >= 100:
				return r
			n = "%%%d" % (o + self.il_c)
			d[r] = n
			self.il_c += 1
			return n
		return r

	def add_il(self, ll, ret=None):
		if ll == None:
			return
		d = {}
		for l in ll:
			if l == None:
				continue
			if isinstance(l, str):
				f = l.split()
			else:
				f = l
				for i in f:
					assert i == i.strip()
			if len(f) == 0:
				continue
			v = []
			for i in f:
				j = d.get(i)
				if j is not None:
					v.append(j)
					continue
				j = self.il_reg(i, d)
				if j != i:
					v.append(j)
					continue
				try:
					j = getattr(self, "ilmacro_" + i)
				except AttributeError:
					v.append(i)
					continue
				# self.il.append(["/* MACRO " + i + " */"])
				k = j()
				if k is not None:
					x = self.il_reg(k, d)
					v.append(x)
			if len(v) == 0:
				continue

			try:
				j = getattr(self, "ilfunc_" + v[0])
			except AttributeError:
				self.il.append(v)
				continue
			# self.il.append(["/* FUNC " + " ".join(v) + " */" ])
			j(v[1:])
		return d.get(ret)

	def render(self, pj):
		for i in self.il:
			self.lcmt += "IL " + " ".join(i) + "\n"
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

class Instree_assy(Assy):
	def __init__(self, pj, lim, lang):
		lo = lim[0].adr
		hi = lim[-1].adr + lim[-1].len
		super(Instree_assy, self).__init__(pj, lo, hi, lang)
		self.prefix = False
		self.cc = True
		self.dstadr = None
		self.lim = lim
		self.mne = lim[-1].assy[0]
		self.cache = {}
		if self.mne[0] == "+":
			self.prefix = True
		self.oper = list()
		for self.im in lim:
			i = self.im.assy
			for j in i[1].split(","):
				try:
					x = getattr(self, "assy_" + j)
					typ=1
				except AttributeError:
					x = None
				if x is None:
					x = lang.args.get(j)
					typ=2
				if x is None:
					if j == "-":
						continue
					x = "?" + j + "?"
					print("ERROR: ARG <%s> not translated" % j)
				if not isinstance(x, str):
					if typ == 1:
						x = x(pj)
					else:
						x = x(pj, self)
				if isinstance(x, str):
					x = Arg_verbatim(pj, x)
				if x is None:
					continue
				if not isinstance(x, Arg):
					print(self)
					print(lim)
					print(lang)
					raise Wrong("Not Arg, type '%s', str '%s'" %
					    (str(type(x)), str(x)))
				self.oper.append(x)

		if len(self.flow_out) == 0:
			self.add_flow(pj, True)

	def __getitem__(self,f):
		return self.lim[-1][f]

	def __setitem__(self,f,v):
		self.lim[-1][f] = v

#######################################################################

class Instree_disass(code.Decode):
	def __init__(self, name, ins_word=8, mem_word=None, endian=None):
		super(Instree_disass, self).__init__(name)
		self.args = {
			"-":	None,
			">R":	Arg_flow_return,
			">RC":	Arg_flow_return_cond,
			">J":	Arg_flow_jmp,
			">JC":	Arg_flow_jmp_cond,
			">C":	Arg_flow_call,
		}
		if mem_word is None:
			mem_word = ins_word
		self.it = instree.Instree(ins_word, mem_word, endian)
		self.flow_check = []
		self.myleaf = Instree_assy
		self.il = False

	def decode(self, pj, adr, l=None):
		if l is None:
			l = []
		y = None
		for x in self.it.find(pj, adr):
			l.append(x)
			try:
				y = self.myleaf(pj, l, self)
			except Invalid:
				y = None
				l.pop(-1)
				continue
			if not y.prefix:
				break
			y = self.decode(pj, adr + x.len, l)
			if y != None:
				break
			l.pop(-1)
		if y != None:
			if self.il:
				x = y.im.il.ilspec
				if x is not None:
					y.add_il(x.split("\n"))
				else:
					y.add_il(["pyreveng.noidea ( )"])
			for i in self.flow_check:
				i(pj, y)
		return y


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
			return self.pfx + "%s" % l + self.sfx
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

def Arg_flow_return(pj, ins):
	ins.add_flow(pj, "R", ins.cc)

def Arg_flow_return_cond(pj, ins):
	ins.add_flow(pj, "R", ins.cc)
	ins.add_flow(pj, True, "!" + ins.cc, ins.hi)

def Arg_flow_jmp(pj, ins):
	ins.add_flow(pj, ">", True, ins.dstadr)

def Arg_flow_jmp_cond(pj, ins):
	if ins.cc == True:
		ins.add_flow(pj, ">", "?", ins.dstadr)
		ins.add_flow(pj, ">", "!?", ins.hi)
	else:
		ins.add_flow(pj, ">", ins.cc, ins.dstadr)
		ins.add_flow(pj, True, "!" + ins.cc, ins.hi)

def Arg_flow_call(pj, ins):
	ins.add_flow(pj, "C", True, ins.dstadr)
	ins.add_flow(pj, True, True, ins.hi)
