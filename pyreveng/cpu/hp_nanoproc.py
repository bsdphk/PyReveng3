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
Disassembler for HP 1820-1692 "nanoprocessor"

No manuals have been found for this processor
What we know has been gleaned from schematics
and the "09411" files in bitsaver.org's HP1000
software section.

NB:
This disassembler is prepared for bank-switching, in that it
assumes that the upper (0xf800) address bits are preserved.
"""

from __future__ import print_function

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join("..")))


from pyreveng import instree, assy

# Lower-case means we guessed
# Uppercase came from 09411 listing

hp_nanoproc_instructions="""
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
OTR 	dev,imm		|1 1 0 0| dev   | imm		|
LDR	imm		|1 1 0 0|1 1 1 1| imm		|
STR	reg,imm		|1 1 0 1| reg   | imm		|
"""

class arg_imm(object):
	def __init__(self, pj, ins):
		self.value = ins.im.F_imm

	def render(self, pj):
		return "#0x%x" % self.value

class arg_adrl(assy.Arg_dst):
	def __init__(self, pj, ins):
		ins.dstadr = (ins.lo & 0xf800) | (ins.im.F_ahi<<8) | ins.im.F_alo
		super(arg_adrl, self).__init__(pj, ins.dstadr)

class arg_reg(object):
	def __init__(self, pj, ins):
		self.ins = ins
		self.reg = ins.im.F_reg

	def render(self, pj):
		return self.ins.lang.reg[self.reg]
		
class arg_bno(object):
	def __init__(self, pj, ins):
		self.ins = ins
		self.bno = ins.im.F_bno

	def render(self, pj):
		return self.ins.lang.bno[self.bno]
		
class arg_dctl(object):
	def __init__(self, pj, ins):
		self.ins = ins
		self.dctl = ins.im.F_dctl

	def render(self, pj):
		return self.ins.lang.dctl[self.dctl]
		
class arg_dev(object):
	def __init__(self, pj, ins):
		self.ins = ins
		self.dev = ins.im.F_dev

	def render(self, pj):
		return self.ins.lang.dev[self.dev]

class arg_iA(object):
	def __init__(self, pj, ins):
		ins.dstadr = None
		self.ins = ins

	def render(self, pj):
		return "(0x%x+A)" % (self.ins.lo & 0xf800)

class arg_dA(object):
	def __init__(self, pj, ins):
		ins.dstadr = None
		self.ins = ins

	def render(self, pj):
		return "(0x%x-A)" % (0x800 + self.ins.lo & 0xf800)

def ins_skip(pj, ins):
	ins.cc = ins.mne[1:]
	ins.dstadr = ins.hi + 2

class hp_nanoproc(assy.Instree_disass):
	def __init__(self):
		super(hp_nanoproc, self).__init__("HP nanoprocessor", 8)
		self.it.load_string(hp_nanoproc_instructions)
		self.args.update({
			"imm":	arg_imm,
			"adrl":	arg_adrl,
			"reg":	arg_reg,
			"bno":	arg_bno,
			"dev":	arg_dev,
			"dctl":	arg_dctl,
			"S":	ins_skip,
			"iA":	arg_iA,
			"dA":	arg_dA,
		})

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

hp_nanoproc_pg_instructions="""
LJMP pgadr,>J |1 1 0 0 1 0 0 0|0 0 1 1 0| pgno|1 0 0 0|0| ahi | alo           |
LRET >R	      |0 1 1 0 1 1 1 1|0 1 0 1 1 0 0 0|1 0 1 1 1 0 0 0|
MCTL  mctl    |1 1 0 0 1 0 0 0| mctl          |
"""

class arg_pgadr(assy.Arg_dst):
	def __init__(self, pj, ins):
		ins.dstadr = ins.im.F_pgno << 11
		ins.dstadr |= (ins.im.F_ahi<<8) | ins.im.F_alo
		super(arg_pgadr, self).__init__(pj, ins.dstadr)

class arg_mctl(object):
	def __init__(self, pj, ins):
		self.mctl = ins.im.F_mctl
		self.ins = ins

	def render(self, pj):
		l = list()
		if self.mctl & 0x10:
			l.append("RMA")
		if self.mctl & 0x20:
			l.append("RMB")
		if self.mctl & 0x40:
			l.append("IN")
		if self.mctl & 0x80:
			l.append("UP")
		pg = self.ins.lo >> 11
		npg = self.mctl & 7
		if pg != npg:
			l.append("%x" % npg)
		return "+".join(l)

class hp_nanoproc_pg(hp_nanoproc):
	def __init__(self):
		super(hp_nanoproc_pg, self).__init__()
		self.it.load_string(hp_nanoproc_pg_instructions)
		# self.it.print()
		self.args["pgadr"] = arg_pgadr
		self.args["mctl"] = arg_mctl

if __name__ == "__main__":
	h = hp_nanoproc()
	h.it.print()
