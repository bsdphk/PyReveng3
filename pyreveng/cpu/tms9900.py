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
# XXX: Does "NEG *R2+" increment once or twice ? (we assume once)
# XXX: But how does "A *R2+, R2" behave  ?
# XXX: and what about "A *R2+, *R2+" ?

'''Texas Instruments TMS9990
'''

from pyreveng import assy, data

tms9900_desc = """

# Page numbers referst to:
#	9900 Family Systems Design
#	and Data Book
#	LCC4000 97049-118-NI

# 6-18 / 328
LI	w,i	|0 0 0 0 0 0 1 0 0 0 0|n| w	| iop				| {
	R = i16 IMM
	FLAGS3 IMM
}
LIMI	i	|0 0 0 0 0 0 1 1 0 0 0|0 0 0 0 0| iop				| {
	%status.imask = trunc i16 IMM to i4
}

# 6-19 / 329
LWPI	i	|0 0 0 0 0 0 1 0 1 1 1|0 0 0 0 0| iop				| {
	LWPI IMM
}
MOV	so,do	|1 1 0 0|td | d     |ts | s     | {
	LD RS
	FLAGS3 RS
}

# 6-20 / 330
MOVb	so,do	|1 1 0 1|td | d     |ts | s     | {
	LD RS
	PARITY RS
	FLAGS3 RS
}

# 6-21 / 331
SWPB	so	|0 0 0 0 0 1 1 0 1 1|ts | s     | {
	%0 = llvm.bswap.i16 ( i16 RS )
	LS %0
}
STST	w	|0 0 0 0 0 0 1 0 1 1 0|0| w	| {
	R = i16 %status
}

# 6-22 / 332
STWP	w	|0 0 0 0 0 0 1 0 1 0 1 0| w	| {
	R = %WP
}

# 6-23 / 333
A	so,do	|1 0 1 0|td | d     |ts | s     | {
	%0 = add i16 RS , RD
	FLAGS5 RS RD %0
	LD %0
}

# 6-24 / 334
Ab	so,do	|1 0 1 1|td | d     |ts | s     | {
	%0 = add i8 RS , RD
	FLAGS3 %0
	FLAGS5 RS RD %0
	PARITY %0
	LD %0
}

# 6-25 / 335
AI	w,i	|0 0 0 0 0 0 1 0 0 0 1|n| w	| iop				| {
	%0 = add i16 R , IMM
	FLAGS5 R IMM %0
	R = %0
}
S	so,do	|0 1 1 0|td | d     |ts | s     | {
	%0 = sub i16 RS , RD
	FLAGS5 RS RD %0
	LD %0
}

# 6-26 / 336
Sb	so,do	|0 1 1 1|td | d     |ts | s     | {
	%0 = sub i8 RS , RD
	FLAGS5 RS RD %0
	PARITY %0
	LD %0
}

# 6-27 / 337
INC	so	|0 0 0 0 0 1 0 1 1 0|ts | s     | {
	%0 = add i16 RS , 0x0001
	FLAGS5 RS 1 %0
	LS %0
}
INCT	so	|0 0 0 0 0 1 0 1 1 1|ts | s     | {
	%0 = add i16 RS , 0x0002
	FLAGS5 RS 2 %0
	LS %0
}

# 6-28 / 338
DEC	so	|0 0 0 0 0 1 1 0 0 0|ts | s	| {
	%0 = sub i16 RS , 0x0001
	FLAGS5 RS 1 %0
	LS %0
}
DECT	so	|0 0 0 0 0 1 1 0 0 1|ts | s	| {
	%0 = sub i16 RS , 0x0002
	FLAGS5 RS 2 %0
	LS %0
}

# 6-29 / 339
NEG	so	|0 0 0 0 0 1 0 1 0 0|ts | s     | {
	%0 = sub i16 0x0000 , RS
	%status.ov = icmp eq i16 RS , 0x8000
	FLAGS3 %0
	LS %0
}
ABS	so	|0 0 0 0 0 1 1 1 0 1|ts | s     | {
	%0 = icmp uge i16 RS , 0x8000
	%1 = sub i16 0 , RS
	%status.ov = icmp eq i16 RS , 0x8000
	FLAGS3 RS
	%2 = select i16 %0 , %1 , RS
	LS %2
}

# 6-30 / 340
MPY	so,w	|0 0 1 1 1 0| w     |ts | s     | {
	%0 = zext i16 R to i32
	%1 = zext i16 RS to i32
	%2 = mul i32 %0 , %1
	RN = trunc i32 %2 to i16
	%3 = shr i32 %2 , 16
	R = trunc i32 %3 to i16
}

# 6-31 / 341
DIV	so,w	|0 0 1 1 1 1| w     |ts | s     | {
	%status.ov = icmp ge i16 R , RS
	%0 = zext i16 R to i32
	%1 = shl i32 %0 , 16
	%2 = zext i16 RN to i32
	%3 = or i32 %1 , %2
	%4 = zext i16 RS to i32
	%5 = udiv i32 %3 , %4
	%6 = urem i32 %3 , %4
	%7 = trunc i32 %5 to i16
	%8 = trunc i32 %6 to i16
	R = select i16 %status.ov , R , %7
	RN = select i16 %status.ov , RN , %8
}

# 6-32 / 342
C	so,do	|1 0 0 0|td | d     |ts | s     | {
	CMPFLAGS i16 RS RD
}

# 6-33 / 343
Cb	so,do	|1 0 0 1|td | d     |ts | s     | {
	PARITY RS
	CMPFLAGS i8 RS RD
}

# 6-34 / 344
CI	w,i	|0 0 0 0 0 0 1 0 1 0 0|n| w	| iop				| {
	CMPFLAGS i16 R IMM
}
COC	so,w	|0 0 1 0 0 0| w     |ts | s     | {
	%0 = and i16 R , RS
	%status.eq = icmp eq i16 %0 , RS
}

# 6-35 / 345
CZC	so,w	|0 0 1 0 0 1| w     |ts | s     | {
	%0 = and i16 R , RS
	%status.eq = icmp eq i16 %0 , 0x0000
}

# 6-36 / 346
ANDI	w,i	|0 0 0 0 0 0 1 0 0 1 0|n| w	| iop				| {
	R = and i16 R , IMM
	FLAGS3 R
}

# 6-37 / 347
ORI	w,i	|0 0 0 0 0 0 1 0 0 1 1|n| w	| iop				| {
	R = or i16 R , IMM
	FLAGS3 R
}

# 6-38 / 348
XOR	so,w	|0 0 1 0 1 0| w     |ts | s     | {
	R = xor i16 R , RS
	FLAGS3 R
}
INV	so	|0 0 0 0 0 1 0 1 0 1|ts | s     | {
	%0 = xor i16 RS , 0xffff
	LS %0
	FLAGS3 %0
}

# 6-39 / 349
CLR	so	|0 0 0 0 0 1 0 0 1 1|ts | s     | {
	LS 0x0000
}
SETO	so	|0 0 0 0 0 1 1 1 0 0|ts | s     | {
	LS 0xffff
}

# 6-40 / 350
SOC	so,do	|1 1 1 0|td | d     |ts | s     | {
	%0 = or i16 RS , RD
	LD %0
	FLAGS3 %0
}
SOCb	so,do	|1 1 1 1|td | d     |ts | s     | {
	%0 = or i8 RS , RD
	LD %0
	PARITY %0
	FLAGS3 %0
}

# 6-41 / 351
SZC	so,do	|0 1 0 0|td | d     |ts | s     | {
	%0 = xor i16 RS , 0xffff
	%1 = and i16 RD , %0
	LD %1
	FLAGS3 %1
}

# 6-42 / 352
SZCb	so,do	|0 1 0 1|td | d     |ts | s     | {
	%0 = xor i8 RS , 0xffff
	%1 = and i8 RD , %0
	LD %1
	PARITY %1
	FLAGS3 %1
}

# 6-43 / 353
SRA	w,R0	|0 0 0 0 1 0 0 0|0 0 0 0| w	| {
	// NB R0=zero is wrong
	%0 = and i16 R0 , 0x000f
	%1 = icmp eq i16 %0 , 0
	%2 = select %1 i16 16 , 0
	%3 = sub i16 %0 , 1
	%4 = lshr i16 R , %3
	%status.c = trunc i16 %4 to i1
	%5 = lshr i16 %4 , 1
	FLAGS3 %5
	R = %5
}

SRA	w,sc	|0 0 0 0 1 0 0 0| c     | w	| {
	%0 = lshr i16 R , SCNT1
	%status.c = trunc i16 %0 to i1
	%1 = lshr i16 %0 , 1
	FLAGS3 %1
	R = %1
}

# 6-44 / 354
SLA	w,R0	|0 0 0 0 1 0 1 0|0 0 0 0| w	| {
	// NB R0=zero is wrong
	%0 = and i16 R0 , 0x000f
	%1 = icmp eq i16 %0 , 0
	%2 = select %1 i16 16 , 0
	%3 = sub i16 %0 , 1
	%4 = shl i16 R , %3
	%5 = lshr i16 %4 , 15
	%status.c = trunc i16 %5 to i1
	%6 = shl i16 %4 , 1
	FLAGS3 %6
	%7 = xor i16 R , %6
	%8 = lshr i16 %2 , 15
	%status.ov = trunc i16 %8 to i1
	R = %6
}
SLA	w,sc	|0 0 0 0 1 0 1 0| c     | w	| {
	%0 = shl i16 R , SCNT1
	%1 = lshr i16 %0 , 15
	%status.c = trunc i16 %1 to i1
	%2 = shl i16 %0 , 1
	FLAGS3 %2
	%3 = xor i16 R , %2
	%4 = lshr i16 %3 , 15
	%status.ov = trunc i16 %4 to i1
	R = %2
}

# 6-45 / 355
SRL	w,R0	|0 0 0 0 1 0 0 1|0 0 0 0| w	| {
	// NB R0=zero is wrong
	%0 = and i16 R0 , 0x000f
	%1 = sub i16 %0 , 1
	%2 = lshr i16 R , %1
	%status.c = trunc i16 %2 to i1
	%3 = lshr i16 %2 , 1
	FLAGS3 %3
	R = %3
}

SRL	w,sc	|0 0 0 0 1 0 0 1| c     | w	| {
	%0 = srl i16 R , SCNT1
	%status.c = trunc i16 %0 to i1
	%1 = srl i16 %0 , 1
	FLAGS3 %1
	R = %1
}

SRC	w,R0	|0 0 0 0 1 0 1 1|0 0 0 0| w	| {
	// NB R0=zero is wrong
	%0 = zext i16 R to i32
	%1 = shl i32 %0 , 16
	%2 = or i32 %0 , %1
	%3 = and i16 R0 , 0x000f
	%4 = sub i16 %3 , 1
	%5 = lshr i32 %2 , %4
	%status.c = trunc i32 %4 to i1
	%6 = lshr i32 %5 , 1
	R = trunc i32 %6 to i16
	FLAGS3 R
}

SRC	w,sc	|0 0 0 0 1 0 1 1| c     | w	| {
	%0 = zext i16 R to i32
	%1 = shl i32 %0 , 16
	%2 = or i32 %0 , %1
	%3 = lshr i32 %2 , SCNT1
	%status.c = trunc i32 %3 to i1
	%4 = lshr i32 %3 , 1
	R = trunc i32 %4 to i16
	FLAGS3 R
}

# 6-46 / 356
B	da,>J	|0 0 0 0 0 1 0 0 0 1|1 0|0 0 0 0| da				| {
	br BRYES
}
B	so,>J	|0 0 0 0 0 1 0 0 0 1|ts | s     | {
	br label AS
}

# 6-47 / 357
BL	da,>C	|0 0 0 0 0 1 1 0 1 0|1 0|0 0 0 0| da				| {
	%R11 = NEXT
	br BRYES
}
BL	so,>C	|0 0 0 0 0 1 1 0 1 0|ts | s     | {
	%R11 = NEXT
	br label AS
}

# 6-48 / 358
BLWP	blwp1,blwp2,>C	|0 0 0 0 0 1 0 0 0 0|1 0|0 0 0 0| ptr				| {
	BLWP
}

BLWP	so	|0 0 0 0 0 1 0 0 0 0|ts | s     | {
	BLWPDYN AS
}

# 6-49 / 259
XOP	?	|0 0 1 0 1 1| d     |ts | s     |

# 6-50 / 360
RTWP	>R	|0 0 0 0 0 0 1 1 1 0 0| n	| {
	RTWP
}
JMP	r,>J	|0 0 0 1 0 0 0 0| disp		| {
	br BRYES
}

# 6-51 / 361
X	so	|0 0 0 0 0 1 0 0 1 0|ts | s	|

# 6-52 / 362
JH	r,>JC	|0 0 0 1 1 0 1 1| disp		| {
	%0 = xor i1 %status.eq , 0x1
	%1 = and i1 %0 , %status.lgt
	br i1 %1 , BRYES , BRNO
}
JL	r,>JC	|0 0 0 1 1 0 1 0| disp		| {
	%0 = or i1 %status.lgt , %status.eq
	br i1 %0 , BRNO , BRYES
}
JHE	r,>JC	|0 0 0 1 0 1 0 0| disp		| {
	%0 = and i1 %status.lgt , %status.eq
	br i1 %0 , BRYES , BRNO
}
JLE	r,>JC	|0 0 0 1 0 0 1 0| disp		| {
	%0 = xor i1 %status.lgt , 0x1
	%1 = and i1 %0 , %status.eq
	br i1 %1 , BRYES , BRNO
}
JGT	r,>JC	|0 0 0 1 0 1 0 1| disp		| {
	br i1 %status.agt , BRYES , BRNO
}
JLT	r,>JC	|0 0 0 1 0 0 0 1| disp		| {
	%0 = or i1 %status.agt , %status.eq
	br i1 %0 , BRNO , BRYES
}
JEQ	r,>JC	|0 0 0 1 0 0 1 1| disp		| {
	br i1 %status.eq , BRYES , BRNO
}
JNE	r,>JC	|0 0 0 1 0 1 1 0| disp		| {
	br i1 %status.eq , BRNO , BRYES
}
JOC	r,>JC	|0 0 0 1 1 0 0 0| disp		| {
	br i1 %status.c , BRYES , BRNO
}
JNC	r,>JC	|0 0 0 1 0 1 1 1| disp		| {
	br i1 %status.c , BRNO , BRYES
}
JNO	r,>JC	|0 0 0 1 1 0 0 1| disp		| {
	br i1 %status.ov , BRNO , BRYES
}
JOP	r,>JC	|0 0 0 1 1 1 0 0| disp		| {
	br i1 %status.op , BRYES , BRNO
}

# 6-53 / 363
SBO	cru	|0 0 0 1 1 1 0 1| cru		| {
	store i1 1, i1* address_space(1) CRU
}

# 6-54 / 364
SBZ	cru	|0 0 0 1 1 1 1 0| cru		| {
	store i1 0, i1* address_space(1) CRU
}
# NB special flags
TB	cru	|0 0 0 1 1 1 1 1| cru		| {
	%status.eq = load i1 , i1* address_space(1) CRU
}

# 6-55 / 365
LDCR	c,so	|0 0 1 1 0 0| c     |ts | s     | {
	LDCR RS
}

# 6-57 / 367
STCR	c,do	|0 0 1 1 0 1| c     |td | d     | {
	STCR %0
	LD %0
}

# 6-58 / 368
LREX	?	|0 0 0 0 0 0 1 1 1 1 1| n	|
CKOF	?	|0 0 0 0 0 0 1 1 1 1 0| n	|
CKON	?	|0 0 0 0 0 0 1 1 1 0 1| n	|
RSET	?	|0 0 0 0 0 0 1 1 0 1 1| n	|
IDLE	?	|0 0 0 0 0 0 1 1 0 1 0| n	|

"""

class vector(data.Data):
    def __init__(self, asp, adr, cx):
        super().__init__(asp, adr, adr + 4)
        self.ws = asp.bu16(adr)
        self.dstadr = asp.bu16(adr + 2)
        cx.disass(self.dstadr, asp)

    def render(self):
        return "WP=0x%04x,IP=%s" % (self.ws, self.aspace.adr(self.dstadr))


class Tms9900_ins(assy.Instree_ins):
    pass

    def sz(self):
        if self.mne[-1] == 'b':
            return 8
        return 16

    def arg_o(self, sd):
        to = self['t' + sd]
        o = self[sd]
        nm = 'G' + sd
        if to == 0:
            return "R%d" % o
        if to == 1:
            return "*R%d" % o

        if to == 2:
            v = self.lang.m.bu16(self.hi)
            self.hi += 2
            self[nm] = v
            if o != 0:
                return "R%d+#0x%04x" % (o, v)

            x = list(self.lang.m.find(v))
            if x:
                return assy.Arg_ref(self.lang.m, x[0])

            try:
                w = self.lang.m.bu16(v)
            except:
                return assy.Arg_dst(self.lang.m, v, "@")

            if self.mne[-1] == "b":
                c = data.Const(self.lang.m, v, v + 1)
                c.typ = ".BYTE"
                c.fmt = "0x%02x" % self.lang.m[v]
            else:
                c = data.Const(self.lang.m, v, v + 2)
                c.typ = ".WORD"
                c.fmt = "0x%04x" % w
            return assy.Arg_ref(self.lang.m, c)

        if to == 3:
            return "*R%d+" % o

    #-----------------------------------
    # Methods related to assembly output
    #-----------------------------------

    def assy_b(self):
        if self['b']:
            ins.mne += "B"
    def assy_blwp1(self):
        a = self['ptr']
        self.cache['blwp1'] = self.lang.m.bu16(a)
        if not self.lang.m.occupied(a):
            data.Pstruct(self.lang.m, a, ">HH", ".BLWP\t0x%04x, 0x%04x")
        return "WP=0x%04x" % self.lang.m.bu16(a)

    def assy_blwp2(self):
        a = self['ptr']
        self.cache['blwp2'] = self.lang.m.bu16(a + 2)
        self.dstadr = self.lang.m.bu16(a+2)
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_c(self):
        x = self['c']
        if x == 0:
            x = 16
        if x <= 8:
            self.mne += "b"
        return assy.Arg_imm(x)

    def assy_cru(self):
        i = self['cru']
        if i & 0x80:
            i -= 0x100
        # XXX: This doubling may be model-dependent
        # XXX: Based on 9980/9981
        i *= 2
        return "R12%#+x" % i

    def assy_da(self):
        self.dstadr = self['da']
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_do(self):
        return self.arg_o('d')

    def assy_i(self):
        return assy.Arg_imm(self['iop'], 16)

    def assy_so(self):
        return self.arg_o('s')

    def assy_r(self):
        i = self['disp']
        if i & 0x80:
            i -= 256
        self.dstadr = self.hi + i * 2
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_sc(self):
        if self['c'] == 0:
            return "R0"
        else:
            return "#%d" % self['c']

    def assy_w(self):
        return "R%d" % self['w']

    #-----------------------------
    # Methods related to IL output
    #-----------------------------

    def pilmacro_R(self):
        return "%%R%d" % self['w']

    def pilmacro_RN(self):
        assert self['w'] != 15
        return "%%R%d" % (self['w'] + 1)

    def pilmacro_IMM(self):
        return "0x%04x" % self['iop']

    def ilarg_ao(self, sd):
        t = self['t' + sd]
        s = self[sd]
        nm = 'G' + sd
        sz = self.sz()
        tsz = "i%d" % sz
        r = "%%R%d" % s
        assert t != 0

        if t == 1:
            return self.add_il([
                [ "%0", '=', 'inttoptr', 'i16', r,
                    'to', tsz + "*"],
            ], "%0")

        if t == 2 and s == 0:
            return "0x%04x" % self[nm]

        if t == 2:
            return self.add_il([
                [ "%0", '=', 'add', 'i16', r, ',',
                    "0x%04x" % self[nm]],
                [ "%1", '=', 'inttoptr', "i16", "%0",
                    'to', tsz + "*"],
            ], "%1")

        assert t == 3
        z = self.cache.get(sd)
        if z is not None:
            return z
        z = self.add_il([
            [ "%0", '=', 'inttoptr', "i16", r, 'to', tsz + "*"],
            [ r, '=', 'add', 'i16', r, ',', '0x%04x' % (sz // 8)],
        ], "%0")
        self.cache[sd] = z
        return z

    def ilarg_ro(self, sd):
        t = self['t' + sd]
        s = self[sd]
        nm = 'G' + sd
        sz = self.sz()
        tsz = "i%d" % sz
        r = "%%R%d" % s
        if t == 0 and sz == 16:
            return r

        if t == 0 and sz == 8:
            return self.add_il([
                [ "%0", '=', 'shr', "i16", r, ',', '8' ],
                [ "%1", '=', 'trunc', "i16", "%0", 'to', 'i8' ],
            ], "%1")

        a = self.ilarg_ao(sd)
        return self.add_il([
            [ "%0", '=', 'load', tsz, ',', tsz + "*", a],
        ], "%0")

    def ilarg_lo(self, sd, args):
        t = self['t' + sd]
        s = self[sd]
        nm = 'G' + sd
        sz = self.sz()
        tsz = "i%d" % sz
        r = "%%R%d" % s
        if t == 0 and sz == 16:
            self.add_il([ [ r, "=", tsz, args[0]], ])
            return
        if t == 0 and sz == 8:
            self.add_il([
                [ "%0", "=", "zext", tsz, args[0],
                    "to", "i16" ],
                [ "%1", "=", "shl", "i16", "%0", ",", "8" ],
                [ r, "=", "and", "i16", r, ",", "0x00ff" ],
                [ r, "=", "or", "i16", r, ",", "%1" ],
            ])
            return

        a = self.ilarg_ao(sd)
        self.add_il([
            [ 'store', tsz, args[0], ',', tsz + "*", a],
        ])
        return

    def pilmacro_SZ(self):
        return "i%d" % self.sz()

    def pilmacro_AS(self):
        return self.ilarg_ao('s')

    def pilfunc_LS(self, args):
        self.ilarg_lo('s', args)

    def pilmacro_RS(self):
        z = self.cache.get("RS")
        if z is None:
            z = self.cache["RS"] = self.ilarg_ro('s')
        return z

    def pilmacro_AD(self):
        return self.ilarg_ao(self['td'], self['d'], 'Gd')

    def pilfunc_LD(self, args):
        self.ilarg_lo('d', args)

    def pilmacro_RD(self):
        z = self.cache.get("RD")
        if z is None:
            z = self.cache["RD"] = self.ilarg_ro('d')
        return z

    def pilmacro_CRU(self):
        o = self['cru']
        l = []
        l.append([ '%0', "=", "lshr", "i16", "%R12", ",", "1"])
        if o & 0x80:
            l.append(
                [ '%1', "=", "sub", "i16", "%0", ",",
                "0x%04x" % (256-o) ])
        else:
            l.append(
                [ '%1', "=", "add", "i16", "%0", ",",
                "0x%04x" % o ])
        l.append([ '%2', "=", "inttoptr", "i16", "%1", "to",
                "i1", "address_space", "(", "1", ")", "*"])
        return self.add_il(l, "%2")

    def pilmacro_SCNT1(self):
        c = self['c']
        if c == 0:
            c = 16
        return "0x%x" % (c - 1)

    def pilmacro_SCNT(self):
        c = self['c']
        if c == 0:
            c = 16
        return "0x%x" % c

    def pilmacro_BRYES(self):
        return ["label", "0x%04x" % self.flow_out[0].to]

    def pilmacro_BRNO(self):
        return ["label", "0x%04x" % self.flow_out[1].to]

    def pilmacro_NEXT(self):
        return "0x%04x" % self.hi

    def aliasregs(self):
        l = []
        l.append(["%50", "=", "inttoptr", "i16", "%WP", "to", "i16*"])
        l.append(["%R0", "=", "pyreveng.alias", "(", "%50", ")"])
        for r in range(1,16):
            rr = "%%%d" % (50 + r)
            l.append(
                [rr, "=", "add", "i16*", "%50", ",", "%d" % (2*r)])
            l.append(
                ["%%R%d" % r, "=", "pyreveng.alias", "(", rr, ")"])
        return l

    def pilfunc_BLWP(self, args):
        l = []
        l.append(["%0", "=", "i16", "%WP"])
        l.append(["%WP", "=", "i16", "0x%04x" % self.cache['blwp1'] ])
        l += self.aliasregs()
        l.append(["%R13", "=", "i16", "%0"])
        l.append(["%R14", "=", "i16", "0x%04x" % self.hi])
        l.append(["%R15", "=", "i16", "%status"])
        l.append(["br", "label", "i16*",
            "0x%04x" % self.cache['blwp2'] ])
        self.add_il(l)

    def pilfunc_BLWPDYN(self, args):
        l = []
        l.append(["%0", '=', "i16*", args[0]])
        l.append(["%1", '=', 'load', 'i16', ',', "i16*", "%0"])
        l.append(["%2", '=', 'add', 'i16*', "%0", ',', '2'])
        l.append(["%3", '=', 'load', 'i16', ',', "i16*", "%2"])
        l.append(["%4", "=", "i16", "%WP"])
        l.append(["%WP", "=", "i16", "%1"])
        l += self.aliasregs()
        l.append(["%R13", "=", "i16", "%4"])
        l.append(["%R14", "=", "i16", "0x%04x" % self.hi])
        l.append(["%R15", "=", "i16", "%status"])
        l.append(["br", "label", "i16*", "%3"])
        self.add_il(l)

    def pilfunc_RTWP(self, args):
        l = []
        l.append(["%status", "=", "i16", "%R15"])
        l.append(["%1", "=", "inttoptr", "i16", "%R14", "to", "i16*"])
        l.append(["%WP", "=", "i16", "%R13"])
        l += self.aliasregs()
        l.append(["br", "label", "i16*", "%1"])
        self.add_il(l)

    def pilfunc_PARITY(self, args):
        # args: [result]
        assert self.sz() == 8
        sz = "i%d" % self.sz()
        self.add_il([
            ["%status.op", "=", "pyreveng.parity.odd.i1",
                "(", sz, args[0], ')'],
        ])

    def pilfunc_FLAGS3(self, args):
        # args: [result]
        sz = "i%d" % self.sz()
        self.add_il([
            ["%status.lgt", "=", "icmp", "ne", sz,
                args[0], ",", "0"],
            ["%status.agt", "=", "icmp", "sgt", sz,
                args[0], ",", "0"],
            ["%status.eq",  "=", "icmp", "eq", sz,
                args[0], ',', "0" ],
        ])

    def pilfunc_FLAGS5(self, args):
        # args: [src, dst, result]
        sz = "i%d" % self.sz()
        self.add_il([
            ["%status.lgt", "=", "icmp", "ne", sz,
                args[2], ",", "0"],
            ["%status.eq",  "=", "icmp", "eq", sz,
                args[2], ',', "0" ],
            ["%status.c", "=", "pyreveng.carry.i1",
                "(", sz, args[0], ",", sz, args[1], ")" ],
            ["%status.ov", "=", "pyreveng.tms99x.ov.i1", "(",
                sz, args[0], ",",
                sz, args[1], ",",
                sz, args[2], ")" ],
        ])

    def pilfunc_CMPFLAGS(self, args):
        # args: [sz, src, dst]
        self.add_il([
            ["%status.lgt", "=", "icmp", "ugt",
                args[0], args[1], ",", args[2]],
            ["%status.agt", "=", "icmp", "sgt",
                args[0], args[1], ",", args[2]],
            ["%status.eq", "=", "icmp", "eq",
                args[0], args[1], ",", args[2]],
        ])

    def pilfunc_LDCR(self, args):
        # pg 365
        c = self['c']
        if c == 0:
            c = 16
        # print(self, "LDCR", c, args)
        self.pilfunc_FLAGS3(args)
        l = []
        ty = "i%d" % self.sz()
        if c <= 8:
            self.pilfunc_PARITY(args)
        l.append(["%0", "=", ty, args[0]])
        l.append(["%1", "=", "shr", "i16", "%R12", ",", "1"])
        l.append(["%2", "=", "inttoptr", "i1", "%1",
            "to", "i16", "address_space(1)*"])
        for j in range(c):
            l.append(["%3", "=", "trunc", ty, "%0", "to", "i1"])
            l.append(["store", "i1", "%3",
                "i1", "address_space(1)*", "%2"])
            l.append(["%0", "=", "shr", ty, "%0", ",", "1"])
            l.append(["%2", "=", "add",
                "i1", "address_space(1)*", "%2", ",", "1"])
        self.add_il(l)

    def pilfunc_STCR(self, args):
        # pg 367
        c = self['c']
        if c == 0:
            c = 16
        print(self, "STCR", c, args)
        l = []
        ty = "i%d" % self.sz()
        l.append(["%0", "=", ty, "0"])
        l.append(["%1", "=", "shr", "i16", "%R12", ",", "1"])
        l.append(["%2", "=", "inttoptr", "i1", "%1",
            "to", "i16", "address_space(1)*"])
        for j in range(c):
            l.append(["%3", "=", "load", "i1", ",",
                "i1", "address_space(1)*", "%2"])
            l.append(["%4", "=", "zext", "i1", "%3", "to", ty])
            l.append(["%0", "=", "shl", ty, "%0", ",", "1"])
            l.append(["%0", "=", "or", ty, "%0", ",", "%4"])
            l.append(["%2", "=", "add",
                "i16", "address_space(1)*", "%2", ",", "1"])
        l.append([args[0], "=", ty, "%0"])
        self.add_il(l)
        self.pilfunc_FLAGS3(args)
        if c <= 8:
            self.pilfunc_PARITY(args)

    def pilfunc_LWPI(self, args):
        x = int(args[0], 0)
        self.add_il([ ["%WP", "=", "i16", args[0]] ])
        self.add_il(self.aliasregs())

class Tms9900(assy.Instree_disass):
    def __init__(self):
        super().__init__(
            "TMS 9900",
            ins_word=16,
            mem_word=8,
            endian=">",
            abits=16,
        )
        self.add_ins(tms9900_desc, Tms9900_ins)
        self.n_interrupt = 16
        self.il = True

    def vector(self, adr):
        return vector(self.m, adr, self)

    def vectors(self, adr=0x0, xops=1):
        def vect(a, lbl):
            c = vector(self.m, a, self)
            self.m.set_label(c.dstadr, lbl)
            return c

        vect(adr, "RESET")
        for i in range(1, self.n_interrupt):
            if self.m.bu16(i * 4) != 0:
                vect(i * 4, "INT%d" % i)
        for i in range(xops):
            vect(0x40 + i * 4, "XOP%d" % i)

    def dataptr(self, a):
        return data.Dataptr(self.m, a, a + 2, self.m.bu16(a))

class Tms9981(Tms9900):
    def __init__(self):
        super().__init__()
        self.n_interrupt = 5

if __name__ == "__main__":
    h = Tms9900()
    h.it.print()
