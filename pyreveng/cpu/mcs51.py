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
# 2. Redistributions in binary fo rm  must reproduce the above copyright
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
Disassembler for Intel mcs-51 microprocessor family
"""

from __future__ import print_function

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join("..")))

import pyreveng
import instree
import assy
import binutils

mcs51_instructions = """

#			|. . . . . . . .|. . . . . . . .|
ACALL	a11,>C	| ahi |1 0 0 0 1| alo		|

ADD	A,Rn		|0 0 1 0 1| rn  |
ADD	A,adir		|0 0 1 0 0 1 0 1| adir		|
ADD	A,@Ri		|0 0 1 0 0 1 1|i|
ADD	A,#data		|0 0 1 0 0 1 0 0| data		|

ADC	A,Rn		|0 0 1 1 1| rn  |
ADC	A,adir		|0 0 1 1 0 1 0 1| adir		|
ADC	A,@Ri		|0 0 1 1 0 1 1|i|
ADC	A,imm		|0 0 1 1 0 1 0 0| imm		|

AJMP	a11,>J		| ahi |0 0 0 0 1| alo		|

ANL	A,Rn		|0 1 0 1 1| rn  |
ANL	A,adir		|0 1 0 1 0 1 0 1| adir		|
ANL	A,@Ri		|0 1 0 1 0 1 1|i|
ANL	A,#data		|0 1 0 1 0 1 0 0| data		|

ANL	adir,A		|0 1 0 1 0 0 1 0| adir		|
ANL	adir,#data	|0 1 0 1 0 0 1 1| adir		| data		|
ANL	C,abit		|1 0 0 0 0 0 1 0| abit		|
ANL	C,/abit		|1 0 1 1 0 0 0 0| abit		|

CJNE	A,adir,arel,>JC	|1 0 1 1 0 1 0 1| adir		| arel		|
CJNE	A,#data,arel,>JC	|1 0 1 1 0 1 0 0| data		| arel		|
CJNE	Rn,#data,arel,>JC	|1 0 1 1 1| rn	| data		| arel		|
CJNE	@Ri,#data,arel,>JC	|1 0 1 1 0 1 1|i| data		| arel		|

CLR	A		|1 1 1 0 0 1 0 0|
CLR	C		|1 1 0 0 0 0 1 1|
CLR	abit		|1 1 0 0 0 0 1 0| abit		|

CPL	A		|1 1 1 1 0 1 0 0|
CPL	C		|1 0 1 1 0 0 1 1|
CPL	abit		|1 0 1 1 0 0 1 0| abit		|

DA	A		|1 1 0 1 0 1 0 0|

DEC	A		|0 0 0 1 0 1 0 0|
DEC	Rn		|0 0 0 1 1| rn  |
DEC	adir		|0 0 0 1 0 1 0 1| adir		|
DEC	@Ri		|0 0 0 1 0 1 1|i|

DIV	AB		|1 0 0 0 0 1 0 0|

DJNZ	Rn,arel		|1 1 0 1 1| rn	| arel		|
DJNZ	adir,arel	|1 1 0 1 0 1 0 1| adir		| arel		|

INC	A		|0 0 0 0 0 1 0 0|
INC	Rn		|0 0 0 0 1| rn	|
INC	adir		|0 0 0 0 0 1 0 1| adir		|
INC	@Ri		|0 0 0 0 0 1 1|i|
INC	DPTR		|1 0 1 0 0 0 1 1|

JB	abit,arel,>JC	|0 0 1 0 0 0 0 0| abit		| arel		|
JBC	abit,arel,>JC	|0 0 0 1 0 0 0 0| abit		| arel		|

JC	arel,>JC	|0 1 0 0 0 0 0 0| arel		|

JMP	@A+DPTR		|0 1 1 1 0 0 1 1|

JNB	abit,arel,>JC	|0 0 1 1 0 0 0 0| abit		| arel		|

JNC	arel,>JC	|0 1 0 1 0 0 0 0| arel		|

JNZ	arel,>JC	|0 1 1 1 0 0 0 0| arel		|

JZ	arel,>JC	|0 1 1 0 0 0 0 0| arel		|

LCALL	a16,>C		|0 0 0 1 0 0 1 0| ahi		| alo		|

LJMP	a16,>J		|0 0 0 0 0 0 1 0| ahi		| alo		|

MOV	A,Rn		|1 1 1 0 1| rn	|
MOV	A,adir		|1 1 1 0 0 1 0 1| adir		|
MOV	A,@Ri		|1 1 1 0 0 1 1|i|
MOV	A,#data		|0 1 1 1 0 1 0 0| data		|
MOV	Rn,A		|1 1 1 1 1| rn	|
MOV	Rn,adir		|1 0 1 0 1| rn	| adir		|
MOV	Rn,#data	|0 1 1 1 1| rn	| data		|
MOV	adir,A		|1 1 1 1 0 1 0 1| adir		|
MOV	adir,Rn		|1 0 0 0 1| rn	| adir		|
MOV	adir2,adir	|1 0 0 0 0 1 0 1| adir		| adir2		|
MOV	adir,@Ri	|1 0 0 0 0 1 1|i| adir		|
MOV	adir,#data	|0 1 1 1 0 1 0 1| adir		| data		|
MOV	@Ri,A		|1 1 1 1 0 1 1|i|
MOV	@Ri,adir	|1 0 1 0 0 1 1|i| adir		|
MOV	@Ri,#data	|0 1 1 1 0 1 1|i| data		|

MOV	C,abit		|1 0 1 0 0 0 1 0| abit		|
MOV	abit,C		|1 0 0 1 0 0 1 0| abit		|

MOV	DPTR,#data16	|1 0 0 1 0 0 0 0| dhi		| dlo		|

MOVC	A,@A+DPTR	|1 0 0 1 0 0 1 1|
MOVC	A,@A+PC		|1 0 0 0 0 0 1 1|

MOVX	A,@Ri		|1 1 1 0 0 0 1|i|
MOVX	A,@DPTR		|1 1 1 0 0 0 0 0|
MOVX	@Ri,A		|1 1 1 1 0 0 1|i|
MOVX	@DPTR,A		|1 1 1 1 0 0 0 0|

MUL	AB		|1 0 1 0 0 1 0 0|

NOP	-		|0 0 0 0 0 0 0 0|

ORL	A,Rn		|0 1 0 0 1| rn	|
ORL	A,adir		|0 1 0 0 0 1 0 1| adir		|
ORL	A,@Ri		|0 1 0 0 0 1 1|i|
ORL	A,#data		|0 1 0 0 0 1 0 0| data		|
ORL	adir,A		|0 1 0 0 0 0 1 0| adir		|
ORL	adir,#data	|0 1 0 0 0 0 1 1| adir		| data		|
ORL	C,bit		|0 1 1 1 0 0 1 0| bit		|
ORL	C,/bit		|1 0 1 0 0 0 0 0| bit		|

POP	adir		|1 1 0 1 0 0 0 0| adir		|
PUSH	adir		|1 1 0 0 0 0 0 0| adir		|

RET	>R		|0 0 1 0 0 0 1 0|

RETI	>R		|0 0 1 1 0 0 1 0|

RL	A		|0 0 1 0 0 0 1 1|
RLC	A		|0 0 1 1 0 0 1 1|
RR	A		|0 0 0 0 0 0 1 1|
RRC	A		|0 0 0 1 0 0 1 1|

SETB	C		|1 1 0 1 0 0 1 1|
SETB	abit		|1 1 0 1 0 0 1 0| abit		|

SJMP	arel,>J		|1 0 0 0 0 0 0 0| arel		|

SUBB	A,Rn		|1 0 0 1 1| rn  |
SUBB	A,adir		|1 0 0 1 0 1 0 1| adir		|
SUBB	A,@Ri		|1 0 0 1 0 1 1|i|
SUBB	A,#data		|1 0 0 1 0 1 0 0| data		|

SWAP	A		|1 1 0 0 0 1 0 0|
XCH	A,Rn		|1 1 0 0 1| rn  |
XCH	A,adir		|1 1 0 0 0 1 0 1| adir		|
XCH	A,@Ri		|1 1 0 0 0 1 1|i|
XCHD	A,@Ri		|1 1 0 1 0 1 1|i|

XRL	A,Rn		|0 1 1 0 1| rn	|
XRL	A,adir		|0 1 1 0 0 1 0 1| adir		|
XRL	A,@Ri		|0 1 1 0 0 1 1|i|
XRL	A,#data		|0 1 1 0 0 1 0 0| data		|
XRL	adir,A		|0 1 1 0 0 0 1 0| adir		|
XRL	adir,#data	|0 1 1 0 0 0 1 1| adir		| data		|

"""


class arg_adir(assy.arg_dst):
	def __init__(self, pj, ins):
		self.ins = ins
		ins.dstadr = ins.im.F_adir
		self.dstadr = ins.dstadr
		super(arg_adir, self).__init__(pj, ins.dstadr)

	def render(self, pj):
		s = self.ins.lang.sfr.get(self.dstadr)
		if s != None:
			return s[0]
		return super(arg_adir, self).render(pj)

class arg_adir2(assy.arg_dst):
	def __init__(self, pj, ins):
		self.ins = ins
		ins.dstadr = ins.im.F_adir2
		self.dstadr = ins.dstadr
		super(arg_adir2, self).__init__(pj, ins.dstadr)

	def render(self, pj):
		s = self.ins.lang.sfr.get(self.dstadr)
		if s != None:
			return s
		return super(arg_adir2, self).render(pj)

class arg_a11(assy.arg_dst):
	def __init__(self, pj, ins):
		a = (ins.im.F_ahi << 8) | ins.im.F_alo
		ins.dstadr = (ins.hi & 0xf800) + a
		super(arg_a11, self).__init__(pj, ins.dstadr)

class arg_a16(assy.arg_dst):
	def __init__(self, pj, ins):
		ins.dstadr = (ins.im.F_ahi << 8) | ins.im.F_alo
		ins.dstadr &= ins.lang.amask
		super(arg_a16, self).__init__(pj, ins.dstadr)

class arg_arel(assy.arg_dst):
	def __init__(self, pj, ins):
		a = ins.im.F_arel
		if a & 0x80:
			a -= 256
		ins.dstadr = ins.hi + a
		super(arg_arel, self).__init__(pj, ins.dstadr)

def arg_iri(pj, ins):
	return "@R%d" % ins.im.F_i

def arg_rn(pj, ins):
	return "R%d" % ins.im.F_rn

def arg_data(pj, ins):
	return "#0x%02x" % ins.im.F_data

def arg_data16(pj, ins):
	v = (ins.im.F_dhi << 8) | ins.im.F_dlo
	return "#0x%04x" % v

def arg_abit(pj, ins):
	b = ins.im.F_abit
	if b < 0x80:
		return "0x%02x.%d" % (0x20 + (b >> 3), b & 7)
	r = ins.lang.sfr.get(b & 0xf8)
	if r != None:
		b &= 7
		if len(r) > (b + 1):
			return "%s.%s" % (r[0], r[b + 1])
		else:
			return "%s.%d" % (r[0], b)
	return "b#%0x2x" % b

def arg_anbit(pj, ins):
	return "/" + arg_abit(pj, ins)

class mcs51(assy.instree_disass):
	def __init__(self, lang = "mcs51"):
		super(mcs51, self).__init__(lang, 8)
		self.it.load_string(mcs51_instructions)
		self.args.update( {
			"arel":		arg_arel,
			"a11":		arg_a11,
			"a16":		arg_a16,
			"abit":		arg_abit,
			"/abit":	arg_anbit,
			"adir":		arg_adir,
			"adir2":	arg_adir2,
			"A":		"A",
			"C":		"C",
			"DPTR":		"DPTR",
			"@A+DPTR":	"@A+DPTR",
			"@A+PC":	"@A+PC",
			"@Ri":		arg_iri,
			"Rn":		arg_rn,
			"#data":	arg_data,
			"#data16":	arg_data16,
		})
		self.amask = 0xffff
		self.sfr = {
			0x80:	["P0",
			    "AD0", "AD1", "AD2", "AD3",
			    "AD4", "AD5", "AD6", "AD7"],
			0x81:	["SP"],
			0x82:	["DPL"],
			0x83:	["DPH"],
			0x87:	["PCON"
			    "IDL", "PD", "GF0", "GF1",
			    "4", "5", "6", "SMOD"],
			0x88:	["TCON",
			    "IT0", "IE0", "IT1", "IE1",
			    "TR0", "TF0", "TR1", "TF1"],
			0x89:	["TMOD",
			    "M00", "M10", "CT0", "GATE0",
			    "M01", "M11", "CT1", "GATE1"],
			0x8a:	["TL0"],
			0x8b:	["TL1"],
			0x8c:	["TH0"],
			0x8d:	["TH1"],
			0x90:	["P1", "T2", "T2EX"],
			0x98:	["SCON",
			    "RI", "TI", "RB8", "TB8",
			    "REN", "SM2", "SM1", "SM0"],
			0x99:	["SBUF"],
			0xa0:	["P2",
			    "A8", "A9", "A10", "A11",
			    "A12", "A13", "A14", "A15"],
			0xa8:	["IE",
			    "EX0", "ET0", "EX1", "ET1",
			    "ES", "5", "6", "EA"],
			0xb0:	["P3",
			    "Rxd", "Txd", "_INT0", "_INT1",
			    "T0", "T1", "_WR", "_RD"],
			0xb8:	["IP",
			    "PX0", "PT0", "PX1", "PT1", "PS"],
			0xd0:	["PSW",
			    "P", "1", "OV", "RS0",
			    "RS1", "F0", "AC", "CY"],
			0xe0:	["ACC"],
			0xf0:	["B"],
		}

	def set_adr_mask(self, a):
		self.amask = a

	def vectors(self, pj):
		pj.todo(0x000, self.disass)
		pj.set_label(0x000, "RESET")
		pj.todo(0x003, self.disass)
		pj.set_label(0x003, "IE0")
		pj.todo(0x00b, self.disass)
		pj.set_label(0x00b, "TF0")
		pj.todo(0x013, self.disass)
		pj.set_label(0x013, "IE1")
		pj.todo(0x01b, self.disass)
		pj.set_label(0x01b, "TF1")
		pj.todo(0x023, self.disass)
		pj.set_label(0x01b, "RI_TI")

class i8032(mcs51):
	def __init__(self):
		super(i8032, self).__init__("i8032")
		self.sfr[0xc8] = ["T2CON",
		    "CP_RL2", "C_T2", "TR2", "EXEN2",
		    "TCLK", "RCLK", "EXF2", "TF2" ]
		self.sfr[0xc9] = ["T2MOD"]
		self.sfr[0xca] = ["RCAP2L"]
		self.sfr[0xcb] = ["RCAP2H"]
		self.sfr[0xcc] = ["TL2"]
		self.sfr[0xcd] = ["TH2"]
		self.sfr[0xd8] = ["WDTCON"]
