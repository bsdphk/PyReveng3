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

from pyreveng import assy

#
# From RCSL 42-i-1008 "RC3803 CPU Programmer's Reference Manual
#
cr80_instructions = '''
# HB: 9-15
MODC	12345,C8		| c8		|1 1 1 0|0 1 0 0|
MODC	12345,CN8		| cn8		|1 0 1 0|0 1 0 0|
# HB: 9-16
MOD4	12345,C8		| c8		|1 1 1 0|0 1 0 1|
MOD4	12345,CN8		| cn8		|1 0 1 0|0 1 0 1|
MOD8	12345,C8		| c8		|0 1 0 1|0 1 1 0|
# HB: 9-17
MOD	12345,B6_X2		|x2 | b6	|0 1 0 1|0 1 0 0|
MODN	12345,B6_X2		|x2 | b6	|0 1 0 1|0 1 0 1|
MOD	12345,B8		| b8		|1 0 0 1|0 1 0 0|
MODN	12345,B8		| b8		|0 0 0 1|0 1 0 0|
MOD	12345,P8		| p8		|1 0 0 1|0 1 0 1|
MODN	12345,P8		| p8		|0 0 0 1|0 1 0 1|
# HB: 9-19
MOVC	12345,C8		| c8		|0 1 0 0|1| r3	|
MOVC	12345,CN8		| cn8		|0 0 1 0|1| r3	|
MOVC	12345,C4		|0| x3	| c4	|0 1 0 1|0 0 0 0|
MOVC	12345,CN4		|0| x3	| cn4	|0 0 0 1|0 0 0 0|
# HB: 9-20
MOV	12345,B8,R3		| b8		|0 1 1 0|1| r3	|
MOV	12345,R3,B8		| b8		|0 1 1 1|0| r3	|
MOV	12345,R3,R3		|0| r3	|0| r3	|1 0 1 1|1 0 1 1|
MOV	12345,R3,B0_X3		|1| r3	|0| x3	|1 0 1 1|1 0 1 1|
MOV	12345,X3,R3		|0| x3	|0| r3	|1 1 1 1|1 0 1 1|
MOV	12345,X3,B0_X3		|1| x3	|0| x3b	|1 1 1 1|1 0 1 1|
MOV	12345,B6_X2,R3		|x2 | b6	|0 0 0 1|1| r3	|
MOV	12345,R3,B6.X2		|x2 | b6	|1 0 0 0|0| r3	|
MOV	12345,P8,R3		| p8		|1 0 0 1|1| r3	|
# HB: 9-21
MOVB	12345,BB6_X2,R2		|x2 | b6	|0 1 1 1|1 0|r2	|
MOVB	12345,R2,BB6_X2		|x2 | b6	|1 0 0 1|0 0|r2	|
# HB: 9-22
MOVL	12345,B6_X2,R2		|x2 | b6	|0 1 1 0|0 0|r2	|
MOVL	R2,B6_X2		|x2 | b6	|1 1 0 1|0 0|r2	|
# HB: 9-23
MVP	12345,P6_X2,R2		|x2 | p6	|0 0 1 0|0 0|r2 |
# HB: 9-24
MOVM	12345,X3,X3b		|0| x3	|0| x3b	|1 1 1 0|1 0 0 1|
# HB: 9-25
PUT	12345,R3,X3		|1| r3	|0| x3	|1 1 1 0|1 0 0 1|
PUT	12345,X3,X3		|1| x3	|1| x3b	|1 1 1 0|1 0 0 0|
# HB: 9-26
XCH	12345,R3,R3		|0| r3	|0| r3b	|1 1 1 0|1 1 1 0|
XCH	12345,R3,B0_X3		|0| r3	|1| x3	|1 1 1 0|1 1 1 0|
XCH	12345,X3,R3		|1| x3	|0| r3	|1 1 1 0|1 1 1 1|
XCH	12345,X3,B0_X3		|1| x3	|1| x3b	|1 1 1 0|1 1 1 1|
# HB: 9-27
STC	12345,C4		|1 1 1 0| c4	|1 0 1 1|1 1 1 0|
STC	12345,R3,B0_X3		|0| r3	|0| x3	|1 0 1 1|1 0 0 1|
STC	12345,X3,B0_X3		|0| x3	|0| x3	|1 1 1 1|1 0 0 1|
# HB: 9-28
UNS	12345,C4		|1 0 1 0| c4	|1 0 1 1|1 1 1 0|
UNS	12345,R3,B0_X3		|0| r3	|1| x3	|1 0 1 1|1 0 0 1|
UNS	12345,X3,B0_X3		|0| x3	|1| x3b	|1 1 1 1|1 0 0 1|
# HB: 9-30 XXX L10 ?
JMP	12345,L10		| l10		|1 1 0 1|1 0|l2 |
JMP	12345,LN10		| ln10		|0 1 0 1|1 0|ln2|
JMP	12345,L8		| l8		|1 1 0 1|1 1 0 0|
JMP	12345,LN8		| ln8		|0 1 0 1|1 1 0 0|
JMP	12345,S2,L8		| l8		|1 1 0 1|1 1| s2|
JMP	12345,S2,LN8		| ln8		|0 1 0 1|1 1| s2|
# HB: 9-31
JMP	12345,P6_X2		|x2 | p6	|1 0 1 1|1 1 1 1|
# HB: 9-32
JMPI	12345,B6_X2		|x2 | b6	|0 0 0 1|0 0 1 0|
JMPI	12345,B8		| b8		|1 1 1 0|0 1 1 1|
JMPI	12345,P8		| p8		|1 1 1 1|1 1 0 0|
JMPI	12345,S2,P8		| p8		|1 1 1 1|1 1| s2|
# HB: 9-33
JON	12345,R3,L4		|1| r3	| l4	|1 1 1 1|0 0 0 0|
JON	12345,R3,LN4		|1| r3	| ln4	|1 0 1 1|0 0 0 0|
JON	12345,X3,L4		|1| x3	| l4	|1 1 1 1|0 0 0 1|
JON	12345,X3,LN4		|1| x3	| ln4	|1 0 1 1|0 0 0 1|
JOZ	12345,R3,L4		|1| r3	| l4	|1 1 1 1|0 0 1 0|
JOZ	12345,R3,LN4		|1| r3	| ln4	|1 0 1 1|0 0 1 0|
JOZ	12345,X3,L4		|1| x3	| l4	|1 1 1 1|0 0 1 1|
JOZ	12345,X3,LN4		|1| x3	| ln4	|1 0 1 1|0 0 1 1|
# HB: 9-34
JVN	12345,L4		|1 0 1 1| l4	|1 0 1 1|1 1 1 0|
JVN	12345,LN4		|0 0 1 1| ln4	|1 0 1 1|1 1 1 0|
# HB: 9-35
SOB	12345,R3,LN8		| ln8		|1 1 0 0|0| r3	|
# HB: 9-37
ADDC	12345,C8,R3		| c8		|1 1 0 0|1| r3	|
ADDC	12345,CN8,R3		| cn8		|1 0 1 0|1| r3	|
ADD	12345,R3,R3		|0| r3	|0| r3	|1 0 0 0|1 0 1 0|
ADD	12345,R3,B0_X3		|0| r3	|1| x3	|1 0 0 0|1 0 1 0|
ADD	12345,X3,R3		|1| x3	|0| r3	|1 0 0 0|1 0 1 0|
ADD	12345,X3,B0_X3		|1| x3	|1| x3b	|1 0 0 0|1 0 1 0|
ADD	12345,B6_X2,R3		|x2 | b6	|0 0 1 1|0| r3	|
ADD	12345,R3,B6_X2		|x2 | b6	|0 0 0 0|1| r3	|
ADDU	12345,R3,R3		|0| r3	|0| r3	|1 1 0 1|0 1 0 0|
ADDU	12345,R3,B0_X3		|0| r3	|1| x3	|1 1 0 1|0 1 0 0|
ADDU	12345,X3,R3		|1| x3	|0| r3	|1 1 0 1|0 1 0 0|
ADDU	12345,X3,B0_X3		|1| x3	|1| x3	|1 1 0 1|0 1 0 0|
# HB: 9-41
SUB	12345,R3,R3		|0| r3	|0| r3	|1 0 0 0|1 0 1 1|
SUB	12345,R3,B0_X3		|0| r3	|1| x3	|1 0 0 0|1 0 1 1|
SUB	12345,X3,R3		|1| x3	|0| r3	|1 0 0 0|1 0 1 1|
SUB	12345,X3,B0_X3		|1| x3	|1| x3	|1 0 0 0|1 0 1 1|
SUBU	12345,R3,R3		|0| r3	|0| r3	|1 1 0 1|0 1 0 1|
SUBU	12345,R3,B0_X3		|0| r3	|1| x3	|1 1 0 1|0 1 0 1|
SUBU	12345,X3,R3		|1| x3	|0| r3	|1 1 0 1|0 1 0 1|
SUBU	12345,X3,B0_X3		|1| x3	|1| x3	|1 1 0 1|0 1 0 1|
# HB: 9-42
MUL	12345,R3,B0_X3		|0| r3	|1| x3	|1 1 1 0|1 0 1 0|
MUL	12345,X3,B0_X3		|1| x3	|1| x3b	|1 1 1 0|1 0 1 0|
# HB: 9-43
MUL	5,R3,R3			|0| r3	|0| r3b	|1 1 1 0|1 0 1 0|
MUL	5,X3,R3			|1| x3	|0| r3	|1 1 1 0|1 0 1 0|
# HB: 9-44
DIV	12345,R3,R3		|0| r3	|0| r3b	|1 1 1 0|1 0 1 1|
DIV	12345,X3,R3		|1| x3	|0| r3	|1 1 1 0|1 0 1 1|
# HB: 9-45
DIV	5,R3,B0_X3		|0| r3	|1| x3	|1 1 1 0|1 0 1 1|
DIV	5,X3,B0_X3		|1| x3	|1| x3b	|1 1 1 0|1 0 1 1|
'''
