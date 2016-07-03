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

fwd="/critter/Doc/TestAndMeasurement/HP8904A/FW/"

#######################################################################
# The HP8904A has five memory pages, four of which occupy the same
# address space.  We analyse them separately.

def setup(pg=4):
	if pg < 4:
		m = mem.byte_mem(0x4000, 0x8000)
		fi = open(fwd + "/08904-87008.hex")
		for i in fi:
			j = i.split()
			if int(j[0],10) == pg:
				m.wr(int(j[1],16), int(j[2],16))
		fi.close()
	else:
		m = mem.byte_mem(0x8000, 0x10000)
		m.load_binfile(0x8000, 1, fwd + "08904-87007.bin")

	pj = job.Job(m, "HP8904A_pg%d" % pg)
	pj.pg = pg
	return pj,m

#######################################################################

hpib = {
	"AHR":	"Amplitude Hop",
	"DPE":	"Digital Port",
	"FRH":	"Frequncy Hop Mode",
	"FHR":	"Frequncy Hop",
	"HRA":	"Hop Register",
	"PHH":	"Phase Hop Mode",
	"PHR":	"Phase Hop",
	"QRE":	"Query Port Status",
	"LO":	"Gaussian Filter",
	"SH":	"Sharp Filter",
	"AU":	"Auto Filter",
	"SI":	"Sine",
	"RA":	"Ramp",
	"TR":	"Triangle",
	"SQ":	"Square",
	"NS":	"Noise",
	"DC":	"DC",
	"KZ":	"kHz",
	"HZ":	"Hz",
	"DG":	"Degrees",
	"RD":	"Radians",
	"VL":	"Volts",
	"MV":	"Millivolts",
	"UV":	"Microvolts",
	"ET":	"Enter",
	"SC":	"Seconds",
	"MS":	"Milliseconds",
	"PC":	"Percent",
	"UP":	"Increment Up",
	"DN":	"Increment Down",
	"SEQE":	"Sequence end",
	"SEQP":	"Sequence index",
	"WSQ":	"Sequence string",
	"FRH":	"Tone Frequency",
	"RUNC":	"Run cont.",
	"RUNM": "Run man.",
	"RUNS":	"Run single",
	"STOP":	"Stop Run mode",
	"AM":	"AM mod.",
	"FM":	"FM mod.",
	"PM":	"PM mod.",
	"DS":	"DSB mod.",
	"PU":	"Pulse mod.",
	"APH":	"Tone/DTMF Amplitude",
	"DAPH":	"Dig.Seq. On Level",
	"DAPL":	"Dig.Seq. Off Level",
	"BSB":	"Dig.Seq. Binary Base",
	"BSO":	"Dig.Seq. Octal Base",
	"BSH":	"Dig.Seq. Hex Base",
	"STOF":	"Tone/DTMF Off time",
	"STON":	"Tone/DTMF On time",
	"SBP":	"Dig.Seq. Period",
	"HRA":	"Tone/DTMF Register Number",
	"APA":	"Amplitude A",
	"APB":	"Amplitude B",
	"APC":	"Amplitude C",
	"APD":	"Amplitude D",
	"BO":	"Backlight On",
	"BF":	"Backlight Off",
	"BP":	"Beep",
	"DEA":	"Destination",
	"DEB":	"Destination",
	"DEC":	"Destination",
	"DED":	"Destination",
	"EM":	"Exit",
	"FS":	"Filter",
	"FC":	"Float Control",
	"FRA":	"Frequency",
	"FRB":	"Frequency",
	"FRC":	"Frequency",
	"FRD":	"Frequency",
	"GM":	"Goto Mode",
	"HP":	"Help",
	"ID":	"Id",
	"IS":	"Increment Set",
	"OF":	"Off",
	"ON":	"On",
	"OO":	"Output Control",
	"PHA":	"Phase",
	"PHB":	"Phase",
	"PHC":	"Phase",
	"PHD":	"Phase",
	"PR":	"Phase Reset",
	"PS":	"Instrument Preset",
	"RC":	"Recall",
	"RP":	"Reverse Power",
	"SV":	"Save",
	"RM":	"Read Service Req Mask",
	"SM":	"Set Service Req Mask",
	"SF":	"Special Function",
	"RSF":	"Read Special Function",
	"EO":	"Read External Reference Status",
	"WFA":	"Waveform",
	"WFB":	"Waveform",
	"WFC":	"Waveform",
	"WFD":	"Waveform",
}

#######################################################################

def symb(pj, cpu):
	for p,a,n in [
		(0, 0x4018, "MAIN_MENUS"),
		(0, 0x43bd, "HOP_RAM_ADRS"),
		(0, 0x4908, "HOP_CFG"),
		(0, 0x4ed8, "0x4ed8"),		# @0:54cb -> 3b85
		(0, 0x51e3, "0x51e3"),		# @1:55bc -> 2213
		(0, 0x5253, "0x5253"),		# @0:54d1 -> 2213
		(0, 0x5d0c, "0x5d0c"),		# @0:54bf -> 220f

		(1, 0x42d1, "0x42d1"),		# @1:6cc4
		(1, 0x444c, "0x444c"),		# @1:6cb1
		(1, 0x4567, "0x4567"),		# @1:5517
		(1, 0x4c01, "0x4c01"),		# @1:550b -> 220f
		(1, 0x5185, "0x5185"),		# @1:5511 -> 2211
		(1, 0x51e3, "0x51e3"),		# @1:55bf -> 2213
		(1, 0x55c5, "APP_TONE"),
		(1, 0x7870, "0x7870"),		# @1:79e5
		(1, 0x7a81, "APP_DTMF"),
		(1, 0x47fa, "TONE_NBR"),
		(1, 0x4842, "TONE_ON_TIME"),
		(1, 0x492c, "TONE_F3"),
		(1, 0x4860, "TONE_OFF_TIME"),
		(1, 0x71b4, "TSEQ_INDEX"),
		(1, 0x726a, "TSEQ_HEX"),
		(1, 0x7203, "TSEQ_EDIT"),
		(1, 0x71de, "TSEQ_END"),
		(1, 0x49ee, "TSEQ_NBR"),
		(1, 0x4a19, "TSEQ_CONT"),
		(1, 0x4aa2, "TSEQ_SINGLE"),
		(1, 0x4ab9, "TSEQ_STOP"),

		(2, 0x4196, "0x4196"),		# @2:543a
		(2, 0x642e, "0x642e"),		# @2:6581
		(2, 0x6646, "0x6646"),		# @2:72f0
		(2, 0x6ad0, "0x6ad0"),		# @2:72e4 -> 220f
		(2, 0x6f60, "0x6f60"),		# @2:72ea -> 2211
		(2, 0x6fbe, "0x6fbe"),		# @2:735b -> 2213
		(2, 0x7364, "APP_DSEQ"),
		(2, 0x689b, "DSEQ_BASE"),
		(2, 0x6940, "DSEQ_ON_LEVEL"),
		(2, 0x6917, "DSEQ_PERIOD"),
		(2, 0x6976, "DSEQ_OFF_LEVEL"),
		(2, 0x5b24, "DSEQ_INDEX"),
		(2, 0x5b4e, "DSEQ_END"),
		(2, 0x5bda, "DSEQ_HEX"),
		(2, 0x5b73, "DSEQ_EDIT"),
		(2, 0x69ed, "DSEQ_BIT"),
		(2, 0x6a18, "DSEQ_CONT"),
		(2, 0x6aa1, "DSEQ_SINGLE"),
		(2, 0x6ab8, "DSEQ_STOP"),

		(3, 0x471c, "ROM_CHECK"),
		(3, 0x4803, "0x4803"),		# @3:4b72 -> 23b0
		(3, 0x4848, "0x4848"),
		(3, 0x4b1e, "KEYBOARD_CHECK"),
		(3, 0x4b85, "0x4b85"),		# @3:4c51 -> 220f
		(3, 0x4c26, "APP_DIAG"),
		(3, 0x4dcf, "RAM_CHECK"),
		(3, 0x4ef7, "LCD_CHECK"),
		(3, 0x50ce, "0x50ce"),		# @3:52f2 -> 220f
		(3, 0x5298, "MEM_ACCESS"),
		(3, 0x530f, "PLL_CHECK"),
		(3, 0x5914, "0x5914"),		# @3:5f7f -> 220f
		(3, 0x5ec8, "MANUAL_COWCHIP"),
		(3, 0x5f96, "0x5f96"),		# @3:6230
		(3, 0x61bb, "MANUAL_MEMORY"),
		(3, 0x6a25, "0x6a25"),		# @3:7323 -> 220d
		(3, 0x6d64, "0x6d64"),		# @3:6f6d -> 220d
		(3, 0x6f80, "0x6f80"),		# @3:7233 -> 220d
		(3, 0x7246, "APP_XX5"),
		(3, 0x7ac3, "APP_XX6"),
		(3, 0x7b7a, "0x7b7a"),

		(4, 0x89aa, "0x89aa"),
		(4, 0x8a08, "SET_MENU"),
		(4, 0x8a2f, "0x8a2f"),
		(4, 0x8b4c, "MENU_EXIT"),
		(4, 0x8c14, "0x8c14"),		# @0x8d51,0x8edb -> 220f
		(4, 0x90c9, "0x90c9"),
		(4, 0x9a40, "0x9a40"),		# #0x9199
		(4, 0x9a47, "0x9a48"),		# #0x917a
		(4, 0x9a4b, "0x9a4b"),		# #0x9189
		(4, 0x975e, "0x975e"),
		(4, 0x9b08, "0x9b08"),
		(4, 0x9b70, "0x9b70"),
		(4, 0x9da2, "0x9da2"),
		(4, 0x9e53, "0x9e53"),		# @0x8d51,0x8edb -> 220f
		(4, 0x9e7a, "0x9e7a"),
		(4, 0xa0d4, "0xa0d4"),
		(4, 0xa23f, "0xa23f"),
		(4, 0xa3e3, "0xa3e3"),
		(4, 0xaba9, "0xaba9"),
		(4, 0xabef, "0xabef"),
		(4, 0xb8ad, "0xb8ad"),
		(4, 0xb8cc, "0xb8cc"),
		(4, 0xc1e3, "0xc1e3"),
		(4, 0xc239, "NULL"),
		(4, 0xc242, "MEMCMP"),
		(4, 0xc285, "MEMCPY"),
		(4, 0xc418, "0xc418"),
		(4, 0xc7b0, "0xc7b0"),
		(4, 0xc855, "0xc855"),
		(4, 0xc885, "0xc885"),
		(4, 0xc973, "0xc973"),
		(4, 0xcb10, "0xcb10"),
		(4, 0xcc09, "0xcc09"),
		(4, 0xccb5, "0xccb5"),
		(4, 0xccff, "0xccff"),
		(4, 0xcd50, "0xcd50"),
		(4, 0xd022, "0xd022"),
		(4, 0xd17d, "0xd17d"),
		(4, 0xd2c6, "0xd2c6"),
		(4, 0xd37d, "NUM="),
		(4, 0xd3c6, "NUM-"),
		(4, 0xd392, "NUM+"),
		(4, 0xd57c, "0xd57c"),
		(4, 0xd71d, "LCD_WR_CTRL"),
		(4, 0xd73f, "LCD_WR_DATA"),
		(4, 0xd761, "LCD_RD_DATA"),
		(4, 0xd781, "LCD_RD_CTRL"),
		(4, 0xd7a0, "LCD_DDRAM"),
		(4, 0xd8ea, "DISPLAY"),
		(4, 0xd989, "DISPLAY2L"),
		(4, 0xd9e6, "LCD_INIT"),
		(4, 0xdae0, "BANKSWITCH"),
		(4, 0xdb2b, "CALL_BANK"),
		(4, 0xdc7b, "RAM_ROM_TEST"),
		(4, 0xdc82, "RAM_TEST"),
		(4, 0xdca9, "ROM_SUM"),
		(4, 0xdd1e, "APP_JMP"),
		(4, 0xdeb6, "0xdeb6"),
		(4, 0xe029, "0xe029"),
		(4, 0xe185, "0xe185"),
		(4, 0xe319, "0xe319"),
		(4, 0xe69c, "0xe69c"),
		(4, 0xe8a7, "0xe8a7"),
		(4, 0xf02a, "0xf02a"),
		(4, 0xf044, "0xf044"),
		(4, 0xf1d9, "0xf1d9"),
		(4, 0xf3f0, "0xf3f0"),
		(4, 0xf7ec, "0xf7ec"),
		(4, 0xf9d4, "0xf9d4"),
		(4, 0xfd50, "PROLOGUE"),

		(6, 0x0300, "LCD_CTL"),
		(6, 0x0301, "LCD_DATA"),
		(6, 0x2223, "MAIN_MENU_LAST_PG"),
		(6, 0x2240, "MENU_PTR"),
		(6, 0x2245, "MAIN_MENU_CUR_PG"),
		(6, 0x2242, "MENU_CNT"),
		(6, 0x247b, "CUR_BANK"),
		(6, 0x247c, "APP_BANK"),
		(6, 0x247d, "APP_VECTOR"),
		(6, 0x3ffc, "OPTIONS"),
		(6, 0xed11, "blank_line"),
	]:
		if p == pj.pg:
			assert a >= pj.m.lo and a < pj.m.hi
			cpu.disass(pj, a)
		if p == pj.pg or p >= 4:
			pj.set_label(a, n)


#######################################################################

def romsum(pj):
	b = 0
	c = 0
	for x in range(pj.m.lo, pj.m.hi):
		b += pj.m.rd(x) + c
		c = b >> 8
		c = 1
		b &= 0xff
	print("CKSUM(0x%04x-0x%04x) = 0x%x" % (pj.m.lo, pj.m.hi, b))

	if pj.pg == 0:
		y = data.Const(pj, 0x4002, 0x4003)
		pj.set_label(y.lo, "EPROM_PAGES")

	if pj.pg < 4:
		assert b == pj.pg

		y = data.Const(pj, 0x4001, 0x4002)
		pj.set_label(y.lo, "EPROM_SUM_%d" % pj.pg)

		y = data.Const(pj, 0x4000, 0x4001, "'%c'")
		assert pj.m.rd(y.lo) == 0x30 + pj.pg
		pj.set_label(y.lo, "EPROM_PAGE_%d" % pj.pg)

	else:
		assert b == 0

#######################################################################

def lexer(pj):

	assert pj.pg == 4

	class lex(data.Data):
		def __init__(self, pj, lo, pfx):
			hi = lo + 4
			self.f = pj.m.rd(lo + 1)
			self.t = pj.m.bu16(lo + 2)
			self.pfx = pfx + "%c" % pj.m.rd(lo)
			if self.f > 0:
				hi += 1
			super(lex, self).__init__(pj, lo, hi, "lex")
			if self.f > 0 and self.pfx in hpib:
				self.lcmt += hpib[self.pfx] + "\n"
			self.compact = True
			if self.f > 0:
				pj.set_label(self.t, "J_" + self.pfx)
				cpu.disass(pj, self.t)

		def render(self, pj):
			s = ".LEX\t\"%s\", " % self.pfx
			s += "%d, " % pj.m.rd(self.lo + 1)
			s += pj.render_adr(pj.m.bu16(self.lo + 2))
			if self.f:
				s += ", 0x%02x" % pj.m.rd(self.lo + 4)
			return s

	def tx(a, pfx):
		t0 = a
		while pj.m.rd(a) != 0:
			y = lex(pj, a, pfx)
			a = y.hi
			if y.f == 0:
				b = pj.m.bu16(y.lo + 2)
				p = pfx + "%c" % pj.m.rd(y.lo)
				pj.set_label(b, "LEX_" + p)
				tx(b, p)
		data.Const(pj, a, a + 1)

	pj.set_label(0x9780, "LEXTAB_ALPHABET")
	n = 65
	for i in range(0x9780, 0x97b4, 2):
		data.Dataptr(pj, i, i + 2, pj.m.bu16(i))
		a = pj.m.bu16(i)
		if n != 0x5a:
			pj.set_label(a, "LEX_%c" % n)
		else:
			pj.set_label(a, "LEX_NULL")
		tx(a, "%c" % n)
		n += 1

	pj.set_label(0x9a22, "LEXTAB_OTHER")
	tx(0x9a22, "")

#######################################################################
# Switch statements

def do_switch():
	retval=False
	for i in pj:
		if i.tag != "mc6809":
			continue
		if pj.m.bu16(i.lo) != 0x6e9b:
			continue
		for j in pj.gaps():
			if j[0] == i.hi:
				break
		if j[0] != i.hi:
			continue
		print("SWITCH", i, "%04x-%04x" % (j[0], j[1]))
		retval=True
		for k in range(j[0], j[1], 2):
			# print("  %04x" % k)
			x = pj.t.find_lo(k)
			if len(x) > 0:
				break
			x = pj.m.bu16(k)
			i.add_flow(pj, ">JC", "EQ", x, i.lang)
			cpu.disass(pj, x)
			while pj.run():
				pass
		for l in range(j[0], k + 2, 2):
			cpu.codeptr(pj, l)
	return retval

#######################################################################

class Num(data.Data):
	def __init__(self, pj, lo):
		super(Num, self).__init__(pj, lo, lo + 3, "Num")
		a = pj.m.rd(lo) << 16
		a += pj.m.rd(lo + 1) << 8
		a += pj.m.rd(lo + 2)
		self.fmt = ".NUM\t%d" % a
		pj.set_label(lo, "N%d" % a)

#######################################################################

class MenuPage(data.Data):
	def __init__(self, pj, cpu, lo):
		super(MenuPage, self).__init__(pj, lo, lo + 10, "MenuPage")
		t = pj.m.bu16(lo)
		y1 = data.Txt(pj, t, t + 40, label=False)
		y1.compact = True
		y2 = data.Txt(pj, t + 40, t + 80, label=False)
		y2.compact = True
		self.t1 = y1.txt
		self.t2 = y2.txt
		self.ptr = []
		for i in range(1, 5):
			u = pj.m.bu16(lo + 2 * i)
			self.ptr.append(u)
			if u >= pj.m.lo and u < pj.m.hi:
				cpu.disass(pj, u)

	def render(self, pj):
		s = "MENUPAGE {\n"
		s += "\t.txt1 = \"%s\"\n" % self.t1
		s += "\t.txt2 = \"%s\"\n" % self.t2
		for i in range(4):
			s += "\t.f%d = " % (i + 1)
			s += "%s\n" % pj.render_adr(self.ptr[i])
		s += "}"
		return s

def Menu(pj, cpu, a, nm):
	pj.set_label(a, nm)
	data.Const(pj, a - 1, a)
	n = pj.m.rd(a - 1)
	for i in range(0, n + 1):
		MenuPage(pj, cpu, a + i * 10)

#######################################################################

def hints(pj, cpu):

	if pj.pg == 0:
		Menu(pj, cpu, 0x433e, "CHANMENU")

		# @0x8948
		data.Const(pj, 0x4003, 0x4004)

		# @0x8954
		for a in range(0x4004,0x4008,2):
			cpu.codeptr(pj, a)

		# @0x8960
		for a in range(0x4008,0x4018,2):
			cpu.codeptr(pj, a)

		for a in range(0x4018, 0x4022, 2):
			y = data.Dataptr(pj, a, a + 2, pj.m.bu16(a))
			u = pj.m.bu16(a)
			y = data.Txt(pj, u, u + 40, label=False)
			y.compact = True

		# @8e1a, @8f08
		for a in range(0x4022,0x4026,2):
			cpu.codeptr(pj, a)

		# @0xc4a5, @0xc318
		for a in range(0x404f,0x4053,2):
			cpu.codeptr(pj, a)

		for a in (0x4027, 0x411b, 0x4143, 0x416b, 0x4193):
			y = data.Txt(pj, a, a + 0x28, label=False)
			y.compact = True

		y = data.Txt(pj, 0x41bb, 0x41bb + 12, label=False)
		y.compact = True


	if pj.pg == 1:
		Menu(pj, cpu, 0x416b, "TONEMENU")
		Menu(pj, cpu, 0x4234, "DTMFMENU")

		for a in (0x69a6,):
			y = data.Txt(pj, a, a + 0x28, label=False)
			y.compact = True
		for a in (0x4142,0x4156):
			y = data.Txt(pj, a, a + 0x14, label=False)
			y.compact = True
		for a in range(0x43bc, 0x43f2, 3):
			data.Const(pj, a, a + 3)

	if pj.pg == 2:
		Menu(pj, cpu, 0x416b, "DSEQMENU")
		for a in range(0x4245, 0x4255, 2):
			cpu.codeptr(pj, a)
		for a in range(0x4330, 0x4340, 2):
			cpu.codeptr(pj, a)

	if pj.pg == 3:
		Menu(pj, cpu, 0x4178, "DIAGMENU")
		MenuPage(pj, cpu, 0x4196)
		for i in range(0x3f):
			a = 0x7349 + 4 * i
			y = data.Const(pj, a, a + 2)
			y.typ = ".BYTE"
			y.fmt = "%d, %d" % (pj.m.rd(a), pj.m.rd(a + 1))
			u = pj.m.bu16(a + 2)
			l = pj.m.rd(a + 1)
			data.Dataptr(pj, a + 2, a + 4, pj.m.bu16(a + 2))
			y = data.Txt(pj, u, u + l, label=False)
			y.compact = True
		for a,b in (
			(0x4002,53),
			(0x41a0,40),
			(0x41c8,0x1a),
			(0x41e2,40),
			(0x420a,40),
			(0x4232,16),
			(0x4242,16),
			(0x4252,40),
			(0x4292,0x1a),
			(0x42ac,40),
			(0x42d4,0x1a),
			(0x42ee,0x1a),
			(0x4308,40),
			(0x4330,40),
			(0x4358,40),
			(0x4386,0x1a),
			(0x43a0,12),
			(0x43ac,40),
			(0x43d4,40),
			(0x43fc,0x1a),
			(0x4416,40),
			(0x443e,40),
			(0x4466,6),
			(0x66fa,16),
			(0x670a,40),
			(0x6732,40),
			(0x675a,40),
			(0x6782,40),
			(0x67aa,40),
			(0x67d2,40),
			(0x67fa,40),
			(0x681a,40),
			(0x6822,40),
		):
			y = data.Txt(pj, a, a + b, label=False)
			y.compact = True

		for a in range(0x63b2, 0x66fa, 40):
			y = data.Txt(pj, a, a + 40, label=False)
			y.compact = True

		a = 0x4c64
		while a < 0x4dcb:
			y = data.Txt(pj, a)
			y.compact = True
			a = y.hi

		a = 0x54cf
		while a < 0x550d:
			y = data.Txt(pj, a)
			y.compact = True
			a = y.hi

		a = 0x624d
		while a < 0x63a4:
			y = data.Txt(pj, a)
			y.compact = True
			a = y.hi


	if pj.pg == 4:
		data.Const(pj, 0xfd6e, 0xfd70)
		for a in range(0xee62, 0xee88, 2):
			u = pj.m.bu16(a)
			y = data.Dataptr(pj, a, a + 2, u)
			y = data.Const(pj, u, u + 1)
			y = data.Txt(pj, u + 1, u + 1 + pj.m.rd(u), label=False)
			y.compact = True
		for a in range(0xeeee, 0x0ef0e, 2):
			u = pj.m.bu16(a)
			y = data.Dataptr(pj, a, a + 2, u)
			y = data.Const(pj, u, u + 1)
			y = data.Txt(pj, u + 1, u + 1 + pj.m.rd(u), label=False)
			y.compact = True
		for a in range(0xef94, 0xf014, 8):
			y = data.Const(pj, a, a + 8, fmt="0x%02x")

		for a,b in (
			(0x8f7c,35),
			(0x977b, 5),
			(0xed11,40),
			(0xea99,0x23),
			(0xeae4,13),
			(0xeb41,40),
			(0xeb69,40),
			(0xec5b,14),
			(0xec69,14),
			(0xec77,14),
			(0xec85,0x36),
			(0xecbb,6),
			(0xecc1,40),
			(0xece9,40),
		):
			y = data.Txt(pj, a, a + b, label=False)
			y.compact = True

		def char_def(pj, a):
			for i in range(8):
				y = data.Data(pj, a + i, a + i + 1)
				x = pj.m.rd(a + i)
				y.fmt = ".BITS\t"
				for j in range(8):
					if x & 0x80:
						y.fmt += "#"
					else:
						y.fmt += "-"
					x = x << 1

		l = [ "LCD_CHR_f", "LCD_CHR_1", "LCD_CHR_2", "LCD_CHR_3",
		      "LCD_CHR_4", "LCD_CHR_phi", "LCD_CHR_mu", "LCD_CHR_is", ]
		for a in range(0xea15, 0xea4e, 8):
			pj.set_label(a, l.pop(0))
			char_def(pj, a)

		data.Const(pj, 0x929d, 0x929d + 8)
		data.Const(pj, 0x9777, 0x9777 + 4)
		data.Const(pj, 0xdd73, 0xdd9d)

		# 2 x 35 bytes, no idea...
		for a in range(0xed89, 0xedcf, 5):
			data.Const(pj, a, a + 5, "0x%02x")

		for a in range(0xee47, 0xee62, 3):
			Num(pj, a)

		for a in (0xea55, 0xea58, 0xea5f, 0xea62, 0xea65,
		    0xea68, 0xea6b, 0xea6e):
			Num(pj, a)


#######################################################################
# Function prologues

def prologues(pj, cpu):
	for i in pj:
		if i.tag != "mc6809":
			continue
		if i.dstadr != 0xfd50:
			continue
		j = pj.t.find_hi(i.lo)
		if len(j) == 0:
			print("NO PROLOGUE %04x" % i.lo, i)
			continue
		if pj.m.rd(j[0].lo) == 0xfc:
			j[0].mne="ldd__"
			u = pj.m.bu16(j[0].lo + 1)
			v = pj.m.bu16(u)
			j[0].mne="ldd__%d" % v
			data.Const(pj, u, u + 1)
			data.Const(pj, u + 1, u + 2)

#######################################################################

for pg in (0,1,2,3,4):

	pj,m = setup(pg)

	romsum(pj)

	cpu = mc6809.mc6809()

	hints(pj, cpu)

	symb(pj, cpu)

	if pj.pg == 4:
		lexer(pj)
		cpu.vectors(pj)

	while pj.run():
		pass

	while do_switch():
		continue

	while pj.run():
		pass

	prologues(pj, cpu)

	code.lcmt_flows(pj)

	listing.Listing(pj)

	import example2

	example2.analyse(pj)

	pj.name = pj.name + "_A"

	listing.Listing(pj)
