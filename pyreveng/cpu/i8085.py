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

'''Intel i8085

Page references to "8085 Instruction Set.pdf"
'''

from pyreveng import assy, data

i8085_desc = """
# pg2			|- - - - - - - -|- - - - - - - -|- - - - - - - -|
MOV	r1,r2		|0 1| ddd | sss | {
	RD = i8 RS
}
MOV	r1,(HL)		|0 1| ddd |1 1 0| {
	RD = load i8 , i8* %HL
}
MOV	(HL),r2		|0 1 1 1 0| sss | {
	store i8 RS , i8* %HL
}
MVI	r1,I		|0 0| ddd |1 1 0| imm		| {
	RD = i8 IMM
}
MVI	(HL),I		|0 0|1 1 0|1 1 0| imm		| {
	store i8 IMM , i8* %HL
}
# pg3			|- - - - - - - -|- - - - - - - -|- - - - - - - -|
LXI	rp,II		|0 0|rp |0 0 0 1| imml		| immh		| {
	RP1 = i8 IMMH
	RP2 = i8 IMML
}
LXI	SP,II		|0 0|1 1|0 0 0 1| imml		| immh		| {
	%SP = i16 IMM16
}
LDA	a		|0 0 1 1 1 0 1 0| lo		| hi		| {
	%A = load i8 , i8* ADR
}
STA	a		|0 0 1 1 0 0 1 0| lo		| hi		| {
	store i8 %A , i8* ADR
}
LHLD	a		|0 0 1 0 1 0 1 0| lo		| hi		| {
	%HL = load i16 , i16* ADR
}
SHLD	a		|0 0 1 0 0 0 1 0| lo		| hi		| {
	store i16 %HL , i16* ADR
}
LDAX	DE		|0 0|0 1|1 0 1 0| {
	%A = load i8 , i8* %DE
}
# Original Intel datasheet has typo: 0x2a
LDAX	BC		|0 0|0 0|1 0 1 0| {
	%A = load i8 , i8* %BC
}
# pg4			|- - - - - - - -|- - - - - - - -|- - - - - - - -|
PCHL	>J		|1 1 1 0 1 0 0 1| {
	br label %HL
}
PUSH	rp		|1 1|rp |0 1 0 1| {
	%SP = sub i16 %SP , 1
	store i8 RP1 , i8* %SP
	%SP = sub i16 %SP , 1
	store i8 RP2 , i8* %SP
}
PUSH	PSW		|1 1 1 1 0 1 0 1| {
	%SP = sub i16 %SP , 1
	store i8 %A , i8* %SP
	%SP = sub i16 %SP , 1
	store i8 %PSW , i8* %SP
}
POP	rp		|1 1|rp |0 0 0 1| {
	RP2 = load i8 , i8* %SP
	%SP = add i16 %SP , 1
	RP1 = load i8 , i8* %SP
	%SP = add i16 %SP , 1
}
# pg5			|- - - - - - - -|- - - - - - - -|- - - - - - - -|
STAX	BC		|0 0|0 0|0 0 1 0| {
	store i8 %A , i8* %BC
}
STAX	DE		|0 0|0 1|0 0 1 0| {
	store i8 %A , i8* %DE
}
XCHG	-		|1 1 1 0 1 0 1 1| {
	%0 = i8 %H
	%1 = i8 %H
	%H = i8 %D
	%L = i8 %E
	%D = i8 %0
	%E = i8 %1
}
ADD	r2		|1 0 0 0 0| sss | {
	%0 = add i8 %A , RS
	ZSP %0
	%F.cy = pyreveng.carry.add ( %A , RS )
	%F.ac = pyreveng.bcdcarry.add ( %A , RS )
	%A = i8 %0
}
ADD	(HL)		|1 0 0 0 0|1 1 0| {
	%1 = load i8 , i8* %HL
	%0 = add i8 %A , %1
	ZSP %0
	%F.cy = pyreveng.carry.add ( %A , %1 )
	%F.ac = pyreveng.bcdcarry.add ( %A , %1 )
	%A = i8 %0
}
ADI	I		|1 1 0 0 0 1 1 0| imm		| {
	%0 = add i8 %A , IMM
	ZSP %0
	%F.cy = pyreveng.carry.add ( %A , IMM )
	%F.ac = pyreveng.bcdcarry.add ( %A , IMM )
	%A = i8 %0
}
ADC	r2		|1 0 0 0 1| sss | {
	%1 = zext i1 %F.cy to i8
	%2 = add i8 %A , %1
	%0 = add i8 %2 , RS
	ZSP %0
	%F.cy = pyreveng.carry.add ( %A , %1, RS )
	%F.ac = pyreveng.bcdcarry.add ( %A , %1, RS )
	%A = i8 %0
}
# pg6			|- - - - - - - -|- - - - - - - -|- - - - - - - -|
ADC	(HL)		|1 0 0 0 1|1 1 0| {
	%3 = load i8 , i8* %HL
	%1 = zext i1 %F.cy to i8
	%2 = add i8 %A , %1
	%0 = add i8 %2 , %3
	ZSP %0
	%F.cy = pyreveng.carry.add ( %A , %1, %3 )
	%F.ac = pyreveng.bcdcarry.add ( %A , %1, %3 )
	%A = i8 %0
}
ACI	I		|1 1 0 0 1 1 1 0| imm		| {
	%1 = zext i1 %F.cy to i8
	%2 = add i8 %A , %1
	%0 = add i8 %2 , IMM
	ZSP %0
	%F.cy = pyreveng.carry.add ( %A , %1, IMM )
	%F.ac = pyreveng.bcdcarry.add ( %A , %1, IMM )
	%A = i8 %0
}
SUB	r2		|1 0 0 1 0| sss | {
	%0 = sub i8 %A , RS
	ZSP %0
	%F.cy = pyreveng.carry.sub ( %A , RS )
	%F.ac = pyreveng.bcdcarry.sub ( %A , RS )
	%A = i8 %0
}
SUB	(HL)		|1 0 0 1 0 1 1 0| {
	%1 = load i8 , i8* %HL
	%0 = sub i8 %A , %1
	ZSP %0
	%F.cy = pyreveng.carry.sub ( %A , %1 )
	%F.ac = pyreveng.bcdcarry.sub ( %A , %1 )
	%A = i8 %0
}
SUI	I		|1 1 0 1 0 1 1 0| imm		| {
	%0 = sub i8 %A , IMM
	ZSP %0
	%F.cy = pyreveng.carry.sub ( %A , IMM )
	%F.ac = pyreveng.bcdcarry.sub ( %A , IMM )
	%A = i8 %0
}
SBB	r2		|1 0 0 1 1| sss | {
	%1 = zext i1 %F.cy to i8
	%2 = sub i8 %A , %1
	%0 = sub i8 %2 , RS
	ZSP %0
	%F.cy = pyreveng.carry.sub ( %A , %1, RS )
	%F.ac = pyreveng.bcdcarry.sub ( %A , %1, RS )
	%A = i8 %0
}
# pg7			|- - - - - - - -|- - - - - - - -|- - - - - - - -|
SBB	(HL)		|1 0 0 1 1 1 1 0| {
	%3 = load i8 , i8* %HL
	%1 = zext i1 %F.cy to i8
	%2 = sub i8 %A , %1
	%0 = sub i8 %2 , %3
	ZSP %0
	%F.cy = pyreveng.carry.sub ( %A , %1, %3 )
	%F.ac = pyreveng.bcdcarry.sub ( %A , %1, %3 )
	%A = i8 %0
}
SBI	I		|1 1 0 1 1 1 1 0| imm		| {
	%1 = zext i1 %F.cy to i8
	%2 = sub i8 %A , %1
	%0 = sub i8 %2 , IMM
	ZSP %0
	%F.cy = pyreveng.carry.sub ( %A , %1, IMM )
	%F.ac = pyreveng.bcdcarry.sub ( %A , %1, IMM )
	%A = i8 %0
}
INR	r1		|0 0| ddd |1 0 0| {
	%0 = add i8 RD , 1
	ZSP %0
	%F.ac = pyreveng.bcdcarry.add ( RD , 1 )
	RD = i8 %0
}
INR	(HL)		|0 0 1 1 0 1 0 0| {
	%3 = load i8 , i8* %HL
	%0 = add i8 %3 , 1
	ZSP %0
	%F.ac = pyreveng.bcdcarry.add ( %3 , 1 )
	store i8 %0 , i8* %HL
}
DCR	r1		|0 0| ddd |1 0 1| {
	%0 = sub i8 RD , 1
	ZSP %0
	%F.ac = pyreveng.bcdcarry.sub ( RD , 1 )
	RD = i8 %0
}
DCR	(HL)		|0 0 1 1 0 1 0 1| {
	%3 = load i8 , i8* %HL
	%0 = sub i8 %3 , 1
	ZSP %0
	%F.ac = pyreveng.bcdcarry.sub ( %3 , 1 )
	store i8 %0 , i8* %HL
}
# pg8			|- - - - - - - -|- - - - - - - -|- - - - - - - -|
INX	rp		|0 0|rp |0 0 1 1| {
	RP = add i16 RP , 1
}
DCX	rp		|0 0|rp |1 0 1 1| {
	RP = sub i16 RP , 1
}
DAD	rp		|0 0|rp |1 0 0 1| {
	%0 = add i16 %HL , RP
	%F.cy = pyreveng.carry.sub ( %HL , RP )
	%HL = i16 %0
}
DAA	-		|0 0 1 0 0 1 1 1| {
	%A = pyreveng.void ( )
	%F = pyreveng.void ( )
}
ANA	r2		|1 0 1 0 0| sss	| {
	%A = and i8 %A , RS
	ZSP %A
	%F.cy = i1 0
	%F.ay = i1 1
}
# pg9			|- - - - - - - -|- - - - - - - -|- - - - - - - -|
ANA	(HL)		|1 0 1 0 0 1 1 0| {
	%3 = load i8 , i8* %HL
	%A = and i8 %A , %3
	ZSP %A
	%F.cy = i1 0
	%F.ay = i1 1
}
ANI	I		|1 1 1 0 0 1 1 0| imm		| {
	%A = and i8 %A , IMM
	ZSP %A
	%F.cy = i1 0
	%F.ay = i1 1
}
XRA	r2		|1 0 1 0 1| sss | {
	%A = and i8 %A , RS
	ZSP %A
	%F.cy = i1 0
	%F.ay = i1 0
}
XRA	(HL)		|1 0 1 0 1|1 1 0| {
	%3 = load i8 , i8* %HL
	%A = xor i8 %A , %3
	ZSP %A
	%F.cy = i1 0
	%F.ay = i1 0
}
XRI	I		|1 1 1 0 1 1 1 0| imm		| {
	%A = xor i8 %A , IMM
	ZSP %A
	%F.cy = i1 0
	%F.ay = i1 0
}
ORA	r2		|1 0 1 1 0| sss | {
	%A = or i8 %A , RS
	ZSP %A
	%F.cy = i1 0
	%F.ay = i1 0
}
# pg10			|- - - - - - - -|- - - - - - - -|- - - - - - - -|
ORA	(HL)		|1 0 1 1 0 1 1 0| {
	%3 = load i8 , i8* %HL
	%A = or i8 %A , %3
	ZSP %A
	%F.cy = i1 0
	%F.ay = i1 0
}
ORI	I		|1 1 1 1 0 1 1 0| imm		| {
	%A = or i8 %A , IMM
	ZSP %A
	%F.cy = i1 0
	%F.ay = i1 0
}
CMP	r2		|1 0 1 1 1| sss | {
	%0 = sub i8 %A , RS
	ZSP %0
	%F.cy = pyreveng.carry.sub ( %A , RS )
	%F.ac = pyreveng.bcdcarry.sub ( %3 , RS )
}
CMP	(HL)		|1 0 1 1 1|1 1 0| {
	%3 = load i8 , i8* %HL
	%0 = sub i8 %A , %3
	ZSP %0
	%F.cy = pyreveng.carry.sub ( %A , %3 )
	%F.ac = pyreveng.bcdcarry.sub ( %3 , %3 )
}
CPI	I		|1 1 1 1 1 1 1 0| imm		| {
	%0 = sub i8 %A , IMM
	ZSP %0
	%F.cy = pyreveng.carry.sub ( %A , IMM )
	%F.ac = pyreveng.bcdcarry.sub ( %3 , IMM )
}
RLC	-		|0 0 0 0 0 1 1 1| {
	%0 = lshr i8 %A , 7
	%F.cy = trunc i8 %0 to i1
	%1 = shl %A , 1
	%A = or i8 %1 , %0
}
# pg11			|- - - - - - - -|- - - - - - - -|- - - - - - - -|
RRC	-		|0 0 0 0 1 1 1 1| {
	%0 = and i8 %A , 1
	%F.cy = trunc i8 %0 to i1
	%1 = lshr i8 %A , 1
	%2 = shl %0 , 7
	%A = and i8 %1 , %2
}
RAL	-		|0 0 0 1 0 1 1 1| {
	%0 = lshr i8 %A , 7
	%1 = shl %A , 1
	%2 = zext i1 %F.cy to i8
	%A = or i8 %1 , %2
	%F.cy = trunc i8 %0 to i1
}
RAR	-		|0 0 0 1 1 1 1 1| {
	%0 = and i8 %A , 1
	%1 = lshr i8 %A , 1
	%2 = zext i1 %F.cy to i8
	%3 = shl %2 , 7
	%A = or i8 %1 , %3
	%F.cy = trunc i8 %0 to i1
}
CMA	-		|0 0 1 0 1 1 1 1| {
	%A = xor i8 %A , 0xff
}
CMC	-		|0 0 1 1 1 1 1 1| {
	%F.cy = xor i1 %F.cy , 1
}
STC	-		|0 0 1 1 0 1 1 1| {
	%F.cy = i1 1
}
# pg12			|- - - - - - - -|- - - - - - - -|- - - - - - - -|
JMP	a,>J		|1 1 0 0 0 0 1 1| lo		| hi		| {
	br label ADR
}
J	cc,a,>JC	|1 1| cc  |0 1 0| lo		| hi		| {
	JCC ADR
}
CALL	a,>C		|1 1 0 0 1 1 0 1| lo		| hi		| {
	%SP = sub i16 %SP , 2
	store i16 HI , i16* %SP
	br label ADR
}
# pg13			|- - - - - - - -|- - - - - - - -|- - - - - - - -|
C	cc,a,>CC	|1 1| cc  |1 0 0| lo		| hi		| {
	JNCC HI
	%SP = sub i16 %SP , 2
	store i16 HI , i16* %SP
	br label ADR
}
RET	>R		|1 1 0 0 1 0 0 1| {
	%0 = load i16 , i16* %SP
	%SP = sub i16 %SP , 2
	br label %0
}
R	cc,>RC		|1 1| cc  |0 0 0| {
	JNCC HI
	%0 = load i16 , i16* %SP
	%SP = sub i16 %SP , 2
	br label %0
}
RST	n,>J		|1 1| n	  |1 1 1| {
	%SP = sub i16 %SP , 2
	store i16 HI , i16* %SP
	br label NADR
}
# pg14			|- - - - - - - -|- - - - - - - -|- - - - - - - -|
POP	PSW		|1 1 1 1 0 0 0 1| {
	%F = load i8 , i8* %SP
	%SP = add i16 %SP , 1
	%A = load i8 , i8* %SP
	%SP = add i16 %SP , 1
}
XTHL	-		|1 1 1 0 0 0 1 1| {
	%0 = load i16 , i16* %SP
	store i16 %HL , i16* %SP
	%HL = i16 %0
}
SPHL	-		|1 1 1 1 1 0 0 1| {
	%SP = i16 %HL
}
IN	p		|1 1 0 1 1 0 1 1| p		| {
	%A = i8085.in ( PORT )
}
OUT	p		|1 1 0 1 0 0 1 1| p		| {
	i8085.out ( PORT , %A )
}
# pg15			|- - - - - - - -|- - - - - - - -|- - - - - - - -|
EI	-		|1 1 1 1 1 0 1 1| {
	i8085.ei ( )
}
DI	-		|1 1 1 1 0 0 1 1| {
	i8085.di ( )
}
HLT	-		|0 1 1 1 0 1 1 0| {
	i8085.hlt ( )
}
NOP	-		|0 0 0 0 0 0 0 0| {
	%0 = i1 0
}
RIM	-		|0 0 1 0 0 0 0 0| {
	%A = i8 i8085.rim ( )
}
# pg16			|- - - - - - - -|- - - - - - - -|- - - - - - - -|
SIM	-		|0 0 1 1 0 0 0 0| {
	i8085.sim ( %A )
}

"""

class i8085_ins(assy.Instree_ins):
    def __init__(self, lim, lang):
        super().__init__(lim, lang)
        self.seg = ""

    def assy_r2(self):
        r = self['sss']
        if r == 6:
            raise assy.Invalid('0x%x rs=6' % self.lo)
        return "BCDEHL-A"[r]

    def assy_r1(self):
        r = self['ddd']
        if r == 6:
            raise assy.Invalid('0x%x rd=6' % self.lo)
        return "BCDEHL-A"[r]

    def assy_cc(self):
        self.cc = (
            'nz', 'z', 'nc', 'c', 'po', 'pe', 'p', 'm')[self['cc']]
        self.mne += self.cc

    def assy_rp(self):
        rp = self['rp']
        if rp == 3:
            raise assy.Invalid('0x%x RP=3' % self.lo)
        return ('BC', 'DE', 'HL')[rp]

    def assy_II(self):
        return "#0x%02x%02x" % (self['immh'], self['imml'])

    def assy_n(self):
        self.dstadr = 8 * self['n']
        return "#%d" % self['n']
        # return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_I(self):
        return "#0x%02x" % self['imm']

    def assy_a(self):
        self.dstadr = self['hi'] << 8 | self['lo']
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def pilmacro_RD(self):
        return "%%%s" % "BCDEHL-A"[self['ddd']]

    def pilmacro_RS(self):
        return "%%%s" % "BCDEHL-A"[self['sss']]

    def pilmacro_IMM(self):
        return "#0x%02x" % self['imm']

    def pilmacro_IMMH(self):
        return "#0x%02x" % self['immh']

    def pilmacro_IMML(self):
        return "#0x%02x" % self['imml']

    def pilmacro_IMM16(self):
        return "#0x%02x%02x" % (self['immh'], self['imml'])

    def pilmacro_ADR(self):
        return "0x%02x%02x" % (self['hi'], self['lo'])

    def pilmacro_PORT(self):
        return "0x%02x" % self['p']

    def pilmacro_NADR(self):
        return "0x%02x" % (self['n'] << 3)

    def pilmacro_RP(self):
        return "%%%s" % ["BC", "DE", "HL", "SP"][self['rp']]

    def pilmacro_RP1(self):
        return "%%%s" % "BDH"[self['rp']]

    def pilmacro_RP2(self):
        return "%%%s" % "CEL"[self['rp']]

    def pilmacro_HI(self):
        return "0x%x" % self.hi

    def pilfunc_ZSP(self, arg):
        self.add_il([
            [ "%F.z", "=", "icmp", "eq", "i8", arg[0], ",", "0" ],
            [ "%F.s", "=", "icmp", "gt", "i8", arg[0], ",", "0x7f" ],
            [ "%F.p", "=", "pyreveng.parity.odd.i1", "(", arg[0], ")" ],
        ])

    def pilfunc_JCC(self, arg):
        i = self['cc']
        b = ["%F.z", "%F.cy", "%F.p", "%F.s"][i >> 1]
        if i & 1:
            a1 = arg[0]
            a2 = "0x%x" % self.hi
        else:
            a1 = "0x%x" % self.hi
            a2 = arg[0]
        self.add_il([
            ["br", "i1", b, "label", a1, ",", "label", a2 ],
        ])

    def pilfunc_JNCC(self, arg):
        i = self['cc']
        b = ["%F.z", "%F.cy", "%F.p", "%F.s"][i >> 1]
        if i & 1:
            a1 = arg[0]
            a2 = "0x%x" % self.hi
        else:
            a1 = "0x%x" % self.hi
            a2 = arg[0]
        self.add_il([
            ["br", "i1", b, "label", a2, ",", "label", a1 ],
        ])


class i8085(assy.Instree_disass):
    def __init__(self):
        super().__init__(
            "i8085",
            ins_word=8,
            abits=16,
        )
        self.add_ins(i8085_desc, i8085_ins)
        self.verbatim += (
            "(HL)",
            "BC",
            "DE",
            "SP",
            "PSW",
        )

    def vectors(self):
        for l,a in (
            ("RESET",  0x0000),
            ("TRAP",   0x0024),
            ("RST1",   0x0008),
            ("RST2",   0x0010),
            ("RST3",   0x0018),
            ("RST4",   0x0020),
            ("RST5",   0x0028),
            ("RST5.5", 0x002c),
            ("RST6",   0x0030),
            ("RST6.5", 0x0034),
            ("RST7",   0x0038),
            ("RST7.5", 0x003c),
        ):
            self.disass(a)
            self.m.set_label(a, l)

    def codeptr(self, adr):
        t = self.m.lu16(adr)
        c = data.Codeptr(self.m, adr, adr + 2, t)
        self.disass(t)
        return c
