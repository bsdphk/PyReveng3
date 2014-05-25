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
Disassembler for MC6800 familiy CPUs.

Presently supported variants:
	6800
	MC68HC11 (incomplete)
"""

from __future__ import print_function

from pyreveng import mem, assy, data

mc6800_instructions = """
NOP	-	|0 0 0 0 0 0 0 1|
TAP	-	|0 0 0 0 0 1 1 0|
TPA	-	|0 0 0 0 0 1 1 1|
INX	-	|0 0 0 0 1 0 0 0|
DEX	-	|0 0 0 0 1 0 0 1|
CLV	-	|0 0 0 0 1 0 1 0|
SEV	-	|0 0 0 0 1 0 1 1|
CLC	-	|0 0 0 0 1 1 0 0|
SLC	-	|0 0 0 0 1 1 0 1|
CLI	-	|0 0 0 0 1 1 1 0|
SEI	-	|0 0 0 0 1 1 1 1|
SBA	-	|0 0 0 1 0 0 0 0|
CBA	-	|0 0 0 1 0 0 0 1|
TAB	-	|0 0 0 1 0 1 1 0|
TBA	-	|0 0 0 1 0 1 1 1|
DAA	-	|0 0 0 1 1 0 0 1|
ABA	-	|0 0 0 1 1 0 1 1|
BRA	r,>J	|0 0 1 0 0 0 0 0| r		|
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
TSX	-	|0 0 1 1 0 0 0 0|
INS	-	|0 0 1 1 0 0 0 1|
PULA	-	|0 0 1 1 0 0 1 0|
PULB	-	|0 0 1 1 0 0 1 1|
DES	-	|0 0 1 1 0 1 0 0|
TXS	-	|0 0 1 1 0 1 0 1|
PSHA	-	|0 0 1 1 0 1 1 0|
PSHB	-	|0 0 1 1 0 1 1 1|
RTS	>R	|0 0 1 1 1 0 0 1|
RTI	>R	|0 0 1 1 1 0 1 1|
WAI	-	|0 0 1 1 1 1 1 0|
SWI	-	|0 0 1 1 1 1 1 1|
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
NEG	x	|0 1 1 0 0 0 0 0| x		|
COM	x	|0 1 1 0 0 0 1 1| x		|
LSR	x	|0 1 1 0 0 1 0 0| x		|
ROR	x	|0 1 1 0 0 1 1 0| x		|
ASR	x	|0 1 1 0 0 1 1 1| x		|
ASL	x	|0 1 1 0 1 0 0 0| x		|
ROL	x	|0 1 1 0 1 0 0 1| x		|
DEC	x	|0 1 1 0 1 0 1 0| x		|
INC	x	|0 1 1 0 1 1 0 0| x		|
TST	x	|0 1 1 0 1 1 0 1| x		|
JMP	x,>J	|0 1 1 0 1 1 1 0| x		|
CLR	x	|0 1 1 0 1 1 1 1| x		|
NEG	e	|0 1 1 1 0 0 0 0| e1		| e2		|
COM	e	|0 1 1 1 0 0 1 1| e1		| e2		|
LSR	e	|0 1 1 1 0 1 0 0| e1		| e2		|
ROR	e	|0 1 1 1 0 1 1 0| e1		| e2		|
ASR	e	|0 1 1 1 0 1 1 1| e1		| e2		|
ASL	e	|0 1 1 1 1 0 0 0| e1		| e2		|
ROL	e	|0 1 1 1 1 0 0 1| e1		| e2		|
DEC	e	|0 1 1 1 1 0 1 0| e1		| e2		|
INC	e	|0 1 1 1 1 1 0 0| e1		| e2		|
TST	e	|0 1 1 1 1 1 0 1| e1		| e2		|
JMP	e,>J	|0 1 1 1 1 1 1 0| e1		| e2		|
CLR	e	|0 1 1 1 1 1 1 1| e1		| e2		|
SUBA	i	|1 0 0 0 0 0 0 0| i		|
CMPA	i	|1 0 0 0 0 0 0 1| i		|
SBCA	i	|1 0 0 0 0 0 1 0| i		|
ANDA	i	|1 0 0 0 0 1 0 0| i		|
BITA	i	|1 0 0 0 0 1 0 1| i		|
LDAA	i	|1 0 0 0 0 1 1 0| i		|
EORA	i	|1 0 0 0 1 0 0 0| i		|
ADCA	i	|1 0 0 0 1 0 0 1| i		|
ORAA	i	|1 0 0 0 1 0 1 0| i		|
ADDA	i	|1 0 0 0 1 0 1 1| i		|
CPX	I	|1 0 0 0 1 1 0 0| I1		| I2		|
BSR	r,>C	|1 0 0 0 1 1 0 1| r		|
LDS	I	|1 0 0 0 1 1 1 0| I1		| I2		|
SUBA	d	|1 0 0 1 0 0 0 0| d		|
CMPA	d	|1 0 0 1 0 0 0 1| d		|
SBCA	d	|1 0 0 1 0 0 1 0| d		|
ANDA	d	|1 0 0 1 0 1 0 0| d		|
BITA	d	|1 0 0 1 0 1 0 1| d		|
LDAA	d	|1 0 0 1 0 1 1 0| d		|
STAA	d	|1 0 0 1 0 1 1 1| d		|
EORA	d	|1 0 0 1 1 0 0 0| d		|
ADCA	d	|1 0 0 1 1 0 0 1| d		|
ORAA	d	|1 0 0 1 1 0 1 0| d		|
ADDA	d	|1 0 0 1 1 0 1 1| d		|
CPX	d	|1 0 0 1 1 1 0 0| d		|
LDS	d	|1 0 0 1 1 1 1 0| d		|
STS	d	|1 0 0 1 1 1 1 1| d		|
SUBA	x	|1 0 1 0 0 0 0 0| x		|
CMPA	x	|1 0 1 0 0 0 0 1| x		|
SBCA	x	|1 0 1 0 0 0 1 0| x		|
ANDA	x	|1 0 1 0 0 1 0 0| x		|
BITA	x	|1 0 1 0 0 1 0 1| x		|
LDAA	x	|1 0 1 0 0 1 1 0| x		|
STAA	x	|1 0 1 0 0 1 1 1| x		|
EORA	x	|1 0 1 0 1 0 0 0| x		|
ADCA	x	|1 0 1 0 1 0 0 1| x		|
ORAA	x	|1 0 1 0 1 0 1 0| x		|
ADDA	x	|1 0 1 0 1 0 1 1| x		|
CPX	x	|1 0 1 0 1 1 0 0| x		|
JSR	x,>C	|1 0 1 0 1 1 0 1| x		|
LDS	x	|1 0 1 0 1 1 1 0| x		|
STS	x	|1 0 1 0 1 1 1 1| x		|
SUBA	e	|1 0 1 1 0 0 0 0| e1		| e2		|
CMPA	e	|1 0 1 1 0 0 0 1| e1		| e2		|
SBCA	e	|1 0 1 1 0 0 1 0| e1		| e2		|
ANDA	e	|1 0 1 1 0 1 0 0| e1		| e2		|
BITA	e	|1 0 1 1 0 1 0 1| e1		| e2		|
LDAA	e	|1 0 1 1 0 1 1 0| e1		| e2		|
STAA	e	|1 0 1 1 0 1 1 1| e1		| e2		|
EORA	e	|1 0 1 1 1 0 0 0| e1		| e2		|
ADCA	e	|1 0 1 1 1 0 0 1| e1		| e2		|
ORAA	e	|1 0 1 1 1 0 1 0| e1		| e2		|
ADDA	e	|1 0 1 1 1 0 1 1| e1		| e2		|
CPX	e	|1 0 1 1 1 1 0 0| e1		| e2		|
JSR	e,>C	|1 0 1 1 1 1 0 1| e1		| e2		|
LDS	e	|1 0 1 1 1 1 1 0| e1		| e2		|
STS	e	|1 0 1 1 1 1 1 1| e1		| e2		|
SUBB	i	|1 1 0 0 0 0 0 0| i		|
CMPB	i	|1 1 0 0 0 0 0 1| i		|
SBCB	i	|1 1 0 0 0 0 1 0| i		|
ANDB	i	|1 1 0 0 0 1 0 0| i		|
BITB	i	|1 1 0 0 0 1 0 1| i		|
LDAB	i	|1 1 0 0 0 1 1 0| i		|
EORB	i	|1 1 0 0 1 0 0 0| i		|
ADCB	i	|1 1 0 0 1 0 0 1| i		|
ORAB	i	|1 1 0 0 1 0 1 0| i		|
ADDB	i	|1 1 0 0 1 0 1 1| i		|
LDX	I	|1 1 0 0 1 1 1 0| I1		| I2		|
SUBB	d	|1 1 0 1 0 0 0 0| d		|
CMPB	d	|1 1 0 1 0 0 0 1| d		|
SBCB	d	|1 1 0 1 0 0 1 0| d		|
ANDB	d	|1 1 0 1 0 1 0 0| d		|
BITB	d	|1 1 0 1 0 1 0 1| d		|
LDAB	d	|1 1 0 1 0 1 1 0| d		|
STAB	d	|1 1 0 1 0 1 1 1| d		|
EORB	d	|1 1 0 1 1 0 0 0| d		|
ADCB	d	|1 1 0 1 1 0 0 1| d		|
ORAB	d	|1 1 0 1 1 0 1 0| d		|
ADDB	d	|1 1 0 1 1 0 1 1| d		|
LDX	d	|1 1 0 1 1 1 1 0| d		|
STX	d	|1 1 0 1 1 1 1 1| d		|
SUBB	x	|1 1 1 0 0 0 0 0| x		|
CMPB	x	|1 1 1 0 0 0 0 1| x		|
SBCB	x	|1 1 1 0 0 0 1 0| x		|
ANDB	x	|1 1 1 0 0 1 0 0| x		|
BITB	x	|1 1 1 0 0 1 0 1| x		|
LDAB	x	|1 1 1 0 0 1 1 0| x		|
STAB	x	|1 1 1 0 0 1 1 1| x		|
EORB	x	|1 1 1 0 1 0 0 0| x		|
ADCB	x	|1 1 1 0 1 0 0 1| x		|
ORAB	x	|1 1 1 0 1 0 1 0| x		|
ADDB	x	|1 1 1 0 1 0 1 1| x		|
LDX	x	|1 1 1 0 1 1 1 0| x		|
STX	x	|1 1 1 0 1 1 1 1| x		|
SUBB	e	|1 1 1 1 0 0 0 0| e1		| e2		|
CMPB	e	|1 1 1 1 0 0 0 1| e1		| e2		|
SBCB	e	|1 1 1 1 0 0 1 0| e1		| e2		|
ANDB	e	|1 1 1 1 0 1 0 0| e1		| e2		|
BITB	e	|1 1 1 1 0 1 0 1| e1		| e2		|
LDAB	e	|1 1 1 1 0 1 1 0| e1		| e2		|
STAB	e	|1 1 1 1 0 1 1 1| e1		| e2		|
EORB	e	|1 1 1 1 1 0 0 0| e1		| e2		|
ADCB	e	|1 1 1 1 1 0 0 1| e1		| e2		|
ORAB	e	|1 1 1 1 1 0 1 0| e1		| e2		|
ADDB	e	|1 1 1 1 1 0 1 1| e1		| e2		|
LDX	e	|1 1 1 1 1 1 1 0| e1		| e2		|
STX	e	|1 1 1 1 1 1 1 1| e1		| e2		|
"""

def arg_d(pj, ins):
	ins.dstadr = ins.im.F_d
	return assy.Arg_dst(pj, ins.dstadr)

def arg_e(pj, ins):
	ins.dstadr = (ins.im.F_e1 << 8) | ins.im.F_e2
	return assy.Arg_dst(pj, ins.dstadr)

def arg_i(pj, ins):
	return assy.Arg_imm(pj, ins.im.F_i, 8)

def arg_I(pj, ins):
	ins.dstadr = (ins.im.F_I1 << 8) | ins.im.F_I2
	return assy.Arg_dst(pj, ins.dstadr, "#")

def arg_r(pj, ins):
	a = ins.im.F_r
	if a & 0x80:
		a -= 256
	ins.dstadr = ins.hi + a
	if ins.mne != "BRA":
		ins.cc = ins.mne[1:]
	return assy.Arg_dst(pj, ins.dstadr)

class arg_x(assy.Arg):
	def __init__(self, pj, ins):
		super(arg_x, self).__init__(pj)
		self.val = ins.im.F_x
		self.ins = ins

	def __str__(self):
		return "0x%02x+" % self.val + self.ins.idx

class mc6800(assy.Instree_disass):
	def __init__(self, mask=0xffff):
		super(mc6800, self).__init__("mc6800", 8)
		self.it.load_string(mc6800_instructions)
		self.args.update({
			"d":	arg_d,
			"e":	arg_e,
			"i":	arg_i,
			"I":	arg_I,
			"r":	arg_r,
			"x":	arg_x,
		})
		self.mask = mask

	def init_code(self, pj, ins):
		ins.idx = "X"

	def codeptr(self, pj, adr):
		t = pj.m.bu16(adr)
		c = data.Codeptr(pj, adr, adr + 2, t)
		pj.todo(t, self.disass)
		return c

	def vectors(self, pj, adr=0xfff8):
		for v in ("IRQ", "SWI", "NMI", "RST"):
			c = self.codeptr(pj, adr)
			pj.set_label(c.dst, "VEC" + v)
			adr += 2

mc68hc11_instructions = """
IDIV	-		|0 0 0 0 0 0 1 0|
FDIV	-		|0 0 0 0 0 0 1 1|
LSRD	-		|0 0 0 0 0 1 0 0|
ASLD	-		|0 0 0 0 0 1 0 1|

+	Y		|0 0 0 1 1 0 0 0|

BRSET	d,i,r,>C	|0 0 0 1 0 0 1 0| d		| i		| r		|
BRCLR	d,i,r,>C	|0 0 0 1 0 0 1 1| d		| i		| r		|
BSET	d,i		|0 0 0 1 0 1 0 0| d		| i		|
BCLR	d,i		|0 0 0 1 0 1 0 1| d		| i		|

CPD	I		|0 0 0 1 1 0 1 0|1 0 0 0 0 0 1 1| I1		| I2		|
CPD	d		|0 0 0 1 1 0 1 0|1 0 0 1 0 0 1 1| d		|
CPD	x		|0 0 0 1 1 0 1 0|1 0 1 0 0 0 1 1| x		|
CPD	e		|0 0 0 1 1 0 1 0|1 0 1 1 0 0 1 1| e1		| e2		|
CPD	y		|1 1 0 0 1 1 0 1|1 0 1 0 0 0 1 1| y		|

LDY	x		|0 0 0 1 1 0 1 0|1 1 1 0 1 1 1 0| x		|
STY	x		|0 0 0 1 1 0 1 0|1 1 1 0 1 1 1 1| x		|

LDX	y		|1 1 0 0 1 1 0 1|1 1 1 0 1 1 1 0| y		|
STX	y		|1 1 0 0 1 1 0 1|1 1 1 0 1 1 1 1| y		|


BSET	x,i		|0 0 0 1 1 1 0 0| x		| i		|
BCLR	x,i		|0 0 0 1 1 1 0 1| x		| i		|
BRSET	x,i,r,>C	|0 0 0 1 1 1 1 0| x		| i		| r		|
BRCLR	x,i,r,>C	|0 0 0 1 1 1 1 1| x		| i		| r		|

ABX	-		|0 0 1 1 1 0 1 0|

PSHX	-		|0 0 1 1 1 1 0 0|
MUL	-		|0 0 1 1 1 1 0 1|

PULX	-		|0 0 1 1 1 0 0 0|

SUBD	I		|1 0 0 0 0 0 1 1| I1		| I2		|
SUBD	d		|1 0 0 1 0 0 1 1| d		|
SUBD	x		|1 0 1 0 0 0 1 1| x		|
SUBD	e		|1 0 1 1 0 0 1 1| e1		| e2		|

ADDD	I		|1 1 0 0 0 0 1 1| I1		| I2		|
ADDD	d		|1 1 0 1 0 0 1 1| d		|
ADDD	x		|1 1 1 0 0 0 1 1| x		|
ADDD	e		|1 1 1 1 0 0 1 1| e1		| e2		|

XGDX	-		|1 0 0 0 1 1 1 1|

LDD	I		|1 1 0 0 1 1 0 0| I1		| I2		|
LDD	d		|1 1 0 1 1 1 0 0| d		|
LDD	x		|1 1 1 0 1 1 0 0| x		|
LDD	e		|1 1 1 1 1 1 0 0| e1		| e2		|

STD	d		|1 1 0 1 1 1 0 1| d		|
STD	x		|1 1 1 0 1 1 0 1| x		|
STD	e		|1 1 1 1 1 1 0 1| e1		| e2		|

"""

class arg_y(assy.Arg):
	def __init__(self, pj, ins):
		super(arg_y, self).__init__(pj)
		self.val = ins.im.F_y

	def __str__(self):
		return "0x%02x+Y" % self.val

def arg_Y(pj, ins):
	if ins.mne[-1] == "X":
		ins.mne = ins.mne[:-1] + "Y"
	ins.idx = "Y"

class mc68hc11(mc6800):
	def __init__(self, mask=0xffff):
		super(mc68hc11, self).__init__(mask=mask)
		self.it.load_string(mc68hc11_instructions)
		self.args.update(
			{
			"y":	arg_y,
			"Y":	arg_Y,
			}
		)

	def register_labels(self, pj):
		pj.set_label(0x1000, "PORTA")
		pj.set_label(0x1002, "PIOC")
		pj.set_label(0x1003, "PORTC")
		pj.set_label(0x1004, "PORTB")
		pj.set_label(0x1005, "PORTCL")
		pj.set_label(0x1007, "DDRC")
		pj.set_label(0x1008, "PORTD")
		pj.set_label(0x1009, "DDRD")
		pj.set_label(0x100A, "PORTE")
		pj.set_label(0x100B, "CFORC")
		pj.set_label(0x100C, "OC1M")
		pj.set_label(0x100D, "OC1D")
		pj.set_label(0x100E, "TCNTH")
		pj.set_label(0x100F, "TCNTL")

		pj.set_label(0x1010, "TIC1H")
		pj.set_label(0x1011, "TIC1L")
		pj.set_label(0x1012, "TIC2H")
		pj.set_label(0x1013, "TIC2L")
		pj.set_label(0x1014, "TIC3H")
		pj.set_label(0x1015, "TIC4L")
		pj.set_label(0x1016, "TOC1H")
		pj.set_label(0x1017, "TOC1L")
		pj.set_label(0x1018, "TOC2H")
		pj.set_label(0x1019, "TOC2L")
		pj.set_label(0x101A, "TOC3H")
		pj.set_label(0x101B, "TOC3L")
		pj.set_label(0x101C, "TOC4H")
		pj.set_label(0x101D, "TOC4L")
		pj.set_label(0x101E, "TI4_O5H")
		pj.set_label(0x101F, "TI4_O5L")

		pj.set_label(0x1020, "TCTL1")
		pj.set_label(0x1021, "TCTL2")
		pj.set_label(0x1022, "TMSK1")
		pj.set_label(0x1023, "TFLG1")
		pj.set_label(0x1024, "TMSK2")
		pj.set_label(0x1025, "TFLG2")
		pj.set_label(0x1026, "PACTL")
		pj.set_label(0x1027, "PACNT")
		pj.set_label(0x1028, "SPCR")
		pj.set_label(0x1029, "SPSR")
		pj.set_label(0x102A, "SPDR")
		pj.set_label(0x102B, "BAUD")
		pj.set_label(0x102C, "SCCR1")
		pj.set_label(0x102D, "SCCR2")
		pj.set_label(0x102E, "SCSR")
		pj.set_label(0x102F, "SCDR")

		pj.set_label(0x1030, "ADCTL")
		pj.set_label(0x1031, "ADR1")
		pj.set_label(0x1032, "ADR2")
		pj.set_label(0x1033, "ADR3")
		pj.set_label(0x1034, "ADR4")
		pj.set_label(0x1035, "BPROT")
		pj.set_label(0x1036, "EPROG")
		pj.set_label(0x1039, "OPTION")
		pj.set_label(0x103A, "COPRST")
		pj.set_label(0x103B, "PPROG")
		pj.set_label(0x103C, "HPRIO")
		pj.set_label(0x103D, "INIT")
		pj.set_label(0x103F, "CONFIG")


	def vectors(self, pj, adr=0xffd6):
		for v in (
			"SCI",
			"SPI",  "PAI", "PAO",  "TO",
			"I4O5", "OC4", "OC3",  "OC2",
			"OC1",  "IC3", "IC2",  "IC1",
			"RTI",  "IRQ", "XIRQ", "SWI",
			"ILL",  "COP", "CME",  "RESET"
			):
			c = self.codeptr(pj, adr)
			pj.set_label(c.dst, "VEC" + v)
			adr += 2
