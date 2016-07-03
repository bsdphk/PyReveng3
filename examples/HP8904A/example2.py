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

def func_display(pj, args):
	if args[0][:3] != "#0x":
		return
	if args[1][:3] != "#0x":
		return
	s = int(args[0][3:], 16)
	l = int(args[1][3:], 16)
	if s < pj.m.lo or s >= pj.m.hi:
		return
	i = pj.t.find_lo(s)
	print("DD %04x %02x" % (s, l), i)
	y = data.Txt(pj, s, s + l, label=False)
	y.compact = True
	args[0] = '"' + y.txt + '"'

func_handler = {
"DISPLAY":	func_display,
"0xd8a5":	func_display,
}

class Call(job.Leaf):
	def __init__(self, pj, lo, hi, dst, args):
		super(Call, self).__init__(pj, lo, hi, "call")
		pj.insert(self)
		self.dst = dst
		self.args = args
		self.compact = True
		i = func_handler.get(dst)
		if i != None:
			i(pj, args)

	def render(self, pj):
		s = "CALL\t" + self.dst + "("
		l = []
		for i in self.args:
			if i.find(",") != -1:
				l.append("(" + i + ")")
			else:
				l.append(i)
		s += ",".join(l) + ")"
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
		else:
			break

	if na == arg_bytes:
		i = pj.t.find_lo(a0)[0].render(pj).split()
		if dbg:
			print(">", arg_bytes, f, av, x)
		y = Call(pj, a, a1, i[1], av)
		return True

	print("m %04x" % a0, arg_bytes, f, av, x)
	return False

def analyse(pj):
	d = {}
	for i in pj:
		if i.tag != "mc6809":
			continue
		if i.mne != "LBSR" and i.mne != "BSR":
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
		#if i.lo == 0x472e:
		#	return

