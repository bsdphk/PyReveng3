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

from pyreveng import data

class PSOS():

	def __init__(self, cpu, a0):
		print("CPU", cpu)
		self.cpu = cpu
		self.a0 = a0
		self.cfg = {}

		cpu.m.set_label(a0, "PSOS_CFG")
		for o,l,t,n in (
			(  0, 4, self.const,	"ramstart1"),
			(  4, 4, self.const,	"ramend1"),
			(  8, 4, self.const,	"minseg1"),
			( 12, 4, self.const,	"ramstart2"),
			( 16, 4, self.const,	"ramend2"),
			( 20, 4, self.const,	"minseg2"),
			( 24, 2, self.const,	"nproc"),
			( 26, 2, self.const,	"Nexch"),
			( 28, 2, self.const,	"nmgb"),
			( 30, 2, self.const,	"ticks_per_sec"),
			( 32, 2, self.const,	"ticks_per_slice"),
			( 34, 2, self.const,	"niod"),
			( 36, 4, self.const,	"iotable"),
			( 40, 4, self.const,	"subv_stacksize"),
			( 44, 4, self.codeptr,	"root_start"),
			( 48, 4, self.const,	"root_stacksize"),
			( 52, 2, self.const,	"root_priority"),
			( 54, 4, self.codeptr,	"activate_proc"),
			( 58, 4, self.codeptr,	"delete_proc"),
			( 62, 4, self.codeptr,	"switch_proc"),
			( 66, 4, self.const,	"probe_present"),
			( 70, 4, self.const,	"phile_present"),
		):
			cpu.m.set_label(self.a0 + o, "PSOS_CFG." + n)
			t(self.a0 + o, self.a0 + o + l, n)
			if l == 2:
				self.cfg[n] = cpu.m.bu16(self.a0 + o)
			if l == 4:
				self.cfg[n] = cpu.m.bu32(self.a0 + o)

		self.iotable(self.cfg["niod"], self.cfg["iotable"])

	def const(self, lo, hi, lbl):
		data.Const(self.cpu.m, lo, hi)

	def codeptr(self, lo, hi, lbl):
		assert hi == lo + 4
		x = self.cpu.m.bu32(lo)
		if x:
			self.cpu.m.set_label(x, "FOR_PSOS_" + lbl)
			self.cpu.codeptr(lo)

	def iotable(self, niod, iotable):
		n = 0
		a = iotable
		while n <= niod:
			self.cpu.m.set_label(a, "PSOS_IOTABLE[%d]" % n)
			for o, f in (
				(  0, "func0"),
				(  6, "func1"),
				( 12, "func2"),
				( 18, "func3"),
				( 24, "func4"),
				( 30, "func5"),
			):
				self.cpu.m.set_label(a + o,
				    "PSOS_IO_TABLE[%d]." % n + f)
				self.cpu.disass(a + o)
			a += 30
			n += 1
