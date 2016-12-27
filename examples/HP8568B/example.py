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

keyboard = (
	# Row, Column, Text
	( 0, 0, "HZ_UV_USEC"),
	( 0, 3, "MHZ_DBM_SEC"),
	( 0, 5, "BACK_SPACE"),
	( 0, 6, "KHZ_MV_MSEC"),

	( 1, 0, "SAVE"),
	( 1, 1, "RECALL"),
	( 1, 2, "HOLD"),
	( 1, 4, "0_1_5_GHZ"),
	( 1, 6, "POINT"),
	( 1, 7, "GHZ_DBM_DB"),

	( 2, 0, "DIG_0"),
	( 2, 1, "DIG_1"),
	( 2, 2, "DIG_2"),
	( 2, 3, "DIG_3"),
	( 2, 4, "DIG_4"),
	( 2, 5, "DIG_5"),
	( 2, 6, "DIG_6"),
	( 2, 7, "DIG_7"),

	( 3, 0, "DIG_8"),
	( 3, 1, "DIG_9"),
	( 3, 4, "INPUT_1"),
	( 3, 5, "FREQ_COUNT"),
	( 3, 6, "INPUT_1"),

	( 4, 1, "AUTO_RES_BW"),
	( 4, 2, "AUTO_VIDEO_BW"),
	( 4, 3, "AUTO_SWEEP_TIME"),
	( 4, 4, "AUTO_ATTEN"),
	( 4, 5, "AUTO_CF_STEP"),
	( 4, 6, "RES_BW"),
	( 4, 7, "VIDEO_BW"),

	( 5, 0, "SWEEP_TIME"),
	( 5, 1, "ATTEN"),
	( 5, 2, "CF_STEP"),
	( 5, 3, "PEAK_SEARCH"),
	( 5, 4, "MARKER_OFF"),
	( 5, 5, "MARKER_NORMAL"),
	( 5, 6, "MARKER_CF"),
	( 5, 7, "MARKER_DELTA"),

	( 6, 0, "ZOOM"),
	( 6, 1, "MKR_DELTA_STP_SIZE"),
	( 6, 2, "MKR_REF_LVL"),
	( 6, 3, "SIGNAL_TRACK"),
	( 6, 4, "DOWN"),
	( 6, 5, "UP"),
	( 6, 6, "CENTER_FREQ"),
	( 6, 7, "FREQ_SPAN"),

	( 7, 0, "START_FREQ"),
	( 7, 1, "STOP_FREQ"),
	( 7, 2, "REF_LEVEL"),

	( 8, 0, "NORMAL"),
	( 8, 1, "CLEAR_A"),
	( 8, 2, "MAX_A"),
	( 8, 3, "OFF_A_B"),
	( 8, 4, "VIEW_A"),
	( 8, 5, "BLANK_A"),
	( 8, 6, "A_B"),
	( 8, 7, "CLEAR_B"),

	( 9, 0, "MAX_B"),
	( 9, 1, "A_EX_B"),
	( 9, 2, "VIEW_B"),
	( 9, 3, "BLANK_B"),
	( 9, 4, "B-DL-B"),
	( 9, 5, "LINE_OFF"),
	( 9, 6, "LINE_ENTER"),
	( 9, 7, "THRSH_OFF"),

	( 10, 0, "THRSH_ENTER"),
	( 10, 1, "ENTER_DB"),
	( 10, 2, "LIN"),
	( 10, 3, "SHIFT"),
	( 10, 4, "CONT"),
	( 10, 5, "SINGLE"),
	( 10, 6, "TRIG_FREE_RUN"),
	( 10, 7, "TRIG_LINE"),

	( 11, 0, "TRIG_EXT"),
	( 11, 1, "TRIG_VIDEO"),
	( 11, 2, "LOWER_LEFT"),
	( 11, 4, "LOWER_RIGHT"),
)

keynos = {}

cases = {
	0xa5de: { },
	0xb5ec: { },
	0x807e: { },
}

for r,c,t in keyboard:
	n = 0x20 + r * 8 + c
	# if n >= 0x20 and n < 0x41:
	#	cases[0x807e][(n - 0x20)/3] = "KEY_%02x_" % n + t
	if n >= 0x41 and n < 0x5e:
		cases[0xa5de][n - 0x41] = "KEY_%02x_" % n + t
	if n >= 0x61 and n < 0x80:
		cases[0xb5ec][n - 0x61] = "KEY_%02x_" % n + t
	keynos[n] = t
	print("KEY %02x %s" % (n, t))

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
			data.Const(pj, y.lo - 2, y.lo, "%d", pj.m.bs16, 2)
			x = pj.m.bu16(y.lo - 2)
			cs = cases.get(y.lo)
			if cs == None:
				cs = {}
			for i in range(x):
				ct = cs.get(i)
				if ct == None:
					ct = "_%d" % i
				a = y.lo - 4 - 2 * i
				z = pj.m.bs16(a)
				w = data.Const(pj, a, a + 2, "%d", pj.m.bs16, 2)
				if z < 0:
					w.fmt += " -> 0x%04x" % (y.hi + z)
					pj.todo(y.hi + z, self.disass)
					pj.set_label(y.hi + z, ".case_%04x_%s" %
					    (y.lo, ct))
				
			
			
		return y

cpu = cx()

#######################################################################

fns = {}

class params(data.Const):
	def __init__(self, pj, nm, i, j):
		self.pj = pj
		self.b = 0x195c4
		self.i = i
		self.j = j
		self.fi = pj.m.rd(self.b + i)
		self.args = []
		for a in range(j):
			self.args.append(pj.m.rd(self.b + i + 1 + a))
		pj.set_label(self.b + i, "P_" + nm)
		super(params, self).__init__(pj, self.b + i, self.b + i + 1 + j)

		self.fp = 0x196b6 + self.fi * 4
		self.fa = pj.m.bu32(self.fp)
		pj.todo(self.fa, cpu.disass)
		data.Codeptr(pj, self.fp, self.fp + 4, self.fa)
		pj.set_label(self.fa, "F_" + nm + "(" + self.summ() + ")")

	def summ(self):
		t = []
		for i in self.args:
			if i == 0x03:
				t.append("STR")
			elif i == 0x16:
				t.append("int")
			elif i == 0x18:
				t.append("INT")
			elif i == 0x19:
				t.append("REAL")
			else:
				t.append("0x%02x" % i)
		return ",".join(t)

	def funcidx(self):
		return self.fi

mnems = { }

class mnem(data.Data):
	def __init__(self, pj, lo):
		t = ".MNE\t"
		hi = lo
		while True:
			x = pj.m.rd(hi)
			if x <= 0x20 or x > 0x7e or x == 0x40:
				break
			hi += 1
		a,b,c = data.stringify(pj, lo, hi - lo)
		t += "'" + b + "',"
		while len(t) < 16:
			t += " "
		
		if hi & 1:
			hi += 1

		self.a = pj.m.bu16(hi)
		self.b = pj.m.bu16(hi + 2)
		self.c = pj.m.bu16(hi + 4)
		hi += 6

		super(mnem, self).__init__(pj, lo, hi)

		t += "0x%04x" % self.a
		t += ",0x%04x" % self.b
		t += ",0x%04x" % self.c

		if (self.c >> 8) == 0x30:
			pp = params(pj, b, self.b, self.a >> 8)
			fi = pp.funcidx()
			if fi not in fns:
				fns[fi] = []
			fns[fi].append(b)
			t += " (" + pp.summ() + ")"

		self.fmt = t
		self.compact = True
		mnems[b] = self

#######################################################################

if True:
	cpu.vectors(pj, hi = 0xc0)

	#######################################################################

	for b,e in (
		(0x06936, 0x0693a),
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
		(0x17dbe, 0x17dce),
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

	a = 0x18d24
	while a < 0x19398:
		y = mnem(pj, a)
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
	pj.todo(0x0df5e, cpu.disass) # Arg to 0x802
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
		y.lcmt += " n=%03d" % n
		y.lcmt += " n=0x%02x" % n
		k = pj.m.rd(0x194b2 + n)
		y.lcmt += " key=%02x" % k
		if k in keynos:
			y.lcmt += " ('" + keynos[k] + "')"
		
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
pj.set_label(0x6936, "REVISION")
pj.set_label(0x693a, "MODEL")


pj.set_label(0x01b48, "BCD_NEG8")
pj.set_label(0x01b72, "BCD_ADD8")
pj.set_label(0x01cb0, "BCD_SUB8")
pj.set_label(0x02f38, "CASE")
pj.set_label(0x033fc, "SHOW_CHAR")
pj.set_label(0x03412, "SHOW_SEMI")
pj.set_label(0x0341a, "SHOW_COMMA")
pj.set_label(0x03422, "SHOW_CRNL")
pj.set_label(0x03428, "SHOW_NL")
pj.set_label(0x03430, "SHOW_MINUS")
pj.set_label(0x03438, "SHOW_2CHAR")
pj.set_label(0x03498, "SHOW_INT")
pj.set_label(0x03958, "SHOW_TXT_AT(ADR,STR)")
pj.set_label(0x03906, "2DISPLAY")
pj.set_label(0x039b0, "SHOW_WORD(INT)")
pj.set_label(0x06a2c, "MSG_TXT")
pj.set_label(0x06ce0, "SHOW_TXT(STR)")
pj.set_label(0x06cf2, "SHOW_CRNL")
pj.set_label(0x06d20, "SHOW_MSG")
pj.set_label(0x07b4e, "FILL_DISPLAY")
pj.set_label(0x0940c, "EXEC_KEY(INT)")
pj.set_label(0x0ee6a, "OLDCMD")
pj.set_label(0x17dce, "SHOW_COMMA")
pj.set_label(0x17e9e, "PL_MOVE")
pj.set_label(0x17eac, "PL_LINE")

#pj.set_label(0x18d24, "MNEM")
#pj.set_label(0x195c4, "PARMTYPE")
#pj.set_label(0x196b6, "PRCADRS")


# 0xffff0005
# 0xffff0007
# 0xffff0009
# 0xffff0013
# 0xffff0019
# 0xffff0021
# 0xffff0027
# 0xffff0035

# 0xffff4000
# 0xffff4001
# 0xffff4002
# 0xffff4004
# 0xffff4005
# 0xffff4006
# 0xffff4007

# 0xffff8000

# 0xffffa6ae = stack

# 0xffffa6ae
# 0xffffa6b2
# 0xffffa6b6
# 0xffffa6ba
# 0xffffa6bc
# 0xffffa6be
# 0xffffa6c2
# 0xffffa6c6
# 0xffffa6ca
# 0xffffa6ce
# 0xffffa6d2
# 0xffffa6ec
# 0xffffa6f0
# 0xffffa6f2
# 0xffffa6f8
# 0xffffa6fe
# 0xffffa704
# 0xffffa707
# 0xffffa708
# 0xffffa70a
# 0xffffa70c
# 0xffffa70e
# 0xffffa710
# 0xffffa712
# 0xffffa714
# 0xffffa716
# 0xffffa71a
# 0xffffa71c
# 0xffffa890
# 0xffffa89e
# 0xffffa8a0
# 0xffffa8a4
# 0xffffa8a6
# 0xffffa8a8
# 0xffffa972
# 0xffffa973
# 0xffffa974
# 0xffffa975
# 0xffffa976
# 0xffffa9af
# 0xffffa9b0
# 0xffffa9b2
# 0xffffa9b4
# 0xffffa9b6
# 0xffffa9ba
# 0xffffa9bb
# 0xffffa9bc
# 0xffffa9be
# 0xffffa9c0
# 0xffffa9f4
# 0xffffa9f6
# 0xffffa9f8
# 0xffffa9fa
# 0xffffa9fc
# 0xffffaa1e
# 0xffffaa20
# 0xffffaa24
# 0xffffaa26
# 0xffffaa28
# 0xffffaa29
# 0xffffaa2a
# 0xffffaa2c
# 0xffffaa2d
# 0xffffaa34
# 0xffffaa38
pj.set_label(0xffffaa3c, "ram_fp_led")
# 0xffffaa3d
# 0xffffaa3e
# 0xffffaa3f
# 0xffffaa40
# 0xffffaa41
# 0xffffaa42
# 0xffffaa44
# 0xffffaa46
# 0xffffaa47
# 0xffffaa48
# 0xffffaa4a
# 0xffffaa4c
# 0xffffaa4e
# 0xffffaa50
# 0xffffaa51
# 0xffffaa58
# 0xffffaa59
# 0xffffaa60
# 0xffffaa62
# 0xffffaa64
# 0xffffaa66
# 0xffffaa68
# 0xffffaa69
# 0xffffaa6a
# 0xffffaa6b
# 0xffffaa72
# 0xffffaa73
# 0xffffaa74
# 0xffffaa76
# 0xffffaa78
# 0xffffaa79
# 0xffffaa82
# 0xffffaa84
# 0xffffaa8a
# 0xffffaa8e
# 0xffffaa92
# 0xffffaa9a
# 0xffffaaa2
# 0xffffaaa6
# 0xffffaaaa
# 0xffffaaae
# 0xffffaab2
# 0xffffaaba
# 0xffffaabc
# 0xffffaabe
# 0xffffaac0
# 0xffffaac2
# 0xffffaaca
# 0xffffaad2
# 0xffffaad4
# 0xffffaad6
# 0xffffaad8
# 0xffffaad9
# 0xffffaada
# 0xffffaadc
# 0xffffaade
# 0xffffaae0
# 0xffffaae2
# 0xffffaae4
# 0xffffaae6
# 0xffffaae8
# 0xffffaaea
# 0xffffaaeb
# 0xffffaaec
# 0xffffaaed
# 0xffffaaee
# 0xffffaaef
# 0xffffaaf0
# 0xffffaaf1
# 0xffffaaf2
# 0xffffaaf4
# 0xffffaaf6
pj.set_label(0xffffaaf8, "ram_kbd_row")
# 0xffffaafa
# 0xffffaafc
# 0xffffaafe
# 0xffffaaff
# 0xffffab00
# 0xffffab02
# 0xffffab04
# 0xffffab06
# 0xffffab07
# 0xffffab08
# 0xffffab0a
# 0xffffab0c
# 0xffffab0e
# 0xffffab10
# 0xffffab11
# 0xffffab12
# 0xffffab13
# 0xffffab14
# 0xffffab16
# 0xffffab18
# 0xffffab1a
# 0xffffab9a
# 0xffffaba8
# 0xffffabb0
# 0xffffabba
# 0xffffabbc
# 0xffffabbe
# 0xffffabc8
# 0xffffabce
# 0xffffabd0
# 0xffffabd2
# 0xffffabd6
# 0xffffabda
# 0xffffabde
# 0xffffabe2
# 0xffffabe4
# 0xffffabe6
# 0xffffabe8
# 0xffffabea
# 0xffffabec
# 0xffffabee
# 0xffffabf0
# 0xffffabf2
# 0xffffabfa
# 0xffffae24

# 0xffffb628
# 0xffffb62a
# 0xffffb630
# 0xffffbe2c
# 0xffffbe2e
# 0xffffbe30
# 0xffffbe32
# 0xffffbe34
# 0xffffbe38
# 0xffffbe3c
# 0xffffbe40
# 0xffffbe42
# 0xffffbe44
# 0xffffbe46
# 0xffffbe48
# 0xffffbe50
# 0xffffbe54
# 0xffffbe5c
# 0xffffbe5e
# 0xffffbe60
# 0xffffbe62
# 0xffffbe64
# 0xffffbe68
# 0xffffbe6a
# 0xffffbe78
# 0xffffbe86
# 0xffffbe88
# 0xffffbe8c
# 0xffffbe8e
# 0xffffbe9c
# 0xffffbeaa
# 0xffffbeac
# 0xffffbeb0
# 0xffffbeb2
# 0xffffbec0

# 0xffffbf1f
# 0xffffbf7e
# 0xffffbfde
# 0xffffbfdf
# 0xffffbfe0
# 0xffffbfe1
pj.set_label(0xffffbfe2, "hpib_address")
pj.set_label(0xffffbfe3, "not_hpib_address")
# 0xffffbfe4
# 0xffffbfe5
# 0xffffbfe6
# 0xffffbfe7
# 0xffffbfe8
# 0xffffbfe9
# 0xffffbfea
# 0xffffbfec
# 0xffffbff0
# 0xffffbff4
# 0xffffbff8
# 0xffffbffc
# 0xffffbffd
# 0xffffbffe

# BOTTOM
# 0xffffc000
# 0xffffc002
# 0xffffc006
# 0xffffc008
# 0xffffc00a
# 0xffffc00c
# 0xffffc00e

# A12
pj.set_label(0xffffc010, "rf_fp_led")
pj.set_label(0xffffc012, "rf_kbd_row")
pj.set_label(0xffffc014, "rf_kbd_col")
pj.set_label(0xffffc016, "rf_rtg")
pj.set_label(0xffffc018, "rf_service_req")
pj.set_label(0xffffc01a, "rf_phase_lock")
pj.set_label(0xffffc01c, "rf_249_lock")
pj.set_label(0xffffc01e, "rf_attn")

# 0xffffc020
# 0xffffc022
# 0xffffc025

# A17
pj.set_label(0xffffc028, "freqcnt_ctrl")	# octal 24 = 0x14 *2= 0x28
pj.set_label(0xffffc02a, "freqcnt_msb")
pj.set_label(0xffffc02c, "freqcnt_lsb")

# TOP
pj.set_label(0xffffc040, "display_address")
pj.set_label(0xffffc042, "display_rd_store")
pj.set_label(0xffffc044, "display_wr_store")

# 0xffffc046

pj.set_label(0xffffc048, "display_wr_off")
pj.set_label(0xffffc04a, "display_rd_scan")

# 0xffffc04b

pj.set_label(0xffffc04c, "display_wr_marker")
pj.set_label(0xffffc04e, "display_wr_scan")

# 0xffffc064
# 0xffffc066
# 0xffffc068
# 0xffffc06a
# 0xffffc06c

# HPIB
# 0xffffc081
# 0xffffc083
# 0xffffc085
# 0xffffc087
# 0xffffc089
# 0xffffc08b
# 0xffffc08d
# 0xffffc08f

# LBUS
# 0xffffc0e0

pj.set_label(0xffffc0e1, "display_status")

# 0xffffc0e5


code.lcmt_flows(pj)

listing.Listing(pj)
