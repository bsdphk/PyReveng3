#!/usr/bin/env python
#
# Copyright (c) 2016-2017 Poul-Henning Kamp <phk@phk.freebsd.dk>
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

"""
Intermediate Language

This is not exactly LLVM's IL.  The we use it as a "generic" assembly
language for human consumption, not for precise directives to code
generators.  However, it is the intent that conversion to proper
LLVM IL a trivial exercise in dumb text-processing

"""

from __future__ import print_function

#######################################################################

class IL(object):
	def __init__(self, lo):
		self.lo = lo
		self.oper = []
		self.il = []
		self.il_c = 0

	def il_reg(self, r, d):
		if r[0] != "%":
			return r
		# XXX Problem with instructions at loc=0
		o = self.lo * 100
		if r[1:].isdigit():
			if int(r[1:]) >= 100:
				return r
			n = "%%%d" % (o + self.il_c)
			d[r] = n
			self.il_c += 1
			return n
		return r

	def add_il(self, ins, ll, ret=None):
		if ll == None:
			return
		d = {}
		for l in ll:
			if l == None:
				continue
			if isinstance(l, str):
				f = l.split()
			else:
				f = l
				for i in f:
					assert i == i.strip()
			if len(f) == 0:
				continue
			v = []
			for i in f:
				j = d.get(i)
				if j is not None:
					v.append(j)
					continue
				j = self.il_reg(i, d)
				if j != i:
					v.append(j)
					continue
				try:
					j = getattr(ins, "ilmacro_" + i)
				except AttributeError:
					v.append(i)
					continue
				# self.il.append(["/* MACRO " + i + " */"])
				k = j()
				if k is not None:
					x = self.il_reg(k, d)
					v.append(x)
			if len(v) == 0:
				continue

			try:
				j = getattr(ins, "ilfunc_" + v[0])
			except AttributeError:
				self.il.append(v)
				continue
			# self.tl.append(["/* FUNC " + " ".join(v) + " */" ])
			j(v[1:])
		return d.get(ret)

	def render(self):
		t = ""
		for i in self.il:
			t += "IL " + " ".join(i) + "\n"
		return t
