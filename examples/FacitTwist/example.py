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

'''Facit Twist terminal

An example of a large, complex handwritten assembler program.


Appendix 1(8) 4440 MLB CPU, CIRCUIT DIAGRAM  21
-----------------------------------------------

D95 decoder for read:

	0x8000 -> D78 status register
	0xa000 -> D104 ROM
	0xc000 -> RDASCI(L) (5A4)
	0xe000 -> RDATT(L) (6A3)

D93 decoder for write:

	0x0000 -> WREALT(L) (3A3)	AEROM circuits
	0x2000 -> WRBRLT(L) (3A2)	Brightness DAC
	0x4000 -> WRCRTC(L) (2A1)	6845
	0x6000 -> WRSTAT(L) (3A1)	Chargen, bell etc.
	0x8000 -> WRMPRM(L) (4A2)	?
	0xa000 -> WRLTCH(L) (4A4,7A1)	?
	0xc000 -> WRASCI(L) (5A2)	VideoRAM
	0xe000 -> WRATT(L) (6A3)	Attribute Ram ?

'''

from pyreveng import mem, listing, discover, data
import pyreveng.toolchest.chargen as chargen
import pyreveng.cpu.z80 as z80

NAME = "FacitTwist"

FILES = (
    ("F4400_27128_1142_35_90_00.bin", 0xbec5),
    ("F4400_27128_1142_35_80_00.bin", 0xf13b),
    ("F4400_2764_1142_36_00_00.bin", 0xc700),
    ("F4400_2732_1142_55_20_00.bin", 0xbfe9),
    ("F4400_2732_1142_55_10_00.bin", 0xd40c),
)

SYMBOLS = {
    0x0700: "INTR_VECTOR_TABLE",
    0x0700: "INTR_VECTOR_TABLE",
    0x0728: "INTR_SPURIOUS",
    0x4a6c: "SWITCH(A, HL)",
    0x7d2a: "hex_byte(A, DE)",
    0x7d31: "hex_digit(A, DE)",
    0xa0c4: "Init_DART1a_1",
    0xa392: "Init_DART1a_1_DATA",
    0xa0ce: "Init_DART1a_2",
    0xa39e: "Init_DART1a_2_DATA",
    0xac5a: "Init_DART1a_3",
    0xacb0: "Init_DART1a_3_DATA",
    0xadc9: "Init_DART0a",
    0xaddd: "Init_DART0_DATA",
    0xadd3: "Init_DART0b",
    0xc2f9: "menu_struct",
    0xcd1a: "cursor",
    0xc472: "DART_0_WR5_COPY",
    0x5493: "DART_Config(C)",
    0xdf65: "DART_Config_DATA",
    0x549e: "Init_Dart_Config_Data(HL)",
}

IO_SYMBOLS = {
    0xec: "DART1_ad",
    0xed: "DART1_bd",
    0xee: "DART1_ac",
    0xef: "DART1_bc",
    0xf4: "DART0_ad",
    0xf5: "DART0_bd",
    0xf6: "DART0_ac",
    0xf7: "DART0_bc",
    0xf8: "CTC_0",
    0xf9: "CTC_1",
    0xfa: "CTC_2",
    0xfb: "CTC_3",
}

class switch_tbl(data.Data):
    def __init__(self, asp, lo, cpu, func=None):
        self.len = asp[lo]
        hi = lo + 1 + self.len * 3
        super().__init__(asp, lo, hi)
        self.case = []
        for i in range(self.len):
            c = []
            c.append(asp[lo + 1 + i])
            c.append(asp.lu16(lo + 1 + self.len + 2 * i))
            self.case.append(c)
            if func is None:
                cpu.disass(c[1])
            else:
                func(asp, c[1])
            asp.set_label(c[1], "Switch_0x%04x_case_0x%02x" % (self.lo, c[0]))

    def render(self):
        t = ".SWITCH {\n"
        t += "\t.len = %d\n" % self.len
        for i in self.case:
            t += "\t.case 0x%02x -> 0x%04x\n" % (i[0], i[1])
        t += "}"
        return t

class menu_desc(data.Data):
    def __init__(self, cpu, lo):
        cpu.m.set_label(lo, "MENU_%04x" % lo)
        super().__init__(cpu.m, lo, lo + 7)
        self.data = (
            cpu.m[lo],
            cpu.m.lu16(lo + 1),
            cpu.m.lu16(lo + 3),
            cpu.m.lu16(lo + 5),
        )
        n = 6 if self.data[0] == 0x2e else 4
        a = self.data[1]
        b = self.data[3]
        for i in range(n):
            x = switch_tbl(cpu.m, a, cpu)
            a = x.hi
            y = switch_tbl(cpu.m, b, cpu, func=x80stringx3)
            b = y.hi

    def render(self):
        t = ".MENU {\n"
        t += "\t.f0 = 0x%02x\n" % self.data[0]
        t += "\t.f1 = 0x%04x\n" % self.data[1]
        t += "\t.f2 = 0x%04x\n" % self.data[2]
        t += "\t.f3 = 0x%04x\n" % self.data[3]
        t += "}"
        return t

class FTString(data.Data):
    def __init__(self, asp, lo):
        self.asp = asp
        l = []
        hi = lo
        while asp[hi] not in (0x80,):
            l.append(asp[hi])
            hi += 1
        super().__init__(asp, lo, hi + 1)
        m = list(self.resolve(l))
        self.txt = "".join(m)
        self.compact = True

    def resolve(self, l):
        l = list(l)
        while l:
            x = l.pop(0)
            i = self.asp.stringset.get(x)
            if i is not None:
                 yield from self.resolve(i)
            elif 32 <= x <= 126:
                 yield "%c" % x
            elif x == 0x81:
                 yield "┄"
            elif x == 0x82:
                 n1 = l.pop(0)
                 n2 = l.pop(0)
                 yield "«\n\t»\\x%02x(0x%02x%02x)" % (x, n1, n2)
            elif x == 0x83:
                 n1 = l.pop(0)
                 n2 = l.pop(0)
                 yield "\\x%02x(0x%02x, 0x%02x)" % (x, n1, n2)
            elif x == 0x84:
                 n = l.pop(0)
                 yield "«\n\t»\\x%02x(0x%02x)" % (x, n)
            elif x == 0x85:
                 n = l.pop(0)
                 yield "┅" * n
            else:
                 yield "\\x%02x" % x

    def render(self):
        return ".STR\t" + "»" + self.txt + "«"

def x80string(asp, lo):
    #y = data.Txt(asp, lo, term=(0x80,), label=False)
    y = FTString(asp, lo)
    y.compact = False
    return y

def x80stringx3(asp, lo):
    y = FTString(asp, lo)
    y.compact = True
    if asp[y.hi] != 0x80:
	    y = FTString(asp, y.hi)
	    y.compact = True
    if asp[y.hi] != 0x80:
	    y = FTString(asp, y.hi)
	    y.compact = True
    return y

def fc_1028(asp, ins):
    if asp[ins.lo - 3] != 0x11:
        return
    da = asp.lu16(ins.lo - 2)
    ins.lang.disass(da)

def fc_4919(asp, ins):
    if asp[ins.lo - 3] != 0x11:
        return
    da = asp.lu16(ins.lo - 2)
    y = FTString(asp, da)
    y.lcmt = "0x4919_arg"

def fc_4a6c(asp, ins):
    if asp[ins.lo - 3] != 0x21:
        return
    da = asp.lu16(ins.lo - 2)
    switch_tbl(asp, da, ins.lang)

def fc(asp, ins):
    for f in ins.flow_out:
        if f.to == 0x4919:
            fc_4919(asp, ins)
        if f.to in (0x4a6c, 0x517c,):
            fc_4a6c(asp, ins)
        if f.to == 0x1028:
            fc_1028(asp, ins)

def hack(cpu, lo):
    while lo:
        y = cpu.dataptr(lo)
        x = data.Pstruct(cpu.m, lo + 2, "B" * 1, fmt=", ".join(["0x%02x"] * 1))
        #x = data.Txt(cpu.m, lo + 3, term=(0x85,), label=False)
        x = FTString(cpu.m, lo + 3)
        x.compact = True
        x = data.Pstruct(cpu.m, x.hi, "B" * 2, fmt=", ".join(["0x%02x"] * 2))
        x.compact = True
        lo = y.dst


def charrom(m1, m2):
    s = chargen.SVG_Charset(
        "/tmp/_" + NAME + "_chargen.svg",
        cols=8,
        char_w=16,
        char_h=32,
        imargin=1,
        linewidth=1,
    )
    for i in range(128):
        l = []
        for j in range(0, 32):
            x = m1[i * 32 + j]
            y = m2[i * 32 + j]
            a = 0
            b = 0x80
            while b:
                a = a << 2
                a |= 2 if y & b else 0
                a |= 1 if x & b else 0
                b = b >> 1
            l.append(a)
        s.set_char(i // 16, i % 16, l)
    s.render()

def example():
    m = []
    for fn, csum in FILES:
        i = mem.Stackup(files=(fn,), nextto=__file__,)
        assert sum(i.bytearray(i.lo, i.hi)) & 0xffff == csum
        m.append(i)


    charrom(m[3], m[4])

    cpu = z80.z80()
    cpu.m.map(m[0], 0x0000)
    cpu.m.map(m[1], 0x4000)
    cpu.m.map(m[2], 0xa000)

    cpu.flow_check.append(fc)

    cpu.stringset = {}
    cpu.m.stringset = cpu.stringset

    r1 = 0x85a # Keypad
    r1 = 0x864 # Keypad
    r2 = 0xb2
    o1 = r1 - r2 * 2
    o2 = r1 + r2 * 2
    print("O1", hex(o1), "O2", hex(o2))
    for a in range(0x0810, 0x0900, 2):
        x = cpu.dataptr(a)
        y = data.Txt(cpu.m, x.dst, term=(0x81,), label=False)
        w = (a - o1) // 2
        cpu.stringset[w] = [cpu.m[x] for x in range(y.lo, y.hi)]
        x.lcmt = "0x%02x  " % ((a - o1) // 2)
        x.lcmt += y.txt

    for a, b in SYMBOLS.items():
        cpu.m.set_label(a, b)

    for a, b in IO_SYMBOLS.items():
        cpu.as_io.set_label(a, b)

    for a in range(0x3d, 0x60, 2):
        x = cpu.codeptr(a)
        cpu.m.set_line_comment(x.dst, "From tbl@0x003d")

    for a in range(0x0700, 0x0728, 2):
        x = cpu.codeptr(a)
        n = (a - 0x700) 
        if x.dst != 0x728:
            cpu.m.set_label(x.dst, "IRQ_VEC_%02x" % n)
        cpu.m.set_line_comment(x.dst, "From tbl@0x0700")

    for a in range(0x0800, 0x0810, 2):
        x = cpu.codeptr(a)
        n = (a - 0x800) // 2
        cpu.m.set_label(x.dst, "Str_%02x_Handler" % (0x80 + n))

    for a in range(0x0900, 0x0908, 2):
        x = cpu.codeptr(a)
        cpu.m.set_line_comment(x.dst, "From tbl@0x0900")

    for a in range(0xe00, 0xfa0, 2):
        x = cpu.codeptr(a)
        cpu.m.set_line_comment(x.dst, "From tbl@0x0e00")

    for a in range(0x0a45, 0x0be3, 2):
        x = cpu.dataptr(a)
        #y = data.Txt(cpu.m, x.dst, term=(0x80,), label=False)
        y = FTString(cpu.m, x.dst)
        x.lcmt = y.txt

    for a in range(0x3bb1, 0x3bd1, 2):
        x = cpu.dataptr(a)
        cpu.m.set_label(x.dst, "KBD_%x" % a)
        for i in range(29):
            try:
                y = data.Pstruct(cpu.m, x.dst + i * 5, "B" * 5, fmt=", ".join(["0x%02x"] * 5))
                y.compact = True
            except:
                pass

    hack(cpu, 0x264b)

    a = 0xa51a
    b = 0xa539
    while cpu.m[a] != 0xff:
        x = data.Pstruct(cpu.m, a, "BBB", fmt=", ".join(["0x%02x"] * 3))
        a = x.hi
        y = data.Txt(cpu.m, b, b + 0x1e, label=False)
        b = y.hi
    data.Const(cpu.m, a, a + 1)

    x = data.Pstruct(cpu.m, 0x54a7, "B" * 12, fmt=", ".join(["0x%02x"] * 12))
    x = data.Pstruct(cpu.m, 0x54b3, "B" * 12, fmt=", ".join(["0x%02x"] * 12))
    x = data.Pstruct(cpu.m, 0xaddd, "B" * 12, fmt=", ".join(["0x%02x"] * 12))
    x = data.Pstruct(cpu.m, 0xa392, "B" * 12, fmt=", ".join(["0x%02x"] * 12))
    x = data.Pstruct(cpu.m, 0xa39e, "B" * 12, fmt=", ".join(["0x%02x"] * 12))
    x = data.Pstruct(cpu.m, 0xacb0, "B" * 10, fmt=", ".join(["0x%02x"] * 10))

    cpu.m.set_label(0xa2c4, "TestNames")
    for a in range(0xa2c4, 0xa384, 0x10):
        x = data.Txt(cpu.m, a, a + 0x10, label=False)

    for a in range(0xade9, 0xae21, 7):
        x = data.Txt(cpu.m, a, a + 0x7, label=True)

    menu_desc(cpu, 0x7103)
    menu_desc(cpu, 0x742b)
    menu_desc(cpu, 0x7689)

    for a, l in (
            (0xa384, 0x7),
            (0xa38b, 0x7),
            (0xae21, 0xa),
            (0xae2c, 0xc),
            (0xae38, 0x7),
            (0xae40, 0x9),
            (0xae4a, 0xa),
            (0xae54, 0xb),
            (0xae5f, 0xf),
            (0xae6f, 0x7),
            (0xae76, 0xb),
            (0xae81, 0x7),
    ):
        x = data.Txt(cpu.m, a, a + l)

    cpu.vectors(
        (
            "RESET",
            "RST08",
            "RST10",
            "RST18",
            "RST28",
            "IRQ",
            "NMI",
        )
    )

    # switch_tbl(cpu.m, 0x0dc0, cpu)
    switch_tbl(cpu.m, 0x32f8, cpu)
    switch_tbl(cpu.m, 0x334a, cpu)
    switch_tbl(cpu.m, 0x33c1, cpu)
    switch_tbl(cpu.m, 0x5328, cpu)
    switch_tbl(cpu.m, 0x5383, cpu)
    switch_tbl(cpu.m, 0x53b9, cpu)
    switch_tbl(cpu.m, 0x53a2, cpu)
    switch_tbl(cpu.m, 0x53af, cpu)

    for a in range(0x789b, 0x78bb, 2):
        y = cpu.dataptr(a)
        FTString(cpu.m, y.dst)

    for a in (
            0x0915,
            0x0cbe,
            0x7926,
            0x7cf7,
            0x7d03,
            0x6fba,
            0x6fd1,
            0x6fd5,
            0x6fdf,
    ):
        y = FTString(cpu.m, a)
        y.lcmt = "MANUAL"

    a = 0x600
    while a < 0x67e:
        y = FTString(cpu.m, a)
        a = y.hi

    if False:
        # See 0x43cc
        for a in range(0x3d, 0x58, 2):
            y = cpu.codeptr(a)
            cpu.m.set_line_comment(y.dst, "MANUAL from tbl@0x3c")

    data.Pstruct(cpu.m, 0x89, "2B", fmt=", ".join(["0x%02x"] * 2))
    for a in range(0x524, 0x56c, 4):
        data.Pstruct(cpu.m, a, "4B", fmt=", ".join(["0x%02x"] * 4))

    for a, b in (
            (0x008b, "via IY"),
            (0x04f6, "via IY"),
            (0x0506, "via IY"),
            (0x0518, "via IY"),
            (0x0fc7, "via xfa0"),
            (0x0fe5, "via xfa0"),
            (0x1006, "via xfa0"),
            (0x1397, None),
            (0x5c03, "via 0xc296"),
            (0x5df9, "via 0xc296"),
            (0x5e25, "via 0xc296"),
            (0x5ecb, "via 0xc296"),
            (0x5f7f, "via 0xc296"),
            (0x5fbc, "via 0xc296"),
            (0xac5a, None),
            (0xb800, None),
            (0xb874, "via 0xc1da ptr"),
            (0xb8db, "via 0xc1d8 ptr"),
            (0xb8e2, "via 0xc1d8 ptr"),
            (0xb8e9, "via 0xc1d8 ptr"),
            (0xb8f0, "via 0xc1d8 ptr"),
            (0xb8f7, "via 0xc1d8 ptr"),
            (0xb844, None),
            (0x3916, "via 0xcf58 ptr"),
            (0x3936, "via 0xcf58 ptr"),
            (0x3948, "via 0xcf58 ptr"),
            (0x39d8, "via 0xcf58 ptr"),
            (0x39b4, "DART: Reset ext/status interrupts"),
            (0x3a47, "DART: Error Reset"),
            (0x3a52, "DART: RAISE DTR"),
            (0x3a79, "DART: LOWER DTR"),
            (0x3ab7, "DART: RAISE RTS"),
            (0x3ae1, "DART: Reset ext/status interrupts"),
            (0x3b02, "DART: Reset ext/status interrupts"),
            (0x3b16, "DART: Reset ext/status interrupts"),
            (0x4621, "DART: FLIP DTR ?"),
            (0xac5d, "DART1_ac"),
            (0xadc9, "DART0_ac"),
            (0xadd3, "DART0_bc"),
            (0xa0c7, "DART1_ac"),
            (0xa0d1, "DART1_ac"),
            (0x5466, "DART1_bc"),
            (0x546b, "DART1_ac"),
    ):
        cpu.disass(a)
        if not b:
            b = "MANUAL"
        cpu.m.set_line_comment(a, b)

    y = data.Data(cpu.m, 0x4707, 0x4707 + 0x15e)

    cpu.m.set_block_comment(0x4919, 'String Expansion(HL=dst, DE=src)')
    cpu.m.set_label(0x4919, "ExpandString(dst=HL,src=DE)")
    cpu.m.set_block_comment(0x493f, '0x80 End')
    cpu.m.set_block_comment(0x4942, '0x81 Pop level')
    cpu.m.set_block_comment(0x4947, '0x84[1] ??')
    cpu.m.set_block_comment(0x4951, '0x83[2] ??')
    cpu.m.set_block_comment(0x4968, '0x82[2] Move to new destination address')
    cpu.m.set_block_comment(0x496f, '0x85[1] Repeat space')
    cpu.m.set_block_comment(0x497b, '0x86 Reset (u/l?) mode')
    cpu.m.set_block_comment(0x4980, '0x87 Backspace')

    cpu.m.set_label(0x4919, "ExpandString(dst=HL,src=DE)")

    cpu.m.set_block_comment(0xb9a5, 'Send break ?')
    cpu.m.set_block_comment(0xb9c6, 'Clear RTS ?')

    if False:
        discover.Discover(cpu)

    return NAME, (cpu.m,)


if __name__ == '__main__':
    listing.Example(example)
