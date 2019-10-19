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

'''II Morrow Apollo 618C Loran - Navigation Processor
'''

from pyreveng import mem, data, listing
import pyreveng.cpu.i8086 as i8086

NAME = "Apollo618c"

FILENAME = "618TCA_R_U2_C_U15_PN_138_0193_V4_4.bin"

SYMBOLS = {
}

def example():
    m = mem.Stackup((FILENAME,), nextto=__file__)
    cx = i8086.i8086()
    cx.has_8087()
    cx.m.map(m, 0xe0000)

    cx.disass(0xffff0)

    def vect(seg, off):
        a = (seg << 4) + off
        # print("VECTOR %05x" % a)
        cx.disass(a)
        cx.m.set_label(a, "VECTOR")

    # Vectors initialized at 0xe21b2...
    vect(0xe000, 0x1e67)
    vect(0xe1f5, 0x35e9)
    vect(0xe737, 0x1fdf)
    vect(0xf8bd, 0x417b)

    #######################################################################
    # Random guesses

    if False:
        cx.disass(0xe63cf)
        cx.disass(0xe7bd7)
        cx.disass(0xe7fdd)
        cx.disass(0xe834c)
        cx.disass(0xe9251)
        cx.disass(0xfcd68)
        cx.disass(0xffb56)

    #######################################################################

    def txl(seg, a):
        for i in range(2, 0x22, 2):
            x = cx.m.lu16(a + i)
            #print("%04x" % seg, i, "%05x" % (a + i), "%04x" % x, "%05x" % (seg * 16 + x))
            y = data.Codeptr(cx.m, a + i, a + i + 2, seg*16+x)

    txl(0xff1b, 0xffe00)
    txl(0xff1b, 0xffe22)
    txl(0xff1b, 0xffe44)
    txl(0xff1b, 0xffe66)
    txl(0xff1b, 0xffe88)
    txl(0xff1b, 0xffeaa)

    ###################################################################

    def tbl(seg, off_lo, off_hi):
        cx.m.add_range(off_lo, off_hi, "%04x-jmp-tbl" % seg)
        for i in range(off_lo, off_hi, 2):
            off = cx.m.lu16(i)
            a = (seg << 4) + off
            x = data.Codeptr(cx.m, i, i + 2, a)
            cx.disass(a)

    def tbl2(a):
        assert cx.m[a + 0] == 0x2e
        assert cx.m[a + 1] == 0xff
        assert cx.m[a + 2] == 0xa7
        o = cx.m.lu16(a + 3)
        s = (a + 5 - o)
        #print("T2", "seg", "%05x" % s, "off", "%04x" % o)
        e = o + s
        l = 0xfffff
        while e < l:
            n = cx.m.lu16(e)
            if s + n < l:
                l = s + n
            # print("e %05x" % e, "l %05x" % l, "n %04x -> %05x" % (n, s + n))
            e += 2
        tbl(s >> 4, o + s, e)

    t2dict = {}

    more = True

    while more:
        more = False
        for i in cx.m:
            if i.tag != "i8086":
                continue
            if i.lo in t2dict:
                continue
            if cx.m[i.lo + 0] != 0x2e:
                continue
            if cx.m[i.lo + 1] != 0xff:
                continue
            if cx.m[i.lo + 2] != 0xa7:
                continue
            t2dict[i.lo] = True
            tbl2(i.lo)
            more = True

    #######################################################################

    more = False
    while more:
        more = False
        for lo, hi in cx.m.gaps():
            if lo + 1 == hi:
                continue
            if cx.m[lo] == 0x55:
                print("%04x, %04x" % (lo, hi))
                cx.disass(lo)
                more = True
            elif cx.m[lo] == 0x00 and cx.m[lo + 1] == 0x55:
                print("%04x, %04x" % (lo, hi))
                cx.disass(lo + 1)
                more = True


    #######################################################################

    def text_lines(cx, a):
        # cx.m.set_line_comment(a, "txt-tbl")
        cx.m.add_range(a, a + 24, "text-tbl")
        data.Txt(cx.m, a, a + 8, label=False)
        data.Txt(cx.m, a + 8, a + 16, label=False)
        data.Txt(cx.m, a + 16, a + 24, label=False)

    text_lines(cx, 0xe57e0 + 0x1f0)
    text_lines(cx, 0xe57e0 + 0x208)
    text_lines(cx, 0xe57e0 + 0x220)

    text_lines(cx, 0xe68d0)
    text_lines(cx, 0xe68e8)
    text_lines(cx, 0xe6900)

    #######################################################################

    return NAME, (cx.m,)


if __name__ == '__main__':
    listing.Example(example)
