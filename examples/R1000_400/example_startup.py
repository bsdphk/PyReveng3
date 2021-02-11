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
   Total startup memory picture
   ----------------------------
'''

from pyreveng import mem, listing
import pyreveng.cpu.m68020 as m68020
import pyreveng.cpu.m68000_switches as m68000_switches

import ioc_hardware
import ioc_eeprom_exports
import ioc_m200_exports

import example_ioc_eeprom_part1
import example_ioc_eeprom_part2
import example_ioc_eeprom_part3
import example_ioc_eeprom_part4
import example_ioc_resha_eeprom
import example_ioc_dfs_bootstrap
import example_ioc_kernel
import example_ioc_fs
import example_ioc_startup

import m200_pushtxt

NAME = "IOC_STARTUP"

#######################################################################

class Startup():

    ''' The total picture after bootstrap '''

    def __init__(self, ramfile=None):
        self.cx = m68020.m68020()

        self.parts = [
            example_ioc_eeprom_part1.IocEepromPart1(cx=self.cx),
            example_ioc_eeprom_part2.IocEepromPart2(cx=self.cx),
            example_ioc_eeprom_part3.IocEepromPart3(cx=self.cx),
            example_ioc_eeprom_part4.IocEepromPart4(cx=self.cx),
            example_ioc_resha_eeprom.ReshaEeprom(cx=self.cx),
            example_ioc_dfs_bootstrap.DfsBootstrap(cx=self.cx),
            example_ioc_kernel.IocKernel(cx=self.cx),
            example_ioc_fs.IocFs(cx=self.cx),
            example_ioc_startup.IocStartup(cx=self.cx),
        ]
        for i in self.parts:
            i.default_image()
            i.augment_cx()

        if ramfile:
            self.load_ram(ramfile)

        m68000_switches.m68000_switches(self.cx)
        m200_pushtxt.add_pushtxt(self.cx)
        ioc_hardware.add_symbols(self.cx.m)
        ioc_eeprom_exports.add_symbols(self.cx.m)
        ioc_eeprom_exports.add_flow_check(self.cx)
        ioc_m200_exports.add_symbols(self.cx.m)

        for i in range(3):
            for j in self.parts:
                j.ponder_round(i)

    def load_ram(self, ramfile):
        ''' Load a RAM dump on top '''
        mram = mem.Stackup((ramfile,))

        # Map missing regions
        fm = 0
        for i in list(sorted(self.cx.m.mapping)):
            lo = i[0]
            hi = i[1]
            to = min(lo, mram.hi)
            if fm < to:
                m = mem.ByteMem(0, to-fm)
                self.cx.m.map(m, fm, to)
            fm = hi

        for i in list(sorted(self.cx.m.mapping)):
            print("%08x" % i[0], "%08x" % i[1], i[2:])
        # Overwrite with RAM content
        for i in range(mram.lo, mram.hi):
            self.cx.m[i] = mram[i]

    def example(self):
        ''' example protocol function '''
        return NAME, (self.cx.m,)

#######################################################################

def example():
    ''' Follow the example protocol '''
    return Startup().example()

#######################################################################

if __name__ == '__main__':

    import sys

    if len(sys.argv) == 2 and sys.argv[1] == "-ram":
        listing.Example(Startup("/tmp/_.ram").example, ncol=8)
    else:
        listing.Example(example, ncol=8)
