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
#
# JSR 0x10284 followed by string 'Words error :_' in DISK_GEOMETRY.M200

from pyreveng import mem, listing, data, assy
import pyreveng.cpu.m68020 as m68020
import pyreveng.cpu.m68000_switches as m68000_switches

FILENAME = "CLI.M200"
BASE = 0x20000

#######################################################################

m200_syscall_desc = '''
SYSJMP		sc		| 4E | F9 | 00 | 01 |
SYSJMP		sc		| 4E | F9 | 80 | 00 |
SYSCALL		sc		| 4E | B9 | 00 | 01 |
SYSCALL		sc		| 4E | B9 | 80 | 00 |
STRING		str		| 43 | FA |
'''

class m200_syscall_ins(m68020.m68020_ins):

    def assy_str(self):
        a = self.lo
        m = self.lang.m
        for o, i in (
            (4, (0x70, 0x72,)),
            (6, (0x10,)),
            (7, (0xd9,)),
            (8, (0x51,)),
            (9, (0xc8, 0xc9,)),
            (10, (0xff,)),
            (11, (0xfc,)),
        ):
            if m[a + o] not in i:
                # print(self, "@%x" % o, i, "0x%x" % m[a + o])
                raise assy.Invalid()
        d = a + 2 + m.bs16(a + 2)
        i = m[a + 5] + 1
        a = self.lo
        m = self.lang.m
        for j in range(d, d + i):
            if not 0x20 <= m[j] <= 0x7e and m[j] not in (9, 10, 12, 13):
                raise assy.Invalid()
        y = data.Txt(m, d, d + i, label=False)
        m.set_line_comment(a, '"' + y.txt + '"')
        raise assy.Invalid()


    def assy_sc(self):
        self.syscall = self.lang.m.bu16(self.hi)
        self.syscall |= self.lang.m.bu16(self.hi - 2) << 16
        self.hi += 2
        j = "syscall_%x" % self.syscall
        if hasattr(self, j):
            return getattr(self, j)()
        if self.lang.m[self.lo + 1] == 0xf9:
            self.flow_J()
        return "0x%x" % self.syscall

    def syscall_10284(self):
        self.flow_J()
        return "0x%x" % self.syscall

    def syscall_10568(self):
        l = self.lang.m[self.hi + 2]
        data.Txt(self.lang.m, self.hi + 3, self.hi + 3 + l, label=False)
        self.flow_J()
        return "0x%x" % self.syscall

class m200_68k(m68020.m68020):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_ins(m200_syscall_desc, m200_syscall_ins)

#######################################################################

def head1_indir(cx, adr):
    if cx.m[adr] != 0x4f:
        return
    adr += 1
    if cx.m[adr] != 0xfa:
        return
    adr += 1
    b = cx.m.bs16(adr)
    cx.disass(adr + b)

def m200_file(m0):

    #cx = m68020.m68020()
    cx = m200_68k()
    m68000_switches.m68000_switches(cx)
    cx.m.map(m0, BASE)

    head = []
    for a in range(BASE, BASE+0x20, 4):
        head.append(cx.dataptr(a))

    for i in (1, 6, 7):
        cx.disass(head[i].dst)
        cx.m.set_label(head[i].dst, "HEAD.%d" % i)

    head1_indir(cx, head[1].dst)

    while True:
        stop = True
        for i, _j in cx.m.gaps():
            if not i & 1 and cx.m.bu16(i) in (
                0x4cdf,
                0x4e56,
                0x4eb9,
            ):
                # print("0x%x" % i, "0x%x" % cx.m.bu16(i))
                cx.m.set_line_comment(i, "(discovered)")
                cx.disass(i)
                stop = False
                break
        if stop:
            break

    return cx

def example():
    m0 = mem.Stackup((FILENAME,), nextto=__file__)
    cx = m200_file(m0)
    return "R1K_M200", (cx.m,)

#######################################################################

if __name__ == '__main__':
    import sys

    if len(sys.argv) == 3:
        mb = mem.Stackup((sys.argv[1],))
        cx = m200_file(mb)
        listing.Listing(cx.m, fn=sys.argv[2], ncol=8, leaf_width=72)
        exit(0)

    listing.Example(example)
