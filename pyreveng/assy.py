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
"""

from __future__ import print_function

import instree
import code

import pyreveng

#######################################################################

class assy(code.code):
	def __init__(self, pj, lo, hi, lang):
		super(assy, self).__init__(pj, lo, hi, lang)
		self.mne = "???"
		self.oper = []

	def render(self, pj):
		s = self.mne + "\t"
		t = ""
		for i in self.oper:
			if type(i) == str:
				s += t + i
			else:
				s += t + i.render(pj)
			t = ","
		return s

#######################################################################

class instree_assy(assy):
	def __init__(self, pj, im, lang):
		lo = im.adr
		hi = im.adr + im.len
		super(instree_assy, self).__init__(pj, lo, hi, lang)
		self.cc = True
		self.dstadr = None
		self.im = im
		i = im.spec.split()
		self.mne = i[0]
		self.oper = list()
		for j in i[1].split(","):
			o = None
			if j in lang.args:
				x = lang.args[j]
				if type(x) == str:
					o = arg_verbatim(pj, x)
				else:
					o = lang.args[j](pj, self)
			elif j != "-":
				print("Ignoring argument", j, "in", lang.name, i)
			if o != None:
				self.oper.append(o)
		if len(self.flow_out) == 0:
			self.add_flow(pj, True)

#######################################################################

class instree_disass(object):
	def __init__(self, name, word_size = 8):
		self.name = name
		self.args = {
			">R":	arg_flow_return,
			">J":	arg_flow_jmp,
			">JC":	arg_flow_jmp_cond,
			">C":	arg_flow_call,
		}
		self.it = instree.instree(iword = word_size, memword=word_size)
		self.flow_check = []

	def disass(self, pj, adr):
		if pj.find(adr, self.name) != None:
			return False
		x = self.it.find(pj, adr)
		if x != None:
			y = instree_assy(pj, x, self)
			for i in self.flow_check:
				i(y)
			y.propagate(pj)
			return True
		print(self.name, "%x" % adr,
		    "disass (%02x) failed" % pj.m.rd(adr))
		return False
	

#######################################################################

class arg_dst(object):
	def __init__(self, pj, dst, pfx=""):
		self.dst = dst
		self.pfx = pfx

	def render(self, pj):
		if self.dst in pj.labels:
			return self.pfx + "%s" % pj.labels[self.dst]
		else:
			return self.pfx + "0x%x" % self.dst

class arg_verbatim(object):
	def __init__(self, pj, txt):
		self.txt = txt

	def render(self, pj):
		return self.txt

def arg_flow_return(pj, ins):
	ins.add_flow(pj, "R", ins.cc)

def arg_flow_jmp(pj, ins):
	ins.add_flow(pj, ">", True, ins.dstadr)

def arg_flow_jmp_cond(pj, ins):
	ins.add_flow(pj, ">", ins.cc, ins.dstadr)
	ins.add_flow(pj, True, "!" + ins.cc, ins.hi)

def arg_flow_call(pj, ins):
	ins.add_flow(pj, "C", True, ins.dstadr)
	ins.add_flow(pj, True, True, ins.hi)
