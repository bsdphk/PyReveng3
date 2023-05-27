#!/usr/bin/env python
#
# Copyright (c) 2023 Poul-Henning Kamp <phk@phk.freebsd.dk>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#notice, this list of conditions and the following disclaimer in the
#documentation and/or other materials provided with the distribution.
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

'''
   Christian Rovsing CR80
   ======================
'''

from pyreveng import instree, assy

#
# From RCSL 42-i-1008 "RC3803 CPU Programmer's Reference Manual
#
cr80_mod12345_instructions = '''
# HB: 9-15
MODC	C8		| c8		|1|p|1 0|0 1 0 0|
# HB: 9-16
MOD4	C8		| c8		|1|p|1 0|0 1 0 1|
MOD8	C8		| c8		|0 1 0 1|0 1 1 0|
# HB: 9-17
MOD	B6_X2		|x2 | b6	|0 1 0 1|0 1 0|n|
MOD	B8		| b8		|p|0 0 1|0 1 0 0|
MOD	P8		| p8		|p|0 0 1|0 1 0 1|
# HB: 9-19
MOVC	C8		| c8		|0|p|0 0|1| r3	|
MOVC	C4		|0| x3	| c4	|0|p|0 1|0 0 0 0|
# HB: 9-20
MOV	B8,R3			| b8		|0 1 1 0|1| r3	|
MOV	R3,B8			| b8		|0 1 1 1|0| r3	|
MOV	R3,R3			|0| r3	|0| r3	|1 0 1 1|1 0 1 1|
MOV	R3,B0_X3		|1| r3	|0| x3	|1 0 1 1|1 0 1 1|
MOV	X3,R3			|0| x3	|0| r3	|1 1 1 1|1 0 1 1|
MOV	X3,B0_X3		|1| x3	|0| x3b	|1 1 1 1|1 0 1 1|
MOV	B6_X2,R3		|x2 | b6	|0 0 0 1|1| r3	|
MOV	R3,B6.X2		|x2 | b6	|1 0 0 0|0| r3	|
MOV	P8,R3			| p8		|1 0 0 1|1| r3	|
# HB: 9-21
MOVB	BB6_X2,R2		|x2 | b6	|0 1 1 1|1 0|r2	|
MOVB	R2,BB6_X2		|x2 | b6	|1 0 0 1|0 0|r2	|
# HB: 9-22
MOVL	B6_X2,R2		|x2 | b6	|0 1 1 0|0 0|r2	|
MOVL	R2,B6_X2		|x2 | b6	|1 1 0 1|0 0|r2	|
# HB: 9-23
MVP	P6_X2,R2		|x2 | p6	|0 0 1 0|0 0|r2 |
# HB: 9-24
MOVM	X3,X3b			|0| x3	|0| x3b	|1 1 1 0|1 0 0 1|
# HB: 9-25
PUT	R3,X3			|1| r3	|0| x3	|1 1 1 0|1 0 0 1|
PUT	X3,X3			|1| x3	|1| x3b	|1 1 1 0|1 0 0 0|
# HB: 9-26
XCH	R3,RBX3			|0| r3	| rbx3 	|1 1 1 0|1 1 1 0|
XCH	X3,RBX3			|1| x3	| rbx3	|1 1 1 0|1 1 1 1|
# HB: 9-27
STC	C4			|1 1 1 0| c4	|1 0 1 1|1 1 1 0|
STC	R3,B0_X3		|0| r3	|0| x3	|1 0 1 1|1 0 0 1|
STC	X3,B0_X3		|0| x3	|0| x3	|1 1 1 1|1 0 0 1|
# HB: 9-28
UNS	C4			|1 0 1 0| c4	|1 0 1 1|1 1 1 0|
UNS	R3,B0_X3		|0| r3	|1| x3	|1 0 1 1|1 0 0 1|
UNS	X3,B0_X3		|0| x3	|1| x3b	|1 1 1 1|1 0 0 1|
# HB: 9-30 XXX L10 ?
JMP	L10			| l10		|p|1 0 1|1 0|l2 |
JMP	L8			| l8		|p|1 0 1|1 1 0 0|
JMP	S2,L8			| l8		|p|1 0 1|1 1| s2|
# HB: 9-31
JMP	P6_X2			|x2 | p6	|1 0 1 1|1 1 1 1|
# HB: 9-32
JMPI	B6_X2			|x2 | b6	|0 0 0 1|0 0 1 0|
JMPI	B8			| b8		|1 1 1 0|0 1 1 1|
JMPI	P8			| p8		|1 1 1 1|1 1 0 0|
JMPI	S2,P8			| p8		|1 1 1 1|1 1| s2|
# HB: 9-33
JON	R3,L4			|1| r3	| l4	|1|p|1 1|0 0 0 0|
JON	X3,L4			|1| x3	| l4	|1|p|1 1|0 0 0 1|
JOZ	R3,L4			|1| r3	| l4	|1|p|1 1|0 0 1 0|
JOZ	X3,L4			|1| x3	| l4	|1|p|1 1|0 0 1 1|
# HB: 9-34
JVN	L4			|p|0 1 1| l4	|1 0 1 1|1 1 1 0|
# HB: 9-35
SOB	R3,LN8			| ln8		|1 1 0 0|0| r3	|
# HB: 9-37
ADDC	C8,R3			| c8		|1 1 0 0|1| r3	|
ADDC	CN8,R3			| cn8		|1 0 1 0|1| r3	|
# HB: 9-39
ADD	RX3,RBX3		| rx3	| rbx3	|1 0 0 0|1 0 1 0|
ADD	B6_X2,R3		|x2 | b6	|0 0 1 1|0| r3	|
ADD	R3,B6_X2		|x2 | b6	|0 0 0 0|1| r3	|
ADDU	RX3,RBX3		| rx3	| rbx3	|1 1 0 1|0 1 0 0|
# HB: 9-41
SUB	RX3,RBX3		| rx3	| rbx3	|1 0 0 0|1 0 1 1|
SUBU	RX3,RBX3		| rx3	| rbx3	|1 1 0 1|0 1 0 1|
# HB: 9-42
MUL	RX3,B0_X3		| rx3	|1| x3	|1 1 1 0|1 0 1 0|
# HB: 9-44
DIV	RX3,R3			| rx3	|0| r3b	|1 1 1 0|1 0 1 1|
# HB: 9-46
AND	RX3,RBX3		| rx3	| rbx3	|1 0 0 0|1 1 0 0|
IOR	RX3,RBX3		| rx3	| rbx3	|1 0 0 0|1 1 0 1|
XOR	RX3,R3			| rx3	|0| r3	|1 1 1 0|1 0 0 0|
# HB: 9-47
CLR	B6_X2			|x2 | b6	|0 0 1 0|0 1 1 1|
DEC	B6_X2			|x2 | b6	|0 0 0 1|0 0 1 1|
INC	B6_X2			|x2 | b6	|0 0 0 1|0 1 1 0|
INV	RBX3			|1 0 0 1| rbx3	|1 0 1 1|1 1 0 0|
NEG	RBX3			|1 1 1 1| rbx3	|1 0 1 1|1 1 0 0|
SWP	RBX3			|0 1 1 0| rbx3	|1 0 1 1|1 1 0 0|
# HB: 9-48
DECD	R3,R3			|0| r3	|1| r3	|1 0 0 0|1 1 1 0|
DECD	X3,B0_X3		|1| x3	|1| x3b	|1 0 0 0|1 1 1 1|
INCD	R3,R3			|0| r3	|0| r3	|1 0 0 0|1 1 1 0|
INCD	X3,B0_X3		|1| x3	|0| x3b	|1 0 0 0|1 1 1 1|
# HB: 9-49
DOCP	RBX3			|0 0 1 1| rbx3	|1 0 1 1|1 1 0 0|
DICP	RBX3			|0 0 1 0| rbx3	|1 0 1 1|1 1 0 0|
# HB: 9-50
SXT	X3,C4			|0| x3	| c4	|0 1 1 0|0 1 1 1|
# HB: 9-51
XTR	RX3,C4			| rx3	| c4	|1 1 1 0|1 1 0 1|
# HB: 9-53
SBN	R3,C4			|0| r3	| c4	|1 1 1 1|0 0 0 0|
SBN	X3,C4			|0| x3	| c4	|1 1 1 1|0 0 0 1|
SBZ	R3,C4			|0| r3	| c4	|1 1 1 1|0 0 1 0|
SBZ	X3,C4			|0| x3	| c4	|1 1 1 1|0 0 1 1|
SBNP	R3,C4			|0| r3	| c4	|1 0 1 1|0 0 0 0|
SBNP	X3,C4			|0| x3	| c4	|1 0 1 1|0 0 0 1|
SBZP	R3,C4			|0| r3	| c4	|1 0 1 1|0 0 1 0|
SBZP	X3,C4			|0| x3	| c4	|1 0 1 1|0 0 1 1|
# HB: 9-54
SON	B0_X2			|x2 | b6	|0 0 1 1|1 0 1 1|
SOZ	B0_X2			|x2 | b6	|0 0 1 1|1 0 1 0|
SONP	B0_X2			|x2 | b6	|0 0 1 1|1 0 0 1|
SOZP	B0_X2			|x2 | b6	|0 0 1 1|1 0 0 0|
# HB: 9-56
SEQ	R3,C4			|n| r3	| c4	|0 1 1 1|1 1 1 0|
SEQ	X3,C4			|n| x3	| c4	|0 1 1 1|1 1 1 1|
SEQ	RX3,RBX3		| rx3	| rbx3	|1 1 1 1|1 0 1 0|
SNE	R3,C4			|n| r3	| c4	|0 1 1 1|1 1 0 0|
SNE	X3,C4			|n| x3	| c4	|0 1 1 1|1 1 0 1|
SNE	RX3,RBX3		| rx3	| rbx3	|1 1 1 1|1 0 0 0|
SGE	R3,C4			|1| r3	| c4	|0 1 0 0|0 0 1 0|
SGE	X3,C4			|1| x3	| c4	|0 1 0 0|0 0 1 1|
SGE	RX3,RX3			| rx3 	| rx3b	|1 1 1 1|0 1 1 0|
SLT	R3,C4			|1| r3	| c4	|0 1 0 0|0 0 0 0|
SLT	X3,C4			|1| x3	| c4	|0 1 0 0|0 0 0 1|
SLT	RX3,RX3			| rx3 	| rx3b	|1 1 1 1|0 1 0 0|
SHS	R3,C4			|1| r3	| c4	|0 1 0 0|0 1 1 0|
SHS	X3,C4			|1| x3	| c4	|0 1 0 0|0 1 1 1|
SHS	RX3,RX3			| rx3 	| rx3b	|1 1 1 1|0 1 1 1|
SLO	R3,C4			|1| r3	| c4	|0 1 0 0|0 1 0 0|
SLO	X3,C4			|1| x3	| c4	|0 1 0 0|0 1 0 1|
SLO	RX3,RX3			| rx3 	| rx3b	|1 1 1 1|0 1 0 1|
# HB: 9-57
SEQP	R3,C4			|n| r3	| c4	|0 0 1 1|1 1 1 0|
SEQP	X3,C4			|n| x3	| c4	|0 0 1 1|1 1 1 1|
SEQP	RX3,RBX3		| rx3	| rbx3	|1 0 1 1|1 0 1 0|
SNEP	R3,C4			|n| r3	| c4	|0 0 1 1|1 1 0 0|
SNEP	X3,C4			|n| x3	| c4	|0 0 1 1|1 1 0 1|
SNEP	RX3,RBX3		| rx3	| rbx3	|1 0 1 1|1 0 0 0|
SGEP	R3,C4			|1| r3	| c4	|0 0 0 0|0 0 1 0|
SGEP	X3,C4			|1| x3	| c4	|0 0 0 0|0 0 1 1|
SGEP	RX3,RX3			| rx3 	| rx3b	|1 0 1 1|0 1 1 0|
SLTP	R3,C4			|1| r3	| c4	|0 0 0 0|0 0 0 0|
SLTP	X3,C4			|1| x3	| c4	|0 0 0 0|0 0 0 1|
SLTP	RX3,RX3			| rx3 	| rx3b	|1 0 1 1|0 1 0 0|
SHSP	R3,C4			|1| r3	| c4	|0 0 0 0|0 1 1 0|
SHSP	X3,C4			|1| x3	| c4	|0 0 0 0|0 1 1 1|
SHSP	RX3,RX3			| rx3 	| rx3b	|1 0 1 1|0 1 1 1|
SLOP	R3,C4			|1| r3	| c4	|0 0 0 0|0 1 0 0|
SLOP	X3,C4			|1| x3	| c4	|0 0 0 0|0 1 0 1|
SLOP	RX3,RX3			| rx3 	| rx3b	|1 0 1 1|0 1 0 1|
# HB: 9-59
SLC	R3,C4			|1| r3	| c4	|1 0 1 0|0 0 1 0|
SLC	X3,C4			|1| x3	| c4	|1 1 1 0|0 0 1 0|
SRA	R3,C4			|1| r3	| c4	|0 0 1 0|0 1 1 0|
SRA	X3,C4			|1| x3	| c4	|0 1 1 0|0 1 1 0|
SLL	R3,C4			|1| r3	| c4	|1 0 1 0|0 0 0 0|
SLL	X3,C4			|1| x3	| c4	|1 1 1 0|0 0 0 0|
SRL	R3,C4			|1| r3	| c4	|0 0 1 0|0 1 0 0|
SRL	X3,C4			|1| x3	| c4	|0 1 1 0|0 1 0 0|
# HB: 9-60
SLLL	R3,C4			|0| r3	| c4	|1 0 1 0|0 0 0 1|
SLLL	X3,C4			|0| x3	| c4	|1 1 1 0|0 0 0 1|
SRLL	R3,C4			|0| r3	| c4	|0 0 1 0|0 1 0 1|
SRLL	X3,C4			|0| x3	| c4	|0 1 1 0|0 1 0 1|
# HB: 9-62
CLRS	R3,RBX3			|0| r3	| rbx3	|1 0 0 0|1 0 0 0|
CLRS	X3,RBX3			|1| x3	| rbx3	|1 0 0 0|1 0 0 1|
# HB: 9-63
SETS	R3,RBX3			|0| r3	| rbx3	|0 1 0 1|0 0 1 0|
SETS	X3,RBX3			|1| x3	| rbx3	|0 1 0 1|0 0 1 1|
SETS	R3,C4			|0| r3	| c4	|1 0 1 0|0 0 1 1|
SETS	X3,C4			|0| x3	| c4	|1 1 1 0|0 0 1 1|
# HB: 9-64
RELS	X3,C4			|0| x3	| c4	|0 0 0 1|0 0 0 1|
# HB: 9-65
RESS	X3,C4			|0| x3	| c4	|0 1 0 1|0 0 0 1|
# HB: 9-73
LDS	RBX3			|1 1 1 0| rbx3	|1 0 1 1|1 1 0 0|
SVS	RBX3			|1 1 0 1| rbx3	|1 0 1 1|1 1 0 0|
LDT	RBX3			|0 1 0 1| rbx3	|1 0 1 1|1 1 0 0|
SVT	RBX3			|1 1 0 0| rbx3	|1 0 1 1|1 1 0 0|
LDM	C4			|0 0 0 1| c4	|1 0 1 1|1 1 1 0|
# HB: 9-81
XCU	RBX3			|1 0 0 0| rbx3	|1 0 1 1|1 1 0 0|
# HB: 9-87
NOP	-			|1 0 0 0|0 0 0 0|1 1 1 1|0 0 0 0|
# HB: 9-89
TRP	C4			|0 0 0 0| c4	|1 0 1 1|1 1 1 0|
'''

cr80_mod1234_instructions = '''
# HB: 9-67
SIO	R3,R3			|0| r3	|0| r3b	|1 0 0 1|0 1 1 0|
SIO	X3,R3			|0| x3	|0| r3b	|1 1 0 1|0 1 1 0|
CIO	R3,R3			|1| r3	|0| r3b	|1 0 0 1|0 1 1 0|
CIO	X3,R3			|1| x3	|0| r3b	|1 1 0 1|0 1 1 0|
RIO	R3,R3			|0| r3	|0| r3b	|1 0 0 1|0 1 1 1|
RIO	X3,R3			|0| x3	|0| r3b	|1 1 0 1|0 1 1 1|
WIO	R3,R3			|1| r3	|0| r3b	|1 0 0 1|0 1 1 1|
WIO	X3,R3			|1| x3	|0| r3b	|1 1 0 1|0 1 1 1|
# HB: 9-76
SVP	L4			|0 0 1 0| l4	|1 0 1 1|1 1 1 0|
# HB: 9-77
LDN	RBX3			|0 1 0 0| rbx3	|1 0 1 1|1 1 0 0|
LDP	RBX3			|0 0 0 0| rbx3	|1 0 1 1|1 1 0 0|
# HB: 9-82
MON	C8			| c8		|1 0 1 0|0 1 1 0|
# HB: 9-83
DML	-			|0 1 1 1|0 0 0 0|1 0 1 1|1 1 0 0|
# HB: 9-88
CPU	-			|0 1 1 0|1 1 1 1|1 0 1 1|1 1 1 0|
# HB: 9-90
INT	RX3			|0 0 1 0| RX3	|1 0 1 1|1 1 0 1|
'''

cr80_mod12_instructions = '''
# HB: 9-78
LDR	RBX3			|0 0 0 1| rbx3	|1 0 1 1|1 1 0 0|
# HB: 9-79
XRM	C8			| c8		|1 1 1 0|0 1 1 0|
'''

cr80_mod2_instructions = '''
# HB: 9-68
FNC	R3			|1| r3	|0 0 0 0|0 0 0 1|0 0 0 1|
FNC	X3			|1| r3	|0 0 0 0|0 1 0 1|0 0 0 1|
FNC	R3,X3			|1| r3	|1| x3  |0 0 0 1|0 0 0 1|
FNC	X3,X3			|1| x3	|1| x3b |0 1 0 1|0 0 0 1|
'''

cr80_mod345_instructions = '''
# HB:	9-80
ALT	-			|1 0 1 1|0 0 0 0|1 0 1 1|1 1 0 0|
'''

cr80_mod45_instructions = '''
# HB:	9-81
CAE	-			|1 0 0 0|0 0 0 0|1 0 1 1|1 1 1 0|
CAD	-			|1 0 0 0|0 0 0 1|1 0 1 1|1 1 1 0|
CAC	-			|1 0 0 0|0 0 1 0|1 0 1 1|1 1 1 0|
TST	-			|1 0 0 0|0 0 1 1|1 0 1 1|1 1 1 0|
RCR	-			|1 0 0 0|0 1 0 0|1 0 1 1|1 1 1 0|
TTM	-			|1 0 0 0|0 1 0 1|1 0 1 1|1 1 1 0|
'''


cr80_mod5_instructions = '''
# HB: 9-43
MUL	RX3,R3			| rx3 	|0| r3b	|1 1 1 0|1 0 1 0|
# HB: 9-45
DIV	RX3,B0_X3		| rx3	|1| x3	|1 1 1 0|1 0 1 1|
# HB: 9-70
SIO	R3,R3			|0| r3	|0| r3	|1 0 0 1|0 1 1 0|
SIO	X3,R3			|0| x3	|0| r3	|1 1 0 1|0 1 1 0|
CIO	R3,R3			|1| r3	|0| r3	|1 0 0 1|0 1 1 0|
CIO	X3,R3			|1| x3	|0| r3	|1 1 0 1|0 1 1 0|
# HB: 9-71
RIO	R3,R3			|0| r3	|0| r3	|1 0 0 1|0 1 1 1|
RIO	X3,R3			|0| x3	|0| r3	|1 1 0 1|0 1 1 1|
WIO	R3,R3			|1| r3	|0| r3	|1 0 0 1|0 1 1 1|
WIO	X3,R3			|1| x3	|0| r3	|1 1 0 1|0 1 1 1|
# HB: 9-74
SVE	RBX3			|0 1 1 0| rbx3	|1 0 1 1|1 1 0 1|
# HB: 9-75
STP	C4			|0 0 0 1| c4	|1 0 1 1|1 1 0 0|
# HB: 9-85
MON	C8			| c8		|1 0 1 0|0 1 1 0|
# HB: 9-86
RTM	C4			|0 0 1 0| c4	|1 0 1 1|1 1 0 1|
# HB: 9-92
CALL	C4,P16			|0 1 1 1| c4	|1 0 1 1|1 1 1 0| p16				|
# HB: 9-95
RET	C4			|1 0 1 0| c4	|1 0 1 1|1 1 0 1|
# HB: 9-96
CPU	RBX3			|0 1 1 0| rbx3	|1 0 1 1|1 1 1 0|
# HB: 9-97
LDB	RBX3			|0 0 0 0| rbx3	|1 0 1 1|1 1 0 0|
# HB: 9-98
SVB	RBX3			|0 1 0 0| rbx3	|1 0 1 1|1 1 0 0|
# HB: 9-99
LTT	RBX3			|1 1 1 0| rbx3	|1 0 1 1|1 1 0 1|
# HB: 9-100
CSP	X3,R3			|1| x3	|0| r3	|0 0 0 1|0 0 0 0|
# HB: 9-101
INX	X3,R3			|1| x3	|1| r3	|0 0 0 1|0 0 0 0|
'''

cr80_float_instructions = '''
# HB: 9-105
FADD	X3,X3			|0| x3	|l| x3	|0 0 0 0|0 0 0 1|
# HB: 9-106
FSUB	X3,X3			|0| x3	|l| x3	|0 0 0 0|0 0 1 0|
# HB: 9-107
FMUL	X3,X3			|0| x3	|l| x3	|0 0 0 0|0 0 1 1|
# HB: 9-108
FDIV	X3,X3			|0| x3	|l| x3	|0 0 0 0|0 1 0 0|
# HB: 9-109
FREM	X3,X3			|0| x3	|l| x3	|0 0 0 0|0 1 0 1|
# HB: 9-110
SQRT	X3,X3			|0| x3	|l| x3	|0 0 0 0|0 1 1 0|
# HB: 9-111
TAN	X3,X3			|0| x3	|l| x3	|0 0 0 0|0 1 1 1|
# HB: 9-112
ATAN	X3,X3			|1| x3	|l| x3	|0 0 0 1|0 0 0 1|
# HB: 9-113
EXP2	X3,X3			|1| x3	|l| x3	|0 0 1 0|0 1 0 1|
# HB: 9-114
LOG2	X3,X3			|0| x3	|l| x3	|0 0 1 0|0 1 0 0|
# HB: 9-116
FCNV	X3,X3			|0| x3	|l| x3	|0 0 1 0|0 1 1 0|
# HB: 9-117
FINT	X3,X3			|0| x3	|l| x3	|0 1 0 0|0 0 0 0|
# HB: 9-118
INTF	X3,X3			|0| x3	|l| x3	|0 1 0 0|0 0 0 1|
# HB: 9-120
FDEC	X3,X3			|0| x3	|l| x3	|0 1 0 0|0 0 1 0|
# HB: 9-122
DECF	X3,X3			|0| x3	|l| x3	|0 1 0 0|0 0 1 1|
# HB: 9-123
FSLT	X3,X3			|0| x3	|l| x3	|0 1 0 0|0 1 0 0|
FSEQ	X3,X3			|0| x3	|l| x3	|0 1 0 0|0 1 0 1|
FSGE	X3,X3			|0| x3	|l| x3	|0 1 0 0|0 1 1 0|
FSUO	X3,X3			|0| x3	|l| x3	|0 1 0 0|0 1 1 1|
FSLTP	X3,X3			|1| x3	|l| x3	|0 1 0 1|0 0 0 0|
# HB: 9-124
FSEQP	X3,X3			|1| x3	|l| x3	|0 1 0 1|0 0 0 1|
FSGEP	X3,X3			|1| x3	|l| x3	|0 1 0 1|0 0 1 0|
FSUOP	X3,X3			|0| x3	|l| x3	|0 1 0 1|0 0 1 1|
'''

cr80_alt_move_instructions = '''
# HB: 9-127
MOWA	X3,X3			|0| x3	|0| x3	|0 0 0 0 1| r3	|
# HB: 9-128
MOWD	X3,X3			|0| x3	|1| x3	|0 0 0 0 1| r3	|
# HB: 9-129
MSWA	X3,X3,R33		|1| x3	|0| x3	|0 0 1 0 0| r33	|
# HB: 9-130
MSWD	X3,X3,R33		|1| x3	|1| x3	|0 0 1 0 0| r33	|
# HB: 9-131
MOBA	X3,X3,R3		|1| x3	|0| x3	|0 0 0 0 1| r3 	|
# HB: 9-132
MOBD	X3,X3,R3		|1| x3	|1| x3	|0 0 0 0 1| r3	|
# HB: 9-133
GMOW	GX33,GX33,R3		|0| gx33|x|gx33 |0 0 0 1 0| r3	|
# HB: 9-134
GMSW	GX33,GX33,R3		|0| gx33|0|gx33 |0 0 1 0 0| r3	|
# HB: 9-135
GMOB	GX33,GX33,R3		|0| gx33|0|gx33 |0 0 0 1 1| r3	|
# HB: 9-136
GLDB	GX33,R3			|0| gx33|0| r3	|0 0 1 1 0 0 0 0|
# HB: 9-137
GSTB	R3,GX33,R3		|0| gx33|1| r3	|0 0 1 1 0 0 0 0|
# HB: 9-138
GLDW	GX33,R3			|1| gx33|0| r3	|0 0 1 1 0 0 0 0|
# HB: 9-139
GSTW	R3,GX33,R3		|1| gx33|1| r3	|0 0 1 1 0 0 0 0|
# HB: 9-140
GNW	B8,R3			| b8		|0 1 0 0 0| r3	|
'''

class cr80_ins(assy.Instree_ins):
    ''' ... '''

class cr32(assy.Instree_disass):
    def __init__(self, macros=False):
        super().__init__(
                    "cr80",
                    ins_word=16,
                    abits=32,
                    endian=">",
                )
        self.add_ins(cr80_mod12345_instructions, cr80_ins)
        #self.add_ins(cr80_mod1234_instructions, cr80_ins)
        self.add_ins(cr80_mod5_instructions, cr80_ins)
        self.add_ins(cr80_float_instructions, cr80_ins)


if __name__ == '__main__':
    m = cr32()
    m.it.dump()
