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

'''HP8904 Synthesizer/Level Generator
'''

from pyreveng import mem, listing, assy, data, code, discover
import pyreveng.cpu.mc6809 as mc6809
import pyreveng.cpu.banked as banked

NAME = "HP8904_BANKED"
FILENAME1 = "08904-87011.BIN"
DIR = "/critter/Doc/TestAndMeasurement/HP8904A/FW/"
NPG = 6

SYMBOLS = (
	(0, 0x0100, "SERVICE_SWITCH"),
	(0, 0x0200, "NSMIC"),
	(0, 0x0300, "LCD_CTL"),
	(0, 0x0301, "LCD_DATA"),
	(0, 0x0400, "HPIB_0"),
	(0, 0x0401, "HPIB_1"),
	(0, 0x0402, "HPIB_2"),
	(0, 0x0403, "HPIB_3"),
	(0, 0x0404, "HPIB_4"),
	(0, 0x0405, "HPIB_5"),
	(0, 0x0406, "HPIB_6"),
	(0, 0x0407, "HPIB_7"),
	(0, 0x0600, "IO_600"),
	(0, 0x0900, "LEDS"),
	(0, 0x0a00, "KBD_SCAN"),
	(0, 0x0b00, "HOPLATCH"),
	(0, 0x0c00, "OUTPUT_1"),
	(0, 0x0d00, "OUTPUT_2"),
	(0, 0x0e00, "OUTPUT_3"),
	(0, 0x0f00, "OUTPUT_4"),
	(0, 0x1000, "PTM_0"),
	(0, 0x1001, "PTM_1"),
	(0, 0x1002, "PTM_TIMER1"),
	(0, 0x1003, "PTM_TIMER2"),
	(0, 0x1004, "PTM_TIMER3"),

        (0, 0x8dba, "SETUP_MENU(Y, U)"),
        (0, 0x8efe, "MENU_EXIT()"),
        (0, 0xc52a, "MENU_NOP()"),
)

def romsum(m, lo, hi):
    '''XXX: this looks bogus'''
    b = 0
    c = 0
    for j in range(0x4000, 0x8000):
        b += m.m[j] + c
        c = b >> 8
        c = 1
        b &= 0xff
    print("Bank sum %x %x" % (b, c))

def dataptr(cx, a):
    y = data.Dataptr(cx.m, a, a + 2, cx.m.bu16(a))
    return y

def textptr(cx, a):
    y = dataptr(cx, a)
    data.Txt(cx[0].m, y.dst, pfx=1, label=False)
    return y

def menuxxx(cx, a):
    s = set()
    for i in range(0, 5):
        y = dataptr(cx, a + i * 2)
        if y.dst not in s:
            s.add(y.dst)
            data.Txt(cx.m, y.dst, y.dst + 40, label=False)

class MenuPage(data.Data):

    def __init__(self, cx, adr):
        super().__init__(cx.m, adr, adr + 10)
        self.tp = []
        x = cx.m.bu16(adr)
        self.tp.append(data.Txt(cx.m, x, x + 40, label=False))
        self.tp.append(data.Txt(cx.m, x + 40, x + 80, label=False))
        self.fp = []
        for i in range(2, 10, 2):
            self.fp.append(cx.m.bu16(adr + i))
            cx.m.set_block_comment(self.fp[-1], "Menu@%x[%d]" % (adr, i//2))
            cx.disass(self.fp[-1])

    def render(self):
        t = ".MENU {\n"
        for i in self.tp:
            t += "\t.txt =\t'" + i.txt + "'\n"
        for i, j in enumerate(self.fp):
            t += "\t.f%d =\t" % (i + 1) + self.aspace.afmt(j) + "\n"
        t += "}"
        return t

class Menu():
    def __init__(self, cx, adr, n):
        for i in range(n):
            y = MenuPage(cx, adr)
            adr = y.hi

def pg0(cx):
    menuxxx(cx, 0x4018)
    cx.codeptr(0x4004)
    cx.codeptr(0x4006)
    cx.codeptr(0x4008)
    cx.codeptr(0x400a)
    cx.codeptr(0x400c)
    cx.codeptr(0x400e)
    cx.codeptr(0x4010)
    cx.codeptr(0x4012)
    cx.codeptr(0x4014)
    cx.codeptr(0x4016)
    cx.codeptr(0x4022)
    cx.codeptr(0x4024)
    cx.codeptr(0x4027)
    cx.codeptr(0x4029)

    for a in range(0x40ce, 0x410b, 7):
        x = cx.m[a + 1]
        y = cx.m.bu16(a + 3)
        print(cx, " -> %x" % a, "%x" % x, "%x" % y)
        cx[x].disass(y)

def pg1(cx):
    for a in range(0x43af, 0x43bf, 2):
        cx.codeptr(a)

def flow_out_ffed(a, b):
    if b.mne == "BSR" and b.dstadr == 0xffed:
        print("FFED", a, b.render(), b.flow_out)
        b.flow_out.pop(1)
    if b.mne == "BSR" and b.dstadr == 0xfd89:
        if b.lang.m[b.lo - 3] == 0xfc:
            x = b.lang.m.bu16(b.lo - 2)
            #data.Pstruct(b.lang.m, x, "B")
            #data.Pstruct(b.lang.m, x + 1, "B")
            y = b.lang.m.bu16(x)
            b.lcmt = "= #0x%04x" % y

class mycpu(mc6809.mc6809):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flow_check.append(flow_out_ffed)

def example():
    rv = []
    m1 = mem.Stackup((FILENAME1,), prefix=DIR)
    rv.append(m1)
    m3 = mem.ByteMem(lo=0x0000, hi=0x4000)

    cx = banked.BankedCPU(NPG, mycpu)
    for i in range(NPG):
        cx[i].m.map(m3, 0x0000, 0x4000, shared=True)
        cx[i].m.map(m1, 0x4000, 0x8000, offset = i * 0x4000)
        cx[i].m.map(m1, 0x8000, 0x10000, shared=True, offset = 6 * 0x4000)
        rv.append(cx[i].m)

        romsum(cx[i], 0x4000, 0x8000)

    for b in cx.bank:
        print(b, b.m)
        y = data.Const(b.m, 0x4000, 0x4001)
        y.lcmt = "Bank#"
        y = data.Const(b.m, 0x4001, 0x4002)
        y.lcmt = "Checksum Adjust"

    for p, a, t in SYMBOLS:
        cx[p].m.set_label(a, t)
       
    cx[0].vectors()

    for a, b in (
        (0x9280, 0x92c4),
        (0xa9d2, 0xa9dc),
        (0xaab7, 0xaac3),
        (0xb0cd, 0xb0dd),
	(0xb1d0, 0xb238),
	(0xb31a, 0xb328),
	(0xb5ae, 0xb5ba),
	(0xc443, 0xc463),
	(0xd78e, 0xd79a),
	(0xe433, 0xe43f),
    ):
        for i in range(a, b, 2):
            cx[0].codeptr(i)

    for a, b in (
        (0xee5b, 0xee91),
        (0xef1f, 0xef41),
    ):
        for i in range(a, b, 2):
            y = data.Dataptr(cx[0].m, i, i + 2, cx[0].m.bu16(i))
            data.Txt(cx[0].m, y.dst, pfx=1, label=False)

    for a, b in (
        (0, 0x45ba,),
        (0, 0x4d99,),
        (0, 0x58c7,),
        (0, 0x5b01,),
        (0, 0x6aef,),
        (0, 0x6fe9,),

        (1, 0x4607,),
        (1, 0x4f71,),
        (1, 0x5033,),
        (1, 0x50ab,),
        (1, 0x54ea,),
        (1, 0x56a1,),
        (1, 0x57b3,),
        (1, 0x627e,),

        # Common page
        (0, 0x8000,),
        (0, 0x8de1,),
        (0, 0x8f6a,),
        (0, 0xa1ac,),
        (0, 0xa23b,),
        (0, 0xa421,),
        (0, 0xa45b,),
        (0, 0xa5c9,),
        (0, 0xa69d,),
        (0, 0xa6cf,),
        (0, 0xa705,),
        (0, 0xa732,),
        (0, 0xa758,),
        (0, 0xc601,),
        (0, 0xca79,),
        (0, 0xcb68,),
        (0, 0xcc32,),
        (0, 0xcd13,),
        (0, 0xce0c,),
        (0, 0xce56,),
        (0, 0xcebd,),
        (0, 0xd1d1,),
        (0, 0xd6f8,),
        (0, 0xdafe,),
        (0, 0xf07f,),
        (0, 0xf1a3,),
        (0, 0xf42c,),
        (0, 0xfa0d,),
    ):
        cx[a].disass(b)
        cx[a].m.set_line_comment(b, "%x:%x MANUAL" % (a,b))

    pg0(cx[0])
    pg1(cx[1])

    # discover.Discover(cx[0])

    Menu(cx[0], 0x4257, 7)
    Menu(cx[1], 0x437d, 5)
    Menu(cx[2], 0x416b, 4)
    Menu(cx[2], 0x4234, 4)
    Menu(cx[3], 0x4292, 4)
    Menu(cx[4], 0x4172, 4)
    Menu(cx[5], 0x4144, 4)

    return NAME, rv

if __name__ == '__main__':
    listing.Example(example, ncol=8, pil=False)

