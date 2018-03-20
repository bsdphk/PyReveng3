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

from __future__ import print_function

import os
from pyreveng import job, mem, listing, code, discover, data
import pyreveng.cpu.z80 as z80

def mem_setup():
	m = mem.byte_mem(0x0000, 0x10000)
	dn = os.path.dirname(__file__)
	m.load_binfile(0x0000, 1, os.path.join(dn, "EPROM_ROB_357.bin"))

	for a in range(0x7ee):
		m.wr(0xa000 + a, m.rd(0x0012 + a))
	return m

def setup():
	pj = job.Job(mem_setup(), "RC702_bootrom_rob_357")
	cx = z80.z80()
	return pj, cx

def task(pj, cx):
	data.Txt(pj, 0xa533, label=False)
	data.Txt(pj, 0xa546, label=False)
	data.Txt(pj, 0xa571, label=False)
	data.Txt(pj, 0xa574, label=False)
	data.Txt(pj, 0xa593, 0xa593 + 0x7, label=False)

	pj.todo(0x0000, cx.disass)
	x = data.Const(pj, 0x0012, 0x0800)
	x.typ = ".BYTE"
	x.fmt = "{Payload moved to 0xa000}"

	# Interrupt vector table
	for a in range(12):
		cx.codeptr(pj, 0xa000 + a * 2)


	#discover.Discover(pj, cx)

	return

	# 0x70e5
	pj.todo(0x0027, cx.disass)

	pj.todo(0x0066, cx.disass)


	pj.todo(0x70d0, cx.disass)

	pj.todo(0x7322, cx.disass)
	pj.todo(0x7615, cx.disass)

	# Interrupt vector table
	for a in range(16):
		cx.codeptr(pj, 0x7300 + a * 2)

	data.Txt(pj, 0x707d, 0x707d + 0x14, label=False)
	data.Txt(pj, 0x70b0, 0x70b0 + 0xf, label=False)
	data.Txt(pj, 0x7092, 0x7092 + 0x1d, label=False)
	data.Txt(pj, 0x73f0, 0x73f0 + 0x12, label=False)
	data.Txt(pj, 0x7071, 0x7071 + 0x6, label=False)
	data.Txt(pj, 0x7077, 0x7077 + 0x6, label=False)

	discover.Discover(pj, cx)

	pj.set_label(0x7068, "memcpy(BC, DE,  L)")

def output(pj):
	listing.Listing(pj, ncol = 4)

if __name__ == '__main__':
	print(__file__)
	pj, cx = setup()
	task(pj, cx)
	output(pj)

