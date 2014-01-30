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
import sys

#######################################################################
# Set up a search path to two levels below

sys.path.insert(0, os.path.abspath(os.path.join("..", "..", "pyreveng")))

#######################################################################

symbols = {
	0x6800:		"KEY_PRESET_STORE",
	0x680f:		"KEY_PRESET_DISPLAY",
	0x6815:		"KEY_PRESET_RECALL",
	0x69ca:		"KEY_BACK_SPACE",
	0x69ea:		"KEY_PERIOD",
	0x6ab3:		"KEY_Hz_DEG",
	0x6aca:		"KEY_kHz_+dBm",
	0x6ae8:		"KEY_MHz_-dBm",
	0x6b9a:		"CMD_ILL",
	0x6cc3:		"KEY_INCR",
	0x70a0:		"KEY_MANUAL_TUNE_ON_OFF",
	0x71a0:		"FREQ_KNOB",
	0x732a:		"KEY_SWEEP_START_SINGLE_10_50",
	0x736f:		"KEY_SWEEP_MANUAL",
	0x738f:		"KEY_SWEEP_GOTO_START_FREQ",
	0x73b1:		"KEY_SWEEP_STOP",
	0x73f6:		"KEY_SWEEP_START_AUTO",
	0x748d:		"KEY_nc2 ?",
	0x760f:		"5c= 2*'.'",
	0x7617:		"5a= 2*'-'",
	0x761f:		"72= 2*'9'",
	0x7623:		"5e= 2*'?'",
	0x7627:		"digit",
	0x7966:		"KEY_nc",
	0x7cd1:		"KEY_FREQUENCY",
	0x7ce0:		"KEY_AMPLITUDE",
	0x7ce4:		"KEY_DISPLAY_LAST_ENTRY",
	0x7cf7:		"KEY_SWEEP_WIDTH",
	0x7cfe:		"KEY_PHASE_INCR",
	0x7d04:		"KEY_AMPTD_INCR",
	0x7d08:		"KEY_FREQ_INCR",
	0x7d0c:		"KEY_ENTRY_CLEAR",
	0x7d2f:		"DIGIT",
}
#######################################################################
# Stuff we need...

import pyreveng
import mem
import listing
import code
import seven_segment

import cpu.mc6800

m = mem.byte_mem(0x6800, 0x8000)
m.load_binfile(0x6800, 1, "A13U2.bin")
m.load_binfile(0x7000, 1, "A13U3.bin")
m.load_binfile(0x7800, 1, "A13U4.bin")

pj = pyreveng.job(m, "HP3335A")

pj.apct = "%04x"

#######################################################################

def rom(lo, hi):
	pj.add(lo, hi, "ROM")
	s = 0
	for a in range(lo, hi):
		s += pj.m.rd(a)
	s &= 0xff
	if s == 0:
		print("ROM %04x-%04x sum good (%02x)" % (lo, hi, s))
	else:
		print("ROM %04x-%04x sum BAD (%02x)" % (lo, hi, s))

rom(0x6800, 0x7000)
rom(0x7000, 0x7800)
rom(0x7800, 0x8000)

for i in (0x6fff, 0x77ff, 0x7ff7):
	c = pj.add(i, i + 1, "csum")
	c.rendered = c.tag

#######################################################################

cpu = cpu.mc6800.mc6800(mask = 0x7fff)

def vec(a, n):
	c = pj.add(a, a + 2, "vector")
	c.rendered = "vector(%s)" % n
	v = pj.m.bu16(a)
	pj.todo(v, cpu.disass)

vec(0x7ff8, "IRQ")
vec(0x7ffa, "SWI")
vec(0x7ffc, "NMI")
vec(0x7ffe, "RST")

#######################################################################

class ptr(pyreveng.leaf):
	def __init__(self, pj, adr):
		super(ptr, self).__init__(pj, adr, adr + 2, "ptr")

	def render(self, pj):
		v = pj.m.bu16(self.lo)
		l = pj.labels.get(v)
		if l == None:
			return ".PTR 0x%x" % v
		else:
			return ".PTR %s" % l
		

def jmptbl(lo, hi, x = None):
	c = pj.add(lo, hi, "jmptbl (%04x-%04x)" % (lo, hi))
	# c.rendered = c.tag
	n = 0
	for a in range(lo, hi, 2):
		v = pj.m.bu16(a)
		d = ptr(pj, a)
		if x != None and len(x) > n:
			if v not in symbols:
				symbols[v] = "CMD_" + x[n]
		n += 1
		pj.todo(v, cpu.disass)

jmptbl(0x7768, 0x77b6, '9876543210.-@ABCDEFGHIJKLMNOPQRSTUVWXYZ')
jmptbl(0x7860, 0x787c)
jmptbl(0x78a0, 0x78bc)
jmptbl(0x78c0, 0x78dc)

#######################################################################

def tblx(a):
	c = pj.add(a, a + 16, "tblx")
	s = ""
	for i in range(10):
		v = pj.m.rd(a + i)
		s += " %02x" % v
	s += "  "
	for i in range(10,16):
		v = pj.m.rd(a + i)
		s += " %02x" % v
	c.rendered = "TBLX " + s
	c.compact = True

for a in range(0x7000,0x70a0,16):
	tblx(a)

for a in range(0x7100,0x71a0,16):
	tblx(a)

#######################################################################

#seven_segment.hunt(pj, 0x6800, 0x8000, pattern="AbCdE")
#seven_segment.hunt(pj, 0x6800, 0x8000)

seven_segment.table(pj, 0x7800, 0x7810,
    map = ( 128, 64, 32, 16, 8, 4, 2, 1, 0),
    inv=True, verbose=False)


#######################################################################
if True:
	for a,l in symbols.items():
		pj.set_label(a,l)


while pj.run():
	pass

code.lcmt_flows(pj)
listing.listing(pj, "/tmp/_.hp3335a.txt")

if False:
	import a2
	a = a2.analysis(pj)
	a.dot(pj, "/tmp/_1.dot")
	a.reduce(pj)
	a.dot(pj, "/tmp/_2.dot")

