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
   Second quarter of the IOC EEPROM
   --------------------------------
'''

import os

from pyreveng import mem, data, assy
import pyreveng.cpu.m68020 as m68020

import ioc_utils
import ioc_hardware
import ioc_eeprom_exports

NAME = "IOC_EEPROM_PART2"
BASE = 0x80002000
SIZE = 0x2000

FILENAME = os.path.join(os.path.split(__file__)[0], "IOC_EEPROM.bin")

IOC_INSTRUCTION_SPEC = '''
OUTTEXT         outtxt,>J       | 4E | 96 |
'''

class IocInstructionIns(m68020.m68020_ins):
    ''' Pseudo-instructions '''

    def assy_outtxt(self):
        ''' inline text '''
        if self.lo < BASE or self.hi > BASE + SIZE:
            raise assy.Invalid()
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
#######################################################################

class IocEepromPart2(ioc_utils.IocJob):
    ''' Second quarter of IOC EEPROM image '''

    def __init__(self, **kwargs):
        super().__init__(BASE, BASE+SIZE, name=NAME, **kwargs)

    def default_image(self):
        ''' Load default image '''
        self.map(mem.Stackup((FILENAME,)), offset=0x4000)

    def augment_cx(self):
        ''' Add Capabilities to cx '''
        cx = self.cx
        cx.flow_check.append(flow_check)
        cx.add_ins(IOC_INSTRUCTION_SPEC, IocInstructionIns)

    def config_cx(self):
        ''' Add global symbol sets etc. '''
        cx = self.cx
        ioc_eeprom_exports.add_flow_check(cx)
        ioc_eeprom_exports.add_symbols(cx.m)
        ioc_hardware.add_symbols(cx.m)
        cx.flow_check.append(flow_check)

    def round_0(self):
        ''' Things to do before the disassembler is let loose '''

    def round_1(self):
        ''' Let the disassembler loose '''
        cx = self.cx
        for a in range(0x80002000, 0x80002074, 4):
            cx.disass(a)

    def round_2(self):
        ''' Spelunking in what we alrady found '''
        cx = self.cx
        ioc_eeprom_exports.add_exports(
            cx.m,
            ioc_eeprom_exports.IOC_EEPROM_PART2_EXPORTS
        )

    def round_0_1e86e987852d2e14(self):
        ''' Things to do before the disassembler is let loose '''
        cx = self.cx

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
            data.Txt(cx.m, y.dst, label=False)

    def round_1_1e86e987852d2e14(self):
        ''' Let the disassembler loose '''
        cx = self.cx

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

        # EEprom writing trampoline
        data.Const(cx.m, 0x80003a2a, 0x80003a2c)
        cx.disass(0x80003a2c)

        for a, b in (
            (0x800025ce, "ask_which_boot_device"),
            (0x80002634, "boot_L"),
            (0x80002642, "boot_tape"),
            (0x800026a2, "boot_disk"),
            (0x800026d6, "boot_400S"),
            (0x8000271a, "boot_default_device"),
            (0x80002e22, "show_boot_menu"),
            (0x80002f2c, "menu_change_boot_crash_maint"),
            (0x80002f58, "menu_change_iop_config"),
            (0x80002e8c, "menu_enable_manual_crash_debugging"),
            (0x80002e84, "menu_boot_iop_ask_media"),
            (0x80003344, "REPORT_BOOT_IP_TAPE_CONFIG"),
            (0x80003526, "REPORT_TAPE_DRIVES"),
            (0x8000366e, "OUTPUT_IP_NUMBER(A1)"),
            (0x800036e8, "machine_type_table"),
            (0x8000386c, "whine_on_duarts"),
            (0x800038b0, "duart_loop"),
            (0x800038ee, "duart_step_a"),
            (0x80003914, "duart_step_b"),
            (0x8000394c, "duart_step_c"),
            (0x80003950, "duart_step_d"),
            (0x8000396c, "duart_modem_rxchar(->D0)"),
            (0x8000397a, "duart_modem_txchar(D0)"),
            (0x80003988, "duart_diag_rxchar(->D0)"),
            (0x80003996, "duart_diag_tx_mode_1b_char(D0)"),
            (0x800039b0, "duart_diag_tx_mode_1f_char(D0)"),
            (0x80003a2a, "eeprom_trampoline_magic"),
            (0x80003a2c, "eeprom_write_trampoline"),
        ):
            cx.m.set_label(a, b)

#######################################################################

def example():
    ''' Follow the example protocol '''
    return IocEepromPart2().example()

#######################################################################

if __name__ == '__main__':
    ioc_utils.mainfunc(__file__, example, IocEepromPart2)
