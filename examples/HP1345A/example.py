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
from pyreveng import job, mem, listing, data, code, assy
import pyreveng.cpu.mcs48 as mcs48
import pyreveng.cpu.hp1345a as hp1345a

fw="01347-80010.bin"

#######################################################################

def setup():
	m = mem.byte_mem(0x0, 0x400)
	m.load_binfile(0x0, 1, os.path.join(os.path.dirname(__file__), fw))

	pj = job.Job(m, "HP1345A")
	cpu = mcs48.i8748()
	return pj,cpu

#######################################################################

def task(pj, cx):
	cpu = mcs48.i8748()
	gpu = hp1345a.hp1345a()

	pj.set_label(0x00a, "reset")
	pj.set_label(0x010, "int")
	pj.set_label(0x014, "tint")
	pj.set_label(0x017, "RESET_TIMER")
	pj.set_label(0x01d, "R1d")
	pj.set_label(0x032, "MEMTST")
	pj.set_label(0x048, "048")
	pj.set_label(0x06e, "06e")
	pj.set_label(0x0a1, "Ra1")
	pj.set_label(0x0ac, "0ac")
	pj.set_label(0x0c2, "0c2")
	pj.set_label(0x0d2, "0d2")
	pj.set_label(0x0d6, "0d6")
	pj.set_label(0x0de, "0de")
	pj.set_label(0x0ea, "0ea")
	pj.set_label(0x100, "ALIGN")
	pj.set_label(0x200, "ALIGN2")
	pj.set_label(0x300, "FOCUS")

	cpu.vectors(pj)

	while pj.run():
		pass

	for a in range(0x122, 0x200, 2):
		gpu.disass(pj, a)

	for a in range(0x222, 0x2c8, 2):
		gpu.disass(pj, a)

	for a in range(0x31e,0x400, 2):
		gpu.disass(pj, a)

def output(pj):
	code.lcmt_flows(pj)
	listing.Listing(pj, ncol=2)

if __name__ == '__main__':
	print(__file__)
	pj, cx = setup()
	task(pj, cx)
	output(pj)

