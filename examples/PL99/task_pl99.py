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

seven_segment.known[0x21] = "r"
seven_segment.known[0x63] = "o"
seven_segment.known[0x04] = "i"
seven_segment.known[0x41] = "="
seven_segment.known[0x20] = "i"
seven_segment.known[0x30] = "I"

m = mem.byte_mem(0x8000, 0x10000)
m.load_binfile(0x8000, 1, "PL99.mc68hc11.bin")

pj  = pyreveng.Job(m, "PL99")
cx = cpu.mc6800.mc68hc11()

cx.register_labels(pj)

cx.vectors(pj)


def cbyte(pj, a):
	c = data.const(pj, a, a + 1)
	c.val = pj.m.rd(a)
	c.typ = ".BYTE"
	c.fmt = "0x%02x" % c.val
	return c

def cword(pj, a):
	c = data.const(pj, a, a + 2)
	c.val = pj.m.bu16(a)
	c.typ = ".WORD"
	c.fmt = "0x%04x" % c.val
	return c 

class d_chain(data.Data):
	def __init__(self, pj, a):
		super(d_chain, self).__init__(pj, a, a + 4)
		self.num = '%c%c%c' % (
			pj.m.rd(self.lo),
			pj.m.rd(self.lo + 1),
			pj.m.rd(self.lo + 2),
		)

	def render(self, pj):
		return ".STRUCT chain { '%c%c%c', %d }" % (
			pj.m.rd(self.lo),
			pj.m.rd(self.lo + 1),
			pj.m.rd(self.lo + 2),
			pj.m.rd(self.lo + 3),
		)

class d_asf(data.Data):
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

class d_q(data.Data):
	"""
	Numbers are sign + 31 bit binary q-complement fractions:
		[Sign][31 bit fraction]
	"""
	def __init__(self, pj, a, lbl = True):
		if pj.find(a, ".D4") != None:
			return
		super(d_q, self).__init__(pj, a, a + 4, ".D4")
		self.val = pj.m.bu32(a)
		self.dec = self.val
		if self.dec & 0x80000000:
			self.dec &= 0x7fffffff
			self.dec *= -1
		self.dec *= 2**-31
		if lbl:
			pj.set_label(self.lo, "Q_%04x_%g" % (self.lo, self.dec))

	def render(self, pj):
		if self.dec != 0.0:
			b = 1.0/self.dec
		else:
			b = 0.
		return ".D4 %12g = 1/%g" % (self.dec, b)


#######################################################################

led_map = [1, 2, 4, 128, 64, 16, 32, 8, 0]

seven_segment.table(pj, 0xecb4, 0xecd4, map = led_map, verbose = False)
pj.set_label(0xecb4, "7SEG_TBL")

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
	pj.set_label(a, "MSG_" + t)

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
					d_q(pj, d)
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

chains = []
x = pj.add(0x9d20, 0x9d68, "chain-tbl")
pj.set_label(x.lo, "CHAINS")
for a in range(x.lo, x.hi, 4):
	chains.append("GRI_" + d_chain(pj, a).num + "0")


"""
This is probably ASF data
(Based partially on number of records = 204)
"""
x = pj.add(0x9d68, 0xaa28, "asf-tbl")
for a in range(x.lo, x.hi, 16):
	d_asf(pj, a)

# ON_KEY table
x = pj.add(0xe072, 0xe0e2, "on-key-tbl")
pj.set_label(x.lo, "ON_KEY_TBL")
n = 0x80
for a in range(x.lo, x.hi, 2):
	x = cx.codeptr(pj, a)
	pj.set_label(x.dst, "ON_KEY_0x%02x" % n)
	n += 1

# CMD table
x = pj.add(0x9b81, 0x9bff, "cmd-tbl")
pj.set_label(x.lo, "CMDTBL")
for a in range(x.lo, x.hi, 3):
	y = data.txt(pj, a, a+1, label = False)
	z = cx.codeptr(pj, a + 1)
	if y.txt == " ":
		pj.set_label(z.dst, "CMD_SP")
	else:
		pj.set_label(z.dst, "CMD_%s" % y.txt)
	
# FN table
x = pj.add(0xf885, 0xf94d, "fn-tbl")
pj.set_label(x.lo, "FN_TBL")
d = dict()
n = 0
for a in range(x.lo, x.hi, 2):
	y = cx.codeptr(pj, a)
	if not y.dst in d:
		d[y.dst] = []
	d[y.dst].append(n)
	n += 1
for i in d:
	e = d[i]
	if len(e) == 1:
		pj.set_label(i, "FN_%02d" % e[0])
	elif len(e) > 10:
		pj.set_label(i, "FN_UNDEF")
	else:
		pj.set_label(i, "FN_%02d_%02d" % (e[0], e[-1]))

def longitude(pj, a):
	"""
	This gives values closely matching table values
	"""
	x = d_q(pj, a, lbl = False)
	s = ""
	v = x.dec * 180.
	if v < 0:
		v *= -1
		s += "W"
		v = 180. - v
	else:
		s += "E"
	deg = v.__trunc__()
	v -= deg
	s += "%4d" % deg

	v *= 60
	mi = v.__trunc__()
	v -= mi
	s += " %2d'" % mi

	v *= 60
	s += ' %2.3f"' % v

	x.lcmt = s
	return x

def lattitude(pj, a):
	"""
	This calculation is not quite right.
	"""
	x = d_q(pj, a, lbl = False)
	s = ""
	v = x.dec * 90.
	v = 108 - v
	if v < 0:
		v *= -1
		s += "S"
		v = 180. - v
	else:
		s += "N"
	deg = v.__trunc__()
	v -= deg
	s += "%4d" % deg

	v *= 60
	mi = v.__trunc__()
	v -= mi
	s += " %2d'" % mi

	v *= 60
	s += ' %2.3f"' % v

	x.lcmt = s
	return x

#
# Chain data, idx'ed by 0x9d20
#
x = pj.add(0xaa29, 0xb131, "tbl")
n = 0
for a in range(x.lo, x.hi, 100):
	x = pj.add(a, a + 100, "chain-tbl")
	pj.set_label(a, "CHAIN_" + chains[n])
	x = cword(pj,  a)
	x.lcmt = "GRI %d * 5" % (x.val / 5)
	#data.data(pj, a, a + 100)
	x = pj.add(a + 0x02, a + 0x02 + 5 * 4, "alpha-tbl")
	x = pj.add(a + 0x16, a + 0x16 + 5 * 4, "beta-tbl")
	x = pj.add(a + 0x2a, a + 0x2a + 5 * 4, "gamma-tbl")
	for c in range(5):
		d_q(pj, a + 0x02 + c * 4, lbl = False)
		lat = lattitude(pj, a + 0x16 + c * 4)
		lon = longitude(pj, a + 0x2a + c * 4)

	x = pj.add(a + 0x3e, a + 0x3e + 4 * 4, "rho-tbl")
	x = pj.add(a + 0x4e, a + 0x4e + 4 * 4, "sigma-tbl")
	for c in range(4):
		x = d_q(pj, a + 0x3e + c * 4, lbl = False)
		x.lcmt = "%.3f us / 2^23" % (x.dec * 2**23)
		d_q(pj, a + 0x4e + c * 4, lbl = False)

	x = pj.add(a + 0x5e, a + 0x5e + 5, "epsilon-tbl")
	for c in range(5):
		cbyte(pj, a + 0x5e + c)

	x = cbyte(pj, a + 99)
	x.lcmt = "# slaves"
	n += 1

for a in range(0xc2fe, 0xc38e, 4):
	d_q(pj, a)

# idx into tbl at b156
# Chain data (18 pieces)
#
x = pj.add(0xb132, 0xb155, "tbl")
n = 0
for a in range(x.lo, x.hi, 2):
	y = cword(pj, a)
	y.lcmt = chains[n]
	pj.set_label(0xb156 + y.val, "CHAIN_I_" + chains[n])
	n += 1

x = pj.add(0xb156, 0xb43e, "tbl")
for a in range(x.lo, x.hi, 4):
	#data.data(pj, a, a + 4)
	d_q(pj, a, lbl = False)

for a in range(0xc3a6, 0xc41e, 4):
	d_q(pj, a)

for a in range(0x906f, 0x9087, 2):
	c = cword(pj, a)
	c.fmt = "%d" % c.val

x = pj.add(0x9d00, 0x9d20, "tbl")
x.lcmt += "accessed via 0x9cc2 pointer"
for a in range(x.lo, x.hi, 2):
	c = cword(pj, a)

pj.todo(0x9102, cx.disass)
pj.todo(0x95da, cx.disass)
pj.todo(0x9b29, cx.disass)
pj.todo(0x9a96, cx.disass)
pj.todo(0x9b44, cx.disass)
pj.todo(0x9b57, cx.disass)
pj.todo(0xdda1, cx.disass)
pj.todo(0xdde0, cx.disass)
pj.todo(0xde00, cx.disass)
pj.todo(0xde20, cx.disass)
pj.todo(0xf719, cx.disass)

for a in range(0x9789, 0x97a5, 4):
	d_q(pj, a)

for i in range(0xf220, 0xf226, 2):
	data.dataptr(pj, i, i + 2, pj.m.bu16(i))
	cword(pj, i + 6)

#for i in range(0x89d8, 0x8a20, 2):
#	data.dataptr(pj, i, i + 2, pj.m.bu16(i))

for i in range(0xe363, 0xe369, 2):
	x = cx.codeptr(pj, i)

x = pj.add(0xb963, 0xb975, "tbl")
for i in range(x.lo, x.hi):
	cbyte(pj, i)



data.Data(pj, 0xca73, 0xca7c)

data.Data(pj, 0xec7c, 0xec81)
data.Data(pj, 0xec81, 0xec85)
data.Data(pj, 0xec85, 0xec8b)
data.Data(pj, 0xec8b, 0xec91)

d_q(pj, 0xcb70)
d_q(pj, 0xd4f5)
d_q(pj, 0xd4f9)
d_q(pj, 0xd4fd)
d_q(pj, 0xd501)

while pj.run():
	pass

pj.set_label(0x6489, "CHAIN_PTR")

pj.set_label(0xb800, "MEMCPY(X, Y, B)")
pj.set_label(0xb80c, "SHR_Q")
pj.set_label(0xb821, "SHL_Q")
pj.set_label(0xb836, "COM_Q")
pj.set_label(0xb846, "ADD_Q")
pj.set_label(0xb86c, "SUB_Q")
pj.set_label(0xb892, "MUL_Q")

pj.set_label(0xec91, "7SEG_XLAT(0x66a9)")
pj.set_label(0xecaa, "7SEG_DIG(B)")

pj.set_label(0xecd4, "DISPLAY(Y)")

pj.set_label(0xf1a9, "DISPLAY_YES_NO(Y)")
pj.set_label(0xf1b7, "IS_YES()")
pj.set_label(0xf878, "PAUSE()")
pj.set_label(0xfe5c, "Analog_Capture")
pj.set_label(0xfe6e, "Capture_One_Analog")

pj.set_label(0xf9, "ON_KEY")

code.lcmt_flows(pj)

if False:
	import a2
	a = a2.analysis(pj)
	a.dot(pj, "/tmp/_1.dot")
	a.reduce(pj)
	a.dot(pj, "/tmp/_2.dot")

listing.Listing(pj, "/tmp/_.PL99.out", ncol = 4, fmt = "x", ascii = True)
