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
This is the EPROM from the Commodore 900 floppy disk controller.

See also: https://datamuseum.dk/wiki/Commodore/CBM900
'''

import os
from pyreveng import job, mem, data, code, misc, listing
import pyreveng.cpu.mos6500 as mos6500

def mem_setup():
    m = mem.byte_mem(0xe000, 0x10000)
    fn = os.path.join(os.path.dirname(__file__), "EPROM_Z8000_Fl.Cont._S41_6-20-85.bin")
    m.load_binfile(0xe000, 1, fn)
    return m

def setup():
    pj = job.Job(mem_setup(), "CBM900_FDC")
    cx = mos6500.mos6500()
    return pj, cx

def task(pj, cx):
    cx.vectors(pj)
    for i in range(7):
        data.Const(pj, 0xe28a + i, 0xe28a + i + 1)
    for i in range(6):
        cx.codeptr(pj, 0xe291 + 2 * i)

    a = 0xe7bf
    pj.set_label(a, "GEOMETRY")
    for i in range(5):
        y = data.Pstruct(pj, a, "<4B")
        a = y.hi

    a = 0xe80a
    pj.set_label(a, "STEPPER_PHASE")
    y = data.Pstruct(pj, a, "<4B")

    a = 0xe675
    y = data.Pstruct(pj, a, "<4B")
    a = y.hi
    y = data.Pstruct(pj, a, "<4B")

    a = 0xe962
    y = data.Pstruct(pj, a, "<5B")
    a = 0xe967
    y = data.Pstruct(pj, a, "<B")
    a = 0xe968
    y = data.Pstruct(pj, a, "<5B")

    a = 0xff9c
    y = data.Pstruct(pj, a, "<HH")

    for a in (
        0xe034,
        0xe906,
        0xe90c,
        0xe948,
        0xe96d,
        0xe972,
        0xe977,
        0xe989,
        0xe98e,
        0xe993,
        0xea33,
        0xea36,
        0xea39,
        0xea9c,
        0xeab1,
        0xff93,
        0xff96,
        0xff99,
        0xfff3,
        0xfff6,
        0xfff9,
    ):
        pj.todo(a, cx.disass)
        pj.m.set_line_comment(a, "MANUAL")

    while pj.run():
        pass

if __name__ == '__main__':
    pj, cx = setup()
    task(pj, cx)
    code.lcmt_flows(pj)
    listing.Listing(pj, ncol=4)
