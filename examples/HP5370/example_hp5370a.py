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

'''HP5370A Time Interval Counter
'''

from pyreveng import listing
import pyreveng.cpu.mc6800 as mc6800
from pyreveng.toolchest import seven_segment
import utils

NAME = "HP5370A"

FILENAME = "HP5370A.ROM"

SYMBOLS = {
    0x66ea: "ERR5_UNDEF_KEY",
}

def example():
    cx = utils.setup(FILENAME, -1)

    for a, b in SYMBOLS.items():
        cx.m.set_label(a, b)

    seven_segment.table(cx.m, 0x7e29, 0x7e39, verbose=False)

    ct = utils.cmd_tbl(cx, 0x7c5d, 0x7c91)
    cta = utils.arg_range(cx, ct, 0x7d65, 0x7d81)
    utils.cmd_dispatch(cx, cta, 0x644c)

    utils.key_dispatch(cx, 0x640c, 0x644c)

    utils.dsp_dispatch(cx, 0x6848, 0x6858)

    for i in (0x614c, 0x619c, 0x61a3, 0x69dd, 0x69e4):
        utils.float70(cx.m, i)

    utils.square_tbl(cx.m)

    utils.apply_labels(cx, "A")
    utils.tramp(cx)

    return NAME, (cx.m,)

if __name__ == '__main__':
    listing.Example(example)
