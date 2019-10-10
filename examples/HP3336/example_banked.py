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

'''HP3336 Synthesizer/Level Generator
'''

from pyreveng import mem, listing, assy, data
import pyreveng.cpu.hp_nanoproc as hp_nanoproc
import pyreveng.cpu.banked as banked

import common

NAME = "HP3336_BANKED"
FILENAME = "hp3336.bin"

#######################################################################

hp_nanoproc_pg_desc = '''
LJMP pgadr,>J |1 1 0 0 1 0 0 0|0 0 1 1 0| pgno|1 0 0 0|0| ahi | alo           |
LRET >R	      |0 1 1 0 1 1 1 1|0 1 0 1 1 0 0 0|1 0 1 1 1 0 0 0|
MCTL  mctl    |1 1 0 0 1 0 0 0| mctl          |
'''

class hp_nanoproc_pg_ins(assy.Instree_ins):

    def assy_pgadr(self):
        self.dst_pg = self['pgno']
        self.dst_off = (self['ahi']<<8) | self['alo']
        self.lang[self.dst_pg].m.set_block_comment(self.dst_off, "LJMP target from " + self.lang.m.afmt(self.lo))
        self.lang[self.dst_pg].disass(self.dst_off)
        return assy.Arg_dst(self.lang[self.dst_pg].m, self.dst_off)

    def assy_mctl(self):
        self.mctl = self['mctl']
        l = list()
        if self.mctl & 0x10:
            l.append("RMA")
        if self.mctl & 0x20:
            l.append("RMB")
        if self.mctl & 0x40:
            l.append("IN")
        if self.mctl & 0x80:
            l.append("UP")
        pg = self.lo >> 11
        npg = self.mctl & 7
        if pg != npg:
            l.append("%x" % npg)
        return "+".join(l)

#########################################################################

JMPTABLES = [
    [1, 0x780, 0x7a8, 4, "1:501", "1:502", " - LED Segment Table"],
    [1, 0x7a8, 0x7c0, 2, "1:2b2", "None", ""],
    [1, 0x7c0, 0x7e0, 4, "1:33b", "1:33c", ""],
    [1, 0x7e0, 0x800, 4, "1:362", "1:363", ""],
    [3, 0x040, 0x078, 8, "3:2a0", "3:2a1", ""],
    [5, 0x7b8, 0x800, 8, "5:1f9", "5:1fa", ""],
    [7, 0x7d8, 0x800, 4, "7:437", "RET", ""],
]

def jmptables(cx):
    for pg, lo, hi, wid, fm, to, desc in JMPTABLES:
        if lo == 0x7e0:
            data.Range(cx[pg].m, lo, hi, "Jump table")
        for a in range(lo, hi, wid):
            cx[pg].disass(a)
        cx[pg].m.set_block_comment(
            lo,
            "From %s," % fm + " To %s" % to + desc
        )

def pagejumps(cx):
    '''You are not supposed to understand this'''
    for a in range(0x004, 0x020, 4):
        y = cx[0].disass(a)
        y = cx[0].m.find_lo(a)[0]
        print("PGJ %x" % a, y)
        fnn = "DISP_%d" % (a // 4)
        cx[y.dst_pg].m.set_label(y.dst_off, fnn)
        for b in range(0, y.dst_off, 2):
            z = cx[y.dst_pg].disass(b)
            z = cx[y.dst_pg].m.find_lo(b)[0]
            cx[y.dst_pg].m.set_label(z.dstadr, "FN%d_%d" % (y.dst_pg, b // 2))

#########################################################################

def example():
    m = mem.Stackup((FILENAME,), nextto=__file__)
    m.name = "EPROM"

    cx = banked.BankedCPU(8, hp_nanoproc.hp_nanoproc)
    cx.add_ins(hp_nanoproc_pg_desc, hp_nanoproc_pg_ins)

    l = [m]
    for p in range(8):
        cx[p].m.map(m, 0x000, 0x7ff, offset=p * 0x800)
        l.append(cx[p].m)

    for i, j in common.SYMBOLS.items():
        pg = i >> 11
        off = i & 0x7ff
        cx[pg].m.set_label(off, j)

    cx[0].disass(0x000)
    cx[0].disass(0x0ff)

    jmptables(cx)

    pagejumps(cx)

    return NAME, l

if __name__ == '__main__':
    listing.Example(example)
