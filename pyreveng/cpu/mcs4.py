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
Disassembler for Intel MCS4 ("Worlds first") microprocessor
"""

from __future__ import print_function

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join("..")))

import pyreveng
import instree
import assy

mcs4_instructions="""
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

class arg_data(object):
	def __init__(self, pj, ins):
		self.value = ins.im.F_data

	def render(self, pj):
		return "#0x%02x" % self.value

class arg_d(object):
	def __init__(self, pj, ins):
		self.value = ins.im.F_d

	def render(self, pj):
		return "#0x%01x" % self.value

class arg_cc(object):
	def __init__(self, pj, ins):
		self.ins = ins
		self.cc = ins.im.F_cc
		ins.cc = self.render(pj)

	def render(self, pj):
		x = self.ins.lang.cc.get(self.cc)
		if x == None:
			return "CC#0x%x" % self.cc
		else:
			return x

class arg_r(object):
	def __init__(self, pj, ins):
		self.ins = ins
		self.reg = ins.im.F_r

	def render(self, pj):
		return "r%d" % self.reg

class arg_rr(object):
	def __init__(self, pj, ins):
		self.ins = ins
		self.reg = ins.im.F_rr << 1

	def render(self, pj):
		return "rr%d" % self.reg

class arg_adr(assy.arg_dst):
	def __init__(self, pj, ins):
		ins.dstadr = (ins.lo & ~0xff) | ins.im.F_adr
		super(arg_adr, self).__init__(pj, ins.dstadr)

class arg_ladr(assy.arg_dst):
	def __init__(self, pj, ins):
		ins.dstadr = (ins.im.F_ahi << 8) | ins.im.F_alo
		super(arg_ladr, self).__init__(pj, ins.dstadr)

def arg_isz(pj, ins):
	ins.cc = "Z"

class mcs4(assy.Instree_disass):
	def __init__(self):
		super(mcs4, self).__init__("mcs4", 8)
		self.it.load_string(mcs4_instructions)
		self.args.update( {
			"data":	arg_data,
			"d":	arg_d,
			"r":	arg_r,
			"rr":	arg_rr,
			"adr":	arg_adr,
			"ladr":	arg_ladr,
			"isz":	arg_isz,
			"cc":	arg_cc,
			"(rr0)": "(rr0)",
		})
		self.cc = {
			0x1: "JNT",
			0x2: "JC",
			0x4: "JZ",
			0x9: "JT",
			0xa: "JNC",
			0xc: "JNZ",
		}
