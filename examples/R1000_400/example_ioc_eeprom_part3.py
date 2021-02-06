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

from pyreveng import mem, listing, data
import pyreveng.cpu.m68020 as m68020
import pyreveng.cpu.m68000_switches as m68000_switches
import pyreveng.toolchest.srecords as srecords

import ioc_hardware
import ioc_eeprom_exports

NAME = "IOC_EEPROM_PART3"

FILENAME = os.path.join(os.path.split(__file__)[0], "IOC_EEPROM.bin")

def artifact_232718caeffce073(cx):

    ioc_eeprom_exports.add_symbols(cx.m)
    ioc_eeprom_exports.add_flow_check(cx)

    for a in (
        0x80004afe,
        0x80004b42,
        0x80004b68,
        0x80004ece,
        0x80004eeb,
        0x80004f17,
        0x80004f2c,
        0x80004f40,
        0x80004f56,
        0x80004f74,
        0x80004f8a,
        0x80004f95,
        0x80004fac,
    ):
        data.Txt(cx.m, a, splitnl=True)

    for a in range(0x80004000, 0x80004008, 4):
        cx.disass(a)

    for a, b in (
        (0x800040a0, None),
        (0x80004498, None),
        (0x800044a4, None),
        (0x800044c8, None),
        (0x800044f8, None),
        (0x80004510, None),
        (0x8000456c, None),
        (0x80004578, None),
        (0x80004648, None),
        (0x800046aa, None),
        (0x800046c2, None),
        (0x800046d0, None),
        (0x80004730, None),
        (0x80004862, None),
        (0x80004912, None),
        (0x80004ad2, None),
        (0x80004ae8, None),
        (0x80004b10, None),
        (0x80004b8c, None),
        (0x80004cd0, None),
    ):
        cx.disass(a)
        cx.m.set_line_comment(a, "MANUAL")
        if b:
            cx.m.set_label(a, b)

    ioc_eeprom_exports.add_exports(cx.m, ioc_eeprom_exports.IOC_EEPROM_PART3_EXPORTS)

def ioc_eeprom_part3(m0, ident=None):
    ''' Third part of IOC eeprom '''

    cx = m68020.m68020()
    m68000_switches.m68000_switches(cx)

    if m0[0] == 0x53 and 0x30 <= m0[1] <= 0x39:
        srec = srecords.SRecordSet().from_mem(m0)
        srec.map(cx.m, lo=0x80004000)
    else:
        # The two middle quarters of this image are swapped
        cx.m.map(m0, 0x80004000, 0x80006000, 0x2000)
        # Also map the last quarter with the configuration values
        cx.m.map(m0, 0x80006000, 0x80008000, 0x6000)

    ioc_hardware.add_symbols(cx.m)

    digest = hashlib.sha256(cx.m.bytearray(0x80004000, 0x2000)).hexdigest()[:16]
    print("DD", __file__, digest, ident)

    if digest == "232718caeffce073":
        artifact_232718caeffce073(cx)
    else:
        for a in range(0x80004000, 0x80004008, 4):
            cx.disass(a)

    return cx

def example():
    ''' Third part of IOC eeprom '''

    m0 = mem.Stackup((FILENAME,))
    cx = ioc_eeprom_part3(m0)

    return NAME, (cx.m,)

#######################################################################

if __name__ == '__main__':
    import sys

    if len(sys.argv) == 5 and sys.argv[1] == "-AutoArchaeologist":
        print(__file__, sys.argv)
        mb = mem.Stackup((sys.argv[3],))
        cx = ioc_eeprom_part3(mb, sys.argv[2])
        listing.Listing(cx.m, fn=sys.argv[4], ncol=8, leaf_width=72)
        exit(0)

    listing.Example(example, ncol=8)
