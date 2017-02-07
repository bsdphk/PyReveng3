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

class ILS(object):
	def __init__(self, spec):
		self.spec = spec

	def render(self):
		return " ".join(self.spec)

	def outputs(self):
		l = []
		if self.spec[1] == "=":
			l.append(self.spec[0])
		return l

	def inputs(self):
		l = []
		if self.spec[1] == "=":
			for i in self.spec[2:]:
				if i[0] == "%":
					l.append(i)
		else:
			for i in self.spec:
				if i[0] == "%":
					l.append(i)
		return l

class IL(object):
	def __init__(self, ins = None):
		self.ins = ins
		self.il = []
		self.il_c = 0

	def il_reg(self, r, d):
		if r[0] != "%":
			return r
		# We add a million to avoid problems at lo=0
		o = self.ins.lo * 100 + 10000000
		if r[1:].isdigit():
			if int(r[1:]) >= 100:
				return r
			n = "%%%d" % (o + self.il_c)
			d[r] = n
			self.il_c += 1
			return n
		return r

	def add_il(self, ins, ll, ret=None):
		'''
		Add IL's in 'll', translating "%0" .. "%99" to unique
		names along the way.  'ret' can be one of these and
		the new unique name will be returned.
		'''
		if ll == None:
			assert ret is None
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
				if isinstance(k, list):
					for x in k:
						y = self.il_reg(x, d)
						v.append(y)
				elif k is not None:
					assert isinstance(k, str)
					x = self.il_reg(k, d)
					v.append(x)
			if len(v) == 0:
				continue

			try:
				j = getattr(ins, "ilfunc_" + v[0])
			except AttributeError:
				self.il.append(ILS(v))
				continue
			# self.tl.append(["/* FUNC " + " ".join(v) + " */" ])
			j(v[1:])
		return d.get(ret)

	def render(self):
		t = ""
		for i in self.il:
			t += "IL " + i.render() + "\n"
		return t

	def dot_def(self, fo):
		fo.write('IL%x [shape="record",label="{' % self.lo)
		fo.write("<in>0x%x-0x%x|" % (self.lo, self.hi))
		for i in self.il:
			j = i.render()
			fo.write("%s\\l" % j)
		if len(self.il) == 0:
			fo.write("|XXX")
		fo.write('|<out>}"]\n')

import assy

class analysis(object):
	def __init__(self, pj):
		self.ils = {}
		self.writes = {}
		self.reads = {}
		for j in pj:
			if not isinstance(j, assy.Assy):
				continue
			x = j.il
			self.ils[j.lo] = x
			x.next = None
			x.prev = None
			x.comefrom = []
			x.goto = []
			x.lo = x.ins.lo
			x.hi = x.ins.hi
			x.ins = [x.ins]
			x.parts = []
			if len(x.il) == 0:
				x.il.append(ILS(["pyreveng.void", "(", ")"]))
			for y in x.il:
				for z in y.outputs():
					self.writes[z] = True
				for z in y.inputs():
					self.reads[z] = True

		print("RAW", self.stats())
		self.find_flow()
		self.stitch()
		print("STICHED", self.stats())
		self.dead_stores()
		print("DEAD STORES", self.stats())
		self.totally_dead()
		self.dot()

	def stats(self):
		n = 0
		for a,x in self.ils.iteritems():
			n += len(x.il)
		return "%d ILs with %d instructions" % (len(self.ils), n)

	def find_flow(self):
		for j,x in self.ils.iteritems():
			z = x.il[-1]
			if z.spec[0] != "br":
				continue
			d = []
			p = 1
			while p < len(z.spec):
				if z.spec[p] != "label":
					p += 1
					continue
				if z.spec[p+1][:2] == "0x":
					d.append(int(z.spec[p+1], 0))
					p += 2
					continue
				if z.spec[p+1][:1] == "i" and z.spec[p+2][:2] == "0x":
					d.append(int(z.spec[p+2], 0))
					p += 3
					continue
				print(z.spec[p:])
				d.append(None)
				p += 1
			assert len(d) > 0
			for y in d:
				if y is not None:
					z = self.ils[y]
					x.goto.append(z)
					z.comefrom.append(y)
				else:
					x.goto.append(None)

	def stitch(self):
		joins = []

		# Convert .ins to list
		for j,x in self.ils.iteritems():
			if x.il[-1].spec[0] != "br":
				y = self.ils[x.hi]
				if len(y.comefrom) == 0:
					joins.append(x)
					x.next = y
					y.prev = x
				else:
					x.il.append(ILS(
					    ["br", "label", "0x%x" % x.hi]
					))
					x.goto.append(y)
					y.comefrom.append(x)

		heads = []
		for j in joins:
			if j.prev == None:
				heads.append(j)

		for j in heads:
			k = IL()
			k.lo = j.lo
			k.ins = []
			k.comefrom = j.comefrom
			k.parts = []
			n = j
			while n is not None:
				k.parts.append(n)
				k.il += n.il
				k.hi = n.hi
				k.ins += n.ins
				k.goto = n.goto
				del self.ils[n.lo]
				n = n.next
			self.ils[k.lo] = k

	def dead_stores(self):
		for a,x in self.ils.iteritems():
			edit = ""
			nn = 0
			j = 0
			while j < len(x.il):
				if x.il[j].spec[1] != "=":
					j += 1
					continue
				t = x.il[j].spec[0]
				m = "  " + x.il[j].render()
				for k in range(j+1,len(x.il)):
					p = x.il[k]
					if p.spec[0] == "pyreveng.void":
						break
					if t not in p.spec:
						continue
					if p.spec[0] == t and p.spec[1] == "=":
						y = x.il.pop(j)
						m = "-" + m[1:]
						nn += 1
						j -= 1
						break
					else:
						break
				edit += "\n" + m
				j += 1
			if nn > 0:
				print("EDIT 0x%x" % x.lo, edit);

	def totally_dead(self):
		for i in self.writes:
			if not i in self.reads:
				print("Totally dead", i)

	def dot(self):
		# present
		fo = open("/tmp/_.dot", "w")
		fo.write("digraph {\n");
		for a,x in self.ils.iteritems():
			n=0
			x.dot_def(fo)
			for j in x.goto:
				fo.write("IL%x -> " % a)
				if j is None:
					fo.write("XX%x_%d\n" % (a, n))
					n += 1
				else:
					fo.write("IL%x:in\n" % j.lo)
		fo.write("}\n")



