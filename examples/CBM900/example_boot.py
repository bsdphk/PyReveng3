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
This is the boot EPROM(s) from the Commodore 900.

See also: https://datamuseum.dk/wiki/Commodore/CBM900
'''

import os
from pyreveng import job, mem, code, data, misc, listing
import pyreveng.cpu.z8000 as z8000

def mem_setup():
    m = mem.byte_mem(0x0, 0x8000)
    fn = os.path.join(os.path.dirname(__file__), "EPROM_C_900_boot-")
    m.load_binfile(0x1, 2, fn + "L_V_1.0.bin")
    m.load_binfile(0x0, 2, fn + "H_V_1.0.bin")
    return m

def setup():
    pj = job.Job(mem_setup(), "CBM900_BOOT")
    cx = z8000.z8001()
    return pj, cx

def task(pj, cx):
    pj.set_label(0x0090, "size_ram")
    pj.set_label(0x00ca, "ram_sized")
    pj.set_label(0x00f4, "copy_dataseg")
    pj.set_label(0x023a, "SetMMU(int seg, int base1, int base2)")
    cx.vectors(pj)
    for v, a in (
	("VEC0", 0x0008,),
	("VEC1", 0x0010,),
	("VEC2", 0x0018,),
	("VEC3", 0x0020,),
	("VEC4", 0x0028,),
	("VEC5", 0x0030,),
    ):
        cx.vector(pj, a, v)

    for a in range(0x06b2, 0x06da, 4):
        y = cx.codeptr(pj, a)
        pj.set_label(y.dst, "PTR_%x" % a)

    for a in range(0x31cc, 0x31dc, 4):
        y = cx.codeptr(pj, a)
        pj.set_label(y.dst, "PTR_%x" % a)

    for a in range(0x39da, 0x3a18, 4):
        y = cx.codeptr(pj, a)
        pj.set_label(y.dst, "PTR_%x" % a)

    for a in range(0x419e, 0x4202, 4):
        y = cx.codeptr(pj, a)
        pj.set_label(y.dst, "PTR_%x" % a)

    pj.todo(0x20bc, cx.disass)
    pj.todo(0x3ec6, cx.disass)

    for a in (
        0x0c08,
        0x01ba,
        0x0c3e,
        0x0e98,
        0x0ea8,
        0x0eda,
        0x0eea,
    ):
        pj.m.set_block_comment(a, "CALL_RR10_%x" % a)
        pj.todo(a + 2, cx.disass)

    pj.m.set_block_comment(0x6800, "DATA SEGMENT, len=0x1016")

    y = data.Data(pj, 0x45fe, 0x6706)
    y.compact = True
    pj.m.set_label(0x45fe, "CHARGEN")

    while pj.run():
        pass

    misc.fill_all_blanks(pj, minsize=2)

    while pj.run():
        pass


if __name__ == '__main__':
    pj, cx = setup()
    task(pj, cx)
    code.lcmt_flows(pj)
    listing.Listing(pj, ncol=4)
