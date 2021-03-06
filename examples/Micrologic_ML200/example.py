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

'''Micrologic ML200 Loran-C Receiver
'''

import os
from pyreveng import mem, listing
import pyreveng.cpu.mcs4 as mcs4

NAME = "Micrologic_ML200"

SYMBOLS = {
    0x6e8: "Incr_rr0()",
    0x6bc: "Count_Down()",
    0x7df: "Update_Display()",
}

def example():
    m = mem.ByteMem(0x0, 0x900)
    def hexfile(bn, a0):
        fn = os.path.join(os.path.dirname(__file__), bn)
        fi = open(fn)
        for i in fi:
            j = i.split()
            if len(j) == 0:
                continue
            if j[0][0] == "#":
                continue
            a = int(j[0], 16)
            b = int(j[1], 16)
            m[a0 + a] = b
        fi.close()

    hexfile("P8316.hex", 0)
    hexfile("P1702.hex", 0x800)

    cx = mcs4.mcs4()
    cx.m.map(m, 0)

    for a, b in SYMBOLS.items():
        cx.m.set_label(a, b)

    cx.disass(0)


    if False:
        cmt = """-
        This is the RESET "countdown" routine

        Displays:
          .9.9.9.9 9.9
          .8.8.8.8 8.8
          ...
          .0.0.0.0 0.0

        It calls 0x5ca a lot, presumably to let the analog stuff settle ?
        """

    if False:
        cmt = """
        The display is driven by two chains of 3 three P4003 10-bit shift
        registers, which again drives 7447 7-segment drivers.
        On entry r2 contains 0x20 or 0x40, depending on which clock-pulse
        line should be driven.
        A total of 30 pulses are sent:
            6 x 1  Decimal points, left to right
            6 x 4  BCD to 7447, LSD to MSD order.
        """

    if False:
        cmt = """
            0x66a-0x676
            are 3-byte constants
        """

    return NAME, (cx.m,)

if __name__ == '__main__':
    listing.Example(example, pil=True)
