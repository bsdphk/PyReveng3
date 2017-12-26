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
Disassembler for MC6809 familiy CPUs.

Presently supported variants:
	6809
"""

from __future__ import print_function

from pyreveng import assy, data

mc6809_instructions = """

+	PFX10	|0 0 0 1 0 0 0 0|

+	PFX11	|0 0 0 1 0 0 0 1|

NEG	d	|0 0 0 0 0 0 0 0| d		| {
	%1 = load i8 , i8* D
	%2 = sub i8 %1 , 1
	store i8 %2 , i8* D
	FLG UXXXX %2 sub %1 1
}

NEG	M	|0 1 1|e|0 0 0 0| m		| {
	%1 = load i8 , i8* M
	%2 = sub i8 %1 , 1
	store i8 %2 , i8* M
	FLG UXXXX %2 sub %1 1
}

COM	d	|0 0 0 0 0 0 1 1| d		| {
	%1 = load i8 , i8* D
	%2 = xor i8 %1 , 0xff
	store i8 %2 , i8* D
	FLG UXX01 %2
}

COM	M	|0 1 1|e|0 0 1 1| m		| {
	%1 = load i8 , i8* M
	%2 = xor i8 %1 , 0xff
	store i8 %2 , i8* M
	FLG UXX01 %2
}

LSR	d	|0 0 0 0 0 1 0 0| d		|

LSR	M	|0 1 1|e|0 1 0 0| m		|

ROR	d	|0 0 0 0 0 1 1 0| d		|

ROR	M	|0 1 1|e|0 1 1 0| m		|

ASR	d	|0 0 0 0 0 1 1 1| d		|

ASR	M	|0 1 1|e|0 1 1 1| m		|

ASL	d	|0 0 0 0 1 0 0 0| d		|

ASL	M	|0 1 1|e|1 0 0 0| m		|

ROL	d	|0 0 0 0 1 0 0 1| d		|

ROL	M	|0 1 1|e|1 0 0 1| m		|

DEC	d	|0 0 0 0 1 0 1 0| d		| {
	%1 = load i8 , i8* D
	%2 = sub i8 %1 , 1
	store i8 %2 , i8* D
	FLG -XXX- %2 sub %1 1
}

DEC	M	|0 1 1|e|1 0 1 0| m		|

INC	d	|0 0 0 0 1 1 0 0| d		| {
	%1 = load i8 , i8* D
	%2 = add i8 %1 , 1
	store i8 %2 , i8* D
	FLG -XXX- %2 add %1 1
}

INC	M	|0 1 1|e|1 1 0 0| m		|

TST	d	|0 0 0 0 1 1 0 1| d		| {
	%1 = load i8 , i8* D
	FLG -XX0- %1
}

JMP	d,>J	|0 0 0 0 1 1 1 0| d		| {
	br label D
}

JMP	M,>J	|0 1 1|e|1 1 1 0| m		|

CLR	d	|0 0 0 0 1 1 1 1| d		| {
	store i8 0 , i8* D
	FLG -0100
}

B	R,CC	|0 0 0 1 0 0 0 0|0 0 1 0| cc    | R1		| R2		| {
	BR
}

SWI2	>J	|0 0 0 1 0 0 0 0|0 0 1 1 1 1 1 1|

CMPD	I	|0 0 0 1 0 0 0 0|1 0 0 0 0 0 1 1| I1		| I2		|

CMPD	d	|0 0 0 1 0 0 0 0|1 0 0 1 0 0 1 1| d		|

CMPD    P	|0 0 0 1 0 0 0 0|1 0 1 0 0 0 1 1|X| R |i| m     |

CMPD	E	|0 0 0 1 0 0 0 0|1 0 1 1 0 0 1 1| e1		| e2		|

SWI3	>J	|0 0 0 1 0 0 0 1|0 0 1 1 1 1 1 1|

CMPU	I	|0 0 0 1 0 0 0 1|1 0 0 0 0 0 1 1| I1		| I2		|

CMPS	I	|0 0 0 1 0 0 0 1|1 0 0 0 1 1 0 0| I1		| I2		|

CMPU	I	|0 0 0 1 0 0 0 1|1 0 0 1 0 0 1 1| d		|

CMPS	I	|0 0 0 1 0 0 0 1|1 0 0 1 1 1 0 0| d		|

CMPU	P	|0 0 0 1 0 0 0 1|1 0 1 0 0 0 1 1|X| R |i| m     |

CMPS	P	|0 0 0 1 0 0 0 1|1 0 1 0 1 1 0 0|X| R |i| m     |

CMPU	E	|0 0 0 1 0 0 0 1|1 0 1 1 0 0 1 1| e1		| e2		|

CMPS	E	|0 0 0 1 0 0 0 1|1 0 1 1 1 1 0 0| e1		| e2		|

NOP	-	|0 0 0 1 0 0 1 0|

SYNC	-	|0 0 0 1 0 0 1 1|

BRA	R,>J	|0 0 0 1 0 1 1 0| R1            | R2		| {
	br label DST
}

BSR	R,>C	|0 0 0 1 0 1 1 1| R1            | R2		| {
	%S = sub i16 %S , 2
	store i16 HI, i16* %S
	br label DST
}

DAA	-	|0 0 0 1 1 0 0 1|

ORCC	i	|0 0 0 1 1 0 1 0| i		|

ANDCC	i	|0 0 0 1 1 1 0 0| i		| {
	%CC = and i8 %CC , I
}

SEX	-	|0 0 0 1 1 1 0 1|

EXG	t	|0 0 0 1 1 1 1 0| t		|

TFR	t	|0 0 0 1 1 1 1 1| t		| {
	TFR
}

B	r,CC	|0 0 1 0| cc    | r		| {
	BR
}

LEAX	P	|0 0 1 1 0 0 0 0|X| R |i| m	|

LEAY	P	|0 0 1 1 0 0 0 1|X| R |i| m	|

LEAS	P	|0 0 1 1 0 0 1 0|X| R |i| m     |

LEAU	P	|0 0 1 1 0 0 1 1|X| R |i| m     |

PSHS	s	|0 0 1 1 0 1 0 0| i		| {
	PUSH S
}

PULS	s	|0 0 1 1 0 1 0 1| i		| {
	PULL S
}

PSHU	s	|0 0 1 1 0 1 1 0| i		| {
	PUSH U
}

PULU	s	|0 0 1 1 0 1 1 1| i		| {
	PULL U
}

RTS	>R	|0 0 1 1 1 0 0 1| {
	%0 = load i16 , i16* %S
	%S = add i16 %S , 2
	br label %0
}

AB	XY,-	|0 0 1 1 1 0 1 0|

RTI	>R	|0 0 1 1 1 0 1 1|

CWAI	i	|0 0 1 1 1 1 0 0| i		|

MUL	-	|0 0 1 1 1 1 0 1|

SWI	-	|0 0 1 1 1 1 1 1|

NEG	AB	|0 1 0|a|0 0 0 0|

COM	AB	|0 1 0|a|0 0 1 1|

LSR	AB	|0 1 0|a|0 1 0 0|

ROR	AB	|0 1 0|a|0 1 1 0|

ASR	AB	|0 1 0|a|0 1 1 1|

ASL	AB	|0 1 0|a|1 0 0 0|

ROL	AB	|0 1 0|a|1 0 0 1|

DEC	AB	|0 1 0|a|1 0 1 0|

INC	AB	|0 1 0|a|1 1 0 0|

TST	AB	|0 1 0|a|1 1 0 1|

CLR	AB	|0 1 0|a|1 1 1 1| {
	AB = i8 0
	FLG -0100
}

TST	M	|0 1 1|e|1 1 0 1| m		|

CLR	M	|0 1 1|e|1 1 1 1| m		|

SUB	AB,i	|1|a|0 0 0 0 0 0| i		| {
	%1 = i8 AB
	AB = sub i8 AB , I
	FLG UXXXX AB sub %1 I
}

CMP	AB,i	|1|a|0 0 0 0 0 1| i		| {
	%2 = sub i8 AB , I
	FLG UXXXX %2 sub AB I
}

SBC	AB,i	|1|a|0 0 0 0 1 0| i		|

SUBD	I	|1 0 0 0 0 0 1 1| I1		| I2		|

ADDD	I	|1 1 0 0 0 0 1 1| I1		| I2		|

AND	AB,i	|1|a|0 0 0 1 0 0| i		|

BIT	AB,i	|1|a|0 0 0 1 0 1| i		|

LD	AB,i	|1|a|0 0 0 1 1 0| i		|

EOR	AB,i	|1|a|0 0 1 0 0 0| i		|

ADC	AB,i	|1|a|0 0 1 0 0 1| i		|

OR	AB,i	|1|a|0 0 1 0 1 0| i		|

ADD	AB,i	|1|a|0 0 1 0 1 1| i		|


CMP	XY,I	|1 0 0 0 1 1 0 0| I1		| I2		|

BSR	r,>C	|1 0 0 0 1 1 0 1| r		| {
	%S = sub i16 %S , 2
	store i16 HI, i16* %S
	br label DST
}

LD	XY,I	|1 0 0 0 1 1 1 0| I1		| I2		| {
	XY = i16 I16
	FLG -XX0- I16
}

SUB	AB,d	|1|a|0 1 0 0 0 0| d		|

CMP	AB,d	|1|a|0 1 0 0 0 1| d		|

SBC	AB,d	|1|a|0 1 0 0 1 0| d		|

SUBD	d	|1 0 0 1 0 0 1 1| d		|

ADDD	d	|1 1 0 1 0 0 1 1| d		|

AND	AB,d	|1|a|0 1 0 1 0 0| d		|

BIT	AB,d	|1|a|0 1 0 1 0 1| d		|

LD	AB,d	|1|a|0 1 0 1 1 0| d		|

ST	AB,d	|1|a|0 1 0 1 1 1| d		|

EOR	AB,d	|1|a|0 1 1 0 0 0| d		|

ADC	AB,d	|1|a|0 1 1 0 0 1| d		|

OR	AB,d	|1|a|0 1 1 0 1 0| d		|

ADD	AB,d	|1|a|0 1 1 0 1 1| d		|

LDD	d	|1 1 0 1 1 1 0 0| d		| {
	%D = load i16 , i16* D
	FLG16 -XX0- %D
	MKAB
}

STD	d	|1 1 0 1 1 1 0 1| d		| {
	MKD
	store i16* D , %D
	FLG16 -XX0- %D
}

CMP	XY,d	|1 0 0 1 1 1 0 0| d		|

JSR	d,>C	|1 0 0 1 1 1 0 1| d		|

LD	XY,d	|1 0 0 1 1 1 1 0| d		|

ST	XY,d	|1 0 0 1 1 1 1 1| d		|

SUB	AB,M	|1|a|1|e|0 0 0 0| m		|

CMP	AB,M	|1|a|1|e|0 0 0 1| m		|

SBC	AB,M	|1|a|1|e|0 0 1 0| m		|

SUBD	M	|1 0 1|e|0 0 1 1| m		|

ADDD	M	|1 1 1|e|0 0 1 1| m		|

AND	AB,M	|1|a|1|e|0 1 0 0| m		|

BIT	AB,M	|1|a|1|e|0 1 0 1| m		|

LD	AB,M	|1|a|1|e|0 1 1 0| m		|

ST	AB,M	|1|a|1|e|0 1 1 1| m		|

EOR	AB,M	|1|a|1|e|1 0 0 0| m		|

ADC	AB,M	|1|a|1|e|1 0 0 1| m		|

OR	AB,M	|1|a|1|e|1 0 1 0| m		|

ADD	AB,M	|1|a|1|e|1 0 1 1| m		|

CMP	XY,M	|1 0 1|e|1 1 0 0| m		|

JSR	M,>C	|1 0 1|e|1 1 0 1| m		|

LD	XY,M	|1 0 1|e|1 1 1 0| m		|

ST	XY,M	|1 0 1|e|1 1 1 1| m		|

LDD	I	|1 1 0 0 1 1 0 0| I1		| I2		| {
	%A = i8 I1
	%B = i8 I2
	FLG16 -XX0- I16
}

LD	SU,I	|1 1 0 0 1 1 1 0| I1		| I2		| {
	SU = I16
	FLG16 -XX0- I16
}

LD	SU,d	|1 1 0 1 1 1 1 0| d		|

ST	SU,d	|1 1 0 1 1 1 1 1| d		|

LDD	M	|1 1 1|e|1 1 0 0| m		| {
	%D = load i16 , i16* M
	FLG16 -XX0- %D
	MKAB
}

STD	M	|1 1 1|e|1 1 0 1| m		| {
	MKD
	store i16* M , %D
	FLG16 -XX0- %D
}

LD	SU,M	|1 1 1|e|1 1 1 0| m		|

ST	SU,M	|1 1 1|e|1 1 1 1| m		|

"""

mc6809_macro_instructions = """
LDDx	i	|1 1 0 0 0 1 1 0| i		|0 1 0 0 1 1 1 1| {
	%B = i8 I
	%A = i8 0
	FLG -0100
}

ANDD	I	|1 0 0 0 0 1 0 0| I1		|1 1 0 0 0 1 0 0| I2		| {
	%A = and i8 %A , I1
	%B = and i8 %A , I2
	FLG -XX0- %B
}

ORD	I	|1 0 0 0 1 0 1 0| I1		|1 1 0 0 1 0 1 0| I2		| {
	%A = or i8 %A , I1
	%B = or i8 %A , I2
	FLG -XX0- %B
}

CLRD	-	|0 1 0 1 1 1 1 1|0 1 0 0 1 1 1 1| {
	%A = i8 0
	%B = i8 0
	FLG -0100
}

CLRD	-	|0 1 0 0 1 1 1 1|0 1 0 1 1 1 1 1| {
	%A = i8 0
	%B = i8 0
	FLG -0100
}

"""


class mc6809_ins(assy.Instree_ins):
	def __init__(self, pj, lim, lang):
		super(mc6809_ins, self).__init__(pj, lim, lang)
		self.isz = "i8"
		self.icache = {}
		self.pfx = None
		self.off = None

	def assy_PFX10(self, pj):
		self.pfx = 0x10

	def assy_PFX11(self, pj):
		self.pfx = 0x11

	def assy_AB(self, pj):
		self.mne += "AB"[self['a']]

	def assy_M(self, pj):
		if self['e']:
			self.hi += 1
			self.dstadr = pj.m.bu16(self.hi - 2)
			return assy.Arg_dst(pj, self.dstadr)

		a = self['m']
		X = a >> 7
		r = "XYUS"[(a>>5)&3]
		i = (a >> 4) & 1
		m = a & 0xf
		if not X:
			if i:
				return("%s-%d" % (r, 16-m))
			else:
				return("%s+%d" % (r, m))

		self.hi += [
		    0, 0, 0, 0, 0, 0, 0, 0,
		    1, 2, 0, 0, 1, 2, 0, 2][m]

		if m == 0 and i == 0:
			return r + "+"
		elif m == 1:
			s = r + "++"
		elif m == 2 and i == 0:
			return "-" + r
		elif m == 3:
			s = "--" + r
		elif m == 4:
			s = r
		elif m == 5:
			s = r + "+B"
		elif m == 6:
			s = r + "+A"
		elif m == 8:
			self.off = pj.m.s8(self.hi - 1)
			s = r + "%+d" % self.off
		elif m == 0x9:
			self.off = pj.m.bs16(self.hi - 2)
			s = r + "%+d" % self.off
		elif m == 0xb:
			s = r + "+D"
		elif m == 0xd:
			self.off = pj.m.bs16(self.hi - 2)
			s = "0x%x" % ((0x10000 + self.hi + self.off & 0xffff))
		elif m == 0xf:
			self.off = pj.m.bs16(self.hi - 2)
			s = "0x%x" % self.off
		else:
			return "XXX"
		if i:
			return "[" + s + "]"
		else:
			return s

	def assy_P(self, pj):
		if self['X'] == 1:
			self.hi += [
			    0, 0, 0, 0, 0, 0, 0, 0,
			    1, 2, 0, 0, 1, 2, 0, 2][self['m']]
		if self['X'] == 1 and self['m'] == 0xf:
			self.dstadr = pj.m.bu16(self.hi - 2)
		r = ["X", "Y", "U", "S"][self['R']]
		if self['X'] == 0:
			o = self['m']
			if self['i']:
				o -= 16
			return("%s%+d" % (r, o))
		if self['m'] == 0x0:
			s = r + "+"
		elif self['m'] == 0x1:
			s = r + "++"
		elif self['m'] == 0x2:
			s = "-" + r
		elif self['m'] == 0x3:
			s = "--" + r
		elif self['m'] == 0x4:
			s = r
		elif self['m'] == 0x5:
			s = r + "+B"
		elif self['m'] == 0x6:
			s = r + "+A"
		elif self['m'] == 0x8:
			o = pj.m.s8(self.hi - 1)
			s = r + "%+d" % o
		elif self['m'] == 0x9:
			o = pj.m.bs16(self.hi - 2)
			s = r + "%+d" % o
		elif self['m'] == 0xb:
			s = r + "+D"
		elif self['m'] == 0xd:
			o = pj.m.bs16(self.hi - 2)
			s = "0x%x" % ((0x10000 + self.hi + o & 0xffff))
		elif self['m'] == 0xf:
			o = pj.m.bu16(self.hi - 2)
			s = "0x%x" % o
		else:
			raise assy.Wrong("somehow... @ 0x%x" % self.lo + " %d" % self['m'])
		if self['i']:
			return "[" + s + "]"
		return s

	def assy_XY(self, pj):
		if self.pfx == 0x10:
			self.mne += "Y"
		else:
			self.mne += "X"

	def assy_SU(self, pj):
		if self.pfx == 0x10:
			self.mne += "S"
		else:
			self.mne += "U"

	def assy_d(self, pj):
		return "$0x%02x" % self['d']

	def assy_i(self, pj):
		return "#0x%02x" % self['i']

	def assy_CC(self, pj):
		self.cc = [
			"RA", "RN", "HI", "LS", "CC", "CS", "NE", "EQ",
			"VC", "VS", "PL", "MI", "GE", "LT", "GT", "LE"
		][self['cc']]
		self.mne += self.cc
		if self['cc'] == 0:
			self.flow_J(pj)
		elif self['cc'] > 1:
			self.flow_JC(pj)

	def assy_I(self, pj):
		self.dstadr = (self['I1'] << 8) | self['I2']
		return assy.Arg_dst(pj, self.dstadr, "#")

	def assy_E(self, pj):
		self.dstadr = (self['e1'] << 8) | self['e2']
		return assy.Arg_dst(pj, self.dstadr)

	def assy_r(self, pj):
		a = self['r']
		if a & 0x80:
			a += 0xff00
		self.dstadr = (self.hi + a) & 0xffff
		return assy.Arg_dst(pj, self.dstadr)

	def assy_R(self, pj):
		a = self['R1'] << 8 | self['R2']
		self.dstadr = (self.hi + a) & 0xffff
		return assy.Arg_dst(pj, self.dstadr)

	def assy_s(self, pj):
		# XXX: if PULL PC fix flow record
		x = self['i']
		l = []
		r = ["CCR", "A", "B", "DPR", "X", "Y", "_", "PC"]
		if self.mne[-1] == "S":
			r[6] = "U"
		if self.mne[-1] == "U":
			r[6] = "S"
		for i in r:
			if x & 1:
				l.append(i)
			x >>= 1
		if self.mne[:3] == "PSH":
			l = reversed(l)
		return ",".join(l)


	def assy_t(self, pj):
		val = self['t']
		sr = val >> 4
		dr = val & 0xf
		r = [
			"D", "X",  "Y", "U",
			"S", "PC", "?6?", "?7?",
			"A", "B", "CCR", "DPR",
			"?c?", "?d?", "?e?", "?f?"
		]
		if r[sr][0] == "?" or r[dr][0] == "?":
			raise assy.Wrong("Wrong arg to TFR (0x%02x)" % val)
		return r[sr] + "," + r[dr]

	###############################################################

	def il_adr(self):

		e = self.get('e')

		if e is None:
			d = self.get('d')
			if not d is None:
				j = self.add_il([
					["%0", "=", "add", "i16", "%DP", ",", "0x%02x" % d]
				], "%0")
				return j
			return None

		if e:
			return "0x%04x" % self.dstadr

		a = self['m']
		X = a >> 7
		r = "%" + "XYUS"[(a>>5)&3]
		i = (a >> 4) & 1
		m = a & 0xf

		if X == 0:
			if i:
				return self.add_il([
					["%0", "=", "sub", "i16", r, ",", "0x%x" % (16 - m)],
				], "%0")
			else:
				return self.add_il([
					["%0", "=", "add", "i16", r, ",", "0x%x" % m],
				], "%0")
		if m == 0:
			adr = self.add_il([
				["%0", "=", "i16", r],
				[r, "=", "add", "i16", r, ",", "1"],
			], "%0")
		elif m == 1:
			adr = self.add_il([
				["%0", "=", "i16", r],
				[r, "=", "add", "i16", r, ",", "2"],
			], "%0")
		elif m == 2:
			self.add_il([
				[r, "=", "sub", "i16", r, ",", "1"],
			])
			adr = r
		elif m == 3:
			self.add_il([
				[r, "=", "sub", "i16", r, ",", "2"],
			])
			adr = r
		elif m == 4:
			adr = r
		elif m == 5:
			adr = self.add_il([
				["%1", "=", "zext", "i8", "%B", "to", "i16"],
				["%0", "=", "add", "i16", "%1", ",", r],
			], "%0")
		elif m == 6:
			adr = self.add_il([
				["%1", "=", "zext", "i8", "%A", "to", "i16"],
				["%0", "=", "add", "i16", "%1", ",", r],
			], "%0")
		elif m == 8 or m == 9:
			adr = self.add_il([
				["%0", "=", "add", "i16", r, ",", "0x%x" % self.off],
			], "%0")
		elif m == 11:
			adr = self.add_il([
				["%0", "=", "add", "i16", r, ",", "D"],
			], "%0")
		elif m == 12 or m == 13:
			adr = self.add_il([
				["%0", "=", "add", "i16", r, ",", "0x%x" % (self.hi + self.off)],
			], "%0")
		elif m == 15:
			adr = "0x%04x" % self.off
		else:
			return "XXXm%d" % m

		if i:
			return self.add_il([
				["%0", "=", "load", "i16", ",", "i16*", adr],
			], "%0")

		return adr

	def il_val8(self):
		adr = self.il_adr()
		if adr is None:
			i = self.get('i')
			m = self.get('m')
			if i is None or not m is None:
				return
			return "0x%02x" % i
		else:
			return self.add_il([
				[ "%0", "=", "load", "i8", ",", "i8*", adr ]
			], "%0")

	def il_logic(self):
		val = self.il_val8()
		if val is None:
			return
		r = "%" + self.mne[-1]
		op = {
			"OR":	"or",
			"AND":	"and",
			"EOR":	"xor",
		}.get(self.mne[:-1])
		self.add_il([
			[ r, "=", op, 'i8', r, ',', val ],
			["FLG", "-XX0-", r],
		])

	def il_add8(self, op, flg, val=None):
		if val is None:
			val = self.il_val8()
		if val is None:
			return
		r = "%" + self.mne[-1]
		self.add_il([
			[ "%1", "=", "i8", r ],
			[ r, "=", op, "i8", r , ",", val ],
			[ "FLG", flg, r, op, "%1", val ]
		])

	def il_ld8(self):
		r = "%" + self.mne[-1]
		adr = self.il_adr()
		if not adr is None:
			self.add_il([
				[ r, "=", "load", "i8", ",", "i8*", adr ],
				[ "FLG", "-XX0-", r ],
			])
			return

		val = self.il_val8()
		if val is None:
			return
		self.add_il([
			[ r, "=", val ],
			[ "FLG", "-XX0-", r ],
		])

	def il_st8(self):
		r = "%" + self.mne[-1]
		adr = self.il_adr()
		if adr is None:
			return
		self.add_il([
			[ "store", "i8", r, ",", "i8*", adr ],
			[ "FLG", "-XX0-", r ],
		])

	def il_clr(self):
		adr = self.il_adr()
		if adr is None:
			return
		self.add_il([
			[ "store", "i8", "0", ",", "i8*", adr ],
			[ "FLG", "-1000" ],
		])
		
	def ildefault(self):
		mne1 = self.mne[:-1]
		if mne1 in ('OR', 'AND', 'EOR'):
			self.il_logic()
		if self.mne in ('ADDA', 'ADDB'):
			self.il_add8("add", "XXXXX")
		if self.mne in ('INCA', 'INCB'):
			self.il_add8("add", "-XXX-", "1")
		if self.mne in ('LDA', 'LDB'):
			self.il_ld8()
		if self.mne in ('STA', 'STB'):
			self.il_st8()
		if self.mne == "CLR":
			self.il_clr()

	def ilmacro_AB(self):
		return "%" + "AB"[self['a']]

	def ilmacro_M(self):
		m = self.il_adr()
		if m is None:
			print(self)
			print(self.mne)
		assert not m is None
		return m

	def ilmacro_BR(self):
		cc = self['cc']
		if cc == 0:
			self.add_il([["br", "label", "0x%04x" % self.dstadr]])
			return
		if cc == 1:
			self.add_il([["%0", "=", "i8", "0"]])
			return
		if cc & 1:
			d1 = "0x%04x" % self.dstadr
			d2 = "HI"
		else:
			d1 = "HI"
			d2 = "0x%04x" % self.dstadr
		l = []
		cc &= 0xe
		if cc == 2:
			l.append(["%0", "=", "or", "i1", "%CC.z", ",", "%CC.c"])
			bb = "%0"
		elif cc == 4:
			bb = "%CC.c"
		elif cc == 6:
			bb = "%CC.z"
		elif cc == 8:
			bb = "%CC.v"
		elif cc == 10:
			bb = "%CC.n"
		elif cc == 12:
			l.append(["%0", "=", "xor", "i1", "%CC.n", ",", "%CC.v"])
			bb = "%0"
		else:
			l.append(["%0", "=", "xor", "i1", "%CC.n", ",", "%CC.v"])
			l.append(["%1", "=", "or", "i1", "%CC.z", ",", "%0"])
			bb = "%1"
		l.append(["br", "i1", bb, "label", d1, ",", "label", d2])

		self.add_il(l)

	def ilmacro_D(self):
		j = self.icache.get("d")
		if j is None:
			j = self.add_il([
				["%1", "=", "add", "i16", "%DP", ",", "0x%02x" % self['d']]
			], "%1")
		self.icache["d"] = j
		return j

	def ilmacro_DST(self):
		return "0x%04x" % self.dstadr

	def ilmacro_HI(self):
		return "0x%x" % self.hi

	def ilmacro_I(self):
		return "0x%02x" % (self['i'])

	def ilmacro_I1(self):
		return "0x%02x" % (self['I1'])

	def ilmacro_I2(self):
		return "0x%02x" % (self['I2'])

	def ilmacro_I(self):
		return "0x%02x" % (self['i'])

	def ilmacro_I16(self):
		self.isz = "i16"
		return "0x%02x%02x" % (self['I1'], self['I2'])

	def ilmacro_MKAB(self):
		self.add_il([
			["%B", "=", "trunc", "i16", "%D", "to", "i8"],
			["%D", "=", "srl", "i16", "%D", "," "8"],
			["%A", "=", "trunc", "i16", "%D", "to", "i8"],
		])

	def ilmacro_MKD(self):
		self.isz = "i16"
		self.add_il([
			["%0", "=", "zext", "i8", "%A", "to", "i16"],
			["%1", "=", "shl", "i16", "%0", ",", "8"],
			["%2", "=", "zext", "i8", "%B", "to", "i16"],
			["%D", "=", "or", "i16", "%1", ",", "%2"],
		])

	def ilmacro_SU(self):
		if self.pfx == 0x10:
			return "%S"
		else:
			return "%U"

	def ilmacro_XY(self):
		if self.pfx == 0x10:
			return "%Y"
		else:
			return "%X"

	def ilfunc_TFR(self, arg):
		val = self['t']
		sr = val >> 4
		dr = val & 0xf
		sz = ["i16", "i8"][sr >> 3]
		r = [
			"?0?", "%X",  "%Y", "%U",
			"%S", "%PC", "?6?", "?7?",
			"%A", "%B", "%CC", "%DP",
			"?c?", "?d?", "?e?", "?f?"
		]
		if sr == 0:
			r[0] = self.add_il([
				["%1", "=", "zext", "i16", "%A"],
				["%2", "=", "zext", "i16", "%B"],
				["%3", "=", "shl", "i16", "8", "%2"],
				["%0", "=", "or", "i16", "%1", ",", "%3"],
			], "%0")
		elif dr == 0:
			r[0] = "%0"
		self.add_il([
			[r[dr], "=", sz, r[sr]]
		])
		if dr == 0:
			self.add_il([
				["%A", "=", "trunc", "i16", r[0], "to", "i8"],
				["%0", "=", "shr", "i16", r[0], "8"],
				["%B", "=", "trunc", "i16", "%0", "to", "i8"],
			])

	def ilfunc_FLG_N(self, arg):
		c = "0x80"
		if self.isz == "i16":
			c += "00"
		self.add_il([
			["%1", "=", "and", self.isz, arg[0], ",", c],
			["%CC.n", "=", "icmp", "eq", self.isz, "%1", ",", c]
		])

	def ilfunc_FLG_V(self, arg):
		# XXX "Set if the carry from the MSB in the ALU does not match
		# XXX the carry from the MSB-1"
		assert len(arg) == 4
		self.add_il([
			["%CC.v", "=", "i1",
			    "pyreveng.overflow." + arg[1], "(", arg[2], ",", arg[3], ")"]
		])

	def ilfunc_FLG_Z(self, arg):
		self.add_il([
			["%CC.z", "=", "icmp", "eq", self.isz, arg[0], ",", "0"]
		])

	def ilfunc_FLG_H(self, arg):
		# XXX
		self.add_il([
			["%CC.h", "=", "i1", "void"]
		])

	def ilfunc_FLG_C(self, arg):
		assert len(arg) == 4
		self.add_il([
			["%CC.c", "=", "i1",
			    "pyreveng.carry." + arg[1], "(", arg[2], ",", arg[3], ")"]
		])

	def ilfunc_FLG(self, arg):
		f = {
			"H": self.ilfunc_FLG_H,
			"N": self.ilfunc_FLG_N,
			"Z": self.ilfunc_FLG_Z,
			"V": self.ilfunc_FLG_V,
			"C": self.ilfunc_FLG_C,
		}
		a1 = arg.pop(0)
		for j in "HNZVC":
			if a1[0] == "0":
				self.add_il([["%CC." + j.lower(), "=", "i1", "0"]])
			elif a1[0] == "1":
				self.add_il([["%CC." + j.lower(), "=", "i1", "1"]])
			elif a1[0] == "U":
				self.add_il([["%CC." + j.lower(), "=", "i1", "void"]])
			elif a1[0] != "-":
				assert len(arg) > 0
				f[j](arg)
			a1 = a1[1:]

	def ilfunc_FLG16(self, arg):
		self.isz = "i16"
		self.ilfunc_FLG(arg)

	def ilfunc_PULL(self, arg):
		i = self['i']
		s = "%" + arg[0]
		if s == "%S":
			sa = "%U"
		else:
			sa = "%S"
		j = 0x01
		for r in ('%CC', '%A', '%B', '%DP'):
			if i & j:
				self.add_il([
					[r, "=", "load", "i8", ",", "i8*", ",", s],
					[s, "=", "add", "i16", s, ",", "1"],
				])
			j <<= 1
		for r in ('%X', '%Y', sa):
			if i & j:
				self.add_il([
					[r, "=", "load", "i16", ",", "i16*", ",", s],
					[s, "=", "add", "i16", s, ",", "2"],
				])
			j <<= 1
		if i & j:
			self.add_il([
				["%0", "=", "load", "i16", ",", "i16*", ",", s],
				[s, "=", "add", "i16", s, ",", "2"],
				["br", "label", "%0"],
			])

	def ilfunc_PUSH(self, arg):
		i = self['i']
		s = "%" + arg[0]
		if s == "%S":
			sa = "%U"
		else:
			sa = "%S"
		j = 0x80
		for r in ('HI', sa, '%Y', '%X'):
			if i & j:
				self.add_il([
					[s, "=", "sub", "i16", s, ",", "2"],
					["store", "i16*", s, ",", r],
				])
			j >>= 1
		for r in ('%DP', '%B', '%A', '%CC'):
			if i & j:
				self.add_il([
					[s, "=", "sub", "i16", s, ",", "1"],
					["store", "i16*", s, ",", r],
				])
			j >>= 1


class mc6809(assy.Instree_disass):
	def __init__(self, mask=0xffff, macros=True):
		super(mc6809, self).__init__("mc6809", 8)
		self.it.load_string(mc6809_instructions)
		self.il = None
		self.myleaf = mc6809_ins
		if macros:
			self.it.load_string(mc6809_macro_instructions)
		self.mask = mask

	def codeptr(self, pj, adr):
		t = pj.m.bu16(adr)
		c = data.Codeptr(pj, adr, adr + 2, t)
		pj.todo(t, self.disass)
		return c

	def vectors(self, pj, adr=0xfff0):
		for v in (
			"V??", "SWI3", "SWI2", "FIRQ",
			"IRQ", "SWI", "NMI", "RST"
		):
			c = self.codeptr(pj, adr)
			pj.set_label(c.dst, "VEC" + v)
			adr += 2
