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

class Assy(code.Code):
	def __init__(self, pj, lo, hi, lang):
		super(Assy, self).__init__(pj, lo, hi, lang)
		self.mne = "???"
		self.oper = []

	def render(self, pj):
		s = self.mne + "\t"
		t = ""
		for i in self.oper:
			if i == None:
				continue
			s += t
			t = ","
			if type(i) == str:
				s += i
				continue
			try:
				s += i.render(pj)
			except AttributeError:
				s += str(i)
		return s

#######################################################################

class Instree_assy(Assy):
	def __init__(self, pj, lim, lang):
		lo = lim[0].adr
		hi = lim[-1].adr + lim[-1].len
		super(Instree_assy, self).__init__(pj, lo, hi, lang)
		self.cc = True
		self.dstadr = None
		self.lim = lim
		self.mne = lim[-1].spec.split()[0]
		self.oper = list()
		for self.im in lim:
			i = self.im.spec.split()
			for j in i[1].split(","):
				if j == "-":
					continue
				x = lang.args.get(j)
				if x == None:
					print("Ignoring argument",
					    j, "in", lang.name, i)
					self.oper.append("?" + j + "?")
				elif type(x) == str:
					self.oper.append(x)
				else:
					self.oper.append(x(pj, self))
		if len(self.flow_out) == 0:
			self.add_flow(pj, True)

#######################################################################

class Instree_disass(code.Decode):
	def __init__(self, name, ins_word=8, mem_word=None, endian=None):
		super(Instree_disass, self).__init__(name)
		self.args = {
			">R":	Arg_flow_return,
			">RC":	Arg_flow_return_cond,
			">J":	Arg_flow_jmp,
			">JC":	Arg_flow_jmp_cond,
			">C":	Arg_flow_call,
		}
		if mem_word == None:
			mem_word = ins_word
		self.it = instree.instree(ins_word, mem_word, endian)
		self.flow_check = []

	def decode(self, pj, adr):
		l = []
		a = adr
		while True:
			x = self.it.find(pj, a)
			if x == None:
				break
			l.append(x)
			if x.spec[0] != "+":
				break
			a += x.len
		if len(l) == 0:
			return None
		y = Instree_assy(pj, l, self)
		for i in self.flow_check:
			i(y)
		return y


#######################################################################

class Arg(object):
	def __init__(self, pj):
		self.pj = pj

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
		elif self.dst == None:
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
