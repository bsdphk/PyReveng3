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
from pyreveng import job, mem, listing, data, code, assy, discover
import pyreveng.cpu.mc6809 as mc6809


fwd="/critter/Doc/TestAndMeasurement/HP6626A/FW/"

m = mem.byte_mem(0x8000, 0x10000)
fi = open(fwd + "06626-80005-REV-A-00-04.hex")
for i in fi:
	j = i.split()
	m.wr(int(j[0],16), int(j[1],16))

pj = job.Job(m, "HP6626")

cpu = mc6809.mc6809()
cpu.vectors(pj)

token = {
	1:	'?',
	2:	'end',
	3:	'sep',
	4:	'number',
	6:	'string',
}

err = {
}

def softlbl(a,n):
	if a not in pj.labels:
		pj.set_label(a, n)

for a,n in (
	(0x0085, "n_chan"),
	(0x0086, "model_desc_ptr"),
	(0x038f, "B_flag1"),
	(0x0390, "B_flag2"),
	(0x01bc, "cal_lock_flag"),
	(0x1000, "gpib"),
	(0x2000, "slv_force"),
	(0x3000, "slv_sense"),
	(0x4000, "dip_kbd_sense"),
	(0x5000, "kbd_dsply_scan"),
	(0x8465, "MSG(X)"),
	(0x8775, "task_keyboard"),
	(0x88b6, "GETKEY"),
	(0x8c1a, "key_03_LCL"),
	(0x91d7, "ERR=A"),
	(0x93f7, "err_NUMBER_RANGE"),
	(0x9463, "Get_Chan"),
	(0x99d5, "cmd_A"),
	(0x99d9, "cmd_B"),
	(0x99dd, "cmd_S"),
	(0xa14b, "cmd_ID"),
	(0xaaf9, "Get_Nbr"),
	(0xb00b, "Output_40W20V_1"),
	(0xb032, "Output_40W50V_1"),
	(0xb059, "Output_80W20V_1"),
	(0xb080, "Output_80W50V_1"),
	(0xb0a7, "Output_25W_1"),
	(0xb0ce, "Output_50W_1"),
	(0xb0f5, "Output_100W20V_1"),
	(0xb11c, "Output_100W50V_1"),
	(0xb143, "Output_200W20V_1"),
	(0xb16a, "Output_200W50V_1"),
	(0xb191, "Output_10W10V_1"),
	(0xb1b8, "Output_40W20V_2"),
	(0xb1e4, "Output_40W50V_2"),
	(0xb210, "Output_80W20V_2"),
	(0xb23c, "Output_80W50V_2"),
	(0xb268, "Output_25W_2"),
	(0xb294, "Output_50W_2"),
	(0xb2c0, "Output_100W20V_2"),
	(0xb2ec, "Output_100W50V_2"),
	(0xb318, "Output_200W20V_2"),
	(0xb344, "Output_200W50V_2"),
	(0xb370, "Output_10W10V_2"),
	(0xb476, "Config_Model"),
	(0xb4c5, "ERR_NO_MODEL"),
	(0xb5ca, "special_model"),
	(0xbade, "EE_Write_Word"),
	(0xbae9, "EE_Write_Byte"),
	(0xbb1e, "I2C_Ready"),
	(0xbb37, "EE_Read_Word"),
	(0xbb7f, "EE_Read_Byte"),
	(0xbbbf, "I2C_Error"),
	(0xbbcb, "I2C_Start_Byte"),
	(0xbbd2, "I2C_Poll_Ack"),
	(0xbbf5, "EE_SCL_LH"),
	(0xbc00, "EE_SCL_L"),
	(0xbc06, "I2C_Read_Byte"),
	(0xbc23, "I2C_Write_Byte"),
	(0xbc45, "I2C_Start"),
	(0xbc70, "I2C_Stop"),
	(0xbc8d, "I2C_Get_Ack"),
	(0xbc9f, "EE_Ack"),
	(0xbcd5, "cmd_OVCAL"),
	(0xc36a, "err_CAL_ERROR"),
	(0xc5cf, "cmd_CMODE"),
	(0xc62f, "err_CAL_LOCKED"),
	(0xc637, "err_STORE_LIMIT"),
	):
	pj.set_label(a, n)

data.Const(pj, 0x8000, 0x8002)
data.Const(pj, 0xd472, 0xd47a)

for a,b in (
	(0x8002, 0x802a),
	(0x827b, 0x8287),
	):
	y = data.Txt(pj, a, b)
	y.compact = True

for a in (
	0x849b,
	0x84a7,
	0x84b3,
	0x84bf,
	0x84cb,
	0x84d7,
	0xbcb1,
	0xbcbd,
	0xbcc9,
	0xc255,
	0xcf01,
	0xd262,
	):
	y = data.Txt(pj, a, a + 12)
	y.compact = True

for a in (
	0xa183,
	0xa186,
	0xa18f,
	0xa198,
	0xaffe,
	):
	data.Const(pj, a, a + 1)
	y = data.Txt(pj, a + 1, a + 1 + pj.m.rd(a))
	y.compact = True

n = 0
for a in range(0x8ec2, 0x9036, 12):
	y = data.Txt(pj, a, a + 12)
	err[n] = y.txt
	n += 1
	y.compact = True

a = 0xa225
nn = 7
while a < 0xa370:
	data.Const(pj, a, a + 1)
	b = pj.m.rd(a)
	if b == 0:
		break
	y = data.Txt(pj, a + 1, a + 1 + b)
	# print("0x%02x" % nn, y.txt)
	token[nn] = y.txt
	y.compact = True
	a += 1 + b
	nn += 1

print("NN", nn)

for a in range(0x87d0, 0x8810, 8):
	data.Const(pj, a, a + 8)

def t1(a):
	while True:
		y = data.Txt(pj, a)
		y.compact = True
		a = y.hi
		cpu.codeptr(pj, a)
		# data.Const(pj, a, a + 2)
		a += 2
		data.Const(pj, a, a + 1)
		if pj.m.rd(a) == 0:
			return a + 1
		a += 1

t1(0x8825)
t1(0x8861)

n = 0
for a in range(0x87b4, 0x87d0, 2):
	x = pj.m.bu16(a)
	softlbl(x, "key_%02x_%04x" % (n, x))
	n += 1
	cpu.codeptr(pj, a)

n = 1

for a in range(0xa5d3, 0xa687, 2):
	x = pj.m.bu16(a)
	softlbl(x, "cmd_%02x_%04x" % (n,x))
	n += 1
	cpu.codeptr(pj, a)

class tt_5(data.Data):
	def __init__(self, pj, lo):
		hi = lo + 4
		super(tt_5, self).__init__(pj, lo, hi, "tt_5")

	def render(self, pj):
		s = ".TT5\t"
		t = pj.m.rd(self.lo)
		if t in token:
			s += token[t] + ", "
		else:
			s += "T%02x, " % t
		s += "0x%02x, " % pj.m.rd(self.lo + 1)
		w = pj.m.bu16(self.lo + 2)
		s += pj.render_adr(w)
		return s

def tt5(a, f, l = None, ex = 0):
	if l == None:
		l = []
	pj.set_label(a, "tt5_%04x" % a)
	while True:
		ll = list(l)
		if pj.m.rd(a) == 0:
			data.Const(pj, a, a + 1)
			break
		t = pj.m.rd(a)
		if t in token:
			ll.append(token[t])
		else:
			ll.append("T%02x" % t)
		e = pj.m.rd(a + 1)
		if e != 0:
			ex = f + e * 2
			z = pj.m.bu16(ex)
			# print("%04x" % a, "%04x" % z, "A %02x" % e, ll)
			pj.set_label(z, "cmd_" + "_".join(ll))
		tt_5(pj, a)
		x = pj.m.bu16(a + 2)
		if x != 0:
			tt5(x, f, ll, ex)
		else:
			# print("%04x" % a, ll, "%04x" % ex)
			y = pj.t.find_lo(ex)
			y[0].lcmt += " ".join(ll) + "\n"
			# print(y)
			
		a += 4

tt5(0xa3a2, 0xa5d1)

for a in range(0xb7ac, 0xb7c4, 2):
	data.Const(pj, a, a + 2)


# Task or coroutine table
for a in range(0xce62, 0xce80, 6):
	z = pj.m.bu16(a + 2)
	softlbl(z, "task_%04x" % z)
	cpu.codeptr(pj, a + 2)
	

cpu.disass(pj, 0x8631)
cpu.disass(pj, 0x8b65)
cpu.disass(pj, 0x8b78)
cpu.disass(pj, 0x8b86)
cpu.disass(pj, 0x8b91)
cpu.disass(pj, 0x8e87)
cpu.disass(pj, 0x8d76)

cpu.disass(pj, 0xc7a2)
cpu.disass(pj, 0xc7ad)
cpu.disass(pj, 0xc7b8)
cpu.disass(pj, 0xc7c5)
cpu.disass(pj, 0xc7d9)
cpu.disass(pj, 0xc7e6)
cpu.disass(pj, 0xc7fc)
cpu.disass(pj, 0xc809)
cpu.disass(pj, 0xc814)
cpu.disass(pj, 0xc821)
cpu.disass(pj, 0xc835)
cpu.disass(pj, 0xc842)
cpu.disass(pj, 0xc84b)
cpu.disass(pj, 0xc855)
cpu.disass(pj, 0xd3b8)
cpu.disass(pj, 0xd3f8)

##############

def fp_val(pj, lo, hi):
	e = pj.m.s8(hi - 1)
	m = 0
	i = 0
	a = hi - 2
	while a >= lo:
		m |= pj.m.rd(a) << i
		i += 8
		a -= 1
	m *= 10 ** e
	return m

class fp(data.Data):
	def __init__(self, pj, lo, hi):
		super(fp, self).__init__(pj, lo, hi, "fp")
		self.val = fp_val(pj, lo, hi)

	def render(self, pj):
		return ".FP\t%g" % self.val

class tt_2(data.Data):
	def __init__(self, pj, lo):
		hi = lo + 5 + pj.m.rd(lo + 4) * 4
		super(tt_2, self).__init__(pj, lo, hi, "tt_2")

	def render(self, pj):
		s = ".TT2\t{\n"
		w = pj.m.bu16(self.lo + 0)
		s += "\t.next = " + pj.render_adr(w) + "\n"
		s += "\t.model = %4d\n" % pj.m.bu16(self.lo + 2)
		n = pj.m.rd(self.lo + 4)
		s += "\t.outputs = %d\n" % n
		a = self.lo + 5
		for i in range(n):
			w = pj.m.bu16(a)
			s += "\t.out1[%d] = " % i + pj.render_adr(w) + "\n"
			a += 2
			w = pj.m.bu16(a)
			s += "\t.out2[%d] = " % i + pj.render_adr(w) + "\n"
			a += 2
		return s + "\t}"

class tt_output1(data.Data):
	def __init__(self, pj, lo):
		hi = lo + 39
		super(tt_output1, self).__init__(pj, lo, hi, "tt_output1")
		self.compact = True

	def render(self, pj):
		s = ".OUTPUT1\t"
		a = self.lo
		f = [ "%4.1f", "%4.1f", "%6.3f", "%6.3f", "%4.1f"]
		for i in range(5):
			s += "0x%04x, " % pj.m.bu16(a)
			a += 2
			s += (f[i] + ", ") % fp_val(pj, a, a + 4)
			a += 4
		for i in range(3):
			s += "%5.2f, " % fp_val(pj, a, a + 3)
			a += 3
		return s[:-2]

class tt_output2(data.Data):
	def __init__(self, pj, lo):
		hi = lo + 44
		super(tt_output2, self).__init__(pj, lo, hi, "tt_output2")
		self.compact = True

	def render(self, pj):
		s = ".OUTPUT2\t"
		a = self.lo
		f = [ "%4.1f", "%4.1f", "%6.3f", "%6.3f", "%4.1f",
		    "%5.3f", "%4.1f"]
		for i in range(7):
			s += "0x%04x, " % pj.m.bu16(a)
			a += 2
			s += (f[i] + ", ") % fp_val(pj, a, a + 4)
			a += 4
		s += "0x%04x" % pj.m.bu16(a)
		return s

tt = {}

def tt3_1(a):
	if a in tt:
		return
	tt[a] = True
	tt_output1(pj, a)

def tt3_2(a):
	if a in tt:
		return
	tt[a] = True
	tt_output2(pj, a)
	return
	softlbl(a, "tt3_2_%04x" % a)
	while True:
		if pj.m.rd(a + 2) > 2:
			break
		data.Const(pj, a, a+2, fmt="0x%02x")
		fp(pj, a + 2, a + 6)
		a += 6
	data.Const(pj, a, a+2, fmt="0x%02x")

a = 0xb39c
while a:
	pj.set_label(a, "tt2_%04x" % a)
	x = pj.m.bu16(a)
	if x == 0:
		data.Dataptr(pj, a, a + 2, x)
		break
	y = tt_2(pj, a);
	a = x
	continue
	data.Const(pj, a + 2, a + 4, fmt="%d")
	data.Const(pj, a + 4, a + 5)
	y = pj.m.rd(a + 4)
	a += 5
	for i in range(y * 2):
		z = pj.m.bu16(a)
		tt3_1(z)
		data.Dataptr(pj, a, a + 2, z)
		a += 2
		z = pj.m.bu16(a)
		tt3_2(z)
		data.Dataptr(pj, a, a + 2, z)
		a += 2
	a = x

##############
for a in range(0xb437, 0xb46e, 5):
	pj.set_label(a, "tt1_%04x" % a)
	data.Const(pj, a, a+1)
	z = pj.m.bu16(a + 1)
	data.Dataptr(pj, a + 1, a + 3, z)
	tt3_1(z)
	z = pj.m.bu16(a + 3)
	data.Dataptr(pj, a + 3, a + 5, z)
	tt3_2(z)

##############


while pj.run():
	pass

#############
# Add comment with error message

for i in pj:
	if i.tag != "mc6809":
		continue
	if i.dstadr != 0x91d7:
		continue
	j = pj.t.find_hi(i.lo)
	if len(j) != 1:
		continue
	j=j[0]
	x = pj.m.rd(j.lo)
	if x != 0x86:
		continue
	y = pj.m.rd(j.lo + 1)
	j.lcmt += "Error: " + err[y] + "\n"

#############
# discover.Discover(pj, cpu)

code.lcmt_flows(pj)

listing.Listing(pj)
