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
Partial disassembler for Z80
"""

from __future__ import print_function

from pyreveng import assy, data

z80_instructions = """
LD	rd,rs		|0 1| rd  | rs  |
LD	rd,n		|0 0| rd  |1 1 0| n		|
LD	rd,iHL		|0 1| rd  |1 1 0|
LD	iHL,rs		|0 1 1 1 0| rs  |
LD	iHL,n		|0 0 1 1 0 1 1 0| n		|
LD	A,(BC)		|0 0 0 0 1 0 1 0|
LD	A,(DE)		|0 0 0 1 1 0 1 0|
LD	A,inn		|0 0 1 1 1 0 1 0| n1		| n2		|
LD	(BC),A		|0 0 0 0 0 0 1 0|
LD	(DE),A		|0 0 0 1 0 0 1 0|
LD	inn,A		|0 0 1 1 0 0 1 0| n1		| n2		|
LD	A,I		|1 1 1 0 1 1 0 1|0 1 0 1 0 1 1 1|
LD	A,R		|1 1 1 0 1 1 0 1|0 1 0 1 1 1 1 1|
LD	I,A		|1 1 1 0 1 1 0 1|0 1 0 0 0 1 1 1|
LD	R,A		|1 1 1 0 1 1 0 1|0 1 0 0 1 1 1 1|
LD	dd,nn		|0 0| dd|0 0 0 1| n1		| n2		|
LD	HL,inn		|0 0 1 0 1 0 1 0| n1		| n2		|
LD	dd,inn		|1 1 1 0 1 1 0 1|0 1| dd|1 0 1 1| n1		| n2		|
LD	inn,HL		|0 0 1 0 0 0 1 0| n1		| n2		|
LD	inn,dd		|1 1 1 0 1 1 0 1|0 1| dd|0 0 1 1| n1		| n2		|
LD	SP,HL		|1 1 1 1 1 0 0 1|
PUSH	qq		|1 1| qq|0 1 0 1|
POP	qq		|1 1| qq|0 0 0 1|
EX	DE,HL		|1 1 1 0 1 0 1 1|
EX	AF,AF'		|0 0 0 0 1 0 0 0|
EXX	-		|1 1 0 1 1 0 0 1|
EX	(SP),HL		|1 1 1 0 0 0 1 1|
LDI	-		|1 1 1 0 1 1 0 1|1 0 1 0 0 0 0 0|
LDIR	-		|1 1 1 0 1 1 0 1|1 0 1 1 0 0 0 0|
LDD	-		|1 1 1 0 1 1 0 1|1 0 1 0 1 0 0 0|
LDDR	-		|1 1 1 0 1 1 0 1|1 0 1 1 1 0 0 0|
CPI	-		|1 1 1 0 1 1 0 1|1 0 1 0 0 0 0 1|
CPIR	-		|1 1 1 0 1 1 0 1|1 0 1 1 0 0 0 1|
CPD	-		|1 1 1 0 1 1 0 1|1 0 1 0 1 0 0 1|
CPDR	-		|1 1 1 0 1 1 0 1|1 0 1 1 1 0 0 1|
ADD	A,rs		|1 0|0 0 0| rs	|
ADD	A,n		|1 1|0 0 0|1 1 0| n		|
ADD	A,iHL		|1 0|0 0 0|1 1 0|

ADC	A,rs		|1 0|0 0 1| rs	|
ADC	A,n		|1 1|0 0 1|1 1 0| n		|
ADC	A,iHL		|1 0|0 0 1|1 1 0|

SUB	A,rs		|1 0|0 1 0| rs	|
SUB	A,n		|1 1|0 1 0|1 1 0| n		|
SUB	A,iHL		|1 0|0 1 0|1 1 0|

SBC	A,rs		|1 0|0 1 1| rs	|
SBC	A,n		|1 1|0 1 1|1 1 0| n		|
SBC	A,iHL		|1 0|0 1 1|1 1 0|

AND	A,rs		|1 0|1 0 0| rs	|
AND	A,n		|1 1|1 0 0|1 1 0| n		|
AND	A,iHL		|1 0|1 0 0|1 1 0|

XOR	A,rs		|1 0|1 0 1| rs	|
XOR	A,n		|1 1|1 0 1|1 1 0| n		|
XOR	A,iHL		|1 0|1 0 1|1 1 0|

OR	A,rs		|1 0|1 1 0| rs	|
OR	A,n		|1 1|1 1 0|1 1 0| n		|
OR	A,iHL		|1 0|1 1 0|1 1 0|

CP	A,rs		|1 0|1 1 1| rs	|
CP	A,n		|1 1|1 1 1|1 1 0| n		|
CP	A,iHL		|1 0|1 1 1|1 1 0|

INC	rd		|0 0|  rd |1 0 0|
INC	iHL		|0 0|1 1 0|1 0 0|
DEC	rd		|0 0|  rd |1 0 1|
DEC	iHL		|0 0|1 1 0|1 0 1|

DAA	-		|0 0 1 0 0 1 1 1|
CPL	-		|0 0 1 0 1 1 1 1|
NEG	-		|1 1 1 0 1 1 0 1|0 1 0 0 0 1 0 0|
CCF	-		|0 0 1 1 1 1 1 1|
SCF	-		|0 0 1 1 0 1 1 1|
NOP	-		|0 0 0 0 0 0 0 0|
HALT	-		|0 1 1 1 0 1 1 0|
DI	-		|1 1 1 1 0 0 1 1|
EI	-		|1 1 1 1 1 0 1 1|
IM	0		|1 1 1 0 1 1 0 1|0 1 0 0 0 1 1 0|
IM	1		|1 1 1 0 1 1 0 1|0 1 0 1 0 1 1 0|
IM	2		|1 1 1 0 1 1 0 1|0 1 0 1 1 1 1 0|

ADD	HL,dd		|0 0| dd|1|0 0 1|
ADC	HL,dd		|1 1|1 0 1|1 0 1|0 1| dd|1 0 1 0|
SBC	HL,dd		|1 1|1 0 1|1 0 1|0 1| dd|0 0 1 0|
INC	dd		|0 0| dd|0 0 1 1|
DEC	dd		|0 0| dd|1 0 1 1|

RLCA	-		|0 0 0 0 0 1 1 1|
RLA	-		|0 0 0 1 0 1 1 1|
RRCA	-		|0 0 0 0 1 1 1 1|
RRA	-		|0 0 0 1 1 1 1 1|

RLC	rs		|1 1 0 0 1 0 1 1|0 0|0 0 0|  rs |
RLC	iHL		|1 1 0 0 1 0 1 1|0 0|0 0 0|1 1 0|

RL	rs		|1 1 0 0 1 0 1 1|0 0|0 1 0|  rs |
RL	iHL		|1 1 0 0 1 0 1 1|0 0|0 1 0|1 1 0|

RRC	rs		|1 1 0 0 1 0 1 1|0 0|0 0 1|  rs |
RRC	iHL		|1 1 0 0 1 0 1 1|0 0|0 0 1|1 1 0|

RR	rs		|1 1 0 0 1 0 1 1|0 0|0 1 1|  rs |
RR	iHL		|1 1 0 0 1 0 1 1|0 0|0 1 1|1 1 0|

SLA	rs		|1 1 0 0 1 0 1 1|0 0|1 0 0|  rs |
SLA	iHL		|1 1 0 0 1 0 1 1|0 0|1 0 0|1 1 0|

SRA	rs		|1 1 0 0 1 0 1 1|0 0|1 0 1|  rs |
SRA	iHL		|1 1 0 0 1 0 1 1|0 0|1 0 1|1 1 0|

SRL	rs		|1 1 0 0 1 0 1 1|0 0|1 1 1|  rs |
SRL	iHL		|1 1 0 0 1 0 1 1|0 0|1 1 1|1 1 0|

RLD	-		|1 1 1 0 1 1 0 1|0 1 1 0 1 1 1 1|
RRD	-		|1 1 1 0 1 1 0 1|0 1 1 0 0 1 1 1|

BIT	b,rs		|1 1 0 0 1 0 1 1|0 1|  b  |  rs |
BIT	b,iHL		|1 1 0 0 1 0 1 1|0 1|  b  |1 1 0|

SET	b,rd		|1 1 0 0 1 0 1 1|1 1|  b  |  rd |
SET	b,iHL		|1 1 0 0 1 0 1 1|1 1|  b  |1 1 0|

RES	b,rd		|1 1 0 0 1 0 1 1|1 0|  b  |  rd |
RES	b,iHL		|1 1 0 0 1 0 1 1|1 0|  b  |1 1 0|

JP	nn,>J		|1 1 0 0 0 0 1 1| n1		| n2		|
JP	cc,nn,>JC	|1 1| cc  |0 1 0| n1		| n2		|
JR	e,>J		|0 0 0 1 1 0 0 0| e		|
JR	C,e,>JC		|0 0 1 1 1 0 0 0| e		|
JR	NC,e,>JC	|0 0 1 1 0 0 0 0| e		|
JR	Z,e,>JC		|0 0 1 0 1 0 0 0| e		|
JR	NZ,e,>JC	|0 0 1 0 0 0 0 0| e		|
JP	iHL,>J		|1 1 1 0 1 0 0 1|
DJNZ	e,>JC		|0 0 0 1 0 0 0 0| e		|

CALL	nn,>C		|1 1 0 0 1 1 0 1| n1		| n2		|
CALL	cc,nn,>C	|1 1|  cc |1 0 0| n1		| n2		|
RET	>R		|1 1 0 0 1 0 0 1|
RET	cc,>RC		|1 1|  cc |0 0 0|
RETI	>R		|1 1 1 0 1 1 0 1|0 1 0 0 1 1 0 1|
RETN	>R		|1 1 1 0 1 1 0 1|0 1 0 0 0 1 0 1|
RST	t,>C		|1 1|  t  |1 1 1|

IN	A,io		|1 1 0 1 1 0 1 1| io		|
IN	rd,(C)		|1 1 1 0 1 1 0 1|0 1|  rd |0 0 0|
INI	-		|1 1 1 0 1 1 0 1|1 0 1 0 0 0 1 0|
INIR	-		|1 1 1 0 1 1 0 1|1 0 1 1 0 0 1 0|
IND	-		|1 1 1 0 1 1 0 1|1 0 1 0 1 0 1 0|
INDR	-		|1 1 1 0 1 1 0 1|1 0 1 1 1 0 1 0|

OUT	io,A		|1 1 0 1 0 0 1 1| io		|
OUT	(C),rs		|1 1 1 0 1 1 0 1|0 1|  rs |0 0 1|

OUTI	-		|1 1 1 0 1 1 0 1|1 0 1 0 0 0 1 1|
OUTIR	-		|1 1 1 0 1 1 0 1|1 0 1 1 0 0 1 1|
OUTD	-		|1 1 1 0 1 1 0 1|1 0 1 0 1 0 1 1|
OUTDR	-		|1 1 1 0 1 1 0 1|1 0 1 1 1 0 1 1|
+IX	iIX		|1 1 1 1 1 1 0 1|
+IY	iIX		|1 1 0 1 1 1 0 1|
"""

class z80_ins(assy.Instree_ins):
	def __init__(self, pj, lim, lang):
		super(z80_ins, self).__init__(pj, lim, lang)
		self.idx = "HL"

	def assy_e(self, pj):
		self.dstadr = self.hi
		e = self['e']
		if e & 0x80:
			e -= 256
		self.dstadr += e
		return assy.Arg_dst(pj, self.dstadr)

	def assy_nn(self, pj):
		self.dstadr = (self['n2'] << 8) | self['n1']
		return assy.Arg_dst(pj, self.dstadr)

	def assy_t(self, pj):
		self.dstadr = self['t'] << 3
		return assy.Arg_dst(pj, self.dstadr)

	def assy_inn(self, pj):
		self.dstadr = (self['n2'] << 8) | self['n1']
		return assy.Arg_dst(pj, self.dstadr, "(", ")")

	def assy_dd(self, pj):
		return ["BC", "DE", self.idx, "SP"][self['dd']]

	def assy_qq(self, pj):
		return ["BC", "DE", self.idx, "AF"][self['qq']]

	def assy_rs(self, pj):
		return ["B", "C", "D", "E", "H", "L", None, "A"][self['rs']]

	def assy_rd(self, pj):
		return ["B", "C", "D", "E", "H", "L", None, "A"][self['rd']]

	def assy_cc(self, pj):
		self.cc = [
		    "NZ", "Z", "NC", "C", "PO", "PE", "P", "M"
		][self['cc']]
		return self.cc

	def assy_b(self, pj):
		return assy.Arg_imm(pj, self['b'], 8)

	def assy_n(self, pj):
		return assy.Arg_imm(pj, self['n'], 8)

	def assy_io(self, pj):
		return assy.Arg_imm(pj, self['io'], 8)

	def assy_iIX(self, pj):
		self.idx = "IX"

	def assy_iIY(self, pj):
		self.idx = "IY"

	def assy_HL(self, pj):
		return self.idx

	def assy_iHL(self, pj):
		if self.idx == "HL":
			return "(HL)"
		d = pj.m.rd(self.hi)
		self.hi += 1
		if d & 0x80:
			d = 256 - d
			return "(%s-0x%x)" % (self.idx, d)
		else:
			return "(%s+0x%x)" % (self.idx, d)

class z80(assy.Instree_disass):
	def __init__(self, mask=0xffff):
		super(z80, self).__init__("z80", 8)
		self.it.load_string(z80_instructions)
		self.myleaf = z80_ins
		self.mask = mask
		self.verbatim |= set(["A", "DE", "(DE)", "(BC)", "(SP)",
		    "(C)", "SP", "I", "2", "C", "NC", "NZ", "Z", "AF", "AF'"])

	def codeptr(self, pj, adr):
		t = pj.m.lu16(adr)
		c = data.Codeptr(pj, adr, adr + 2, t)
		pj.todo(t, self.disass)
		return c

	def vectors(self, pj):
		return
