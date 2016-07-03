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

from pyreveng import mem, assy, data

mc6809_instructions = """
NEG	-	|0 0 0 0 0 0 0 0|

LBRN	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 0 0 0 1| R1		| R2		|
LBHI	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 0 0 1 0| R1		| R2		|
LBLS	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 0 0 1 1| R1		| R2		|
LBCC	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 0 1 0 0| R1		| R2		|
LBCS	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 0 1 0 1| R1		| R2		|
LBNE	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 0 1 1 0| R1		| R2		|
LBEQ	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 0 1 1 1| R1		| R2		|
LBVC	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 1 0 0 0| R1		| R2		|
LBVS	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 1 0 0 1| R1		| R2		|
LBPL	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 1 0 1 0| R1		| R2		|
LBMI	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 1 0 1 1| R1		| R2		|
LBGE	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 1 1 0 0| R1		| R2		|
LBLT	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 1 1 0 1| R1		| R2		|
LBGT	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 1 1 1 0| R1		| R2		|
LBLT	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 1 1 1 1| R1		| R2		|

CMPD	I	|0 0 0 1 0 0 0 0|1 0 0 0 0 0 1 1| I1		| I2		|
LDY     I	|0 0 0 1 0 0 0 0|1 0 0 0 1 1 1 0| I1		| I2		|
CMPD    P	|0 0 0 1 0 0 0 0|1 0 1 0 0 0 1 1|X| R |i| m     |
LDY     P	|0 0 0 1 0 0 0 0|1 0 1 0 1 1 1 0|X| R |i| m     |
STY     P	|0 0 0 1 0 0 0 0|1 0 1 0 1 1 1 1|X| R |i| m     |
CMPD	E	|0 0 0 1 0 0 0 0|1 0 1 1 0 0 1 1| E1		| E2		|
CMPY	E	|0 0 0 1 0 0 0 0|1 0 1 1 1 1 0 0| E1		| E2		|
LDY	E	|0 0 0 1 0 0 0 0|1 0 1 1 1 1 1 0| E1		| E2		|
STY	E	|0 0 0 1 0 0 0 0|1 0 1 1 1 1 1 1| E1		| E2		|
LDS     I	|0 0 0 1 0 0 0 0|1 1 0 0 1 1 1 0| I1		| I2		|

NOP	-	|0 0 0 1 0 0 1 0|
LBRA	R,>J	|0 0 0 1 0 1 1 0| R1            | R2 		|
LBSR	R,>C	|0 0 0 1 0 1 1 1| R1            | R2 		|
DAA 	-	|0 0 0 1 1 0 0 1|
ORCC	i	|0 0 0 1 1 0 1 0| i		|
ANDCC	i	|0 0 0 1 1 1 0 0| i		|
SEX	-	|0 0 0 1 1 1 0 1|
EXG	t	|0 0 0 1 1 1 1 0| t		|
TFR	t	|0 0 0 1 1 1 1 1| t		|

BRA	r,>J	|0 0 1 0 0 0 0 0| r		|
BRN	r,>JC	|0 0 1 0 0 0 0 1| r		|
BHI	r,>JC	|0 0 1 0 0 0 1 0| r		|
BLS	r,>JC	|0 0 1 0 0 0 1 1| r		|
BCC	r,>JC	|0 0 1 0 0 1 0 0| r		|
BCS	r,>JC	|0 0 1 0 0 1 0 1| r		|
BNE	r,>JC	|0 0 1 0 0 1 1 0| r		|
BEQ	r,>JC	|0 0 1 0 0 1 1 1| r		|
BVC	r,>JC	|0 0 1 0 1 0 0 0| r		|
BVS	r,>JC	|0 0 1 0 1 0 0 1| r		|
BPL	r,>JC	|0 0 1 0 1 0 1 0| r		|
BMI	r,>JC	|0 0 1 0 1 0 1 1| r		|
BGE	r,>JC	|0 0 1 0 1 1 0 0| r		|
BLT	r,>JC	|0 0 1 0 1 1 0 1| r		|
BGT	r,>JC	|0 0 1 0 1 1 1 0| r		|
BLE	r,>JC	|0 0 1 0 1 1 1 1| r		|

LEAX	P	|0 0 1 1 0 0 0 0|X| R |i| m	|
LEAY	P	|0 0 1 1 0 0 0 1|X| R |i| m	|
LEAS	P	|0 0 1 1 0 0 1 0|X| R |i| m     |
LEAU	P	|0 0 1 1 0 0 1 1|X| R |i| m     |
PSHS	s	|0 0 1 1 0 1 0 0| i		|
PULS	s	|0 0 1 1 0 1 0 1| i		|
PSHU	s	|0 0 1 1 0 1 1 0| i		|
PULU	s	|0 0 1 1 0 1 1 1| i		|
RTS	>R	|0 0 1 1 1 0 0 1|
ABX	-	|0 0 1 1 1 0 1 0|
RTI	>R	|0 0 1 1 1 0 1 1|
CWAI	i	|0 0 1 1 1 1 0 0| i		|
MUL 	-	|0 0 1 1 1 1 0 1|
SWI 	-	|0 0 1 1 1 1 1 1|

NEGA	-	|0 1 0 0 0 0 0 0|
COMA	-	|0 1 0 0 0 0 1 1|
LSRA	-	|0 1 0 0 0 1 0 0|
RORA	-	|0 1 0 0 0 1 1 0|
ASRA	-	|0 1 0 0 0 1 1 1|
ASLA	-	|0 1 0 0 1 0 0 0|
ROLA	-	|0 1 0 0 1 0 0 1|
DECA	-	|0 1 0 0 1 0 1 0|
INCA	-	|0 1 0 0 1 1 0 0|
TSTA	-	|0 1 0 0 1 1 0 1|
CLRA	-	|0 1 0 0 1 1 1 1|

NEGB	-	|0 1 0 1 0 0 0 0|
COMB	-	|0 1 0 1 0 0 1 1|
LSRB	-	|0 1 0 1 0 1 0 0|
RORB	-	|0 1 0 1 0 1 1 0|
ASRB	-	|0 1 0 1 0 1 1 1|
ASLB	-	|0 1 0 1 1 0 0 0|
ROLB	-	|0 1 0 1 1 0 0 1|
DECB	-	|0 1 0 1 1 0 1 0|
INCB	-	|0 1 0 1 1 1 0 0|
TSTB	-	|0 1 0 1 1 1 0 1|
CLRB	-	|0 1 0 1 1 1 1 1|

NEG	P	|0 1 1 0 0 0 0 0|X| R |i| m	|
COM	P	|0 1 1 0 0 0 1 1|X| R |i| m	|
LSR	P	|0 1 1 0 0 1 0 0|X| R |i| m	|
ROR	P	|0 1 1 0 0 1 1 0|X| R |i| m	|
ASR	P	|0 1 1 0 0 1 1 1|X| R |i| m	|
ASL	P	|0 1 1 0 1 0 0 0|X| R |i| m	|
ROL	P	|0 1 1 0 1 0 0 1|X| R |i| m	|
DEC	P	|0 1 1 0 1 0 1 0|X| R |i| m	|
INC	P	|0 1 1 0 1 1 0 0|X| R |i| m	|
TST	P	|0 1 1 0 1 1 0 1|X| R |i| m	|
JMP	P,>J	|0 1 1 0 1 1 1 0|X| R |i| m	|
CLR	P	|0 1 1 0 1 1 1 1|X| R |i| m	|

NEG	E	|0 1 1 1 0 0 0 0| E1		| E2		|
COM	E	|0 1 1 1 0 0 1 1| E1		| E2		|
LSR	E	|0 1 1 1 0 1 0 0| E1		| E2		|
ROR	E	|0 1 1 1 0 1 1 0| E1		| E2		|
ASR	E	|0 1 1 1 0 1 1 1| E1		| E2		|
ASL	E	|0 1 1 1 1 0 0 0| E1		| E2		|
ROL	E	|0 1 1 1 1 0 0 1| E1		| E2		|
DEC	E	|0 1 1 1 1 0 1 0| E1		| E2		|
INC	E	|0 1 1 1 1 1 0 0| E1		| E2		|
TST	E	|0 1 1 1 1 1 0 1| E1		| E2		|
JMP	E	|0 1 1 1 1 1 1 0| E1		| E2		|
CLR	E	|0 1 1 1 1 1 1 1| E1		| E2		|

SUBA	i	|1 0 0 0 0 0 0 0| i		|
CMPA	i	|1 0 0 0 0 0 0 1| i		|
SBCA	i	|1 0 0 0 0 0 1 0| i		|
SUBD	I	|1 0 0 0 0 0 1 1| I1		| I2		|
ANDA	i	|1 0 0 0 0 1 0 0| i		|
BITA	i	|1 0 0 0 0 1 0 1| i		|
LDA	i	|1 0 0 0 0 1 1 0| i		|
EORA	i	|1 0 0 0 1 0 0 0| i		|
ADCA	i	|1 0 0 0 1 0 0 1| i		|
ORA 	i	|1 0 0 0 1 0 1 0| i		|
ADDA	i	|1 0 0 0 1 0 1 1| i		|
CMPX	I	|1 0 0 0 1 1 0 0| I1		| I2		|
BSR	r,>C	|1 0 0 0 1 1 0 1| r		|
LDX	I	|1 0 0 0 1 1 1 0| I1		| I2		|

SUBA	P	|1 0 1 0 0 0 0 0|X| R |i| m	|
CMPA	P	|1 0 1 0 0 0 0 1|X| R |i| m	|
SBCA	P	|1 0 1 0 0 0 1 0|X| R |i| m	|
SUBD	P	|1 0 1 0 0 0 1 1|X| R |i| m	|
ANDA	P	|1 0 1 0 0 1 0 0|X| R |i| m	|
BITA	P	|1 0 1 0 0 1 0 1|X| R |i| m	|
LDA	P	|1 0 1 0 0 1 1 0|X| R |i| m	|
STA	P	|1 0 1 0 0 1 1 1|X| R |i| m	|
EORA	P	|1 0 1 0 1 0 0 0|X| R |i| m	|
ADCA	P	|1 0 1 0 1 0 0 1|X| R |i| m	|
ORA 	P	|1 0 1 0 1 0 1 0|X| R |i| m	|
ADDA	P	|1 0 1 0 1 0 1 1|X| R |i| m	|
CMPX	P	|1 0 1 0 1 1 0 0|X| R |i| m	|
JSR	P,>C	|1 0 1 0 1 1 0 1|X| R |i| m	|
LDX	P	|1 0 1 0 1 1 1 0|X| R |i| m     |
STX	P	|1 0 1 0 1 1 1 1|X| R |i| m     |

SUBA	E	|1 0 1 1 0 0 0 0| E1		| E2		|
CMPA	E	|1 0 1 1 0 0 0 1| E1		| E2		|
SBCA	E	|1 0 1 1 0 0 1 0| E1		| E2		|
SUBD	E	|1 0 1 1 0 0 1 1| E1		| E2		|
ANDA	E	|1 0 1 1 0 1 0 0| E1		| E2		|
BITA	E	|1 0 1 1 0 1 0 1| E1		| E2		|
LDA	E	|1 0 1 1 0 1 1 0| E1		| E2		|
STA	E	|1 0 1 1 0 1 1 1| E1		| E2		|
EORA	E	|1 0 1 1 1 0 0 0| E1		| E2		|
ADCA	E	|1 0 1 1 1 0 0 1| E1		| E2		|
ORA	E	|1 0 1 1 1 0 1 0| E1		| E2		|
ADDA	E	|1 0 1 1 1 0 1 1| E1		| E2		|
CMPX	E	|1 0 1 1 1 1 0 0| E1		| E2		|
JSR	E,>C	|1 0 1 1 1 1 0 1| E1		| E2		|
LDX	E	|1 0 1 1 1 1 1 0| E1		| E2		|
STX	E	|1 0 1 1 1 1 1 1| E1		| E2		|

SUBB	i	|1 1 0 0 0 0 0 0| i		|
CMPB	i	|1 1 0 0 0 0 0 1| i		|
SBCB	i	|1 1 0 0 0 0 1 0| i		|
ADDD	I	|1 1 0 0 0 0 1 1| I1		| I2		|
ANDB	i	|1 1 0 0 0 1 0 0| i		|
BITB	i	|1 1 0 0 0 1 0 1| i		|
LDB 	i	|1 1 0 0 0 1 1 0| i		|
EORB	i	|1 1 0 0 1 0 0 0| i		|
ADCB	i	|1 1 0 0 1 0 0 1| i		|
ORB 	i	|1 1 0 0 1 0 1 0| i		|
ADDB	i	|1 1 0 0 1 0 1 1| i		|
LDD	I	|1 1 0 0 1 1 0 0| I1		| I2		|
LDU	I	|1 1 0 0 1 1 1 0| I1		| I2		|

SUBB	P	|1 1 1 0 0 0 0 0|X| R |i| m     |
CMPB	P	|1 1 1 0 0 0 0 1|X| R |i| m     |
SBCB	P	|1 1 1 0 0 0 1 0|X| R |i| m     |
ADDD	P	|1 1 1 0 0 0 1 1|X| R |i| m     |
ANDB	P	|1 1 1 0 0 1 0 0|X| R |i| m     |
BITB	P	|1 1 1 0 0 1 0 1|X| R |i| m     |
LDB	P	|1 1 1 0 0 1 1 0|X| R |i| m     |
STB	P	|1 1 1 0 0 1 1 1|X| R |i| m     |
EORB	P	|1 1 1 0 1 0 0 0|X| R |i| m     |
ADCB	P	|1 1 1 0 1 0 0 1|X| R |i| m     |
ORB	P	|1 1 1 0 1 0 1 0|X| R |i| m     |
ADDB	P	|1 1 1 0 1 0 1 1|X| R |i| m     |
LDD	P	|1 1 1 0 1 1 0 0|X| R |i| m     |
STD	P	|1 1 1 0 1 1 0 1|X| R |i| m     |
LDU	P	|1 1 1 0 1 1 1 0|X| R |i| m     |
STU	P	|1 1 1 0 1 1 1 1|X| R |i| m     |

SUBB	E	|1 1 1 1 0 0 0 0| E1		| E2		|
CMPB	E	|1 1 1 1 0 0 0 1| E1		| E2		|
SBCB	E	|1 1 1 1 0 0 1 0| E1		| E2		|
ADDD	E	|1 1 1 1 0 0 1 1| E1		| E2		|
ANDB	E	|1 1 1 1 0 1 0 0| E1		| E2		|
BITB	E	|1 1 1 1 0 1 0 1| E1		| E2		|
LDB	E	|1 1 1 1 0 1 1 0| E1		| E2		|
STB	E	|1 1 1 1 0 1 1 1| E1		| E2		|
EORB	E	|1 1 1 1 1 0 0 0| E1		| E2		|
ADCB	E	|1 1 1 1 1 0 0 1| E1		| E2		|
ORB	E	|1 1 1 1 1 0 1 0| E1		| E2		|
ADDB	E	|1 1 1 1 1 0 1 1| E1		| E2		|
LDD	E	|1 1 1 1 1 1 0 0| E1		| E2		|
STD	E	|1 1 1 1 1 1 0 1| E1		| E2		|
LDU	E	|1 1 1 1 1 1 1 0| E1		| E2		|
STU	E	|1 1 1 1 1 1 1 1| E1		| E2		|
"""

mc6809_macro_instructions = """
LDD	i	|1 1 0 0 0 1 1 0| i		|0 0 0 1 1 1 0 1|
CLRD	-	|0 1 0 1 1 1 1 1|0 0 0 1 1 1 0 1|
"""

class arg_i(object):
	def __init__(self, pj, ins):
		self.val = ins.im.F_i

	def render(self, pj):
		return "#0x%02x" % self.val

class arg_I(assy.Arg_dst):
	def __init__(self, pj, ins):
		ins.dstadr = (ins.im.F_I1 << 8) | ins.im.F_I2
		super(arg_I, self).__init__(pj, ins.dstadr, "#")

class arg_E(assy.Arg_dst):
	def __init__(self, pj, ins):
		ins.dstadr = (ins.im.F_E1 << 8) | ins.im.F_E2
		super(arg_E, self).__init__(pj, ins.dstadr, "")

class arg_r(assy.Arg_dst):
	def __init__(self, pj, ins):
		a = ins.im.F_r
		if a & 0x80:
			a += 0xff00
		ins.dstadr = (ins.hi + a) & 0xffff
		super(arg_r, self).__init__(pj, ins.dstadr)

class arg_R(assy.Arg_dst):
	def __init__(self, pj, ins):
		a = ins.im.F_R1 << 8 | ins.im.F_R2
		ins.dstadr = (ins.hi + a) & 0xffff
		super(arg_R, self).__init__(pj, ins.dstadr)

class arg_s(assy.Arg_dst):
	def __init__(self, pj, ins):
		x = ins.im.F_i
		l = []
		r = ["CCR", "A", "B", "DPR", "X", "Y", "_", "PC"]
		if ins.mne[-1] == "S":
			r[6] = "U"
		if ins.mne[-1] == "U":
			r[6] = "S"
		for i in r:
			if x & 1:
				l.append(i)
			x >>= 1
		if ins.mne[:3] == "PSH":
			l = reversed(l)
		self.s = ",".join(l)
		
	def render(self, pj):
		return self.s


class arg_P(assy.Arg_dst):
	def __init__(self, pj, ins):
		self.ins = ins
		if ins.im.F_X == 1:
			ins.hi += [0,0,0,0,0,0,0,0,1,2,0,0,1,2,0,2][ins.im.F_m]
		if self.ins.im.F_X == 1 and self.ins.im.F_m == 0xf:
			ins.dstadr = pj.m.bu16(self.ins.hi - 2)
		super(arg_P, self).__init__(pj, ins.dstadr, "")

	def render(self, pj):
		r = ["X", "Y", "U", "S"][self.ins.im.F_R]
		if self.ins.im.F_X == 0:
			o = self.ins.im.F_m
			if self.ins.im.F_i:
				o -= 16
			return("%s%+d" % (r, o))

		if self.ins.im.F_m == 0x0:
			s = r + "+"
		elif self.ins.im.F_m == 0x1:
			s = r + "++"
		elif self.ins.im.F_m == 0x2:
			s = "-" + r
		elif self.ins.im.F_m == 0x3:
			s = "--" + r
		elif self.ins.im.F_m == 0x4:
			s = r
		elif self.ins.im.F_m == 0x5:
			s = r + "+B"
		elif self.ins.im.F_m == 0x6:
			s = r + "+A"
		elif self.ins.im.F_m == 0x8:
			o = pj.m.s8(self.ins.hi - 1)
			s = r + "%+d" % o
		elif self.ins.im.F_m == 0x9:
			o = pj.m.bs16(self.ins.hi - 2)
			s = r + "%+d" % o
		elif self.ins.im.F_m == 0xb:
			s = r + "+D"
		elif self.ins.im.F_m == 0xf:
			s = str(self)	# XXX HACK, FIX
		else:
			s = "<%d,%s,%d,0x%x>XXXIDX" % (
				self.ins.im.F_X,
				["X", "Y", "U", "S"][self.ins.im.F_R],
				self.ins.im.F_i,
				self.ins.im.F_m
			)
		if self.ins.im.F_i:
			return "[" + s + "]"
		return s
			
class arg_t(object):
	def __init__(self, pj, ins):
		self.val = ins.im.F_t

	def render(self, pj):
		r = [
			"D", "X", "Y", "U",
			"S", "PC","?6?", "?7?",
			"A", "B", "CCR", "DPR",
			"?c?", "?d?", "?e?", "?f?"
		]
		# XXX: two args as one string is bad for analysis...
		s = r[self.val >> 4] + "," + r[self.val & 0xf]
		return s

class mc6809(assy.Instree_disass):
	def __init__(self, mask=0xffff, macros=True):
		super(mc6809, self).__init__("mc6809", 8)
		self.it.load_string(mc6809_instructions)
		if macros:
			self.it.load_string(mc6809_macro_instructions)
		self.args.update( {
			"i":	arg_i,
			"s":	arg_s,
			"I":	arg_I,
			"r":	arg_r,
			"t":	arg_t,
			"P":	arg_P,
			"E":	arg_E,
			"R":	arg_R,
		})
		self.mask = mask

	def init_ins(self, pj, ins):
		ins.idx = "X"

	def codeptr(self, pj, adr):
		t = pj.m.bu16(adr)
		c = data.Codeptr(pj, adr, adr + 2, t)
		pj.todo(t, self.disass)
		return c

	def vectors(self, pj, adr = 0xfff0):
		for v in (
			"V??", "SWI3", "SWI2", "FIRQ",
			"IRQ", "SWI", "NMI", "RST"
		):
			c = self.codeptr(pj, adr)
			pj.set_label(c.dst, "VEC" + v)
			adr += 2
