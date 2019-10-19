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

'''HP5370B Time Interval Counter
'''

from pyreveng import listing, data
import pyreveng.cpu.mc6800 as mc6800
from pyreveng.toolchest import seven_segment
import utils

NAME = "HP5370B"

FILENAME = "HP5370B.ROM"

SYMBOLS = {
    0x7ead: "ROM_LOCS",
    0x7eed: "RAM_TEST_VALS",
    0x66ea: "ERR5_UNDEF_KEY",
}

def example():
    cx = utils.setup(FILENAME, -1)

    for a, b in SYMBOLS.items():
        cx.m.set_label(a, b)

    ct = utils.cmd_tbl(cx, 0x7c64, 0x7c98)
    cta = utils.arg_range(cx, ct, 0x7d6c, 0x7d88)

    def cbyte(asp, a):
        c = data.Const(asp, a, a + 1)
        c.val = asp[a]
        c.typ = ".BYTE"
        c.fmt = "0x%02x" % c.val

    cx.dataptr(0x6403)
    cx.dataptr(0x6405)
    cx.dataptr(0x6407)

    for a in range(0x7eed, 0x7ef9):
        cbyte(cx.m, a)

    c = cx.dataptr(0x7915)
    cx.m.set_label(c.lo, "@7SEGCODES")
    cx.m.set_label(c.dst, "7SEGCODES")
    c = seven_segment.table(cx.m, c.dst, c.dst + 0x10, verbose=False)


    for a in range(0x7ead, 0x7ebf, 2):
        cx.dataptr(a)

    # XXX: Add mising flow
    cx.disass(0x6845)
    cx.disass(0x6867)

    for i in range(0x6b23, 0x6b3b, 3):
        utils.data24(cx.m, i)

    for a in range(0x77d7, 0x77f7, 4):
        data.Txt(cx.m, a, a + 4)

    data.Txt(cx.m, 0x78f3, 0x78f7)
    data.Txt(cx.m, 0x78f7, 0x78fd)
    data.Txt(cx.m, 0x78fd, 0x78ff)

    utils.cmd_dispatch(cx, cta, 0x644c)

    utils.key_dispatch(cx, 0x640c, 0x644c)

    utils.dsp_dispatch(cx, 0x6848, 0x6858)

    for i in (0x614c, 0x619c, 0x61a3, 0x69dd, 0x69e4):
        utils.float70(cx.m, i)

    c = cx.codeptr(0x7909)
    cx.m.set_label(c.dst, "HPIB_CMD_PARSE")

    utils.square_tbl(cx.m)

    utils.apply_labels(cx, "B")
    utils.tramp(cx)

    return NAME, (cx.m,)

if __name__ == '__main__':
    listing.Example(example)
