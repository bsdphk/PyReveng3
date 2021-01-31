#!/usr/bin/env python
#
# Copyright (c) 2012-2021 Poul-Henning Kamp <phk@phk.freebsd.dk>
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

'''
   IOC KERNEL
   ----------
'''

import os

from pyreveng import mem, listing, data, assy
import pyreveng.cpu.m68020 as m68020
import pyreveng.cpu.m68000_switches as m68000_switches

import ioc_hardware
import ioc_eeprom_exports
import ioc_m200_exports

NAME = "IOC_KERNEL"

FILENAME = os.path.join(os.path.split(__file__)[0], "KERNEL_0.M200")

KERNEL_DESC = '''
MYTRAP  vect,>J         |1 0 1 0 0 0 0 0| vect          |
PANIC.W tvect,>R        |0 1 0 1|0 0 0 0|1 1 1 1|1 0 1 0| w                             |
'''

class KernelIns(m68020.m68020_ins):
    ''' Kernel specific (pseudo-)instructions'''
    def assy_tvect(self):
        w= self['w']
        return assy.Arg_imm(w)

def vector_line_a(cx):
    ''' Follow the LINE_A vector to find KERNCALL entrypoints '''
    a = cx.m.bu32(0x28)
    for i, j in (
        (0x00, 0x48), (0x01, 0xe7), (0x02, 0x80), (0x03, 0x04),
        (0x1a, 0x4e), (0x1b, 0xb0), (0x1c, 0x05),
    ):
        if cx.m[a + i] != j:
            print("Line_a mismatch", "0x%x" % i, "0x%x" % j, "0x%x" % cx.m[a+i])
            return
    if cx.m[a + 0x1d] == 0xa1:
        tbl = cx.m.bu16(a + 0x1e)
    elif cx.m[a + 0x1d] == 0xb1:
        tbl = cx.m.bu32(a + 0x1e)
    else:
        print("Line_a mismatch", "0x1d", "(0xa1/0xb1)", "0x%x" % cx.m[a+0x1d])
        return

    cx.m.set_label(tbl, "KERNCALL_VECTORS")
    for sc in range(32):
        i = tbl + sc * 4
        y = cx.codeptr(i)
        cx.m.set_label(y.dst, "_" + ioc_m200_exports.kerncall_name(sc))
        cx.m.set_block_comment(
            y.dst,
            "PTR @ 0x%x %s" % (i, ioc_m200_exports.kerncall_name(sc))
        )

def ioc_kernel(m0, ident=None):
    ''' A generic IOC Kernel '''

    cx = m68020.m68020()
    m68000_switches.m68000_switches(cx)
    cx.it.load_string(KERNEL_DESC, KernelIns)

    cx.m.map(m0, 0x00000000)

    ioc_hardware.add_symbols(cx.m)
    ioc_eeprom_exports.add_symbols(cx.m)
    ioc_eeprom_exports.add_flow_check(cx)

    vector_line_a(cx)

    if ident:
        cx.vectors(0x400)

    return cx

def example():
    ''' A specific IOC kernel '''

    m0 = mem.Stackup((FILENAME,))
    cx = ioc_kernel(m0)

    # Stop disassembler
    for a in (
        0x492,
        0x754,
        0xf2c,
        0xf4c,
    ):
        data.Const(cx.m, a)

    for a in (
        0x000004ec,
        0x0000800c,
        0x0000a46a,
        0x0000a518,
        0x0000a53b,
    ):
        data.Txt(cx.m, a, splitnl=True)

    a = 0xa24e
    while a < 0xa35d:
        y = data.Txt(cx.m, a, term=(0x02, 0x03,), splitnl=True, label=False)
        a = y.hi

    for a in range(0x0000a3c8, 0x0000a3d8, 4):
        y = cx.dataptr(a)
        data.Txt(cx.m, y.dst, term=(0x01,))

    cx.vectors(0x400)

    for a, b, c in (
        (0x2448, 0x2454, 4),
        (0x3b82, 0x3b90, 4),
        (0x42e6, 0x42f2, 2),
        (0x9e88, 0x9f00, 8),
        (0xa19c, 0xa1b4, 4),
    ):
        for i in range(a, b, c):
            cx.disass(i)
            cx.m.set_block_comment(i, "TBL @ 0x%x" % i)

    for a, b in (
        (0x6962, 0x6972),
        (0x6720, 0x6734),
        (0x7890, 0x78b0),
        (0x7b5c, 0x7b6c),
        (0x7e1e, 0x7e3a),
        (0x8188, 0x81a0),
        (0x8234, 0x824c),
        (0xa494, 0xa4b4),
        (0xa4e0, 0xa518),
        (0xa5b1, 0xa688),
        (0xa68c, 0xa710),
        (0xa718, 0xa72c),
        (0xa734, 0xa740),
        (0xa744, 0xa748),
        (0xa750, 0xa794),
        (0xa79c, 0xa7c4),
        (0xa7c4, 0xa7c8),
        (0xa8a0, 0xa940),
        (0xa954, 0xa994),
    ):
        for i in range(a, b, 4):
            y = cx.codeptr(i)
            cx.m.set_block_comment(y.dst, "PTR @ 0x%x" % i)

    for a, b in (
        (0xa21c, 0xa246),
        (0xa3b7, 0xa3c5),
        (0xa3d8, 0xa456),
        (0xa4b4, 0xa4de),
    ):
        for i in range(a, b, 2):
            y = data.Pstruct(cx.m, i, ">H", fmt="0x%08x")
            cx.disass(y.data[0])
            cx.m.set_block_comment(y.data[0], "TBL @ 0x%x" % i)

    for a, b in (
        (0x2602, "see 0x2612"),
        (0x2602, "via 0x09c4()"),
        (0x263e, "via 0x118"),
        (0x2694, "via 0x128"),
        (0x2f02, "via 0x147d"),
        (0x3180, "via 0x09c4()"),
        (0x31c4, "via 0x12c"),
        (0x36aa, "via 0x09c4()"),
        (0x3b3e, "via 0x130"),
        (0x3b4a, "via 0x1438"),
        (0x3ed2, "via 0x143c"),
        (0x3ee0, "via 0x143c"),
        (0x3eee, "via 0x1440"),
        (0x3efc, "via 0x1440"),
        (0x3f08, "via 0x1444"),
        (0x3f16, "via 0x1444"),
        (0x3f24, "via 0x1448"),
        (0x3f32, "via 0x1448"),
        (0x4104, "via 0x09c4()"),
        (0x4120, "via 0x11c"),
        (0x4208, "via 0x144c"),
        (0x4214, "via 0x144c"),
        (0x4226, "via 0x09c4()"),
        (0x440e, "via 0x09c4()"),
        (0x4544, "via 0x147d"),
        (0x4548, "via 0x147d"),
        (0x46aa, "via 0x147d"),
        (0x49ba, "via 0x128"),
        (0x6246, "via 0x177c"),
        (0x6312, "via 0x520"),
        (0x6940, "via 0x09c4()"),
        (0x6a0e, "via 0x520"),
        (0x6b8e, "via 0x09c4()"),
        (0x7fd4, "via 0x177c"),
        (0x8208, "via 0x520"),
        (0x82bc, "Via 0x8"),
        (0x8480, "via 0x09c4()"),
        (0x9cb8, "via 0x520"),
        (0x9f0e, "via 0x09c4()"),
        (0x2e04, "See 00002bb6"),
        (0x3b58, "See 0000354e"),
        (0xac06, "MANUAL"),
        (0x8d72, "MANUAL"),
        (0x9cc0, "MANUAL"),
        (0x46a0, "MANUAL"),
        (0x50b8, "MANUAL"),
        (0x6738, "MANUAL"),
        (0x46c8, "MANUAL"),
        (0xad58, "MANUAL"),
        (0xad6e, "MANUAL"),
        (0xae90, "MANUAL"),
        (0xafd8, "MANUAL"),
        (0xb458, "MANUAL"),
        (0xb5f6, "MANUAL"),
        (0xb8ca, "MANUAL"),
        (0xbbe8, "MANUAL"),
        (0xbc28, "MANUAL"),
    ):
        cx.disass(a)
        cx.m.set_block_comment(a, b)

    return NAME, (cx.m,)

#######################################################################

if __name__ == '__main__':
    import sys

    if len(sys.argv) == 5 and sys.argv[1] == "-AutoArchaeologist":
        mb = mem.Stackup((sys.argv[3],))
        cx = ioc_kernel(mb, sys.argv[2])
        listing.Listing(cx.m, fn=sys.argv[4], ncol=8, leaf_width=72)
        exit(0)

    listing.Example(example, ncol=8)
