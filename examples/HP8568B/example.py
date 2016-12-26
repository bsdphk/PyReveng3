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
#
# Patent
# 4,244,024  Object code listing for 'A' CPU.
#	     IO-map, display microcode
#
# 4,253,152  Looks identical to 4,244,024, different pagination
#
# 4,257,104  Looks identical to 4,253,152, different pagination
#
# 4.264,958  Refers to 4,253,152 for "computer printout"
#
# 4,649,496  Wheelgol excerpts (typeset):
#	     Appendix I:  mkrsave, nxtpk, mkpk, mkasrch, slft, srgt,
#	     		  setavoid, newmrkrs, 
#	     Appendix II: sertrcad, loadtrc, mkrtrc, mkrad, mkrspot,
#			  mkrdout, mkron, doeos, domrkr, newcmd,
#			  oldcmd, trcadrs, dostring, dosoftkey ...
# 
# 4,660,150  Wheelgol excerpts (tty):
#	     same as 4,649,496 ?
#######################################################################
# 4,244,024
#	pg 248 ln 2363 -> 0x7366
#	pg 262 ln 3700 -> 0x4fac
#	pg 272 ln 4631 -> 0x54b0
#	pg 280 ln 5392 -> 0x7e86


from __future__ import print_function

import os
from pyreveng import job, mem, listing, data, code, assy
import pyreveng.cpu.m68000 as m68000
import pyreveng.cpu.hp85662a as hp85662a

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
			data.Txt(pj, x, pfx=1, align=2)

	#######################################################################


	for a in (
		0x0e2fa,
		0x0e308,
		0x0e318,
		0x12986,
		0x12988,
		0x1298c,
		0x12990,
		0x1694e,
		0x16954,
		0x1873e,
		0x1874a,
		0x18756,
		0x18762,
	):
		y = data.Txt(pj, a, pfx=1, align=2)

	#######################################################################

	pj.set_label(0x0693c, "MSG_ADR_X_Y")
	for a in range(0x693c, 0x6a2c, 6):
		data.Const(pj, a, a+6, "0x%04x", pj.m.bu16, 2)

	#######################################################################

	pj.set_label(0x6b84, "G_CTRL")
	pj.set_label(0x6ba8, "G_CENTER")
	pj.set_label(0x6bcc, "G_MARKER")
	pj.set_label(0x6be2, "G_DSP_LINE")
	pj.set_label(0x6bf8, "G_GRATICULE")
	pj.set_label(0x6c4c, "G_HP_LOGO")
	pj.set_label(0x6c5e, "G_ACT_FUNC")

	a = 0x6b84

	dsp = hp85662a.hp85662a()
	while a < 0x6c98:
		x = pj.m.bs16(a)
		if x < 0:
			y = data.Data(pj, a, a + 2)
			y.fmt = ".DSPLOC\t0x%04x" % -x
			y.lcmt = "adr=%d" % -x
			dsp = hp85662a.hp85662a()
		else:
			y = dsp.disass(pj, a)
		a = y.hi

	#######################################################################

	pj.set_label(0x0e3be, "UNITS")
	for a in range(0x0e3be, 0x0e3d4, 2):
		data.Txt(pj, a, a + 2, label=False)

	#######################################################################

	a = 0x18c3a
	y = data.Txt(pj, a, 0x18c5f, align=2)

	#######################################################################

	fns = {}

	class tbl1(data.Data):
		def __init__(self, pj, lo):
			t = ""
			hi = lo
			while True:
				x = pj.m.rd(hi)
				if x <= 0x20 or x > 0x7e or x == 0x40:
					break
				hi += 1
			a,b,c = data.stringify(pj, lo, hi - lo)
			t += "'" + b + "',"
			while len(t) < 12:
				t += " "
			
			if hi & 1:
				hi += 1

			x = pj.m.bu16(hi + 2)
			if x < 242:
				pj.set_label(0x195c4 + x, "P_" + b)
				fns[pj.m.rd(0x195c4 + x)] = b

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
	# 0ee98  00 01 93 be
	# 0eeaa  00 01 93 da  |    |
	# 0ee8e  00 01 da ee  |    |
	#######################################################################
	# Orphans ?

	pj.todo(0x01b88, cpu.disass)
	pj.todo(0x01b8e, cpu.disass)
	pj.todo(0x01b94, cpu.disass)
	pj.todo(0x01b9a, cpu.disass)
	pj.todo(0x01b9e, cpu.disass)
	pj.todo(0x01ba2, cpu.disass)
	pj.todo(0x01ba8, cpu.disass)
	pj.todo(0x01c76, cpu.disass)
	pj.todo(0x01c82, cpu.disass)
	pj.todo(0x01c90, cpu.disass)
	pj.todo(0x01cd2, cpu.disass)
	pj.todo(0x01d14, cpu.disass)

	pj.todo(0x01578, cpu.disass)
	pj.todo(0x01594, cpu.disass)
	pj.todo(0x0171a, cpu.disass)
	pj.todo(0x01906, cpu.disass)
	pj.todo(0x02dee, cpu.disass)
	pj.todo(0x02df4, cpu.disass)
	pj.todo(0x03412, cpu.disass)
	pj.todo(0x11e74, cpu.disass)

	pj.todo(0x3292, cpu.disass)	# 0x3284

	#######################################################################
	# pat 4,244,024 pg 262 lin 3700

	pj.set_label(0x4fac, "SCANTAB")
	for a in range(0x4fac, 0x4fec, 2):
		y = data.Const(pj, a, a+2, "0x%04x", pj.m.bu16, 2)

	#######################################################################
	pj.set_label(0x193be, "HASHPTR")
	for a in range(0x193be, 0x193da, 2):
		y = data.Const(pj, a, a + 2)
		y.fmt = "%d" % pj.m.bu16(a)

	print("HASHPTR %d" % ((0x193da-0x193be)/2))

	#######################################################################

	pj.set_label(0x193da, "OLDCMDS")
	n = 0
	for a in range(0x193da, 0x194b2, 2):
		y = data.Txt(pj, a, a + 2, label=False, align=2)
		cmd = pj.m.bu16(a)
		y.lcmt += " n=%d" % n
		imm = (pj.m.rd(0x1951e + (n >> 3)) >> (n & 7)) & 1
		y.lcmt += " imm=%d" % imm
		if not imm:
			svfi = pj.m.rd(0x194b2 + n)
			y.lcmt += " svfi=%d" % svfi
			svf = pj.m.bu32(0x1952c + svfi * 2)
			y.lcmt += " svf=0x%08x" % svf
		n += 1
		
	print("OLDCMDS %d" % ((0x194b2-0x193da)/2))

	#######################################################################
	pj.set_label(0x194b2, "KEYTAB")
	for a in range(0x194b2, 0x1951e, 1):
		y = data.Const(pj, a, a + 1, fmt="0x%02x")
	print("KEYTAB %d" % ((0x1951e-0x194b2)/1))

	#######################################################################
	pj.set_label(0x1951e, "IMEDBITS")
	for a in range(0x1951e, 0x1952c, 1):
		y = data.Const(pj, a, a + 1, fmt="0x%02x")
	print("IMEDBITS %d" % ((0x1952c-0x1951e)/1))

	#######################################################################
	pj.set_label(0x1952c, "SFLGVAL")
	for a in range(0x1952c, 0x195c4, 2):
		y = data.Const(pj, a, a + 4)
		y.fmt = "0x%08x" % pj.m.bu32(a)
	print("SFLGVAL %d" % ((0x195c4-0x1952c)/2))

	#######################################################################
	pj.set_label(0x195c4, "PARMTYPE")
	for a in range(0x195c4, 0x196b6, 1):
		y = data.Const(pj, a, a + 1, fmt="0x%02x")
	print("PARMTYPE %d" % ((0x196b6-0x195c4)/1))

	#######################################################################
	#######################################################################

	pj.set_label(0x196b6, "PRCADRS")
	n = 0
	for a in range(0x196b6, 0x19826, 4):
		x = m.bu32(a)
		pj.todo(x, cpu.disass)
		data.Codeptr(pj, a, a + 4, x)
		if n in fns:
			y = fns[n]
		else:
			y = "CMD_"
		y += "(0x%02x)" % n
		pj.set_label(x, y)
		n += 1
	print("PRCADRS %d" % ((0x19826-0x196b6)/4))

	#######################################################################
	pj.set_label(0x19826, "PFXSCALE")
	for a in range(0x19826, 0x19853, 1):
		y = data.Const(pj, a, a + 1, fmt="0x%02x")
	print("PFXSCALE %d" % ((0x19853-0x19826)/1))


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
		z = data.Txt(pj, y.dstadr, pfx=1, align=2)
		y.lcmt = "'" + z.txt + "'"
	if i.dstadr in (0xe718, 0x3456, 0x6ce0):
		y = pj.t.find_hi(i.lo)
		if len(y) != 1:
			continue
		y = y[0]
		if pj.m.bu16(y.lo) != 0x203c:
			continue
		a = pj.m.bu32(y.lo + 2)
		z = data.Txt(pj, a, pfx=1, align=2)
		y.lcmt = "'" + z.txt + "'"
		if i.dstadr == 0xe718:
			w = pj.t.find_hi(y.lo)
			if len(w) != 1:
				continue
			w = w[0]
			if w.mne != "PEA.L":
				continue
			z = data.Txt(pj, w.dstadr, pfx=1, align=2)
			w.lcmt = "'" + z.txt + "'"

y = data.Const(pj, 0x693a, 0x693c, "%d")
y.fmt = "%d" % pj.m.bu16(y.lo)
pj.set_label(0x693a, "MODEL")


pj.set_label(0x01b48, "BCD_NEG8")
pj.set_label(0x01b72, "BCD_ADD8")
pj.set_label(0x01cb0, "BCD_SUB8")
pj.set_label(0x02f38, "CASE")
pj.set_label(0x0ee6a, "OLDCMD")
pj.set_label(0x17e9e, "PL_MOVE")
pj.set_label(0x17eac, "PL_LINE")
pj.set_label(0x033fc, "SHOW_CHAR")
pj.set_label(0x03412, "SHOW_SEMI")
pj.set_label(0x0341a, "SHOW_COMMA")
pj.set_label(0x03422, "SHOW_CRNL")
pj.set_label(0x03428, "SHOW_NL")
pj.set_label(0x03430, "SHOW_MINUS")
pj.set_label(0x03438, "SHOW_2CHAR")
pj.set_label(0x03498, "SHOW_INT")
pj.set_label(0x06a2c, "MSG_TXT")
pj.set_label(0x03906, "2DISPLAY")
pj.set_label(0x06d20, "SHOW_MSG")
pj.set_label(0x06ce0, "SHOW_TXT")
pj.set_label(0x06cf2, "SHOW_CRNL")
pj.set_label(0x07b4e, "FILL_DISPLAY")

pj.set_label(0xffffc030, "freqcnt_ctrl")
pj.set_label(0xffffc032, "freqcnt_msb")
pj.set_label(0xffffc034, "freqcnt_lsb")

pj.set_label(0xffffc040, "display_address")
pj.set_label(0xffffc042, "display_rd_store")
pj.set_label(0xffffc044, "display_wr_store")
pj.set_label(0xffffc048, "display_wr_off")
pj.set_label(0xffffc04a, "display_rd_scan")
pj.set_label(0xffffc04c, "display_wr_marker")
pj.set_label(0xffffc04e, "display_wr_scan")
pj.set_label(0xffffc0e1, "display_status")


code.lcmt_flows(pj)

listing.Listing(pj)
