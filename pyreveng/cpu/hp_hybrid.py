#!/usr/bin/env python #
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

'''Hewlett Packard Hybrid Processor

Used in HP98xx calculators and HP8566A Spectrum Analyzer

'''

from pyreveng import assy, data, code, mem

''' see 09845-91083_asmDevRom_Mar80.pdf p 292 '''

hp_hybrid_desc = """
NOP	-		|0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0|

LDx	x,ddst		|d|0 0 0|x|c| adr		|

CPx	x,ddst,skp	|d|0 0 1|x|c| adr		|

ADx	x,ddst		|d|0 1 0|x|c| adr		|

STx	x,ddst		|d|0 1 1|x|c| adr		|

JSM	dst,>C		|d|1 0 0|0|c| adr		|

AND	ddst		|d|1 0 1|0|c| adr		|

ISZ	ddst,skp	|d|1 0 0|1|c| adr		|

DSZ	ddst,skp	|d|1 0 1|1|c| adr		|

IOR	ddst		|d|1 1 0|0|c| adr		|

JMP	dst,>J		|d|1 1 0|1|c| adr		|

SFS	skip		|0|1 1 1|0 1 0|0 1 0|d| skip	|
SFC	skip		|0|1 1 1|0 1 0|1 1 0|d| skip	|
SDS	skip		|0|1 1 1|0 1 0|0 1 1|d| skip	|
SDC	skip		|0|1 1 1|0 1 0|1 1 1|d| skip	|

RZx	x,skip		|0 1 1 1|x|1 0 0 0 0|d| skip	|
RIx	x,skip 		|0 1 1 1|x|1 0 0 0 1|d| skip	|
SZx	x,skip		|0 1 1 1|x|1 0 1 0 0|d| skip	|
SIx	x,skip		|0 1 1 1|x|1 0 1 0 1|d| skip	|

RLx	x,skip,cs	|0 1 1 1|x|1 1 1|h|c|d| skip	|
SLx	x,skip,cs	|0 1 1 1|x|1 1 0|h|c|d| skip	|

SSS	skip		|0 1 1 1 1 1 0 0 1 0|d| skip	|
SSC	skip		|0 1 1 1 1 1 0 1 1 0|d| skip	|

SHS	skip		|0 1 1 1 1 1 0 0 1 1|d| skip	|
SHC	skip		|0 1 1 1 1 1 0 1 1 1|d| skip	|

SxP	x,skip,cs	|1 1 1 1|x|1 0 0|h|c|d| skip	|
SxM	x,skip,cs	|1 1 1 1|x|1 0 1|h|c|d| skip	|

SOS	skip,cs		|1 1 1 1 0 1 1 1|h|c|d| skip	|
SOC	skip,cs		|1 1 1 1 0 1 1 0|h|c|d| skip	|
SES	skip,cs		|1 1 1 1 1 1 1 1|h|c|d| skip	|
SEC	skip,cs		|1 1 1 1 1 1 1 0|h|c|d| skip	|

RET	nret,>R		|1 1 1 1 0 0 0 0 1 0| n		|


AxR	x,n		|1|1 1 1|x|0 0|1 0 0|0 0| n	|
CBL	-		|0|1 1 1|0 0 0|1 0 1|0 0 1|0 0 0|
CBU	-		|0|1 1 1|0 0 0|1 0 1|0 1 1|0 0 0|
CDC	-		|0|1 1 1|0 0 1|1 1 1|0 0 0|0 0 0|
CLx	x		|1|1 1 1|x|0 0|1 0 1|0 0 1|1 1 1|
CLR	n		|0 1 1 1 0 0 1 1 1 0 0 0| n	|
CMx	x		|1 1 1 1|x|0 0 0 0 1 1 0 0 0 0 0|
CMX	-		|0 1 1 1 0 0 1 0 0 1 1 0 0 0 0 0|
CMY	-		|0 1 1 1 0 0 1 0 0 0 1 0 0 0 0 0|
DBL	-		|0 1 1 1 0 0 0 1 0 1 0 0 0 0 0 0|
DBU	-		|0 1 1 1 0 0 0 1 0 1 0 1 0 0 0 0|
DDR	-		|0 1 1 1 0 0 0 1 0 0 1 1 1 0 0 0|
DIR	-		|0 1 1 1 0 0 0 1 0 0 0 1 1 0 0 0|
DMA	-		|0 1 1 1 0 0 0 1 0 0 1 0 0 0 0 0|
DRS	-		|0 1 1 1 1 0 1 1 0 0 1 0 0 0 0 1|
EIR	-		|0 1 1 1 0 0 0 1 0 0 0 1 0 0 0 0|
EXE	exereg,d	|d|1 1 1 0 0 0 0 0 0 0| reg	|
FDV	-		|0 1 1 1 1 0 1 0 0 0 1 0 0 0 0 1|
FMP	-		|0 1 1 1 1 0 1 0 0 0 0 0 0 0 0 0|
FXA	-		|0 1 1 1 0 0 1 0 1 0 0 0 0 0 0 0|
MLY	-		|0 1 1 1 1 0 1 1 0 1 1 0 0 0 0 1|
MPY	-		|0 1 1 1 1 0 1 1 1 0 0 0 1 1 1 1|
MRX	-		|0 1 1 1 1 0 1 1 0 0 0 0 0 0 0 0|
MRY	-		|0|1 1 1|1 0 1|1 0 1|0 0 0 0 0 0|
MWA	-		|0|1 1 1|0 0 1|0 0 0|0 0 0|0 0 0|
NRM	-		|0 1 1 1 0 0 1 1 0 1 0 0 0 0 0 0|
PBC	reg		|0 1 1 1 1 0 0 1|d|1 1 0 0| r	|
PBD	reg		|0 1 1 1 1 0 0 1|d|1 1 0 1| r	|
PWC	reg		|0 1 1 1 0 0 0 1|d|1 1 0 0| r	|
PWD	reg		|0 1 1 1 0 0 0 1|d|1|1 0 1| r	|
#RxL	?		|1 1 1 1|x|0 0 1 1 1 0 0|n	|
RxR	x,n		|1 1 1 1|x|0 0 1 1 1 0 0|n	|
SxL	x,n		|1 1 1 1|x|0 0 1 1 0|0 0|n	|
SxR	x,n		|1 1 1 1|x|0 0 1 0 1|0 0|n	|
SDI	-		|0 1 1 1 0 0 0 1 0 0|0 0 1|0 0 0|
SDO	-		|0 1 1 1 0 0 0 1 0 0 0 0 0 0 0 0|
TCx	x		|1 1 1 1|x|0 0 0 0 0|1 0 0 0 0 0|
WBC	reg		|0 1 1 1 1 0 0 1|d|1|1 1 0|r	|
WBD	reg		|0 1 1 1 1 0 0 1|d|1|1 1 1|r	|
WWC	reg		|0 1 1 1 0 0 0 1|d|1|1 1 0|r	|
WWD	reg		|0 1 1 1 0 0 0 1|d|1|1 1 1|r	|
XFR	n		|0 1 1 1 0 0 1 1 0 0 0 0|n	|
"""

class hp_hybrid_ins(assy.Instree_ins):

    def assy_x(self):
        self.mne = self.mne.replace('x', "AB"[self['x']])

    def assy_reg(self):
        return (
            "A",
            "B",
            "?R2?",
            "?R3?",
            "?R4?",
            "?R5?",
            "?R6?",
            "?R7?",
        )[self['r']]

    def assy_cs(self):
        if self['h'] and not self['c']:
            return 'C'
        if self['h'] and self['c']:
            return 'S'
        if self['c']:
            return "?C?"
        if self['h']:
            return "?H?"

    def assy_n(self):
        return "0x%x" % (self['n'] + 1)

    def assy_d(self):
        if self['d']:
            return "I"

    def assy_exereg(self):
        return "0x%x" % self['reg']

    def assy_nret(self):
        return "0x%x" % self['n']

    def assy_dst(self, cde=True):
        a = self['adr']
        if a & 0x200:
            a -= 0x400
        if self['c']:
            a += self.lo 

        dd = (a + (1 << 16)) & 0x7fff
        if not self['d']:
            if cde:
                self.dstadr = dd
            return assy.Arg_dst(self.lang.m, dd)
        try:
            d = self.lang.m[dd]
            y = data.Data(self.lang.m, dd, dd + 1)
            y.rendered = ".REF\t0x%04x" % d
            if cde:
                self.dstadr = d
            return [assy.Arg_dst(self.lang.m, d), assy.Arg_verbatim("[Via 0x%04x]" % dd)]
        except mem.MemError:
            pass
        if cde:
            self.dstadr = dd
        return [assy.Arg_dst(self.lang.m, dd), assy.Arg_verbatim("I")]

    def assy_ddst(self):
        return self.assy_dst(cde=False)

    def assy_skp(self):
        self += code.Jump(cond="?", to=self.hi)
        self += code.Jump(cond="?", to=self.hi + 1)

    def assy_skip(self):
        s = self['skip']
        d = self['d']
        if d:
            s = 0x20 - s
            self.dstadr = self.lo - s
        else:
            self.dstadr = self.lo + s
        self += code.Jump(cond="?s", to=self.hi)
        self += code.Jump(cond="?!s", to=self.dstadr)
        return assy.Arg_dst(self.lang.m, self.dstadr)

class hp_hybrid(assy.Instree_disass):
    def __init__(self, abits=16):
        super().__init__(
            "HP Hybrid Processor",
            mem_word=16,
            ins_word=16,
            abits=abits,
            endian=">",
        )
        self.add_ins(hp_hybrid_desc, hp_hybrid_ins)
        for a, b in (
            (0x0000, "%A"),
            (0x0001, "%B"),
            (0x0002, "%PC"),
            (0x0003, "%RSP"),
            (0x0004, "%R4"),
            (0x0005, "%R5"),
            (0x0006, "%R6"),
            (0x0007, "%R7"),
            (0x000b, "%DMAPA"),
            (0x000c, "%DMAMA"),
            (0x000d, "%DMAC"),
            (0x000e, "%CSP"),
            (0x000f, "%DSP"),
        ):
            self.m.set_label(a, b)
