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

# Page numbers referst to:
#	9900 Family Systems Design
#	and Data Book
#	LCC4000 97049-118-NI

# 6-18 / 328
LI	w,i	|0 0 0 0 0 0 1 0 0 0 0|n| w	| iop				|
LIMI	i	|0 0 0 0 0 0 1 1 0 0 0|0 0 0 0 0| iop				|

# 6-19 / 329
LWPI	i	|0 0 0 0 0 0 1 0 1 1 1|0 0 0 0 0| iop				|
MOV	so,do	|1 1 0 0|td | d     |ts | s     |

# 6-20 / 330
MOVb	so,do	|1 1 0 1|td | d     |ts | s     |

# 6-21 / 331
SWPB	so	|0 0 0 0 0 1 1 0 1 1|ts | s     |
STST	w	|0 0 0 0 0 0 1 0 1 1 0|0| w	|

# 6-22 / 332
STWP	?	|0 0 0 0 0 0 1 0 1 0 1|n| w	|

# 6-23 / 333
A	so,do	|1 0 1 0|td | d     |ts | s     |

# 6-24 / 334
Ab	so,do	|1 0 1 1|td | d     |ts | s     |

# 6-25 / 335
AI	w,i	|0 0 0 0 0 0 1 0 0 0 1|n| w	| iop				|
S	so,do	|0 1 1 0|td | d     |ts | s     |

# 6-26 / 336
Sb	so,do	|0 1 1 1|td | d     |ts | s     |

# 6-27 / 337
INC	so	|0 0 0 0 0 1 0 1 1 0|ts | s     |
INCT	so	|0 0 0 0 0 1 0 1 1 1|ts | s     |

# 6-28 / 338
DEC	so	|0 0 0 0 0 1 1 0 0 0|ts | s	|
DECT	so	|0 0 0 0 0 1 1 0 0 1|ts | s	|

# 6-29 / 339
NEG	so	|0 0 0 0 0 1 0 1 0 0|ts | s     |
ABS	so	|0 0 0 0 0 1 1 1 0 1|ts | s     |

# 6-30 / 340
MPY	so,w	|0 0 1 1 1 0| w     |ts | s     |

# 6-31 / 341
DIV	so,w	|0 0 1 1 1 1| w     |ts | s     |

# 6-32 / 342
C	so,do	|1 0 0 0|td | d     |ts | s     |

# 6-33 / 343
Cb	so,do	|1 0 0 1|td | d     |ts | s     |

# 6-34 / 344
CI	w,i	|0 0 0 0 0 0 1 0 1 0 0|n| w	| iop				|
COC	so,w	|0 0 1 0 0 0| w     |ts | s     |

# 6-35 / 345
CZC	so,w	|0 0 1 0 0 1| w     |ts | s     |

# 6-36 / 346
ANDI	w,i	|0 0 0 0 0 0 1 0 0 1 0|n| w	| iop				|

# 6-37 / 347
ORI	w,i	|0 0 0 0 0 0 1 0 0 1 1|n| w	| iop				|

# 6-38 / 348
XOR	so,w	|0 0 1 0 1 0| w     |ts | s     |
INV	so	|0 0 0 0 0 1 0 1 0 1|ts | s     |

# 6-39 / 349
CLR	so	|0 0 0 0 0 1 0 0 1 1|ts | s     |
SETO	so	|0 0 0 0 0 1 1 1 0 0|ts | s     |

# 6-40 / 350
SOC	so,do	|1 1 1 0|td | d     |ts | s     |
SOCb	so,do	|1 1 1 1|td | d     |ts | s     |

# 6-41 / 351
SZC	so,do	|0 1 0 0|td | d     |ts | s     |

# 6-42 / 352
SZCb	so,do	|0 1 0 1|td | d     |ts | s     |

# 6-43 / 353
SRA	sc,w	|0 0 0 0 1 0 0 0| c     | w	|

# 6-44 / 354
SLA	sc,w	|0 0 0 0 1 0 1 0| c     | w	|

# 6-45 / 355
SRL	sc,w	|0 0 0 0 1 0 0 1| c     | w	|
SRC	sc,w	|0 0 0 0 1 0 1 1| c     | w	|

# 6-46 / 356
B	da,>J	|0 0 0 0 0 1 0 0 0 1|1 0|0 0 0 0| da				|
B	so,>J	|0 0 0 0 0 1 0 0 0 1|ts | s     |

# 6-47 / 357
BL	da,>C	|0 0 0 0 0 1 1 0 1 0|1 0|0 0 0 0| da				|
BL	so,>C	|0 0 0 0 0 1 1 0 1 0|ts | s     |

# 6-48 / 358
BLWP	blwp1,blwp2,>C	|0 0 0 0 0 1 0 0 0 0|1 0|0 0 0 0| ptr				|
BLWP	so	|0 0 0 0 0 1 0 0 0 0|ts | s     |

# 6-49 / 259
XOP	?	|0 0 1 0 1 1| d     |ts | s     |

# 6-50 / 360
RTWP	>R	|0 0 0 0 0 0 1 1 1 0 0| n	|
JMP	r,>J	|0 0 0 1 0 0 0 0| disp		|

# 6-51 / 361
X	so	|0 0 0 0 0 1 0 0 1 0|ts | s	|

# 6-52 / 362
JH	r,>JC	|0 0 0 1 1 0 1 1| disp		|
JL	r,>JC	|0 0 0 1 1 0 1 0| disp		|
JHE	r,>JC	|0 0 0 1 0 1 0 0| disp		|
JLE	r,>JC	|0 0 0 1 0 0 1 0| disp		|
JGT	r,>JC	|0 0 0 1 0 1 0 1| disp		|
JLT	r,>JC	|0 0 0 1 0 0 0 1| disp		|
JEQ	r,>JC	|0 0 0 1 0 0 1 1| disp		|
JNE	r,>JC	|0 0 0 1 0 1 1 0| disp		|
JOC	r,>JC	|0 0 0 1 1 0 0 0| disp		|
JNC	r,>JC	|0 0 0 1 0 1 1 1| disp		|
JNO	r,>JC	|0 0 0 1 1 0 0 1| disp		|
JOP	r,>JC	|0 0 0 1 1 1 0 0| disp		|

# 6-53 / 363
SBO	cru	|0 0 0 1 1 1 0 1| cru		|

# 6-54 / 364
SBZ	cru	|0 0 0 1 1 1 1 0| cru		|
TB	cru	|0 0 0 1 1 1 1 1| cru		|

# 6-55 / 365
LDCR	c,so	|0 0 1 1 0 0| c     |ts | s     |

# 6-57 / 367
STCR	c,so	|0 0 1 1 0 1| c     |ts | s     |

# 6-58 / 368
LREX	?	|0 0 0 0 0 0 1 1 1 1 1| n	|
CKOF	?	|0 0 0 0 0 0 1 1 1 1 0| n	|
CKON	?	|0 0 0 0 0 0 1 1 1 0 1| n	|
RSET	?	|0 0 0 0 0 0 1 1 0 1 1| n	|
IDLE	?	|0 0 0 0 0 0 1 1 0 1 0| n	|

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
		if ins.mne[-1] == "b":
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

def arg_blwp1(pj, ins):
	a = ins.im.F_ptr
	data.Pstruct(pj, a, ">HH", ".BLWP\t0x%04x, 0x%04x")
	return assy.Arg_verbatim(pj, "WP=0x%04x" % pj.m.bu16(a))

def arg_blwp2(pj, ins):
	a = ins.im.F_ptr
	ins.dstadr = pj.m.bu16(a+2)
	return assy.Arg_dst(pj, ins.dstadr)

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
		    "w":	arg_w,
		    "b":	arg_b,
		    "c":	arg_c,
		    "so":	arg_so,
		    "do":	arg_do,
		    "da":	arg_da,
		    "sc":	arg_sc,
		    "cru":	arg_cru,
		    "blwp1":	arg_blwp1,
		    "blwp2":	arg_blwp2,
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
