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

'''Rational R1000/400 Ada machine code
'''

from pyreveng import mem, listing, data

import pyreveng.cpu.r1000 as r1000

NAME = "R1000_400_6466568"

FILENAME = "6466568.SEG"

#######################################################################

def debug_table(m, adr, number):
    m.set_block_comment(adr, "Debug3 Subtable 0x%x" % number)
    y = data.Const(m, adr, adr+2, fmt="0x%04x")
    y.typ = ".DBG3TAB"
    neg = m[adr]
    pos = m[adr + 1]
    a = adr + 2
    for i in range(neg + pos):
        data.Const(m, a, a + 2, fmt="0x%04x")
        m.set_line_comment(
            m[a],
            "Debug Table 0x%x.0x%x = 0x%x,0x%x" % (number, i, m[a], m[a+1])
        )
        a += 2

def chain(m, adr):
    m.set_block_comment(adr, "Debug chain")
    y = data.Const(m, adr, adr+2, fmt="0x%04x")
    y.typ = ".DBGLEN"
    n0 = m[adr]
    n1 = m[adr + 1]
    if n0 + n1 == 0:
        return
    adr += 2
    y = data.Const(m, adr, adr+n0+n1, fmt="0x%04x")
    y.typ = ".DBGLNO"
    adr += n0 + n1

def debug(m):
    b = m[3]
    assert 0 < b < m.hi
    m.set_block_comment(b, "Debug Table")

    if m[b] == 3:
        data.Const(m, b, b+2, fmt="0x%04x")
        a = b+2
        for i in range(m[b+1]):
            y = data.Const(m, a, a + 8, fmt="0x%04x")
            y.typ = ".DEBUG"
            spa = m[a]
            #assert (spa & 3) == 3, "0x%x" % spa
            #spa &= ~3
            m.set_line_comment(spa, "Debug Table 0x%x = %s" % (i, y.render()))
            debug_table(m, m[a + 1], i)
            a += 8
    elif m[b] == 4:
        y = data.Const(m, b, b+6, fmt="0x%04x")
        y.typ = ".DEBUG4"
        n = m[b + 5]
        a = b + 6
        for i in range(n):
            y = data.Const(m, a, a+4, fmt="0x%04x")
            y.typ = ".DBG4T"
            c = m[a + 1]
            if c:
                chain(m, c)
            a = a + 4

class StringTable():

    def __init__(self, cx):
        self.cx = cx
        self.lostr = 0xffff
        self.histr = 0x0000
        self.lop = 0xffff
        self.hip = 0x0000

        if not cx.strtabs:
            return

        for y in cx.strtabs.values():
            self.add(y)

        for a in range(self.lop, self.hip):
            if a not in self.cx.strtabs:
                self.add(cx.strtab(a))

        while True:
            i = self.strptr(self.lop - 1)
            #print("SPEC %04x -> %04x -> %04x" % (self.lop - 1, i, i >> 1))
            if i >= self.lostr:
                break
            if (i>>1) < self.hip + 2:
                break
            self.add(cx.strtab(self.lop - 1))

        while self.hip + 2 < self.lostr >> 1:
            i = self.strptr(self.hip + 1)
            if i <= self.histr:
                break
            self.add(cx.strtab(self.hip + 1))

        y = data.Data(cx.m, self.hip + 1, self.hip +2)
        y.rendered = ".STREND 0x%04x->0x%04x" % (cx.m[y.lo], self.strptr(y.lo) >> 1)

        ep = self.hip + 1 + (cx.m[self.hip + 1] >> 1)
        if cx.m[self.hip + 1] & 1:
            ep += 1
        y = data.Data(cx.m, self.lostr >> 1, ep)
        y.compact = True
        y.rendered = ".STRTAB_STRINGS"
        cx.m.set_block_comment(self.lop, "STRING TABLE")

    def add(self, yy):
        self.lop = min(self.lop, yy.lo)
        self.hip = max(self.hip, yy.lo)
        self.lostr = min(self.lostr, yy.strptr)
        self.histr = max(self.histr, yy.strptr)
        #print("ST %04x" % yy.lo, "LOP %04x" % self.lop, "HIP %04x" % self.hip, "LOSTR %04x" % self.lostr)

    def strptr(self, aa):
        return (aa  << 1) + self.cx.m[aa]

#######################################################################

def segment_file(mb):

    m = mem.WordMem(0, mb.hi >> 1, bits=16, ncol=1)
    for i in range(0, mb.hi, 2):
        m[i >> 1] = (mb[i] << 8) | mb[i + 1]

    cx = r1000.r1000()
    cx.m.map(m, 0)

    for a in range(0, 8):
        data.Const(cx.m, a, fmt="0x%04x")
    cx.m.set_line_comment(0, "Version of machine code")
    cx.m.set_line_comment(1, "Diana Version, RCG Major Version, RCG minor version")
    cx.m.set_line_comment(2, "Zero")
    cx.m.set_line_comment(3, "Offset of debug table")
    cx.m.set_line_comment(4, "Default exception handler - raise instruction")
    cx.m.set_line_comment(5, "Module termination instruction - signal completion")
    cx.m.set_line_comment(6, "Offset to segment table (only in elab segments)")
    cx.m.set_line_comment(7, "0, wired, #pages in seg - 1)")
    if cx.m[6]:
        print("NB: ELAB SEGMENT TABLE at 0x%04x" % cx.m[6])
        cx.m.set_block_comment(cx.m[6], "Segment Table")

    cx.subprogram(0xb)

    if cx.m[3] and True:
        try:
            debug(cx.m)
        except mem.MemError:
            m.set_line_comment(3, "XXX DEBUG FAILED")

    StringTable(cx)

    return cx

#######################################################################

def example():
    mb = mem.Stackup((FILENAME,), nextto=__file__)
    cx = segment_file(mb)
    return NAME, (cx.m,)

if __name__ == '__main__':

    import sys

    if len(sys.argv) == 3:
        mb = mem.Stackup((sys.argv[1],))
        cx = segment_file(mb)
        listing.Listing(cx.m, fn=sys.argv[2], ncol=1, leaf_width=72)
        exit(0)

    listing.Example(example, ncol=1)

    if False:
        import glob

        #for fn in sorted(glob.glob("/critter/aa/r1k*/*/*.bin")):
        for fn in sorted(glob.glob("/critter/aa/r1k*/00/*.bin")):
            b = open(fn, "rb").read(131073)
            if len(b) > 131072:
                continue
            if b[0] or b[1] != 0xf or b[2] != 0x58:
                continue
            i = fn.split("/")
            i = "".join(i[-2:])[:-4]
            FILENAME=fn
            NAME=i
            print('=' * 20 + fn + '=' * 20)
            listing.Example(example, ncol=1, leaf_width=72)
