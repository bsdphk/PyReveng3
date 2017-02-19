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
#
# Ideas:  "DEFAULT_VECTOR" to target having most vectors pointed at it

"""
Disassembler for M68000 familiy CPUs.

Presently supported variants:
	68000
"""

from __future__ import print_function
from pyreveng import assy, data

m68000_instructions = """
#		src,dst		ea	|_ _ _ _|_ _ _v_|_ _v_ _|_v_ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|
# 107/4-3
aBCD		B,Dy,Dx		0000	|1 1 0 0| Dx  |1 0 0 0 0|0| Dy  |
ABCD		B,decAy,decAx	0000	|1 1 0 0| Ax  |1 0 0 0 0|1| Ay  |
# 108/4-4
ADD		Z,Dn,ea		037d	|1 1 0 1| Dn  |1| sz| ea	|
ADD		Z,ea,Dn		1f7f	|1 1 0 1| Dn  |0| sz| ea	|
# 111/4-7
ADDA		W,ea,An		1f7f	|1 1 0 1| An  |0 1 1| ea	|
ADDA		L,ea,An		1f7f	|1 1 0 1| An  |1 1 1| ea	|
# 113/4-9
ADDI		Z,data,ea	037d	|0 0 0 0 0 1 1 0| sz| ea	|
# 115/4-11
# FIX ADDQ.B ->An sounds bogus, and unreferenced '*' footnote indicates not available
ADDQ		Z,const,ea	037f	|0 1 0 1|const|0| sz| ea	|
# 117/4-13
# Collision with ADDA.L
ADDX		Z,Dy,Dx		0000	|1 1 0 1| Dx  |1| sz|0 0|0| Dy  |
ADDX		Z,decAy,decAx	0000	|1 1 0 1| Ax  |1| sz|0 0|1| Ay  |
# 119/4-15
# XXX AND.W An,Dn sounds like it should be possible ?
AND		Z,ea,Dn		1f7d	|1 1 0 0| Dn  |0| sz| ea	|
AND		Z,Dn,ea		037c	|1 1 0 0| Dn  |1| sz| ea	|
# 122/4-18
ANDI		Z,data,ea	037d	|0 0 0 0 0 0 1 0| sz| ea	|
# 124/4-20
ANDI		B,const,CCR	0000	|0 0 0 0|0 0 1 0|0 0 1 1|1 1 0 0|0 0 0 0|0 0 0 0| const		|
# 125/4-21
ASL		Z,Dx,Dy		0000	|1 1 1 0| Dx  |1| sz|1|0 0| Dy  |
ASR		Z,Dx,Dy		0000	|1 1 1 0| Dx  |0| sz|1|0 0| Dy  |
ASL		Z,rot,Dn	0000	|1 1 1 0|  rot|1| sz|0|0 0| Dn  |
ASR		Z,rot,Dn	0000	|1 1 1 0|  rot|0| sz|0|0 0| Dn  |
aSL		W,ea		037c	|1 1 1 0|0 0 0|1|1 1| ea	|
aSR		W,ea		037c	|1 1 1 0|0 0 0|0|1 1| ea	|
# 129/4-25
B		cc,dst,>JC	0000	|0 1 1 0| cc    | disp8		|
# 131/4-27
bCHG		B,Dn,ea		037c	|0 0 0 0| Dn  |1 0 1| ea	|
BCHG		L,Dx,Dy		0000	|0 0 0 0| Dx  |1 0 1|0 0 0| Dy  |
BCHG		B,bn,ea		037c	|0 0 0 0|1 0 0|0 0 1| ea	|0 0 0 0|0 0 0 0| bn		|
BCHG		L,bn,Dn		0000	|0 0 0 0|1 0 0|0 0 1|0 0 0| Dn  |0 0 0 0|0 0 0 0| bn		|
# 134/4-30
BCLR		B,Dn,ea		037c	|0 0 0 0| Dn  |1 1 0| ea	|
BCLR		L,Dx,Dy		0000	|0 0 0 0| Dx  |1 1 0|0 0 0| Dy  |
BCLR		B,bn,ea		037c	|0 0 0 0|1 0 0|0 1 0| ea	|0 0 0 0|0 0 0 0| bn		|
BCLR		L,bn,Dn		0000	|0 0 0 0|1 0 0|0 1 0|0 0 0| Dn  |0 0 0 0|0 0 0 0| bn		|
# 159/4-55
BRA		dst,>J		0000	|0 1 1 0|0 0 0 0| disp8		|
# 160/4-56
BSET		B,Dn,ea		037c	|0 0 0 0| Dn  |1 1 1| ea	|
BSET		L,Dx,Dy		0000	|0 0 0 0| Dx  |1 1 1|0 0 0| Dy  |
BSET		B,bn,ea		037c	|0 0 0 0|1 0 0|0 1 1| ea	|0 0 0 0|0 0 0 0| bn		|
BSET		L,bn,Dn		0000	|0 0 0 0|1 0 0|0 1 1|0 0 0| Dn  |0 0 0 0|0 0 0 0| bn		| {
	%0 = and i32 DN , BN
	%CCR.z = icmp eq i32 %0 , 0
	DN = or i32 DN , BN
}
# 163/4-59
BSR		dst,>C		0000	|0 1 1 0|0 0 0 1| disp8		|
# 165/4-61
BTST		B,Dn,ea		037c	|0 0 0 0| Dn  |1 0 0| ea	|
BTST		L,Dx,Dy		0000	|0 0 0 0| Dx  |1 0 0|0 0 0| Dy  |
BTST		B,bn,ea		037c	|0 0 0 0|1 0 0|0 0 0| ea	|0 0 0 0|0 0 0 0| bn		|
BTST		L,bn,Dn		0000	|0 0 0 0|1 0 0|0 0 0|0 0 0| Dn  |0 0 0 0|0 0 0 0| bn		|
# 173/4-69
cHK		W,ea,Dn		1f7d	|0 1 0 0| Dn  |1 1|0| ea	|
CHK		L,ea,Dn		1f7d	|0 1 0 0| Dn  |1 0|0| ea	|
# 177/4-73
CLR		Z,ea		037d	|0 1 0 0|0 0 1 0| sz| ea	|
# 179/4-75
CMP		Z,ea,Dn		1f7f	|1 0 1 1| Dn  |0| sz| ea	|
# 181/4-77
CMPA		W,ea,An		1f7f	|1 0 1 1| An  |0|1 1| ea	|
CMPA		L,ea,An		1f7f	|1 0 1 1| An  |1 1 1| ea	|
# 183/4-79
CMPI		Z,data,ea	0f7d	|0 0 0 0|1 1 0 0| sz| ea	|
# 185/4-81
CMPM		Z,Ayinc,Axinc	0000	|1 0 1 1| Ax  |1| sz|0 0 1| Ay  |
# 194/4-90
DB		cc,Dn,disp16,>JC	0000	|0 1 0 1| cc    |1 1 0 0 1| Dn  | disp16			|
# 196/4-92
DIVS		W,ea,Dn		1f7d	|1 0 0 0| Dn  |1 1 1| ea	|
# 201/4-97
DIVU		W,ea,Dn		1f7d	|1 0 0 0| Dn  |0 1 1| ea	|
# 204/4-100
EOR		Z,Dn,ea		037d	|1 0 1 1| Dn  |1| sz| ea	|
# 206/4-102
EORI		Z,data,ea	037d	|0 0 0 0|1 0 1 0| sz| ea	|
# 208/4-104
eORI		B,const,CCR	0000	|0 0 0 0|1 0 1 0|0 0|1 1 1|1 0 0|0 0 0 0|0 0 0 0| const		|
# 209/4-105
EXG		L,Dx,Dy		0000	|1 1 0 0| Dx  |1|0 1 0 0 0| Dy  |
EXG		L,Ax,Ay		0000	|1 1 0 0| Ax  |1|0 1 0 0 1| Ay  |
EXG		L,Dx,Ay		0000	|1 1 0 0| Dx  |1|1 0 0 0 1| Ay  |
# 210/4-106
EXTB		W,Dn		0000	|0 1 0 0|1 0 0|0 1 0|0 0 0| Dn  |
EXTW		L,Dn		0000	|0 1 0 0|1 0 0|0 1 1|0 0 0| Dn  |
EXTB		L,Dn		0000	|0 1 0 0|1 0 0|1 1 1|0 0 0| Dn  |
# 211/4-107
iLLEGAL		-		0000	|0 1 0 0|1 0 1 0|1 1 1 1|1 1 0 0|
# 212/4-108
JMP		ea,>J		0f64	|0 1 0 0|1 1 1 0|1 1| ea	|
# 213/4-109
JSR		ea,>C		0f64	|0 1 0 0|1 1 1 0|1 0| ea	|
# 214/4-110
LEA		L,ea,An		0f64	|0 1 0 0| An  |1 1 1| ea	|
# 215/4-111
LINK		W,An,word	0000	|0 1 0 0|1 1 1 0|0 1 0 1|0| An  | word				|
# 217/4-113
LSL		Z,Dx,Dy		0000	|1 1 1 0| Dx  |1| sz|1|0 1| Dy  |
LSR		Z,Dx,Dy		0000	|1 1 1 0| Dx  |0| sz|1|0 1| Dy  |
LSL		Z,rot,Dn	0000	|1 1 1 0|  rot|1| sz|0|0 1| Dn  |
LSR		Z,rot,Dn	0000	|1 1 1 0|  rot|0| sz|0|0 1| Dn  |
lSL		W,ea		037c	|1 1 1 0|0 0 1|1|1 1| ea	|
LSR		W,ea		037c	|1 1 1 0|0 0 1|0|1 1| ea	|
# 220/4-116 NB! Not the usual BWL encoding
MOVE		B,ea,ead	1f7f	|0 0|0 1|earx |eamx | ea	| {
	%0 = i8 EA
	EAD %0
	%CCR.z = icmp eq i8 %0 , 0
	%CCR.n = icmp slt i8 %0 , 0
	%CCR.v = i1 0
	%CCR.c = i1 0
}
MOVE		L,ea,ead	1f7f	|0 0|1 0|earx |eamx | ea	| {
	%0 = i32 EA
	EAD %0
	%CCR.z = icmp eq i32 %0 , 0
	%CCR.n = icmp slt i32 %0 , 0
	%CCR.v = i1 0
	%CCR.c = i1 0
}
MOVE		W,ea,ead	1f7f	|0 0|1 1|earx |eamx | ea	| {
	%0 = i16 EA
	EAD %0
	%CCR.z = icmp eq i16 %0 , 0
	%CCR.n = icmp slt i16 %0 , 0
	%CCR.v = i1 0
	%CCR.c = i1 0
}
# 223/4-119
MOVEA		W,ea,An		1f7f	|0 0|1 1| An  |0 0 1| ea	| {
	AN EA
}
MOVEA		L,ea,An		1f7f	|0 0|1 0| An  |0 0 1| ea	| {
	AN EA
}
# 225/4-121
MOVE		W,CCR,ead	037d	|0 1 0 0|0 0 1|0 1 1| eamx| earx| {
	EAD %CCR
}
# 227/4-123
MOVE		W,ea,CCR	1f7d	|0 1 0 0|0 1 0|0 1 1| ea	| {
	%CCR = i16 EA
}
# 229/4-125
MOVE		W,SR,ead	037d	|0 1 0 0|0 0 0|0 1 1| eamx| earx| {
	EAD %SR
}
# 232/4-128
MOVEM		W,rlist,ea	0374	|0 1 0 0|1 0 0|0 1 0| ea	| rlist				|
MOVEM		L,rlist,ea	0374	|0 1 0 0|1 0 0|0 1 1| ea	| rlist				|
MOVEM		W,ea,rlist	0f6c	|0 1 0 0|1 1 0|0 1 0| ea	| rlist				|
MOVEM		L,ea,rlist	0f6c	|0 1 0 0|1 1 0|0 1 1| ea	| rlist				|
# 235/4-131
MOVEP		W,Dn,An+disp16	0000	|0 0 0 0| Dn  |1|1 0|0 0 1| An  | disp16			|
MOVEP		L,Dn,An+disp16	0000	|0 0 0 0| Dn  |1|1 1|0 0 1| An  | disp16			|
MOVEP		W,An+disp16,Dn	0000	|0 0 0 0| Dn  |1|0 0|0 0 1| An  | disp16			|
MOVEP		L,An+disp16,Dn	0000	|0 0 0 0| Dn  |1|0 1|0 0 1| An  | disp16			|
# 238/4-134
MOVEQ		L,data8,Dn	0000	|0 1 1 1| Dn  |0| data8		|
# 239/4-135
MULS		W,ea,Dn		1f7d	|1 1 0 0| Dn  |1 1 1| ea	|
# 243/4-139
MULU		W,ea,Dn		1f7d	|1 1 0 0| Dn  |0 1 1| ea	|
# 245/4-141
NBCD		B,ea		037d	|0 1 0 0|1 0 0|0 0 0| ea	|
# 247/4-143
NEG		Z,ea		037d	|0 1 0 0|0 1 0|0| sz| ea	|
# 249/4-146
NEGX		Z,ea		037d	|0 1 0 0|0 0 0|0| sz| ea	|
# 251/4-147
NOP		-		0000	|0 1 0 0|1 1 1|0 0 1|1 1 0|0 0 1| {
	%0 = i32 0
}
# 252/4-148
NOT		Z,ead		037d	|0 1 0 0|0 1 1|0| sz| eamx| earx|
# 254/4-150
OR		Z,ea,Dn		1f7d	|1 0 0 0| Dn  |0| sz| ea	|
OR		Z,Dn,ea		037c	|1 0 0 0| Dn  |1| sz| ea	|
# 257/4-153
ORI		Z,data,ea	037d	|0 0 0 0|0 0 0 0| sz| ea	|
# 259/4-155
ORI		word,CCR	0000	|0 0 0 0|0 0 0 0|0 0 1 1|1 1 0 0|0 0 0 0|0 0 0 0| word		|
# 263/4-159
PEA		L,ea		0f64	|0 1 0 0|1 0 0|0 0 1| ea	|
# 264/4-160
ROL		Z,Dx,Dy		0000	|1 1 1 0| Dx  |1| sz|1|1 1| Dy  |
ROR		Z,Dx,Dy		0000	|1 1 1 0| Dx  |0| sz|1|1 1| Dy  |
ROL		Z,rot,Dn	0000	|1 1 1 0|  rot|1| sz|0|1 1| Dn  |
ROR		Z,rot,Dn	0000	|1 1 1 0|  rot|0| sz|0|1 1| Dn  |
rOL		W,ea		037c	|1 1 1 0|0 1 1|1|1 1| ea	|
rOR		W,ea		037c	|1 1 1 0|0 1 1|0|1 1| ea	|
# 267/4-163
rOXL		Z,Dx,Dy		0000	|1 1 1 0| Dx  |1| sz|1|1 0| Dy  |
rOXR		Z,Dx,Dy		0000	|1 1 1 0| Dx  |0| sz|1|1 0| Dy  |
ROXL		Z,rot,Dn	0000	|1 1 1 0|  rot|1| sz|0|1 0| Dn  |
ROXR		Z,rot,Dn	0000	|1 1 1 0|  rot|0| sz|0|1 0| Dn  |
rOXL		W,ea		037c	|1 1 1 0|0 1 0|1|1 1| ea	|
rOXR		W,ea		037c	|1 1 1 0|0 1 0|0|1 1| ea	|
# 272/4-168
RTR		-		0000	|0 1 0 0|1 1 1 0|0 1 1 1|0 1 1 1|
# 273/4-169
RTS		>R		0000	|0 1 0 0|1 1 1 0|0 1 1 1|0 1 0 1|
# 274/4-170
sBCD		B,Dx,Dy		0000	|1 0 0 0| Dy  |1 0 0 0 0|0| Dx  |
SBCD		B,decAx,decAy	0000	|1 0 0 0| Ay  |1 0 0 0 0|1| Ax  |
# 276/4-172
S		cc,B,ea		037d	|0 1 0 1| cc    |1 1| ea	|
# 278/4-174
SUB		Z,ea,Dn		1f7f	|1 0 0 1| Dn  |0| sz| ea	|
SUB		Z,Dn,ea		037c	|1 0 0 1| Dn  |1| sz| ea	|
# 281/4-177
SUBA		W,ea,An		1f7f	|1 0 0 1| An  |0 1 1| ea	|
SUBA		L,ea,An		1f7f	|1 0 0 1| An  |1 1 1| ea	|
# 283/4-179
SUBI		Z,data,ea	037d	|0 0 0 0|0 1 0 0| sz| ea	|
# 285/4-181
SUBQ		Z,const,ea	037f	|0 1 0 1|const|1| sz| ea	|
# 287/4-183
SUBX		Z,Dx,Dy		0000	|1 0 0 1| Dy  |1| sz|0 0|0| Dx  |
SUBX		Z,decAx,decAy	0000	|1 0 0 1| Ay  |1| sz|0 0|1| Ax  |
# 289/4-185
SWAP		W,Dn		0000	|0 1 0 0|1 0 0 0|0 1 0 0|0| Dn  | {
	%0 = lshr i32 DN , 16
	%1 = shl i32 DN , 16
	DN = or i32 %0 , %1
	%CCR.n = icmp slt i32 DN , 0
	%CCR.z = icmp eq i32 DN , 0
	%CCR.v = i1 0
	%CCR.c = i1 0
}
# 290/4-186
tAS		B,ea		037d	|0 1 0 0|1 0 1 0|1 1| ea	|
# 292/4-188
TRAP		vect		0000	|0 1 0 0|1 1 1 0|0 1 0 0| vect	|
# 295/4-191
tRAPV		-		0000	|0 1 0 0|1 1 1 0|0 1 1 1|0 1 1 0|
# 296/4-192
TST		Z,ea		1f7f	|0 1 0 0|1 0 1 0| sz| ea	|
# 298/4-194
UNLK		An		0000	|0 1 0 0|1 1 1 0|0 1 0 1|1| An  |
# 456/6-2
ANDI		W,word,SR	0000	|0 0 0 0|0 0 1 0|0 1 1 1|1 1 0 0| word				|
# 464/6-10
eORI		W,word,SR	0000	|0 0 0 0|1 0 1 0|0 1 1 1|1 1 0 0| word				|
# 473/6-19
MOVE		W,ea,SR		1f7d	|0 1 0 0|0 1 1 0|1 1| ea	| {
	%SR = i16 EA
}
# 475/6-21
MOVE		L,An,USP	0000	|0 1 0 0|1 1 1 0|0 1 1 0|0| An  |
MOVE		L,USP,An	0000	|0 1 0 0|1 1 1 0|0 1 1 0|1| An  |
# 481/6-27
ORI		W,word,SR	0000	|0 0 0 0|0 0 0 0|0 1 1 1|1 1 0 0| word				|
# 537/6-83
RESET		-		0000	|0 1 0 0|1 1 1 0|0 1 1 1|0 0 0 0|
# 538/6-84
RTE		>R		0000	|0 1 0 0|1 1 1 0|0 1 1 1|0 0 1 1|
# 539/6-85
STOP		word,>R		0000	|0 1 0 0|1 1 1 0|0 1 1 1|0 0 1 0| word				|
# ...
# 539/6-85
#		src,dst		ea	|_ _ _ _|_ _ _v_|_ _v_ _|_v_ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|
"""
# p3-19/90
cond_code = (
	"T",  "F",  "HI", "LS", "CC", "CS", "NE", "EQ",
	"VC", "VS", "PL", "MI", "GE", "LT", "GT", "LE"
)

#######################################################################

class m68000_ins(assy.Instree_ins):
	def __init__(self, pj, lim, lang):
		super(m68000_ins, self).__init__(pj, lim, lang)
		self.ea = {}
		self.isz = "i32"

	def assy_An(self, pj):
		return "A%d" % self['An']

	def assy_decAx(self, pj):
		return "-(A%d)" % self['Ax']

	def assy_Axinc(self, pj):
		return "(A%d)+" % self['Ax']

	def assy_Ax(self, pj):
		return "A%d" % self['Ax']

	def assy_decAy(self, pj):
		return "-(A%d)" % self['Ay']

	def assy_Ayinc(self, pj):
		return "(A%d)+" % self['Ay']

	def assy_Ay(self, pj):
		return "A%d" % self['Ay']

	def assy_B(self, pj):
		self.sz = 1
		self.isz = "i8"
		self.mne += ".B"

	def assy_bn(self, pj):
		return "#0x%x" % self['bn']

	def assy_cc(self, pj):
		self.mne += cond_code[self['cc']]

	def assy_const(self, pj):
		o = self['const']
		if o == 0:
			o = 8
		return "#0x%x" % o

	def assy_data(self, pj):
		if self.sz == 1:
			self.v = pj.m.bu16(self.hi)
		elif self.sz == 2:
			self.v = pj.m.bu16(self.hi)
		elif self.sz == 4:
			self.v = pj.m.bu32(self.hi)
		else:
			assert False
		self.hi += self.sz
		if self.sz == 1:
			self.hi += 1
		return "#0x%0*x" % (self.sz * 2, self.v)

	def assy_data8(self, pj):
		return "#0x%02x" % self['data8']

	def assy_disp16(self, pj):
		o = self['disp16']
		if o & 0x8000:
			o -= 1 << 16
		self.dstadr = self.hi + o - 2
		return assy.Arg_dst(pj, self.dstadr)

	def assy_Dn(self, pj):
		return "D%d" % self['Dn']

	def assy_dst(self, pj):
		x = self['disp8']
		if x == 0x00:
			self.dstadr = self.hi + pj.m.bs16(self.hi)
			self.hi += 2
		elif x == 0xff:
			self.dstadr = self.hi + pj.m.bs32(self.hi)
			self.hi += 4
		elif x & 0x80:
			self.dstadr = self.hi + x - 0x100
		else:
			self.dstadr = self.hi + x
		return assy.Arg_dst(pj, self.dstadr)

	def assy_Dx(self, pj):
		return "D%d" % self['Dx']

	def assy_Dy(self, pj):
		return "D%d" % self['Dy']

	def assy_eaxt(self, pj, id, ref):
		'''Extension Word Controlled Address Mode'''
		il = self.ea[id]
		iltyp = self.isz + "*"
		ll = [None]
		ew = pj.m.bu16(self.hi)

		if ew & 0x100:
			print("0x%x FULL EXT WORD" % self.lo, self)
			raise assy.Invalid("FULL EXT WORD")

		if ew & 0x600:
			print("0x%x Non-zero SCALE" % self.lo, self)
			raise assy.Invalid("BAD BRIEF EXT WORD")

		self.hi += 2

		if ew & 0x8000:
			reg = "A"
		else:
			reg = "D"

		reg = reg + "%d" % ((ew >> 12) & 7)

		if ew & 0x800:
			wl = ".L"
			ll.append(
				["%2", "=", iltyp, "%" + reg]
			)
		else:
			ll.append(
				["%1", "=", "trunc", "i32", "%" + reg,
				    "to", "i16"]
			)
			ll.append(
				["%2", "=", "sext", "i16", "%1",
				    "to", iltyp]
			)
			wl = ".W"
		ll[0] = "%2"

		scl = (ew >> 9) & 3
		sc = 1 << scl
		if scl != 0:
			ll.append(
				["%3", "=", "shl", iltyp, "%0", ",", "%d" % scl]
			)
			ll[0] = "%3"

		d = ew & 0xff
		if d & 0x80:
			d -= 0x100
		if d > 0:
			ll.append(
				["%4", "=", "add", iltyp, ll[0], ",",
				    "0x%x" % d]
			)
			ll[0] = "%4"
		if d < 0:
			ll.append(
				["%4", "=", "sub", iltyp, ll[0], ",",
				    "0x%x" % -d]
			)
			ll[0] = "%4"

		ll.append(
		    ["%5", "=", "add", iltyp, ll[0], ",", "%" + ref]
		)
		ll[0] = "%5"

		s = "("
		if ref == "PC":
			s += "#0x%x" % (d + self.hi - 2)
		elif d != 0:
			s += "#0x%x+" % d + ref
		else:
			s += ref
		s += "+" + reg + wl
		if sc > 1:
			s += "*%d" % sc
		s += ")"
		if id == "s":
			il += [ll[0], ll[1:]]
		elif id == "d":
			ll.append(
				["store", self.isz, "%0", ",",
				    iltyp, ll[0]]
			)
			il += [None, ll[1:]]
		return s


	def assy_eax(self, pj, id, eam, ear):
		il = []
		self.ea[id] = il
		eax = 1 << eam
		if eax > 0x40:
			eax = 0x100 << ear
		eamask = int(self.im.assy[-1], 16)
		if not eax & eamask:
			print ("0x%x Wrong EA mode m=%d/r=%d" % (self.lo, eam, ear))
			raise assy.Invalid("0x%x Wrong EA mode m=%d/r=%d" % (
			    self.lo, eam, ear))
		if eax == 0x0001:
			il.append("%%D%d" % ear)
			return "D%d" % ear
		if eax == 0x0002:
			il.append("%%A%d" % ear)
			return "A%d" % ear
		if eax == 0x0004:
			if id == "s":
				il += [ "%0", [
				    ["%0", "=", "load", self.isz, ",",
					self.isz + "*", "%%A%d" % ear],
				]]
			if id == "d":
				il += [ None, [
				    ["store", self.isz, "%0", ",",
					self.isz + "*", "%%A%d" % ear],
				]]
			return "(A%d)" % ear
		if eax == 0x0008:
			r = "A%d" % ear
			if id == "s":
				il += [ "%0", [
				    ["%0", "=", "load", self.isz, ",",
					self.isz + "*", "%%A%d" % ear],
				    ["%" + r, "=", "add", "i32",
					"%" + r, ",", "%d" % self.sz],
				]]
			elif id == "d":
				il += [ None, [
				    ["store", self.isz, "%0", ",",
					self.isz + "*", "%%A%d" % ear],
				    ["%" + r, "=", "add", "i32",
					"%" + r, ",", "%d" % self.sz],
				]]
			return "(A%d)+" % ear
		if eax == 0x0010:
			'''Address Register Indirect with Predecrement'''
			r = "A%d" % ear
			if id == "s":
				il += [ "%0", [
				    ["%" + r, "=", "sub", "i32",
					"%" + r, ",", "%d" % self.sz],
				    ["%0", "=", "load", self.isz, ",",
					self.isz + "*", "%" +r],
				]]
			elif id == "d":
				il += [ None, [
				    ["%" + r, "=", "sub", "i32",
					"%" + r, ",", "%d" % self.sz],
				    ["store", self.isz, "%0", ",",
					self.isz + "*", "%" +r],
				]]
			return "-(%s)" % r
		if eax == 0x0020:
			'''Address Register Indirect with Displacement'''
			o = pj.m.bs16(self.hi)
			self.hi += 2
			if id == "s":
				il += [ "%0", [
				    ["%1", "=", "add", self.isz + "*",
					"%%A%d" % ear, ",", "0x%x" % o],
				    ["%0", "=", "load", self.isz, ",",
					self.isz + "*", "%1"],
				]]
			elif id == "d":
				il += [ None, [
				    ["%1", "=", "add", self.isz + "*",
					"%%A%d" % ear, ",", "0x%x" % o],
				    ["store", self.isz, "%0", ",",
					self.isz + "*", "%1"],
				]]
			if o < 0:
				return "(A%d-0x%x)" % (ear, -o)
			else:
				return "(A%d+0x%x)" % (ear, o)
		if eax == 0x0040:
			return self.assy_eaxt(pj, id, "A%d" % ear)
		if eax == 0x0100:
			o = pj.m.bu16(self.hi)
			self.hi += 2
			if o & 0x8000:
				o |= 0xffff0000
			self.dstadr = o
			if id == "s":
				il += [ "%0", [
				    [ "%0", "=", "load", self.isz, ",",
					self.isz + "*", "0x%x" % o],
				]]
			elif id == "d":
				il += [ None, [
				    [ "store", self.isz, "%0", ",",
					self.isz + "*", "0x%x" % o],
				]]
			return assy.Arg_dst(pj, o)
		if eax == 0x0200:
			o = pj.m.bu32(self.hi)
			self.hi += 4
			self.dstadr = o
			if id == "s":
				il += [ "%0", [
				    [ "%0", "=", "load", self.isz, ",",
					self.isz + "*", "0x%x" % o],
				]]
			elif id == "d":
				il += [ None, [
				    [ "store", self.isz, "%0", ",",
					self.isz + "*", "0x%x" % o],
				]]
			return assy.Arg_dst(pj, o)
		if eax == 0x0400:
			o = self.hi + pj.m.bs16(self.hi)
			self.hi += 2
			self.dstadr = o
			if id == "s":
				il += [ "%0", [
				    [ "%0", "=", "load", self.isz, ",",
					self.isz + "*", "0x%x" % o],
				]]
			elif id == "d":
				il += [ None, [
				    [ "store", self.isz, "%0", ",",
					self.isz + "*", "0x%x" % o],
				]]
			return assy.Arg_dst(pj, o)
		if eax == 0x0800:
			return self.assy_eaxt(pj, id, "PC")
		if eax == 0x1000 and self.sz == 1:
			v = pj.m.rd(self.hi+1)
			self.hi += 2
			il += ["0x%x" % v]
			return "#0x%02x" % v
		if eax == 0x1000 and self.sz == 2:
			v = pj.m.bu16(self.hi)
			self.hi += 2
			il += ["0x%x" % v]
			return "#0x%04x" % v
		if eax == 0x1000 and self.sz == 4:
			v = pj.m.bu32(self.hi)
			self.hi += 4
			il += ["0x%x" % v]
			return "#0x%08x" % v
		print("0x%x EA? 0x%04x m=%d/r=%d" % (self.lo, eax, eam, ear))
		raise assy.Invalid(
		    "0x%x EA? 0x%04x m=%d/r=%d" % (self.lo, eax, eam, ear))

	def assy_ea(self, pj):
		j = self['ea']
		return self.assy_eax(pj, "s", j >> 3, j & 7)

	def assy_ead(self, pj):
		return self.assy_eax(pj, "d", self['eamx'], self['earx'])

	def assy_L(self, pj):
		self.sz = 4
		self.isz = "i32"
		self.mne += ".L"

	def assy_rlist(self, pj):
		v = self['rlist']
		l = []
		if (self['ea'] >> 3) == 4:
			for r in ("A", "D"):
				for n in range(7, -1, -1):
					if v & 0x0001:
						l.append(r + "%d" % n)
					v >>= 1
		else:
			for r in ("D", "A"):
				for n in range(0, 8):
					if v & 0x0001:
						l.append(r + "%d" % n)
					v >>= 1
		return "+".join(l)

	def assy_rot(self, pj):
		a = self['rot']
		if a == 0:
			a = 8
		return "#0x%x" % a

	def assy_vect(self, pj):
		return "#%d" % self['vect']

	def assy_W(self, pj):
		self.sz = 2
		self.isz = "i16"
		self.mne += ".W"

	def assy_word(self, pj):
		return "#0x%04x" % self['word']

	def assy_Z(self, pj):
		if self['sz'] == 3:
			raise assy.Invalid('0x%x F_sz == 3' % self.lo)
		i, j = [
			[1, ".B"],
			[2, ".W"],
			[4, ".L"],
		] [self['sz']]
		self.sz = i
		self.isz = "i%d" % (i*8)
		self.mne += j

	def ilmacro_BN(self):
		return "0x%x" % (1 << self['bn'])

	def ilmacro_DN(self):
		return "%%D%d" % self['Dn']

	def ilmacro_EA(self):
		il = self.ea["s"]
		if len(il) > 1:
			return self.add_il(il[1],il[0])
		elif len(il) > 0:
			return il[0]
		return "XXX EA %d %d %s" % (self['eam'], self['ear'], str(il))

	def ilmacro_SZ(self):
		return self.isz

	def ilfunc_AN(self, arg):
		self.add_il([
			[ "%%A%d" % self['An'], "=", self.isz, arg[0] ],
		])

	def ilfunc_EAD(self, arg):
		il = self.ea["d"]
		if len(il) == 1:
			self.add_il([
			    [ il[0], "=", self.isz, arg[0]],
			])
			return
		elif len(il) == 2 and il[0] is None:
			ll = [
			    [ "%0", "=", self.isz, arg[0]],
			]
			ll += il[1]
			self.add_il(ll)
		else:
			e = "XXX EAD eam %d ear %d il %s arg %s" % (self['eamx'], self['earx'], str(il), str(arg))
			self.add_il([[ e ]])
			print(self, e)

class m68000(assy.Instree_disass):
	def __init__(self, lang="m68000"):
		super(m68000, self).__init__(
		    lang,
		    ins_word=16,
		    mem_word=8,
		    endian=">")
		self.it.load_string(m68000_instructions)
		self.il = None
		self.myleaf = m68000_ins
		self.verbatim |= set(["CCR", "SR", "USP"])

	def set_adr_mask(self, a):
		self.amask = a

	def vector_name(self, v):
		n = {
			1: "RESET",
			2: "BUS_ERROR",
			3: "ADDRESS_ERROR",
			4: "ILLEGAL_INSTRUCTION",
			5: "ZERO_DIVIDE",
			6: "CHK",
			7: "TRAPV",
			8: "PRIV_VIOLATION",
			9: "TRACE",
			10: "LINE_A",
			11: "LINE_F",
			15: "UNINIT_VEC",
			24: "SPURIOUS_IRQ",
		}.get(v)
		if n != None:
			return "VECTOR_" + n
		if v >= 25 and v <= 31:
			return "VECTOR_IRQ_LEVEL_%d" % (v - 24)
		if v >= 32 and v <= 47:
			return "VECTOR_TRAP_%d" % (v - 32)
		return "VECTOR_%d" % v

	def vectors(self, pj, hi=0x400):
		y = data.Const(pj, 0, 4, "0x%08x", pj.m.bu32, 4)
		y.lcmt = "Reset SP"
		vn = {}
		vi = {}
		a = 0x4
		while a < hi:
			x = pj.m.bu32(a)
			if x in (0x0, 0xffffffff):
				y = data.Const(pj, a, a + 4,
				    "0x%04x", pj.m.bu32, 4)
			else:
				if x not in vn:
					vi[x] = self.disass(pj, x)
					vn[x] = []
				vn[x].append(a >> 2)
				if x > a:
					y = data.Codeptr(pj, a, a + 4, x)
			y.lcmt = self.vector_name(a >> 2)
			hi = min(hi, x)
			a += 4
		mv = 0
		for i in vn:
			for v in vn[i]:
				k = self.vector_name(v)
				if vi[i] != None:
					vi[i].lcmt += "--> " + k + "\n"

			if len(vn[i]) == 1:
				k = self.vector_name(vn[i][0])
				pj.set_label(i, k)
			else:
				pj.set_label(i, "VECTORS_%d" % mv)
				mv += 1
