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

'''Artificial banked memory example
'''

from pyreveng import mem, listing, assy, data, code, discover
import pyreveng.cpu.mc6809 as mc6809
import pyreveng.cpu.banked as banked

NAME = "BankMem"
NPG = 3

def example():
    rv = []
    m1 = mem.ByteMem(0, 256)
    for i in range(256):
        m1[i] = i
    rv.append(m1)

    cx = banked.BankedCPU(NPG, mc6809.mc6809)
    for i in cx.bank:
        i.m.map(m1, lo=0x00, hi=0x20, shared=True)
        i.m.map(m1, lo=0x40, hi=0x60, offset=0x30 + i.bank * 0x20)
        i.m.map(m1, lo=0xd0, hi=0xe0, offset=0xb0)
        i.m.map(m1, lo=0xe0, hi=0xf0, offset=0xb3)
        rv.append(i.m)

    cx[0].m.map(m1, lo=0x80, hi=0x90, offset=0xd0, shared=True)
    cx[1].m.map(m1, lo=0x90, hi=0xa0, offset=0xd0, shared=True)
    cx[2].m.map(m1, lo=0xa0, hi=0xb0, offset=0xd0, shared=True)

    if True:
        m1.set_block_comment(0x00, " 0x00-0x20 Mapped Shared 3x @0x00")
        m1.set_block_comment(0x20, " 0x20-0x30")
        m1.set_block_comment(0x30, " 0x30-0x50 Mapped cx0 @ 0x40")
        m1.set_block_comment(0x50, " 0x50-0x70 Mapped cx1 @ 0x40")
        m1.set_block_comment(0x70, " 0x70-0x90 Mapped cx2 @ 0x40")
        m1.set_block_comment(0x90, " 0x90-0xb0")
        m1.set_block_comment(0xb0, " 0xb0-0xc3 Mapped Shared 3x @0xd0-0xe0 & @+3:0xe0-0xf0")
        m1.set_block_comment(0xc3, " 0xc3-0xd0")
        m1.set_block_comment(0xd0, " 0xd0-0xe0 Mapped Shared cx0@0x80, cx1@0x90, cx2@0xa0")
        m1.set_block_comment(0xe0, " 0xe3-0xff")

    for i in cx.bank:
        for a in range(0, 256, 16):
            b = a + i.bank
            m = "CX[%d][0x%x]" % (i.bank, b)
            #print(i, "%x" % b)
            i.m.set_label(b, m)
            i.m.set_line_comment(b, "C_" + m)
            try:
                y = data.Pstruct(i.m, b, "B")
                y.typ = m
            except mem.MemError:
                pass

    m = [m1]
    m += [x.m for x in cx.bank]
    for i in m:
        a = list(sorted(i.find(lo=0x00, hi=0x100)))
        b = list(sorted(i))
        for x,y in zip(a,b):
            xr = x.render()
            yr = y.render()
            assert xr == yr, "Find(%s) %s %s" % (str(i), xr, yr)
        assert len(a) == len(b), "Find(%s)\n\t%s\n\t%s" % (str(i), str(a), str(b))
        
    return NAME, rv

if __name__ == '__main__':
    listing.Example(example, ncol=8, pil=False)

