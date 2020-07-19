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

from pyreveng import mem, listing, data, assy
import pyreveng.cpu.mc6809 as mc6809
import pyreveng.cpu.banked as banked
import pyreveng.toolchest.bitmap as bitmap

NAME = "HP8904_BANKED"
FILENAME1 = "08904-87011.BIN"
DIR = "/critter/Doc/TestAndMeasurement/HP8904A/FW/"
NPG = 6

CHARSET = dict(data.ASCII.items())
CHARSET[0x00] = "f̲"
CHARSET[0x01] = "1̲"
CHARSET[0x02] = "2̲"
CHARSET[0x03] = "3̲"
CHARSET[0x04] = "4̲"
CHARSET[0x05] = "φ"
CHARSET[0x06] = "µ"

class Txt(data.Txt):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, charset=CHARSET, **kwargs)

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

    (0, 0xd68f, "LCD_WR_CTL()"),
    (0, 0xd6b1, "LCD_WR_DATA()"),
    (0, 0xd6d3, "LCD_RD_DATA()"),
    (0, 0xd6f8, "LCD_RD_CTL()"),
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
    Txt(cx[0].m, y.dst, pfx=1, label=False)
    return y

def menuxxx(cx, a):
    s = set()
    for i in range(0, 5):
        y = dataptr(cx, a + i * 2)
        if y.dst not in s:
            s.add(y.dst)
            Txt(cx.m, y.dst, y.dst + 40, label=False)

class MenuPage(data.Data):

    def __init__(self, cx, adr):
        super().__init__(cx.m, adr, adr + 10)
        self.tp = []
        x = cx.m.bu16(adr)
        self.tp.append(Txt(cx.m, x, x + 40, label=False))
        self.tp.append(Txt(cx.m, x + 40, x + 80, label=False))
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

mc6809_prologue = '''
PROLOGUE	a	|1 1 1 1 1 1 0 0|a		|b		|0 0 0 1 0 1 1 1| c		| d		|
PROLOGUE	b	|1 1 0 0 1 1 0 0|a		|b		|0 0 0 1 0 1 1 1| c		| d		|
'''

class mc6809_prologue_ins(assy.Instree_ins):

    def __init__(self, lim, lang):
        super().__init__(lim, lang)
        i = (self['c'] << 8) | self['d']
        i = (self.hi + i) & 0xffff
        if i != 0xfd89:
            raise assy.Invalid("6809 PROLOGUE wrong dest")

    def assy_a(self):
        i = (self['a'] << 8) | self['b']
        self.heap = self.lang.m.bu16(i)
        if self.heap:
            y = data.Const(self.lang.m, i, i + 2, func=self.lang.m.bu16, size=2)
        else:
            y = data.Const(self.lang.m, i, i + 1, size=1)
        return assy.Arg_imm(self.heap)

    def assy_b(self):
        i = (self['a'] << 8) | self['b']
        self.heap = i
        return assy.Arg_imm(self.heap)


mc6809_switches = '''
SWITCH	-	|1 0 0 0 1 1 1 0| a		| b		| 58 | 49 | 6E | 9B |
SWITCH	-	|1 0 0 0 1 1 1 0| a		| b		| 4F | 58 | 49 | 6E | 9B |
'''

class mc6809_switch_ins(assy.Instree_ins):

    def __init__(self, lim, lang):
        super().__init__(lim, lang)
        tbl = self['a'] << 8
        tbl |= self['b']
        if tbl != self.hi:
            raise assy.Invalid("Not a recognized 6809 SWITCH ")
        print("6809SW", lim, tbl - self.hi)
        a = self.hi
        n = 0
        while True:
            if lang.m.occupied(a):
                break
            d = lang.m.bu16(a)
            if d - self.hi > 0x800:
                print("SW", "0x%x" % self.hi, n, "%x" % a, "%x" % d, self.hi - d, lang.m.occupied(a), "BAIL")
                break
            if self.hi - d > 0x800:
                print("SW", "0x%x" % self.hi, n, "%x" % a, "%x" % d, self.hi - d, lang.m.occupied(a), "BAIL")
                break
            #print("SW", "0x%x" % self.hi, n, "%x" % a, "%x" % d, self.hi - d, lang.m.occupied(a))
            y = lang.codeptr(a)
            lang.m.set_label(y.dst, "SWITCH_0x%x_0x%x" % (self.hi, n))
            a += 2
            n += 1
        raise assy.Invalid("6809 SWITCH incomplete")


class mycpu(mc6809.mc6809):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flow_check.append(flow_out_ffed)
        self.add_ins(mc6809_switches, mc6809_switch_ins)
        self.add_ins(mc6809_prologue, mc6809_prologue_ins)

def lcd_config(cx):

    a = 0xea03
    for ch in range(8):
        bm = bitmap.BitMap(8, 8)
        for y in range(8):
            for x in range(8):
                if cx[1].m[a + y] & (1<<x):
                    bm.set(7 - x, y)
        z = data.Data(cx[1].m, a, a + 8, fmt = str(bm))
        a = z.hi

def example():
    rv = []
    m1 = mem.Stackup((FILENAME1,), prefix=DIR)
    m3 = mem.ByteMem(lo=0x0000, hi=0x4000)

    cx = banked.BankedCPU(NPG, mycpu)
    for i in range(NPG):
        cx[i].m.map(m3, 0x0000, 0x4000, shared=True)
        cx[i].m.map(m1, 0x4000, 0x8000, offset=i * 0x4000)
        cx[i].m.map(m1, 0x8000, 0x10000, shared=True, offset=6 * 0x4000)
        rv.append(cx[i].m)

        romsum(cx[i], 0x4000, 0x8000)

    rv.append(m1)

    for b in cx.bank:
        print(b, b.m)
        y = data.Const(b.m, 0x4000, 0x4001)
        y.lcmt = "Bank#"
        y = data.Const(b.m, 0x4001, 0x4002)
        y.lcmt = "Checksum Adjust"

    lcd_config(cx)

    for p, a, t in SYMBOLS:
        cx[p].m.set_label(a, t)

    cx[0].vectors()


    for a, b in (
            (0xee5b, 0xee91),
            (0xef1f, 0xef41),
    ):
        for i in range(a, b, 2):
            y = data.Dataptr(cx[0].m, i, i + 2, cx[0].m.bu16(i))
            Txt(cx[0].m, y.dst, pfx=1, label=False)

    for p, a, b in (
            (1, 0x449a, 0x44aa),
    ):
        for i in range(a, b, 2):
            cx[p].codeptr(i)

    pg0(cx[0])
    pg1(cx[1])

    for a in range(0x514a, 0x519a, 8):
        data.Pstruct(cx[5].m, a, ">d")

    # discover.Discover(cx[0])

    Menu(cx[0], 0x4257, 7)
    Menu(cx[1], 0x437d, 5)
    Menu(cx[2], 0x416b, 4)
    Menu(cx[2], 0x4234, 4)
    Menu(cx[3], 0x4292, 4)
    Menu(cx[4], 0x4172, 4)
    Menu(cx[5], 0x4144, 4)

    ads = set()
    while True:
        l = []
        for p in range(NPG):
            for a, b in cx[p].m.gaps():
                try:
                    if not cx[p].m[a]:
                        a += 1
                    #print("G", p, "0x%x" % a, "0x%x" % b, "0x%04x" % cx[p].m.bu16(a))
                    if cx[p].m[a] in (0xcc, 0xfc,) and cx[p].m[a + 3] == 0x17:
                        j = (p, a)
                        if j not in ads:
                            l.append(j)
                            ads.add(j)
                except mem.MemError:
                    pass
        if not l:
            break
        for p, a in l:
            cx[p].disass(a)
            cx[p].m.set_line_comment(a, "AUTODISC")

    return NAME, rv

if __name__ == '__main__':
    listing.Example(example, ncol=8, pil=False)
