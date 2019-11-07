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
    0x4a6c: "SWITCH(A, HL)",
    0x7d2a: "hex_byte(A, DE)",
    0x7d31: "hex_digit(A, DE)",
    0xa0c4: "Init_DART_1_c_1",
    0xa0ce: "Init_DART_1_c_2",
    0xac5a: "Init_DART_1_c_3",
    0xadc9: "Init_DART_0_c",
    0xadd3: "Init_DART_0_d",
    0xc2f9: "menu_struct",
    0xcd1a: "cursor",
}

IO_SYMBOLS = {
    0xec: "DART_1_a",
    0xee: "DART_1_c",
    0xf4: "DART_0_a",
    0xf5: "DART_0_b",
    0xf6: "DART_0_c",
    0xf7: "DART_0_d",
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
            y = switch_tbl(cpu.m, b, cpu, func=x80string)
            b = y.hi

    def render(self):
        t = ".MENU {\n"
        t += "\t.f0 = 0x%02x\n" % self.data[0]
        t += "\t.f1 = 0x%04x\n" % self.data[1]
        t += "\t.f2 = 0x%04x\n" % self.data[2]
        t += "\t.f3 = 0x%04x\n" % self.data[3]
        t += "}"
        return t

def x80string(asp, lo):
    y = data.Txt(asp, lo, term=(0x80,), label=False)
    y.compact = False
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
    y = data.Txt(asp, da, term=(0x80, 0x85), label=False)
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
        x = data.Txt(cpu.m, lo + 3, term=(0x85,), label=False)
        x.compact = True
        x = data.Pstruct(cpu.m, x.hi, "B" * 2, fmt=", ".join(["0x%02x"] * 2))
        x.compact = True
        lo = y.dst


def charrom_big(m1, m2):
    s = chargen.SVG_Charset(
        "/tmp/_" + NAME + "_chargen_big.svg",
        cols=8,
        char_w=15,
        char_h=20,
        imargin=1,
        linewidth=1,
    )
    for i in range(128):
        l = []
        for j in range(8, 28):
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

def charrom_small(m1, m2):
    s = chargen.SVG_Charset(
        "/tmp/_" + NAME + "_chargen_small.svg",
        cols=8,
        char_w=15,
        char_h=6,
        imargin=1,
        linewidth=1,
    )
    for i in range(128):
        l = []
        for j in range(0, 6):
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

    charrom_big(m[3], m[4])
    charrom_small(m[3], m[4])

    cpu = z80.z80()
    cpu.m.map(m[0], 0x0000)
    cpu.m.map(m[1], 0x4000)
    cpu.m.map(m[2], 0xa000)

    cpu.flow_check.append(fc)

    for a, b in SYMBOLS.items():
        cpu.m.set_label(a, b)

    for a, b in IO_SYMBOLS.items():
        cpu.as_io.set_label(a, b)

    for a in range(0x3d, 0x60, 2):
        x = cpu.codeptr(a)
        cpu.m.set_line_comment(x.dst, "From tbl@0x003d")

    for a in range(0x0700, 0x0728, 2):
        x = cpu.codeptr(a)
        cpu.m.set_line_comment(x.dst, "From tbl@0x0700")

    for a in range(0x0800, 0x0810, 2):
        x = cpu.codeptr(a)
        cpu.m.set_line_comment(x.dst, "From tbl@0x0800")

    for a in range(0x0900, 0x0908, 2):
        x = cpu.codeptr(a)
        cpu.m.set_line_comment(x.dst, "From tbl@0x0900")

    for a in range(0xe00, 0xfa0, 2):
        x = cpu.codeptr(a)
        cpu.m.set_line_comment(x.dst, "From tbl@0x0e00")

    for a in range(0x0810, 0x0900, 2):
        x = cpu.dataptr(a)
        y = data.Txt(cpu.m, x.dst, term=(0x81,), label=False)
        x.lcmt = y.txt

    for a in range(0x0a45, 0x0be3, 2):
        x = cpu.dataptr(a)
        y = data.Txt(cpu.m, x.dst, term=(0x80,), label=False)
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
        data.Txt(cpu.m, y.dst, term=(0x80,))

    for a in (
            0x7926,
            0x7cf7,
            0x7d03,
    ):
        data.Txt(cpu.m, a, term=(0x80,))

    if False:
        # See 0x43cc
        for a in range(0x3d, 0x58, 2):
            y = cpu.codeptr(a)
            cpu.m.set_line_comment(y.dst, "MANUAL from tbl@0x3c")

    if False:
        # See 0x493e
        for a in range(0x800, 0x900, 2):
            y = cpu.codeptr(a)
            cpu.m.set_line_comment(y.dst, "MANUAL from tbl@0x800")

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
    ):
        cpu.disass(a)
        if not b:
            b = "MANUAL"
        cpu.m.set_line_comment(a, b)

    y = data.Data(cpu.m, 0x4707, 0x4707 + 0x15e)

    if False:
        discover.Discover(cpu)

    return NAME, (cpu.m,)


if __name__ == '__main__':
    listing.Example(example)
