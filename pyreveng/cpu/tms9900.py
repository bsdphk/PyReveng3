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
#
# XXX: Does "NEG *R2+" increment once or twice ?

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
LI	w,i	|0 0 0 0 0 0 1 0 0 0 0|n| w	| iop				| {
	R = i16 IMM
}
LIMI	i	|0 0 0 0 0 0 1 1 0 0 0|0 0 0 0 0| iop				|

# 6-19 / 329
LWPI	i	|0 0 0 0 0 0 1 0 1 1 1|0 0 0 0 0| iop				| {
	%WP = i16 IMM
}
MOV	so,do	|1 1 0 0|td | d     |ts | s     | {
	LD RS
}

# 6-20 / 330
MOVb	so,do	|1 1 0 1|td | d     |ts | s     | {
	LD RS
}

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
NEG	so	|0 0 0 0 0 1 0 1 0 0|ts | s     | {
	%0 = sub i16 0x0000 , RS
	%status.ov = icmp eq i16 RS , 0x8000
	XXX %status.c
	LS %0
	FLAGS3 %0
}
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
ANDI	w,i	|0 0 0 0 0 0 1 0 0 1 0|n| w	| iop				| {
	R = and i16 R , IMM
	FLAGS3 R
}

# 6-37 / 347
ORI	w,i	|0 0 0 0 0 0 1 0 0 1 1|n| w	| iop				| {
	R = or i16 R , IMM
	FLAGS3 R
}

# 6-38 / 348
XOR	so,w	|0 0 1 0 1 0| w     |ts | s     | {
	R = xor i16 R , RS
	FLAGS3 R
}
INV	so	|0 0 0 0 0 1 0 1 0 1|ts | s     | {
	%0 = xor i16 RS , 0xffff
	LS %0
	FLAGS3 %0
}

# 6-39 / 349
CLR	so	|0 0 0 0 0 1 0 0 1 1|ts | s     | {
	LS 0x0000
}
SETO	so	|0 0 0 0 0 1 1 1 0 0|ts | s     | {
	LS 0xffff
}

# 6-40 / 350
SOC	so,do	|1 1 1 0|td | d     |ts | s     | {
	%0 = or i16 RS , RD
	LD %0
	FLAGS3 %0
}
SOCb	so,do	|1 1 1 1|td | d     |ts | s     | {
	%0 = or i8 RS , RD
	LD %0
	FLAGS3 %0
}

# 6-41 / 351
SZC	so,do	|0 1 0 0|td | d     |ts | s     | {
	%0 = xor i16 RS , 0xffff
	%1 = and i16 RD , %0
	LD %1
	FLAGS3 %1
}

# 6-42 / 352
SZCb	so,do	|0 1 0 1|td | d     |ts | s     | {
	%0 = xor i8 RS , 0xffff
	%1 = and i8 RD , %0
	LD %1
	FLAGS3 %1
}

# 6-43 / 353
SRA	sc,w	|0 0 0 0 1 0 0 0| c     | w	|

# 6-44 / 354
SLA	sc,w	|0 0 0 0 1 0 1 0| c     | w	|

# 6-45 / 355
SRL	sc,w	|0 0 0 0 1 0 0 1|0 0 0 0| w	| 
SRL	sc,w	|0 0 0 0 1 0 0 1| c     | w	| {
	%0 = srl i16 R , SCNT1
	%status.c = trunc i16 %0 to i1
	R = srl i16 %0 , 1
	FLAGS3 R
}
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
JMP	r,>J	|0 0 0 1 0 0 0 0| disp		| {
	br BRYES
}

# 6-51 / 361
X	so	|0 0 0 0 0 1 0 0 1 0|ts | s	|

# 6-52 / 362
JH	r,>JC	|0 0 0 1 1 0 1 1| disp		| {
	%0 = xor i1 %status.eq , 0x1
	%1 = and i1 %0 , %status.lgt
	br i1 %1 , BRYES , BRNO
}
JL	r,>JC	|0 0 0 1 1 0 1 0| disp		| {
	%0 = or i1 %status.lgt , %status.eq
	br i1 %0 , BRNO , BRYES
}
JHE	r,>JC	|0 0 0 1 0 1 0 0| disp		| {
	%0 = and i1 %status.lgt , %status.eq
	br i1 %0 , BRYES , BRNO
}
JLE	r,>JC	|0 0 0 1 0 0 1 0| disp		| {
	%0 = xor i1 %status.lgt , 0x1
	%1 = and i1 %0 , %status.eq
	br i1 %1 , BRYES , BRNO
}
JGT	r,>JC	|0 0 0 1 0 1 0 1| disp		| {
	br i1 %status.agt , BRYES , BRNO
}
JLT	r,>JC	|0 0 0 1 0 0 0 1| disp		| {
	%0 = or i1 %status.agt , %status.eq
	br i1 %0 , BRNO , BRYES
}
JEQ	r,>JC	|0 0 0 1 0 0 1 1| disp		| {
	br i1 %status.eq , BRYES , BRNO
}
JNE	r,>JC	|0 0 0 1 0 1 1 0| disp		| {
	br i1 %status.eq , BRNO , BRYES
}
JOC	r,>JC	|0 0 0 1 1 0 0 0| disp		| {
	br i1 %status.c , BRYES , BRNO
}
JNC	r,>JC	|0 0 0 1 0 1 1 1| disp		| {
	br i1 %status.c , BRNO , BRYES
}
JNO	r,>JC	|0 0 0 1 1 0 0 1| disp		| {
	br i1 %status.ov , BRNO , BRYES
}
JOP	r,>JC	|0 0 0 1 1 1 0 0| disp		| {
	br i1 %status.op , BRYES , BRNO
}

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

def arg_o(pj, ins, to, o, nm):
	if to == 0:
		return "R%d" % o
	if to == 1:
		return "*R%d" % o

	if to == 2:
		v = pj.m.bu16(ins.hi)
		ins.hi += 2
		ins[nm] = v
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
	return arg_o(pj, ins, ins['ts'], ins['s'], 'Gs')

def arg_do(pj, ins):
	return arg_o(pj, ins, ins['td'], ins['d'], 'Gd')

def arg_b(pj, ins):
	if ins['b']:
		ins.mne += "B"

def arg_blwp1(pj, ins):
	a = ins['ptr']
	data.Pstruct(pj, a, ">HH", ".BLWP\t0x%04x, 0x%04x")
	return assy.Arg_verbatim(pj, "WP=0x%04x" % pj.m.bu16(a))

def arg_blwp2(pj, ins):
	a = ins['ptr']
	ins.dstadr = pj.m.bu16(a+2)
	return assy.Arg_dst(pj, ins.dstadr)

def arg_da(pj, ins):
	ins.dstadr = ins['da']
	return assy.Arg_dst(pj, ins.dstadr)

def arg_r(pj, ins):
	i = ins['disp']
	if i & 0x80:
		i -= 256
	ins.dstadr = ins.hi + i * 2
	return assy.Arg_dst(pj, ins.dstadr)

def arg_c(pj, ins):
	return assy.Arg_imm(pj, ins['c'])

def arg_i(pj, ins):
	return assy.Arg_imm(pj, ins['iop'], 16)

def arg_w(pj, ins):
	return "R%d" % ins['w']

def arg_cru(pj, ins):
	i = ins['cru']
	if i & 0x80:
		i -= 0x100
	# XXX: This doubling may be model-dependent
	# XXX: Based on 9980/9981
	i *= 2
	return "R12%#+x" % i

def arg_sc(pj, ins):
	if ins['c'] == 0:
		return "R0"
	else:
		return "#%d" % ins['c']

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


class Tms9900assy(assy.Instree_assy):
	pass

	def sz(self):
		if self.mne[-1] == 'b':
			return 8
		return 16

	def macro_R(self):
		return "%%R%d" % self['w']

	def macro_IMM(self):
		return "0x%04x" % self['iop']

	def arg_ro(self, t, s, nm):
		sz = self.sz()
		print(self, self.mne, self.oper, ['// YYY RO %d ' % sz + "T %x S %x  " % (t, s) ])
		tsz = "i%d" % sz
		r = "%%R%d" % s
		if t == 0 and sz == 16:
			return r
		
		if t == 0 and sz == 8:
			self.add_il([
				[ "%0", '=', 'shr', "i16", r, ',', '8' ],
				[ "%1", '=', 'trunc', "i16", "%0", 'to', 'i8' ],
			])
			return "%-1"
		
		if t == 1:
			self.add_il([
				[ "%0", '=', 'inttoptr', 'i16', r, 'to', tsz + "*"],
				[ "%1", '=', 'load', tsz, ',', tsz + "*", "%0" ],
			])
			return "%-1"

		if t == 2 and s == 0:
			self.add_il([
				[ "%0", '=', 'load', tsz, ',', tsz + "*", "0x%04x" % self[nm]],
			])
			return "%-1"

		if t == 2:
			self.add_il([
				[ "%0", '=', 'add', 'i16', r, ',', "0x%04x" % self[nm]],
				[ "%1", '=', 'inttoptr', "i16", "%0", 'to', tsz + "*"],
				[ "%2", '=', 'load', tsz, ',', tsz + "*", "%1"],
			])
			return "%-1"

		if t == 3:
			self.add_il([
				[ "%0", '=', 'inttoptr', "i16", r, 'to', tsz + "*"],
				[ r, '=', 'add', 'i16', r, ',', '0x%04x' % (sz / 8)],
				[ "%1", '=', 'load', tsz, ',', tsz + "*", "%0"],
			])
			return "%-1"
			
		self.add_il(['// YYY RO %d ' % sz + "T %x S %x  " % (t, s) ])
		return "ZZZ"

	def arg_lo(self, t, s, args, nm):
		sz = self.sz()
		print(self, ['// YYY LO %d ' % sz + "T %x S %x  " % (t, s) + " ".join(args) ])
		tsz = "i%d" % sz
		r = "%%R%d" % s
		if t == 0 and sz == 16:
			self.add_il([ [ r, "=", tsz, args[0]], ])
			return
		if t == 0 and sz == 8:
			self.add_il([
				[ "%0", "=", "zext", tsz, args[0], "to", "i16" ],
				[ "%1", "=", "shl", "i16", "%0", ",", "8" ],
				[ r, "=", "and", "i16", r, ",", "0x00ff" ],
				[ r, "=", "or", "i16", r, ",", "%1" ],
			])
			return
		if t == 1:
			self.add_il([
				[ "%0", '=', 'inttoptr', 'i16', r, 'to', tsz + "*"],
				[ 'store', tsz, args[0], ',', tsz + "*", "%0" ],
			])
			return

		if t == 2 and s == 0:
			self.add_il([
				[ 'store', tsz, args[0], ',', tsz + "*", "0x%04x" % self[nm]],
			])
			return
		if t == 2:
			self.add_il([
				[ "%0", '=', 'add', 'i16', r, ',', "0x%04x" % self[nm]],
				[ "%1", '=', 'inttoptr', "i16", "%0", 'to', tsz + "*"],
				[ 'store', tsz, args[0], ',', tsz + "*", "%1"],
			])
			return
		if t == 3:
			self.add_il([
				[ "%0", '=', 'inttoptr', "i16", r, 'to', tsz + "*"],
				[ r, '=', 'add', 'i16', r, ',', '0x%04x' % (sz / 8)],
				[ 'store', tsz, args[0], ',', tsz + "*", "%0"],
			])
			return
		

		self.add_il(['// YYY LO %d ' % sz + "T %x S %x  " % (t, s) + " ".join(args) ])
		return

	def func_LS(self, args):
		self.arg_lo(self['ts'], self['s'], args, 'Gs')

	def macro_RS(self):
		return self.arg_ro(self['ts'], self['s'], 'Gs')

	def func_LD(self, args):
		self.arg_lo(self['td'], self['d'], args, 'Gd')

	def macro_RD(self):
		return self.arg_ro(self['td'], self['d'], 'Gd')

	def macro_SCNT1(self):
		return "0x%x" % (self['c'] - 1)

	def macro_SCNT(self):
		return "0x%x" % self['c']

	def macro_BRYES(self):
		return "label 0x%04x" % self.flow_out[0].to

	def macro_BRNO(self):
		return "label 0x%04x" % self.flow_out[1].to


	def func_FLAGS3(self, args):
		self.add_il([
			["%status.eq",  "=", "pyreveng.tms9900.seteq",  "i1", "(", "i%d" % self.sz(), args[0], ')'],
			["%status.lgt", "=", "pyreveng.tms9900.setlgt", "i1", "(", "i%d" % self.sz(), args[0], ')'],
			["%status.agt", "=", "pyreveng.tms9900.setagt", "i1", "(", "i%d" % self.sz(), args[0], ')'],
		])

class Tms9900(assy.Instree_disass):
	def __init__(self):
		super(Tms9900, self).__init__("TMS 9900", 16, 8, ">")
		self.it.load_string(tms9900_instructions)
		self.n_interrupt = 16
		self.myleaf = Tms9900assy
		self.il = True
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
