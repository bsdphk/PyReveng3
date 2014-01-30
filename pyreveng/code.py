#!/usr/local/bin/python
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
Code leaf subclasses

The code object represents an amount of memory content which is executed
somehow.  Code objects tie together with "flow" objects, which tell
where execution will continue.

"""

from __future__ import print_function

import pyreveng

#######################################################################

class flow(object):
	def __init__(self, fm, typ, cond=True, to=None, lang=None):
		if lang == None:
			lang = fm.lang
		self.fm = fm
		self.lang = lang
		self.typ = typ
		self.cond = cond
		self.to = to
		self.dst = None

		if typ == True:
			self.to = fm.hi

	def propagate(self, pj):
		if self.fm.lo in pj.pending_flows:
			x = pj.pending_flows[self.fm.lo]
			del pj.pending_flows[self.fm.lo]
			x.propagate(pj)

		if self.to != None:
			pj.todo(self.to, self.lang.disass)
		if False:
			if self.typ == True:
				pj.todo(self.fm.hi, self.lang.disass)
			elif self.typ == "R":
				return
			elif self.typ == ">" or self.typ == "C":
				if type(self.to) == int:
					pj.todo(self.to, self.lang.disass)
			elif self.typ == "S1":
				x = pj.find(self.fm.hi, self.fm.tag)
				if x == None:
					pj.pending_flows[self.fm.hi] = self
				else:
					pj.todo(x.hi, self.lang.disass)
			else:
				print("Missing flow", self.typ)

	def __repr__(self):
		s = "<Flow @%x " % self.fm.lo + str(self.typ) 
		if self.to == None:
			s += " -"
		else:
			s += " 0x%x" % self.to
		s += ">"
		return s

	def lcmt(self, leaf):
		if self.typ == True:
			return
		s = "Flow %s" % self.typ
		if self.cond == None:
			s += " cc=?"
		elif self.cond != True:
			s += " cc=%s" % self.cond
		if self.to != None:
			s += " 0x%x" % self.to
		leaf.lcmt += s + "\n"

	
#######################################################################

def lcmt_flows(pj):
	"""
	Add line-comments for all flow records
	"""
	for i in pj:
		if isinstance(i, code):
			for j in i.flow_out:
				j.lcmt(i)

#######################################################################

class code(pyreveng.leaf):
	def __init__(self, pj, lo, hi, lang):
		self.lang = lang
		super(code, self).__init__(pj, lo, hi, lang.name)
		self.flow_in = []
		self.flow_out = []

	def render(self, pj):
		return "<Code %x-%x %s>" % (self.lo, self.hi, self.lang.name)

	def add_flow(self, pj, typ, cond=True, to=None, lang=None):
		"""
		Add a flow record
		"""
		f = flow(self, typ, cond, to, lang)
		self.flow_out.append(f)

	def propagate(self, pj):
		"""
		Follow the flow records to find more code
		"""
		for f in self.flow_out:
			f.propagate(pj)
