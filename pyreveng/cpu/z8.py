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

'''Zilog Z8
'''

from pyreveng import mem, assy

Z8_DESC = '''
ADC	dst_src			|0 0 0 1| x	| y		|
ADD	dst_src			|0 0 0 0| x	| y		|
AND	dst_src			|0 1 0 1| x	| y		|
CALL	DA,>C			|1 1 0 1|0 1 1 0| da_h		| da_l		|
CALL	IRR			|1 1 0 1|0 1 0 0| RR		|
CFF	-			|1 1 1 0|1 1 1 1|
CLR	iR			|1 0 1 1|0 0 0|i| R		|
COM	iR			|0 1 1 0|0 0 0|i| R		|
CP	dst_src			|1 0 1 0| x	| y		|
DA	iR			|0 1 0 0|0 0 0|i| R		|
DEC	iR			|0 0 0 0|0 0 0|i| R		|
DECW	iRR			|1 0 0 0|0 0 0|i| RR		|
DI	-			|1 0 0 0|1 1 1 1|
DJNZ	r,RA,>JC		| r	|1 0 1 0| ra		|
EI	-			|1 0 0 1|1 1 1 1|
INC	r			| r	|1 1 1 0|
INC	iR			|0 0 1 0|0 0 0|i| R		|
INCW	iRR			|1 0 1 0|0 0 0|i| RR		|
IRET	>R			|1 0 1 1|1 1 1 1|
JP	cc,DA,>JC		| cc	|1 1 0 1| da_h		| da_l		|
JP	DA,>J			|1 0 0 0|1 1 0 1| da_h		| da_l		|
JP	IRR			|0 0 1 1|0 0 0 0| RR		|
JR	cc,RA,>JC		| cc	|1 0 1 1| ra		|
JR	RA,>JC			|1 0 0 0|1 0 1 1| ra		|
LD	r,Im			| r	|1 1 0 0| IM		|
LD	r,R			| r	|1 0 0 0| R		|
LD	R,r			| r	|1 0 0 1| R		|
LD	r,Ir			|1 1 1 0|0 0 1 1| r	| Ir	|
LD	Ir,r			|1 1 1 1|0 0 1 1| Ir	| r	|
LD	R,R2			|1 1 1 0|0 1 0 0| R2		| R		|
LD	R,IR			|1 1 1 0|0 1 0 1| IR		| R		|
LD	iR,Im			|1 1 1 0|0 1 1|i| R		| IM		|
LD	IR,R			|1 1 1 1|0 1 0 1| R		| IR		|
LD	r,X			|1 1 0 0|0 1 1 1| r	| X	| src		|
LD	X,r			|1 1 0 1|0 1 1 1| r	| X	| dst		|
LDC	rIrr			|1 1 0|d|0 0 1 0| r	| Irr	|
LDCI	rIrr			|1 1 0|d|0 0 1 1| r	| Irr	|
LDE	rIrr			|1 0 0|d|0 0 1 0| r	| Irr	|
LDEI	rIrr			|1 0 0|d|0 0 1 1| r	| Irr	|
NOP	-			|1 1 1 1|1 1 1 1|
OR	dst_src			|0 1 0 0| x	| y		|
POP	R			|0 1 0 1|0 0 0|i| R		|
PUSH	R			|0 1 1 1|0 0 0|i| R		|
RCF	-			|1 1 0 0|1 1 1 1|
RET	>R			|1 0 1 0|1 1 1 1|
RL	iR			|1 0 0 1|0 0 0|i| R		|
RLC	iR			|0 0 0 1|0 0 0|i| R		|
RR	iR			|1 1 1 0|0 0 0|i| R		|
RRC	iR			|1 1 0 0|0 0 0|i| R		|
SBC	dst_src			|0 0 1 1| x	| y		|
SCF	-			|1 1 0 1|1 1 1 1|
SRA	iR			|1 1 0 1|0 0 0|i| R		|
SRP	Im			|0 0 1 1|0 0 0 1| IM		|
SUB	dst_src			|0 0 1 0| x	| y		|
SWAP	iR			|1 1 1 1|0 0 0|i| R		|
TCM	dst_src			|0 1 1 0| x	| y		|
TM	dst_src			|0 1 1 1| x	| y		|
XOR	dst_src			|1 0 1 1| x	| y		|
'''

Z8_REGISTERS = {
    0x00: "P0",
    0x01: "P1",
    0x02: "P2",
    0x03: "P3",
    0xf0: "SIO",
    0xf1: "TMR",
    0xf2: "T1",
    0xf3: "PRE1",
    0xf4: "T0",
    0xf5: "PRE0",
    0xf6: "P2M",
    0xf7: "P3M",
    0xf8: "P01M",
    0xf9: "IPR",
    0xfa: "IRQ",
    0xfb: "IMR",
    0xfc: "FLAGS",
    0xfd: "RP",
    0xfe: "SPH",
    0xff: "SPL",
}

class Z8Ins(assy.Instree_ins):

    def __init__(self, *args, **kwargs):
        #print("II", *args, **kwargs)
        super().__init__(*args, **kwargs)

    def assy_cc(self):
        self.cc = {
            0: False,
            1: "LT",
            2: "LE",
            3: "ULE",
            4: "OV",
            5: "MI",
            6: "Z",
            7: "C",
            8: True,
            9: "GE",
            10: "GT",
            11: "UGT",
            12: "NOV",
            13: "PL",
            14: "NZ",
            15: "NC",
        }[self['cc']]
        return str(self.cc)

    def assy_r(self):
        return 'R%d' % self['r']

    def assy_R(self, r = None):
        if r is None:
            r = self['R']
        if 128 <= r < 224:
            raise assy.Invalid("invalid R")
        if r >> 4 == 14:
            r &= 0xf
            return "R%d" % r
        n = Z8_REGISTERS.get(r)
        if n:
            return n
        return "0x%x" % r

    def assy_R2(self, r = None):
        return self.assy_R(self['R2'])

    def assy_IR(self, r = None):
        return '(' + self.assy_R(self['IR']) + ')'

    def assy_RR(self):
        r = self['RR']
        if 128 <= r < 224:
            raise assy.Invalid("invalid R")
        if r >> 4 == 14:
            r &= 0xf
            return "RR%d" % r
        n = Z8_REGISTERS.get(r)
        if n:
            return n
        return "0x%x" % r

    def assy_IRR(self):
        return "@" + self.assy_RR()

    def assy_iR(self):
        if self['i']:
            return "@" + self.assy_R()
        return self.assy_R()

    def assy_iRR(self):
        if self['i']:
            return "@" + self.assy_RR()
        return self.assy_RR()

    def assy_Im(self):
        return "#0x%x" % self['IM']

    def assy_Ir(self):
        return "@R%d" % self['Ir']

    def assy_DA(self):
        self.dstadr = (self['da_h'] << 8) | self['da_l']
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_RA(self):
        ra = self['ra']
        self.dstadr = self.hi + ra
        if ra & 0x80:
            self.dstadr -= 256
       
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_rIrr(self):
        r = "R%d" % self['r']
        irr = "@RR%d" % self['Irr']
        if self['d']:
            self.oper.append(assy.Arg_verbatim(irr))
            self.oper.append(assy.Arg_verbatim(r))
        else:
            self.oper.append(assy.Arg_verbatim(r))
            self.oper.append(assy.Arg_verbatim(irr))

    def assy_dst_src(self):
        x = self['x']
        if x < 2:
            raise assy.Invalid("invalid x")
        elif x < 4:
            src = 'R%d' % (self['y'] & 0xf)
            dst = 'R%d' % (self['y'] >> 4)
        elif x < 6:
            src = self.assy_R(self['y'])
            dst = self.assy_R(self.lang.m[self.hi])
            self.hi += 1
        elif x < 8:
            dst = self.assy_R(self['y'])
            src = '#0x%x' % self.lang.m[self.hi]
            self.hi += 1
        else:
            raise assy.Invalid("invalid x")
        if x & 1:
            src = '@' + src
        self.oper.append(assy.Arg_verbatim(dst))
        self.oper.append(assy.Arg_verbatim(src))

Z8_MACROS = '''
LD	mRRmIMM			| r1	|1 1 0 0| im1		| r2	|1 1 0 0| im2		|
CLR	mRR			|1 0 1 1|0 0 0 0|1 1 1 0| r1	|1 0 1 1|0 0 0 0|1 1 1 0| r2	|
LD	m2RR			| rr1   |1 0 0 0|1 1 1 0| r1	| rr2   |1 0 0 0|1 1 1 0| r2	|
'''

class Z8MacroIns(Z8Ins):

    def assy_mRR(self):
        if self['r1'] + 1 == self['r2']:
            rr = "RR%d" % self['r1']
        elif self['r2'] + 1 == self['r1']:
            rr = "RR%d" % self['r2']
        else:
            raise assy.Invalid()
        return rr

    def assy_m2RR(self):
        if self['r1'] + 1 == self['r2'] and self['rr1'] + 1 == self['rr2']:
            rr1 = "RR%d" % self['r1']
            rr2 = "RR%d" % self['rr1']
        elif self['r2'] + 1 == self['r1'] and self['rr2'] + 1 == self['rr1']:
            rr1 = "RR%d" % self['r2']
            rr2 = "RR%d" % self['rr2']
        else:
            raise assy.Invalid()
        self.oper.append(assy.Arg_verbatim(rr1))
        self.oper.append(assy.Arg_verbatim(rr2))

    def assy_mRRmIMM(self):
        if self['r1'] + 1 == self['r2']:
            rr = "RR%d" % self['r1']
            v = (self['im1'] << 8) | self['im2']
        elif self['r2'] + 1 == self['r1']:
            rr = "RR%d" % self['r2']
            v = (self['im2'] << 8) | self['im1']
        else:
            raise assy.Invalid()
        self.oper.append(assy.Arg_verbatim(rr))

        self.oper.append(assy.Arg_imm(v))

class Z8(assy.Instree_disass):
    def __init__(self, lang="z8"):
        super().__init__(
            lang,
            ins_word=8,
            abits=16,
            endian='>',
        )
        self.it.load_string(Z8_DESC, Z8Ins)

    def use_macros(self):
        self.it.load_string(Z8_MACROS, Z8MacroIns)

    def vectors(self, which=None):
        for a, b in (
                (0x0000, "IRQ0_P3_2"),
                (0x0002, "IRQ1_P3_3"),
                (0x0004, "IRQ2_P3_1"),
                (0x0006, "IRQ3_P3_0_SIN"),
                (0x0008, "IRQ4_T0_SOUT"),
                (0x000a, "IRQ5_TI"),
                (0x000c, "RESET"),
        ):
            if not which or a in which or b in which:
                if a < 0x000c:
                    self.codeptr(a)
                    self.m.set_line_comment(a, b)
                    a = self.m.bu16(a)
                self.disass(a)
                self.m.set_label(a, b)

if __name__ == "__main__":

    cx = Z8()
    cx.it.dump()


