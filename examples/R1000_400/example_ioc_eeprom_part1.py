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
import hashlib

from pyreveng import mem, listing, data, code
import pyreveng.cpu.m68020 as m68020
import pyreveng.cpu.m68000_switches as m68000_switches
import pyreveng.toolchest.srecords as srecords

import ioc_hardware
import ioc_eeprom_exports

NAME = "IOC_EEPROM_PART1"

FILENAME = os.path.join(os.path.split(__file__)[0], "IOC_EEPROM.bin")

def flow_check(asp, ins):
    ''' Flowcheck for inline texts '''
    if ins.lo in (
        0x8000001c,
    ):
        return
    for flow in ins.flow_out:
        if flow.to in (0x8000001c, 0x800000e2, ):
            y = data.Txt(asp, ins.hi, label=False, align=2, splitnl=True)
            ins.dstadr = y.hi
            ins.flow_out.pop(-1)
            ins += code.Jump(cond=True, to=ins.dstadr)
        elif flow.to in (0x80001010, 0x80001122,):
            if asp.bu16(ins.lo - 6) == 0x43f9:
                a = asp.bu32(ins.lo - 4)
                y = data.Txt(asp, a, splitnl=True)

def artifact_a17915e91cbe29ca(cx):

    ioc_eeprom_exports.add_symbols(cx.m)

    y = data.Txt(cx.m, 0x8000015b)
    y = data.Txt(cx.m, 0x80000156, y.lo)

    for a in (
        0x80000072,
        0x800001c4,
        0x80000314,
        0x80000374,
    ):
        data.Txt(cx.m, a, splitnl=True)

    for a in (
        0x800001c2,
        0x80001b96,
    ):
        data.Const(cx.m, a, a+2)
        cx.m.set_line_comment(a, "NB: odd address jump")

    cx.vectors(0x8)

    for a, b in (
        (0x80000010, "TEST_FAILED"),
        (0x80000014, "IOC_14_XXX"),
        (0x80000020, "IOC_20_XXX"),
        (0x80000088, "_TEST_FAILED"),
        (0x800000d8, "OUTSTR_PRESERVE_D0(A0)"),
        (0x800000f8, "OUTSTR_SMASH_D0(A0)"),
        (0x80000142, "OUTSTR_OK()"),
        (0x8000014c, "OUTSTR_CRNL()"),
        (0x8000015e, "DELAY(D0)"),
        (0x8000016c, "CHECKSUM_FUNC"),
        (0x800001e4, "CHECKSUM_EEPROM"),
        (0x800001f6, None),
        (0x80000208, None),
        (0x8000021a, None),
        (0x80001524, None),
        (0x80001566, None),
        (0x800015a8, None),
        (0x800015d4, None),
        (0x80001628, None),
        (0x80001672, None),
        (0x800016a2, None),
        (0x800016c2, None),
    ):
        cx.disass(a)
        cx.m.set_line_comment(a, "Manual")
        if b:
            cx.m.set_label(a, b)

    cx.m.set_block_comment(0x80000222, 'CONSOLE_UART Test Mode registers')
    cx.m.set_block_comment(0x8000025c, 'CONSOLE_UART Local Loopback')
    cx.m.set_line_comment(0x80000266, '16x N81')
    cx.m.set_line_comment(0x8000026c, '1X,BKDET,async 9600')
    cx.m.set_line_comment(0x80000272, 'Local Loopback -RTS RxEN +DTR TxEN')
    cx.m.set_block_comment(0x800002c4, 'CONSOLE_UART')
    cx.m.set_block_comment(0x80000314, 'IOC SELFTEST')
    cx.m.set_block_comment(0x80000b90, 'SelfTest: PIT')
    cx.m.set_line_comment(0x80000ba8, 'BRG=1, Counter, IP2 = PITCLK')
    cx.m.set_line_comment(0x80000ba8, 'PITCLK IOCp76 = 100ns * 256 = 25.6us')
    cx.m.set_block_comment(0x80000bf8, 'SelfTest: Modem DUART channel')
    cx.m.set_block_comment(0x80000d26, 'SelfTest: Diagnostic DUART channel')
    cx.m.set_block_comment(0x80000ddc, 'SelfTest: Clock / Calendar SELFTEST')
    cx.m.set_block_comment(0x80000eca, 'SelfTest: Checking for RESHA board')
    cx.m.set_block_comment(0x80000f7a, 'SelfTest: RESHA EEProm Interface')
    cx.m.set_block_comment(0x800011a0, 'SelfTest: Local interrupts')
    cx.m.set_block_comment(0x800011dc, 'SelfTest: Local interrupts 0x50')
    cx.m.set_block_comment(0x80001202, 'SelfTest: Local interrupts 0x42 RX_BREAK')
    cx.m.set_line_comment(0x80001202, 'Local Loopbac')
    cx.m.set_line_comment(0x80001208, 'Local Loopback +TX-break')
    cx.m.set_line_comment(0x80001226, 'Local Loopback -TX-break')
    cx.m.set_line_comment(0x8000122c, 'Wait for txhold empty')
    cx.m.set_line_comment(0x80001238, 'Wait for txshift non-empty')
    cx.m.set_line_comment(0x80001240, 'Wait for txshift empty')
    cx.m.set_line_comment(0x80001248, 'Wait for txshift empty')
    cx.m.set_line_comment(0x80001250, 'Wait for txhold empty')
    cx.m.set_block_comment(0x80001280, 'SelfTest: Local interrupts 0x51')
    cx.m.set_block_comment(0x8000129e, 'SelfTest: Local interrupts 0x46')
    cx.m.set_block_comment(0x800012cc, 'SelfTest: Local interrupts 0x45 - CONSOLE_RXRDY')
    cx.m.set_line_comment(0x800012d2, 'Wait for txhold empty')
    cx.m.set_line_comment(0x800012de, 'Wait for rxhold full')
    cx.m.set_line_comment(0x800012f2, 'Wait for txshift empty')
    cx.m.set_line_comment(0x800012fa, 'Wait for txshift empty')
    cx.m.set_line_comment(0x80001302, 'Wait for txshift empty')
    cx.m.set_block_comment(0x8000132a, 'SelfTest: Local interrupts 0x44')
    cx.m.set_block_comment(0x8000135c, 'SelfTest: Local interrupts 0x52')
    cx.m.set_block_comment(0x8000137a, 'SelfTest: Local interrupts 0x4f')
    cx.m.set_block_comment(0x800013a8, 'SelfTest: Local interrupts 0x4d')
    cx.m.set_block_comment(0x800013d6, 'SelfTest: Local interrupts 0x4e')
    cx.m.set_block_comment(0x80001408, 'SelfTest: Local interrupts 0x4b')
    cx.m.set_block_comment(0x80001436, 'SelfTest: Local interrupts 0x4a')
    cx.m.set_block_comment(0x80001470, 'SelfTest: Local interrupts 0x49')
    cx.m.set_block_comment(0x800014a8, 'SelfTest: Local interrupts 0x48')
    cx.m.set_block_comment(0x800014d6, 'SelfTest: Illegal reference protection')
    cx.m.set_block_comment(0x800015d4, 'SelfTest: I/O bus parity')
    cx.m.set_block_comment(0x80001672, 'SelfTest: I/O bus spurious interrupts')
    cx.m.set_block_comment(0x800016e4, 'SelfTest: Temperature sensors')
    cx.m.set_block_comment(0x8000174c, 'SelfTest: IOC diagnostic processor')
    cx.m.set_block_comment(0x800017fe, 'SelfTest: Power margining')
    cx.m.set_block_comment(0x80001862, 'SelfTest: Clock margining')

    ioc_eeprom_exports.add_exports(cx.m, ioc_eeprom_exports.IOC_EEPROM_PART1_EXPORTS)


def ioc_eeprom_part1(m0, ident=None):
    ''' First part of an IOC eeprom '''

    cx = m68020.m68020()
    m68000_switches.m68000_switches(cx)
    cx.flow_check.append(flow_check)

    if m0[0] == 0x53 and 0x30 <= m0[1] <= 0x39:
        srec = srecords.SRecordSet().from_mem(m0)
        srec.map(cx.m, lo=0x80000000, hi=0x80002000)
    else:
        cx.m.map(m0, 0x80000000, 0x80002000)

    m2 = mem.ByteMem(0x0, 0x8)
    for i in range(8):
        m2[i] = cx.m[0x80000000 + i]

    cx.m.map(m2, 0x00000000, 0x00000008)

    cx.m.set_block_comment(0x0, '''
For the first few clock-cycles the 'IPCNT1' counter on:
        R1000_SCHEMATIC_IOC.PDF p13
inverts the MSB address line, mapping the EEPROM to 0x0 just long enough for
the CPU to fetch the stack and reset vectors
''')

    ioc_hardware.add_symbols(cx.m)

    digest = hashlib.sha256(cx.m.bytearray(0x80000000, 0x2000)).hexdigest()[:16]
    print("DD", __file__, digest, ident)

    if digest == "a17915e91cbe29ca":
         artifact_a17915e91cbe29ca(cx)
    else:
         cx.vectors(0x8)

    return cx

def example():
    ''' First part of IOC eeprom '''

    m0 = mem.Stackup((FILENAME,))
    cx = ioc_eeprom_part1(m0)

    return NAME, (cx.m,)

#######################################################################

if __name__ == '__main__':
    import sys

    if len(sys.argv) == 5 and sys.argv[1] == "-AutoArchaeologist":
        print(__file__, sys.argv)
        mb = mem.Stackup((sys.argv[3],))
        cx = ioc_eeprom_part1(mb, sys.argv[2])
        listing.Listing(cx.m, fn=sys.argv[4], ncol=8, leaf_width=72)
        exit(0)

    listing.Example(example, ncol=8)
