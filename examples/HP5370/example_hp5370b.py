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

'''HP5370B Time Interval Counter
'''

from pyreveng import listing, code, data, seven_segment
from . import utils

def setup():
	return utils.setup("HP5370B", "HP5370B.ROM", -1)


def task(pj, cpu):
	ct = utils.cmd_tbl(pj, 0x7c64, 0x7c98)
	cta = utils.arg_range(pj, ct, 0x7d6c, 0x7d88)

	def ptr(pj, a):
		return data.Dataptr(pj, a, a + 2, pj.m.bu16(a))

	def cbyte(pj, a):
		c = data.Const(pj, a, a + 1)
		c.val = pj.m[a]
		c.typ = ".BYTE"
		c.fmt = "0x%02x" % c.val

	ptr(pj, 0x6403)
	ptr(pj, 0x6405)
	ptr(pj, 0x6407)

	pj.set_label(0x7eed, "RAM_TEST_VALS")
	for a in range(0x7eed, 0x7ef9):
		cbyte(pj,a)

	c = ptr(pj, 0x7915)
	pj.set_label(c.lo, "@7SEGCODES")
	pj.set_label(c.dst, "7SEGCODES")
	c = seven_segment.table(pj, c.dst, c.dst + 0x10, verbose=False)

	pj.set_label(0x7ead, "ROM_LOCS")
	for a in range(0x7ead, 0x7ebf, 2):
		ptr(pj, a)

	# XXX: Add mising flow
	pj.todo(0x6845, cpu.disass)
	pj.todo(0x6867, cpu.disass)

	for i in range(0x6b23, 0x6b3b, 3):
		utils.data24(pj, i)

	for a in range(0x77d7, 0x77f7, 4):
		data.Txt(pj, a, a + 4)

	data.Txt(pj, 0x78f3, 0x78f7)
	data.Txt(pj, 0x78f7, 0x78fd)
	data.Txt(pj, 0x78fd, 0x78ff)

	utils.cmd_dispatch(pj, cpu, cta, 0x644c)

	pj.set_label(0x66ea, "ERR5_UNDEF_KEY")
	utils.key_dispatch(pj, cpu, 0x640c, 0x644c)

	utils.dsp_dispatch(pj, cpu, 0x6848, 0x6858)

	for i in (0x614c, 0x619c, 0x61a3, 0x69dd, 0x69e4):
		utils.float70(pj, i)

	c = cpu.codeptr(pj, 0x7909)
	pj.set_label(c.dst, "HPIB_CMD_PARSE")

	utils.square_tbl(pj)

	while pj.run():
		pass

	utils.apply_labels(pj, "B")
	utils.tramp(pj)

if __name__ == '__main__':
	pj, cx = setup()
	task(pj, cx)
	listing.Listing(pj)

