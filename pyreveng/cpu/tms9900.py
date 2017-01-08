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
Disassembler for TI TMS9900 microprocessor
"""


from __future__ import print_function

from pyreveng import assy, data

tms9900_instructions = """
A	b,so,do	|1 0 1|b|td | d     |ts | s     |
C	b,so,do	|1 0 0|b|td | d     |ts | s     |
S	b,so,do	|0 1 1|b|td | d     |ts | s     |
SOC	b,so,do	|1 1 1|b|td | d     |ts | s     |
SZC	b,so,do	|0 1 0|b|td | d     |ts | s     |
MOV	b,so,do	|1 1 0|b|td | d     |ts | s     |

COC	so,w	|0 0 1 0 0 0| w     |ts | s     |
CZC	so,w	|0 0 1 0 0 1| w     |ts | s     |
XOR	so,w	|0 0 1 0 1 0| w     |ts | s     |
MPY	so,w	|0 0 1 1 1 0| w     |ts | s     |
DIV	so,w	|0 0 1 1 1 1| w     |ts | s     |

XOP	?	|0 0 1 0 1 1| d     |ts | s     |

B	da,>J	|0 0 0 0 0 1 0 0 0 1|1 0|0 0 0 0| da				|
B	so,>J	|0 0 0 0 0 1 0 0 0 1|ts | s     |
BL	da,>C	|0 0 0 0 0 1 1 0 1 0|1 0|0 0 0 0| da				|
BL	so,>C	|0 0 0 0 0 1 1 0 1 0|ts | s     |
BLWP	ptr,>C	|0 0 0 0 0 1 0 0 0 0|1 0|0 0 0 0| ptr				|
BLWP	so	|0 0 0 0 0 1 0 0 0 0|ts | s     |

CLR	so	|0 0 0 0 0 1 0 0 1 1|ts | s     |
SETO	so	|0 0 0 0 0 1 1 1 0 0|ts | s     |
INV	so	|0 0 0 0 0 1 0 1 0 1|ts | s     |
NEG	so	|0 0 0 0 0 1 0 1 0 0|ts | s     |
ABS	so	|0 0 0 0 0 1 1 1 0 1|ts | s     |
SWPB	so	|0 0 0 0 0 1 1 0 1 1|ts | s     |

INC	so	|0 0 0 0 0 1 0 1 1 0|ts | s     |
INCT	so	|0 0 0 0 0 1 0 1 1 1|ts | s     |
DEC	so	|0 0 0 0 0 1 1 0 0 0|ts | s	|
DECT	so	|0 0 0 0 0 1 1 0 0 1|ts | s	|
X	so	|0 0 0 0 0 1 0 0 1 0|ts | s	|

LDCR	c,so	|0 0 1 1 0 0| c     |ts | s     |
STCR	c,so	|0 0 1 1 0 1| c     |ts | s     |

SBO	cru	|0 0 0 1 1 1 0 1| cru		|
SBZ	cru	|0 0 0 1 1 1 1 0| cru		|
TB	cru	|0 0 0 1 1 1 1 1| cru		|

JEQ	r,>JC	|0 0 0 1 0 0 1 1| disp		|
JGT	r,>JC	|0 0 0 1 0 1 0 1| disp		|
JH	r,>JC	|0 0 0 1 1 0 1 1| disp		|
JHE	r,>JC	|0 0 0 1 0 1 0 0| disp		|
JL	r,>JC	|0 0 0 1 1 0 1 0| disp		|
JLE	r,>JC	|0 0 0 1 0 0 1 0| disp		|
JLT	r,>JC	|0 0 0 1 0 0 0 1| disp		|
JMP	r,>J	|0 0 0 1 0 0 0 0| disp		|
JNC	r,>JC	|0 0 0 1 0 1 1 1| disp		|
JNE	r,>JC	|0 0 0 1 0 1 1 0| disp		|
JNO	r,>JC	|0 0 0 1 1 0 0 1| disp		|
JOC	r,>JC	|0 0 0 1 1 0 0 0| disp		|
JOP	r,>JC	|0 0 0 1 1 1 0 0| disp		|

SLA	sc,w	|0 0 0 0 1 0 1 0| c     | w	|
SRA	sc,w	|0 0 0 0 1 0 0 0| c     | w	|
SRC	sc,w	|0 0 0 0 1 0 1 1| c     | w	|
SRL	sc,w	|0 0 0 0 1 0 0 1| c     | w	|

AI	w,i	|0 0 0 0 0 0 1 0 0 0 1|n| w	| iop				|
ANDI	w,i	|0 0 0 0 0 0 1 0 0 1 0|n| w	| iop				|
CI	w,i	|0 0 0 0 0 0 1 0 1 0 0|n| w	| iop				|
LI	w,i	|0 0 0 0 0 0 1 0 0 0 0|n| w	| iop				|
ORI	w,i	|0 0 0 0 0 0 1 0 0 1 1|n| w	| iop				|

LWPI	i	|0 0 0 0 0 0 1 0 1 1 1|0 0 0 0 0| iop				|
LIMI	i	|0 0 0 0 0 0 1 1 0 0 0|0 0 0 0 0| iop				|

STST	w	|0 0 0 0 0 0 1 0 1 1 0|0| w	|
STWP	?	|0 0 0 0 0 0 1 0 1 0 1|n| w	|

RTWP	>R	|0 0 0 0 0 0 1 1 1 0 0| n	|

IDLE	?	|0 0 0 0 0 0 1 1 0 1 0| n	|
RSET	?	|0 0 0 0 0 0 1 1 0 1 1| n	|
CKOF	?	|0 0 0 0 0 0 1 1 1 1 0| n	|
CKON	?	|0 0 0 0 0 0 1 1 1 0 1| n	|
LREX	?	|0 0 0 0 0 0 1 1 1 1 1| n	|

"""

def arg_o(pj, ins, to, o):
	if to == 0:
		return "R%d" % o
	if to == 1:
		return "*R%d" % o

	if to == 2:
		v = pj.m.bu16(ins.hi)
		ins.hi += 2
		if o != 0:
			return "R%d+#0x%04x" % (o, v)

		x = pj.find(v)
		if len(x) > 0:
			return assy.Arg_ref(pj, x[0])

		try:
			w = pj.m.bu16(v)
		except:
			return assy.Arg_dst(pj, v, "@")

		# print("XXX", "%04x" % v, "%04x" % w, ins.mne)
		if ins.mne[-1] == "B":
			c = data.Const(pj, v, v + 1)
			c.typ = ".BYTE"
			c.fmt = "0x%02x" % pj.m.rd(v)
		else:
			c = data.Const(pj, v, v + 2)
			c.typ = ".WORD"
			c.fmt = "0x%04x" % w
		return assy.Arg_ref(pj, c)

	if to == 3:
		return "*R%d+" % o

def arg_so(pj, ins):
	return arg_o(pj, ins, ins.im.F_ts, ins.im.F_s)

def arg_do(pj, ins):
	return arg_o(pj, ins, ins.im.F_td, ins.im.F_d)

def arg_b(pj, ins):
	if ins.im.F_b:
		ins.mne += "B"

def arg_da(pj, ins):
	ins.dstadr = ins.im.F_da
	return assy.Arg_dst(pj, ins.dstadr)

def arg_r(pj, ins):
	i = ins.im.F_disp
	if i & 0x80:
		i -= 256
	ins.dstadr = ins.hi + i * 2
	return assy.Arg_dst(pj, ins.dstadr)

def arg_c(pj, ins):
	return assy.Arg_imm(pj, ins.im.F_c)

class arg_ptr(assy.Arg_ref):
	def __init__(self, pj, ins):
		self.val = ins.im.F_ptr
		self.vector = vector(pj, self.val, ins.lang)
		ins.dstadr = self.vector.dstadr
		super(arg_ptr, self).__init__(pj, self.vector)

def arg_i(pj, ins):
	return assy.Arg_imm(pj, ins.im.F_iop, 16)

def arg_w(pj, ins):
	return "R%d" % ins.im.F_w

def arg_cru(pj, ins):
	i = ins.im.F_cru
	if i & 0x80:
		i -= 0x100
	# XXX: This doubling may be model-dependent
	# XXX: Based on 9980/9981
	i *= 2
	return "R12%#+x" % i

def arg_sc(pj, ins):
	if ins.im.F_c == 0:
		return "R0"
	else:
		return "#%d" % ins.im.F_c

class vector(data.Data):
	def __init__(self, pj, adr, cx):
		super(vector, self).__init__(pj, adr, adr + 4)
		self.ws = data.Dataptr(pj, adr + 0x00, adr + 0x02,
		    pj.m.bu16(adr))
		self.ip = cx.codeptr(pj, adr + 0x02)
		self.dstadr = self.ip.dst

	def render(self, pj):
		return self.ws.render(pj) + "; " + self.ip.render(pj)

	def arg_render(self, pj):
		return self.ip.arg_render(pj)

class Tms9900(assy.Instree_disass):
	def __init__(self):
		super(Tms9900, self).__init__("TMS 9900", 16, 8, ">")
		self.it.load_string(tms9900_instructions)
		self.n_interrupt = 16
		self.args.update({
		    "r":	arg_r,
		    "i":	arg_i,
		    "ptr":	arg_ptr,
		    "w":	arg_w,
		    "b":	arg_b,
		    "c":	arg_c,
		    "so":	arg_so,
		    "do":	arg_do,
		    "da":	arg_da,
		    "sc":	arg_sc,
		    "cru":	arg_cru,
		})

	def codeptr(self, pj, adr):
		t = pj.m.bu16(adr)
		c = data.Codeptr(pj, adr, adr + 2, t)
		pj.todo(t, self.disass)
		return c

	def vector(self, pj, adr):
		return vector(pj, adr, self)

	def vectors(self, pj, adr=0x0, xops=1):
		def vect(pj, a, lbl):
			c = vector(pj, a, self)
			pj.set_label(c.dstadr, lbl)
			return c

		vect(pj, adr, "RESET")
		for i in range(1, self.n_interrupt):
			if pj.m.bu16(i * 4) != 0:
				vect(pj, i * 4, "INT%d" % i)
		for i in range(xops):
			vect(pj, 0x40 + i * 4, "XOP%d" % i)

class Tms9981(Tms9900):
	def __init__(self):
		super(Tms9981, self).__init__()
		self.n_interrupt = 5

if __name__ == "__main__":
	h = Tms9900()
	h.it.print()
