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

import os
import sys

from pyreveng import instree, assy

hp1345a_instructions = """
_SET	i,l,s,>R	|0 1 1| i | ? | l |0|?| s | ?	|
_LOADX	c,>R		|0 0 0 0|p| c			|
_PLOTY	c,p,>R		|0 0 0 1|p| c			|
_DX	c,>R		|0 0 1 0|p| c			|
_GRAPH	c,p,>R		|0 0 1 1|p| c			|
_CHR	a,t,>R		|0 1 0| s | r |e| t		|
"""

class arg_adr(assy.Arg_dst):
	def __init__(self, pj, ins):
		ins.dstadr = (ins.im.F_ahi << 8) | ins.im.F_alo
		self.dstadr = ins.dstadr
		super(arg_adr, self).__init__(pj, ins.dstadr)

class arg_a8(assy.Arg_dst):
	def __init__(self, pj, ins):
		ins.dstadr = (ins.lo & ~0x0ff) | ins.im.F_a8
		self.dstadr = ins.dstadr
		super(arg_a8, self).__init__(pj, ins.dstadr)

def arg_c(pj, ins):
	return "#%d" % ins.im.F_c

def arg_t(pj, ins):
	a = ins.im.F_t
	if a < 32 or a > 126:
		return "#0x%02x" % a
	else:
		return "'%c'" % a

def arg_a(pj, ins):
	if not ins.im.F_e:
		return "-"
	s = ["1x", "1.5x", "2x", "2.5x"][ins.im.F_s]
	s += "@%d" % (ins.im.F_r * 90)
	return s

def arg_p(pj, ins):
	return ["OFF", "ON"][ins.im.F_p]

def arg_im(pj, ins):
	return "#0x%02x" % ins.im.F_im

def arg_i(pj, ins):
	return ("Blank", "Dim", "Half", "Full")[ins.im.F_i]

def arg_l(pj, ins):
	return ("Solid", "Ends", "Long", "Short")[ins.im.F_l]

def arg_s(pj, ins):
	return ("slow", "low", "med", "high")[ins.im.F_s]


class hp1345a(assy.Instree_disass):
	def __init__(self, lang = "hp1345a"):
		super(hp1345a, self).__init__(lang, 16, 8, ">")
		self.it.load_string(hp1345a_instructions)

		self.args.update( {
			"c":		arg_c,
			"t":		arg_t,
			"a":		arg_a,
			"p":		arg_p,
			"i":		arg_i,
			"l":		arg_l,
			"s":		arg_s,
		})
		self.amask_ = 0xfff

	def set_adr_mask(self, a):
		self.amask = a

	def vectors(self, pj):
		return
