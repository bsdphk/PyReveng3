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

'''Motorola M68000
'''

from pyreveng import assy, data, mem

m68000_desc = """
#		src,dst		ea	|_ _ _ _|_ _ _v_|_ _v_ _|_v_ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|
# 107/4-3
aBCD		B,Dy,Dx		0000	|1 1 0 0| Dx  |1 0 0 0 0|0| Dy  |
ABCD		B,decAy,decAx	0000	|1 1 0 0| Ax  |1 0 0 0 0|1| Ay  |
# 108/4-4
ADD		Z,Dn,ea		037d	|1 1 0 1| Dn  |1| sz| ea	| {
	%0 = add SZ EA , DN
	%SR.n = icmp slt SZ %0 , 0
	%SR.z = icmp eq SZ %0 , 0
	%SR.c = pyreveng.carry.add ( EA , DN )
	%SR.v = pyreveng.overflow.add ( EA , DN )
	%SR.x = i1 %SR.c
	LEAS %0
}
ADD		Z,ea,Dn		1f7f	|1 1 0 1| Dn  |0| sz| ea	| {
	%0 = add SZ DN , EA
	%SR.n = icmp slt SZ %0 , 0
	%SR.z = icmp eq SZ %0 , 0
	%SR.c = pyreveng.carry.add ( DN , EA )
	%SR.v = pyreveng.overflow.add ( DN , EA )
	%SR.x = i1 %SR.c
	DN = %0
}
# 111/4-7
ADDA		W,ea,An		1f7f	|1 1 0 1| An  |0 1 1| ea	| {
	%0 = sext SZ EA to i32
	AN = add i32 AN , %0
}
ADDA		L,ea,An		1f7f	|1 1 0 1| An  |1 1 1| ea	| {
	AN = add SZ AN , EA
}
# 113/4-9
ADDI		Z,data,ea	037d	|0 0 0 0 0 1 1 0| sz| ea	| {
	%0 = add SZ EA , DATA
	%SR.n = icmp slt SZ %0 , 0
	%SR.z = icmp eq SZ %0 , 0
	%SR.c = pyreveng.carry.add ( EA , DATA )
	%SR.v = pyreveng.overflow.add ( EA , DATA )
	LEAS %0
}
# 115/4-11
ADDQ		L,const,An	0	|0 1 0 1|const|0|1 0|0 0 1| An	| {
	AN = add SZ AN , CONST
}
ADDQ		L,const,An	0	|0 1 0 1|const|0|0 1|0 0 1| An	| {
	AN = add SZ AN , CONST
}
ADDQ		Z,const,ea	037f	|0 1 0 1|const|0| sz| ea	| {
	%0 = add SZ EA , CONST
	%SR.n = icmp slt SZ %0 , 0
	%SR.z = icmp eq SZ %0 , 0
	%SR.c = pyreveng.carry.add ( EA , CONST )
	%SR.v = pyreveng.overflow.add ( EA , CONST )
	LEAS %0
}
# 117/4-13
ADDX		Z,Dy,Dx		0000	|1 1 0 1| Dx  |1| sz|0 0|0| Dy  | {
	%0 = add SZ DX , DY
	%1 = zext i1 %SR.x to SZ
	%2 = add SZ %0 , %1
	%SR.n = icmp slt SZ %2 , 0
	%3 = icmp eq SZ %2 , 0
	%SR.z = and i1 %3 , %SR.z
	%SR.c = pyreveng.carry.add ( DX , DY , %1 )
	%SR.v = pyreveng.overflow.add ( DX , DY , %1 )
	%SR.x = pyreveng.carry.add ( DX , DY , %1 )
	DX = SZ %2
}
ADDX		Z,decAy,decAx	0000	|1 1 0 1| Ax  |1| sz|0 0|1| Ay  |
# 119/4-15
# XXX AND.W An,Dn sounds like it should be possible ?
AND		Z,ea,Dn		1f7d	|1 1 0 0| Dn  |0| sz| ea	| {
	DN = and SZ DN , EA
	STDF4 DN
}
AND		Z,Dn,ea		037c	|1 1 0 0| Dn  |1| sz| ea	| {
	%0 = and SZ EA , DN
	STDF4 %0
	LEAS %0
}
# 122/4-18
ANDI		Z,data,ea	037d	|0 0 0 0 0 0 1 0| sz| ea	| {
	%0 = and SZ EA , DATA
	STDF4 %0
	LEAS %0
}
# 124/4-20
ANDI		B,const,CCR	0000	|0 0 0 0|0 0 1 0|0 0 1 1|1 1 0 0|0 0 0 0|0 0 0 0| const		|
# 125/4-21
ASL		Z,Dx,Dy		0000	|1 1 1 0| Dx  |1| sz|1|0 0| Dy  |
ASR		Z,Dx,Dy		0000	|1 1 1 0| Dx  |0| sz|1|0 0| Dy  | {
	DY = ashr SZ DY , DX
	%SR.n = icmp slt SZ DY , 0
	%SR.z = icmp eq SZ DY , 0
	%SR.v = i1 0
	%SR.x = XXX
	%SR.c = XXX
}
ASL		Z,rot,Dn	0000	|1 1 1 0|  rot|1| sz|0|0 0| Dn  |
ASR		Z,rot,Dn	0000	|1 1 1 0|  rot|0| sz|0|0 0| Dn  | {
	DN = ashr SZ DN , ROT
	%SR.n = icmp slt SZ DN , 0
	%SR.z = icmp eq SZ DN , 0
	%SR.v = i1 0
	%SR.x = XXX
	%SR.c = XXX
}
aSL		W,ea		037c	|1 1 1 0|0 0 0|1|1 1| ea	|
ASR		W,ea		037c	|1 1 1 0|0 0 0|0|1 1| ea	| {
	%0 = ashr SZ EA , 1
	%SR.n = icmp slt SZ %0 , 0
	%SR.z = icmp eq SZ %0 , 0
	%SR.v = i1 0
	%SR.x = XXX
	%SR.c = XXX
	LEA %0
}
# 129/4-25
B		cc,dst,>JC	0000	|0 1 1 0| cc    | disp8		| {
	br i1 CC label DST , label HI
}
# 131/4-27
bCHG		B,Dn,ea		037c	|0 0 0 0| Dn  |1 0 1| ea	| {
	%0 = and SZ DN , 7
	%1 = shl SZ 1 , %0
	%2 = and SZ EA , %1
	%SR.z = icmp ne SZ %2 , 0
	%3 = xor SZ EA , %1
	LEAS %3
}
BCHG		L,Dx,Dy		0000	|0 0 0 0| Dx  |1 0 1|0 0 0| Dy  | {
	%0 = and SZ DX , 31
	%1 = shl SZ 1 , %0
	%2 = and SZ DY , %1
	%SR.z = icmp ne SZ %2 , 0
	DY = xor SZ DY , %1
}
BCHG		B,bn,ea		037c	|0 0 0 0|1 0 0|0 0 1| ea	|0 0 0 0|0 0 0 0| bn		| {
	%0 = and SZ EA , BN
	%SR.z = icmp eq SZ %0 , 0
	%1 = xor SZ EA , BN
	LEAS %1
}
BCHG		L,bn,Dn		0000	|0 0 0 0|1 0 0|0 0 1|0 0 0| Dn  |0 0 0 0|0 0 0 0| bn		| {
	%0 = and SZ DN , BN
	%SR.z = icmp eq SZ %0 , 0
	DN = xor SZ DN , BN
}
# 134/4-30
BCLR		B,Dn,ea		037c	|0 0 0 0| Dn  |1 1 0| ea	| {
	%0 = and SZ DN , 7
	%1 = shl SZ 1 , %0
	%2 = and SZ EA , %1
	%SR.z = icmp ne SZ %2 , 0
	%3 = xor SZ %1 , -1
	%4 = and SZ EA , %3
	LEAS %4
}
BCLR		L,Dx,Dy		0000	|0 0 0 0| Dx  |1 1 0|0 0 0| Dy  | {
	%0 = and SZ DX , 31
	%1 = shl SZ 1 , %0
	%2 = and SZ DY , %1
	%SR.z = icmp ne SZ %2 , 0
	%3 = xor SZ %1 , -1
	DY = and SZ DY , %3
}
BCLR		B,bn,ea		037c	|0 0 0 0|1 0 0|0 1 0| ea	|0 0 0 0|0 0 0 0| bn		| {
	%0 = and SZ EA , BN
	%SR.z = icmp eq SZ %0 , 0
	%1 = and SZ EA , IBN
	LEAS %1
}
BCLR		L,bn,Dn		0000	|0 0 0 0|1 0 0|0 1 0|0 0 0| Dn  |0 0 0 0|0 0 0 0| bn		| {
	%0 = and SZ DN , BN
	%SR.z = icmp eq SZ %0 , 0
	DN = and SZ DN , IBN
}
# 159/4-55
BRA		dst,>J		0000	|0 1 1 0|0 0 0 0| disp8		| {
	br label DST
}
# 160/4-56
BSET		B,Dn,ea		037c	|0 0 0 0| Dn  |1 1 1| ea	| {
	%0 = and SZ DN , 7
	%1 = shl i8 1 , %0
	%2 = and i8 EA , %1
	%SR.z = icmp ne i8 %2 , 0
	%3 = or i8 EA , %1
	LEAS %3
}
BSET		L,Dx,Dy		0000	|0 0 0 0| Dx  |1 1 1|0 0 0| Dy  | {
	%0 = and SZ DX , 31
	%1 = shl i32 1 , %0
	%2 = and i32 DY , %1
	%SR.z = icmp ne i32 %2 , 0
	DY = or i32 DY , %1
}
BSET		B,bn,ea		037c	|0 0 0 0|1 0 0|0 1 1| ea	|0 0 0 0|0 0 0 0| bn		| {
	%0 = and SZ EA , BN
	%SR.z = icmp eq SZ %0 , 0
	%1 = or SZ EA , BN
	LEAS %1
}
BSET		L,bn,Dn		0000	|0 0 0 0|1 0 0|0 1 1|0 0 0| Dn  |0 0 0 0|0 0 0 0| bn		| {
	%0 = and SZ DN , BN
	%SR.z = icmp eq SZ %0 , 0
	DN = or SZ DN , BN
}
# 163/4-59
BSR		dst,>C		0000	|0 1 1 0|0 0 0 1| disp8		| {
	%A7 = sub i32 %A7 , 4
	store i32 HI , i32* %A7
	br label DST
}
# 165/4-61
BTST		B,Dn,ea		037c	|0 0 0 0| Dn  |1 0 0| ea	| {
	%0 = and SZ DN , 7
	%1 = shr i32 EA , %0
	%SR.z = trunc i32 %1 to i1
}
BTST		L,Dx,Dy		0000	|0 0 0 0| Dx  |1 0 0|0 0 0| Dy  | {
	%0 = and SZ DX , 31
	%1 = shr i32 DY , %0
	%SR.z = trunc i32 %1 to i1
}
BTST		B,bn,ea		037c	|0 0 0 0|1 0 0|0 0 0| ea	|0 0 0 0|0 0 0 0| bn		| {
	%0 = and SZ EA , BN
	%SR.z = icmp eq SZ %0 , 0
}
BTST		L,bn,Dn		0000	|0 0 0 0|1 0 0|0 0 0|0 0 0| Dn  |0 0 0 0|0 0 0 0| bn		| {
	%0 = and SZ DN , BN
	%SR.z = icmp eq SZ %0 , 0
}
# 173/4-69
cHK		W,ea,Dn		1f7d	|0 1 0 0| Dn  |1 1|0| ea	|
CHK		L,ea,Dn		1f7d	|0 1 0 0| Dn  |1 0|0| ea	|
# 177/4-73
CLR		Z,ea		037d	|0 1 0 0|0 0 1 0| sz| ea	| {
	LEAS 0
	%SR.z = i1 1
	%SR.v = i1 0
	%SR.c = i1 0
}
# 179/4-75
CMP		Z,ea,Dn		1f7f	|1 0 1 1| Dn  |0| sz| ea	| {
	%0 = sub SZ DN , EA
	%SR.n = icmp slt SZ %0 , 0
	%SR.z = icmp eq SZ %0 , 0
	%SR.c = pyreveng.carry.sub ( DN , EA )
	%SR.v = pyreveng.overflow.sub ( DN , EA )
}
# 181/4-77
CMPA		W,ea,An		1f7f	|1 0 1 1| An  |0|1 1| ea	| {
	%0 = sub SZ AN , EA
	%SR.n = icmp slt SZ %0 , 0
	%SR.z = icmp eq SZ %0 , 0
	%SR.c = pyreveng.carry.sub ( AN , EA )
	%SR.v = pyreveng.overflow.sub ( AN , EA )
}
CMPA		L,ea,An		1f7f	|1 0 1 1| An  |1 1 1| ea	| {
	%0 = sub SZ AN , EA
	%SR.n = icmp slt SZ %0 , 0
	%SR.z = icmp eq SZ %0 , 0
	%SR.c = pyreveng.carry.sub ( AN , EA )
	%SR.v = pyreveng.overflow.sub ( AN , EA )
}
# 183/4-79
CMPI		Z,data,ea	0f7d	|0 0 0 0|1 1 0 0| sz| ea	| {
	%0 = sub SZ EA , DATA
	%SR.n = icmp slt SZ %0 , 0
	%SR.z = icmp eq SZ %0 , 0
	%SR.c = pyreveng.carry.sub ( EA , DATA )
	%SR.v = pyreveng.overflow.sub ( EA , DATA )
}
# 185/4-81
CMPM		Z,Ayinc,Axinc	0000	|1 0 1 1| Ax  |1| sz|0 0 1| Ay  |
# 194/4-90
DBF		Dn,disp16,>JC	0000	|0 1 0 1|0 0 0 1|1 1 0 0 1| Dn  | disp16			| {
	DN = sub i32 DN , 1
	%0 = icmp ne i32 DN , -1
	br i1 %0 label DST , label HI
}
DB		cc,Dn,disp16,>JC	0000	|0 1 0 1| cc    |1 1 0 0 1| Dn  | disp16			| {
	br i1 CC label HI , label %0
%0:
	DN = sub i16 DN , 1
	%2 = icmp eq i16 DN , 0xffff
	br i1 %2 label DST , label HI
}
# 196/4-92
DIVS		W,ea,Dn		1f7d	|1 0 0 0| Dn  |1 1 1| ea	|
# 201/4-97
DIVU		W,ea,Dn		1f7d	|1 0 0 0| Dn  |0 1 1| ea	|
# 204/4-100
EOR		Z,Dn,ea		037d	|1 0 1 1| Dn  |1| sz| ea	| {
	%0 = xor SZ EA , DN
	STDF4 %0
	LEAS %0
}
# 206/4-102
EORI		Z,data,ea	037d	|0 0 0 0|1 0 1 0| sz| ea	| {
	%0 = xor SZ EA , DATA
	STDF4 %0
	LEAS %0
}
# 208/4-104
eORI		B,const,CCR	0000	|0 0 0 0|1 0 1 0|0 0|1 1 1|1 0 0|0 0 0 0|0 0 0 0| const		|
# 209/4-105
EXG		L,Dx,Dy		0000	|1 1 0 0| Dx  |1|0 1 0 0 0| Dy  | {
	%0 = i32 DY
	DY = i32 DX
	DX = i32 %0
}
EXG		L,Ax,Ay		0000	|1 1 0 0| Ax  |1|0 1 0 0 1| Ay  | {
	%0 = i32 AY
	AY = i32 AX
	AX = i32 %0
}
EXG		L,Dx,Ay		0000	|1 1 0 0| Dx  |1|1 0 0 0 1| Ay  | {
	%0 = i32 AY
	AY = i32 DX
	DX = i32 %0
}
# 210/4-106
EXTB		W,Dn		0000	|0 1 0 0|1 0 0|0 1 0|0 0 0| Dn  | {
	DN = exts i8 DN to i16
	STDF4 DN
}
EXTW		L,Dn		0000	|0 1 0 0|1 0 0|0 1 1|0 0 0| Dn  | {
	DN = exts i16 DN to i32
	STDF4 DN
}
# 211/4-107
iLLEGAL		-		0000	|0 1 0 0|1 0 1 0|1 1 1 1|1 1 0 0|
# 212/4-108
JMP		ea,>J		0f64	|0 1 0 0|1 1 1 0|1 1| ea	| {
	br label PTR_EA
}
# 213/4-109
JSR		ea,>C		0f64	|0 1 0 0|1 1 1 0|1 0| ea	| {
	%A7 = sub i32 %A7 , 4
	store i32 HI , i32* %A7
	br label PTR_EA
}
# 214/4-110
LEA		L,ea,An		0f64	|0 1 0 0| An  |1 1 1| ea	| {
	AN = SZ PTR_EA
}
# 215/4-111
LINK		W,An,word	0000	|0 1 0 0|1 1 1 0|0 1 0 1|0| An  | word				| {
	%A7 = sub i32 %A7 , 4
	store i32 AN , i32* %A7
	AN = i32 %A7
	%A7 = add i32 %A7 , WORDSGN
}
# XXX: LINK L ?
# 217/4-113
LSL		Z,Dx,Dy		0000	|1 1 1 0| Dx  |1| sz|1|0 1| Dy  | {
	DY = shl SZ DY , DX
	%SR.n = icmp slt SZ DY , 0
	%SR.z = icmp eq SZ DY , 0
	%SR.v = i1 0
	%SR.x = XXX
	%SR.c = XXX
}
LSR		Z,Dx,Dy		0000	|1 1 1 0| Dx  |0| sz|1|0 1| Dy  | {
	DY = lshr SZ DY , DX
	%SR.n = icmp slt SZ DY , 0
	%SR.z = icmp eq SZ DY , 0
	%SR.v = i1 0
	%SR.x = XXX
	%SR.c = XXX
}
LSL		Z,rot,Dn	0000	|1 1 1 0|  rot|1| sz|0|0 1| Dn  | {
	DN = shl SZ DN , ROT
	%SR.n = icmp slt SZ DN , 0
	%SR.z = icmp eq SZ DN , 0
	%SR.v = i1 0
	%SR.x = XXX
	%SR.c = XXX
}
LSR		Z,rot,Dn	0000	|1 1 1 0|  rot|0| sz|0|0 1| Dn  | {
	DN = lshr SZ DN , ROT
	%SR.n = icmp slt SZ DN , 0
	%SR.z = icmp eq SZ DN , 0
	%SR.v = i1 0
	%SR.x = XXX
	%SR.c = XXX
}
LSL		W,ead		037c	|1 1 1 0|0 0 1|1|1 1| ead	| {
	%0 = shl SZ EAD , 1
	%SR.n = icmp slt SZ %0 , 0
	%SR.z = icmp eq SZ %0 , 0
	%SR.v = i1 0
	%SR.x = XXX
	%SR.c = XXX
	LEAD %0
}
LSR		W,ead		037c	|1 1 1 0|0 0 1|0|1 1| ead	| {
	%0 = lshr SZ EAD , 1
	%SR.n = icmp slt SZ %0 , 0
	%SR.z = icmp eq SZ %0 , 0
	%SR.v = i1 0
	%SR.x = XXX
	%SR.c = XXX
	LEAD %0
}
# 220/4-116 NB! Not the usual BWL encoding
MOVE		B,ea,ead	1f7f	|0 0|0 1| ead       | ea	| {
	STDF4 EA
	LEAD EA
}
MOVE		L,ea,ead	1f7f	|0 0|1 0| ead       | ea	| {
	STDF4 EA
	LEAD EA
}
MOVE		W,ea,ead	1f7f	|0 0|1 1| ead       | ea	| {
	STDF4 EA
	LEAD EA
}
# 223/4-119
MOVEA		W,ea,An		1f7f	|0 0|1 1| An  |0 0 1| ea	| {
	AN = SZ EA
}
MOVEA		L,ea,An		1f7f	|0 0|1 0| An  |0 0 1| ea	| {
	AN = SZ EA
}
# 225/4-121
MOVE		W,CCR,ea	037d	|0 1 0 0|0 0 1|0 1 1| ea	| {
	%0 = and SZ %SR , 0x1f
	LEAS %0
}
# 227/4-123
MOVE		W,ea,CCR	1f7d	|0 1 0 0|0 1 0|0 1 1| ea	| {
	%0 = and SZ EA , 0x1f
	%1 = and SZ %SR , 0xff00
	%SR = or SZ %1 , %0
}
# 229/4-125
MOVE		W,SR,ea		037d	|0 1 0 0|0 0 0|0 1 1| ea	| {
	LEAS %SR
}
# 232/4-128
MOVEM		W,rlist,ea	0374	|0 1 0 0|1 0 0|0 1 0| ea	| rlist				| {
	MOVEM_RM
}
MOVEM		L,rlist,ea	0374	|0 1 0 0|1 0 0|0 1 1| ea	| rlist				| {
	MOVEM_RM
}
MOVEM		W,ea,rlist	0f6c	|0 1 0 0|1 1 0|0 1 0| ea	| rlist				| {
	MOVEM_MR
}
MOVEM		L,ea,rlist	0f6c	|0 1 0 0|1 1 0|0 1 1| ea	| rlist				| {
	MOVEM_MR
}
# 235/4-131
MOVEP		W,Dn,Andisp16	0000	|0 0 0 0| Dn  |1|1 0|0 0 1| An  | disp16			| {
	MOVEP1
}
MOVEP		L,Dn,Andisp16	0000	|0 0 0 0| Dn  |1|1 1|0 0 1| An  | disp16			| {
	MOVEP1
}
MOVEP		W,Andisp16,Dn	0000	|0 0 0 0| Dn  |1|0 0|0 0 1| An  | disp16			| {
	MOVEP2
}
MOVEP		L,Andisp16,Dn	0000	|0 0 0 0| Dn  |1|0 1|0 0 1| An  | disp16			| {
	MOVEP2
}
# 238/4-134
MOVEQ		L,data8,Dn	0000	|0 1 1 1| Dn  |0| data8		| {
	DN = i32 DATA8
	STDF4 DN
}
# 239/4-135
MULS		W,ea,Dn		1f7d	|1 1 0 0| Dn  |1 1 1| ea	| {
	%0 = sext i16 DN to i32
	%1 = sext i16 EA to i32
	DN = mul i32 %0 , %1
	STDF4 DN
}
# 243/4-139
MULU		W,ea,Dn		1f7d	|1 1 0 0| Dn  |0 1 1| ea	| {
	%0 = and i32 DN , 0xffff
	%1 = and i32 EA , 0xffff
	DN = mul i32 %0 , %1
	STDF4 DN
}
# 245/4-141
NBCD		B,ea		037d	|0 1 0 0|1 0 0|0 0 0| ea	|
# 247/4-143
NEG		Z,ea		037d	|0 1 0 0|0 1 0|0| sz| ea	| {
	%0 = sub SZ 0 , EA
	%SR.n = icmp slt SZ %0 , 0
	%SR.z = icmp eq SZ %0 , 0
	%SR.c = pyreveng.carry.sub ( 0 , EA )
	%SR.v = pyreveng.overflow.sub ( 0 , EA )
	%SR.x = %SR.c
	LEAS %0
}
# 249/4-146
NEGX		Z,ea		037d	|0 1 0 0|0 0 0|0| sz| ea	|
# 251/4-147
NOP		-		0000	|0 1 0 0|1 1 1|0 0 1|1 1 0|0 0 1| {
	%0 = i32 0
}
# 252/4-148
NOT		Z,ea		037d	|0 1 0 0|0 1 1|0| sz| ea	| {
	%0 = xor SZ EA , -1
	STDF4 %0
	LEAS %0
}
# 254/4-150
OR		Z,ea,Dn		1f7d	|1 0 0 0| Dn  |0| sz| ea	| {
	DN = or SZ DN , EA
	STDF4 DN
}
OR		Z,Dn,ea		037c	|1 0 0 0| Dn  |1| sz| ea	| {
	%0 = or SZ EA , DN
	STDF4 %0
	LEAS %0
}
# 257/4-153
ORI		Z,data,ea	037d	|0 0 0 0|0 0 0 0| sz| ea	| {
	%0 = or SZ EA , DATA
	STDF4 %0
	LEAS %0
}
# 259/4-155
ORI		W,word,CCR	0000	|0 0 0 0|0 0 0 0|0 0 1 1|1 1 0 0|0 0 0 0|0 0 0 0| word		| {
	%0 = and SZ WORD , 0x1f
	%SR = or SZ %SR , %0
}
# 263/4-159
PEA		L,ea		0f64	|0 1 0 0|1 0 0|0 0 1| ea	| {
	%A7 = sub i32 %A7 , 4
	store i32 PTR_EA , i32* %A7
}
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
RTS		>R		0000	|0 1 0 0|1 1 1 0|0 1 1 1|0 1 0 1| {
	%0 = load i32 , i32* %A7
	%A7 = add i32 %A7 , 4
	br label %0
}
# 274/4-170
sBCD		B,Dx,Dy		0000	|1 0 0 0| Dy  |1 0 0 0 0|0| Dx  |
SBCD		B,decAx,decAy	0000	|1 0 0 0| Ay  |1 0 0 0 0|1| Ax  |
# 276/4-172
S		cc,B,ea		037d	|0 1 0 1| cc    |1 1| ea	| {
	%0 = sext i1 CC to i8
	LEAS %0
}
# 278/4-174
SUB		Z,ea,Dn		1f7f	|1 0 0 1| Dn  |0| sz| ea	| {
	%0 = sub SZ DN , EA
	%SR.n = icmp slt SZ %0 , 0
	%SR.z = icmp eq SZ %0 , 0
	%SR.c = pyreveng.carry.sub ( DN , EA )
	%SR.v = pyreveng.overflow.sub ( DN , EA )
	DN = %0
}
SUB		Z,Dn,ea		037c	|1 0 0 1| Dn  |1| sz| ea	| {
	%0 = sub SZ EA , DN
	%SR.n = icmp slt SZ %0 , 0
	%SR.z = icmp eq SZ %0 , 0
	%SR.c = pyreveng.carry.sub ( EA , DN )
	%SR.v = pyreveng.overflow.sub ( EA , DN )
	LEAS %0
}
# 281/4-177
SUBA		W,ea,An		1f7f	|1 0 0 1| An  |0 1 1| ea	| {
	%0 = sext SZ EA to i32
	AN = sub i32 AN , %0
}
SUBA		L,ea,An		1f7f	|1 0 0 1| An  |1 1 1| ea	| {
	AN = sub i32 AN , EA
}
# 283/4-179
SUBI		Z,data,ea	037d	|0 0 0 0|0 1 0 0| sz| ea	| {
	%0 = sub SZ EA , DATA
	%SR.n = icmp slt SZ %0 , 0
	%SR.z = icmp eq SZ %0 , 0
	%SR.c = pyreveng.carry.sub ( EA , DATA )
	%SR.v = pyreveng.overflow.sub ( EA , DATA )
	LEAS %0
}
# 285/4-181
SUBQ		L,const,An	037f	|0 1 0 1|const|1|0 1|0 0 1| An	| {
	AN = sub SZ AN , CONST
}
SUBQ		L,const,An	037f	|0 1 0 1|const|1|1 0|0 0 1| An	| {
	AN = sub SZ AN , CONST
}
SUBQ		Z,const,ea	037f	|0 1 0 1|const|1| sz| ea	| {
	%0 = sub SZ EA , CONST
	%SR.n = icmp slt SZ %0 , 0
	%SR.z = icmp eq SZ %0 , 0
	%SR.c = pyreveng.carry.sub ( EA , CONST )
	%SR.v = pyreveng.overflow.sub ( EA , CONST )
	LEAS %0
}
# 287/4-183
SUBX		Z,Dx,Dy		0000	|1 0 0 1| Dy  |1| sz|0 0|0| Dx  |
SUBX		Z,decAx,decAy	0000	|1 0 0 1| Ay  |1| sz|0 0|1| Ax  |
# 289/4-185
SWAP		W,Dn		0000	|0 1 0 0|1 0 0 0|0 1 0 0|0| Dn  | {
	%0 = lshr i32 DN , 16
	%1 = shl i32 DN , 16
	DN = or i32 %0 , %1
	STDF4 DN
}
# 290/4-186
tAS		B,ea		037d	|0 1 0 0|1 0 1 0|1 1| ea	|
# 292/4-188
TRAP		vect,>J		0000	|0 1 0 0|1 1 1 0|0 1 0 0| vect	|
# 293/4-189
TRAP		cc,W,word,>JC	0000	|0 1 0 1|cc	|1 1 1 1 1|0 1 0| word				|
TRAP		cc,L,long,>JC	0000	|0 1 0 1|cc	|1 1 1 1 1|0 1 1| word1				| word2				|
TRAP		cc,>J		0000	|0 1 0 1|cc	|1 1 1 1 1|1 0 0|
# 295/4-191
tRAPV		-		0000	|0 1 0 0|1 1 1 0|0 1 1 1|0 1 1 0|
# 296/4-192
TST		Z,ea		1f7f	|0 1 0 0|1 0 1 0| sz| ea	| {
	STDF4 EA
}
# 298/4-194
UNLK		An		0000	|0 1 0 0|1 1 1 0|0 1 0 1|1| An  | {
	%A7 = i32 AN
	AN = load i32 , i32* %A7
	%A7 = add i32 %A7 , 4
}
# 456/6-2
ANDI		W,word,SR	0000	|0 0 0 0|0 0 1 0|0 1 1 1|1 1 0 0| word				| {
	%SR = and SZ %SR , WORD
}
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
RTE		>R		0000	|0 1 0 0|1 1 1 0|0 1 1 1|0 0 1 1| {
	%SR = load i16 , i16* %A7
	%A7 = add i32 %A7 , 2
	%0 = load i32 , i32* %A7
	%A7 = add i32 %A7 , 4
	br label %0
}
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
		if self.lo & 1:
			raise assy.Invalid("Odd Address")
		self.ea = {}
		self.isz = "i32"
		self.icache = {}
		self.ea_fullext = lang.ea_fullext
		self.ea_scale = lang.ea_scale

	def subr_rlist(self):
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
		return l

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
		self.imsk = 0xff
		self.mne += ".B"

	def assy_bn(self, pj):
		return "#0x%x" % (self['bn'] % (self.sz*8))

	def assy_cc(self, pj):
		c = cond_code[self['cc']]
		if c != 'T':
			self.mne += c
		# XXX: remove flow

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
		i = self['data8']
		if i & 0x80:
			i -= 256
		if i < 0:
			return "#-0x%02x" % (-i)
		else:
			return "#0x%02x" % (i)

	def assy_disp16(self, pj):
		o = self['disp16']
		if o & 0x8000:
			o -= 1 << 16
		self.dstadr = self.hi + o - 2
		return assy.Arg_dst(pj, self.dstadr)

	def assy_Andisp16(self, pj):
		o = self['disp16']
		if o & 0x8000:
			o -= 1 << 16
			return "A%d" % self['An'] + "-0x%x" % -o
		else:
			return "A%d" % self['An'] + "+0x%x" % o

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
		elif x & 0x01:
			raise assy.Invalid("Odd numbered destination address")
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
		self.hi += 2

		if ew & 0x100 and not self.ea_fullext:
			raise assy.Invalid("Full extension word")

		if ew & 0x600 and not self.ea_scale:
			raise assy.Invalid("Non-zero scale in extension word")

		basedisp = 0
		outherdisp = 0
		nobase = 0
		noidx = 0
		if ew & 0x100:
			# Full extension word
			bd = (ew >> 4) & 3
			if bd == 2:
				basedisp = pj.m.bu16(self.hi)
				self.hi += 2
			elif bd == 3:
				basedisp = pj.m.bu32(self.hi)
				self.hi += 4

			IS = (ew >> 6) & 1
			IIS = (ew & 7)
			if (IIS & 2) and (not IS or IIS < 4):
				if ew & 1:
					outherdisp = pj.m.bu32(self.hi)
					self.hi += 4
				else:
					outherdisp = pj.m.bu16(self.hi)
					self.hi += 2
		else:
			basedisp = ew & 0xff
			if basedisp & 0x80:
				basedisp -= 0x100

		scale = (ew >> 9) & 3

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

		if scale != 0:
			ll.append(
				["%3", "=", "shl", iltyp, "%0", ",", "%d" % scale]
			)
			ll[0] = "%3"

		if basedisp > 0:
			ll.append(
				["%4", "=", "add", iltyp, ll[0], ",",
				    "0x%x" % basedisp]
			)
			ll[0] = "%4"
		if basedisp < 0:
			ll.append(
				["%4", "=", "sub", iltyp, ll[0], ",",
				    "0x%x" % -basedisp]
			)
			ll[0] = "%4"

		ll.append(
		    ["%5", "=", "add", iltyp, ll[0], ",", "%" + ref]
		)
		ll[0] = "%5"

		s = "("
		if ref == "PC":
			s += "#0x%x" % (basedisp + self.hi - 2)
		elif basedisp != 0:
			s += "#0x%x+" % basedisp + ref
		else:
			s += ref
		s += "+" + reg + wl
		if scale:
			s += "*%d" % (1 << scale)
		s += ")"
		il += [ll[0], ll[1:]]
		if outherdisp:
			s += " {XXX: outherdisp=0x%x} " % outherdisp
		return s


	def assy_eax(self, pj, id, eam, ear):
		il = []
		self.ea[id] = il
		eax = 1 << eam
		if eax > 0x40:
			eax = 0x100 << ear
		eamask = int(self.im.assy[-1], 16)
		if not eax & eamask:
			raise assy.Invalid("0x%x Wrong EA mode m=%d/r=%d" % (
			    self.lo, eam, ear), self.im)
		if eax == 0x0001:
			il += ["%%D%d" % ear]
			return "D%d" % ear
		if eax == 0x0002:
			il += ["%%A%d" % ear]
			return "A%d" % ear
		if eax == 0x0004:
			il += [ "%%A%d" % ear, []]
			return "(A%d)" % ear
		if eax == 0x0008:
			r = "A%d" % ear
			il += [ "%0", [
			    ["%0", "=", self.isz + "*", "%" + r],
			    ["%" + r, "=", "add", "i32",
				"%" + r, ",", "%d" % self.sz],
			]]
			return "(A%d)+" % ear
		if eax == 0x0010:
			'''Address Register Indirect with Predecrement'''
			r = "A%d" % ear
			il += [ "%0", [
			    ["%" + r, "=", "sub", "i32",
				"%" + r, ",", "%d" % self.sz],
			    ["%0", "=", "i32", "%" + r],
			]]
			return "-(%s)" % r
		if eax == 0x0020:
			'''Address Register Indirect with Displacement'''
			o = pj.m.bs16(self.hi)
			self.hi += 2
			if o < 0:
				il += [ "%0", [
				    ["%0", "=", "sub", self.isz + "*",
					"%%A%d" % ear, ",", "0x%x" % -o],
				]]
				return "(A%d-0x%x)" % (ear, -o)
			else:
				il += [ "%0", [
				    ["%0", "=", "add", self.isz + "*",
					"%%A%d" % ear, ",", "0x%x" % o],
				]]
				return "(A%d+0x%x)" % (ear, o)
		if eax == 0x0040:
			return self.assy_eaxt(pj, id, "A%d" % ear)
		if eax == 0x0100:
			o = pj.m.bu16(self.hi)
			self.hi += 2
			if o & 0x8000:
				o |= 0xffff0000
			self.dstadr = o
			il += [ "0x%x" % o, [] ]
			return assy.Arg_dst(pj, o)
		if eax == 0x0200:
			o = pj.m.bu32(self.hi)
			self.hi += 4
			self.dstadr = o
			il += [ "0x%x" % o, [] ]
			return assy.Arg_dst(pj, o)
		if eax == 0x0400:
			o = self.hi + pj.m.bs16(self.hi)
			self.hi += 2
			self.dstadr = o
			il += [ "0x%x" % o, [] ]
			return assy.Arg_dst(pj, o)
		if eax == 0x0800:
			return self.assy_eaxt(pj, id, "PC")
		if eax == 0x1000 and self.sz == 1:
			v = pj.m[self.hi+1]
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
		raise assy.Invalid(
		    "0x%x EA? 0x%04x m=%d/r=%d" % (self.lo, eax, eam, ear))

	def assy_ea(self, pj):
		try:
			j = self['ea']
		except KeyError as e:
			raise assy.Invalid("0x%x no EA?" % self.lo, e, self.lim)
		return self.assy_eax(pj, "s", j >> 3, j & 7)

	def assy_ead(self, pj):
		j = self['ead']
		return self.assy_eax(pj, "d", j & 7, j >> 3)

	def assy_L(self, pj):
		self.sz = 4
		self.isz = "i32"
		self.imsk = 0xffffffff
		self.mne += ".L"

	def assy_rlist(self, pj):
		return "+".join(self.subr_rlist())

	def assy_rot(self, pj):
		a = self['rot']
		if a == 0:
			a = 8
		return "#0x%x" % a

	def assy_vect(self, pj):
		if self.lang.trap_returns.get(self['vect']):
			# XXX: use flow
			pj.todo(self.hi, self.lang.disass)
		return "#%d" % self['vect']

	def assy_W(self, pj):
		self.sz = 2
		self.isz = "i16"
		self.imsk = 0xffff
		self.mne += ".W"

	def assy_long(self, pj):
		return "#0x%08x" % ((self['word1'] << 16) | self['word2'])

	def assy_word(self, pj):
		return "#0x%04x" % self['word']

	def assy_Z(self, pj):
		if self['sz'] == 3:
			raise assy.Invalid('0x%x F_sz == 3' % self.lo, self.lim)
		i, j, m = [
			[1, ".B", 0xff],
			[2, ".W", 0xffff],
			[4, ".L", 0xffffffff],
		] [self['sz']]
		self.sz = i
		self.isz = "i%d" % (i*8)
		self.imsk = m
		self.mne += j

	def pilmacro_AN(self):
		return "%%A%d" % self['An']

	def pilmacro_AX(self):
		return "%%A%d" % self['Ax']

	def pilmacro_AY(self):
		return "%%A%d" % self['Ay']

	def pilmacro_BN(self):
		j = self['bn'] % (self.sz*8)
		return "0x%x" % (1 << j)

	def pilmacro_CC(self):
		cc = self['cc']
		if cc == 0:
			return "1"
		if cc == 1:
			return "0"
		f = {
		4: "%SR.c",
		6: "%SR.z",
		8: "%SR.v",
		10: "%SR.n",
		}.get(cc & 0xe)
		if cc == 2 or cc == 3: # XXX check this
			f = self.add_il([
			    ["%0", "=", "or", "i1", "%SR.c", ",", "%SR.z"],
			], "%0")
		if cc == 12 or cc == 13:
			f = self.add_il([
			    ["%0", "=", "xor", "i1", "%SR.v", ",", "%SR.n"],
			], "%0")
		if cc == 14 or cc == 15:
			f = self.add_il([
			    ["%0", "=", "xor", "i1", "%SR.v", ",", "%SR.n"],
			    ["%1", "=", "or", "i1", "%SR.z", ",", "%0"],
			], "%1")
		assert f is not None
		if cc & 1:
			return f
		return self.add_il([
		    ["%0", "=", "xor", "i1", f, ",", "1"],
		], "%0")

	def pilmacro_HI(self):
		return "0x%x" % self.hi

	def pilmacro_IBN(self):
		j = self['bn'] % (self.sz*8)
		return "0x%x" % (self.imsk ^ (1 << j))

	def pilmacro_CONST(self):
		i = self['const']
		if i == 0:
			i = 0
		return "0x%x" % i

	def pilmacro_DATA(self):
		return "0x%x" % self.v

	def pilmacro_DATA8(self):
		i = self['data8']
		if i & 0x80:
			i -= 256
			return "-0x%x" % (-i)
		else:
			return "0x%x" % i

	def pilmacro_DN(self):
		return "%%D%d" % self['Dn']

	def pilmacro_DX(self):
		return "%%D%d" % self['Dx']

	def pilmacro_DY(self):
		return "%%D%d" % self['Dy']

	def pilmacro_DST(self):
		return "0x%x" % self.dstadr

	def pilmacro_EA(self):
		il = self.ea["s"]
		if len(il) == 1:
			return il[0]
		j = self.icache.get("EA")
		if j is not None:
			return j
		if len(il[1]) > 0:
			j = self.add_il(il[1], il[0])
		else:
			j = il[0]
		self.icache["EAs"] = j
		j = self.add_il([
			[ "%0", "=", "load", self.isz, ",", self.isz + "*", j ],
		], "%0")
		self.icache["EA"] = j
		return j

	def pilmacro_PTR_EA(self):
		il = self.ea["s"]
		assert len(il) == 2
		if len(il[1]) > 0:
			return self.add_il(il[1], il[0])
		else:
			return il[0]

	def pilmacro_ROT(self):
		a = self['rot']
		if a == 0:
			a = 8
		return "0x%x" % a

	def pilmacro_SZ(self):
		return self.isz

	def pilmacro_WORDSGN(self):
		i = self['word']
		if i & 0x8000:
			i -= 65536
		if i < 0:
			return "-0x%x" % (-i)
		else:
			return "0x%x" % i

	def pilmacro_WORD(self):
		return "0x%x" % self['word']

	def isubr_LEA(self, arg, which):
		if not which in self.ea:
			raise assy.Invalid("0x%x No '%s' in EA %s" % (self.lo, which, str(self.im)))
		il = self.ea[which]
		if len(il) == 1:
			self.add_il([
			    [ il[0], "=", self.isz, arg[0]],
			])
			return
		assert len(il) == 2
		j = self.icache.get("EA" + which)
		if j is None:
			self.icache["EA" + which] = il[0]
			ll = []
			ll += il[1]
			ll.append(
			    [ "store", self.isz, arg[0], ",",
				self.isz + "*", il[0]],
			)
			self.add_il(ll)
		else:
			self.add_il([
			    [ "store", self.isz, arg[0], ",",
				self.isz + "*", j],
			])

	def pilfunc_LEAD(self, arg):
		self.isubr_LEA(arg, "d")

	def pilfunc_LEAS(self, arg):
		self.isubr_LEA(arg, "s")

	def pilfunc_MOVEM_RM(self, arg):
		ll = []
		eam = self['ea'] >> 3
		if eam == 3:
			raise assy.Invalid(
			    "0x%x MOVEM r->m predecrement" % (self.lo))
		elif eam == 4:
			dr = "%%A%d" % (self['ea'] & 7)
			rl = self.subr_rlist()
			if dr[1:] in rl:
				return
				raise assy.Missing(
				    "0x%x MOVEM push(SP)" % (self.lo))
			for r in self.subr_rlist():
				ll += [
					[ dr, "=", "sub", "i32", dr, ",",
					    "%d" % self.sz],
					[ "store", "SZ", "%" + r, ",",
					    self.isz + "*", dr],
				]
		else:
			x = self.pilmacro_PTR_EA()
			ll += [
				[ "%0", "=", "SZ", x ],
			]
			for r in self.subr_rlist():
				ll += [
					[ "store", "SZ", "%" + r, ",",
					    self.isz + "*", "%0"],
					[ "%0", "=", "add", "i32","%0",",",
					    "%d" % self.sz],
				]
		self.add_il(ll)

	def pilfunc_MOVEM_MR(self, arg):
		ll = []
		eam = self['ea'] >> 3
		if eam == 3:
			sr = "%%A%d" % (self['ea'] & 7)
			for r in self.subr_rlist():
				if r == sr[1:]:
					ll += [
						[ sr, "=", "add", "i32", sr,",",
						    "%d" % self.sz],
					]
					continue
				ll += [
					[ "%" + r, "=", "load", self.isz, ",",
					    self.isz + "*", sr ],
					[ sr, "=", "add", "i32", sr,",",
					    "%d" % self.sz],
				]
				if self.sz == 4:
					continue
				ll += [
					[ "%" + r, "=", "sext", self.isz,
					    "%" + r, "to", "i32"],
				]
		elif eam == 4:
			raise assy.Invalid(
			    "0x%x MOVEM m->r postincrement" % (self.lo))
		else:
			x = self.pilmacro_PTR_EA()
			ll += [
				[ "%0", "=", self.isz + "*", x ],
			]
			for r in self.subr_rlist():
				ll += [
					[ "%" + r, "=", "load", self.isz, ",",
					    self.isz + "*", "%0" ],
					[ "%0", "=", "add", "i32", "%0",",",
					    "%d" % self.sz],
				]
				if self.sz == 4:
					continue
				ll += [
					[ "%" + r, "=", "sext", self.isz,
					    "%" + r, "to", "i32"],
				]
		self.add_il(ll)

	def pilfunc_STDF4(self, arg):
		self.add_il([
			["%SR.n", "=", "icmp", "slt","SZ",arg[0],",","0"],
			["%SR.z", "=", "icmp", "eq","SZ",arg[0],",","0"],
			["%SR.v", "=", "i1", "0"],
			["%SR.c", "=", "i1", "0"],
		])

	def pilfunc_MOVEP1(self, arg):
		o = self['disp16']
		if o & 0x8000:
			o -= 1 << 16
			oo = "-0x%x" % -o
		else:
			oo = "0x%x" % o
		l = [
			["%0", "=", "add", "i32*", "%%A%d" % self['An'], ",", oo],
			["%1", "=", self.isz, "%%D%d" % self['Dn']],
		]
		for i in range(0, self.sz):
			l.append(["%2", "=", "trunc", self.isz, "%1", "to", "i8"])
			l.append(["%1", "=", "lshr", self.isz, "%1", ",", "8"])
			l.append(["store", "i8", "%2", ",", "i8*", "%0"])
			l.append(["%0", "=", "add", "i32*", "%0", ",", "2"])
		self.add_il(l)

	def pilfunc_MOVEP2(self, arg):
		o = self['disp16']
		if o & 0x8000:
			o -= 1 << 16
			oo = "-0x%x" % -o
		else:
			oo = "0x%x" % o
		l = [
			["%0", "=", "add", "i32*", "%%A%d" % self['An'], ",", oo],
			["%1", "=", self.isz, "0"],
		]
		for i in range(0, self.sz):
			l.append(["%2", "=", "load", "i8", ",", "i8*", "%0"])
			l.append(["%0", "=", "add", "i32*", "%0", ",", "2"])
			l.append(["%1", "=", "shl", self.isz, "%1", ",", "8"])
			l.append(["%1", "=", "or", self.isz, "%1", ",", "%2"])

		l.append(["%%D%d" % self['Dn'], "=", self.isz, "%1"])
		self.add_il(l)


class m68000(assy.Instree_disass):
	def __init__(self, lang="m68000"):
		super().__init__(
		    lang,
		    ins_word=16,
		    mem_word=8,
		    endian=">",
                    abits=32,
                )
		self.it.load_string(m68000_desc, m68000_ins)
		self.il = None
		self.verbatim |= set(["CCR", "SR", "USP"])
		self.ea_fullext = False
		self.ea_scale = False
		self.trap_returns = {}

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
		y = self.dataptr(pj, 0)
		y.lcmt = "Reset SP"
		vn = {}
		vi = {}
		a = 0x4
		while a < hi:
			x = pj.m.bu32(a)
			if x in (0x0, 0xffffffff):
				y = self.dataptr(pj, a)
				#y = data.Const(pj, a, a + 4,
				#    "0x%04x", pj.m.bu32, 4)
			else:
				if x not in vn:
					try:
						vi[x] = self.disass(pj, x)
						vn[x] = []
						vn[x].append(a >> 2)
					except assy.Invalid:
						pass
					except mem.MemError:
						pass
				if x > a:
					y = self.codeptr(pj, a)
			y.lcmt = self.vector_name(a >> 2)
			hi = min(hi, x)
			a += 4
		mv = 0
		for i in vn:
			for v in vn[i]:
				k = self.vector_name(v)
				if vi[i] != None and isinstance(vi[i], m68000_ins):
					vi[i].lcmt += "--> " + k + "\n"

			if len(vn[i]) == 1:
				k = self.vector_name(vn[i][0])
				pj.m.set_label(i, k)
			else:
				pj.m.set_label(i, "VECTORS_%d" % mv)
				mv += 1

	def codeptr(self, pj, adr):
		t = pj.m.bu32(adr)
		c = data.Codeptr(pj.m, adr, adr + 4, t)
		pj.todo(t, self.disass)
		return c

	def dataptr(self, pj, adr):
		return data.Dataptr(pj.m, adr, adr + 4, pj.m.bu32(adr))
		

