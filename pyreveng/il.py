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

class IL_Stmt(object):
	''' A single IL statement '''
	def __init__(self, spec):
		self.spec = spec
		self.decorate = None

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

	def __getitem__(self, i):
		return self.spec[i]

	def __repr__(self):
		return "<IL %s>" % self.render()

#######################################################################

class IL_Ins(object):
	''' IL statements related to a single assy/code object '''
	def __init__(self, ins = None):
		self.ins = ins
		self.il = []
		self.il_c = 0
		# self.add_il(ins, [["0x%x" % ins.lo, ":"]])

	def il_reg(self, r, d):
		if r[0] != "%":
			return r
		if r[1:].isdigit():
			n = "%%_i%x_%d" % (self.ins.lo, self.il_c)
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
				self.il.append(IL_Stmt(v))
				continue
			# self.tl.append(["/* FUNC " + " ".join(v) + " */" ])
			j(v[1:])
		return d.get(ret)

	def render(self):
		t = ""
		for i in self.il:
			t += "IL " + i.render() + "\n"
		return t

#######################################################################

class IL_BB(object):
	def __init__(self):
		self.lo = None
		self.hi = None
		self.ilins = []
		self.ils = []
		self.goto = []
		self.comefrom = []
		self.doa = set()

	def __repr__(self):
		return "<BB 0x%x-0x%x>" % (self.lo, self.hi)

	def dot_def(self, fo, pj):
		def bb():
			fo.write('<TR><TD ALIGN="left" BALIGN="left">\n')
			fo.write('<FONT FACE="Courier">\n')
		def ee():
			fo.write('</FONT>\n')
			fo.write("</TD></TR>\n")

		fo.write('IL%x [shape="none",label=<\n' % self.lo)
		fo.write('<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"')
		fo.write(' ALIGN="left">\n')
		fo.write('<TR><TD>0x%x-0x%x</TD></TR>\n' % (self.lo, self.hi))

		bb()
		for i in self.ilins:
			fo.write(i.render(pj).expandtabs())
			fo.write('<BR/>\n')
		ee()

		bb()
		fo.write("DOA:<BR/>\n")
		l = list(self.doa)
		l.sort()
		for i in l:
			fo.write('%s<BR/>\n' % i)
		ee()

		bb()
		fo.write("From:<BR/>\n")
		for i in self.comefrom:
			fo.write('0x%x-0x%x <BR/>\n' % (i.lo, i.hi))
		ee()

		bb()
		for i in self.ils:
			if i.decorate is not None:
				fo.write('<FONT color="%s">' % i.decorate)
			fo.write('%s' % i.render())
			if i.decorate is not None:
				fo.write('</FONT>')
			fo.write('<BR/>\n')
		ee()

		bb()
		fo.write("To:<BR/>\n")
		for i in self.goto:
			if isinstance(i, IL_BB):
				fo.write("0x%x-0x%x<BR/>\n" % (i.lo, i.hi))
			else:
				fo.write("%s<BR/>\n" % i)
		ee()

		fo.write('</TABLE>\n')
		fo.write('>]\n')
		return

	def whereto(self):
		j = self.ils[-1]
		if j[0] != "br":
			return [ self.hi ]
		l = []
		for x in range(len(j.spec)):
			if j[x] != "label":
				continue
			x += 1
			if j[x][0] == "i":
				x += 1
			if j[x][:3] == "0x-":
				continue
			if j[x][:2] == "0x":
				l.append(int(j[x], 0))
			else:
				l.append(j[x])
		return l

	def build_doa(self, init=None, color = "blue"):
		nn = 0
		# print("DOA", self, color, init)
		doa = {}
		if init is not None:
			for j in init:
				doa[j] = True

		for j in self.ils:
			for x in j.outputs():
				if x[:2] == "%1":
					doa[x] = True

		for j in reversed(self.ils):
			if j[0] == "pyreveng.void":
				doa = {}
				continue
			n = 0
			m = 0
			for x in j.outputs():
				m += 1
				z = doa.get(x)
				if z is not True:
					n += 1
				doa[x] = True
			if n == 0 and m > 0:
				if j.decorate is None:
					j.decorate = color
					nn += 1
			else:
				for x in j.inputs():
					doa[x] = False
		for i in doa:
			if i[:2] != "%1" and doa[i] is True:
				self.doa.add(i)
		return nn


class analysis(object):
	def __init__(self, pj):
		self.ilbbs = {}
		self.pj = pj

		noil = {}

		# XXX: This is kind of silly
		from . import assy

		for j in pj:
			if not isinstance(j, assy.Assy):
				continue
			y = IL_BB()
			for x in j.il.il:
				y.ils.append(x)
			if len(y.ils) == 0:
				a = j.render(pj).expandtabs()
				b = j.lim[-1].assy[0]
				if b not in noil:
					noil[b] = 1
				else:
					noil[b] += 1
				z = IL_Stmt(["pyreveng.void", "(",
				    '"' + a + '"', ")"])
				z.decorate = "magenta"
				y.ils.append(z)
			y.lo = j.lo
			y.hi = j.hi
			y.ilins.append(j)
			self.ilbbs[j.lo] = y

		#l = list(noil.iteritems())
		l = list(noil.items())
		l.sort(key=lambda x: -x[1])
		print("Top twenty IL-deficient instructions:")
		for i,j in l[:20]:
			print("\t", i, j)

		self.build_flow()
		#for a,x in self.ilbbs.iteritems():
		for a,x in self.ilbbs.items():
			x.build_doa()
		self.propagate_doa("red")
		self.propagate_doa("green")
		for i in range(10):
			if self.propagate_doa("brown") == 0:
				break

	def dump_bbs(self, fo):
		l = list(self.ilbbs.keys())
		l.sort()
		for j in l:
			x = self.ilbbs[j]
			fo.write("digraph {\n")
			x.dot_def(fo, self.pj)
			fo.write("}\n")

	def build_flow(self):
		#for a,x in self.ilbbs.iteritems():
		for a,x in self.ilbbs.items():
			d = x.whereto()
			for j in d:
				if isinstance(j, int):
					y = self.ilbbs.get(j)
					if y == None:
						print("None bbs", j)
						continue
					assert y != None
					y.comefrom.append(x)
					x.goto.append(y)
				else:
					x.goto.append(None)
					# print(x, j)
		l = list(self.ilbbs.keys())
		l.sort()
		for j in l:
			while True:
				x = self.ilbbs.get(j)
				if x is None:
					break
				if len(x.goto) > 1:
					break
				if len(x.goto) == 0:
					print("No goto", x)
					break
				z = x.goto[0]
				if z is None:
					break
				if z.lo != x.hi:
					break
				y = self.ilbbs.get(x.hi)
				assert y is not None
				if len(y.comefrom) != 1:
					break
				assert y.comefrom[0] == x
				x.ils += y.ils
				x.hi = y.hi
				x.ilins += y.ilins
				for i in y.goto:
					if isinstance(i, IL_BB):
						i.comefrom.remove(y)
						i.comefrom.append(x)
				x.goto = y.goto
				del self.ilbbs[y.lo]

	def propagate_doa(self, color):
		n = 0
		#for a,x in self.ilbbs.iteritems():
		for a,x in self.ilbbs.items():
			#print("PROP", x)
			if len(x.goto) == 0:
				continue
			if None in x.goto:
				continue
			dd = x.goto[0].doa
			for j in x.goto:
				#print("\t", j, j.doa)
				dd = dd.intersection(j.doa)
			if len(dd) == 0:
				continue
			#print("  ", dd)
			n += x.build_doa(dd, color)
		print("PROP eliminated", n)
		return n
