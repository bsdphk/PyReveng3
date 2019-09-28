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

'''HP6034A System DC Power Supply
'''

import os
from pyreveng import job, mem, listing, data, code
import pyreveng.cpu.tms9900 as tms9900

def mem_setup():
	m = mem.ByteMem(0x0000, 0x2000)
	fn = os.path.join(os.path.dirname(__file__), "HP6034A_U25.hex")
	for i in open(fn):
		j = i.split()
		m.wr(int(j[0], 16), int(j[1], 16))
	return m

def setup():
	cx = tms9900.Tms9981()
	cx.m.map(mem_setup(), 0)
	pj = job.Job(cx.m, "HP6034A")
	return pj, cx

cru_adr = {
	# U12
	0x080:	"LED_RMT",
	0x082:	"LED_CV_NORMAL",
	0x084:	"LED_CC_NORMAL",
	0x086:	"LED_OVP",
	0x088:	"LED_UNREGULATED",
	0x08a:	"LED_CV_LIMIT",
	0x08c:	"LED_DISABLED",
	0x08e:	"LED_SRQ",

	# U13
	0x090:	"LED_OTP",
	0x092:	"LED_LSN",
	0x094:	"#M2_MODE",
	0x096:	"#M1_MODE",
	0x098:	"LED_INVALID_REQUEST",
	0x09a:	"#REQ_SERVICE",
	0x09c:	"TEST",
	0x09e:	"INTERRUPT_ENABLE",

	# U14
	0x0c0:	"#DISABLE",
	0x0c2:	"LED_TLK",
	0x0c4:	"OVP_RESET",
	0x0c6:	"RESET_RPG_DECODER",
	0x0c8:	"TIMER_TRIGGER",
	0x0ca:	"LED_VOLTAGE",
	0x0cc:	"LED_CURRENT",
	0x0ce:	"LED_CC_LIMIT",

	0x0d0:	"VOLTAGE_DAC",
	# ... 0x0e6

	0x0e8:	"CURRENT_DAC",
	# ... 0x0fe

	0x100:	"OVP_DAC",
	0x110:	"LOAD_DACS",
}

def task(pj, cx):

	cx.vectors(pj, xops = 0)

	def dptr(pj, a):
		v = pj.m.bu16(a)
		data.Dataptr(pj.m, a, a + 2, v)
		return v


	i_args = {
		0x79c:	"ii",
		0x936:	"i",
	}

	def inline_args(pj, ins):
		for f in ins.flow_out:
			i = i_args.get(f.to)
			if i == None:
				continue
			ins.flow_out = []
			ins.add_flow(pj, "C", True, f.to)
			a = ins.hi
			for j in i:
				if j == "i":
					d = pj.m.bu16(a)
					data.Dataptr(pj.m, a, a + 2, d)
					a += 2
				else:
					print("IARG:", j)
					assert False
			ins.add_flow(pj, ">", True, a)
			return

	cx.flow_check.append(inline_args)

	if True:
		# HPIB input command dispatch
		l = []
		for a in range(0x0cd3, 0x0ce2):
			c = data.Txt(pj.m, a, a + 1, False)
			l.append(c.txt)
		# print(l)
		for a in range(0xcee, 0xd0c, 2):
			c = cx.codeptr(pj, a)
			n = l.pop(0)
			if n == "\\r":
				n = "SEP"
			elif n == "+":
				n = "SIGN"
			elif n == "C":
				n = "CP"
			if not pj.m.get_labels(c.dst):
				pj.m.set_label(c.dst, "CMD_" + n)

	if True:
		for a in range(0x0d0c, 0x0d0f):
			data.Txt(pj.m, a, a + 1, False)
		for a in range(0xf43, 0xf4a):
			data.Txt(pj.m, a, a + 1, False)
		data.Txt(pj.m, 0xf4a, 0xf4c, False)
		for a in range(0xf54, 0xf56):
			data.Txt(pj.m, a, a + 1, False)

	if True:

		for i in range(0, 12, 2):
			dptr(pj, 0x230 + i)
			dptr(pj, 0x248 + i)
			dptr(pj, 0x254 + i)
			cx.codeptr(pj, 0x23c + i)

	if True:
		cx.disass(pj, 0x037c)
		cx.disass(pj, 0x038e)
		cx.disass(pj, 0x03aa)
		cx.disass(pj, 0x03ba)
		cx.disass(pj, 0x03ca)
		cx.disass(pj, 0x0406)
		cx.disass(pj, 0x0428)
		cx.disass(pj, 0x044a)
		cx.disass(pj, 0x0458)
		cx.disass(pj, 0x052e)

	if True:
		# Pure guesswork
		#for a in range(0xcee, 0xd0c, 2):
		#	cx.codeptr(pj, a)
		cx.disass(pj, 0x0e1e)

	if True:
		cx.disass(pj, 0x0d18)

	if True:
		cx.disass(pj, 0x0e50)
		cx.disass(pj, 0x0e80)

	if True:
		for a in range(0xf1c, 0xf20):
			data.Txt(pj.m, a, a + 1, False)

	if True:
		cx.disass(pj, 0x10b2)

	if True:
		# Continuation addresses when more bytes arrive
		for a in range(0xf4e, 0xf54, 2):
			cx.codeptr(pj, a)

	if True:
		for a in range(0xf3e, 0xf42, 2):
			cx.codeptr(pj, a)

	if True:
		for a in range(0x468, 0x474, 2):
			v = dptr(pj, a)
			cx.vector(pj, v)

	if True:
		for a in range(0xf5a, 0xf7a, 2):
			c = data.Const(pj.m, a, a + 2)
			c.typ = ".WORD"
			c.fmt = "0x%04x" % pj.m.bu16(a)
		for a in range(0xf7a, 0xf7e, 2):
			c = data.Const(pj.m, a, a + 2)
			c.typ = ".WORD"
			c.fmt = "%d" % pj.m.bu16(a)
		for a in range(0xf7e, 0xfaa, 2):
			c = data.Const(pj.m, a, a + 2)
			c.typ = ".WORD"
			c.fmt = "%d" % pj.m.bu16(a)

	if True:
		# Failure Flash Codes
		for a in range(0xcc, 0xd8, 2):
			dptr(pj, a)

	pj.m.set_label(0x00cc, "FAIL_LEDS")
	pj.m.set_label(0x0140, "FAIL_1")
	pj.m.set_label(0x0146, "FAIL_2")
	pj.m.set_label(0x018a, "FAIL_3")
	pj.m.set_label(0x0190, "FAIL_4")
	pj.m.set_label(0x01d6, "FAIL_5")
	pj.m.set_label(0x01e2, "FAIL_6")
	pj.m.set_label(0x0212, "FLASH_FAIL")
	pj.m.set_label(0x0656, "MESH_PREMPTED")
	pj.m.set_label(0x0660, "HPIB_PREMPTED")
	pj.m.set_label(0x066a, "TIMER_PREMPTED")
	pj.m.set_label(0x0912, "PON2_1")
	pj.m.set_label(0x08e4, "PON2_2")
	pj.m.set_label(0x0894, "PON2_3")
	pj.m.set_label(0x08bc, "PON2_4")
	pj.m.set_label(0x0920, "PON2_5")
	pj.m.set_label(0x0abe, "TIMER_INTR")
	pj.m.set_label(0x0b7c, "HPIB_INTR")
	pj.m.set_label(0x0ccc, "HPIP_INCHAR")
	pj.m.set_label(0x0ce2, "END_INCHAR")
	pj.m.set_label(0x0d18, "INCHAR_MAIN")
	pj.m.set_label(0x0f7e, "1_10_100_1000")
	pj.m.set_label(0x1328, "MESH_INTR")
	pj.m.set_label(0x175c, "SET_CC_CV_LEDS")
	pj.m.set_label(0x2002, "NEXT_CHAR_PROC")
	pj.m.set_label(0x20ca, "CV_DAC_VAL")
	pj.m.set_label(0x20cc, "CC_DAC_VAL")
	pj.m.set_label(0x20ce, "CV_DAC_SET")
	pj.m.set_label(0x20d0, "CC_DAC_SET")
	pj.m.set_label(0x20d6, "DELAY_VAL")
	pj.m.set_label(0x20d8, "MODE_SET")
	pj.m.set_label(0x20da, "MODE_VAL")
	pj.m.set_label(0x20d4, "COUNT_DOWN")


if __name__ == '__main__':
	pj, cx = setup()
	task(pj, cx)
	listing.Listing(pj, ncol = 4)
