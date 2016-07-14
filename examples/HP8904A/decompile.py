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

from __future__ import print_function

import os
from pyreveng import job, mem, listing, data, code, assy
import pyreveng.cpu.mc6809 as mc6809

class Call(code.Code):
	def __init__(self, pj, lo, hi, lang, dst, args):
		super(Call, self).__init__(pj, lo, hi, lang)
		self.dst = dst
		self.args = list(reversed(args))
		self.compact = True
		pj.insert(self)
		self.add_flow(pj, "C", True, dst, lang)

	def render(self, pj):
		s = "CALL\t" + pj.render_adr(self.dst) + "("
		l = []
		l.append('/%d/' % int(self.args[0][1:], 16))
		for i in self.args[1:]:
			if i.find(",") != -1:
				l.append("(" + i + ")")
			else:
				l.append(i)
		s += ", ".join(l) + ")"
		return s

def assemble_call(pj, a0, a1, arg_bytes):
	dbg = False
	if dbg:
		print("---- %04x" % a0, arg_bytes)
	a = a0
	f = []
	av = []
	na = 0
	while na < arg_bytes:
		if dbg:
			print("M", arg_bytes, f, av)
		i = pj.t.find_hi(a)
		if len(i) != 1:
			return

		x = i[0].render(pj).split()
		a = i[0].lo
		if dbg:
			print("X", x)
		if x[0] == "PSHS":
			f = x[1].replace("B,A", "D").split(",") + f
			av = x[1].replace("B,A", "D").split(",") + av
		elif x[0] in ("LEAX", "LEAY", "LEAU") and x[1][0] == "S":
			r = x[0][-1]
			j = f.index(r)
			f[j] = f[j].lower()
			av[j] = "#" + x[1]
			na += 2
		elif x[0] in ("LDY", "LDX", "LDD", "LDU"):
			j = f.index(x[0][-1])
			f[j] = f[j].lower()
			av[j] = x[1]
			na += 2
		elif x[0] == "CLRD":
			j = f.index("D")
			f[j] = "d"
			av[j] = "#0"
			na += 2
		elif x[0] == "TFR":
			j = x[1].split(",")
			k = f.index(j[1])
			f[k] = j[0]
			av[k] = j[0]
		elif x[0] == "CLRA":
			j = f.index("D")
			k = pj.t.find_hi(a)
			if len(k) != 1:
				return
			a = k[0].lo
			y = k[0].render(pj).split()
			if dbg:
				print("Y", y)
			if y[0] == "LDB":
				av[j] = y[1]
				na += 2
			else:
				break
		elif x[0] == "BSR" and na + 2 == arg_bytes:
			print("MX %04x" % a0, na, arg_bytes, "F", f, "AV", av, x)
			a = i[0].hi
			na += 2
		else:
			break

	if na == arg_bytes:
		j = pj.t.find_lo(a0)[0]
		i = j.render(pj).split()
		if dbg:
			print(">", arg_bytes, f, av, x)
		y = Call(pj, a, a1, j.lang, j.dstadr, av)
		return True

	print("m %04x" % a0, na, arg_bytes, f, av, x)
	return False

#######################################################################
# Setup

def setup(pj):
	pj.cc_locs = set()
	pj.analysed = set()

#######################################################################
# This derivative knows more about the compiler used.
#
# The compiler used often emits "LDD romaddress" to load the constant
# argument to PROLOGUE (probably because the size would not be known
# until later.) We turn them into IMM and .COMP for the target

class arg_E(assy.Arg_dst):
	def __init__(self, pj, ins):
		u = (ins.im.F_E1 << 8) | ins.im.F_E2
		if ins.mne[:2] == "LD" and u >= pj.m.lo and u < pj.m.hi:
			v = pj.m.bu16(u)
			ins.dstadr = v
			super(arg_E, self).__init__(pj, ins.dstadr, "#")
			pj.cc_locs.add(u)
			pj.cc_locs.add(u + 1)
		else:
			ins.dstadr = u
			super(arg_E, self).__init__(pj, ins.dstadr, "")

class mc6809a(mc6809.mc6809):
	def __init__(self):
		super(mc6809a, self).__init__(macros=True)
		self.args["E"] = arg_E

#######################################################################
#

recog0 = {
    "ROLA": {
	"ASLB": {
	    "LDX":	0,
	    "CLRA": {
	        "LDX":	1,
	    }
	}
    }
}

recog1 = {
    "BHI": {
	"CMPB": {
	    "BCS": {
		"CMPB": 2
	    }
	},
    },
    "TFR": {
	"BHI" : {
	    "CMPX": {
		"BCS" : {
		    "CMPX": 3
		}
	    }
	},
	"BGT" : {
	    "CMPX": {
		"BLT" : {
		    "CMPX": 3
		}
	    }
	}
    },
    "BLT": {
	"SUBD": {
	    "TFR": {
		"BGT": {
		    "CMPX": 4
		}
	    }
	}
    },
}

def recognize(pj, a, pat, l=None):
	if l == None:
		l = []
	x = pj.t.find_hi(a)
	if len(x) != 1:
		return False
	l.insert(0, x[0])
	i = x[0].mne
	j = pat.get(i)
	if j == None:
		l.pop(0)
		return [],False
	if type(j) == int:
		s = []
		for i in l:
			s.append(i.mne)
		# print("RECOG @0x%04x" % l[0].lo, ",".join(s))
		return l,j
	if type(j) == dict:
		return recognize(pj, x[0].lo, j, l)
	assert [],False

class switch(object):
	def __init__(self, pj, cpu, i):
		self.pj = pj
		self.cpu = cpu
		self.i = i
		self.top = i.lo
		self.state = 0
		self.tbl = None

	def attempt(self):
		l,w = recognize(self.pj, self.top, recog0)
		if type(w) != int:
			return False
		self.tbl = l[0].dstadr
		self.top = l[0].lo

		l,w = recognize(self.pj, self.top, recog1)
		if type(w) != int:
			s = []
			j = self.top
			for i in range(10):
				x = self.pj.t.find_hi(j)
				if len(x) != 1:
					break
				s.insert(0, x[0].mne)
				j = x[0].lo
			s = ",".join(s)
			return False
		if w == 2:
			lo = self.pj.m.rd(l[0].lo + 1)
			hi = self.pj.m.rd(l[2].lo + 1)
			d = l[-1].dstadr
		elif w == 3:
			lo = self.pj.m.bu16(l[0].lo + 1)
			hi = self.pj.m.bu16(l[2].lo + 1)
			d = l[-2].dstadr
		elif w == 4:
			lo = self.pj.m.bu16(l[3].lo + 1)
			hi = self.pj.m.bu16(l[0].lo + 1)
			d = l[-1].dstadr
		else:
			print("S1?? %04x" % self.top, w)
			return False
		l[-1].lcmt += "SWITCH type=%d lo=%d hi=%d\n" % (w, lo, hi)
		# print("S1 %04x" % self.top, w, lo, hi, "D", d)
		self.pj.set_label(d, "default")
		a = self.i.hi
		for i in range(lo, hi + 1):
			self.pj.cc_locs.add(a)
			self.pj.cc_locs.add(a + 1)
			u = self.pj.m.bu16(a)
			if u != d:
				self.pj.set_label(u, "case_%d" % i)
			self.i.add_flow(self.pj, ">JC", "%d" % i,
			    u, self.i.lang)
			self.i.lang.disass(self.pj, u)
			a += 2
		return True

#######################################################################
#

recog_array = {
    "LDX": {
	"LDA": {
	    "PSHS": {
		"TFR": {
		    "CLRA": {
			"LDB": {
			    "LDU": 2,
			}
		    }
	        },
		"LDY": {
		    "LDU": 2
		}
	    }
	}
    }
}

def analyse_array(pj, cpu, i):
	l,w = recognize(pj, i.lo, recog_array)
	if type(w) != int:
		i.lcmt += "ARRAYMISS\n"
		return
	d = pj.m.bu16(l[-1].lo + 1)
	u1 = pj.m.bu16(d)
	u2 = pj.m.bu16(d + 2)
	u3 = pj.m.bu16(d + 4)
	for a in range(d, d+6):
		pj.cc_locs.add(a)
	assert u1 == 1
	assert u2 == 0
	l[w].lcmt += "Array Index, stride %d\n" % u3
	a = "%s*%d" % (l[1].mne[-1],u3)
	y = Call(pj, l[w].lo, i.hi, l[w].lang, i.dstadr, ["U", a, "#0x0"])

#######################################################################
#

def analyse(pj, cpu):
	d = {}
	while True:
		again = False
		for i in pj:
			if i.tag != "mc6809":
				continue
			if i.lo in pj.analysed:
				continue
			pj.analysed.add(i.lo)
			u = pj.m.bu16(i.lo)
			if u == 0x6e9b:
				x = switch(pj, cpu, i)
				if x.attempt():
					again = True
				continue
			# continue
			if i.mne != "BSR" or i.dstadr == None:
				continue
			if i.dstadr == 0xfcea:
				analyse_array(pj, cpu, i)
				continue
			j = pj.t.find_hi(i.lo)
			if len(j) != 1:
				continue
			if pj.m.rd(j[0].lo) != 0x34:
				continue
			k = pj.t.find_lo(i.hi)
			if len(k) != 1:
				continue
			if pj.m.rd(k[0].lo) != 0x32:
				continue
			if not assemble_call(pj, i.lo, k[0].hi, pj.m.rd(k[0].lo + 1) & 0xf):
				continue
		while pj.run():
			pass
		if not again:
			break

#######################################################################
# Turn all the compiler generated constants into .COMP

def mopup(pj, cpu):
	if len(pj.cc_locs) > 0:
		l = list(pj.cc_locs)
		l.sort()
		a = l[0]
		b = l[0] + 1
		for i in l[1:]:
			if i == b:
				b += 1
				continue
			y = data.Const(pj, a, b)
			y.typ = ".COMP"
			a = i;
			b = i + 1
		y = data.Const(pj, a, b)
		y.typ = ".COMP"
