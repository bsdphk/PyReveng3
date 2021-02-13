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
   The RESHA eeprom (binary/S-Records)
   -----------------------------------
'''

import os

from pyreveng import mem, data

import ioc_utils
import ioc_hardware
import ioc_eeprom_exports

NAME = "IOC_RESHA_EEPROM"
BASE = 0x70000
SIZE = 0x8000
SEGMENT = 0x2000
FILENAME = os.path.join(os.path.split(__file__)[0], "RESHA_EEPROM.bin")

#######################################################################

class ReshaEeprom(ioc_utils.IocJob):

    ''' A RESHA Eeprom in binary or S-Records'''

    def __init__(self, **kwargs):
        super().__init__(BASE, BASE+SIZE, name=NAME, **kwargs)

    def default_image(self):
        ''' Load default image '''
        self.map(mem.Stackup((FILENAME,)))

    def config_cx(self):
        ''' Add global symbol sets etc. '''
        cx = self.cx
        ioc_eeprom_exports.add_flow_check(self.cx)
        ioc_hardware.add_symbols(cx.m)
        ioc_eeprom_exports.add_symbols(cx.m)

    def round_0(self):
        ''' Things to do before the disassembler is let loose '''
        cx = self.cx

        for a in range(BASE, BASE+SIZE, SEGMENT):
            cx.m.set_block_comment(a, "PROGRAM VECTORS")
            data.Const(cx.m, a, a + 2)

        for a, b in (
            (0x76084, 0x760c8),
        ):
            for i in range(a, b, 4):
                y = cx.dataptr(i)
                data.Txt(cx.m, y.dst)

        for a, b in (
            (0x7063e, 0x70708),
            (0x71025, 0x7105f),
            (0x712a6, 0x7130c),
            (0x719f2, 0x71a99),
            (0x74006, 0x7412e),
            (0x76248, 0x763b1),
        ):
            i = a
            while i < b:
                y = data.Txt(cx.m, i, splitnl=True)
                i = y.hi

        for a in range(0x765e4, 0x76650, 6):
            y = cx.dataptr(a + 2)
            data.Txt(cx.m, y.dst)

        for a in (
            0x7200a,
            0x769ce,
            0x769ec,
            0x76a0a,
            0x76a28,
        ):
            data.Txt(cx.m, a, splitnl=True)

    def round_1(self):
        ''' Let the disassembler loose '''
        cx = self.cx
        for key, desc in ioc_eeprom_exports.RESHA_PROGRAMS.items():
            a = BASE + SEGMENT * (key & 0xff)
            ptr = a + (key >> 7)
            data.Const(cx.m, ptr, ptr + 2, func=cx.m.bu16, size=2)
            prog = a + cx.m.bu16(ptr)
            cx.disass(prog)
            cx.m.set_label(prog, "RESHA_PROGRAM_%04x" % key)
            t = "RESHA PROGRAM 0x%04x @0x%08x - " % (key, prog) + desc
            cx.m.set_block_comment(prog, t)
            cx.m.set_line_comment(ptr, t)

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
            (0x730a8, None),
            (0x73258, None),
            (0x733a2, None),
            (0x73396, None),
            (0x74266, "SCSI_D_TEST_UNIT_READY"),
            (0x743dc, "SCSI_D_SOFT_RESET()"),
            (0x7459a, "SCSI_D_AWAIT_INTERRUPT()"),
            (0x77386, "SCSI_T_AWAIT_INTERRUPT()"),
            (0x77662, None),
        ):
            cx.disass(a)
            if b:
                cx.m.set_label(a, b)

        for a, b in (
            (0x000743e6, "SCSI_ID=7, EnableAdvancedFeatures"),
            (0x000743ee, "CMD=Soft Reset"),
            (0x71206, "????"),
            (0x71212, "B#13 = GOOD_PARITY"),
            (0x714da, "B#13 = GOOD_PARITY"),
        ):
            cx.m.set_line_comment(a, b)

#######################################################################

def example():
    ''' Follow the example protocol '''
    return ReshaEeprom().example()

#######################################################################

if __name__ == '__main__':
    ioc_utils.mainfunc(__file__, example, ReshaEeprom)
