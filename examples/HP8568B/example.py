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

import hp856x_cmds

m = mem.byte_mem(0x0, 0x20000)
m.load_binfile(first = 0x00000, step = 0x2, filename="85680-80116.BIN")
m.load_binfile(first = 0x00001, step = 0x2, filename="85680-80115.BIN")
m.load_binfile(first = 0x10000, step = 0x2, filename="85680-80114.BIN")
m.load_binfile(first = 0x10001, step = 0x2, filename="85680-80113.BIN")

# Checum EPROMS
# See 00e9e/ROMSUM
s = [0xff, 0xff, 0xff, 0xff]
for a in range(32768):
	s[0] += m.rd(a * 2)
	s[1] += m.rd(a * 2 + 1)
	s[2] += m.rd(a * 2 + 65536)
	s[3] += m.rd(a * 2 + 65536 + 1)
for i in s:
	assert i & 0xff == 0

pj = job.Job(m, "HP8568B")

class mycpu(m68000.m68000):
	def __init__(self):
		super(mycpu, self).__init__()

	def macro(self, nm, l):
		s = nm + " - "
		for i in l:
			if i == " ":
				continue
			j = int(i, 16)
			s += "|%d %d %d %d" % (
				(j >> 3) & 1,
				(j >> 2) & 1,
				(j >> 1) & 1,
				(j >> 0) & 1
			)
		s += "|\n"
		self.it.load_string(s)

cpu = mycpu()
cpu.macro("DISPLAY_READY()", "0838 0007 c0e1 66f8")

#######################################################################

# Where ?
# y = data.Const(pj, 0xfffe, 0x10000)
# pj.set_label(y.lo, "eprom_lo_chksum")
y = data.Const(pj, 0x19854, 0x19856)
pj.set_label(y.lo, "eprom_hi_chksum")

#######################################################################

def data_double(pj, a):
	return data.Pstruct(pj, a, ">d", "%g", ".DOUBLE")

def data_float(pj, a):
	y = data.Data(pj, a, a + 4)
	x = pj.m.bu32(a)
	e = x & 0xff
	if e & 0x80:
		e -= 0x100
	m = x >> 8
	s = m >> 23
	m &= 0x7fffff
	y.val = m * (2.0 ** (e - 22.0))
	if s:
		y.val *= -1
	y.fmt = ".FLOAT\t%g" % y.val
	y.lcmt = "s=%d m=0x%06x e=%d" % (s,m,e)
	return y

def data_bcd(pj, a):
	return data.Pstruct(pj, a, ">Q", "%016x", ".BCD")

#######################################################################
# Functions taking arguments after call instruction

post_arg = {
	0x1bc8: ("BCD_CMP",	"brel",	"D01"),
	0x1bcc: ("BCD_CMP",	"babs",	"D01"),
	0x1bd0: ("BCD_CMP",	"bA6rel", "D01"),
	0x1bdc: ("BCD_CMP",	"D01",	"babs"),
	0x1be0: ("BCD_CMP",	"D01",	"bA6rel"),

	0x1c52: ("BCD_ADD",	"brel",	"D01"),
	0x1c56: ("BCD_ADD",	"babs",	"D01"),
	0x1c5a: ("BCD_ADD",	"bA6rel",	"D01"),
	0x1c5e: ("BCD_ADD",	"stk",	"D01"),

	0x1c76: ("BCD_SUB",	"brel", "D01"),
	0x1c7a: ("BCD_SUB",	"babs", "D01"),
	0x1c7e: ("BCD_SUB",	"bA6rel", "D01"),

	0x1c88: ("BCD_SUB",	"brel", "D01"),
	0x1c8c: ("BCD_SUB",	"babs", "D01"),
	0x1c90: ("BCD_SUB",	"bA6rel", "D01"),

	0x1ccc: ("",	"dabs", "FPXXX"),
	0x2218: ("BCD_LD_D01", "bcd"),
	0x223c: ("BCD_LD_D23", "bcd"),
	0x238e: ("",	"drel", "FPXXX"),
	0x239a: ("",	"dA6rel", "FPXXX"),
	0x23f6: ("",	"drel", "FPXXX"),
	0x2402: ("",	"D0+D1", "dA6rel"),
	0x24ac: ("",	"drel", "FPXXX"),
	0x24b8: ("",	"dA6rel", "FPXXX"),
	0x24c4: ("",	"drel", "FPXXX"),
	0x25b0: ("",	"drel", "FPXXX"),
	0x25c8: ("",	"drel", "FPXXX"),
	0x25fa: ("",	"dA6rel", "FPXXX"),
	0x27ee: ("",	"lrel", "FPXXX"),

	0x2862: ("",	"lrel", "LFXXX"),
	0x28c2: ("",	"lrel", "LFXXX"),
	0x28ce: ("",	"fabs", "LFXXX"),
	0x297c: ("",	"fA6rel", "LFXXX"),
	0x2982: ("",	"fabs", "LFXXX"),
	0x2988: ("",	"frel", "FFXXX"),
	0x29ba: ("",	"fA6rel", "LFXXX"),
	0x29c6: ("",	"frel", "FFXXX"),
	0x29ea: ("",	"fA6rel", "LFXXX"),
	0x29f6: ("",	"frel", "FFXXX"),
	0x2a02: ("",	"fA6rel", "LFXXX"),
	0x2a0e: ("",	"frel", "FFXXX"),
	0x2a34: ("",	"frel", "FFXXX"),
	0x2a6e: ("",	"frel", "FFXXX"),
	0x2b08: ("",	"fA6rel", "LFXXX"),
	0x2b14: ("",	"frel", "FFXXX"),
	0x2b2c: ("",	"frel", "FFXXX"),
}

for i in post_arg:
	j = post_arg[i]
	if len(j) > 0 and j[0] != "":
		pj.set_label(i, j[0])

def flow_post_arg(pj, ins):
	z = post_arg.get(ins.dstadr)
	if z == None:
		return
	ins.flow_out.pop(-1)
	if len(z) <= 1:
		a = data.Pstruct(pj, ins.hi, ">h", "%d", ".INFIX").hi
		ins.add_flow(pj, ">", True, a)
		return
	l = []
	for i in z[1:]:
		if i[1:] == "A6rel":
			r = pj.m.bs16(ins.hi)
			ins.hi += 2
			if r < 0:
				l.append("(A6-0x%x)" % -r)
			else:
				l.append("(A6+0x%x)" % r)
		elif i[1:] == "abs":
			r = pj.m.bu16(ins.hi)
			if r & 0x8000:
				r |= 0xffff0000
			ins.hi += 2
			l.append("0x%08x" % r)
		elif i == "drel":
			r = ins.hi + pj.m.bs16(ins.hi)
			ins.hi += 2
			ins.lcmt += " @0x%x\n" % r
			y = data_double(pj, r)
			l.append("%g" % y.data[0])
		elif i == "brel":
			r = ins.hi + pj.m.bs16(ins.hi)
			ins.hi += 2
			ins.lcmt += " @0x%x\n" % r
			y = data_bcd(pj, r);
			l.append("%x" % y.data[0])
		elif i == "lrel":
			r = ins.hi + pj.m.bs16(ins.hi)
			ins.hi += 2
			ins.lcmt += " @0x%x\n" % r
			y = data.Pstruct(pj, r, ">L", "%d", ".LONG")
			l.append("%d" % y.data[0])
		elif i == "frel":
			r = ins.hi + pj.m.bs16(ins.hi)
			ins.hi += 2
			ins.lcmt += " @0x%x\n" % r
			y = data_float(pj, r)
			l.append("%g" % y.val)
		elif i == "bcd":
			r = pj.m.bu16(ins.hi)
			y = data.Pstruct(pj, ins.hi, ">H", "%x", ".BCD")
			l.append("%04x" % r)
			ins.hi += 2
		else:
			l.append(i)
	ins.oper.append("(" + ",".join(l) + ")")
	ins.add_flow(pj, True, True, ins.hi)

cpu.flow_check.append(flow_post_arg)

#######################################################################

switches = {
	0x13624: {
		0: "ALL",
		1: "ONEOS",
		2: "ONSWP",
		3: "TRMATH",
	},
}

def flow_switch(pj, ins):
	if ins.dstadr != 0x2f38:
		return
	ins.flow_out.pop(0)
	ins.add_flow(pj, ">", "?", ins.hi)
	pj.set_label(ins.hi, "break_%04x" % ins.lo)

	y = data.Const(pj, ins.lo - 2, ins.lo)
	ncase = pj.m.bu16(ins.lo - 2)
	y.typ = ".NCASE"
	y.fmt = "%d" % ncase
	cs = switches.get(ins.lo)
	if cs == None:
		cs = {}
	a = ins.lo - 2
	for i in range(ncase):
		a -= 2
		ct = cs.get(i)
		if ct == None:
			ct = "_%d" % i

		w = data.Const(pj, a, a + 2)
		z = pj.m.bs16(a)
		w.typ = ".CASE"
		w.fmt = "0x%x, %d" % (i,z)

		w.fmt += ", 0x%04x" % (ins.hi + z)
		ins.add_flow(pj, ">", "0x%x" % i, ins.hi + z)
		if z < 0:
			pj.set_label(ins.hi + z, ".case_%04x_%s" % (ins.lo, ct))

cpu.flow_check.append(flow_switch)
pj.todo(0x2f38, cpu.disass)

#######################################################################

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
for r,c,t in keyboard:
	n = 0x20 + r * 8 + c
	keynos[n] = t


#######################################################################

class params(data.Data):
	def __init__(self, pj, nm, i, j):
		self.nm = nm
		self.b = 0x195c4
		self.i = i
		self.j = j
		self.fi = pj.m.rd(self.b + i)
		self.args = []
		for a in range(j):
			self.args.append(pj.m.rd(self.b + i + 1 + a))
		super(params, self).__init__(pj, self.b + i, self.b + i + 1 + j)

		self.fp = 0x196b6 + self.fi * 4
		self.fa = pj.m.bu32(self.fp)
		pj.todo(self.fa, cpu.disass)
		data.Codeptr(pj, self.fp, self.fp + 4, self.fa)
		pj.set_label(self.fa, "F_" + nm + "(" + self.summ() + ")")

	def render(self, pj):
		t = ".PARAM\t"
		t += "func=%d" % self.fi
		t += " call=%s" % self.nm 
		t += "(" + self.summ() + ")"
		return t

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

class mnem(data.Data):
	def __init__(self, pj, hi):
		lo = hi
		lo -= 2
		self.c = pj.m.bu16(lo)
		lo -= 2
		self.b = pj.m.bu16(lo)
		lo -= 2
		self.a = pj.m.bu16(lo)

		self.len = self.c & 0xfff
		self.type = self.c >> 12

		lo -= (self.len + 1) & 0xffe
		super(mnem, self).__init__(pj, lo, hi)


		self.compact = True

		a,b,c = data.stringify(pj, self.lo, self.len)
		self.string = b

		self.hash = 0
		for i in bytearray(self.string):
			self.hash += i
		self.hash %= 13

		self.pp = None
		self.args = None

		if self.type == 3:
			self.pp = params(pj, self.string, self.b, self.a >> 8)
		if self.type == 1:
			if self.b not in keynos:
				keynos[self.b] = "CMD_" + self.string


	def render(self, pj):
		t = ".MNEM\t"
		t += "0x%04x" % self.a
		t += ", 0x%04x" % self.b
		t += ", 0x%x" % self.type
		t += ", len=0x%03x" % self.len
		t += ", hash=%2d" % self.hash
		t += ", '" + self.string + "'"
		return t

if True:
	pj.set_label(0x18c3a, "MNETABLE")
	a = 0x193a0
	while a > 0x18c3a:
		y = mnem(pj, a)
		x = pj.m.bu16(y.lo - 2)
		a = y.lo

#######################################################################

class oldcmd(data.Data):
	def __init__(self, pj, lo, n):
		super(oldcmd, self).__init__(pj, lo, lo + 2)
		x,self.name,y = data.stringify(pj, self.lo, 2)

		self.key = pj.m.rd(0x194b2 + n)
		self.imm = (pj.m.rd(0x1951e + (n >> 3)) >> (n & 7)) & 1
		if not self.imm:
			self.svf1 = pj.m.bu16(0x1952c + self.key * 4)
			self.svf2 = pj.m.bu16(0x1952c + self.key * 4 + 2)
			if not self.svf2 in keynos:
				keynos[self.svf2] = "CMD_" + self.name

	def render(self, pj):
		t = ".OLDCMD\t"
		t += "'" + self.name + "'"
		t += " imm=%x" % self.imm
		t += " key=%02x" % self.key
		if self.imm and self.key in keynos:
			t += " ('" + keynos[self.key] + "')"
		if not self.imm:
			t += " svf=0x%04x,0x%04x" % (self.svf1, self.svf2)
			t += " xxx=%02x" % (self.svf1 & 0x1e)
		return t

if True:
	pj.set_label(0x193da, "OLDCMDS")
	n = 0
	for a in range(0x193da, 0x194b2, 2):
		y = oldcmd(pj, a, n)
		n += 1
	print("OLDCMDS %d" % ((0x194b2-0x193da)/2))

	pj.set_label(0x194b2, "KEYTAB")
	for a in range(0x194b2, 0x1951e, 8):
		y = data.Const(pj, a, min(a + 8, 0x1951e), fmt="0x%02x")
	print("KEYTAB %d" % ((0x1951e-0x194b2)/1))

	pj.set_label(0x1951e, "IMEDBITS")
	for a in range(0x1951e, 0x1952c, 8):
		y = data.Const(pj, a, min(a + 8, 0x1952c), fmt="0x%02x")
	print("IMEDBITS %d" % ((0x1952c-0x1951e)/1))

	pj.set_label(0x1952c, "SFLGVAL")
	for a in range(0x1952c, 0x195c4, 16):
		y = data.Const(pj, a, min(a + 16, 0x195c4),
		    "0x%08x", pj.m.bu32, 4)
	print("SFLGVAL %d" % ((0x195c4-0x1952c)/2))

#######################################################################

switches[0x09ae8] = {}
switches[0x09d78] = {}
switches[0x0a5de] = {}
switches[0x0af5c] = {}
switches[0x0b5ec] = {}
switches[0x0bb4e] = {}
switches[0x0bd5a] = {}
switches[0x0bd6e] = {
	0: "KEYS_00_1f",
	1: "KEYS_20_3f",
	2: "KEYS_40_5f",
	3: "KEYS_60_7f",
	4: "KEYS_80_9f",
	5: "KEYS_a0_bf",
}

for n in keynos:
	t = keynos[n]
	print("KEY_%02x" % n, t)
	sk = "KS%c" % n
	ksk = hp856x_cmds.cmds.get(sk)
	if ksk != None and type(ksk) != str:
		ksk = ksk[1]
	if ksk == None:
		ksk = "==" + t
	if n < 0x20:
		switches[0x9ae8][n] = "KEY_%02x_" % n + t
	if n >= 0x20 and n < 0x30:
		switches[0x9d78][n - 0x20] = "KEY_%02x_" % n + t
	if n >= 0x40 and n < 0x60:
		switches[0xa5de][n - 0x41] = "KEY_%02x_" % n + t
		switches[0xaf5c][n - 0x41] = "KEY_S%02x_KS%c_" % (n, n) + ksk
	if n >= 0x60 and n < 0x80:
		switches[0xb5ec][n - 0x61] = "KEY_%02x_" % n + t
		switches[0xbb4e][n - 0x60] = "KEY_S%02x_KS%c_" % (n, n) + ksk
	if n >= 0xa0 and n <= 0xbf:
		switches[0xbd5a][n - 0xa0] = "KEY_%02x_" % n + t

if True:
	for b,e in (
		( 0x0e750, 0x0e778),
		( 0x15ca4, 0x15cb4),
	):
		for a in range(b, e, 8):
			data_double(pj, a)

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

	data.Txt(pj, 0x15dfc, pfx=1, align=2)

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

	data.Dataptr(pj, 0xe39a, 0xe39a + 4, pj.m.bu32(0xe39a))

	data.Const(pj, 0x2140, 0x2148, "%d", pj.m.bu64, 8)
	data.Const(pj, 0x2148, 0x214c, "%d", pj.m.bu32, 4)

	for a in (
		0x0645e,
		0x06476,
		0x0647e,
		0x0648a,
		0x06492,
		0x0649a,
		0x064a6,
		0x064be,
		0x0e2c4,
		0x0e2d4,
		0x0e2cc,
		0x0e32a,
		0x0e332,
		0x0e37c,
		0x0e384,
		0x128ca,
		0x15da0,
	):
		y = data_bcd(pj, a)
		pj.set_label(a, "BCD_%x" % y.data[0])


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
	# 0ee98  00 01 93 be
	# 0eeaa  00 01 93 da  |    |
	# 0ee8e  00 01 da ee  |    |
	#######################################################################
	# Orphans ?

	if False:
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

	# from 0x2272
	pj.todo(0x2282, cpu.disass)

	# filled in 0xffffabd2
	pj.todo(0x0ed98, cpu.disass)

	pj.todo(0x0df5e, cpu.disass) # Arg to 0x802
	pj.todo(0x3292, cpu.disass)	# 0x3284

	#######################################################################
	# pat 4,244,024 pg 262 lin 3700

	pj.set_label(0x4fac, "SCANTAB")
	for a in range(0x4fac, 0x4fec, 2):
		y = data.Const(pj, a, a+2, "0x%04x", pj.m.bu16, 2)

	#######################################################################

	y = data.Const(pj, 0x193a2, 0x193be, "%d", pj.m.bu16, 2)
	pj.set_label(y.lo, "HASHPTR2")
	y = data.Const(pj, 0x193be, 0x193da, "%d", pj.m.bu16, 2)
	pj.set_label(y.lo, "HASHPTR")



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
	if i.dstadr in (0x940c, 0xed54):
		y = pj.t.find_hi(i.lo)
		if len(y) != 1:
			continue
		y = y[0]
		if pj.m.rd(y.lo) == 0x70:
			k = pj.m.rd(y.lo + 1)
		elif pj.m.bu16(y.lo) == 0x103c:
			k = pj.m.bu16(y.lo + 2)
		else:
			continue
		if not k in keynos:
			continue
		y.oper[1].txt = "#KEY_" + keynos[k]
		
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

y = data.Const(pj, 0x693a, 0x693c, "%d", pj.m.bu16, 2)

pj.set_label(0x009b8, "RESET")
pj.set_label(0x00c2e, "SELFTEST")
pj.set_label(0x00d7a, "CPUTEST_FAIL")
pj.set_label(0x00e9a, "epromsize")
y = data.Const(pj, 0x00e9a, 0x00e9e, "%d", pj.m.bu32, 4)
pj.set_label(0x00ef2, "ramaddress")
y = data.Const(pj, 0x00ef2, 0x00efe, "0x%08x", pj.m.bu32, 4)
pj.set_label(0x00e9e, "ROMSUM")
pj.set_label(0x00ec0, "ROMTEST")
pj.set_label(0x01ae2, "BCD_FMT(BCD, PTR)")
pj.set_label(0x01b34, "BCD_ABS(BCD)")
pj.set_label(0x01b38, "BCD_NEG(BCD)")
pj.set_label(0x01be6, "BCD_CMP(R01,R23)")
pj.set_label(0x01bea, "BCD_CMP(R23,R01)")
pj.set_label(0x01c00, "stk_64")
pj.set_label(0x01c14, "rel_64")
pj.set_label(0x01c28, "abs_64")
pj.set_label(0x01c3c, "loc_64")
pj.set_label(0x01b48, "BCD_NEG8(&A0)")
pj.set_label(0x01b62, "BCD_NEG(D23)")
pj.set_label(0x01b72, "BCD_ADD8(&A0,&A1)")
pj.set_label(0x01c60, "BCD_ADD(D01, D23)")
pj.set_label(0x01c98, "BCD_SUBR(D23, D01(order?)")
pj.set_label(0x01c9c, "BCD_SUB(D01, D23(order?)")
pj.set_label(0x01cb0, "BCD_SUB8(&A0,&A1)")
pj.set_label(0x0214c, "BCD_MUL5(D01)")
pj.set_label(0x0217e, "BCD_MUL3(D01)")
pj.set_label(0x0218c, "BCD_MUL6(D01)")
pj.set_label(0x021be, "BCD_MUL8(D01)")
pj.set_label(0x021c0, "BCD_MUL4(D01)")
pj.set_label(0x021c4, "BCD_MUL2(D01)")
pj.set_label(0x021f6, "BCD_DIV2(D01)")
pj.set_label(0x02224, "BCD_LD(D0.W)")
pj.set_label(0x0222c, "BCD_LD(D0.L)")
pj.set_label(0x023ec, "FD_ABS(R2+R3)")
pj.set_label(0x0287e, "rel_32")
pj.set_label(0x02892, "abs_32")
pj.set_label(0x028a4, "loc_32")
pj.set_label(0x02f38, "SWITCH")
pj.set_label(0x0320e, "BZERO(PTR,INT)")
pj.set_label(0x033fc, "SHOW_CHAR")
pj.set_label(0x03412, "SHOW_SEMI")
pj.set_label(0x0341a, "SHOW_COMMA")
pj.set_label(0x03422, "SHOW_CRNL")
pj.set_label(0x03428, "SHOW_NL")
pj.set_label(0x03430, "SHOW_MINUS")
pj.set_label(0x03438, "SHOW_2CHAR")
pj.set_label(0x03498, "SHOW_INT")
pj.set_label(0x03932, "DISP_RD(INT ADR)")
pj.set_label(0x03958, "SHOW_TXT_AT(ADR,STR)")
pj.set_label(0x03906, "DISP_WR(INT ADR, INT DATA)")
pj.set_label(0x039b0, "SHOW_WORD(INT)")
pj.set_label(0x03c0a, "FREQ_CNT_SET_PERIOD(INT)")
pj.set_label(0x03c26, "FREQ_CNT_WAIT()")
pj.set_label(0x03c3a, "FREQ_CNT_10MHZ(INT)")
pj.set_label(0x06936, "REVISION")
pj.set_label(0x0693a, "MODEL")
pj.set_label(0x06a2c, "MSG_TXT")
pj.set_label(0x06ce0, "SHOW_TXT(STR)")
pj.set_label(0x06cf2, "SHOW_CRNL")
pj.set_label(0x06cfc, "SET_IF_LEDS(INT)")
pj.set_label(0x06d20, "SHOW_MSG")
pj.set_label(0x070be, "UPD_DETECTOR")
pj.set_label(0x07b4e, "FILL_DISPLAY")
pj.set_label(0x08164, "SHOW_CR[NL]")
pj.set_label(0x0940c, "EXEC(INT KEY)")
pj.set_label(0x0e39a, "VAR_HEAD")
pj.set_label(0x0ed54, "EXEC2(INT KEY)")
pj.set_label(0x0eddc, "SEARCH(NAMLEN.W, CHAIN.L, HASH.L, NAME.L)")
pj.set_label(0x0ee6a, "FIND_OLDCMD(INT)")
pj.set_label(0x0f72c, "NAME2TRACE")
pj.set_label(0x0a986, "CALIBRATING")
pj.set_label(0x0aa7a, "AUTOCAL")
pj.set_label(0x13092, "WHICH(PTR TABLE, STR KEY, INT N)")
pj.set_label(0x14158, "TRACE_MATH(LONG, INT, STR, STR, STR)")
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

#pj.set_label(0xffff4000, "PIT_PGCR")
#pj.set_label(0xffff4002, "PIT_PSRR")
#pj.set_label(0xffff4004, "PIT_PADDR")
#pj.set_label(0xffff4006, "PIT_PBDDR")
#pj.set_label(0xffff4008, "PIT_PCDDR")

#pj.set_label(0xffff4010, "PIT_PADR")
#pj.set_label(0xffff4012, "PIT_PBDR")

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
pj.set_label(0xffffa6d2, "ram_var_hash")
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
pj.set_label(0xffffaa2c, "ram_center_freq")
# 0xffffaa2d
pj.set_label(0xffffaa34, "ram_freq_span")
# 0xffffaa38
pj.set_label(0xffffaa3c, "ram_rf_fp_leds")
pj.set_label(0xffffaa3e, "ram_if_fp_leds")
# 0xffffaa3f
# 0xffffaa40	if_scale_gain copy
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
pj.set_label(0xffffabd2, "func_ptr+a6+a7")
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
pj.set_label(0xffffbfe2, "ram_hpib_address")
pj.set_label(0xffffbfe3, "ram_not_hpib_address")
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


# I/O Decoding on A15
#####################
# 0x...00 BIO - BOTTOM/RF
# 0x...20 DBCLK      #2
# 0x...40 TIO - TOP/IF
# 0x...64 LDBTEST    #7
# 0x...80 LHPIB
# 0x...a4 LDBTEST    #7
# 0x...c0 LBUS
# 0x...e0 HPIBSW     #1
# 0x...e4 LATR       #5


# BIO/BOTTOM/RF
###############
pj.set_label(0xffffc000, "rf_50vto_lo_dac")
pj.set_label(0xffffc002, "rf_50vto_hi_dac")
pj.set_label(0xffffc006, "rf_yig_dac")
pj.set_label(0xffffc008, "rf_scan_atten_vto")
pj.set_label(0xffffc00a, "rf_scantime")
pj.set_label(0xffffc00c, "rf_yig_lock_scan")
pj.set_label(0xffffc00e, "rf_scan_mode")

# A12
pj.set_label(0xffffc010, "rf_fp_leds")
pj.set_label(0xffffc012, "rf_kbd_row")
pj.set_label(0xffffc014, "rf_kbd_col")
pj.set_label(0xffffc016, "rf_rpg")
pj.set_label(0xffffc018, "rf_srq_resets")
pj.set_label(0xffffc01a, "rf_phase_lock")
pj.set_label(0xffffc01c, "rf_245_lock")
pj.set_label(0xffffc01e, "rf_attn")

# A15
pj.set_label(0xffffc020, "dbus_test_0")
pj.set_label(0xffffc022, "dbus_test_2")
pj.set_label(0xffffc025, "dbus_test_5")

# A17
pj.set_label(0xffffc028, "rf_freqcnt_ctrl")
pj.set_label(0xffffc02a, "rf_freqcnt_msb")
pj.set_label(0xffffc02c, "rf_freqcnt_lsb")

#
pj.set_label(0xffffc030, "rf_inputs_atten_20")
pj.set_label(0xffffc032, "rf_vunit_atten_30")
pj.set_label(0xffffc034, "rf_atten_40")
pj.set_label(0xffffc034, "rf_atten_50")
pj.set_label(0xffffc034, "rf_atten_60")
pj.set_label(0xffffc034, "rf_atten_70")

# TIO/TOP/IF
############
pj.set_label(0xffffc040, "display_address")
pj.set_label(0xffffc042, "display_rd_store")
pj.set_label(0xffffc044, "display_wr_store")
pj.set_label(0xffffc046, "display_wr_offset")
pj.set_label(0xffffc048, "display_control")
pj.set_label(0xffffc04a, "display_rd_scan")
pj.set_label(0xffffc04c, "display_wr_marker")
pj.set_label(0xffffc04e, "display_wr_scan")

# SWEEP
pj.set_label(0xffffc064, "if_sweep_src_trig")
pj.set_label(0xffffc066, "if_sweep_time")
pj.set_label(0xffffc068, "if_scale_gain")
pj.set_label(0xffffc06a, "if_bw_fine")
pj.set_label(0xffffc06c, "if_fp_leds")

# HPIB 
######
# 0xffffc081
# 0xffffc083
# 0xffffc085
# 0xffffc087
# 0xffffc089
# 0xffffc08b
# 0xffffc08d
# 0xffffc08f

# LBUS
######

# 0xffffc0e0 ?

# HPIBSW
pj.set_label(0xffffc0e1, "adrsw_srq_display_ready")

pj.set_label(0xffffc0e5, "latr_test")

#######################################################################

if False:
	for a in (
		0x01298,
		0x013a8,
		0x013d8,
		0x013de,
		0x013e4,
		0x01e12,
		0x01e94,
		0x0217e,
		0x0218c,
		0x02194,
		0x021a8,
		0x02268,
	):
		print("ORPHAN %x" % a)
		y = cpu.disass(pj, a)
		y.lcmt = "ORPHAN - "

	nondisc = {
		0x14ce:	0,
	}

	while True:
		l = []
		for b,e in pj.gaps():
			if b in nondisc:
				continue
			if e - b < 2:
				continue
			if pj.m.bu16(b) in (0x4eb8, 0x4e56):
				l.append(b)
			elif pj.m.rd(b) in (0x61,):
				l.append(b)
		print(l)
		for i in l:
			y = cpu.disass(pj, i)
			y.lcmt = "DISCOVER - "
		while pj.run():
			pass
		if len(l) == 0:
			break

#######################################################################


code.lcmt_flows(pj)

listing.Listing(pj, ncol=8)
