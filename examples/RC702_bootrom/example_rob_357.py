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

'''Regnecentralen Piccolo - RC702 boot EPROM
'''

from pyreveng import mem, listing, data
import pyreveng.cpu.z80 as z80

NAME = "RC702_bootrom_rob_357"

FILENAME = "EPROM_ROB_357.bin"

def example():
    cx = z80.z80()
    m = mem.Stackup(files=(FILENAME,), nextto=__file__)
    cx.m.map(m, 0, 0x12)
    cx.m.map(m, lo=0xa000, hi=0xa59a, offset=0x12)

    data.Txt(cx.m, 0xa533, label=False)
    data.Txt(cx.m, 0xa546, label=False)
    data.Txt(cx.m, 0xa571, label=False)
    data.Txt(cx.m, 0xa574, label=False)
    data.Txt(cx.m, 0xa588, 0xa58c, label=False)
    data.Txt(cx.m, 0xa58c, 0xa590, label=False)
    data.Txt(cx.m, 0xa593, 0xa593 + 0x7, label=False)

    cx.disass(0x0000)

    # Interrupt vector table
    for a in range(12):
        cx.codeptr(0xa000 + a * 2)

    return NAME, (cx.m,)

if __name__ == '__main__':
    listing.Example(example)
