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

import os
from pyreveng import job, mem, listing, code, discover, data
import pyreveng.cpu.mc6800 as mc6800

def mem_setup():
	m = mem.byte_mem(0xd000,0x10000)
	dn = os.path.dirname(__file__)
	m.load_binfile(0xf000, 1, os.path.join(dn, "Rev107f0.BIN"))
	m.load_binfile(0xe000, 1, os.path.join(dn, "Rev107f1.BIN"))
	m.load_binfile(0xd000, 1, os.path.join(dn, "Rev107f2.BIN"))
	return m

def setup():
	pj = job.Job(mem_setup(), "Austron2100F_107")
	cx = mc6800.mc6800()
	return pj, cx

class w8(data.Const):
	def __init__(self, pj, a):
		super(w8, self).__init__(pj, a, a + 1)
		self.typ = ".BYTE"
		self.val = pj.m.rd(a)
		self.fmt = "0x%02x" % self.val

class w16(data.Const):
	def __init__(self, pj, a):
		super(w16, self).__init__(pj, a, a + 2)
		self.typ = ".WORD"
		self.val = pj.m.bu16(a)
		self.fmt = "0x%04x" % self.val

class w32(data.Const):
	def __init__(self, pj, a):
		super(w32, self).__init__(pj, a, a + 4)
		self.typ = ".LWORD"
		self.val = pj.m.bu32(a)
		self.fmt = "0x%08x" % self.val
		self.fmt = "%d" % self.val

def w8t(pj, lo, hi):
	for a in range(lo, hi, 1):
		w8(pj, a)

def w16t(pj, lo, hi):
	for a in range(lo, hi, 2):
		w16(pj, a)

def w32t(pj, lo, hi):
	for a in range(lo, hi, 2):
		w32(pj, a)

def codet(pj, cx, lo, hi):
	for a in range(lo, hi, 2):
		x = pj.m.bu16(a)
		if x >= pj.m.lo and x < pj.m.hi:
			cx.codeptr(pj, a)
			pj.set_label(x, "L%04x" % x)
		else:
			w16(pj, a)


def task(pj, cx):

	cx.vectors(pj)

	##################################################################
	# Tables

	# Checksum
	w8(pj, 0xd000)

	# End address of checksum calc
	w16(pj, 0xd001)

	# Check checksum
	s = 0
	for a in range(0xd001, pj.m.bu16(0xd001)):
		s ^= pj.m.rd(a)
	print("SUM", s, pj.m.rd(0xd000))
	assert s == pj.m.rd(0xd000)

	w16t(pj, 0xd8fb, 0xd903)
	w32t(pj, 0xd903, 0xd90b)

	# IEEE cmd+digit -> keycode
	# d935  53 0c     |S  | 'S0' -> KEY_CLEAR
	# d937  54 0d     |T  | 'S1' -> KEY_TEST
	# d939  55 0f     |U  | 'S2' -> KEY_STATUS
	# d93b  56 11     |V  | 'S3' -> KEY_GRI
	# d93d  57 1c     |W  | 'S4' -> KEY_?
	# d93f  41 13     |A  | 'A0' -> KEY_STATION_ADVANCE
	# d941  42 14     |B  | 'A1' -> KEY_ACQ
	# d943  4d 16     |M  | 'M0' -> KEY_PHASE_O_FS
	# d945  4e 17     |N  | 'M1' -> KEY_PHASE_RANGE
	# d947  4f 18     |O  | 'M2' -> KEY_FREQ_OFF
	# d949  50 1b     |P  | 'M3' -> KEY_BACK_LIGHT
	w16t(pj, 0xd935, 0xd94b)

	codet(pj, cx, 0xd94b, 0xd9b1)

	w16t(pj, 0xdce7, 0xdceb)

	w8t(pj, 0xde38, 0xde3a)

	w16t(pj, 0xe0b0, 0xe0c6)

	w32t(pj, 0xeb37, 0xeb4e)

	w16t(pj, 0xed1f, 0xed2b)

	# 128 entries approx X*X>>2
	# Table duplicated ?
	w16t(pj, 0xec1f, 0xed1f)
	w16t(pj, 0xee3b, 0xef3b)

	w16(pj, 0xee39)

	codet(pj, cx, 0xf3c3, 0xf3d3)

	w16t(pj, 0xf580, 0xf598)

	# XXX: Startup display data ?
	w8t(pj, 0xf685, 0xf697)

	##################################################################
	# Code

	# Addresses stored into 0x0010
	pj.todo(0xd401, cx.disass)
	pj.todo(0xde3a, cx.disass)

	# Addresses stored into 0x0033
	pj.todo(0xdaaa, cx.disass)
	pj.todo(0xdceb, cx.disass)
	pj.todo(0xdd0d, cx.disass)

	# Addresses stored into 0x003a
	pj.todo(0xf284, cx.disass)

	# Addresses stored into 0x008d (Key-handlers ?)
	pj.todo(0xe02b, cx.disass)
	pj.todo(0xe05e, cx.disass)
	pj.todo(0xe37e, cx.disass)
	pj.todo(0xdf41, cx.disass)
	pj.todo(0xf429, cx.disass)
	pj.todo(0xf377, cx.disass)

	# Addresses stored into 0x010c
	pj.todo(0xdb26, cx.disass)
	pj.todo(0xdb32, cx.disass)

	# LDS-JMP-TSX calls
	pj.todo(0xd033, cx.disass)
	pj.todo(0xf44d, cx.disass)

	# Things discover gets wrong
	pj.todo(0xdee2, cx.disass)
	pj.todo(0xde3a, cx.disass)

	while True:
		while pj.run():
			continue

		# Find queue'd entry points
		stop = True
		for i in pj.m:
			if i.tag != cx.name:
				continue
			if pj.m.rd(i.lo) != 0xce:
				continue
			j = pj.m.rd(i.lo + 3)
			if j != 0xbd and j != 0x7e:
				continue
			if pj.m.rd(i.lo + 4) != 0xf1:
				continue
			if pj.m.rd(i.lo + 5) != 0x01:
				continue
			a = pj.m.bu16(i.lo + 1)
			if len(pj.find(a)) == 0:
				print("Queued: 0x%04x" % a)
				pj.todo(a, cx.disass)
				pj.set_label(a, "Q%04x" % a)
				stop = False
		if stop:
			break

	# Find some dead code
	discover.Discover(pj, cx)

	pj.set_label(0xe7dd, "?mul2(ce_d2)")
	pj.set_label(0xe7ae, "?mul10(ce_d2)")
	pj.set_label(0xe965, "?mul2(b3_b8)")
	pj.set_label(0xea83, "?zero(ce_d2)")
	pj.set_label(0xeaf4, "?divide()")
	pj.set_label(0xf101, "queue(X)")
	pj.set_label(0xf11f, "dispatch()")
	pj.set_label(0xf45d, "ramtest_280_29f()")
	pj.set_label(0xf4bd, "test_and_init_ram()")
	pj.set_label(0xf598, "check_sum_rom()")

	pj.set_label(0xd34f, "TIMER_SECOND()")

	pj.set_label(0xe34c, "KEYPRESS")
	pj.set_label(0xe51d, "DO_KEY_CLEAR")
	pj.set_label(0xe02b, "KEY_HANDLER_1")
	pj.set_label(0xe05e, "KEY_HANDLER_2")
	pj.set_label(0xe3c1, "DO_KEY_STATUS")
	pj.set_label(0xe542, "DO_KEY_BACKLIGHT")
	pj.set_label(0xe37e, "KEY_HANDLER_3")
	pj.set_label(0xdf41, "KEY_HANDLER_4")
	pj.set_label(0xf429, "KEY_HANDLER_5")
	pj.set_label(0xf377, "KEY_HANDLER_6")
	pj.set_label(0xf6bd, "KEY_SOMETHING")

	pj.set_label(0xe1c4, "BA=BCD([X++])")
	pj.set_label(0xe127, "SHOW_TIME")
	pj.set_label(0xe180, "SHOW_TIME_X")
	pj.set_label(0xe514, "MEMSET(X, A, 8)")
	pj.set_label(0xe516, "MEMSET(X, A, -B)")
	pj.set_label(0xe572, "__HELP__()")

	pj.set_label(0xe4d7, "PREP_IEEE_STRING()")
	pj.set_label(0xd089, "IEEE_INIT")
	pj.set_label(0xd3a2, "IEEE_TALK_ONLY")
	pj.set_label(0xe4b6, "IEEE_SEND()")
	pj.set_label(0xe2e3, "IEEE_RECV")
	pj.set_label(0xe32b, "IEEE_RECV_NO_CMD_YET")

	###############################################################
	# RAM
	pj.set_label(0x0012, "hours")
	pj.set_label(0x0013, "minutes")
	pj.set_label(0x0014, "seconds")
	pj.set_label(0x0015, "backlight_timer")
	pj.set_label(0x002c, "status_low_copy")
	pj.set_label(0x007f, "status_high_copy")
	for a in range(10):
		pj.set_label(0x0069 + a, "ascii_%d" % a)
	for a in range(12):
		pj.set_label(0x0073 + a, "ieee_%d" % a)
	pj.set_label(0x11c, "ieee_len")
	pj.set_label(0x80, "ieee_busy")
	pj.set_label(0x82, "ieee_ptr")
	pj.set_label(0x86, "ieee_cmd")

	pj.set_label(0x0055, "key_press")
	pj.set_label(0x0081, "has_ieee488")
	pj.set_label(0x008f, "key_press2")

	###############################################################
	# I/O space
	# Charset: '0123456789-EHLP "
	for a in range(8):
		pj.set_label(0xe00 + a, "LCD_%d" % a)

	pj.set_label(0xe08, "STATUS_LOW")
	pj.set_label(0xe0c, "STATUS_HIGH")
	pj.set_label(0xe10, "SWITCH_LOW")
	pj.set_label(0xe14, "SWITCH_HIGH")

	for a in range(8):
		pj.set_label(0xa000 + a, "IEEE488_R%d" % a)

if __name__ == '__main__':
	print(__file__)
	pj, cx = setup()
	task(pj, cx)
	listing.Listing(pj, ncol = 3)
