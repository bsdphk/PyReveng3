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

from pyreveng import mem, listing
import pyreveng.cpu.hp_nanoproc as hp_nanoproc

import hp3336_common as common

NAME = "HP3336"

FILENAME = "hp3336.bin"

def example():
    m = mem.Stackup((FILENAME,), nextto=__file__)

    cx = hp_nanoproc.hp_nanoproc_pg()
    cx.m.map(m, 0)

    for a, b in common.SYMBOLS.items():
        cx.m.set_label(a, b)

    cx.disass(0)
    cx.disass(0xff)

    #######################################################################
    if True:
        for a0 in range(4, 0x20, 4):
            assert cx.m[a0] == 0xc8
            pg = (cx.m[a0 + 1] & 0x07) << 11
            assert pg == a0 << 9
            dpf = cx.m[a0 + 2] << 8
            dpf |= cx.m[a0 + 3]
            dpf &= 0x7ff
            dpf |= pg
            cx.m.set_label(dpf, "DISP_%d" % (a0 >> 2))
            cx.disass(a0)
            cx.disass(dpf)
            for a1 in range(pg, dpf, 2):
                da = cx.m[a1] << 8
                da |= cx.m[a1 + 1]
                da &= 0x7ff
                da |= pg
                v = a0 << 3
                v |= (a1 - pg) >> 1
                cx.m.set_label(a1, "PTR_%02x" % v)
                cx.m.set_label(da, "FN_%02x" % v)
                cx.disass(a1)

    #######################################################################
    def jmp_table(lo, hi, span, txt="table"):
        cx.m.set_block_comment(lo, txt)
        for a in range(lo, hi, span):
            cx.disass(a)

    #######################################################################
    if True:
        # Comes from 0x0d01
        # returns to 0xd02
        jmp_table(0x0f80, 0x0fa8, 4, "LED Segment Table")

    #######################################################################
    if True:
        # Comes from 0xab2
        # does not return
        jmp_table(0x0fa8, 0x0fc0, 2)

    #######################################################################
    if True:
        # Comes from 0xb3b
        # returns to 0xb3c
        jmp_table(0x0fc0, 0x0fe0, 4)

    #######################################################################
    if True:
        # Comes from 0xb62
        # returns to 0xb63
        jmp_table(0x0fe0, 0x1000, 4)

    #######################################################################
    if True:
        # Comes from 0x1aa0
        # returns to 1aa1
        jmp_table(0x1840, 0x1878, 8)

    #######################################################################
    if True:
        # Comes from 0x29f9
        # returns to 29fa
        jmp_table(0x2fb8, 0x3000, 8)

    #######################################################################
    if True:
        # Comes from 0x3c37
        # does RET
        jmp_table(0x3fd8, 0x4000, 4)

    return NAME, (m,)

if __name__ == '__main__':
    listing.Example(example)
