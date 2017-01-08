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
Disassembler for Intel mcs-48 microprocessor family
"""

from __future__ import print_function

from pyreveng import assy

mcs48_instructions = """
# 4-8
ADD	A,r		|0 1 1 0|1|  r  |
ADD	A,@r		|0 1 1 0|0 0 0|r|
ADD	A,im		|0 0 0 0|0 0 1 1| im		|
ADDC	A,r		|0 1 1 1|1|  r	|

# 4-9
ADDC	A,@r		|0 1 1 1|0 0 0|r|
ADDC	A,im		|0 0 0 1|0 0 1 1| im		|
ANL	A,r		|0 1 0 1|1|  r	|
ANL	A,@r		|0 1 0 1|0 0 0|r|

# 4-10
ANL	A,im		|0 1 0 1|0 0 1 1| im		|
ANL	BUS,im		|1 0 0 1|1 0 0 0| im		|
ANL	p,im		|1 0 0 1|1 0| p | im		|
ANLD	p,A		|1 0 0 1|1 1| p |

# 4-11
CALL	adr,>C		| ahi |1|0 1 0 0| alo		|

# 4-12
CLA	A		|0 0 1 0|0 1 1 1|
CLR	C		|1 0 0 1|0 1 1 1|
CLR	F1		|1 0 1 0|0 1 0 1|
CLR	F0		|1 0 0 0|0 1 0 1|
CPL	A		|0 0 1 1|0 1 1 1|
CPL	C		|1 0 1 0|0 1 1 1|

# 4-13
CPL	F0		|1 0 0 1|0 1 0 1|
CPL	F1		|1 0 1 1|0 1 0 1|
DA	A		|0 1 0 1|0 1 1 1|
DEC	A		|0 0 0 0|0 1 1 1|

# 4-14
DEC	r		|1 1 0 0|1|  r	|
DIS	I		|0 0 0 1|0 1 0 1|
DIS	TCNTI		|0 0 1 1|0 1 0 1|
DJNZ	r,a8		|1 1 1 0|1|  r	| a8		|

# 4-15
EN	I		|0 0 0 0|0 1 0 1|
EN	TCNTI		|0 0 1 0|0 1 0 1|
ENT0	CLK		|0 1 1 1|0 1 0 1|
INS	A,p		|0 0 0 0|1 0| p |

# 4-16
IN	A		|0 0 0 1|0 1 1 1|
INC	r		|0 0 0 1|1|  r	|
INC	@r		|0 0 0 1|0 0 0|r|

# 4-17
#IN	A,P0		|0 0 0 0|1 0 0 0|
IN	A,BUS		|0 0 0 0|1 0 0 0|
JB	b,a8,>JC	|  b  |1|0 0 1 0| a8		|
JC	a8,>JC		|1 1 1 1|0 1 1 0| a8		|
JF0	a8,>JC		|1 0 1 1|0 1 1 0| a8		|

# 4-18
JF1	a8,>JC		|0 1 1 1|0 1 1 0| a8		|
JMP	adr,>J		| ahi |0|0 1 0 0| alo		|
JMPP	@A,>J		|1 0 1 1|0 0 1 1|
JNC	a8,>JC		|1 1 1 0|0 1 1 0| a8		|

# 4-19
JNI	a8,>JC		|1 0 0 0|0 1 1 0| a8		|
JNT0	a8,>JC		|0 0 1 0|0 1 1 0| a8		|
JNT1	a8,>JC		|0 1 0 0|0 1 1 0| a8		|
JNZ	a8,>JC		|1 0 0 1|0 1 1 0| a8		|

# 4-20
JTF	a8,>JC		|0 0 0 1|0 1 1 0| a8		|
JT0	a8,>JC		|0 0 1 1|0 1 1 0| a8		|
JT1	a8,>JC		|0 1 0 1|0 1 1 0| a8		|
JZ	a8,>JC		|1 1 0 0|0 1 1 0| a8		|

# 4-21
MOV	A,im		|0 0 1 0|0 0 1 1| im		|
MOV	A,PSW		|1 1 0 0|0 1 1 1|
MOV	A,r		|1 1 1 1|1|  r	|
MOV	A,@r		|1 1 1 1|0 0 0|r|

# 4-22
MOV	A,T		|0 1 0 0|0 0 1 0|
MOV	PSW,A		|1 1 0 1|0 1 1 1|
MOV	r,A		|1 0 1 0|1|  r	|
MOV	r,im		|1 0 1 1|1|  r	| im		|

# 4-23
MOV	@r,A		|1 0 1 0|0 0 0|r|
MOV	@r,im		|1 0 1 1|0 0 0|r| im		|
MOV	T,A		|0 1 1 0|0 0 1 0|

# 4-24
MOVD	A,p		|0 0 0 0|1 1| p |
MOVD	p,A		|0 0 1 1|1 1| p |
MOVP	A,@A		|1 0 1 0|0 0 1 1|

# 4-25
MOVP3	A,@A		|1 1 1 0|0 0 1 1|
MOVX	A,@r		|1 0 0 0|0 0 0|r|

# 4-26
MOVX	@r,A		|1 0 0 1|0 0 0|r|
NOP	-		|0 0 0 0|0 0 0 0|
ORL	A,r		|0 1 0 0|1|  r	|
ORL	A,@r		|0 1 0 0|0 0 0|r|
ORL	A,im		|0 1 0 0|0 0 1 1| im		|

# 4-27
ORL	BUS,im		|1 0 0 0|1 0 0 0| im		|
ORL	p,im		|1 0 0 0|1 0| p | im		|
ORLD	p,A		|1 0 0 0|1 1| p |
OUTL	P0,A		|1 0 0 1|0 0 0 0|
OUTL	BUS,A		|0 0 0 0|0 0 1 0|

# 4-28
OUTL	p,A		|0 0 1 1|1 0| p |
RET	>R		|1 0 0 0|0 0 1 1|
RETR	>R		|1 0 0 1|0 0 1 1|
RL	A		|1 1 1 0|0 1 1 1|

# 4-29
RLC	A		|1 1 1 1|0 1 1 1|
RR	A		|0 1 1 1|0 1 1 1|
RRC	A		|0 1 1 0|0 1 1 1|

# 4-30
SEL	MBO		|1 1 1 0|0 1 0 1|
SEL	MB1		|1 1 1 1|0 1 0 1|
SEL	RB0		|1 1 0 0|0 1 0 1|
SEL	RB1		|1 1 0 1|0 1 0 1|

# 4-31
STOP	TCNT		|0 1 1 0|0 1 0 1|

# 4-32
STRT	CNT		|0 1 0 0|0 1 0 1|
STRT	T		|0 1 0 1|0 1 0 1|
SWAP	A		|0 1 0 0|0 1 1 1|

# 4-33
XCH	A,r		|0 0 1 0|1|  r	|
XCH	A,@r		|0 0 1 0|0 0 0|r|
XCHD	A,@r		|0 0 1 1|0 0 0|r|

# 4-34
XRL	A,r		|1 1 0 1|1|  r	|
XRL	A,@r		|1 1 0 1|0 0 0|r|
XRL	A,im		|1 1 0 1|0 0 1 1| im		|


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

def arg_p(pj, ins):
	return "P%d" % ins.im.F_p

def arg_ar(pj, ins):
	return "@R%d" % ins.im.F_r

def arg_r(pj, ins):
	return "R%d" % ins.im.F_r

def arg_im(pj, ins):
	return "#0x%02x" % ins.im.F_im

class mcs48(assy.Instree_disass):
	def __init__(self, lang="mcs48"):
		super(mcs48, self).__init__(lang, 8)
		self.it.load_string(mcs48_instructions)

		self.args.update( {
			"TCNTI":	"TCNTI",
			"BUS":		"BUS",
			"T":		"T",
			"A":		"A",
			"@A":		"@A",
			"I":		"I",
			"F0":		"F0",
			"F1":		"F1",
			"adr":		arg_adr,
			"a8":		arg_a8,
			"r":		arg_r,
			"@r":		arg_ar,
			"p":		arg_p,
			"im":		arg_im,
		})
		self.amask_ = 0xffff

	def set_adr_mask(self, a):
		self.amask = a

	def vectors(self, pj):
		for a, l in (
			(0x000, "RESET"),
			(0x003, "INT"),
			(0x007, "TINT"),
		):
			pj.todo(a, self.disass)
			pj.set_label(a, l)


class i8748(mcs48):
	'''
	i8748 chip
	'''
