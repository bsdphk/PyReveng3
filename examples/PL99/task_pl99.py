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

sys.path.insert(0, os.path.abspath(os.path.join("..", "..", "pyreveng")))

#######################################################################
# Stuff we need...

#import utils

import pyreveng
import mem
import data
import cpu.mc6800
import listing
import code
import seven_segment

m = mem.byte_mem(0x8000, 0x10000)
m.load_binfile(0x8000, 1, "PL99.mc68hc11.bin")

pj  = pyreveng.job(m, "PL99")
cx = cpu.mc6800.mc68hc11()

cx.vectors(pj)

# Random
for a in range(0xe072, 0xe0e2, 2):
	cx.codeptr(pj, a)
for a in range(0xf885, 0xf94d, 2):
	cx.codeptr(pj, a)

def cbyte(pj, a):
	c = data.const(pj, a, a + 1)
	c.val = pj.m.rd(a)
	c.typ = ".BYTE"
	c.fmt = "0x%02x" % c.val

def cword(pj, a):
	c = data.const(pj, a, a + 2)
	c.val = pj.m.bu16(a)
	c.typ = ".WORD"
	c.fmt = "0x%04x" % c.val

class d_chain(data.data):
	def __init__(self, pj, a):
		super(d_chain, self).__init__(pj, a, a + 4)

	def render(self, pj):
		return ".STRUCT chain { '%c%c%c', %d }" % (
			pj.m.rd(self.lo),
			pj.m.rd(self.lo + 1),
			pj.m.rd(self.lo + 2),
			pj.m.rd(self.lo + 3),
		)

class d_asf(data.data):
	def __init__(self, pj, a):
		super(d_asf, self).__init__(pj, a, a + 16)

	def render(self, pj):
		s = ".STRUCT asf {"
		t = " "
		for i in range(0, 16, 2):
			s += t + "%6d" % pj.m.bu16(self.lo + i)
			t = ", "
		s += "}"
		return s

class d_d3(data.data):
	def __init__(self, pj, a):
		super(d_d3, self).__init__(pj, a, a + 3)
		n = pj.m.bu16(self.lo + 1)
		pj.todo(n, cx.disass)

	def render(self, pj):
		return ".STRUCT d3 { 0x%02x, 0x%04x}" % (
			pj.m.rd(self.lo),
			pj.m.bu16(self.lo + 1),
		)

class d_d4(data.data):
	def __init__(self, pj, a):
		if pj.find(a, ".D4") != None:
			return
		super(d_d4, self).__init__(pj, a, a + 4, ".D4")
		self.val = pj.m.bu32(a)
		self.dec = self.val
		if self.dec & 0x80000000:
			self.dec &= 0x7fffffff
			self.dec *= -1
		pj.set_label(self.lo, "Q_%04x" % self.lo)

	def render(self, pj):
		return ".D4 0x%08x %12d %12g" % (self.val, self.dec, float(self.dec) / 2**16)


#######################################################################

led_map = [1, 2, 4, 128, 64, 16, 32, 8, 8]

seven_segment.table(pj, 0xecb4, 0xecd4, map = led_map, verbose = False)

LED_lbl = {
	0xf94d:  "_PL-99___LORAN-C",
	0xf95d:  "__Progr____PL-15",
	0xf96d:  "_Please___Choose",
	0xf97d:  "Lat-Lon___or_Gri",
	0xf98d:  "__L-L=4____Gri=7",
	0xf99d:  "Enter____Gri____",
	0xf9ad:  "Enter____Lat-Lon",
	0xf9bd:  "________________",
	0xf9cd:  "_Enter___Fn_no__",
	0xf9dd:  "_______A_Gri___0",
	0xf9ed:  "Search_A_Gri___0",
	0xf9fd:  "SAVE_in_____no__",
	0xfa0d:  "___no_______Fn__",
	0xfa1d:  "_________CAL____",
	0xfa2d:  "Enter______deg__",
	0xfa3d:  "8888888888888888",
	0xfa4d:  "Oscil___________",
	0xfa5d:  "__AREA____CHANGE",
	0xfa6d:  "__Pri=1____Alt=4",
	0xfa7d:  "_reset___spd_fil",
	0xfa8d:  "__speed___filter",
	0xfa9d:  "__slo_____15_set",
	0xfaad:  "regular___15_set",
	0xfabd:  "___fast___15_set",
	0xfacd:  "__slo=1____reg=2",
	0xfadd:  "_fast=3__A5_15=C",
	0xfaed:  "display_____no__",
	0xfafd:  "_Go_to______no__",
	0xfb0d:  "no_ASF___Entered",
	0xfb1d:  "__ASF____Entered",
	0xfb2d:  "CHANGE_____by__0",
	0xfb3d:  "Enter____ASF____",
	0xfb4d:  "Enter_______no__",
	0xfb5d:  "1_For0___2_For00",
	0xfb6d:  "Start_______no__",
	0xfb7d:  "__L-L=4____tds=7",
	0xfb8d:  "________________",
	0xfb9d:  "_fast____Average",
	0xfbad:  "regular__Average",
	0xfbbd:  "__Light_____on__",
	0xfbcd:  "__Light_____off_",
	0xfbdd:  "_dest_______no__",
	0xfbed:  "Select______no__",
	0xfbfd:  "__________Cntr__",
	0xfc0d:  "_____00__set_CL_",
	0xfc1d:  "_____00_____CL0C",
	0xfc2d:  "_____00__set_ttG",
	0xfc3d:  "_____00______ttG",
	0xfc4d:  "ASF______Entr___",
	0xfc5d:  "Arr_0____dist___",
	0xfc6d:  "Anchor______no__",
	0xfc7d:  "Anchor____dist__",
	0xfc8d:  "set_0____d55____",
	0xfc9d:  "Clr_cyc___Error_",
	0xfcad:  "__Plan______Fn__",
	0xfcbd:  "_CHANGE____Gri__",
	0xfccd:  "_Cold_____Start_",
	0xfcdd:  "reStart_________",
	0xfced:  "__YE5=1_____no=4",
	0xfcfd:  "reset____hot_t__",
	0xfd0d:  "reset____cold_t_",
	0xfd1d:  "__route_____no__",
	0xfd2d:  "__route_____no-_",
	0xfd3d:  "__Use=1__displ=4",
	0xfd4d:  "Pt___15___done=4",
	0xfd5d:  "__End=1___Cont=4",
	0xfd6d:  "speed____display",
	0xfd7d:  "_Crse=1___Grnd=4",
	0xfd8d:  "set_brg___corr=0",
	0xfd9d:  "_Seed____Lat-Lon",
	0xfdad:  "_Output__data_on",
	0xfdbd:  "_Output__dataoff",
	0xfdcd:  "_Auto=1____not=4",
	0xfddd:  "_Clear_____ASF__",
	0xfded:  "Input____OSC____",
	0xfdfd:  "___SELF_____TRAC",
}

for a in range(0xf94d, 0xfdfe, 16):
	c = seven_segment.table(pj, a, a + 16, map = led_map, verbose = False)
	t = LED_lbl.get(a)
	assert t != None
	if t == None:
		# Try to construct a string ourselves...
		t = ""
		for i in c:
			if i == None:
				t += "?"
			elif len(i) == 1:
				t += i
			elif i == "blank":
				t += "_"
			else:
				t += "?"
	pj.set_label(a, "LED_" + t)

#######################################################################
def post_arg_func(ins):
	post_arg_funcs = {
		0xb80c:		"WB",
		0xb821:		"WB",
		0xb836:		"W",
		0xb846:		"WWW",
		0xb86c:		"WWW",
		0xb892:		"WWW",
		0xb989:		"WWW",
		0xbabc:		"WW",
		0xbb60:		"WWW",
		0xbca1:		"WWW",
		0xbdeb:		"WW",
	}
	for f in ins.flow_out:
		i = post_arg_funcs.get(f.to)
		if i == None:
			continue
		ins.flow_out = []
		ins.add_flow(pj, "C", True, f.to)
		a = ins.hi
		for j in i:
			if j == "W":
				d = pj.m.bu16(a)
				data.dataptr(pj, a, a + 2, d)
				a += 2
				if d >= 0x8000:
					d_d4(pj, d)
			elif j == "B":
				cbyte(pj, a)
				# data.data(pj, a, a + 1)
				a += 1
			else:
				assert False
		ins.add_flow(pj, ">", True, a)
		return

cx.flow_check.append(post_arg_func)
#######################################################################

def bogo_flow(ins):
	for f in ins.flow_out:
		if f.to == None:
			pass
		elif f.to < 0x8000 or f.to > 0xffff:
			print("BOGO", ins)

cx.flow_check.append(bogo_flow)

#######################################################################

pj.set_label(0x9d20, "CHAINS")
for a in range(0x9d20, 0x9d68, 4):
	d_chain(pj, a)

for a in range(0x9d68, 0xaa28, 16):
	d_asf(pj, a)
for a in range(0x9b81, 0x9bff, 3):
	d_d3(pj, a)

for a in range(0xaa29, 0xb131, 100):
	data.data(pj, a, a + 100)

for a in range(0xb132, 0xb155, 2):
	data.data(pj, a, a + 2)

for a in range(0xc2fe, 0xc38e, 4):
	d_d4(pj, a)

for a in range(0xb156, 0xb43e, 4):
	data.data(pj, a, a + 4)

for a in range(0xc3a6, 0xc41e, 4):
	d_d4(pj, a)

pj.todo(0x9b44, cx.disass)
pj.todo(0x9b57, cx.disass)
pj.todo(0xdda1, cx.disass)
pj.todo(0xdde0, cx.disass)
pj.todo(0xde00, cx.disass)
pj.todo(0xde20, cx.disass)
pj.todo(0xf719, cx.disass)

for i in range(0xf220, 0xf226, 2):
	data.dataptr(pj, i, i + 2, pj.m.bu16(i))
	cword(pj, i + 6)

for i in range(0xe363, 0xe369, 2):
	x = cx.codeptr(pj, i)




data.data(pj, 0xca73, 0xca7c)

data.data(pj, 0xec7c, 0xec81)
data.data(pj, 0xec81, 0xec85)
data.data(pj, 0xec85, 0xec8b)
data.data(pj, 0xec8b, 0xec91)

d_d4(pj, 0xcb70)
d_d4(pj, 0xd4f5)
d_d4(pj, 0xd4f9)
d_d4(pj, 0xd4fd)
d_d4(pj, 0xd501)

while pj.run():
	pass


pj.set_label(0xb800, "MEMCPY(X, Y, B)")
pj.set_label(0xb80c, "SHR_Q")
pj.set_label(0xb821, "SHL_Q")
pj.set_label(0xb836, "COM_Q")
pj.set_label(0xb846, "ADD_Q")
pj.set_label(0xb86c, "SUB_Q")
pj.set_label(0xb892, "MUL_Q")
pj.set_label(0xecd4, "DISPLAY(Y)")

code.lcmt_flows(pj)

if False:
	import a2
	a = a2.analysis(pj)
	a.dot(pj, "/tmp/_1.dot")
	a.reduce(pj)
	a.dot(pj, "/tmp/_2.dot")

listing.listing(pj, "/tmp/_.PL99.out", ncol = 4, fmt = "x", ascii = True)
