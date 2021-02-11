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
   First quarter of the IOC EEPROM
   -------------------------------
'''

import os

from pyreveng import mem, data, code

import ioc_utils
import ioc_hardware
import ioc_eeprom_exports

NAME = "IOC_EEPROM_PART1"
BASE = 0x80000000
SIZE = 0x2000

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


#######################################################################

class IocEepromPart1(ioc_utils.IocJob):
    ''' First quarter of IOC EEPROM image '''

    def __init__(self, **kwargs):
        super().__init__(BASE, BASE+SIZE, name=NAME, **kwargs)

    def default_image(self):
        ''' Load default image '''
        self.map(mem.Stackup((FILENAME,)))

    def augment_cx(self):
        ''' Add Capabilities to cx '''
        cx = self.cx
        cx.flow_check.append(flow_check)

    def config_cx(self):
        ''' Add global symbol sets etc. '''
        cx = self.cx
        ioc_eeprom_exports.add_flow_check(cx)
        ioc_eeprom_exports.add_symbols(cx.m)
        ioc_hardware.add_symbols(cx.m)

    def round_0(self):
        ''' Things to do before the disassembler is let loose '''

    def round_1(self):
        ''' Let the disassembler loose '''
        cx = self.cx
        cx.codeptr(0x80000004)
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

    def round_2(self):
        ''' Spelunking in what we alrady found '''
        cx = self.cx
        ioc_eeprom_exports.add_exports(
            cx.m,
            ioc_eeprom_exports.IOC_EEPROM_PART1_EXPORTS
        )

    def round_0_a17915e91cbe29ca(self):
        ''' Things to do before the disassembler is let loose '''
        cx = self.cx
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


#######################################################################

def example():
    ''' Follow the example protocol '''
    return IocEepromPart1().example()

#######################################################################

if __name__ == '__main__':
    ioc_utils.mainfunc(__file__, example, IocEepromPart1)
