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

'''Regnecentralen Piccolo - RC702 boot EPROM
'''

import os
from pyreveng import job, mem, listing, code, discover, data, misc
import pyreveng.cpu.z80 as z80

def setup():
	cx = z80.z80()
	m = mem.Stackup(files=("EPROM_ROB_357.bin",), nextto=__file__)
	cx.m.map(m, 0, 0x12)
	cx.m.map(m, 0xa000, offset=0x12)
	pj = job.Job(cx.m, "RC702_bootrom_rob_357")
	return pj, cx

def task(pj, cx):
	data.Txt(pj.m, 0xa533, label=False)
	data.Txt(pj.m, 0xa546, label=False)
	data.Txt(pj.m, 0xa571, label=False)
	data.Txt(pj.m, 0xa574, label=False)
	data.Txt(pj.m, 0xa588, 0xa58c, label=False)
	data.Txt(pj.m, 0xa58c, 0xa590, label=False)
	data.Txt(pj.m, 0xa593, 0xa593 + 0x7, label=False)

	misc.fill_all_blanks(cx.m, vals={0xff,})

	cx.disass(0x0000)

	# Interrupt vector table
	for a in range(12):
		cx.codeptr(0xa000 + a * 2)

	#discover.Discover(cx)

if __name__ == '__main__':
	print(__file__)
	pj, cx = setup()
	task(pj, cx)
	listing.Listing(pj, ncol = 4)

