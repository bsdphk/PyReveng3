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

'''HP1345 - Built-in Diagnostic processor
'''

from pyreveng import mem, listing
import pyreveng.cpu.mcs48 as mcs48
import pyreveng.cpu.hp1345a as hp1345a
import pyreveng.cpu.hp1345_render as hp1345_render

NAME = "HP1345A"

FILENAME = "01347-80010.bin"

SYMBOLS = {
    0x00a: "reset",
    0x010: "int",
    0x014: "tint",
    0x017: "RESET_TIMER",
    0x01d: "R1d",
    0x032: "MEMTST",
    0x048: "048",
    0x06e: "06e",
    0x0a1: "Ra1",
    0x0ac: "0ac",
    0x0c2: "0c2",
    0x0d2: "0d2",
    0x0d6: "0d6",
    0x0de: "0de",
    0x0ea: "0ea",
    0x100: "ALIGN",
    0x200: "ALIGN2",
    0x300: "FOCUS",
}

#######################################################################

def example():
    m = mem.Stackup((FILENAME,), nextto=__file__)
    cx = mcs48.i8748()
    cx.m.map(m, 0)

    for a, b in SYMBOLS.items():
        cx.m.set_label(a, b)

    gpu = hp1345a.hp1345a()

    cx.vectors()

    l = []
    for a in range(0x122, 0x200, 2):
        l.append(cx.m.bu16(a))
        gpu.disass(a, cx.m)

    for a in range(0x222, 0x2c8, 2):
        l.append(cx.m.bu16(a))
        gpu.disass(a, cx.m)

    hp1345_render.svg(cx.m, 0x122, 0x2c8, l=l)

    for a in range(0x31e, 0x400, 2):
        gpu.disass(a, cx.m)
    hp1345_render.svg(cx.m, 0x31e, 0x400)

    return NAME, (cx.m,)

if __name__ == '__main__':
    listing.Example(example)
