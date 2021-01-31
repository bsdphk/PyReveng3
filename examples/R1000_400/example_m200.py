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

'''
   DFS .M200 binary files
   ----------------------
'''

from pyreveng import mem, listing
import pyreveng.cpu.m68020 as m68020
import pyreveng.cpu.m68000_switches as m68000_switches

import m200_pushtxt
import m200_syscall

FILENAME = "CLI.M200"
BASE = 0x20000

def head1_indir(cx, adr):
    if cx.m[adr] != 0x4f:
        return
    adr += 1
    if cx.m[adr] != 0xfa:
        return
    adr += 1
    b = cx.m.bs16(adr)
    cx.disass(adr + b)

def m200_file(m0, _ident=None):
    ''' A generic .M200 file '''
    cx = m68020.m68020()
    m68000_switches.m68000_switches(cx)
    m200_syscall.add_syscall(cx)
    m200_pushtxt.add_pushtxt(cx)
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
    ''' Follow the example protocol '''
    m0 = mem.Stackup((FILENAME,), nextto=__file__)
    cx = m200_file(m0)
    return "R1K_M200", (cx.m,)

#######################################################################

if __name__ == '__main__':
    import sys

    if len(sys.argv) == 5 and sys.argv[1] == "-AutoArchaeologist":
        mb = mem.Stackup((sys.argv[3],))
        cx = m200_file(mb, sys.argv[2])
        listing.Listing(cx.m, fn=sys.argv[4], ncol=8, leaf_width=72)
        exit(0)

    listing.Example(example)
