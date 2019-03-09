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
Disassembler for HP1345A graphical primitives
"""

from __future__ import print_function

from pyreveng import instree, assy

hp85662a_instructions = """
DSPJMP	dst		|?      |0 1 0|?|0 0 0|?|1 0 1 1| dst				|
DSPJSB	dst		|?      |0 1 0|?|1 0 0|?|1 0 1 1| dst				|
DSPRET	-		|?      |0 1 0|?|1 1 0|?|1 0 1 1|
DSPSKC	-		|?      |0 1 0|?    |0|?|0 0 1 1|
DSPSKP	-		|?      |0 1 0|?    |1|?|0 0 0 0|
DSPDSZ	-		|?      |0 1 0|?|0 1 0|?|1 0 1 1|
DSPEND	-		|?      |0 1 0|?          |1|?  |
DSPLDC	dst		|?	|0 1 1 0| dst		|
DSPTHO	-		|?	|0 1 1 1| ?		|
DSPVEC	V,b,i,e,c,d	|?      |0 1 0|b|i|e|0|c|d|0|1 0|
DSPLBL	L,b,i,e,c,d	|?      |0 1 0|b|i|e|0|c|d|0|0 1|
DSPGRA	G,b,i,e,c,d	|?      |0 1 0|b|i|e|0|c|d|0|0 0|
"""

hp85662a_c_instructions = """
DSPX	-		|?				|
"""

hp85662a_v_instructions = """
DSPMOVE	R		|?	|R|0| X			|?	|1|0| Y			|
DSPLINE	R		|?	|R|0| X			|?	|0|0| Y			|
"""

hp85662a_l_instructions = """
DSPCHR	C		|?		| chr		|
"""

hp85662a_g_instructions = """
DSPG	-		|?				|
"""

class hp85662a_ins(assy.Instree_ins):
	pass

	def assy_dst(self, pj):
		return "#0x%04x" % self['dst']

	def assy_b(self, pj):
		if self['b']:
			return "bex"

	def assy_i(self, pj):
		if self['i']:
			return "brt"

	def assy_e(self, pj):
		if self['e']:
			return "exs"

	def assy_c(self, pj):
		if self['c']:
			return "clx"

	def assy_d(self, pj):
		if self['d']:
			return "dim"

	def assy_V(self, pj):
		self.lang.it = self.lang.itv

	def assy_L(self, pj):
		self.lang.it = self.lang.itl

	def assy_G(self, pj):
		self.lang.it = self.lang.itg

	def assy_C(self, pj):
		x = self['chr']
		t = "0x%02x" % x
		if x >= 0x20 and x < 0x7e:
			t += " '%c'" % x
		nm = {
			17:	"bkon",
			18:	"bkoff",
			145:	"sk16",
			146:	"sk32",
			147:	"sk64",
			0xc8:	"HP-h",
			0xd0:	"HP-p",
			0xd8:	"X-mrk",
			0xd9:	"Y-mrk",
		}
		a = nm.get(x)
		if a != None:
			t += " " + a
		return t

	def assy_R(self, pj):
		t = ""
		if self['R']:
			t += "+%d" % (self['X'])
			t += ",+%d" % (self['Y'])
		else:
			t += "%d" % (self['X'])
			t += ",%d" % (self['Y'])
		return t


class hp85662a(assy.Instree_disass):
	def __init__(self, lang="hp85662a"):
		super(hp85662a, self).__init__(lang, 16, 8, ">")
		self.myleaf = hp85662a_ins

		self.itc = instree.Instree(16, 8)
		self.itc.load_string(hp85662a_instructions)
		self.itc.load_string(hp85662a_c_instructions)

		self.itg = instree.Instree(16, 8)
		self.itg.load_string(hp85662a_instructions)
		self.itg.load_string(hp85662a_g_instructions)

		self.itl = instree.Instree(16, 8)
		self.itl.load_string(hp85662a_instructions)
		self.itl.load_string(hp85662a_l_instructions)

		self.itv = instree.Instree(16, 8)
		self.itv.load_string(hp85662a_instructions)
		self.itv.load_string(hp85662a_v_instructions)

		self.it = self.itc

		self.amask_ = 0xfff

	def set_adr_mask(self, a):
		self.amask = a

	def vectors(self, pj):
		return
