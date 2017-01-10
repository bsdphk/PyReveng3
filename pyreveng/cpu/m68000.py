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
ABCD		B,-(Ay),-(Ax)	0000	|1 1 0 0| Ax  |1 0 0 0 0|1| Ay  |
# 108/4-4
ADD		Z,Dn,ea		037d	|1 1 0 1| Dn  |1| sz| eam | ear |
ADD		Z,ea,Dn		1f7f	|1 1 0 1| Dn  |0| sz| eam | ear |
# 111/4-7
ADDA		W,ea,An		1f7f	|1 1 0 1| An  |0 1 1| eam | ear |
ADDA		L,ea,An		1f7f	|1 1 0 1| An  |1 1 1| eam | ear |
# 113/4-9
ADDI		Z,data,ea	037d	|0 0 0 0 0 1 1 0| sz| eam | ear |
# 115/4-11
# FIX ADDQ.B ->An sounds bogus, and unreferenced '*' footnote indicates not available
ADDQ		Z,const,ea	037f	|0 1 0 1|const|0| sz| eam | ear |
# 117/4-13
# Collision with ADDA.L
ADDX		Z,Dy,Dx		0000	|1 1 0 1| Dx  |1| sz|0 0|0| Dy  |
ADDX		Z,-(Ay),-(Ax)	0000	|1 1 0 1| Ax  |1| sz|0 0|1| Ay  |
# 119/4-15
# XXX AND.W An,Dn sounds like it should be possible ?
AND		Z,ea,Dn		1f7d	|1 1 0 0| Dn  |0| sz| eam | ear |
AND		Z,Dn,ea		037c	|1 1 0 0| Dn  |1| sz| eam | ear |
# 122/4-18
ANDI		Z,data,ea	037d	|0 0 0 0 0 0 1 0| sz| eam | ear |
# 124/4-20
ANDI		B,const,CCR	0000	|0 0 0 0|0 0 1 0|0 0 1 1|1 1 0 0|0 0 0 0|0 0 0 0| const		|
# 125/4-21
ASL		Z,Dx,Dy		0000	|1 1 1 0| Dx  |1| sz|1|0 0| Dy  |
ASR		Z,Dx,Dy		0000	|1 1 1 0| Dx  |0| sz|1|0 0| Dy  |
ASL		Z,rot,Dn	0000	|1 1 1 0|  rot|1| sz|0|0 0| Dn  |
ASR		Z,rot,Dn	0000	|1 1 1 0|  rot|0| sz|0|0 0| Dn  |
aSL		W,ea		037c	|1 1 1 0|0 0 0|1|1 1| eam | ear |
aSR		W,ea		037c	|1 1 1 0|0 0 0|0|1 1| eam | ear |
# 129/4-25
B		cc,#dst,>JC	0000	|0 1 1 0| cc    | disp8		|
# 131/4-27
bCHG		B,Dn,ea		037c	|0 0 0 0| Dn  |1 0 1| eam | ear |
BCHG		L,Dx,Dy		0000	|0 0 0 0| Dx  |1 0 1|0 0 0| Dy  |
BCHG		B,bn,ea		037c	|0 0 0 0|1 0 0|0 0 1| eam | ear |0 0 0 0|0 0 0 0| bn		|
BCHG		L,bn,Dn		0000	|0 0 0 0|1 0 0|0 0 1|0 0 0| Dn  |0 0 0 0|0 0 0 0| bn		|
# 134/4-30
BCLR		B,Dn,ea		037c	|0 0 0 0| Dn  |1 1 0| eam | ear |
BCLR		L,Dx,Dy		0000	|0 0 0 0| Dx  |1 1 0|0 0 0| Dy  |
BCLR		B,bn,ea		037c	|0 0 0 0|1 0 0|0 1 0| eam | ear |0 0 0 0|0 0 0 0| bn		|
BCLR		L,bn,Dn		0000	|0 0 0 0|1 0 0|0 1 0|0 0 0| Dn  |0 0 0 0|0 0 0 0| bn		|
# 159/4-55
BRA		#dst,>J		0000	|0 1 1 0|0 0 0 0| disp8		|
# 160/4-56
BSET		B,Dn,ea		037c	|0 0 0 0| Dn  |1 1 1| eam | ear |
BSET		L,Dx,Dy		0000	|0 0 0 0| Dx  |1 1 1|0 0 0| Dy  |
BSET		B,bn,ea		037c	|0 0 0 0|1 0 0|0 1 1| eam | ear |0 0 0 0|0 0 0 0| bn		|
BSET		L,bn,Dn		0000	|0 0 0 0|1 0 0|0 1 1|0 0 0| Dn  |0 0 0 0|0 0 0 0| bn		|
# 163/4-59
BSR		#dst,>C		0000	|0 1 1 0|0 0 0 1| disp8		|
# 165/4-61
BTST		B,Dn,ea		037c	|0 0 0 0| Dn  |1 0 0| eam | ear |
BTST		L,Dx,Dy		0000	|0 0 0 0| Dx  |1 0 0|0 0 0| Dy  |
BTST		B,bn,ea		037c	|0 0 0 0|1 0 0|0 0 0| eam | ear |0 0 0 0|0 0 0 0| bn		|
BTST		L,bn,Dn		0000	|0 0 0 0|1 0 0|0 0 0|0 0 0| Dn  |0 0 0 0|0 0 0 0| bn		|
# 173/4-69
cHK		W,ea,Dn		1f7d	|0 1 0 0| Dn  |1 1|0| eam | ear |
CHK		L,ea,Dn		1f7d	|0 1 0 0| Dn  |1 0|0| eam | ear |
# 177/4-73
CLR		Z,ea		037d	|0 1 0 0|0 0 1 0| sz| eam | ear |
# 179/4-75
CMP		Z,ea,Dn		1f7f	|1 0 1 1| Dn  |0| sz| eam | ear |
# 181/4-77
CMPA		W,ea,An		1f7f	|1 0 1 1| An  |0|1 1| eam | ear |
CMPA		L,ea,An		1f7f	|1 0 1 1| An  |1 1 1| eam | ear |
# 183/4-79
CMPI		Z,data,ea	0f7d	|0 0 0 0|1 1 0 0| sz| eam | ear |
# 185/4-81
CMPM		Z,(Ay)+,(Ax)+	0000	|1 0 1 1| Ax  |1| sz|0 0 1| Ay  |
# 194/4-90
DB		cc,Dn,disp16,>JC	0000	|0 1 0 1| cc    |1 1 0 0 1| Dn  | disp16			|
# 196/4-92
DIVS		W,ea,Dn		1f7d	|1 0 0 0| Dn  |1 1 1| eam | ear |
# 201/4-97
DIVU		W,ea,Dn		1f7d	|1 0 0 0| Dn  |0 1 1| eam | ear |
# 204/4-100
EOR		Z,Dn,ea		037d	|1 0 1 1| Dn  |1| sz| eam | ear |
# 206/4-102
EORI		Z,data,ea	037d	|0 0 0 0|1 0 1 0| sz| eam | ear |
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
JMP		ea,>J		0f64	|0 1 0 0|1 1 1 0|1 1| eam | ear |
# 213/4-109
JSR		ea,>C		0f64	|0 1 0 0|1 1 1 0|1 0| eam | ear |
# 214/4-110
LEA		L,ea,An		0f64	|0 1 0 0| An  |1 1 1| eam | ear |
# 215/4-111
LINK		W,An,word	0000	|0 1 0 0|1 1 1 0|0 1 0 1|0| An  | word				|
# 217/4-113
LSL		Z,Dx,Dy		0000	|1 1 1 0| Dx  |1| sz|1|0 1| Dy  |
LSR		Z,Dx,Dy		0000	|1 1 1 0| Dx  |0| sz|1|0 1| Dy  |
LSL		Z,rot,Dn	0000	|1 1 1 0|  rot|1| sz|0|0 1| Dn  |
LSR		Z,rot,Dn	0000	|1 1 1 0|  rot|0| sz|0|0 1| Dn  |
lSL		W,ea		037c	|1 1 1 0|0 0 1|1|1 1| eam | ear |
LSR		W,ea		037c	|1 1 1 0|0 0 1|0|1 1| eam | ear |
# 220/4-116 NB! Not the usual BWL encoding
MOVE		B,ea,ead	1f7f	|0 0|0 1|earx |eamx | eam | ear |
MOVE		L,ea,ead	1f7f	|0 0|1 0|earx |eamx | eam | ear |
MOVE		W,ea,ead	1f7f	|0 0|1 1|earx |eamx | eam | ear |
# 223/4-119
MOVEA		W,ea,An		1f7f	|0 0|1 1| An  |0 0 1| eam | ear |
MOVEA		L,ea,An		1f7f	|0 0|1 0| An  |0 0 1| eam | ear |
# 225/4-121
MOVE		W,CCR,ea	037d	|0 1 0 0|0 0 1|0 1 1| eam | ear |
# 227/4-123
MOVE		W,ea,CCR	1f7d	|0 1 0 0|0 1 0|0 1 1| eam | ear |
# 229/4-125
MOVE		W,SR,ea		037d	|0 1 0 0|0 0 0|0 1 1| eam | ear |
# 232/4-128
MOVEM		W,rlist,ea	0374	|0 1 0 0|1 0 0|0 1 0| eam | ear | rlist				|
MOVEM		L,rlist,ea	0374	|0 1 0 0|1 0 0|0 1 1| eam | ear | rlist				|
MOVEM		W,ea,rlist	0f6c	|0 1 0 0|1 1 0|0 1 0| eam | ear | rlist				|
MOVEM		L,ea,rlist	0f6c	|0 1 0 0|1 1 0|0 1 1| eam | ear | rlist				|
# 235/4-131
MOVEP		W,Dn,An+disp16	0000	|0 0 0 0| Dn  |1|1 0|0 0 1| An  | disp16			|
MOVEP		L,Dn,An+disp16	0000	|0 0 0 0| Dn  |1|1 1|0 0 1| An  | disp16			|
MOVEP		W,An+disp16,Dn	0000	|0 0 0 0| Dn  |1|0 0|0 0 1| An  | disp16			|
MOVEP		L,An+disp16,Dn	0000	|0 0 0 0| Dn  |1|0 1|0 0 1| An  | disp16			|
# 238/4-134
MOVEQ		L,data8,Dn	0000	|0 1 1 1| Dn  |0| data8		|
# 239/4-135
MULS		W,ea,Dn		1f7d	|1 1 0 0| Dn  |1 1 1| eam | ear |
# 243/4-139
MULU		W,ea,Dn		1f7d	|1 1 0 0| Dn  |0 1 1| eam | ear |
# 245/4-141
NBCD		B,ea		037d	|0 1 0 0|1 0 0|0 0 0| eam | ear |
# 247/4-143
NEG		Z,ea		037d	|0 1 0 0|0 1 0|0| sz| eam | ear |
# 249/4-146
NEGX		Z,ea		037d	|0 1 0 0|0 0 0|0| sz| eam | ear |
# 251/4-147
NOP		-		0000	|0 1 0 0|1 1 1|0 0 1|1 1 0|0 0 1|
# 252/4-148
NOT		Z,ea		037d	|0 1 0 0|0 1 1|0| sz| eam | ear |
# 254/4-150
OR		Z,ea,Dn		1f7d	|1 0 0 0| Dn  |0| sz| eam | ear |
OR		Z,Dn,ea		037c	|1 0 0 0| Dn  |1| sz| eam | ear |
# 257/4-153
ORI		Z,data,ea	037d	|0 0 0 0|0 0 0 0| sz| eam | ear |
# 259/4-155
ORI		word,CCR	0000	|0 0 0 0|0 0 0 0|0 0 1 1|1 1 0 0|0 0 0 0|0 0 0 0| word		|
# 263/4-159
PEA		L,ea		0f64	|0 1 0 0|1 0 0|0 0 1| eam | ear |
# 264/4-160
ROL		Z,Dx,Dy		0000	|1 1 1 0| Dx  |1| sz|1|1 1| Dy  |
ROR		Z,Dx,Dy		0000	|1 1 1 0| Dx  |0| sz|1|1 1| Dy  |
ROL		Z,rot,Dn	0000	|1 1 1 0|  rot|1| sz|0|1 1| Dn  |
ROR		Z,rot,Dn	0000	|1 1 1 0|  rot|0| sz|0|1 1| Dn  |
rOL		W,ea		037c	|1 1 1 0|0 1 1|1|1 1| eam | ear |
rOR		W,ea		037c	|1 1 1 0|0 1 1|0|1 1| eam | ear |
# 267/4-163
rOXL		Z,Dx,Dy		0000	|1 1 1 0| Dx  |1| sz|1|1 0| Dy  |
rOXR		Z,Dx,Dy		0000	|1 1 1 0| Dx  |0| sz|1|1 0| Dy  |
ROXL		Z,rot,Dn	0000	|1 1 1 0|  rot|1| sz|0|1 0| Dn  |
ROXR		Z,rot,Dn	0000	|1 1 1 0|  rot|0| sz|0|1 0| Dn  |
rOXL		W,ea		037c	|1 1 1 0|0 1 0|1|1 1| eam | ear |
rOXR		W,ea		037c	|1 1 1 0|0 1 0|0|1 1| eam | ear |
# 272/4-168
RTR		-		0000	|0 1 0 0|1 1 1 0|0 1 1 1|0 1 1 1|
# 273/4-169
RTS		>R		0000	|0 1 0 0|1 1 1 0|0 1 1 1|0 1 0 1|
# 274/4-170
sBCD		B,Dx,Dy		0000	|1 0 0 0| Dy  |1 0 0 0 0|0| Dx  |
SBCD		B,-(Ax),-(Ay)	0000	|1 0 0 0| Ay  |1 0 0 0 0|1| Ax  |
# 276/4-172
S		cc,B,ea		037d	|0 1 0 1| cc    |1 1| eam | ear |
# 278/4-174
SUB		Z,ea,Dn		1f7f	|1 0 0 1| Dn  |0| sz| eam | ear |
SUB		Z,Dn,ea		037c	|1 0 0 1| Dn  |1| sz| eam | ear |
# 281/4-177
SUBA		W,ea,An		1f7f	|1 0 0 1| An  |0 1 1| eam | ear |
SUBA		L,ea,An		1f7f	|1 0 0 1| An  |1 1 1| eam | ear |
# 283/4-179
SUBI		Z,data,ea	037d	|0 0 0 0|0 1 0 0| sz| eam | ear |
# 285/4-181
SUBQ		Z,const,ea	037f	|0 1 0 1|const|1| sz| eam | ear |
# 287/4-183
SUBX		Z,Dx,Dy		0000	|1 0 0 1| Dy  |1| sz|0 0|0| Dx  |
SUBX		Z,-(Ax),-(Ay)	0000	|1 0 0 1| Ay  |1| sz|0 0|1| Ax  |
# 289/4-185
SWAP		W,Dn		0000	|0 1 0 0|1 0 0 0|0 1 0 0|0| Dn  |
# 290/4-186
tAS		B,ea		037d	|0 1 0 0|1 0 1 0|1 1| eam | ear |
# 292/4-188
TRAP		#vect		0000	|0 1 0 0|1 1 1 0|0 1 0 0| vect	|
# 295/4-191
tRAPV		-		0000	|0 1 0 0|1 1 1 0|0 1 1 1|0 1 1 0|
# 296/4-192
TST		Z,ea		1f7f	|0 1 0 0|1 0 1 0| sz| eam | ear |
# 298/4-194
UNLK		An		0000	|0 1 0 0|1 1 1 0|0 1 0 1|1| An  |
# 456/6-2
ANDI		W,word,SR	0000	|0 0 0 0|0 0 1 0|0 1 1 1|1 1 0 0| word				|
# 464/6-10
eORI		W,word,SR	0000	|0 0 0 0|1 0 1 0|0 1 1 1|1 1 0 0| word				|
# 473/6-19
MOVE		W,ea,SR		1f7d	|0 1 0 0|0 1 1 0|1 1| eam | ear |
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

def arg_an(pj, ins):
	return assy.Arg_verbatim(pj, "A%d" % ins.im.F_An)

def arg_ax_dec(pj, ins):
	return assy.Arg_verbatim(pj, "-(A%d)" % ins.im.F_Ax)

def arg_ax_inc(pj, ins):
	return assy.Arg_verbatim(pj, "(A%d)+" % ins.im.F_Ax)

def arg_ax(pj, ins):
	return assy.Arg_verbatim(pj, "A%d" % ins.im.F_Ax)

def arg_ay_dec(pj, ins):
	return assy.Arg_verbatim(pj, "-(A%d)" % ins.im.F_Ay)

def arg_ay_inc(pj, ins):
	return assy.Arg_verbatim(pj, "(A%d)+" % ins.im.F_Ay)

def arg_ay(pj, ins):
	return assy.Arg_verbatim(pj, "A%d" % ins.im.F_Ay)

def arg_B(pj, ins):
	ins.sz = 1
	ins.mne += ".B"

def arg_bn(pj, ins):
	return assy.Arg_verbatim(pj, "#0x%x" % ins.im.F_bn)

def arg_cc(pj, ins):
	ins.mne += cond_code[ins.im.F_cc]

def arg_const(pj, ins):
	o = ins.im.F_const
	if o == 0:
		o = 8
	return assy.Arg_verbatim(pj, "#0x%x" % o)

class arg_data(assy.Arg_verbatim):
	def __init__(self, pj, ins):
		if ins.sz == 1:
			self.v = pj.m.bu16(ins.hi)
		elif ins.sz == 2:
			self.v = pj.m.bu16(ins.hi)
		elif ins.sz == 4:
			self.v = pj.m.bu32(ins.hi)
		else:
			assert False
		ins.hi += ins.sz
		if ins.sz == 1:
			ins.hi += 1
		super(arg_data, self).__init__(pj,
		    "#0x%0*x" % (ins.sz * 2, self.v)
		)

def arg_data8(pj, ins):
	return assy.Arg_verbatim(pj, "#0x%02x" % ins.im.F_data8)

def arg_disp16(pj, ins):
	o = ins.im.F_disp16
	if o & 0x8000:
		o -= 1 << 16
	ins.dstadr = ins.hi + o - 2
	return assy.Arg_dst(pj, ins.dstadr)

def arg_dn(pj, ins):
	return assy.Arg_verbatim(pj, "D%d" % ins.im.F_Dn)

class arg_dst(assy.Arg_dst):
	def __init__(self, pj, ins):
		x = ins.im.F_disp8
		if x == 0x00:
			ins.dstadr = ins.hi + pj.m.bs16(ins.hi)
			ins.hi += 2
		elif x == 0xff:
			ins.dstadr = ins.hi + pj.m.bs32(ins.hi)
			ins.hi += 4
		elif x & 0x80:
			ins.dstadr = ins.hi + x - 0x100
		else:
			ins.dstadr = ins.hi + x
		super(arg_dst, self).__init__(pj, ins.dstadr)

def arg_dx(pj, ins):
	return assy.Arg_verbatim(pj, "D%d" % ins.im.F_Dx)

def arg_dy(pj, ins):
	return assy.Arg_verbatim(pj, "D%d" % ins.im.F_Dy)

def arg_eaxt(pj, ins, ref):
	ew = pj.m.bu16(ins.hi)
	ins.hi += 2

	if ew & 0x8000:
		reg = "+A"
	else:
		reg = "+D"

	reg = reg + "%d" % ((ew >> 12) & 7)

	if ew & 0x800:
		wl = ".L"
	else:
		wl = ".W"

	sc = 1 << ((ew >> 9) & 3)

	if ew & 0x100:
		print("0x%x FULL EXT WORD" % ins.lo, ins)
		raise assy.Invalid("FULL EXT WORD")
	else:
		d = ew & 0xff
		if d & 0x80:
			d -= 0x100
		s = "("
		if ref == "PC":
			s += "#0x%x" % (d + ins.hi - 2)
		elif d != 0:
			s += "#0x%x+" % d + ref
		else:
			s += ref
		s += reg + wl
		if sc > 1:
			s += "*%d" % sc
		s += ")"
		return s


def arg_eax(pj, ins, eam, ear):
	eax = 1 << eam
	if eax > 0x40:
		eax = 0x100 << ear
	eamask = int(ins.im.assy[-1], 16)
	if not eax & eamask:
		print ("0x%x Wrong EA mode m=%d/r=%d" % (ins.lo, eam, ear))
		raise assy.Invalid("0x%x Wrong EA mode m=%d/r=%d" % (
		    ins.lo, eam, ear))
	if eax == 0x0001:
		return assy.Arg_verbatim(pj, "D%d" % ear)
	if eax == 0x0002:
		return assy.Arg_verbatim(pj, "A%d" % ear)
	if eax == 0x0004:
		return assy.Arg_verbatim(pj, "(A%d)" % ear)
	if eax == 0x0008:
		return assy.Arg_verbatim(pj, "(A%d)+" % ear)
	if eax == 0x0010:
		return assy.Arg_verbatim(pj, "-(A%d)" % ear)
	if eax == 0x0020:
		o = pj.m.bs16(ins.hi)
		ins.hi += 2
		if o < 0:
			return assy.Arg_verbatim(pj, "(A%d-0x%x)" % (ear, -o))
		else:
			return assy.Arg_verbatim(pj, "(A%d+0x%x)" % (ear, o))
	if eax == 0x0040:
		return arg_eaxt(pj, ins, "A%d" % ear)
	if eax == 0x0100:
		o = pj.m.bu16(ins.hi)
		ins.hi += 2
		if o & 0x8000:
			o |= 0xffff0000L
		ins.dstadr = o
		return assy.Arg_dst(pj, o)
	if eax == 0x0200:
		o = pj.m.bu32(ins.hi)
		ins.hi += 4
		ins.dstadr = o
		return assy.Arg_dst(pj, o)
	if eax == 0x0400:
		o = ins.hi + pj.m.bs16(ins.hi)
		ins.hi += 2
		ins.dstadr = o
		return assy.Arg_dst(pj, o)
	if eax == 0x0800:
		return arg_eaxt(pj, ins, "PC")
	if eax == 0x1000 and ins.sz == 1:
		ins.hi += 2
		return assy.Arg_verbatim(pj, "#0x%02x" % pj.m.rd(ins.hi-1))
	if eax == 0x1000 and ins.sz == 2:
		ins.hi += 2
		return assy.Arg_verbatim(pj, "#0x%04x" % pj.m.bu16(ins.hi-2))
	if eax == 0x1000 and ins.sz == 4:
		ins.hi += 4
		return assy.Arg_verbatim(pj, "#0x%08x" % pj.m.bu32(ins.hi-4))
	print("0x%x EA? 0x%04x m=%d/r=%d" % (ins.lo, eax, eam, ear))
	raise assy.Invalid("0x%x EA? 0x%04x m=%d/r=%d" % (ins.lo, eax, eam, ear))

def arg_ea(pj, ins):
	return arg_eax(pj, ins, ins.im.F_eam, ins.im.F_ear)

def arg_ead(pj, ins):
	return arg_eax(pj, ins, ins.im.F_eamx, ins.im.F_earx)

def arg_L(pj, ins):
	ins.sz = 4
	ins.mne += ".L"

def arg_rlist(pj, ins):
	v = ins.im.F_rlist
	l = []
	if ins.im.F_eam == 4:
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

def arg_rot(pj, ins):
	a = ins.im.F_rot
	if a == 0:
		a = 8
	return assy.Arg_verbatim(pj, "#0x%x" % a)

def arg_vect(pj, ins):
	return assy.Arg_verbatim(pj, "#%d" % ins.im.F_vect)

def arg_W(pj, ins):
	ins.sz = 2
	ins.mne += ".W"

def arg_word(pj, ins):
	return assy.Arg_verbatim(pj, "#0x%04x" % ins.im.F_word)

def arg_Z(pj, ins):
	if ins.im.F_sz == 3:
		raise assy.Invalid('0x%x F_sz == 3' % ins.lo)
	i, j = [
		[1, ".B"],
		[2, ".W"],
		[4, ".L"],
	] [ins.im.F_sz]
	ins.sz = i
	ins.mne += j



class m68000(assy.Instree_disass):
	def __init__(self, lang="m68000"):
		super(m68000, self).__init__(
		    lang,
		    ins_word=16,
		    mem_word=8,
		    endian=">")
		self.it.load_string(m68000_instructions)

		self.args.update( {
			'An':		arg_an,
			'-(Ax)':	arg_ax_dec,
			'(Ax)+':	arg_ax_inc,
			'Ax':		arg_ax,
			'-(Ay)':	arg_ay_dec,
			'(Ay)+':	arg_ay_inc,
			'Ay':		arg_ay,
			'B':		arg_B,
			'bn':		arg_bn,
			'cc':		arg_cc,
			'CCR':		'CCR',
			'const':	arg_const,
			'data':		arg_data,
			'data8':	arg_data8,
			'disp16':	arg_disp16,
			'Dn':		arg_dn,
			'#dst':		arg_dst,
			'Dx':		arg_dx,
			'Dy':		arg_dy,
			'ea':		arg_ea,
			'ead':		arg_ead,
			'L':		arg_L,
			'rlist':	arg_rlist,
			'rot':		arg_rot,
			'SR':		'SR',
			'USP':		'USP',
			'#vect':	arg_vect,
			'W':		arg_W,
			'word':		arg_word,
			'Z':		arg_Z,
		})

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
