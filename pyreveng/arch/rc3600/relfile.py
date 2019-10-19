#!/usr/bin/env python
#
# Copyright (c) 2019 Poul-Henning Kamp <phk@phk.freebsd.dk>
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
#

'''DOMUS Relocatable Files

Documentation:
    RCSL-42-I-833 DOMAC Domus Macro Assembler User's Guide
'''

from pyreveng import data, mem

RELOC = {
    1: " ",
    2: "'",
    3: '"',
    7: '*',
}

def b40(x):
    ''' See RCSL-42-I-833 appendix D '''
    t = ""
    c = "_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ.?/"
    for i in (x[1] >> 5, x[0]):
        while i:
            t += c[i % 40]
            i //= 40
    return '"' + t[::-1] + '"'

class DomusMem(mem.WordMem):

    def __init__(self, lo, hi, reloc, **kwargs):
        super().__init__(lo, hi, bits=16, attr=3)
        self.reloc = reloc
        self.apct += RELOC[self.reloc]

    def afmt(self, adr):
        return "%04x" % adr + RELOC[self.reloc]

    def dfmt(self, adr):
        try:
            return "%04x" % self[adr] + RELOC[self.get_attr(adr)]
        except mem.MemError:
            return "---- "

class RelocRecord():

    ''' See RCSL-42-I-833 appendix C '''

    def __init__(self):
        self.words = []
        self.lo = None
        self.hi = None

    def __repr__(self):
        return "<REL " + " ".join(self.render()) + ">"

    def render(self):
        ''' Render record as list of text fields '''
        rv = []
        rv.append("%x" % self.words[0])
        rv.append("%3d" % (self.words[1] - 65536))
        for i in self.words[2:5]:
            rv.append("%05o" % (i >> 1))
        for i in self.words[5:]:
            rv.append("%04x" % i)
        return rv

    def relrec(self):
        ''' Render record as pseudo DOMAC statement '''
        return ".RELREC\t" + ",".join(self.render())

    def reloc(self, n):
        v = self.words[6 + n]
        r = self.words[2 + n // 5]
        r >>= 1 + 3 * (4 - n % 5)
        return r & 7, v

    def from_asp(self, asp, lo, wfunc=None, render=True):
        ''' Read record from address-space '''
        if not wfunc:
            wfunc = asp.lu16
        while not asp[lo]:
            lo += 1
        self.lo = lo
        for i in range(6):
            self.words.append(wfunc(lo))
            lo += 2
        for i in range(self.words[1], 65536):
            self.words.append(wfunc(lo))
            lo += 2
        if sum(self.words) & 0xffff:
            raise Exception("Checksum error")
        self.hi = lo
        if render:
            y = data.Data(asp, self.lo, self.hi)
            y.rendered = self.relrec()
            y.compact = True
            if self.words[0] == 7:
                y.lcmt = b40(self.words[6:8])
        return self, lo

class RelocFile():
    ''' One Relocatable Object File '''

    def __init__(self):
        self.recs = []

    def __iter__(self):
        for i in self.recs:
            yield i

    def from_asp(self, asp, lo, hi=None, render=True, **kwargs):
        ''' Read object file from address space '''
        while True:
            y, lo = RelocRecord().from_asp(asp, lo, **kwargs)
            self.recs.append(y)
            if hi and lo >= hi:
                break
            if self.recs[-1].words[0] == 6:
                break
        if render:
            ttl = self.title()
            if not ttl:
                ttl = "without .TITL record"
            asp.set_block_comment(
                self.recs[0].lo,
                "Relocatable Object " + ttl
            )
        return self, lo

    def title(self):
        ''' .TITL record, if any '''
        for i in self:
            if i.words[0] == 7:
                return b40(i.words[6:8])
        return None

    def start_address(self):
        ''' .END record, if any (reloc + number) '''
        if not self.recs or self.recs[-1].words[0] != 6:
            return None
        return self.recs[-1].reloc(0)

    def load(self, cpu):
        ''' Load object into cpu address space '''
        OFF = {
            1: 0x0000,
            2: 0x3000,
            7: 0x9000
        }
        OFF[3] = OFF[2] << 1
        lo = [1<<16] * 8
        hi = [0] * 8
        for i in self.recs:
            if i.words[0] != 2 or len(i.words) < 8:
                continue
            x, y = i.reloc(0)
            lo[x] = min(lo[x], y)
            hi[x] = max(hi[x], y + len(i.words) - 7)
        for i in (0, 4, 5, 6):
            assert lo[i] > hi[i]
        lo[2] = min(lo[2], lo[3] >> 1)
        hi[2] = max(hi[2], hi[3] >> 1)
        for i in (1, 2, 7):
            if lo[i] < hi[i]:
                mn = DomusMem(0, hi[i] - lo[i], i)
                cpu.m.map(mn, OFF[i] + lo[i])
        for i in self.recs:
            if i.words[0] != 2:
                continue
            ar, adr = i.reloc(0)
            adr += OFF[ar]
            for j in range(1, len(i.words) - 6):
                x, y = i.reloc(j)
                cpu.m[adr] = y + OFF[x]
                cpu.m.set_attr(adr, x)
                adr += 1
