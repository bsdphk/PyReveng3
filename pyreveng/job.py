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
This is the core of a PyReveng job, the one class everything hangs from
and its various helpers.

The reason for not relying on global variables is that it can be very
useful to analyse multiple versions of a given image in parallel.
"""

from __future__ import print_function

from . import tree, mem

class Leaf(object):
	"""
	These are the leaves we hang into the tree class.

	Many datatypes will sub-type this class and add functionality
	"""
	def __init__(self, p, lo, hi, tag):
		self.lo = lo
		self.hi = hi
		self.tag = tag
		self.lcmt = ""
		self.rendered = None
		self.compact = False

	def __repr__(self):
		s = "<leaf 0x%x-0x%x %s" % (self.lo, self.hi, self.tag)
		return s + ">"

	def render(self, pj):
		return self.rendered

	def arg_render(self, pj):
		return ""

class Job(object):
	"""
	A single analysis job

	"""
	def __init__(self, m, name="xxx"):
		self.name = name
		self.m = m
		self.t = tree.Tree(m.lo, m.hi)
		l = max(len("%x" % m.lo), len("%x" % (m.hi - 1)))
		self.apct = "0x%%0%dx" % l
		self.dolist = list()
		self.pending_flows = dict()	# flow.py
		self.labels = dict()
		self.block_comments = dict()
		self.comment_prefix = ";"

	def set_label(self, adr, lbl):
		self.labels[adr] = lbl

	def set_block_comment(self, adr, cmt):
		self.block_comments[adr] = cmt

	def set_comment_prefix(self, prefix):
		self.comment_prefix = prefix

	def afmt(self, a):
		return self.apct % a

	def render_adr(self, a):
		x = self.labels.get(a)
		if x != None:
			return x
		return self.afmt(a)

	def __iter__(self):
		for i in self.t:
			yield i

	def find(self, adr, tag=None):
		x = self.t.find_lo(adr)
		if tag == None:
			return x
		for i in x:
			if i.tag == tag:
				return i
		return None

	def insert(self, leaf):
		self.t.insert(leaf)

	def add(self, lo, hi, tag):
		l = Leaf(self, lo, hi, tag)
		self.t.insert(l)
		return l

	def gaps(self):
		l = list()
		ll = self.m.lo
		for i in self.t:
			if i.lo > ll:
				l.append((ll, i.lo))
			ll = i.hi
		if self.m.hi > ll:
			l.append((ll, self.m.hi))
		return l

	def todo(self, adr, func):
		assert type(adr) == int
		if adr < self.m.lo or adr >= self.m.hi:
			print("WARNING: Ignoring todo at illegal address " +
			    self.afmt(adr), func)
			return
		self.dolist.append((adr, func))

	def run(self):
		rv = False
		while len(self.dolist) > 0:
			rv = True
			adr, func = self.dolist.pop()
			try:
				func(self, adr)
			except mem.MemError:
				print("Fail: memory error",
				    self.afmt(adr), func)
			except:
				raise
		return rv
