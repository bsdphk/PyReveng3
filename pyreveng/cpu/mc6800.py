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

from pyreveng import assy, data

mc6800_instructions = """
NOP	-	|01	|
TAP	-	|06	|
TPA	-	|07	|
INX	-	|08	|
DEX	-	|09	|
CLV	-	|0A	|
SEV	-	|0B	|
CLC	-	|0C	|
SEC	-	|0D	|
CLI	-	|0E	|
SEI	-	|0F	|
SBA	-	|10	|
CBA	-	|11	|
TAB	-	|16	|
TBA	-	|17	|
DAA	-	|19	|
ABA	-	|1B	|
BRA	r,>J	|20	| r		|
BHI	r,>JC	|22	| r		|
BLS	r,>JC	|23	| r		|
BCC	r,>JC	|24	| r		|
BCS	r,>JC	|25	| r		|
BNE	r,>JC	|26	| r		|
BEQ	r,>JC	|27	| r		|
BVC	r,>JC	|28	| r		|
BVS	r,>JC	|29	| r		|
BPL	r,>JC	|2A	| r		|
BMI	r,>JC	|2B	| r		|
BGE	r,>JC	|2C	| r		|
BLT	r,>JC	|2D	| r		|
BGT	r,>JC	|2E	| r		|
BLE	r,>JC	|2F	| r		|
TSX	-	|30	|
INS	-	|31	|
PULA	-	|32	|
PULB	-	|33	|
DES	-	|34	|
TXS	-	|35	|
PSHA	-	|36	|
PSHB	-	|37	|
RTS	>R	|39	|
RTI	>R	|3B	|
WAI	-	|3E	|
SWI	-	|3F	|
NEGA	-	|40	|
COMA	-	|43	|
LSRA	-	|44	|
RORA	-	|46	|
ASRA	-	|47	|
ASLA	-	|48	|
ROLA	-	|49	|
DECA	-	|4A	|
INCA	-	|4C	|
TSTA	-	|4D	|
CLRA	-	|4F	|
NEGB	-	|50	|
COMB	-	|53	|
LSRB	-	|54	|
RORB	-	|56	|
ASRB	-	|57	|
ASLB	-	|58	|
ROLB	-	|59	|
DECB	-	|5A	|
INCB	-	|5C	|
TSTB	-	|5D	|
CLRB	-	|5F	|
NEG	x	|60	| x		|
COM	x	|63	| x		|
LSR	x	|64	| x		|
ROR	x	|66	| x		|
ASR	x	|67	| x		|
ASL	x	|68	| x		|
ROL	x	|69	| x		|
DEC	x	|6A	| x		|
INC	x	|6C	| x		|
TST	x	|6D	| x		|
JMP	x,>J	|6E	| x		|
CLR	x	|6F	| x		|
NEG	e	|70	| e1		| e2		|
COM	e	|73	| e1		| e2		|
LSR	e	|74	| e1		| e2		|
ROR	e	|76	| e1		| e2		|
ASR	e	|77	| e1		| e2		|
ASL	e	|78	| e1		| e2		|
ROL	e	|79	| e1		| e2		|
DEC	e	|7A	| e1		| e2		|
INC	e	|7C	| e1		| e2		|
TST	e	|7D	| e1		| e2		|
JMP	e,>J	|7E	| e1		| e2		|
CLR	e	|7F	| e1		| e2		|
SUBA	i	|80	| i		|
CMPA	i	|81	| i		|
SBCA	i	|82	| i		|
ANDA	i	|84	| i		|
BITA	i	|85	| i		|
LDAA	i	|86	| i		|
EORA	i	|88	| i		|
ADCA	i	|89	| i		|
ORAA	i	|8A	| i		|
ADDA	i	|8B	| i		|
CPX	I	|8C	| I1		| I2		|
BSR	r,>C	|8D	| r		|
LDS	I	|8E	| I1		| I2		|
SUBA	d	|90	| d		|
CMPA	d	|91	| d		|
SBCA	d	|92	| d		|
ANDA	d	|94	| d		|
BITA	d	|95	| d		|
LDAA	d	|96	| d		|
STAA	d	|97	| d		|
EORA	d	|98	| d		|
ADCA	d	|99	| d		|
ORAA	d	|9A	| d		|
ADDA	d	|9B	| d		|
CPX	d	|9C	| d		|
LDS	d	|9E	| d		|
STS	d	|9F	| d		|
SUBA	x	|A0	| x		|
CMPA	x	|A1	| x		|
SBCA	x	|A2	| x		|
ANDA	x	|A4	| x		|
BITA	x	|A5	| x		|
LDAA	x	|A6	| x		|
STAA	x	|A7	| x		|
EORA	x	|A8	| x		|
ADCA	x	|A9	| x		|
ORAA	x	|AA	| x		|
ADDA	x	|AB	| x		|
CPX	x	|AC	| x		|
JSR	x,>C	|AD	| x		|
LDS	x	|AE	| x		|
STS	x	|AF	| x		|
SUBA	e	|B0	| e1		| e2		|
CMPA	e	|B1	| e1		| e2		|
SBCA	e	|B2	| e1		| e2		|
ANDA	e	|B4	| e1		| e2		|
BITA	e	|B5	| e1		| e2		|
LDAA	e	|B6	| e1		| e2		|
STAA	e	|B7	| e1		| e2		|
EORA	e	|B8	| e1		| e2		|
ADCA	e	|B9	| e1		| e2		|
ORAA	e	|BA	| e1		| e2		|
ADDA	e	|BB	| e1		| e2		|
CPX	e	|BC	| e1		| e2		|
JSR	e,>C	|BD	| e1		| e2		|
LDS	e	|BE	| e1		| e2		|
STS	e	|BF	| e1		| e2		|
SUBB	i	|C0	| i		|
CMPB	i	|C1	| i		|
SBCB	i	|C2	| i		|
ANDB	i	|C4	| i		|
BITB	i	|C5	| i		|
LDAB	i	|C6	| i		|
EORB	i	|C8	| i		|
ADCB	i	|C9	| i		|
ORAB	i	|CA	| i		|
ADDB	i	|CB	| i		|
LDX	I	|CE	| I1		| I2		|
SUBB	d	|D0	| d		|
CMPB	d	|D1	| d		|
SBCB	d	|D2	| d		|
ANDB	d	|D4	| d		|
BITB	d	|D5	| d		|
LDAB	d	|D6	| d		|
STAB	d	|D7	| d		|
EORB	d	|D8	| d		|
ADCB	d	|D9	| d		|
ORAB	d	|DA	| d		|
ADDB	d	|DB	| d		|
LDX	d	|DE	| d		|
STX	d	|DF	| d		|
SUBB	x	|E0	| x		|
CMPB	x	|E1	| x		|
SBCB	x	|E2	| x		|
ANDB	x	|E4	| x		|
BITB	x	|E5	| x		|
LDAB	x	|E6	| x		|
STAB	x	|E7	| x		|
EORB	x	|E8	| x		|
ADCB	x	|E9	| x		|
ORAB	x	|EA	| x		|
ADDB	x	|EB	| x		|
LDX	x	|EE	| x		|
STX	x	|EF	| x		|
SUBB	e	|F0	| e1		| e2		|
CMPB	e	|F1	| e1		| e2		|
SBCB	e	|F2	| e1		| e2		|
ANDB	e	|F4	| e1		| e2		|
BITB	e	|F5	| e1		| e2		|
LDAB	e	|F6	| e1		| e2		|
STAB	e	|F7	| e1		| e2		|
EORB	e	|F8	| e1		| e2		|
ADCB	e	|F9	| e1		| e2		|
ORAB	e	|FA	| e1		| e2		|
ADDB	e	|FB	| e1		| e2		|
LDX	e	|FE	| e1		| e2		|
STX	e	|FF	| e1		| e2		|
"""

def arg_d(pj, ins):
	ins.dstadr = ins['d']
	return assy.Arg_dst(pj, ins.dstadr)

def arg_e(pj, ins):
	ins.dstadr = (ins['e1'] << 8) | ins['e2']
	return assy.Arg_dst(pj, ins.dstadr)

def arg_i(pj, ins):
	return assy.Arg_imm(pj, ins['i'], 8)

def arg_I(pj, ins):
	ins.dstadr = (ins['I1'] << 8) | ins['I2']
	return assy.Arg_dst(pj, ins.dstadr, "#")

def arg_r(pj, ins):
	a = ins['r']
	if a & 0x80:
		a -= 256
	ins.dstadr = ins.hi + a
	if ins.mne != "BRA":
		ins.cc = ins.mne[1:]
	return assy.Arg_dst(pj, ins.dstadr)

class arg_x(assy.Arg):
	def __init__(self, pj, ins):
		super(arg_x, self).__init__(pj)
		self.val = ins['x']
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
IDIV	-		|02	|
FDIV	-		|03	|
LSRD	-		|04	|
ASLD	-		|05	|

+	Y		|18	|

BRSET	d,i,r,>C	|12	| d		| i		| r		|
BRCLR	d,i,r,>C	|13	| d		| i		| r		|
BSET	d,i		|14	| d		| i		|
BCLR	d,i		|15	| d		| i		|

CPD	I		|1A	|83	| I1		| I2		|
CPD	d		|1A	|93	| d		|
CPD	x		|1A	|A3	| x		|
CPD	e		|1A	|B3	| e1		| e2		|
CPD	y		|CD	|A3	| y		|

LDY	x		|1A	|EE	| x		|
STY	x		|1A	|EF	| x		|

LDX	y		|CD	|EE	| y		|
STX	y		|CD	|EF	| y		|


BSET	x,i		|1C	| x		| i		|
BCLR	x,i		|1D	| x		| i		|
BRSET	x,i,r,>C	|1E	| x		| i		| r		|
BRCLR	x,i,r,>C	|1F	| x		| i		| r		|

ABX	-		|3A	|

PSHX	-		|3C	|
MUL	-		|3D	|

PULX	-		|38	|

SUBD	I		|83	| I1		| I2		|
SUBD	d		|93	| d		|
SUBD	x		|A3	| x		|
SUBD	e		|B3	| e1		| e2		|

ADDD	I		|C3	| I1		| I2		|
ADDD	d		|D3	| d		|
ADDD	x		|E3	| x		|
ADDD	e		|F3	| e1		| e2		|

XGDX	-		|8F	|

LDD	I		|CC	| I1		| I2		|
LDD	d		|DC	| d		|
LDD	x		|EC	| x		|
LDD	e		|FC	| e1		| e2		|

STD	d		|DD	| d		|
STD	x		|ED	| x		|
STD	e		|FD	| e1		| e2		|

"""

class arg_y(assy.Arg):
	def __init__(self, pj, ins):
		super(arg_y, self).__init__(pj)
		self.val = ins['y']

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
