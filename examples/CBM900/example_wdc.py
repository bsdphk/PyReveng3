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

'''Commodore CBM900 - Hard Disk Controller

See also: https://datamuseum.dk/wiki/Commodore/CBM900
'''

import os
from pyreveng import job, mem, data, misc, listing
import pyreveng.cpu.mcs48 as mcs48

def mem_setup():
    return mem.stackup(("MCU_WDC_U10.bin",), nextto=__file__)

def setup():
    cx = mcs48.mcs48()
    m = mem_setup()
    cx.m.map(m, 0)
    pj = job.Job(cx.m, "CBM900_WDC")
    return pj, cx

def task(pj, cx):
    cx.vectors(pj)
    for a in range(0x0a, 0x21):
        t = pj.m[a]
        data.Codeptr(pj, a, a + 1, t)
        pj.todo(t, cx.disass)
        pj.m.set_block_comment(t, "From PTR 0x%x" % a)
    for a in range(0x000, 0x800, 0x100):
        cx.disass(pj, a + 0xfe)
    data.Txt(pj, 0x5ae, 0x5dc, label=False)
    data.Txt(pj, 0x5dc, 0x5f4, label=False)

    for a in (
            0x695,
            0x700,
            0x70d,
            0x720,
    ):
        pj.todo(a, cx.disass)
        pj.m.set_block_comment(a, "Manual")

    while pj.run():
        pass

    misc.fill_all_blanks(pj, minsize=2)

if __name__ == '__main__':
    pj, cx = setup()
    task(pj, cx)
    listing.Listing(pj, ncol=2)
