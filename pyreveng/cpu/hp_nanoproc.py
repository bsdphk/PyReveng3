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

'''Hewlett Packard Nanoprocessor (1820-1692)

NB:
This disassembler is prepared for bank-switching, in that it
assumes that the upper (0xf800) address bits are preserved.
'''

from pyreveng import assy, mem

# Lower-case means we guessed
# Uppercase came from 09411 listing

hp_nanoproc_desc="""
INB	-		|0 0 0 0|0 0 0 0|		Increment A
DEB	-		|0 0 0 0|0 0 0 1|		Decrement A
IND	-		|0 0 0 0|0 0 1 0|		Increment BCD
DED	-		|0 0 0 0|0 0 1 1|		Decrement BCD
CLA	-		|0 0 0 0|0 1 0 0|		Clear A
CMA	-		|0 0 0 0|0 1 0 1|		Complement A
RSA	-		|0 0 0 0|0 1 1 0|		Right Shift A
LSA	-		|0 0 0 0|0 1 1 1|		Left Shift A
SGT	S,>JC		|0 0 0 0|1 0 0 0|		Skip Greater Than
SLT	S,>JC		|0 0 0 0|1 0 0 1|		Skip Less Than
SEQ	S,>JC		|0 0 0 0|1 0 1 0|		Skip Equal
SAZ	S,>JC		|0 0 0 0|1 0 1 1|		Skip A Zero
SLE	S,>JC		|0 0 0 0|1 1 0 0|		Skip Less or Equal
SGE	S,>JC		|0 0 0 0|1 1 0 1|		Skip Greater or Equal
SNE	S,>JC		|0 0 0 0|1 1 1 0|		Skip Not Equal
SAN	S,>JC		|0 0 0 0|1 1 1 1|		Skip A non-zero
SBS	S,bno,>JC	|0 0 0 1|0| bno |		Skip Bit Set
SFS	S,dctl,>JC	|0 0 0 1|1| dctl|
SES	S,>JC		|0 0 0 1 1 1 1 1|		Skip E Set
SBN	bno		|0 0 1 0|0| bno |		Set A.bit
STC	dctl		|0 0 1 0|1| dctl|
ENI	-		|0 0 1 0|1 1 1 1|		Enable Irq
SBZ	S,bno,>JC	|0 0 1 1|0| bno |		Skip Bit Zero
SFZ	S,dctl,>JC	|0 0 1 1|1| dctl|
SEZ	S,>JC		|0 0 1 1|1 1 1 1|		Skip E Zero
INA	dev		|0 1 0 0| dev	|
OTA	dev		|0 1 0 1| dev	|
NOP	-		|0 1 0 1|1 1 1 1|
LDA	reg		|0 1 1 0| reg   |
STA	reg		|0 1 1 1| reg   |
JMP	adrl,>J		|1 0 0 0|0| ahi | alo		|
JSB	adrl,>C		|1 0 0 0|1| ahi | alo		|
RTI	-		|1 0 0 1|0 0 0 0|		RTI, no ENI
JAI	-		|1 0 0 1|0| ahi |		JMP indirect indexed
JMP	dA,>J		|1 0 0 1|0 1 1 1|
CBN	bno		|1 0 1 0|0| bno |		Clear A.bit
CLC	dctl		|1 0 1 0|1| dctl|
DSI	-		|1 0 1 0|1 1 1 1|		Disable Irq
RTS	>R		|1 0 1 1|1|0 0 0|
JAS	-		|1 0 1 1|1| ahi |		JSB indirect indexed
RTE	-		|1 0 1 1|0|0 0 1|		RTI and ENI
STE	-		|1 0 1 1|0|1 0 0|		Set E
CLE	-		|1 0 1 1|0|1 0 1|		Clear E
OTR	dev,imm		|1 1 0 0| dev   | imm		|
LDR	imm		|1 1 0 0|1 1 1 1| imm		|
STR	reg,imm		|1 1 0 1| reg   | imm		|
"""

class hp_nanoproc_ins(assy.Instree_ins):
	pass

	def assy_imm(self, pj):
		return "#0x%x" % self['imm']

	def assy_adrl(self, pj):
		self.dstadr = (self.lo & 0xf800)
		self.dstadr |= (self['ahi']<<8) | self['alo']
		return assy.Arg_dst(pj.m, self.dstadr)

	def assy_reg(self, pj):
		return self.lang.reg[self['reg']]

	def assy_bno(self, pj):
		return self.lang.bno[self['bno']]

	def assy_dctl(self, pj):
		return self.lang.dctl[self['dctl']]

	def assy_dev(self, pj):
		return self.lang.dev[self['dev']]

	def assy_iA(self, pj):
		return "(0x%x+A)" % (self.lo & 0xf800)

	def assy_dA(self, pj):
		return "(0x%x-A)" % (0x800 + self.lo & 0xf800)

	def assy_S(self, pj):
		self.cc = self.mne[1:]
		self.dstadr = self.hi + 2

class hp_nanoproc(assy.Instree_disass):
	def __init__(self):
		super(hp_nanoproc, self).__init__(
                    "HP nanoprocessor",
                    ins_word=8,
                    abits=16,
                )
		self.add_ins(hp_nanoproc_desc, hp_nanoproc_ins)

		self.reg = list()
		self.dev = list()
		self.dctl = list()
		self.bno = list()
		for i in range(16):
			self.reg.append("REG%d" % i)
			self.dev.append("DEV%d" % i)
			self.dctl.append("DCTL%d" % i)
			self.bno.append("BIT%d" % i)

#######################################################################
# This is a subclass which implements the bank-switching circuitry
# used in the HP3325A and HP3336

hp_nanoproc_pg_desc="""
LJMP pgadr,>J |1 1 0 0 1 0 0 0|0 0 1 1 0| pgno|1 0 0 0|0| ahi | alo           |
LRET >R	      |0 1 1 0 1 1 1 1|0 1 0 1 1 0 0 0|1 0 1 1 1 0 0 0|
MCTL  mctl    |1 1 0 0 1 0 0 0| mctl          |
"""

class hp_nanoproc_pg_ins(hp_nanoproc_ins):
	pass

	def assy_pgadr(self, pj):
		self.dstadr = self['pgno'] << 11
		self.dstadr |= (self['ahi']<<8) | self['alo']
		return assy.Arg_dst(pj.m, self.dstadr)

	def assy_mctl(self, pj):
		self.mctl = self['mctl']
		l = list()
		if self.mctl & 0x10:
			l.append("RMA")
		if self.mctl & 0x20:
			l.append("RMB")
		if self.mctl & 0x40:
			l.append("IN")
		if self.mctl & 0x80:
			l.append("UP")
		pg = self.lo >> 11
		npg = self.mctl & 7
		if pg != npg:
			l.append("%x" % npg)
		return "+".join(l)

class hp_nanoproc_pg(hp_nanoproc):
	def __init__(self):
		super().__init__()
		self.add_ins(hp_nanoproc_pg_desc, hp_nanoproc_pg_ins)

if __name__ == "__main__":
	h = hp_nanoproc()
	h.it.print()
