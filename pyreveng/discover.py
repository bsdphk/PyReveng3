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

"""
Code discovery class

The basic idea here is to build all the possible instructions
and then weed out the least likely ones, until no conflicts
exist any more.

Things to do:

* Report CALLs which never return to next instruction and
  estimate, if possible, size of in-line arguments.


"""

from pyreveng import mem, assy, code

class Discover():
	def __init__(self, pj, cx):
		self.pj = pj
		self.cx = cx

		# Clear the backlog first
		while pj.run():
			continue

		self.build_all()
		self.map_flows()
		self.map_overlap()

		# Let probs stabilize
		self.update_probs()
		self.update_probs()

		while True:
			self.update_probs()
			if self.prune() == 0:
				break
		self.commit()

	def build_all(self):
		"""
		Build all known and possible instructions
		"""

		self.code = dict()
		self.trust = dict()
		self.prob = dict()

		for i in self.pj.m:
			if i.tag == self.cx.name:
				self.code[i.lo] = i
				self.trust[i.lo] = 10
				self.prob[i.lo] = 1.0
		print("Known instructions:", len(self.code))

		n = 0
		for lx, hx in self.pj.m.gaps():
			for adr in range(lx, hx):
				try:
					x = self.cx.decode(self.pj, adr)
				except code.Invalid:
					continue
				except mem.MemError:
					continue
				except assy.Missing:
					continue
				assert x is not None
				for a in range(x.lo + 1, x.hi):
					if self.pj.m.get_labels(a):
						break
					if self.pj.m.get_block_comments(a):
						break
				else:
					self.code[adr] = x
					self.trust[adr] = 1
					self.prob[adr] = .25
					n += 1
		print("Possible instructions:", n)

	def map_flows(self):
		"""
		Link up the flows between instructions
		"""

		n = 0
		m = 0
		self.flow_in = dict()
		for i in self.code.values():
			self.flow_in[i.lo] = []
		for i in self.code.values():
			for f in i.flow_out:
				if f.to in self.code:
					self.flow_in[f.to].append(f)
					n += 1
				else:
					m += 1
		print("Possible flows", n)
		print("Dead end flows", m)

	def map_overlap(self):
		"""
		Build map of overlapping instructions
		"""
		self.overlap = dict()
		for i in self.code:
			if self.trust[i] == 0:
				continue
			c = self.code[i]
			for a in range(c.lo, c.hi):
				if a not in self.overlap:
					self.overlap[a] = []
				self.overlap[a].append(c.lo)
		n = 0
		for i in self.overlap.values():
			if len(i) > 1:
				n += 1
		print("Overlapped locations:", n)

	def update_probs(self):
		for i in self.code:
			self.prob[i] = self.calc_prob(i)

	def calc_prob(self, adr):
		if self.trust[adr] == 0:
			return 0
		if self.trust[adr] > 1:
			return self.prob[adr]

		# Default probability
		p = 0.10

		# Average weight of incoming flows, if any
		n = 0
		m = 0
		for f in self.flow_in[adr]:
			n += 1
			m += self.prob[f.fm.lo]
		if n > 0:
			p = m / float(n)

		# XXX ? Bonus for many incoming flows
		# p += 0.05 * max(0, n - 3)

		## ADDITIVE MODIFIERS ##

		# Reward no overlap on first location
		if len(self.overlap[adr]) == 1:
			p += 0.20


		# Penalize lowest prob in overlap
		c = self.code[adr]
		g = False
		for j in range(c.lo, c.hi):
			for k in self.overlap[j]:
				if k == adr:
					continue
				if self.prob[k] < self.prob[adr]:
					g = True
					break
		if not g:
			p -= 0.1

		# Bracket prob
		p = min(p, 1.0)
		p = max(p, 0.0)

		## SCALING MODIFIERS ##

		# Fractions of flows going somewhere
		n = 0
		c = self.code[adr]
		for f in c.flow_out:
			if f.typ == "R":
				n += 1
				continue
			x = self.trust.get(f.to)
			if x is not None and x > 0:
				n += 1
		p *= n / float(len(c.flow_out))

		return p

	def nuke(self, adr):
		"""
		Nuke an instruction from consideration
		"""

		self.trust[adr] = 0
		c = self.code[adr]
		for a in range(c.lo, c.hi):
			self.overlap[a].remove(adr)
		for f in c.flow_out:
			if f.to in self.code:
				self.flow_in[f.to].remove(f)

	def prune(self):
		"""
		Prune unlikely instructions
		"""

		n = 0
		for i in self.trust:
			if self.trust[i] == 0 or self.trust[i] > 1:
				continue
			if self.prob[i] < 0.1:
				self.nuke(i)
				n += 1
		m = 0
		for i in self.trust.values():
			if i > 0:
				m += 1
		#print("Pruned", n, "Left", m)
		return n

	def commit(self):
		n = 0
		for i in self.code:
			if self.trust[i] > 0 and self.trust[i] < 10:
				c = self.code[i]
				c.lcmt += "<discover>\n"
				c.commit(self.pj)
				n += 1
		print("Committed", n)
