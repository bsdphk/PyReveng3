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
    m.set_block_comment(adr, "Debug Subtable 0x%x" % number)
    data.Const(m, adr, adr+2, fmt="0x%04x")
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

def debug(m):
    b = m[3]
    assert 0 < b < m.hi
    m.set_block_comment(b, "Debug Table")

    data.Const(m, b, b+2, fmt="0x%04x")
    if m[b] != 3:
        return
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

#######################################################################

def segment_file(mb):

    m = mem.WordMem(0, mb.hi >> 1, bits=16, ncol=1)
    for i in range(0, mb.hi, 2):
        m[i >> 1] = (mb[i] << 8) | mb[i + 1]

    cx = r1000.r1000()
    cx.m.map(m, 0)

    for a in range(0, 8):
        data.Const(m, a, fmt="0x%04x")
    m.set_line_comment(0, "Version of machine code")
    m.set_line_comment(1, "Diana Version, RCG Major Version, RCG minor version")
    m.set_line_comment(2, "Zero")
    m.set_line_comment(3, "Offset of debug table")
    m.set_line_comment(4, "Default exception handler - raise instruction")
    m.set_line_comment(5, "Module termination instruction - signal completion")
    m.set_line_comment(6, "Offset to segment table (only in elab segments)")
    m.set_line_comment(7, "0, wired, #pages in seg - 1)")

    cx.subprogram(0xb)

    if m[3] and True:
        try:
            debug(m)
        except mem.MemError:
            m.set_line_comment(3, "XXX DEBUG FAILED")

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
