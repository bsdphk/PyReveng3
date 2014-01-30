#!/usr/local/bin/python
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
import sys

#######################################################################
# Set up a search path to two levels below

sys.path.insert(0, os.path.abspath(os.path.join("..", "..", "pyreveng")))

#######################################################################

symbols = {
	0x1047:	"CMD_RE",
	0x104b:	"CMD_SR",
	0x1053:	"CMD_SE",
	0x1057:	"CMD_DE",
	0x105b:	"CMD_HZ",
	0x105f:	"CMD_KH",
	0x1063:	"CMD_MH",
	0x108b:	"CMD_AP",
	0x108f:	"CMD_AB",
	0x109f:	"CMD_DB",
	0x10cb:	"CMD_ST",
	0x10cf:	"CMD_SP",
	0x10d3:	"CMD_FR",
	0x10d7:	"CMD_MF",
	0x114b:	"CMD_AM",
	0x118e:	"CMD_PH",
	0x1192:	"CMD_TI",
	0x1233: "txt_HZ",
	0x123e: "txt_DB",
	0x1247: "txt_DE",
	0x124d: "txt_SE",
	0x12bd:	"CMD_done",
	0x12f9:	"has_I",
	0x130a:	"has_A",
	0x1311:	"has_AB",
	0x1315:	"has_IAB",
	0x1336:	"has_AM",
	0x133f:	"has_AP",
	0x1348:	"has_D",
	0x134F:	"has_DB",
	0x1358:	"has_DE",
	0x1361:	"has_E",
	0x1368:	"has_ER",
	0x136c:	"has_IER",
	0x137e:	"has_F",
	0x138a:	"has_FR",
	0x1395:	"has_FL",
	0x1399:	"has_IFL",
	0x13ba:	"has_H",
	0x13c6:	"has_HZ",
	0x13cf:	"has_K",
	0x13d6:	"has_KH",
	0x13df:	"has_M",
	0x13e6:	"has_MA",
	0x13ea:	"has_IMA",
	0x140a:	"has_MP",
	0x140e:	"has_IMP",
	0x142e:	"has_MS",
	0x1440:	"has_MF",
	0x1449:	"has_MD",
	0x145e:	"has_MH",
	0x1467:	"has_O",
	0x146e:	"has_OI",
	0x1472:	"has_IOI",
	0x14df:	"has_P",
	0x14e6:	"has_PH",
	0x14ef:	"has_R",
	0x14f6:	"has_RE",
	0x1516:	"has_S",
	0x151d:	"has_ST",
	0x1526:	"has_SP",
	0x152f:	"has_SR",
	0x1546:	"has_SM",
	0x154a:	"has_ISM",
	0x156b:	"has_SS",
	0x1576:	"has_SC",
	0x1581:	"has_SE",
	0x158a:	"has_T",
	0x1591:	"has_TI",
	0x16c7:	"range_01",
	0x16ce:	"range_12",
	0x16d5:	"range_14*",
	0x16dc:	"range_14",
	0x16e3:	"range_09",
	0x16ea:	"range_AZ",
	0x1713:	"CMD_resp",
	0x1d8e:	"ERR_1_param",
	0x1d92:	"ERR_2_units",
	0x1d96:	"ERR_3_",
	0x1d9a:	"ERR_4_sweep_time",
	0x1d9e:	"ERR_6_sweep_freq",
	0x1da2:	"ERR_7_command",
	0x1da6:	"ERR_8_char",
	0x1daa:	"ERR_9_option",
}

#######################################################################
# Stuff we need...

import pyreveng
import mem
import code
import listing

import cpu.hp_nanoproc

m = mem.byte_mem(0x0000, 0x4000)
m.load_binfile(0, 1, "hp3336.bin")

pj = pyreveng.job(m, "HP3336")

dx = cpu.hp_nanoproc.hp_nanoproc_pg()

pj.todo(0, dx.disass)
pj.todo(0xff, dx.disass)

#######################################################################
if True:
	for a0 in range(4,0x20,4):
		assert pj.m.rd(a0) == 0xc8
		pg = (pj.m.rd(a0 + 1) & 0x07) << 11
		assert pg == a0 << 9
		dpf = pj.m.rd(a0 + 2) << 8
		dpf |= pj.m.rd(a0 + 3)
		dpf &= 0x7ff 
		dpf |= pg
		pj.set_label(dpf, "DISP_%d" % (a0 >> 2))
		pj.todo(a0, dx.disass)
		pj.todo(dpf, dx.disass)
		for a1 in range(pg, dpf, 2):
			da = pj.m.rd(a1) << 8
			da |= pj.m.rd(a1 + 1)
			da &= 0x7ff
			da |= pg
			v = a0 << 3
			v |= (a1 - pg) >> 1
			pj.set_label(a1, "PTR_%02x" % v)
			pj.set_label(da, "FN_%02x" % v)
			pj.todo(a1, dx.disass)
		

#######################################################################
def jmp_table(lo, hi, span, txt = "table"):
	x = pj.add(lo, hi, "table")
	for a in range(lo, hi, span):
	        pj.todo(a, dx.disass)
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
	for a,l in symbols.items():
		pj.set_label(a,l)


while pj.run():
	pass

code.lcmt_flows(pj)
listing.listing(pj, "/tmp/_.hp3336.txt")
