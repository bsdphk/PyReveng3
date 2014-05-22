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

# P1.0 + P1.1 = outher switch
# P1.2 + P1.3 = inner switch
# P1.4 3 right buttons
# P1.5 3 left buttons
# P3.3 tied to P3.4 T0->INT1
# P3.2 INT0 probably from main CPU

from __future__ import print_function

import os
import sys

from pyreveng import job, mem, data, listing, code
import pyreveng.cpu.mcs51 as mcs51

m = mem.byte_mem(0x0000, 0x1000)
m.load_binfile(0x0000, 1, "618TCA_CDU_U20_U12_PN_138_0192_V_2_2_C_U5.bin")
pj  = job.Job(m, "Apollo618c_cdu")


if False:
	pj.a.address_space("xrom", m)
	pj.a.address_space("xdata", mem.address_space(0, 0x10000))
	pj.a.address_space("idata", mem.address_space(0, 0x100))

	for i in pj.a:
		print(i, pj.a[i])
	exit(0)

cx = mcs51.i8032()

cx.set_adr_mask(0xfff)

cx.vectors(pj)

# Random
# pj.todo(0x7d2, cx.disass)

for i in range(0, 0x18, 8):
	data.Txt(pj, 0x0a2 + i, 0x0a2 + i + 0x08, label=False)

for i in range(0, 0x18, 8):
	data.Txt(pj, 0x78a + i, 0x78a + i + 0x08, label=False)

#######################################################################

while pj.run():
	pass


code.lcmt_flows(pj)

#######################################################################
def cmd_func(a1, a2, n):
	pj.set_label(a1, "DO_CMD%d" % n)
	a = a2
	while True:
		if pj.m[a] != 0xb4:
			break
		c = pj.m[a + 1]
		d = pj.m[a + 2]
		pj.set_label(a, "CMD%d_%02x" % (n, c))
		a += 3 + d


cmd_func(0xbf3, 0xbf7, 1)
cmd_func(0x823, 0x827, 2)
cmd_func(0x84f, 0x851, 3)
#######################################################################

pj.set_label(0x028, "ZERO_RAM")
pj.set_label(0x039, "MAIN_LOOP")
pj.set_label(0x050, "SETUP")
pj.set_label(0x70e, "CHAR_XLAT")
# 0x5b...0x5d are bits to blink characters
pj.set_label(0x72e, "CHAR_BLINK")
pj.set_label(0x76d, "WATCHDOG")
pj.set_label(0x800, "MAIN_CMD")
pj.set_label(0xc8c, "RX_INTR")
pj.set_label(0xc54, "TX_INTR")

#######################################################################
for a in range(0xba, 0x100, 2):
	x = data.Const(pj, a, a + 2)
	x.typ = ".WORD"
	x.val = pj.m.lu16(a)
	x.fmt = "0x%04x" % x.val

#######################################################################

x = pj.add(0x100, 0x600, "chargen")
x.rendered = "*CHARGEN*"
x.compact = True

if False:
	for c in range(256):
		print("%02x" % c)
		for r in range(8):
			s = ""
			j = 0x80 >> r
			for a in range(0x100, 0x600, 0x100):
				v = pj.m[a + c]
				if v & j:
					s += "#"
				else:
					s += "-"
			print(s)
		print("")

#######################################################################

#data--- pj.set_label(0x5e, "timeout") 
#######################################################################

if False:
	import a2
	a = a2.analysis(pj)
	a.dot(pj, "/tmp/_1.dot")
	a.reduce(pj)
	a.dot(pj, "/tmp/_2.dot")

listing.Listing(pj, "/tmp/_.apollo618_cdu.txt", ncol = 3, fmt = "x", ascii = True)
