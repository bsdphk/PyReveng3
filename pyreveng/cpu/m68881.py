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

"""
MC68881/68882 floating point instructions

Page numbers with '*' reference MC68881/68882 USER's MANUAL (MC68881UM/AD Rev2)

"""

from pyreveng import assy, data, mem
from pyreveng.cpu.m68000 import *

m68881_instructions = '''
#		src,dst		ea	|_ _ _ _|_ _ _v_|_ _v_ _|_v_ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|

# *88/4-30
FBcc		XXX		0	|1 1 1 1| cid |0 1|0| condpred	| oper				|
FBcc		XXX		0	|1 1 1 1| cid |0 1|1| condpred	| oper				| oper2				|

# *96/4-38
FDBcc		XXX		0	|1 1 1 1| cid |0 0 1|0 0 1|count|0 0 0 0 0 0 0 0 0 0| condpred	| disp				|

# *124/4-66
FMOVEFPN	L,ea,XXX	37d	|1 1 1 1| cid |0 0 0| ea	|0 1 1| dfm | src | kfact	|

# *128/4-70
FMOVE		L,ea,XXX	1f7f	|1 1 1 1| cid |0 0 0| ea	|1 0|R| reg |0 0 0|0 0 0 0 0 0 0|

# *130/4-72
FMOVECR		XXX		0	|1 1 1 1| cid |0 0 0|0 0 0 0 0 0|0|1|0|1 1 1| dst | rom         |

# *132/4-74
# 387/5-85
FMOVEM.X	L,ea,XXX	0f6c	|1 1 1 1| cid |0 0 0| ea	|1 1|0|mod|0 0 0| rlist		|
FMOVEM.X	L,ea,XXX	0374	|1 1 1 1| cid |0 0 0| ea	|1 1|1|mod|0 0 0| rlist		|

# *136/4-78
FMOVEM		L,ea		1f7f	|1 1 1 1| cid |0 0 0| ea	|1 0|D|rl |0 0 0 0 0 0 0 0 0 0 0|

# *143/4-85
FNOP		-		0	|1 1 1 1| cid |0 1 0|0 0 0 0 0 0|0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0|

# *146/4-88
FRESTORE	L,ea		76c	|1 1 1 1| cid |1 0 1| ea        |

# *148/4-90
FSAVE		L,ea		374	|1 1 1 1| cid |1 0 0| ea        |

# *154/4-96
# 412/5-110
FScc		B,ea		37d	|1 1 1 1| cid |0 0 1| ea	|0 0 0 0 0 0 0 0 0 0| condpred	|

# *177/4-119
FTRAPcc		XXX		0	|1 1 1 1| cid |0 0 1 1 1 1|0 1 0|0 0 0 0 0 0 0 0 0 0| condpred	| oper				|
FTRAPcc		XXX		0	|1 1 1 1| cid |0 0 1 1 1 1|0 1 1|0 0 0 0 0 0 0 0 0 0| condpred	| oper				| oper2				|
FTRAPcc		XXX		0	|1 1 1 1| cid |0 0 1 1 1 1|1 0 0|0 0 0 0 0 0 0 0 0 0| condpred	|

#############
Fops		X,fop,Fx,Fy	0	|1 1 1 1| cid |0 0 0|0 0 0 0 0 0|0|0|0| Fx  | Fy  | fop		|
Fops		fop,fmt,ea,Fy	1f7d	|1 1 1 1| cid |0 0 0| ea	|0|1|0| fmt | Fy  | fop		|

'''

FOPS = {
	# NB: M68000PRM.pdf suffers badly from copy&paste with many ins having 0x0c
	0x00:	"FMOVE",
	0x01:	"FINT",
	0x02:	"FSINH",
	0x03:	"FINTRZ",
	0x04:	"FSQRT",
	# 0x05
	0x06:	"FLOGNP1",
	# 0x07
	0x08:	"FETOXM1",
	0x09:	"FTANH",
	0x0a:	"FATAN",
	0x0c:	"FASIN",
	0x0d:	"FATANH",
	0x0e:	"FSIN",
	0x0f:	"FTAN",
	0x10:	"FETOX",
	0x11:	"FTWOTOX",
	0x12:	"FTENTOX",
	# 0x13
	0x14:	"FLOGN",
	0x15:	"FLOG10",
	0x16:	"FLOG2",
	# 0x17
	0x18:	"FABS",
	0x19:	"FCOSH",
	0x1a:	"FNEG",
	# 0x1b
	0x1c:	"FACOS",
	0x1d:	"FCOS",
	0x1e:	"FGETEXP",
	0x1f:	"FGETMAN",
	0x20:	"FDIV",
	0x21:	"FMOD",
	0x22:	"FADD",
	0x23:	"FMUL",
	0x24:	"FSGLDIV",
	0x25:	"FREM",
	0x26:	"FSCALE",
	0x27:	"FSGLMUL",
	0x28:	"FSUB",
	# 0x29
	# 0x2a
	# 0x2b
	# 0x2c
	0x2d:	"FMOD",
	# 0x2e
	# 0x2f
	# 0x30-31 XXX FSINCOS
	0x38:	"FCMP",
	0x3a:	"FTST",

	#0x58:	"FSABS",	# M68040
	#0x5c:	"FDABS",	# M68040

	#0x60:	"FSDIV",	# M68040
	#0x62:	"FSADD",	# M68040
	#0x64:	"FDDIV",	# M68040
}

class m68881_ins(m68000_ins):
	def __init__(self, pj, lim, lang):
		super().__init__(pj, lim, lang)
		if self['cid'] != 1:
			raise assy.Invalid("FP cid != 1")

	def assy_fop(self, pj):
		op = FOPS.get(self['fop'])
		if op is not None:
			self.mne = op
		self.sz = 4
		self.isz = "i32"
		self.imsk = 0xffffffff

	def assy_Fx(self, pj):
		return "F%d" % self['Fx']

	def assy_Fy(self, pj):
		return "F%d" % self['Fy']

	def assy_X(self, pk):
		self.mne += ".X"

	def assy_fmt(self, pk):
		self.mne += "." + "LSXPWDB?"[self['fmt']]

def m68881(cpu):
	cpu.it.load_string(m68881_instructions, m68881_ins)
