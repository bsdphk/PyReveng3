#!/usr/bin/env python
#
# Copyright (c) 2021 Poul-Henning Kamp <phk@phk.freebsd.dk>
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

'''Intel MCS-96

This one is surprisingly hard to find docs on, and one crucial
bit of how it works seems to be only documented in this footnote:

	Long indexed and Indirect + instructions have identical
	opcodes with Short indexed and Indirect modes, respectively.
	The second byte of instructions using any Indirect or indexed
	addressing mode specifies the exact mode used. If the second
	byte is even, use Indirect or Short indexed. If it is odd,
	use Indirect + or Long indexed. In all cases the second
	byte of the instruction always specifies an even (word)
	location for the address referenced.

'''

from pyreveng import assy, data

MCS96_DESC = '''
ADD	waop,swreg,dwreg	|0 1 0 0 0 1| aa|
ADD	waop,wreg		|0 1 1 0 0 1| aa|
ADDB	baop,sbreg,dbreg	|0 1 0 1 0 1| aa|
ANDB	baop,breg		|0 1 1 1 0 0| aa|
ANDB	baop,sbreg,dbreg	|0 1 0 1 0 0| aa|
BR	wreg,>J			|1 1 1 0 0 0 1 1|
CLR	wreg			|0 0 0 0 0 0 0 1|
CLRB	breg			|0 0 0 1 0 0 0 1|
CLRC	-			|1 1 1 1 1 0 0 0|
CLRVT	-			|1 1 1 1 1 1 0 0|
CMP	waop,wreg		|1 0 0 0 1 0| aa|
CMPB	baop,breg		|1 0 0 1 1 0| aa|
CMPL	slreg,dlreg		|1 1 0 0 0 1 0 1|
DEC	wreg			|0 0 0 0 0 1 0 1|
DECB	breg			|0 0 0 1 0 1 0 1|
DI	-			|1 1 1 1 1 0 1 0|
DJNZ	breg,cadd_r,>JC		|1 1 1 0 0 0 0 0|
EI	-			|1 1 1 1 1 0 1 1|
EXT	lreg			|0 0 0 0 0 1 1 0|
EXTB	wreg			|0 0 0 1 0 1 1 0|
ADDB	baop,breg		|0 1 1 1 0 1| aa|
ADDC	waop,wreg		|1 0 1 0 0 1| aa|
ADDCB	baop,breg		|1 0 1 1 0 1| aa|
AND	waop,swreg,dwreg	|0 1 0 0 0 0| aa|
AND	waop,wreg		|0 1 1 0 0 0| aa|
DIV 	waop,lreg		|1 1 1 1 1 1 1 0|1 0 0 0 1 1| aa|
DIVB	baop,wreg		|1 1 1 1 1 1 1 0|1 0 0 1 1 1| aa|
DIVU	waop,lreg		|1 0 0 0 1 1| aa|
DIVUB	baop,wreg		|1 0 0 1 1 1| aa|
IDLPD	key			|1 1 1 1 0 1 1 0| key		|
INC	wreg			|0 0 0 0 0 1 1 1|
INCB	breg			|0 0 0 1 0 1 1 1|
JBC	bit,breg,cadd_r,>JC	|0 0 1 1 0| bbb	|
JBS	bit,breg,cadd_r,>JC	|0 0 1 1 1| bbb	|
Jcc	cc,cadd_r,>JC		|1 1 0 1| cc	|
LCALL	cadd16,>C		|1 1 1 0 1 1 1 1|
LD	waop,wreg		|1 0 1 0 0 0| aa|
LDB	baop,breg		|1 0 1 1 0 0| aa|
LDBSE	baop,wreg		|1 0 1 1 1 1| aa|
LDBZE	baop,wreg		|1 0 1 0 1 1| aa|
LJMP	cadd16,>J		|1 1 1 0 0 1 1 1|
MUL	waop,lreg		|1 1 1 1 1 1 1 0|0 1 1 0 1 1| aa|
MUL	waop,wreg,lreg		|1 1 1 1 1 1 1 0|0 1 0 0 1 1| aa|
MULB	baop,breg,wreg		|1 1 1 1 1 1 1 0|0 1 0 1 1 1| aa|
MULB	baop,wreg		|1 1 1 1 1 1 1 0|0 1 1 1 1 1| aa|
MULU	waop,lreg		|0 1 1 0 1 1| aa|
MULU	waop,wreg,lreg		|0 1 0 0 1 1| aa|
MULUB	baop,breg,wreg		|0 1 0 1 1 1| aa|
MULUB	baop,wreg		|0 1 1 1 1 1| aa|
NEG	wreg			|0 0 0 0 0 0 1 1|
NEGB	breg			|0 0 0 1 0 0 1 1|
NOP	-			|1 1 1 1 1 1 0 1|
NORML	breg,lreg		|0 0 0 0 1 1 1 1|
NOT	wreg			|0 0 0 0 0 0 1 0|
NOTB	breg			|0 0 0 1 0 0 1 0|
OR	waop,wreg		|1 0 0 0 0 0| aa|
ORB	baop,breg		|1 0 0 1 0 0| aa|
POP	waop			|1 1 0 0 1 1| aa|
POPA	-			|1 1 1 1 0 1 0 1|
POPF	-			|1 1 1 1 0 0 1 1|
PUSH	waop			|1 1 0 0 1 0| aa|
PUSHA	-			|1 1 1 1 0 1 0 0|
PUSHF	-			|1 1 1 1 0 0 1 0|
RET	>R			|1 1 1 1 0 0 0 0|
RST	>R			|1 1 1 1 1 1 1 1|
SCALL	cadd_s,>C		|0 0 1 0 1| xxx	|
SETC	-			|1 1 1 1 1 0 0 1|
SHL 	breg,wreg		|0 0 0 0 1 0 0 1|
SHLB 	breg,breg		|0 0 0 1 1 0 0 1|
SHLL 	breg,lreg		|0 0 0 0 1 1 0 1|
SHR 	breg,wreg		|0 0 0 0 1 0 0 0|
SHRA 	breg,wreg		|0 0 0 0 1 0 1 0|
SHRAB	breg,breg		|0 0 0 1 1 0 1 0|
SHRAL	breg,lreg		|0 0 0 0 1 1 1 0|
SHRB	breg,breg		|0 0 0 1 1 0 0 0|
SHRL	breg,lreg		|0 0 0 0 1 1 0 0|
SJMP	cadd_s,>J		|0 0 1 0 0| xxx	|
SKIP	breg			|0 0 0 0 0 0 0 0|
ST	waop,wreg		|1 1 0 0 0 0| aa|
STB	baop,breg		|1 1 0 0 0 1| aa|
SUB	waop,swreg,dwreg	|0 1 0 0 1 0| aa|
SUB	waop,wreg		|0 1 1 0 1 0| aa|
SUBB	baop,breg		|0 1 1 1 1 0| aa|
SUBB	baop,sbreg,dbreg	|0 1 0 1 1 0| aa|
SUBC	waop,wreg		|1 0 1 0 1 0| aa|
SUBCB	baop,breg		|1 0 1 1 1 0| aa|
TIJMP	XXX,wreg,wreg2,byte	|1 1 1 0 0 0 1 0| wreg		| byte		| wreg2		|
TRAP	>R			|1 1 1 1 0 1 1 1|
XCH	XXX,swreg,dwreg		|0 0 0 0 1 0 1 1|
XCH	swreg,dwreg		|0 0 0 0 0 1 0 0|
XCHB	XXX,baop,breg		|0 0 0 1 0 1 0 0|
XCHB	XXX,baop,breg		|0 0 0 1 1 0 1 1|
XOR	waop,wreg		|1 0 0 0 0 1| aa|
XORB	baop,breg		|1 0 0 1 0 1| aa|
'''

MCS80C196KB_DESC = """
BMOV	lreg,wreg		|1 1 0 0 0 0 0 1|
DJNZW	wreg,cadd_r		|1 1 1 0 0 0 0 1|
"""

MCS80C196KC_DESC = """
# 3-7
BMOV	lreg,wreg		|1 1 0 0 0 0 0 1| wreg		| lreg		|

# 3-8
BMOVI	lreg,wreg		|1 0 1 0 1 1 0 1| wreg		| lreg		|

# 3-16
DJNZW	wreg,cadd		|1 1 1 0 0 0 0 1| wreg		| disp		|

# 3-17
DPTS	-			|1 1 1 0 1 1 0 0|

# 3-18
EPTS	-			|1 1 1 0 1 1 0 1|
"""

MCS96_MACRO = '''
RCALL	rcall,wreg,>C		|1 1 0 0 1 0 0 1| lo		| hi		|1 1 1 0 0 0 1 1|
'''

class MCS96Ins(assy.Instree_ins):
    ''' ... '''

    def assy_rcall(self):
        w = self['lo'] | (self['hi'] << 8)
        if w != self.hi + 1:
            raise assy.Invalid()

    def assy_cc(self):
        i = self['cc']
        cc = [
            "NST", "NH", "GT", "NC", "NVT", "NV", "GE", "NE",
            "ST", "H", "LE", "C", "VT", "V", "LT", "E",
        ][i]
        self.mne = self.mne.replace("cc", cc)

    def assy_bit(self):
        self.oper.insert(0, assy.Arg_imm(self['bbb']))

    def assy_baop(self):
        aa = self['aa']
        if aa == 0:
            r = self.lang.m[self.hi]
            self.hi += 1
            self.oper.insert(0, assy.Arg_verbatim("B%02x" % r))
        elif aa == 1:
            i = self.lang.m[self.hi]
            self.hi += 1
            self.oper.insert(0, assy.Arg_imm(i))
        elif aa == 2:
            r = self.lang.m[self.hi]
            self.hi += 1
            t = "[0x%02x]" % (r & 0xfe)
            if r & 1:
                t += "+"
            self.oper.insert(0, assy.Arg_verbatim(t))
        elif aa == 3:
            i = self.lang.m[self.hi]
            self.hi += 1
            j = i & 1
            i = i & 0xfe
            if j == 0x1:
                k = "0x%04x" % self.lang.m.lu16(self.hi)
                self.hi += 2
            else:
                k = "0x%02x" % self.lang.m[self.hi]
                self.hi += 1
            if i:
                k += "[R%02x]" % i
            self.oper.insert(0, assy.Arg_verbatim(k))

    def assy_breg(self):
        r = self.lang.m[self.hi]
        self.hi += 1
        self.oper.insert(0, assy.Arg_verbatim("B%02x" % r))

    def assy_dbreg(self):
        return self.assy_breg()

    def assy_sbreg(self):
        return self.assy_breg()

    def assy_cadd_r(self):
        v = self.lang.m[self.hi]
        self.hi += 1
        if v & 0x80:
            v -= 0x100
        self.dstadr = self.hi + v
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_cadd_s(self):
        v = self.lang.m[self.hi]
        self.hi += 1
        v |= self['xxx'] << 8
        if v & 0x400:
            v -= 0x800
        self.dstadr = self.hi + v
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_cadd16(self):
        self.dstadr = self.lang.m.lu16(self.hi)
        self.hi += 2
        self.dstadr += self.hi
        self.dstadr &= 0xffff
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_cnt(self):
        i = self.lang.m[self.hi]
        self.hi += 1
        self.oper.insert(0, assy.Arg_imm(i))

    def assy_key(self):
        self.oper.insert(0, assy.Arg_imm(self['key']))

    def assy_waop(self):
        aa = self['aa']
        if aa == 0:
            r = self.lang.m[self.hi]
            self.hi += 1
            self.oper.insert(0, assy.Arg_verbatim("W%02x" % r))
        elif aa == 1:
            i = self.lang.m.lu16(self.hi)
            self.hi += 2
            self.oper.insert(0, assy.Arg_imm(i))
        elif aa == 2:
            r = self.lang.m[self.hi]
            self.hi += 1
            t = "[0x%02x]" % (r & 0xfe)
            if r & 1:
                t += "+"
            self.oper.insert(0, assy.Arg_verbatim(t))
        elif aa == 3:
            i = self.lang.m[self.hi]
            self.hi += 1
            j = i & 1
            i = i & 0xfe
            if j == 0x1:
                k = "0x%04x" % self.lang.m.lu16(self.hi)
                self.hi += 2
            else:
                k = "0x%02x" % self.lang.m[self.hi]
                self.hi += 1
            if i:
                k += "[R%02x]" % i
            self.oper.insert(0, assy.Arg_verbatim(k))

    def assy_lreg(self):
        r = self.lang.m[self.hi]
        self.hi += 1
        self.oper.insert(0, assy.Arg_verbatim("L%02x" % r))

    def assy_dlreg(self):
        return self.assy_lreg()

    def assy_slreg(self):
        return self.assy_lreg()

    def assy_wreg(self):
        r = self.lang.m[self.hi]
        self.hi += 1
        self.oper.insert(0, assy.Arg_verbatim("W%02x" % r))

    def assy_dwreg(self):
        return self.assy_wreg()

    def assy_swreg(self):
        return self.assy_wreg()

class MCS96(assy.Instree_disass):
    def __init__(self, lang="mcs96"):
        super().__init__(
            lang,
            ins_word=8,
            abits=16,
            endian='<',
        )
        self.it.load_string(MCS96_DESC, MCS96Ins)
        self.it.load_string(MCS96_MACRO, MCS96Ins)

    def vectors(self, which=None):
        for adr,nam in (
            (0x2000, "Timer"),
            (0x2002, "ADC"),
            (0x2004, "HSI_DAV"),
            (0x2006, "HSO"),
            (0x2008, "HSI.0"),
            (0x200a, "SwTimer"),
            (0x200c, "Serial"),
            (0x200e, "ExtInt"),
            (0x2010, "Trap"),
            (0x2012, "UnimpInstr"),
            (0x2030, "TI"),
            (0x2032, "RI"),
            (0x2034, "HSI_FIFO_4TH"),
            (0x2036, "TIMER2_CAPTURE"),
            (0x2038, "TIMER2_OVERFLOW"),
            (0x203a, "EXTINT1"),
            (0x203c, "HSI_FIFO_FULL"),
            (0x203e, "NMI"),
        ):
            if which and adr not in which and nam not in which:
                continue
            y = self.codeptr(adr)
            self.m.set_label(y.dst, "VECTOR_" + nam)

        self.m.set_label(0x2080, "RESET")
        self.disass(0x2080)

    def dataptr(self, adr):
        return data.Dataptr(self.m, adr, adr + 2, self.m.lu16(adr))

class MCS196(MCS96):
    def __init__(self):
        super().__init__()
        self.it.load_string(MCS80C196KB_DESC, MCS96Ins)
