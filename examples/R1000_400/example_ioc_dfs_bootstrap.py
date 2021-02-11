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

'''
   DFS_BOOTSTRAP.M200 binary files
   -------------------------------

   This lives in sector #0 on the harddisk(s?)
'''

import os

from pyreveng import mem, data

import ioc_eeprom_exports
import ioc_hardware
import ioc_utils

NAME = "IOC_DFS_BOOTSTRAP"
BASE = 0x54000
FILENAME = os.path.join(os.path.split(__file__)[0], "M400_DFS_BOOTSTRAP.M200")

def flow_check(asp, ins):
    ''' Flow-check to capture inline strings '''
    for flow in ins.flow_out:
        if flow.to in (
            0x5403e,
        ):
            y = data.Txt(asp, ins.hi, label=False, align=2, splitnl=True)
            ins.dstadr = y.hi
            ins.flow_out.pop(-1)

#######################################################################

class DfsBootstrap(ioc_utils.IocJob):

    ''' A First sector DFS bootstrap code '''

    def __init__(self, **kwargs):
        super().__init__(BASE, name=NAME, **kwargs)

    def default_image(self):
        ''' Load default image '''
        self.map(mem.Stackup((FILENAME,)))

    def config_cx(self):
        ''' Add global symbol sets etc. '''
        cx = self.cx
        ioc_eeprom_exports.add_flow_check(cx)
        ioc_eeprom_exports.add_symbols(cx.m)
        ioc_hardware.add_symbols(cx.m)

    def round_0(self):
        ''' Things to do before the disassembler is let loose '''
        cx = self.cx
        cx.flow_check.append(flow_check)
        cx.m.set_label(0x5403e, "BAIL_OUT")
        cx.m.set_label(0x5405e, "DEVICE_TYPE_2")

    def round_1(self):
        ''' Let the disassembler loose '''
        cx = self.cx
        cx.disass(BASE)

    def round_0_c665a17f1e356161(self):
        ''' Things to do before the disassembler is let loose '''
        cx = self.cx
        cx.m.set_label(0x540fc, "READ_DISK_FILE")
        cx.m.set_label(0x5424c, "DEVICE_TYPE_3")

    def round_0_82a46de15cfc64d0(self):
        ''' Things to do before the disassembler is let loose '''
        cx = self.cx
        cx.m.set_label(0x540fc, "READ_DISK_FILE")
        cx.m.set_label(0x5424c, "DEVICE_TYPE_3")

    def round_0_131ecee574f7c0d5(self):
        ''' Things to do before the disassembler is let loose '''
        cx = self.cx
        cx.m.set_label(0x5410e, "READ_DISK_FILE")
        cx.m.set_label(0x54206, "DEVICE_TYPE_3")
        data.Txt(cx.m, 0x5437a)

#######################################################################

def example():
    ''' Follow the example protocol '''
    return DfsBootstrap().example()

#######################################################################

if __name__ == '__main__':
    ioc_utils.mainfunc(__file__, example, DfsBootstrap)
