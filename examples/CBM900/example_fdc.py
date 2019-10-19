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

'''Commodore CBM900 - Floppy controller

See also: https://datamuseum.dk/wiki/Commodore/CBM900
'''

from pyreveng import mem, data, listing
import pyreveng.cpu.mos6500 as mos6500

NAME = "CBM900_FDC"

FILENAME = "EPROM_Z8000_Fl.Cont._S41_6-20-85.bin"

SYMBOLS = {
    0xe7bf: "GEOMETRY",
    0xe80a: "STEPPER_PHASE",
}

def example():
    m = mem.Stackup((FILENAME,), nextto=__file__)
    cx = mos6500.mos6500()
    cx.m.map(m, 0xe000)

    for a, b in SYMBOLS.items():
        cx.m.set_label(a, b)

    for i in range(7):
        data.Const(cx.m, 0xe28a + i, 0xe28a + i + 1)

    a = 0xe7bf
    for i in range(5):
        y = data.Pstruct(cx.m, a, "<4B")
        a = y.hi

    y = data.Pstruct(cx.m, 0xe80a, "<4B")

    a = 0xe675
    y = data.Pstruct(cx.m, a, "<4B")
    a = y.hi
    y = data.Pstruct(cx.m, a, "<4B")

    a = 0xe962
    y = data.Pstruct(cx.m, a, "<5B")
    a = 0xe967
    y = data.Pstruct(cx.m, a, "<B")
    a = 0xe968
    y = data.Pstruct(cx.m, a, "<5B")

    a = 0xff9c
    y = data.Pstruct(cx.m, a, "<HH")

    cx.vectors()

    for i in range(6):
        cx.codeptr(0xe291 + 2 * i)

    for a in (
            0xe034,
            0xe906,
            0xe90c,
            0xe948,
            0xe96d,
            0xe972,
            0xe977,
            0xe989,
            0xe98e,
            0xe993,
            0xea33,
            0xea36,
            0xea39,
            0xea9c,
            0xeab1,
            0xff93,
            0xff96,
            0xff99,
            0xfff3,
            0xfff6,
            0xfff9,
    ):
        cx.disass(a)
        cx.m.set_line_comment(a, "MANUAL")


    return NAME, (cx.m,)

if __name__ == '__main__':
    listing.Example(example)
