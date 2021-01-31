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
   The hardware self-test part of the IOC EEPROM
   ---------------------------------------------
'''

import os

from pyreveng import mem, listing, data
import pyreveng.cpu.m68020 as m68020
import pyreveng.cpu.m68000_switches as m68000_switches
import pyreveng.toolchest.srecords as srecords

import ioc_hardware
import ioc_eeprom_exports

NAME = "IOC_EEPROM_PART2"

FILENAME = os.path.join(os.path.split(__file__)[0], "IOC_EEPROM.bin")

IOC_INSTRUCTION_SPEC = '''
OUTTEXT         outtxt,>J       | 4E | 96 |
'''

class IocInstructionIns(m68020.m68020_ins):
    ''' Pseudo-instructions '''

    def assy_outtxt(self):
        ''' inline text '''
        y = data.Txt(self.lang.m, self.hi, align=2, label=False, splitnl=True)
        self.dstadr = y.hi

def flow_check(asp, ins):
    ''' Flowcheck for text arguments '''
    for flow in ins.flow_out:
        if flow.to in (0x8000298e, ):
            if asp.bu16(ins.lo - 4) == 0x47fa:
                a = ins.lo - 2 + asp.bs16(ins.lo - 2)
                data.Txt(asp, a, splitnl=True)
            elif asp.bu16(ins.lo - 6) == 0x47f9:
                a = asp.bu32(ins.lo - 4)
                data.Txt(asp, a, splitnl=True)

def boot_reason(cx, a):
    ''' Coded string table '''
    data.Const(cx.m, a, a+1)
    b = cx.m[a]
    assert b & 0x80
    i = 1
    while True:
        j = cx.m[a+i]
        if not j or j & 0x80:
            break
        i += 1
    y = data.Txt(cx.m, a+1, a+i, label=False)
    return y.hi

def ioc_eeprom_part2(m0, _ident=None):
    ''' Second part of an IOC eeprom '''

    cx = m68020.m68020()
    m68000_switches.m68000_switches(cx)
    cx.add_ins(IOC_INSTRUCTION_SPEC, IocInstructionIns)
    cx.flow_check.append(flow_check)

    if m0[0] == 0x53 and 0x30 <= m0[1] <= 0x39:
        srec = srecords.SRecordSet().from_mem(m0)
        srec.map(cx.m, lo=0x80002000, hi=0x80004000)
    else:
        cx.m.map(m0, 0x80002000, 0x80004000, 0x4000)

    ioc_hardware.add_symbols(cx.m)
    ioc_eeprom_exports.add_symbols(cx.m)
    ioc_eeprom_exports.add_flow_check(cx)

    for a in (
        0x8000221c,
        0x80002232,
        0x8000223d,
        0x80002481,
        0x8000256e,
        0x8000257d,
        0x8000258c,
        0x800027ee,
        0x8000287b,
        0x8000289f,
        0x80002a24,
        0x80002a2c,
        0x80002c14,
        0x80003690,

    ):
        data.Txt(cx.m, a, splitnl=True)

    a = 0x8000228f
    while cx.m[a] & 0x80:
        a = boot_reason(cx, a)
    data.Const(cx.m, a, a + 1)
    data.Txt(cx.m, a+1, label=False)

    a = 0x80002d2d
    while a < 0x80002dff:
        y = data.Txt(cx.m, a, label=False)
        a =y.hi

    for a in range(0x800036e8, 0x800036fc, 4):
        y = cx.dataptr(a)
        data.Txt(cx.m, y.dst)

    for a in range(0x80002000, 0x80002074, 4):
        cx.disass(a)

    for a, b in (
        (0x80002790, None),
        (0x800027a8, None),
        (0x80002bc4, None),
    ):
        cx.disass(a)
        cx.m.set_line_comment(a, "MANUAL")
        if b:
            cx.m.set_label(a, b)

    for a in range(0x800038ce, 0x800038ee, 4):
        cx.codeptr(a)
    for a in range(0x8000310e, 0x80003122, 4):
        cx.codeptr(a)

    ioc_eeprom_exports.add_exports(cx.m, ioc_eeprom_exports.IOC_EEPROM_PART2_EXPORTS)

    return cx

def example():
    ''' Second part of IOC eeprom '''

    m0 = mem.Stackup((FILENAME,))
    cx = ioc_eeprom_part2(m0)

    return NAME, (cx.m,)

#######################################################################

if __name__ == '__main__':
    import sys

    if len(sys.argv) == 5 and sys.argv[1] == "-AutoArchaeologist":
        mb = mem.Stackup((sys.argv[3],))
        cx = ioc_eeprom_part2(mb, sys.argv[2])
        listing.Listing(cx.m, fn=sys.argv[4], ncol=8, leaf_width=72)
        exit(0)

    listing.Example(example, ncol=8)
