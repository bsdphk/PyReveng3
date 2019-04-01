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
from pyreveng import job, mem, data, listing, code
import pyreveng.cpu.i8086 as i8086

def mem_setup():
	m = mem.byte_mem(0xe0000, 0x100000)
	fn = os.path.join(os.path.dirname(__file__),
	    "618TCA_R_U2_C_U15_PN_138_0193_V4_4.bin")
	m.load_binfile(0xe0000, 1, fn)
	return m

def setup():
	pj  = job.Job(mem_setup(), "Apollo618c")

	cx = i8086.i8086()
	cx.has_8087()
	return pj,cx

def task(pj, cx):
	pj.todo(0xffff0, cx.disass)

	#######################################################################

	def vect(seg, off):
		a = (seg << 4) + off
		# print("VECTOR %05x" % a)
		pj.todo(a, cx.disass)
		pj.set_label(a, "VECTOR")

	# Vectors initialized at 0xe21b2...
	vect(0xe000, 0x1e67)
	vect(0xe1f5, 0x35e9)
	vect(0xe737, 0x1fdf)
	vect(0xf8bd, 0x417b)

	#######################################################################
	# Random guesses

	if False:
		pj.todo(0xe63cf, cx.disass)
		pj.todo(0xe7bd7, cx.disass)
		pj.todo(0xe7fdd, cx.disass)
		pj.todo(0xe834c, cx.disass)
		pj.todo(0xe9251, cx.disass)
		pj.todo(0xfcd68, cx.disass)
		pj.todo(0xffb56, cx.disass)

	#######################################################################

	def txl(seg, a):
		for i in range(2,0x22, 2):
			x = pj.m.lu16(a + i)
			#print("%04x" % seg, i, "%05x" % (a + i), "%04x" % x, "%05x" % (seg * 16 + x))
			y = data.Codeptr(pj, a + i, a + i + 2, seg*16+x)

	txl(0xff1b, 0xffe00)
	txl(0xff1b, 0xffe22)
	txl(0xff1b, 0xffe44)
	txl(0xff1b, 0xffe66)
	txl(0xff1b, 0xffe88)
	txl(0xff1b, 0xffeaa)

	###################################################################################

	def tbl(seg, off_lo, off_hi):
		pj.add(off_lo, off_hi, "%04x-jmp-tbl" % seg)
		for i in range(off_lo, off_hi, 2):
			off = pj.m.lu16(i)
			a = (seg << 4) + off
			x = data.Codeptr(pj, i, i + 2, a)
			pj.todo(a, cx.disass)

	def tbl2(a):
		assert pj.m.rd(a + 0) == 0x2e
		assert pj.m.rd(a + 1) == 0xff
		assert pj.m.rd(a + 2) == 0xa7
		o = pj.m.lu16(a + 3)
		s = (a + 5 - o)
		#print("T2", "seg", "%05x" % s, "off", "%04x" % o)
		e = o + s
		l = 0xfffff
		while e < l:
			n = pj.m.lu16(e)
			if s + n < l:
				l = s + n
			# print("e %05x" % e, "l %05x" % l, "n %04x -> %05x" % (n, s + n))
			e += 2
		tbl(s >> 4, o + s, e)

	while pj.run():
		pass

	t2dict = {}

	more = True

	while more:
		while pj.run():
			pass
		more = False
		for i in pj:
			if i.tag != "i8086":
				continue
			if i.lo in t2dict:
				continue
			if pj.m.rd(i.lo + 0) != 0x2e:
				continue
			if pj.m.rd(i.lo + 1) != 0xff:
				continue
			if pj.m.rd(i.lo + 2) != 0xa7:
				continue
			t2dict[i.lo] = True
			tbl2(i.lo)
			more = True

	#######################################################################

	more = False
	while more:
		while pj.run():
			pass
		more = False
		for lo,hi,aspace in pj.gaps():
			if lo + 1 == hi:
				continue
			if pj.m.rd(lo) == 0x55:
				print("%04x, %04x" % (lo, hi))
				pj.todo(lo, cx.disass)
				more = True
			elif pj.m.rd(lo) == 0x00 and pj.m.rd(lo + 1) == 0x55:
				print("%04x, %04x" % (lo, hi))
				pj.todo(lo + 1, cx.disass)
				more = True


	#######################################################################

	def text_lines(pj, a):
		pj.add(a, a + 24, "text-tbl")
		data.Txt(pj, a, a + 8, label=False)
		data.Txt(pj, a + 8, a + 16, label=False)
		data.Txt(pj, a + 16, a + 24, label=False)

	text_lines(pj, 0xe57e0 + 0x1f0)
	text_lines(pj, 0xe57e0 + 0x208)
	text_lines(pj, 0xe57e0 + 0x220)

	text_lines(pj, 0xe68d0)
	text_lines(pj, 0xe68e8)
	text_lines(pj, 0xe6900)

	#######################################################################

if __name__ == '__main__':
	pj, cx = setup()
	task(pj, cx)
	listing.Listing(pj, ncol = 8)

