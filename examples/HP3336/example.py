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

'''HP3336 Synthesizer/Level Generator
'''

import os
from pyreveng import job, mem, listing, data
import pyreveng.cpu.hp_nanoproc as hp_nanoproc

import common

def mem_setup():
	m = mem.byte_mem(0x0000, 0x4000)
	fn = os.path.join(os.path.dirname(__file__), "hp3336.bin")
	m.load_binfile(0, 1, fn)
	return m

def setup():

	dx = hp_nanoproc.hp_nanoproc_pg()
	dx.m.map(mem.Stackup(("hp3336.bin",), nextto=__file__), 0)

	pj = job.Job(dx.m, "HP3336")
	return pj, dx

def task(pj, dx):
	dx.disass(0)
	dx.disass(0xff)

	#######################################################################
	if True:
		for a0 in range(4,0x20,4):
			assert pj.m[a0] == 0xc8
			pg = (pj.m[a0 + 1] & 0x07) << 11
			assert pg == a0 << 9
			dpf = pj.m[a0 + 2] << 8
			dpf |= pj.m[a0 + 3]
			dpf &= 0x7ff
			dpf |= pg
			pj.m.set_label(dpf, "DISP_%d" % (a0 >> 2))
			dx.disass(a0)
			dx.disass(dpf)
			for a1 in range(pg, dpf, 2):
				da = pj.m[a1] << 8
				da |= pj.m[a1 + 1]
				da &= 0x7ff
				da |= pg
				v = a0 << 3
				v |= (a1 - pg) >> 1
				pj.m.set_label(a1, "PTR_%02x" % v)
				pj.m.set_label(da, "FN_%02x" % v)
				dx.disass(a1)


	#######################################################################
	def jmp_table(lo, hi, span, txt = "table"):
		x = data.Range(pj.m, lo, hi, "table")
		# x = pj.m.set_line_comment(lo, "table")
		for a in range(lo, hi, span):
			dx.disass(a)
		# x.blockcmt = "-\n" + txt + "\n-\n"
		return x

	#######################################################################
	if True:
		# Comes from 0x0d01
		# returns to 0xd02
		jmp_table(0x0f80, 0x0fa8, 4, "LED Segment Table")

	#######################################################################
	if True:
		# Comes from 0xab2
		# does not return
		jmp_table(0x0fa8, 0x0fc0, 2)

	#######################################################################
	if True:
		# Comes from 0xb3b
		# returns to 0xb3c
		jmp_table(0x0fc0, 0x0fe0, 4)

	#######################################################################
	if True:
		# Comes from 0xb62
		# returns to 0xb63
		jmp_table(0x0fe0, 0x1000, 4)

	#######################################################################
	if True:
		# Comes from 0x1aa0
		# returns to 1aa1
		jmp_table(0x1840, 0x1878, 8)

	#######################################################################
	if True:
		# Comes from 0x29f9
		# returns to 29fa
		x = jmp_table(0x2fb8, 0x3000, 8)

	#######################################################################
	if True:
		# Comes from 0x3c37
		# does RET
		x = jmp_table(0x3fd8, 0x4000, 4)

	#######################################################################
	if True:
		for a,l in common.SYMBOLS.items():
			pj.m.set_label(a,l)

if __name__ == '__main__':
	pj, cx = setup()
	task(pj, cx)
	listing.Listing(pj)

