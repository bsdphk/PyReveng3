#!/usr/bin/env python
#
# Copyright (c) 2012-2014 Poul-Henning Kamp <phk@phk.freebsd.dk>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#notice, this list of conditions and the following disclaimer in the
#documentation and/or other materials provided with the distribution.
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
Data General Nova disassembler
"""

from pyreveng import assy

#
# From RCSL 42-i-1008 "RC3803 CPU Programmer's Reference Manual
#
nova_instructions = '''
JMP	i,db,>J			|0 0 0|0 0|i|idx|displ		|
JSR	i,db,>C			|0 0 0|0 1|i|idx|displ		|
ISZ	i,da,sz,>JC		|0 0 0|1 0|i|idx|displ		|
DSZ	i,da,sz,>JC		|0 0 0|1 1|i|idx|displ		|
LDA	acd,i,da		|0|0 1|acd|i|idx|displ		|
STA	acs,i,da		|0|1 0|acs|i|idx|displ		|
ADD	c,sh,n,acs,acd,skip,>JC	|1|acs|acd|1 1 0|sh | c |n|skip |
SUB	c,sh,n,acs,acd,skip,>JC	|1|acs|acd|1 0 1|sh | c |n|skip |
NEG	c,sh,n,acs,acd,skip,>JC	|1|acs|acd|0 0 1|sh | c |n|skip |
ADC	c,sh,n,acs,acd,skip,>JC	|1|acs|acd|1 0 0|sh | c |n|skip |
MOV	c,sh,n,acs,acd,skip,>JC	|1|acs|acd|0 1 0|sh | c |n|skip |
INC	c,sh,n,acs,acd,skip,>JC	|1|acs|acd|0 1 1|sh | c |n|skip |
COM	c,sh,n,acs,acd,skip,>JC	|1|acs|acd|0 0 0|sh | c |n|skip |
AND	c,sh,n,acs,acd,skip,>JC	|1|acs|acd|1 1 1|sh | c |n|skip |
DIA	f,acd,dev		|0 1 1|acd|0 0 1| f | dev	|
DIB	f,acd,dev		|0 1 1|acd|0 1 1| f | dev	|
DIC	f,acd,dev		|0 1 1|acd|1 0 1| f | dev	|
DOA	f,acs,dev		|0 1 1|acs|0 1 0| f | dev	|
DOB	f,acs,dev		|0 1 1|acs|1 0 0| f | dev	|
DOC	f,acs,dev		|0 1 1|acs|1 1 0| f | dev	|
SKP	t,dev,>JC		|0 1 1|0 0|1 1 1| t | dev	|
NIO	f,dev			|0 1 1|0 0|0 0 0| f | dev	|
INTEN	-			|0 1 1|0 0|0 0 0|0 1|1 1 1 1 1 1|
INTDS	-			|0 1 1|0 0|0 0 0|1 0|1 1 1 1 1 1|
READS	f,acd			|0 1 1|acd|0 0 1| f |1 1 1 1 1 1|
INTA	f,acd			|0 1 1|acd|0 1 1| f |1 1 1 1 1 1|
MSKO	f,acs			|0 1 1|acs|1 0 0| f |1 1 1 1 1 1|
IORST   f,acs			|0 1 1|acs|1 0 1| f |1 1 1 1 1 1|
HALT	f,acs			|0 1 1|acs|1 1 0| f |1 1 1 1 1 1|
'''

#
# From RCSL 42-i-1008 "RC3803 CPU Programmer's Reference Manual
#
rc3803_ins = '''
EN128K	-			|0 1 1|x x|1 0 1|1 1|0 0 0 0 0 1|
TST128K	-			|0 1 1|0 0|1 1 1|1 0|0 0 0 0 0 1|
IDFY	-			|0 1 1|acs|0 0 1|0 0|0 0 0 0 1 0|
LDB	-			|0 1 1|0 0|1 0 1|1 0|0 0 0 0 0 1|
STB	-			|0 1 1|0 0|1 1 0|1 0|0 0 0 0 0 1|
BMOVE	-			|0 1 1|x x|1 0 1|0 0|0 0 0 0 1 0|
WMOVE	-			|0 1 1|x x|1 0 1|0 1|0 0 0 0 1 0|
SCHEL	-			|0 1 1|x x|1 0 1|1 0|0 0 0 0 1 0|
SFREE	-			|0 1 1|x x|1 0 1|1 1|0 0 0 0 1 0|
LINK	-			|0 1 1|x x|1 1 0|0 0|0 0 0 0 1 0|
REMEL	-			|0 1 1|x x|1 1 0|0 1|0 0 0 0 1 0|
PLINK	-			|0 1 1|x x|1 1 0|1 0|0 0 0 0 1 0|
FETCH	-			|0 1 1|x x|1 1 0|1 1|0 0 0 0 1 0|
TKADD	-			|0 1 1|x x|1 1 1|0 0|0 0 0 0 1 0|
TKVAL	-			|0 1 1|x x|1 1 1|0 1|0 0 0 0 1 0|
COMP	-			|0 1 1|x x|1 1 1|1 0|0 0 0 0 1 0|
'''

DEVNAMES = {
	0x08: "TTYI",
	0x09: "TTYO",
	0x0a: "PTR",
	0x0b: "PTP",
	0x0c: "RTC",
	0x0f: "LPT",
	0x18: "MT",
	0x2a: "AMX",
	0x31: "FD0",
	0x34: "FD1",
	0x3b: "DKP",
	0x3f: "CPU",
}

class nova_ins(assy.Instree_ins):

	def assy_sz(self, pj):
		self.dstadr = self.hi + 1

	def assy_sh(self, pj):
		r = (None, "L", "R", "S")[self["sh"]]
		if r:
			self.mne += r

	def assy_skip(self, unused__pj):
		r = (None, "SKP", "SZC", "SNC",
			 "SZR", "SNR", "SEZ", "SEN")[self["skip"]]
		if r:
			self.dstadr = self.hi + 1
		return r

	def assy_c(self, pj):
		r = (None, "Z", "O", "C")[self["c"]]
		if r is not None:
			self.mne += r

	def assy_i(self, pj):
		if self["i"]:
			self.mne += "@"

	def assy_n(self, pj):
		if self["n"]:
			self.mne += "#"

	def assy_acs(self, pj):
		return "%d" % self["acs"]

	def assy_acd(self, pj):
		return "%d" % self["acd"]

	def assy_dev(self, pj):
		t = DEVNAMES.get(self["dev"])
		if t is None:
			return "0x%x" % self["dev"]
		return t

	def assy_t(self, pj):
		self.dstadr = self.hi + 1
		self.mne += ["BN", "BZ", "DN", "DZ"][self["t"]]

	def assy_f(self, pj):
		self.mne += ["", "S", "C", "P"][self["f"]]

	def assy_da(self, pj):
		i = self["idx"]
		d = self["displ"]
		t = None
		if i == 0:
			t = d
		else:
			if d & 0x80:
				d -= 256
			if i == 1:
				t = self.lo + d
		if t is None:
			if d < 0:
				return "-0x%x,%d" % (-d, i)
			return "0x%x,%d" % (d, i)
		if not self['i']:
			self.dstadr = t
		return assy.Arg_dst(pj, t)

	def assy_db(self, pj):
		r = self.assy_da(pj)
		if not isinstance(r, assy.Arg_dst):
			return r
		if not self['i']:
			return r
		t = pj.m[r.dst]
		if t:
			pj.todo(t, self.lang.disass)
		return r

class nova(assy.Instree_disass):
	def __init__(self):
		super().__init__("nova", 16)
		self.add_ins(nova_instructions, nova_ins)
