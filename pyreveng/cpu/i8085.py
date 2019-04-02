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
Disassembler for Intel i8085 microprocessor
"""

from pyreveng import instree, assy, data

i8085_desc="""
#			|- - - - - - - -|- - - - - - - -|- - - - - - - -|
MOV	r1,r2		|0 1| ddd | sss |
MOV	(HL),r2		|0 1 1 1 0| sss |
MOV	r1,(HL)		|0 1| ddd |1 1 0|
MVI	r1,I		|0 0| ddd |1 1 0| imm		|
MVI	(HL),I		|0 0|1 1 0|1 1 0| imm		|
#
LXI	rp,II		|0 0|rp |0 0 0 1| imml		| immh		|
LXI	SP,II		|0 0|1 1|0 0 0 1| imml		| immh		|
LDA	a		|0 0 1 1 1 0 1 0| lo		| hi		|
STA	a		|0 0 1 1 0 0 1 0| lo		| hi		|
LHLD	a		|0 0 1 0 1 0 1 0| lo		| hi		|
SHLD	a		|0 0 1 0 0 0 1 0| lo		| hi		|
LDAX	rp		|0 0|rp |1 0 1 0|
#
PCHL	>J		|1 1 1 0 1 0 0 1|
PUSH	rp		|1 1|rp |0 1 0 1|
PUSH	PSW		|1 1 1 1 0 1 0 1|
POP	rp		|1 1|rp |0 0 0 1|
#
STAX	rp		|0 0|rp |0 0 1 0|
XCHG	-		|1 1 1 0 1 0 1 1|
ADD	r2		|1 0 0 0 0| sss |
ADD	(HL)		|1 0 0 0 0|1 1 0|
ADI	I		|1 1 0 0 0 1 1 0| imm		|
ADC	r2		|1 0 0 0 1| sss |
#
ADC	(HL)		|1 0 0 0 1|1 1 0|
ACI	I		|1 1 0 0 1 1 1 0| imm		|
SUB	r2		|1 0 0 1 0| sss |
SUB	(HL)		|1 0 0 1 0 1 1 0|
SUI	I		|1 1 0 1 0 1 1 0| imm		|
SBB	r2		|1 0 0 1 1| sss |
#
SBB	(HL)		|1 0 0 1 1 1 1 0|
SBI	I		|1 1 0 1 1 1 1 0| imm		|
INR	r1		|0 0| ddd |1 0 0|
INR	(HL)		|0 0 1 1 0 1 0 0|
DCR	r1		|0 0| ddd |1 0 1|
DCR	(HL)		|0 0 1 1 0 1 0 1|
#
INX	rp		|0 0|rp |0 0 1 1|
DCX	rp		|0 0|rp |1 0 1 1|
DAD	rp		|0 0|rp |1 0 0 1|
DAA	-		|0 0 1 0 0 1 1 1|
ANA	r2		|1 0 1 0 0| sss	|
#
ANA	(HL)		|1 0 1 0 0 1 1 0|
ANI	I		|1 1 1 0 0 1 1 0| imm		|
XRA	r2		|1 0 1 0 1| sss |
XRA	(HL)		|1 0 1 0 1|1 1 0|
XRI	I		|1 1 1 0 1 1 1 0| imm		|
ORA	r2		|1 0 1 1 0| sss |
#
ORA	(HL)		|1 0 1 1 0 1 1 0|
ORI	I		|1 1 1 1 0 1 1 0| imm		|
CMP	r2		|1 0 1 1 1| sss |
CMP	(HL)		|1 0 1 1 1|1 1 0|
CPI	I		|1 1 1 1 1 1 1 0| imm		|
RLC	-		|0 0 0 0 0 1 1 1|
#
RRC	-		|0 0 0 0 1 1 1 1|
RAL	-		|0 0 0 1 0 1 1 1|
RAR	-		|0 0 0 1 1 1 1 1|
CMA	-		|0 0 1 0 1 1 1 1|
CMC	-		|0 0 1 1 1 1 1 1|
STC	-		|0 0 1 1 0 1 1 1|
#
JMP	a,>J		|1 1 0 0 0 0 1 1| lo		| hi		|
J	cc,a,>JC	|1 1| cc  |0 1 0| lo		| hi		|
CALL	a,>C		|1 1 0 0 1 1 0 1| lo		| hi		|
C	cc,a,>CC	|1 1| cc  |1 0 0| lo		| hi		|
RET	>R		|1 1 0 0 1 0 0 1|
R	cc,>RC		|1 1| cc  |0 0 0|
RST	n,>J		|1 1| n	  |1 1 1|
#
POP	PSW		|1 1 1 1 0 0 0 1|
XTHL	-		|1 1 1 0 0 0 1 1|
SPHL	-		|1 1 1 1 1 0 0 1|
IN	p		|1 1 0 1 1 0 1 1| p		|
OUT	p		|1 1 0 1 0 0 1 1| p		|
#
EI	-		|1 1 1 1 1 0 1 1|
DI	-		|1 1 1 1 0 0 1 1|
HLT	-		|0 1 1 1 0 1 1 0|
NOP	-		|0 0 0 0 0 0 0 0|
RIM	-		|0 0 1 0 0 0 0 0|
#
SIM	-		|0 0 1 1 0 0 0 0|

"""

if __name__ == "__main__":
	print(i8085_instructions)
	it = instree.Instree(8)
	it.load_string(i8085_instructions)
	it.print()

class i8085_ins(assy.Instree_ins):
	def __init__(self, pj, lim, lang):
		super(i8085_ins, self).__init__(pj, lim, lang)
		self.seg = ""

	def assy_cmdx(self, pj):
		c = self['cmd']
		l = c & 0x0f
		if c & 0xd0 == 0x00:
			s = "REG=0x%x" % l
			r = I7220_REGS.get(l)
			if c & 0x20:
				s += " M"
			if r is not None:
				s += " - " + r
			return s
		if c & 0xf0 == 0x10:
			return "CMD=0x%x - " % l + I7220_CMDS[l]
		return "0x%02x" % c

	def assy_r2(self, pj):
		r = self['sss']
		if r == 6:
			raise assy.Invalid('0x%x rs=6' % self.lo)
		return "BCDEHL-A"[r]

	def assy_r1(self, pj):
		r = self['ddd']
		if r == 6:
			raise assy.Invalid('0x%x rd=6' % self.lo)
		return "BCDEHL-A"[r]

	def assy_cc(self, pj):
		self.cc = (
		    'nz', 'z', 'nc', 'c', 'po', 'pe', 'p', 'm')[self['cc']]
		self.mne += self.cc

	def assy_rp(self, pj):
		rp = self['rp']
		if rp == 3:
			raise assy.Invalid('0x%x RP=3' % self.lo)
		return ('BC', 'DE', 'HL')[rp]

	def assy_II(self, pj):
		return "#0x%02x%02x" % (self['immh'], self['imml'])

	def assy_n(self, pj):
		self.dstadr = 8 * self['n']
		return "#%d" % self['n']
		# return assy.Arg_dst(pj, self.dstadr)

	def assy_I(self, pj):
		return "#0x%02x" % self['imm']

	def assy_a(self, pj):
		self.dstadr = self['hi'] << 8 | self['lo']
		return assy.Arg_dst(pj, self.dstadr)

class i8085(assy.Instree_disass):
	def __init__(self):
		super().__init__("i8085", 8)
		self.add_ins(i8085_desc, i8085_ins)
		self.verbatim |= set ((
		    "(HL)",
		    "SP",
		    "PSW",
		))

	def vectors(self, pj):
		for l,a in (
			("RESET", 	0x0000),
			("TRAP", 	0x0024),
			("RST1",	0x0008),
			("RST2",	0x0010),
			("RST3",	0x0018),
			("RST4",	0x0020),
			("RST5",	0x0028),
			("RST5.5",	0x002c),
			("RST6",	0x0030),
			("RST6.5",	0x0034),
			("RST7",	0x0038),
			("RST7.5",	0x003c),
		):
			pj.todo(a, self.disass)
			pj.set_label(a, l)

	def codeptr(self, pj, adr):
		t = pj.m.lu16(adr)
		c = data.Codeptr(pj, adr, adr + 2, t)
		pj.todo(t, self.disass)
		return c
