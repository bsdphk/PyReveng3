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

'''Intel MCS-51 - 8032/51
'''

from pyreveng import mem, assy

MCS51_DESC = """

#			|. . . . . . . .|. . . . . . . .|
ACALL	a11,>C		| ahi |1 0 0 0 1| alo		| {
	%S = sub i8 %S , 2
	store i16 HI , i16* %S
	br label DST
}

ADD	A,Rn		|0 0 1 0 1| rn  |
ADD	A,adir		|0 0 1 0 0 1 0 1| adir		|
ADD	A,iri		|0 0 1 0 0 1 1|i|
ADD	A,data		|0 0 1 0 0 1 0 0| data		|

ADDC	A,Rn		|0 0 1 1 1| rn  |
ADDC	A,adir		|0 0 1 1 0 1 0 1| adir		|
ADDC	A,iri		|0 0 1 1 0 1 1|i|
ADDC	A,data		|0 0 1 1 0 1 0 0| data		|

AJMP	a11,>J		| ahi |0 0 0 0 1| alo		|

ANL	A,Rn		|0 1 0 1 1| rn  |
ANL	A,adir		|0 1 0 1 0 1 0 1| adir		|
ANL	A,iri		|0 1 0 1 0 1 1|i|
ANL	A,data		|0 1 0 1 0 1 0 0| data		|

ANL	adir,A		|0 1 0 1 0 0 1 0| adir		|
ANL	adir,data	|0 1 0 1 0 0 1 1| adir		| data		|
ANL	C,abit		|1 0 0 0 0 0 1 0| abit		|
ANL	C,nabit		|1 0 1 1 0 0 0 0| abit		|

CJNE	A,adir,arel,>JC	|1 0 1 1 0 1 0 1| adir		| arel		|
CJNE	A,data,arel,>JC	|1 0 1 1 0 1 0 0| data		| arel		|
CJNE	Rn,data,arel,>JC	|1 0 1 1 1| rn	| data		| arel		|
CJNE	iri,data,arel,>JC	|1 0 1 1 0 1 1|i| data		| arel		|

CLR	A		|1 1 1 0 0 1 0 0| {
	%A = i8 0x00
}
CLR	C		|1 1 0 0 0 0 1 1| {
	%C = i1 0
}
CLR	abit		|1 1 0 0 0 0 1 0| abit		| {
	store i1 0 , i1* ABIT
}

CPL	A		|1 1 1 1 0 1 0 0|
CPL	C		|1 0 1 1 0 0 1 1|
CPL	abit		|1 0 1 1 0 0 1 0| abit		|

DA	A		|1 1 0 1 0 1 0 0|

DEC	A		|0 0 0 1 0 1 0 0|
DEC	Rn		|0 0 0 1 1| rn  |
DEC	adir		|0 0 0 1 0 1 0 1| adir		|
DEC	iri		|0 0 0 1 0 1 1|i|

DIV	AB		|1 0 0 0 0 1 0 0|

DJNZ	Rn,arel,>C	|1 1 0 1 1| rn	| arel		|
DJNZ	adir,arel,>C	|1 1 0 1 0 1 0 1| adir		| arel		|

INC	A		|0 0 0 0 0 1 0 0|
INC	Rn		|0 0 0 0 1| rn	|
INC	adir		|0 0 0 0 0 1 0 1| adir		|
INC	iri		|0 0 0 0 0 1 1|i|
INC	DPTR		|1 0 1 0 0 0 1 1|

JB	abit,arel,>JC	|0 0 1 0 0 0 0 0| abit		| arel		|
JBC	abit,arel,>JC	|0 0 0 1 0 0 0 0| abit		| arel		|

JC	arel,>JC	|0 1 0 0 0 0 0 0| arel		|

JMP	@A+DPTR		|0 1 1 1 0 0 1 1|

JNB	abit,arel,>JC	|0 0 1 1 0 0 0 0| abit		| arel		|

JNC	arel,>JC	|0 1 0 1 0 0 0 0| arel		|

JNZ	arel,>JC	|0 1 1 1 0 0 0 0| arel		|

JZ	arel,>JC	|0 1 1 0 0 0 0 0| arel		|

LCALL	a16,>C		|0 0 0 1 0 0 1 0| ahi		| alo		|

LJMP	a16,>J		|0 0 0 0 0 0 1 0| ahi		| alo		|

MOV	A,Rn		|1 1 1 0 1| rn	| {
	%A = i8 RN
}
MOV	A,adir		|1 1 1 0 0 1 0 1| adir		| {
	%A = load i8 , i8* ADIR
}
MOV	A,iri		|1 1 1 0 0 1 1|i| {
	%A = load i8 , i8* RI
}
MOV	A,data		|0 1 1 1 0 1 0 0| data		| {
	%A = i8 DATA
}
MOV	Rn,A		|1 1 1 1 1| rn	| {
	RN = i8 %A
}
MOV	Rn,adir		|1 0 1 0 1| rn	| adir		| {
	RN = load i8 , i8* ADIR
}
MOV	Rn,data	|0 1 1 1 1| rn	| data		| {
	RN = i8 DATA
}
MOV	adir,A		|1 1 1 1 0 1 0 1| adir		| {
	store i8 %A , i8* ADIR
}
MOV	adir,Rn		|1 0 0 0 1| rn	| adir		| {
	store i8 RN , i8* ADIR
}
MOV	adir2,adir	|1 0 0 0 0 1 0 1| adir		| adir2		| {
	%0 = load i8 , i8* ADIR
	store i8 %0 , i8* ADIR2
}
MOV	adir,iri	|1 0 0 0 0 1 1|i| adir		|
MOV	adir,data	|0 1 1 1 0 1 0 1| adir		| data		|
MOV	iri,A		|1 1 1 1 0 1 1|i|
MOV	iri,adir	|1 0 1 0 0 1 1|i| adir		|
MOV	iri,data	|0 1 1 1 0 1 1|i| data		|

MOV	C,abit		|1 0 1 0 0 0 1 0| abit		|
MOV	abit,C		|1 0 0 1 0 0 1 0| abit		|

MOV	DPTR,data16	|1 0 0 1 0 0 0 0| dhi		| dlo		|

MOVC	A,@A+DPTR	|1 0 0 1 0 0 1 1|
MOVC	A,@A+PC		|1 0 0 0 0 0 1 1|

MOVX	A,iri		|1 1 1 0 0 0 1|i|
MOVX	A,@DPTR		|1 1 1 0 0 0 0 0|
MOVX	iri,A		|1 1 1 1 0 0 1|i|
MOVX	@DPTR,A		|1 1 1 1 0 0 0 0|

MUL	AB		|1 0 1 0 0 1 0 0|

NOP	-		|0 0 0 0 0 0 0 0|

ORL	A,Rn		|0 1 0 0 1| rn	|
ORL	A,adir		|0 1 0 0 0 1 0 1| adir		|
ORL	A,iri		|0 1 0 0 0 1 1|i|
ORL	A,data		|0 1 0 0 0 1 0 0| data		|
ORL	adir,A		|0 1 0 0 0 0 1 0| adir		|
ORL	adir,data	|0 1 0 0 0 0 1 1| adir		| data		|
ORL	C,abit		|0 1 1 1 0 0 1 0| abit		|
ORL	C,/abit		|1 0 1 0 0 0 0 0| abit		|

POP	adir		|1 1 0 1 0 0 0 0| adir		|
PUSH	adir		|1 1 0 0 0 0 0 0| adir		|

RET	>R		|0 0 1 0 0 0 1 0|

RETI	>R		|0 0 1 1 0 0 1 0|

RL	A		|0 0 1 0 0 0 1 1|
RLC	A		|0 0 1 1 0 0 1 1|
RR	A		|0 0 0 0 0 0 1 1|
RRC	A		|0 0 0 1 0 0 1 1|

SETB	C		|1 1 0 1 0 0 1 1|
SETB	abit		|1 1 0 1 0 0 1 0| abit		|

SJMP	arel,>J		|1 0 0 0 0 0 0 0| arel		|

SUBB	A,Rn		|1 0 0 1 1| rn  |
SUBB	A,adir		|1 0 0 1 0 1 0 1| adir		|
SUBB	A,iri		|1 0 0 1 0 1 1|i|
SUBB	A,data		|1 0 0 1 0 1 0 0| data		|

SWAP	A		|1 1 0 0 0 1 0 0|
XCH	A,Rn		|1 1 0 0 1| rn  |
XCH	A,adir		|1 1 0 0 0 1 0 1| adir		|
XCH	A,iri		|1 1 0 0 0 1 1|i|
XCHD	A,iri		|1 1 0 1 0 1 1|i|

XRL	A,Rn		|0 1 1 0 1| rn	|
XRL	A,adir		|0 1 1 0 0 1 0 1| adir		|
XRL	A,iri		|0 1 1 0 0 1 1|i|
XRL	A,data		|0 1 1 0 0 1 0 0| data		|
XRL	adir,A		|0 1 1 0 0 0 1 0| adir		|
XRL	adir,data	|0 1 1 0 0 0 1 1| adir		| data		|

"""

class MCS51_Ins(assy.Instree_ins):

    def assy_adir(self):
        self.dstadr = self['adir']
        return assy.Arg_dst(self.lang.as_data, self.dstadr)

    def assy_adir2(self):
        self.dstadr = self['adir2']
        return assy.Arg_dst(self.lang.as_data, self.dstadr)

    def assy_a11(self):
        a = (self['ahi'] << 8) | self['alo']
        self.dstadr = (self.hi & 0xf800) + a
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_a16(self):
        self.dstadr = (self['ahi'] << 8) | self['alo']
        self.dstadr &= self.lang.amask
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_arel(self):
        a = self['arel']
        if a & 0x80:
            a -= 256
        self.dstadr = self.hi + a
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_iri(self):
        return "@R%d" % self['i']

    def assy_Rn(self):
        return "R%d" % self['rn']

    def assy_data(self):
        return "#0x%02x" % self['data']

    def assy_data16(self):
        v = (self['dhi'] << 8) | self['dlo']
        return "#0x%04x" % v

    def assy_abit(self):
        b = self['abit']
        return assy.Arg_dst(self.lang.as_bit, b)

    def assy_nabit(self):
        return "/" + self.assy_abit(pj)

    def pilmacro_ABIT(self):
        b = self['abit']
        if b < 0x80:
            return "%0x02.%d" % (0x20 + (b >> 3), b & 7)
        return "b#%0x2x" % b

    def pilmacro_ADIR(self):
        return "0x%02x" % self['adir']

    def pilmacro_ADIR2(self):
        return "0x%02x" % self['adir2']

    def pilmacro_DATA(self):
        return "0x%02x" % self['data']

    def pilmacro_DST(self):
        return "0x%04x" % self.dstadr

    def pilmacro_HI(self):
        return "0x%04x" % self.hi

    def pilmacro_RI(self):
        return "%%R%d" % self['i']

    def pilmacro_RN(self):
        return "%%R%d" % self['rn']

class BitSpace(mem.AddressSpace):

    def __init__(self, lo, hi, name, dspace):
        super().__init__(lo, hi, name)
        self.dspace = dspace

    def adr(self, dst):
        lbls = self.labels.get(dst)
        if lbls:
            return lbls[0]
        adr = dst & ~7
        bit = dst & 7
        if adr < 0x80:
            adr = 0x20 + (adr >> 3)
        lbls = self.dspace.get_labels(adr)
        if lbls:
            return lbls[0] + ".%d" % bit
        return "0x%02x.%d" % (adr, bit)


class MCS51(assy.Instree_disass):
    def __init__(self, lang="mcs51"):
        super().__init__(
            lang,
            ins_word=8,
            abits=16,
        )
        self.add_as("data", "RAM+I/O", 8)
        self.add_as("bit", aspace=BitSpace(0x00, 0x100, "BITSPACE", self.as_data))

        self.it.load_string(MCS51_DESC, MCS51_Ins)
        self.amask = 0xffff
        self.verbatim |= set(("A", "AB", "C", "DPTR", "@A+DPTR", "@A+PC"))
        self.define_bits(
            0x80,
            "P0",
            ["AD0", "AD1", "AD2", "AD3", "AD4", "AD5", "AD6", "AD7"]
        )
        self.define_bits(0x81, "SP")
        self.define_bits(0x82, "DPL")
        self.define_bits(0x83, "DPH")
        self.define_bits(0x87, "PCON")
        self.define_bits(
            0x88,
            "TCON",
            ["IT0", "IE0", "IT1", "IE1", "TR0", "TF0", "TR1", "TF1"]
        )
        self.define_bits(0x89, "TMOD")
        self.define_bits(0x8a, "TL0")
        self.define_bits(0x8b, "TL1")
        self.define_bits(0x8c, "TH0")
        self.define_bits(0x8d, "TH1")
        self.define_bits(0x90, "P1")
        self.define_bits(
            0x98,
            "SCON",
            ["RI", "TI", "RB8", "TB8", "REN", "SM2", "SM1", "SM0"]
        )
        self.define_bits(0x99, "SBUF")
        self.define_bits(
            0xa0,
            "P2",
            ["A8", "A9", "A10", "A11", "A12", "A13", "A14", "A15"]
        )
        self.define_bits(
            0xa8,
            "IE",
            ["EX0", "ET0", "EX1", "ET1", "ES", "5", "6", "EA"]
        )
        self.define_bits(
            0xb0,
            "P3",
            ["Rxd", "Txd", "_INT0", "_INT1", "T0", "T1", "_WR", "_RD"]
        )
        self.define_bits(0xb8, "IP", ["PX0", "PT0", "PX1", "PT1", "PS"])
        self.define_bits(
            0xd0,
            "PSW",
            ["P", "1", "OV", "RS0", "RS1", "F0", "AC", "CY"]
        )
        self.define_bits(0xe0, "ACC")
        self.define_bits(0xf0, "B")

    def define_bits(self, a, n, b=None):
        self.as_data.set_label(a, n)
        if b and not a & 7:
            for i in b:
                self.as_bit.set_label(a, n + "." + i)
                a += 1

    def set_adr_mask(self, a):
        self.amask = a

    def vectors(self, which=None):
        for a, b in (
                (0x000, "RESET"),
                (0x003, "IE0"),
                (0x00b, "TF0"),
                (0x013, "IE1"),
                (0x01b, "TF1"),
                (0x023, "RI_TI"),
        ):
            if not which or a in which or b in which:
                self.disass(self.m, a)
                self.m.set_label(a, b)

class I8032(MCS51):
    def __init__(self):
        super().__init__("i8032")

        self.define_bits(
            0xc8,
            "T2CON",
            ["CP_RL2", "C_T2", "TR2", "EXEN2", "TCLK", "RCLK", "EXF2", "TF2"],
        )
        self.define_bits(0xc9, "T2MOD")
        self.define_bits(0xca, "RCAP2L")
        self.define_bits(0xcb, "RCAP2H")
        self.define_bits(0xcc, "TL2")
        self.define_bits(0xcd, "TH2")
        self.define_bits(0xd8, "WDTCON")
