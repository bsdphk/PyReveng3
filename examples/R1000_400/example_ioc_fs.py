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
# XXX: extend m200_pushtxt to match also here

'''
   IOC FS
   ------
'''

import os

from pyreveng import mem, listing, data, assy
import pyreveng.cpu.m68020 as m68020
import pyreveng.cpu.m68000_switches as m68000_switches

import ioc_hardware
import ioc_eeprom_exports
import ioc_m200_exports

NAME = "IOC_FS"

FILENAME = os.path.join(os.path.split(__file__)[0], "FS_0.M200")

KERNEL_DESC = '''
KERNCALL	vect,>J         |1 0 1 0 0 0 0 0| vect          |
PANIC.W		tvect,>R        |0 1 0 1|0 0 0 0|1 1 1 1|1 0 1 0| w                             |
TRAP12		tvect		|0 1 0 0|1 1 1 0|0 1 0 0|1 1 0 0| w				|
'''

class KernelIns(m68020.m68020_ins):
    ''' Kernel specific instructions '''

    def assy_tvect(self):
        ''' A-Line trap into kernel '''
        return assy.Arg_imm(self['w'])

def ioc_fs_file(m0, ident=None):
    ''' Generic IOC FS program '''
    cx = m68020.m68020()
    m68000_switches.m68000_switches(cx)
    cx.it.load_string(KERNEL_DESC, KernelIns)

    cx.m.map(m0, 0x00010000)

    ioc_hardware.add_symbols(cx.m)
    ioc_eeprom_exports.add_symbols(cx.m)
    ioc_m200_exports.add_symbols(cx.m)

    cx.codeptr(0x10004)

    for a in ioc_m200_exports.fs_entrypoints():
        y = cx.disass(a)
        j = getattr(y, 'dstadr', None)
        i = list(cx.m.get_labels(a))[0]
        if i and j:
            cx.m.set_label(j, "_" + i)

    return cx

def example():
    ''' Specific IOC FS program '''
    m0 = mem.Stackup((FILENAME,))
    cx = ioc_fs_file(m0)

    for a in (
    ):
        data.Txt(cx.m, a, splitnl=True)

    for a, b in (
        (0x118a2, "see 0x11914"),
        (0x11a36, "see 0x11ba2"),
    ):
        cx.disass(a)
        cx.m.set_block_comment(a, b)

    return NAME, (cx.m,)

#######################################################################

if __name__ == '__main__':
    import sys

    if len(sys.argv) == 5 and sys.argv[1] == "-AutoArchaeologist":
        mb = mem.Stackup((sys.argv[3],))
        cx = ioc_fs_file(mb, sys.argv[2])
        listing.Listing(cx.m, fn=sys.argv[4], ncol=8, leaf_width=72)
        exit(0)

    listing.Example(example, ncol=8)
