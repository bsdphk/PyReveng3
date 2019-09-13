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

'''Commodore CBM900 - Low-Res Character Set

See also: https://datamuseum.dk/wiki/Commodore/CBM900
'''

import os
from pyreveng import job, mem, code, data, misc, listing, charset

def mem_setup():
    m = mem.stackup(
        files=(
            ("EPROM_380217-01_R.B_PC_CHAR._U2.bin",)
        ),
        prefix=os.path.dirname(os.path.abspath(__file__)) + "/"
    )
    return m

def setup():
    pj = job.Job(mem_setup(), "CBM900_CHAR")
    cx = None
    return pj, cx

def task(pj, cx):
    s = charset.SVG_Charset(
        "/tmp/cbm900_lowres.svg",
        cols=16,
        char_w=7,
        char_h=13,
        imargin=1,
        linewidth=1,
    )
    for i in range(256):
        l = []
        for j in range(13):
            l.append(pj.m[i * 16 + j])
        s.set_char(i // 16, i % 16, l)
    s.render()


if __name__ == '__main__':
    pj, cx = setup()
    task(pj, cx)
    code.lcmt_flows(pj)
    listing.Listing(pj, ncol=8)
