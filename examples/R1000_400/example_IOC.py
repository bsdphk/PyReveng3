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
#

import os
from pyreveng import job, mem, listing, data, code, assy, pil, discover
import pyreveng.cpu.m68020 as m68020

def fc_puts_inline(pj, ins, flow):
	y = data.Txt(pj, ins.hi, label=False)
	flow.to = y.hi

def flow_check(pj, ins):
	for i in ins.flow_out:
		h = {
		0x80002028: fc_puts_inline,
		# 0x10284: fc_puts_inline,
		}.get(i.to)
		if h:
			h(pj, ins, i)
			break

mytrap_desc = '''
MYTRAP	vect,>J		|1 0 1 0 0 0 0 0| vect		|
'''

class mytrap_ins(m68020.m68020_ins):
	pass

M200S = []

class M200():

	def __init__(self, filename):
		self.filename = filename
		self.size = os.stat(filename).st_size
		self.m = mem.byte_mem(0, self.size)
		self.m.load_binfile(first = 0, step = 0x1, filename=filename)
		M200S.append(self)

	def __repr__(self):
		return "<M200 %s>" % self.filename

	def load_address(self):
		return self.m.bu16(0) << 15

	def entry_point(self):
		return self.m.bu32(4)

M200("/critter/DDHF/R1000/hack/X/FS_0.M200")
M200("/critter/DDHF/R1000/hack/X/RECOVERY.M200")
M200("/critter/DDHF/R1000/hack/X/M400C_KERNEL_0.M200")

def mem_setup():
	top = 0
	for obj in M200S:
		top = max(top, obj.load_address() + obj.size)
	m = mem.byte_mem(0, top)
	for obj in M200S:
		print("Load", obj, "at 0x%x" % obj.load_address())
		a = obj.load_address()
		for i in range(obj.size):
			m[a + i] = obj.m[i]

	return m

def setup():
	m = mem_setup()

	pj = job.Job(m, "R1000_400_IOC")
	cpu = m68020.m68020()
	cpu.flow_check.append(flow_check)
	cpu.trap_returns[0] = False
	cpu.it.load_string(mytrap_desc, mytrap_ins)
	return pj, cpu

def switch(pj, cpu, lo, hi):
	y = data.Data(pj, lo, hi)
	y.fmt = ""
	n = 0
	for a in range(lo, hi, 2):
		o = pj.m.bs16(a)
		y.fmt += "[%d] -> 0x%x\n" % (n, lo + o)
		pj.todo(lo + o, cpu.disass)
		pj.set_label(lo + o, "CASE_%x_%d" % (lo, n))
		n += 1


#######################################################################

def task(pj, cpu):

	pj.set_label(0x80002028, "INLINE_PUTS")

	cpu.vectors(pj)

	for obj in M200S:
		ep = obj.entry_point()
		pj.set_label(ep, "ENTRYPOINT_%s" % str(obj))
		pj.todo(obj.entry_point(), cpu.disass)

	pj.todo(0x08ad2, cpu.disass)

	if True:
		data.Txt(pj, 0x294cc, 0x294da)
		
	if True:
		for a in (0x08ad6, 0x08ada):
			data.Const(pj, a, a + 4)

	if True:
		for a in range(0x09080, 0x09098, 4):
			pj.todo(a, cpu.disass)
	if True:
		for a in range(0x10460, 0x1061e, 6):
			pj.todo(a, cpu.disass)
	if True:
		for a in range(0x10280, 0x10460, 4):
			pj.todo(a, cpu.disass)

	if True:
		switch(pj, cpu, 0x13368, 0x1336e)
		switch(pj, cpu, 0x14552, 0x14556)
		switch(pj, cpu, 0x1635e, 0x16374)
		switch(pj, cpu, 0x164b4, 0x164c4)
		switch(pj, cpu, 0x16852, 0x16858)
		switch(pj, cpu, 0x19536, 0x1953e)
		switch(pj, cpu, 0x22cf6, 0x22cfe)
		switch(pj, cpu, 0x2413c, 0x24142)
		switch(pj, cpu, 0x255fc, 0x25602)
		switch(pj, cpu, 0x257a8, 0x257b2)
		switch(pj, cpu, 0x293b6, 0x293c4)

	if True:
		for a in range(0x02448, 0x02454, 4):
			pj.todo(a, cpu.disass)
		for a in range(0x03b74, 0x03b84, 4):
			pj.todo(a, cpu.disass)
		for a in range(0x04276, 0x04282, 2):
			pj.todo(a, cpu.disass)

	if True:
		for lo,hi in (
			(0x04dbc, 0x04dd0),
			(0x06596, 0x065ae),
			(0x06642, 0x0665a),
			(0x09378, 0x09398),
		):
			for a in range(lo, hi, 4):
				y = cpu.codeptr(pj, a)
				pj.set_label(y.dst, "PTR_FM_%x" % a)
		for a in range(0x04fca, 0x04fda, 4):
			y = cpu.codeptr(pj, a)
			pj.set_label(y.dst, "PTR_FM_%x" % a)
		for a in range(0x062dc, 0x062f8, 4):
			y = cpu.codeptr(pj, a)
			pj.set_label(y.dst, "PTR_FM_%x" % a)
		for a in range(0x093c4, 0x093fc, 4):
			y = cpu.codeptr(pj, a)
			pj.set_label(y.dst, "PTR_FM_%x" % a)
		for a in range(0x09495, 0x0956d, 4):
			y = cpu.codeptr(pj, a)
			pj.set_label(y.dst, "PTR_FM_%x" % a)
		for a in range(0x09578, 0x095a4, 4):
			y = cpu.codeptr(pj, a)
			pj.set_label(y.dst, "PTR_FM_%x" % a)
		for a in range(0x095e8, 0x0969c, 4):
			y = cpu.codeptr(pj, a)
			pj.set_label(y.dst, "PTR_FM_%x" % a)
		for a in range(0x096c4, 0x096e4, 4):
			y = cpu.codeptr(pj, a)
			pj.set_label(y.dst, "PTR_FM_%x" % a)
		for a in range(0x097bc, 0x0983c, 4):
			y = cpu.codeptr(pj, a)
			pj.set_label(y.dst, "PTR_FM_%x" % a)
		for a in range(0x09850, 0x09894, 4):
			y = cpu.codeptr(pj, a)
			pj.set_label(y.dst, "PTR_FM_%x" % a)
		for a in range(0x06026, 0x06036, 4):
			y = cpu.codeptr(pj, a)
			pj.set_label(y.dst, "PTR_FM_%x" % a)
		for a in range(0x20004, 0x20020, 4):
			if pj.m.bu32(a) and a != 0x20010:
				y = cpu.codeptr(pj, a)
				pj.set_label(y.dst, "PTR_FM_%x" % a)

	if True:
		for lo,hi in (
			(0x09100, 0x0912a),
			(0x0929b, 0x092a9),
			(0x092bc, 0x0933a),
			(0x09398, 0x093c2),
		):
			for a in range(lo, hi, 2):
				y = pj.m.bu16(a)
				data.Const(pj, a, a + 2, func=pj.m.bu16, size=2, fmt="0x%x")
				pj.todo(y, cpu.disass)
				pj.set_label(y, "PTR_FM_%x" % a)
			

	if True:
		for a in range(0x092ac, 0x092bc, 4):
			data.Const(pj, a, a + 4)

	if True:
		for a in (
			0x02602,
			0x02886,
			0x02c2e,
			0x02e00,
			0x02efe,
			0x0317c,
			0x036a6,
			0x03b3c,
			0x03b4a,
			0x03e6a,
			0x03e78,
			0x03e86,
			0x03e94,
			0x03ea0,
			0x03eae,
			0x03eb6,
			0x03ebc,
			0x03eca,
			0x0409c,
			0x04198,
			0x041a4,
			0x041b6,
			0x04354,
			0x04480,
			0x04486,
			0x044b2,
			0x045e2,
			0x045ec,
			0x0460a,
			0x048fc,
			0x04950,
			0x049d8,
			0x04dd0,
			0x04fa8,
			0x051f6,
			0x05c02,
			0x05d28,
			0x06492,
			0x066ca,
			0x069da,
			0x06a22,
			0x06aea,
			0x06da2,
			0x06df8,
			0x07208,
			0x07286,
			0x07b84,
			0x085ee,
			0x0871a,
			0x087a4,
			0x087b0,
			0x087fe,
			0x0889a,
			0x088cc,
			0x08914,
			0x0895c,
			0x08a70,
			0x08b44,
			0x08b4c,
			0x08b72,
			0x08d14,
			0x08d14,
			0x1070c,
			0x11582,
			0x118a2,
			0x11a36,
			0x124a8,
			0x12836,
			0x13954,
			0x15720,
			0x16cf2,
			0x16f50,
			0x1878a,
			0x22522,
			0x225aa,
			0x225ba,
			0x22730,
			0x22ae2,
			0x23bb4,
			0x286b0,
			0x290da,
			0x294b0,
		):
			pj.todo(a, cpu.disass)

	while pj.run():
		pass

	if False:
		d = discover.Discover(pj, cpu)
		while pj.run():
			pass

	return

#######################################################################

if __name__ == '__main__':
	pj, cx = setup()
	task(pj, cx)
	code.lcmt_flows(pj)
	listing.Listing(pj, ncol=8, pil=False)
