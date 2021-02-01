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
   The RESHA eeprom
   ----------------
'''

import os

from pyreveng import mem, listing, data, discover
import pyreveng.cpu.m68020 as m68020
import pyreveng.cpu.m68000_switches as m68000_switches
import pyreveng.toolchest.srecords as srecords

import ioc_hardware
import ioc_eeprom_exports

NAME = "RESHA_EEPROM"

FILENAME = os.path.join(os.path.split(__file__)[0], "RESHA_EEPROM.bin")

def ioc_resha(m0, ident=None):
    ''' A RESHA eeprom '''
    cx = m68020.m68020()
    m68000_switches.m68000_switches(cx)
    ioc_eeprom_exports.add_flow_check(cx)

    if m0[0] == 0x53 and 0x30 <= m0[1] <= 0x39:
        print("SRECS!")
        srec = srecords.SRecordSet().from_mem(m0)
        srec.map(cx.m)
    else:
        cx.m.map(m0, 0x00070000)

    ioc_hardware.add_symbols(cx.m)
    ioc_eeprom_exports.add_symbols(cx.m)

    for n, a in enumerate(range(0x70000,0x78000,0x2000)):
        cx.m.set_block_comment(a, "PROGRAM VECTORS")
        data.Const(cx.m, a, a + 2)

    for key, desc in ioc_eeprom_exports.RESHA_PROGRAMS.items():
        a = 0x70000 + 0x2000 * (key & 0xff)
        ptr = a + (key >> 7)
        data.Const(cx.m, ptr, ptr + 2, func=cx.m.bu16, size=2)
        prog = a + cx.m.bu16(ptr)
        cx.disass(prog)
        cx.m.set_label(prog, "RESHA_PROGRAM_%04x" % key)
        t = "RESHA PROGRAM 0x%04x - " % key + desc
        cx.m.set_block_comment(prog, t)
        cx.m.set_line_comment(ptr, t)

    if ident is not None:
        discover.Discover(cx)

    return cx

def example():
    ''' Specific RESHA eeprom '''

    m = mem.Stackup((FILENAME,))
    cx = ioc_resha(m)

    for a in range(0x734ea, 0x73542, 4):
        b = cx.m.bu32(a)
        if 0x72000 <= b <= 0x74000:
            cx.codeptr(a)

    for a, b in (
        (0x76040, 0x76084),
        (0x767f2, 0x767fe),
    ):
        for i in range(a, b, 4):
            cx.codeptr(i)

    for a, b in (
        (0x76084, 0x760c8),
    ):
        for i in range(a, b, 4):
            y = cx.dataptr(i)
            data.Txt(cx.m, y.dst)

    for a in (
        0x730a8,
        0x73258,
        0x733a2,
        0x73396,
        0x77662,
    ):
        cx.disass(a)

    for a, b in (
        (0x7063e, 0x70708),
        (0x71025, 0x71060),
        (0x712a6, 0x7130c),
        (0x719f2, 0x71a99),
        (0x74006, 0x7412e),
        (0x76248, 0x765e3),
    ):
        i = a
        while i < b:
            y = data.Txt(cx.m, i, splitnl=True)
            i = y.hi

    for a in (
        0x7200a,
        0x769ce,
        0x769ec,
        0x76a0a,
        0x76a28,
    ):
        data.Txt(cx.m, a, splitnl=True)

    for a in range(0x765e4, 0x76652, 6):
        cx.codeptr(a + 2)

    discover.Discover(cx)

    return NAME, (cx.m,)

#######################################################################

if __name__ == '__main__':
    import sys

    if len(sys.argv) == 5 and sys.argv[1] == "-AutoArchaeologist":
        mb = mem.Stackup((sys.argv[3],))
        cx = ioc_resha(mb, sys.argv[2])
        listing.Listing(cx.m, fn=sys.argv[4], ncol=8, leaf_width=72)
        exit(0)

    listing.Example(example, ncol=8)
