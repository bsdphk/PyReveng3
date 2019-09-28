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

'''MOS Technology 6500 Family
'''

from pyreveng import assy, data, mem

mos6500_desc = '''
ADC	Imm	| 69		|
ADC	Pz	| 65		|
ADC	Pzx	| 75		|
ADC	Abs	| 6D		|
ADC	Absx	| 7D		|
ADC	Absy	| 79		|
ADC	Indx	| 61		|
ADC	Indy	| 71		|
AND	Imm	| 29		|
AND	Pz	| 25		|
AND	Pzx	| 35		|
AND	Abs	| 2D		|
AND	Absx	| 3D		|
AND	Absy	| 39		|
AND	Indx	| 21		|
AND	Indy	| 31		|
ASL	A	| 0A		|
ASL	Pz	| 06		|
ASL	Pzx	| 16		|
ASL	Abs	| 0E		|
ASL	Absx	| 1E		|
BCC	Rel,>JC	| 90		|
BCS	Rel,>JC	| B0		|
BEQ	Rel,>JC	| F0		|
BIT	Pz	| 24		|
BIT	Abs	| 2C		|
BMI	Rel,>JC	| 30		|
BNE	Rel,>JC	| D0		|
BPL	Rel,>JC	| 10		|
BRK	-	| 00		|
BVC	Rel,>JC	| 50		|
BVS	Rel,>JC	| 70		|
CLC	-	| 18		|
CLD	-	| D8		|
CLI	-	| 58		|
CLV	-	| B8		|
CMP	Imm	| C9		|
CMP	Pz	| C5		|
CMP	Pzx	| D5		|
CMP	Abs	| CD		|
CMP	Absx	| DD		|
CMP	Absy	| D9		|
CMP	Indx	| C1		|
CMP	Indy	| D1		|
CPX	Imm	| E0		|
CPX	Pz	| E4		|
CPX	Abs	| EC		|
CPY	Imm	| C0		|
CPY	Pz	| C4		|
CPY	Abs	| CC		|
DEC	Pz	| C6		|
DEC	Pzx	| D6		|
DEC	Abs	| CE		|
DEC	Absx	| DE		|
DEX	-	| CA		|
DEY	-	| 88		|
EOR	Imm	| 49		|
EOR	Pz	| 45		|
EOR	Pzx	| 55		|
EOR	Abs	| 4D		|
EOR	Absx	| 5D		|
EOR	Absy	| 59		|
EOR	Indx	| 41		|
EOR	Indy	| 51		|
INC	Pz	| E6		|
INC	Pzx	| F6		|
INC	Abs	| EE		|
INC	Absx	| FE		|
INX	-	| E8		|
INY	-	| C8		|
JMP	Abs,>J	| 4C		|
JMP	Ind,>J	| 6C		|
JSR	Abs,>C	| 20		|
LDA	Imm	| A9		|
LDA	Pz	| A5		|
LDA	Pzx	| B5		|
LDA	Abs	| AD		|
LDA	Absx	| BD		|
LDA	Absy	| B9		|
LDA	Indx	| A1		|
LDA	Indy	| B1		|
LDX	Imm	| A2		|
LDX	Pz	| A6		|
LDX	Pzy	| B6		|
LDX	Abs	| AE		|
LDX	Absx	| BE		|
LDY	Imm	| A0		|
LDY	Pz	| A4		|
LDY	Pzx	| B4		|
LDY	Abs	| AC		|
LDY	Absx	| BC		|
LSR	A	| 4A		|
LSR	Pz	| 46		|
LSR	Pzx	| 56		|
LSR	Abs	| 4E		|
LSR	Absx	| 5E		|
NOP	-	| EA		|
ORA	Imm	| 09		|
ORA	Pz	| 05		|
ORA	Pzx	| 15		|
ORA	Abs	| 0D		|
ORA	Absx	| 1D		|
ORA	Absy	| 19		|
ORA	Indx	| 01		|
ORA	Indy	| 11		|
PHA	-	| 48		|
PHP	-	| 08		|
PLA	-	| 68		|
PLP	-	| 28		|
ROL	A	| 2A		|
ROL	Pz	| 26		|
ROL	Pzx	| 36		|
ROL	Abs	| 2E		|
ROL	Absx	| 3E		|
ROR	A	| 6A		|
ROR	Pz	| 66		|
ROR	Pzx	| 76		|
ROR	Abs	| 6E		|
ROR	Absx	| 7E		|
RTI	-,>R	| 40		|
RTS	-,>R	| 60		|
SBC	Imm	| E9		|
SBC	Pz	| E5		|
SBC	Pzx	| F5		|
SBC	Abs	| ED		|
SBC	Absx	| FD		|
SBC	Absy	| F9		|
SBC	Indx	| E1		|
SBC	Indy	| F1		|
SEC	-	| 38		|
SED	-	| F8		|
SEI	-	| 78		|
STA	Pz	| 85		|
STA	Pzx	| 95		|
STA	Abs	| 8D		|
STA	Absx	| 9D		|
STA	Absy	| 99		|
STA	Indx	| 81		|
STA	Indy	| 91		|
STX	Pz	| 86		|
STX	Pzy	| 96		|
STX	Abs	| 8E		|
STY	Pz	| 84		|
STY	Pzx	| 94		|
STY	Abs	| 8C		|
TAX	-	| AA		|
TAY	-	| A8		|
TSX	-	| BA		|
TXA	-	| 8A		|
TXS	-	| 9A		|
TYA	-	| 98		|
'''

class mos6500_ins(assy.Instree_ins):

    def assy_A(self, pj):
        return "A"

    def assy_Abs(self, pj):
        self.dstadr = pj.m.lu16(self.hi)
        self.hi += 2   
        return assy.Arg_dst(pj.m, self.dstadr)

    def assy_Absx(self, pj):
        d = pj.m.lu16(self.hi)
        self.hi += 2   
        return [
            assy.Arg_dst(pj.m, d),
            assy.Arg_verbatim("X"),
        ]

    def assy_Absy(self, pj):
        d = pj.m.lu16(self.hi)
        self.hi += 2   
        return [
            assy.Arg_dst(pj.m, d),
            assy.Arg_verbatim("Y"),
        ]

    def assy_Ind(self, pj):
        d = pj.m.lu16(self.hi)
        self.hi += 2   
        return "(0x%04x)" % d

    def assy_Indx(self, pj):
        d = pj.m[self.hi]
        self.hi += 1
        return [
            assy.Arg_dst(pj.m, d),
            assy.Arg_verbatim("X"),
        ]

    def assy_Indy(self, pj):
        d = pj.m[self.hi]
        self.hi += 1   
        return [
            assy.Arg_dst(pj.m, d),
            assy.Arg_verbatim("Y"),
        ]

    def assy_Imm(self, pj):
        v = pj.m[self.hi]
        self.hi += 1
        return "#0x%02x" % v

    def assy_Pz(self, pj):
        self.dstadr = pj.m[self.hi]
        self.hi += 1   
        return assy.Arg_dst(pj.m, self.dstadr)

    def assy_Pzx(self, pj):
        d = pj.m[self.hi]
        self.hi += 1   
        return [
            assy.Arg_dst(pj.m, d),
            assy.Arg_verbatim("X"),
        ]

    def assy_Rel(self, pj):
        v = pj.m.s8(self.hi)
        self.hi += 1
        self.dstadr = self.hi + v
        return assy.Arg_dst(pj.m, self.dstadr)
  

class mos6500(assy.Instree_disass):
    def __init__(self):
        super().__init__(
            "mos6500",
            ins_word=8,
            abits=16,
        )
        self.add_ins(mos6500_desc, mos6500_ins)

    def codeptr(self, pj, adr):
        t = pj.m.lu16(adr)
        c = data.Codeptr(pj.m, adr, adr + 2, t)
        self.disass(pj, t)
        return c

    def vectors(self, pj):
        y = self.codeptr(pj, 0xfffe)
        pj.m.set_label(y.dst, "IRQ")
        y = self.codeptr(pj, 0xfffc)
        pj.m.set_label(y.dst, "RESET")
