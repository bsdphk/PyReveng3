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

import math

import pyreveng
import mem
import cpu.mc6800
import code
import data

#----------------------------------------------------------------------

cmd_desc = {
	"FN1":  "Time Interval",
	"FN2":  "Trigger Levels",
	"FN3":  "Frequency",
	"FN4":  "Period",
	"FN5":  "*extension*",
	"GT1":  "Single Period",
	"GT2":  "0.01s",
	"GT3":  "0.1s",
	"GT4":  "1s",
	"ST1":  "Mean",
	"ST2":  "StdDev",
	"ST3":  "Min",
	"ST4":  "Max",
	"ST5":  "Disp Ref",
	"ST6":  "Clr Ref",
	"ST7":  "Disp Evts",
	"ST8":  "Set Ref",
	"ST9":  "Disp All",
	"SS1":  "Sample Size = 1",
	"SS2":  "Sample Size = 100",
	"SS3":  "Sample Size = 1k",
	"SS4":  "Sample Size = 10k",
	"SS5":  "Sample Size = 100k",
	"MD1":  "FP Rate",
	"MD2":  "Hold until MR",
	"MD3":  "Fast",
	"MD4":  "Fast + SRQ",
	"IN1":  "Input: Start+Stop",
	"IN2":  "Input: Stop+Stop",
	"IN3":  "Input: Start+Start",
	"IN4":  "Input: Stop+Start",
	"SA1":  "Start Pos",
	"SA2":  "Start Neg",
	"SO1":  "Stop Pos",
	"SO2":  "Stop Neg",
	"SE1":  "Arm Pos",
	"SE2":  "Arm Neg",
	"AR1":  "+T.I. Arming Only",
	"AR2":  "+T.I. Arming",
	"EH0":  "Ext Holdoff dis",
	"EH1":  "Ext Holdoff ena",
	"EA0":  "Ext Arm dis",
	"EA1":  "Ext Arm ena",
	"IA1":  "Internal Arm Auto",
	"IA2":  "Start Chan Arm",
	"IA3":  "Stop Chan Arm",
	"MR":   "Manual Rate",
	"MI":   "Manual Input",
	"SL":   "Slope Local",
	"SR":   "Slope Remote",
	"TL":   "Trigger Local",
	"TR":   "Trigger Remote",
	"TE":   "Teach",
	"PC":   "Period Complement",
	"TB0":  "Ascii",
	"TB1":  "Binary",
	"SB":   "Sample Size Binary",
	"LN":   "Learn",
	"TA":   "Trigger Start",
	"TO":   "Trigger Stop",
}

#----------------------------------------------------------------------
# We prefer to label the JMP-tables at front of EPROMS, as they are
# quite constant between version

hp5370_lbls = [
	#-----
	(0x080, 0x080,	"S[3]"),
	(0x086, 0x086,	"S[3].e"),
	(0x087, 0x087,	"S[2]"),
	(0x08d, 0x08d,	"S[2].e"),
	(0x08e, 0x08e,	"S[1]"),
	(0x094, 0x094,	"S[1].e"),
	(0x095, 0x095,	"S[0]"),
	(0x09b, 0x09b,	"S[0].e"),
	(0x09c, 0x09c,	"S[-1]"),
	(0x0a2, 0x0a2,	"S[-1].e"),
	(0x0b6, 0x0b6,	"MODE"),
	(0x0bd, 0x0bd,	"NSAMP_SB[H]"),
	(0x0be, 0x0be,	"NSAMP_SB[M]"),
	(0x0bf, 0x0bf,	"NSAMP_SB[L]"),
	(0x0c0, 0x0c0,	"REFPTR"),
	(0x0e8, 0x0e8,  "EVTCNT[H]"),
	(0x0e9, 0x0e9,  "EVTCNT[M]"),
	(0x0ea, 0x0ea,  "EVTCNT[L]"),
	(0x0ed, 0x0ed,  "LED1_68"),
	(0x0ee, 0x0ee,  "LED2_6a"),
	(0x0ef, 0x0ef,  "LED3_6c"),
	(0x0f0, 0x0f0,  "LED4_6e"),
	(0x0fa, 0x0fa,  "REF_FREQ_PER"),
	(0x101, 0x101,  "REF_TI"),
	(0x108, 0x108,  "REF_?1"),
	(0x10f, 0x10f,  "REF_?2"),
	(0x116, 0x116,	"MAX_VAL"),
	(0x11d, 0x11d,	"MIN_VAL"),
	(0x124, 0x124,	"SIGMA"),
	(0x12b, 0x12b,	"SQSIGMA"),
	(0x132, 0x132,	"EVT"),
	(0x139, 0x139,	"COUNT"),
	#-----

	#-----
        (0x6003,	0x6003, "X=PARAM(CUR)"),
        (0x6006,	0x6006, "Delay(X)"),
        (0x600c,	0x600c, "LED_BLANK()"),
        (0x6015,	0x6015, "HPIB_SEND_TRIG_LVL(X)"),
        (0x6018,	0x6018, "S[0]*=10.0()"),
        (0x601b,	0x601b, "CLK_TO_TIME()"),
        (0x601e,	0x601e, "SHOW_RESULT()"),
        (0x6027,	0x6027, "GPIB_RX_ONE()"),
        (0x602a,	0x602a, "TIMEBASE_TO_HPIB()"),
        (0x602d,	0x602d, "CHK_PLL_LOCK()"),
        (0x6030,	0x6030, "LedFillMinus()"),
        (0x6033,	0x6033, "ERR2_TI_OVERRANGE"),
        (0x6039,	0x6039, "LED=LEDBUF()"),
        (0x603f,	0x603f, "X+=A()"),
        (0x6048,	0x6048, "LED=0.00"),
        (0x6054,	0x6054, "CMD(X+A)"),
	#-----

        (None,	0x608d, "LED_BLANK()"),
        (None,	0x608f, "LED_FILL(A)"),
        (None,	0x623e, "ERR4_PLL_UNLOCK"),
        (None,	0x63df, "ERR3_UNDEF_ROUTINE"),
        (None,	0x66ea, "ERR5_UNDEF_KEY"),
        (None,	0x6501, "SET_SS_GT"),

	#-----
        (0x680f,	0x680f, "REF_VALUE=AVG()"),
        (0x6812,	0x6812, "REF_VALUE=0.0()"),
        (0x6815,	0x6815, "SET_REFPTR"),
	#-----


        (None,		0x6b3b, "GET_EVENTS"),
        (None,		0x6b5b, "NEXT_EVENT"),
        (0x6918,	0x6918, "REF_ADJ()"),

	#-----
        (0x7003,	0x7003, "PUSH(?*X)"),
        (0x7006,	0x7006, "*X=S[0]"),
        (0x7009,	0x7009, "Swap(S[0],S[1])"),
        (0x700c,	0x700c, "DUP()"),
        (0x700f,	0x700f, "DROP()"),
        (0x7015,	0x7015, "ROLL()"),
        (0x7018,	0x7018, "ADD()"),
        (0x701b,	0x701b, "SUB()"),
        (0x701e,	0x701e, "MULTIPLY()"),
        (0x7021,	0x7021, "DIVIDE()"),
        (0x7024,	0x7024, "SQRT()"),
        (0x7027,	0x7027, "NEGATE()"),
        (0x702a,	0x702a, "S[0]=0.0()"),
        (0x702d,	0x702d, "NORMRIGHT(*X,A)"),
        (0x7030,	0x7030, "NORMLEFT(*X,A)"),
        (0x7036,	0x7036, "S[1].m+=S[0].m()"),
        (0x7039,	0x7039, "S[1].m-=S[0].m()"),
        (0x703c,	0x703c, "NORM(S[0],S[1])"),
        (0x703f,	0x703f, "NORM(S[1])"),
        (0x7042,	0x7042, "LED_ERR(A)"),
	#-----

        (0x7069,	0x7069, "memcpy(*0xae,*0xac,7)"),

        (None,	0x7115, "A=OR(S[0].m)"),
        (None,	0x7122, "A=OR(S[1].m)"),
        (None,	0x7277, "S[1]==S[0]?()"),
        (None,	0x7356, "S[1]=0.0()"),
        (None,	0x6d5f, "SET_OFLOW_1()"),
        (None,	0x73c3, "SET_OFLOW_2()"),

	#-----
        (0x7403,	0x7403, "RESULT_TO_GPIB()"),
        (0x740c,	0x740b, "FLOAT_FMT()"),
	#-----

        (None,	0x76e6, "ERR1_UNDEF_CMDa"),
        (None,	0x7716, "LED_TO_GPIB()"),
        (None,	0x798c, "UPDATE_LAMPS()"),
        (None,	0x790c, "LAMP_TEST()"),
        (None,	0x790f, "HPIB_RECV(*X,A)"),
        (None,	0x7912, "HPIB_SEND(*X,A)"),
        (None,	0x7918, "FAST_BINARY()"),
        (None,	0x7936, "KEY_PRELL"),
        (None,	0x7987, "GET_FN()"),
        (None,	0x7a69, "*X=NIBBLES(A)"),
        (None,	0x7b38, "EXIT_FAST_BINARY"),
        (None,	0x7bc6, "RESET_STACK_MAIN"),
        (None,	0x7cb2, "SP?"),
        (None,	0x7cb8, "COMMA?"),
        (None,	0x7cbc, "CR?"),
        (None,	0x7cc0, "NL?"),
        (None,	0x7ccb, "TOLOWER"),
        (None,	0x7ccd, "BELOW_A?"),
        (None,	0x7cd1, "ABOVE_Z?"),
        (None,	0x7d19, "ERR1_UNDEF_CMDb"),
        (None,	0x7d21, "CMD_FOUND"),
        (None,	0x7d3f, "BELOW_0"),
        (None,	0x7d43, "ABOVE_9"),
        (0x7de1,	0x7de8, "ERR6.N"),
        (None,	0x7df8, "ERRN.M"),
        (0x7e39,	0x7e40, "ROMTEST"),
        (None,	0x7ec5, "WR_TEST"),
        (None,	0x7eff, "DISPLAYTEST"),
        (None,	0x7f24, "RD_TEST"),
        (0x7d9c,	0x7f4a, "TEST_LOOP"),
]

#----------------------------------------------------------------------

def apply_labels(pj, type):
	if type == "A":
		i = 0
	elif type == "B":
		i = 1
	else:
		raise "Wrong Type"
	for j in hp5370_lbls:
		if j[i] != None:
			pj.set_label(j[i], j[2])
		else:
			print("No address", pj.afmt(j[1-i]), j[2])
			

#----------------------------------------------------------------------
def setup(name, binfile, direction):
	print("\n\nDoing: " + binfile)
	m = mem.byte_mem(0x6000, 0x8000)
	if direction == 1:
		m.load_binfile(0x6000, 1, binfile)
	else:
		m.load_binfile(0x7fff, -1, binfile)
	pj = pyreveng.job(m, name)
	cx = cpu.mc6800.mc6800(mask = 0x7fff)
	eprom(pj, cx.disass, m.lo, m.hi, 0x0400)

	cx.vectors(pj, 0x7ff8)
	return pj,cx

#----------------------------------------------------------------------
# Structure of (virtual) EPROMS
#
def one_eprom(pj, disass, start, eprom_size):

	# Calculate checksum
	j = 0 ^ pj.m.bu16(start)
	for jj in range(2, eprom_size):
		j += pj.m.rd(start + jj)
	j &= 0xffff
	if j == 0xffff:
		j = "OK"
	else:
		print("NB: Bad Eprom checksum @%x" % start)
		j = "BAD"

	c = pj.add(start, start + eprom_size, "EPROM")

	c = pj.add(start, start + 2, "u16")
	c.rendered = ".WORD 0x%04x" % pj.m.bu16(start)
	c.lcmt = "EPROM checksum (%s)" % j

	c = pj.add(start + 2, start + 3, "byte")
	c.rendered = ".BYTE 0x%02x" % pj.m.rd(start + 2)
	c.lcmt = "EPROM ID"

	# Jump table at front of EPROM
	for ax in range(start + 3, start + eprom_size, 3):
		if pj.m.rd(ax) != 0x7e:
			break
		pj.todo(ax, disass)

def eprom(p, disass, start, end, sz):
	lx = list()
	for ax in range(start, end, sz):
		lx.append(ax >> 8)
		lx.append(ax & 0xff)
		one_eprom(p, disass, ax, sz)
	lx.append(end >> 8)
	lx.append(end & 0xff)
	return

	# Find the table of eprom locations
	l = p.m.find(start, end, lx)
	print("EPROM", l)
	assert len(l) == 1
	x = p.t.add(l[0], l[0] + len(lx), "tbl")
	x.blockcmt += "-\nTable of EPROM locations"
	for ax in range(x.start, x.end, 2):
		const.w16(p, ax)
	(None,	l[0], "EPROM_TBL")

def cmd_tbl(pj, start, end):
	x = pj.add(start, end, "CMD_TABLE")
	pj.set_label(start, "CMD_TABLE")
	l = list()
	for a in range(start, end, 2):
		s = ""
		for i in range(2):
			j = pj.m.rd(a + i)
			if i == 1 and j == 0:
				pass
			elif j <= 32 or j > 126:
				s += "\\x%02x" % j
			else:
				s += "%c" % j
		x = pj.add(a, a + 2, "string")
		x.rendered = ".TXT\t'%s'" % s
		l.append(s)
	return l

def arg_range(pj, cmds, start, end):
	x = pj.add(start, end, "ARG_RANGE")
	pj.set_label(start, "ARG_RANGE")
	l = list()
	n = 0
	for a in range(start, end, 2):
		c = cmds[n]
		n += 1
		lo = pj.m.rd(a)
		hi = pj.m.rd(a + 1)
		x = pj.add(a, a + 2, "byte")
		x.rendered = ".BYTE\t0x%02x, 0x%02x" % (lo, hi)
		x.lcmt = c + "[%d" % lo + "-%d]" % hi
		for j in range(lo, hi + 1):
			l.append(c + "%d" %j)
	for j in cmds[n:]:
		l.append(j)
	return l

def cmd_dispatch(pj, cx, cmds, start):
	a = start
	for i in cmds:
		c = cx.codeptr(pj, a)
		if i in cmd_desc:
			c.lcmt = cmd_desc[i]
		pj.set_label(c.dst, "CMD_%s" % i)
		a += 2
	x = pj.add(start, a, "CMD_DISPATCH")
	pj.set_label(start, "CMD_DISPATCH")

def key_dispatch(pj, cx, start, end):
	keys = {
		"KEY_C8_R2": "KEY_Ext_Arm",
		"KEY_C7_R3": "KEY_Ext_Hold_Off",
		"KEY_C7_R1": "KEY_Reset",
	}
	assert end == start + 64
	a = start
	for col in range(8, 0, -1):
		# pj.set_label(a, "KEY_COL_%d" % col)
		for row in range(4, 0, -1):
			n = "KEY_C%d_R%d" % (col,row)
			c = cx.codeptr(pj, a)
			if c.dst not in pj.labels:
				if n in keys:
					m = keys[n]
				else:
					print("Unknown Key %s" % n)
					m = n
				pj.set_label(c.dst, m)
			l = pj.labels[c.dst]
			if l[:4] == "CMD_" and l[4:] in cmd_desc:
				c.lcmt = n + " = " + cmd_desc[l[4:]]
			else:
				c.lcmt = n + " = " + pj.labels[c.dst]
			a += 2
	x = pj.add(start, a, "KEY_DISPATCH")
	pj.set_label(start, "KEY_DISPATCH")

def dsp_dispatch(pj, cx, start, end):
	assert start + 16 == end
	x = pj.add(start, end, "DSP_DISPATCH")
	pj.set_label(start, "DSP_DISPATCH")
	a = start
	for i in ("AVG", "STD", "MIN", "MAX", "REF", "EVT", "ALL", "ALL"):
		c = cx.codeptr(pj, a)
		pj.set_label(c.dst, "DSP_" + i)
		c.lcmt = "DSP_" + i
		a += 2

class data24(data.const):
	def __init__(self, pj, lo):
		super(data24, self).__init__(pj, lo, lo + 3)
		v = pj.m.rd(self.lo) << 16
		v |= pj.m.rd(self.lo + 1) << 8
		v |= pj.m.rd(self.lo + 2)
		self.val = v
		self.fmt = "%d" % v
		self.typ = ".24bit"
		pj.set_label(lo, "c_" + self.fmt)

class float70(data.const):
	def __init__(self, pj, lo):
		super(float70, self).__init__(pj, lo, lo + 7)
		x = pj.m.rd(self.lo)
		if x & 0x80:
			s = -1
			x ^= 0x80
		else:
			s = 1
		o = -7
		m = 0
		for i in range(6):
			m +=  math.ldexp(x, o)
			o -= 8
			x = pj.m.rd(self.lo + 1 + i)
		e =  pj.m.s8(self.lo + 6)
		self.lcmt = "m %g e %g" % (m, e)
		v = s * math.ldexp(m, e)
		self.val = v

		x = "%.9e" % v
		if x.find(".") == -1 and x.find("e") == -1:
			x += "."
		self.fmt = x
		self.typ = ".FLOAT"
		self.compact = False
		pj.set_label(lo, "c_" + x)
		print(self, self.fmt)
		
def square_tbl(pj):
	for i in range(256):
		x = pj.m.rd(0x6e00 + i)
		y = (i * i) & 0xff
		assert x == y
		x = pj.m.rd(0x6f00 + i)
		y = (i * i) >> 8
		assert x == y
	
	x = pj.add(0x6e00, 0x6f00, "TBL_6E00")
	x.rendered = "FOR I (0..255):\n    .BYTE ((I * I) & 0xff)"
	x.compact = True
	pj.set_label(0x6e00, "SQUARE_TBL_LO")
	
	x = pj.add(0x6f00, 0x7000, "TBL_6F00")
	x.rendered = "FOR I (0..255):\n    .BYTE ((I * I) >> 8)"
	x.compact = True
	pj.set_label(0x6f00, "SQUARE_TBL_HI")

def tramp(pj):
	l = list()
	for i in pj:
		if not isinstance(i, code.code):
			continue
		if len(i.flow_out) != 1:
			continue
		if i.flow_out[0].typ != ">":
			continue
		if i.flow_out[0].cond != True:
			continue
		if i.flow_out[0].to == None:
			continue
		l.append(i)
	while True:
		did = 0
		for i in l:
			da = i.flow_out[0].to
			lx = pj.labels.get(i.lo)
			ly = pj.labels.get(da)
			if lx != None:
				if ly != None:
					assert lx == ly
				else:
					#print(pj.afmt(i.lo), "->", pj.afmt(da), lx)
					pj.set_label(da, lx)
					did += 1
			elif ly != None:
				#print(pj.afmt(i.lo), "<-", pj.afmt(da), ly)
				pj.set_label(i.lo, ly)
				did += 1
		if did == 0:
			break

"""
;-------------------------------------------------------------------------------
; HP5370B ROM disassembly
; =======================
; 
;-------------------------------------------------------------------------------
; 0x0000-0x0003	GPIB BOARD (A15) {See HP5370B manual P8-30}
; 
; 	0x0000:R Data In
; 	0x0000:W Data Out
; 	0x0001:R Inq In
; 	0x0001:W Status Out (P3-18)
; 		0x80 = Running NMI Debug monitor
; 		0x40 = Service Requested
; 		0x20 = Oven heater on
; 		0x10 = External Timebase
; 		0x0f = Error message if bit 7 "is used"
; 	0x0002:R Cmd In
; 	0x0002:W Control Out
; 		0x02 = NMI gate
; 		0x10 = EOI out {0x61e9}
; 	0x0003:R State In
; 
;-------------------------------------------------------------------------------
; 0x0050-0x005f	A16 Arming
; 
; 	0x0050-0x0051:R	LDACSR signal
; 	0x0052-0x0053:R A16U21+A16U15 MUX
; 		0x0052:R A16 Service Switch
; 			0x80 = Loop
; 			0x10 = Read
; 			0x08 = Display
; 			0x04 = Write
; 			0x02 = ROM test
; 			0x01 = RAM test
; 	0x0054-0x0055:R	LEN2 signal
; 		0x0054:R
; 			0x80 = Oven heater ("LOVEN")
; 			0x40 = External Tb ("LEXT")
; 			0x3f = N/C
; 		0x0055:R
; 			0x80 = Event counter range/overflow flag ("HN30R")
; 			0x40 = End of measurement ("LPROC")
; 			0x20 = Sign of N0 ("SIGN")
; 			0x10 = Armed flag ("ERMD")
; 			0x08 = PLL out of lock
; 			0x04 = N0 range/overflow flag
; 			0x03 = 257*(N1-N2) counter bits
; 	0x0056-0x0057:R	LEN1 signal
; 		N0 counter, see TB1 description
; 	0x0058-0x0059:R	LEN0 signal
; 		257*(N1-N2) counter, see TB1 description
; 	0x005a-0x005b:R	A16U17+A16U19 MUX
; 		 Eventcounter
; 	{more}
;-------------------------------------------------------------------------------
; 0x0060-0x007f	DISPLAY BOARD (A11)
; 
; 	0x0060:R Buttons
; 		0xf0: scan lines
; 		0x07: sense lines
; 	0x0060-0x006f:W	LEDS
; 	0x0070-0x007f:W	7segs
; 
;-------------------------------------------------------------------------------
; 0x0080-0x0200	RAM
; 
; 	0x0080-0x0086:	SW \  FLOAT
; 	0x0087-0x008d:	SZ  | stack
; 	0x008e-0x0094:	SY  > SW=top
; 	0x0095-0x009b:	SX  | SX=bot
; 	0x009c-0x00a2:	SA /  SA=spill
; 
; 	0x00ae:	0b.......0: EA0 Ext Arm dis
; 	       	0b.......1: EA1 Ext Arm ena
; 	0x00b6: MODE
; 		0b.....000: FN3 Freq
; 		0b.....001: FN4 Period
; 		0b.....010: FN1 TI
; 		0b.....100: FN2 TrigLevel
; 		0b.....101: FN5 ???
; 		0b..00....: MD1 FP rate
; 		0b..01....: MD2 Hold until MR
; 		0b..10....: MD3 Fast
; 		0b..11....: MD4 Fast+SRQ
; 
; 	0x00b7:
; 		0b....X...: SE[12]
; 		0b......X.: SA[12]
; 		0b.......X: SO[12]
; 	0x00bb:
; 		0b......XX: FP/TI Overflow bits
;		0b....X...: SE[12]
; 	0x00bc:
; 		0b...XX...: IN[14]
;	0x00bd-0x00bf:  Sample size binary (24 bits)
; 	0x00c0-0x00c1:	REFPTR
;	0x00e8-0x00ea:	EVTCNT
; 	0x00f2-0x00f3:	Freq/Period
; 	0x00f4-0x00f5:	TI
; 		0b0....... ........ Ascii Output (TB0)
; 		0b1....... ........ Binary Output (TB1)
; 	0x00f6-0x00f7:	Triglev/FN5
; 		0b........ ....0000 SS1 1 sample
; 		0b........ ....0001 SS2 100 sample
; 		0b........ ....0010 SS3 1k sample
; 		0b........ ....0011 SS4 10k sample
; 		0b........ ....0100 SS5 100k sample
; 		0b........ ....0101 GT2 0.01s
; 		0b........ ....0110 GT3 0.1s
; 		0b........ ....0111 GT4 1s
;		0b........ ....1000 SB (sample size binary)
; 		0b........ .000.... ST1 Mean
; 		0b........ .001.... ST2 Stddev
; 		0b........ .010.... ST3 Min
; 		0b........ .011.... ST4 Max
; 		0b........ .100.... ST5 Disp Ref
; 		0b........ .101.... ST7 Disp Evt
; 		0b........ .111.... ST9 Disp All
; 		0b........ 0....... Ref clear
; 		0b........ 1....... Ref set
; 
; 	0x0116-0x011c:	MAX_VALUE (FLOAT)
; 	0x011d-0x0123:	MIN_VALUE (FLOAT)
; 	0x0124-0x012a:
; 	0x012b-0x0131:
; 	0x0132-0x0138:	#Events ? (FLOAT?)
; 	0x0139-0x013f:
; 
; 	0x0140-0x014f:	Led buffer
; 		0bX.......: DP
; 		0b....XXXX: BCD
; 
; 	0x016c-0x016d: GPIB transmit-pointer
; 	0x016f-0x0182: GPIB output buffer
; 		"...,...,...,.E+##
; "
; 
; 0x4000-?	Possibly Service/Expansion EPROM
; 0x6000-0x7fff	EPROMS
; 
;-------------------------------------------------------------------------------
"""
