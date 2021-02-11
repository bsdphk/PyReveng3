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
   IOC FS_?.M200 - DFS filesystem
   ------------------------------
'''

import os

from pyreveng import mem, data

import ioc_utils
import ioc_hardware
import ioc_eeprom_exports
import ioc_m200_exports
import example_ioc_kernel
import m200_pushtxt

NAME = "IOC_FS"
BASE = 0x10000
FILENAME = os.path.join(os.path.split(__file__)[0], "FS_0.M200")

#######################################################################

class IocFs(ioc_utils.IocJob):
    ''' A FS_[012].M200 program '''

    def __init__(self, **kwargs):
        super().__init__(BASE, name=NAME, **kwargs)

    def default_image(self):
        ''' Load default image '''
        self.map(mem.Stackup((FILENAME,)))

    def config_cx(self):
        cx = self.cx
        example_ioc_kernel.IocKernel(cx=cx).augment_cx()
        m200_pushtxt.add_pushtxt(cx)
        ioc_hardware.add_symbols(cx.m)
        ioc_eeprom_exports.add_symbols(cx.m)
        ioc_m200_exports.add_symbols(cx.m)

    def round_1(self):
        ''' Let the disassembler loose '''
        cx = self.cx
        cx.codeptr(0x10004)

        for a in ioc_m200_exports.fs_entrypoints():
            y = cx.disass(a)
            j = getattr(y, 'dstadr', None)
            i = list(cx.m.get_labels(a))
            if len(i) > 0 and j:
                cx.m.set_label(j, "_" + i[0])

    def round_0_6176fa9c7c3f0972(self):
        ''' Things to do before the disassembler is let loose '''
        cx = self.cx

        for a, b in (
            (0x00017c4a, "something_dir_read()"),
            (0x0001857e, "HexDigitToBin()"),
            (0x0001061c, "FS_INIT()"),
            (0x00010648, "BOUNCE_TO_PROOGRAM()"),
        ):
            if b is None:
                b = "L_%08x" % a
            cx.m.set_label(a, b)

        for a,b in (
            (0x15106, 0x1510c),
            (0x1510c, 0x15114),
            (0x15ca8, 0x15cc2),
            (0x1745c, 0x1746c),
            (0x18204, 0x18222),
            (0x18222, 0x18238),
            (0x19794, 0x197a4),
            (0x1a254, 0x1a282),
        ):
            data.Txt(cx.m, a, b, splitnl=True)

    def round_1_6176fa9c7c3f0972(self):
        ''' Let the disassembler loose '''
        cx = self.cx
        for a, b in (
            (0x118a2, "see 0x11914"),
            (0x11a36, "see 0x11ba2"),
        ):
            cx.disass(a)
            cx.m.set_block_comment(a, b)

#######################################################################

def example():
    ''' Follow the example protocol '''
    return IocFs().example()

#######################################################################

if __name__ == '__main__':
    ioc_utils.mainfunc(__file__, example, IocFs)
