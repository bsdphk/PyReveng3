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
import pyreveng.cpu.m68000 as m68000

m = mem.byte_mem(0x0, 0x20000)
m.load_binfile(first = 0x00000, step = 0x2, filename="85680-80116.BIN")
m.load_binfile(first = 0x00001, step = 0x2, filename="85680-80115.BIN")
m.load_binfile(first = 0x10000, step = 0x2, filename="85680-80114.BIN")
m.load_binfile(first = 0x10001, step = 0x2, filename="85680-80113.BIN")

pj = job.Job(m, "HP8568B")

cpu = m68000.m68000()

post_arg = {
	0x1bc8:	1,
	0x1bcc:	1,
	0x1bd0:	1,
	0x1bdc:	1,
	0x1be0:	1,
	0x1c56:	1,
	0x1c5a:	1,
	0x1c7a:	1,
	0x1c7e:	1,
	0x1c88:	1,
	0x1c8c:	1,
	0x1ccc:	1,
	0x2218:	1,
	0x238e:	1,
	0x239a:	1,
	0x23f6:	1,
	0x2402:	1,
	0x24ac:	1,
	0x24b8:	1,
	0x25c8:	1,
	0x25fa:	1,
	0x27ee:	1,
	0x2862:	1,
	0x28c2:	1,
	0x28ce:	1,
	0x297c:	1,
	0x2982:	1,
	0x2988:	1,
	0x29ba: 1,
	0x29c6: 1,
	0x29ea: 1,
	0x29f6: 1,
	0x2a02: 1,
	0x2a0e: 1,
	0x2a34: 1,
	0x2a6e: 1,
	0x2b08: 1,
	0x2b14: 1,
}

class cx(m68000.m68000):

	def decode(self, pj, adr):
		y = super(cx, self).decode(pj, adr)
		if y == None:
			return y
		z = post_arg.get(y.dstadr)
		if z != None:
			y.hi += 2 * z
			y.flow_out.pop(-1)
			y.add_flow(pj, True)
		if y.dstadr == 0x2f38:
			data.Const(pj, y.lo - 2, y.lo)
			x = pj.m.bu16(y.lo - 2)
			for i in range(x):
				a = y.lo - 4 - 2 * i
				z = pj.m.bs16(a)
				data.Const(pj, a, a + 2)
				pj.todo(y.hi + z, self.disass)
				pj.set_label(y.hi + z, ".case_%d" % i)
				
			
			
		return y

cpu = cx()

if True:
	cpu.vectors(pj, hi = 0xc0)

	#######################################################################

	for b,e in (
		(0x06a2c, 0x06b84),
		(0x070ca, 0x070d6),
		(0x081ae, 0x081ba),
		(0x1357a, 0x1358a),
		(0x13e58, 0x13e70),
		(0x14960, 0x1497c),
		(0x14c94, 0x14cb4),
		(0x14f98, 0x14fa8),
		(0x15094, 0x150a4),
		(0x15140, 0x15150),
		(0x15e0e, 0x15e32),
		(0x172b8, 0x172c4),
	):
		for a in range(b, e, 4):
			x = m.bu32(a)
			data.Dataptr(pj, a, a + 4, x)
			data.Txt(pj, x, pfx=1)

	#######################################################################


	for a in (
		0xe2fa,
		0xe308,
		0xe318,
	):
		y = data.Txt(pj, a, pfx=1)

	#######################################################################

	a = 0x693c
	while a < 0x6a2c:
		x = pj.m.bu16(a)
		y = pj.m.bu16(a + 2)
		z = pj.m.bu16(a + 4)
		w = data.Const(pj, a, a + 6)
		w.fmt = "0x%04x, 0x%04x, 0x%04x" % (x, y, z)
		print(a, w.fmt)
		a += 6

	#######################################################################

	class tbl1(data.Data):
		def __init__(self, pj, lo):
			t = ""
			hi = lo
			while True:
				x = pj.m.rd(hi)
				if x <= 0x20 or x > 0x7e or x == 0x40:
					break
				hi += 1
			print(t, "%x" % lo, "%x" % hi)
			a,b,c = data.stringify(pj, lo, hi - lo)
			t += "'" + b + "',"
			while len(t) < 12:
				t += " "
			
			if hi & 1:
				hi += 1

			s = ""
			for x in range(3):
				t += s + "0x%04x" % pj.m.bu16(hi)
				s = ", "
				hi += 2
			super(tbl1, self).__init__(pj, lo, hi)
			self.fmt = t
			self.compact = True

	a = 0x18d24
	while a < 0x19398:
		y = tbl1(pj, a)
		a = y.hi

	#######################################################################

	data.Const(pj, 0x19856, 0x19857)

	#######################################################################

	cmds = {
		0x13572:	"DISPOSE",
		0x14f98:	"AUNITS",
		0x172b0:	"TWNDOW",
	}

	n = 0
	for a in range(0x196b6, 0x19826, 4):
		x = m.bu32(a)
		pj.todo(x, cpu.disass)
		data.Codeptr(pj, a, a + 4, x)
		y = cmds.get(x)
		if y == None:
			y = "CMD_%d" % n
		pj.set_label(x, y)
		n += 1
		
	#######################################################################
	# 0ee98  00 01 93 be
	# 0eeaa  00 01 93 da  |    |
	# 0ee8e  00 01 da ee  |    |
	#######################################################################
	# Orphans ?

	pj.todo(0x01578, cpu.disass)
	pj.todo(0x01594, cpu.disass)
	pj.todo(0x0171a, cpu.disass)
	pj.todo(0x01906, cpu.disass)
	pj.todo(0x02dee, cpu.disass)
	pj.todo(0x02df4, cpu.disass)
	pj.todo(0x11e74, cpu.disass)

	pj.todo(0x3292, cpu.disass)	# 0x3284

	#######################################################################

else: 
	y = cpu.disass(pj, 0xda1e)

	for i in y.__dict__:
		print("\t", i, y.__dict__[i])

while pj.run():
	pass

for i in pj.t:
	if i.tag != "m68000":
		continue
	if i.dstadr in (0xe4e8,):
		y = pj.t.find_hi(i.lo)
		if len(y) != 1:
			continue
		y = y[0]
		if y.mne != "PEA.L":
			continue
		z = data.Txt(pj, y.dstadr, pfx=1)
		y.lcmt = "'" + z.txt + "'"
	if i.dstadr in (0xe718, 0x3456, 0x6ce0):
		y = pj.t.find_hi(i.lo)
		if len(y) != 1:
			continue
		y = y[0]
		if pj.m.bu16(y.lo) != 0x203c:
			continue
		a = pj.m.bu32(y.lo + 2)
		z = data.Txt(pj, a, pfx=1)
		y.lcmt = "'" + z.txt + "'"
		if i.dstadr == 0xe718:
			w = pj.t.find_hi(y.lo)
			if len(w) != 1:
				continue
			w = w[0]
			if w.mne != "PEA.L":
				continue
			z = data.Txt(pj, w.dstadr, pfx=1)
			w.lcmt = "'" + z.txt + "'"

y = data.Const(pj, 0x693a, 0x693c, "%d")
y.fmt = "%d" % pj.m.bu16(y.lo)
pj.set_label(0x693a, "MODEL")


pj.set_label(0x17e9e, "PL_MOVE")
pj.set_label(0x17eac, "PL_LINE")
pj.set_label(0x0693c, "MSG_ADR_X_Y")
pj.set_label(0x06a2c, "MSG_TXT")
pj.set_label(0x03906, "2DISPLAY")
pj.set_label(0x06d20, "SHOW_MSG")
pj.set_label(0x06ce0, "SHOW_TXT")
pj.set_label(0x06cf2, "SHOW_CRNL")

pj.set_label(0xffffc044, "display_data")
pj.set_label(0xffffc0e1, "display_status")


code.lcmt_flows(pj)

listing.Listing(pj)
