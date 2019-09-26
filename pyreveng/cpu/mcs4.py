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

'''Intel 4004/MCS-4

"Worlds First Micro Processor"
'''

from pyreveng import assy, mem

mcs4_desc="""
NOP	-		|0 0 0 0|0 0 0 0|
JCN	cc,adr,>JC	|0 0 0 1| cc    | adr		|
FIM	rr,data		|0 0 1 0| rr  |0| data		|
SRC	rr		|0 0 1 0| rr  |1|
FIN	rr,(rr0)	|0 0 1 1| rr  |0|
JIN	rr		|0 0 1 1| rr  |1|
JUN	ladr,>J		|0 1 0 0| ahi	| alo		|
JMS	ladr,>C		|0 1 0 1| ahi	| alo		|
INC	r		|0 1 1 0| r	|
ISZ	r,adr,isz,>JC	|0 1 1 1| r	| adr		|
ADD	r		|1 0 0 0| r	|
SUB	r		|1 0 0 1| r	|
LD	r		|1 0 1 0| r	|
XCH	r		|1 0 1 1| r	|
BBL	d,>R		|1 1 0 0| d	|
LDM	d		|1 1 0 1| d	|
WRM	-		|1 1 1 0|0 0 0 0|
WMP	-		|1 1 1 0|0 0 0 1|
WRR	-		|1 1 1 0|0 0 1 0|
WPM	-		|1 1 1 0|0 0 1 1|
WR0	-		|1 1 1 0|0 1 0 0|
WR1	-		|1 1 1 0|0 1 0 1|
WR2	-		|1 1 1 0|0 1 1 0|
WR3	-		|1 1 1 0|0 1 1 1|
SBM	-		|1 1 1 0|1 0 0 0|
RDM	-		|1 1 1 0|1 0 0 1|
RDR	-		|1 1 1 0|1 0 1 0|
ADM	-		|1 1 1 0|1 0 1 1|
RD0	-		|1 1 1 0|1 1 0 0|
RD1	-		|1 1 1 0|1 1 0 1|
RD2	-		|1 1 1 0|1 1 1 0|
RD3	-		|1 1 1 0|1 1 1 1|
CLB	-		|1 1 1 1|0 0 0 0|
CLC	-		|1 1 1 1|0 0 0 1|
IAC	-		|1 1 1 1|0 0 1 0|
CMC	-		|1 1 1 1|0 0 1 1|
CMA	-		|1 1 1 1|0 1 0 0|
RAL	-		|1 1 1 1|0 1 0 1|
RAR	-		|1 1 1 1|0 1 1 0|
TCC	-		|1 1 1 1|0 1 1 1|
DAC	-		|1 1 1 1|1 0 0 0|
TCS	-		|1 1 1 1|1 0 0 1|
STC	-		|1 1 1 1|1 0 1 0|
DAA	-		|1 1 1 1|1 0 1 1|
KBP	-		|1 1 1 1|1 1 0 0|
DCL	-		|1 1 1 1|1 1 0 1|
"""

class mcs4_ins(assy.Instree_ins):
	pass

	def assy_data(self, pj):
		return assy.Arg_imm(pj, self['data'], 8)

	def assy_d(self, pj):
		return assy.Arg_imm(pj, self['d'], 4)

	def assy_cc(self, pj):
		self.cc = {
			0x1: "JNT",
			0x2: "JC",
			0x4: "JZ",
			0x9: "JT",
			0xa: "JNC",
			0xc: "JNZ",
		}.get(self['cc'])
		if self.cc is None:
			self.cc = "CC#0x%x" % self['cc']
		return self.cc

	def assy_r(self, pj):
		return "r%d" % self['r']

	def assy_rr(self, pj):
		return "rr%d" % (self['rr'] << 1)

	def assy_adr(self, pj):
		self.dstadr = (self.lo & ~0xff) | self['adr']
		return assy.Arg_dst(pj, self.dstadr)

	def assy_ladr(self, pj):
		self.dstadr = (self['ahi'] << 8) | self['alo']
		return assy.Arg_dst(pj, self.dstadr)

	def assy_isz(self, pj):
		self.cc = "Z"

class mcs4(assy.Instree_disass):
	def __init__(self):
		super().__init__(
                    "mcs4",
                    ins_word=8,
                    abits=12,
                )
		self.it.load_string(mcs4_desc, mcs4_ins)
		self.verbatim.add("(rr0)")
