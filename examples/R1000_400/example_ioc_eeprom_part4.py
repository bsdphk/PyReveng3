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
   Fourth quarter of the IOC EEPROM
   --------------------------------

   Per-site/machine Configuration Data
'''

import os

from pyreveng import mem

import ioc_utils
import ioc_eeprom_exports

NAME = "IOC_EEPROM_PART4"
BASE = 0x80006000
SIZE = 0x2000

FILENAME = os.path.join(os.path.split(__file__)[0], "IOC_EEPROM.bin")

#######################################################################

class IocEepromPart4(ioc_utils.IocJob):
    ''' Fourth quarter of IOC EEPROM image '''

    def __init__(self, **kwargs):
        super().__init__(BASE, BASE+SIZE, name=NAME, **kwargs)

    def default_image(self):
        ''' Load default image '''
        self.map(mem.Stackup((FILENAME,)), offset=0x6000)

    def config_cx(self):
        ''' Add global symbol sets etc. '''

    def round_0(self):
        ''' Things to do before the disassembler is let loose '''
        cx = self.cx
        ioc_eeprom_exports.add_exports(
            cx.m,
            ioc_eeprom_exports.IOC_EEPROM_PART4_EXPORTS
        )

    def round_1(self):
        ''' Let the disassembler loose '''

#######################################################################

def example():
    ''' Follow the example protocol '''
    return IocEepromPart4().example()

#######################################################################

if __name__ == '__main__':
    ioc_utils.mainfunc(__file__, example, IocEepromPart4)
