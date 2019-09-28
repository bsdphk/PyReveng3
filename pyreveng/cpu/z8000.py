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


'''Zilog Z8000
'''

from pyreveng import assy, data, mem

z8000_desc = '''
# Z8000 instruction list
#
# From:
#	Z8000 CPU User's Reference Manual
#	ISBN 0-13-983908-9
#
# Trailing 'address' and 'data' fields are not included, they are
# divined by the disassembler code for the specific cpu type
#
#				|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|

# p57
ADC	W,Rd,Rs			|1 0 1 1 0 1 0|w| rs	| rd	|

# p58
ADD	W,Rd,Rs			|1 0|0 0 0 0 0|w| rs	| rd	|
ADD	L,Rd,Rs			|1 0 0 1 0 1 1 0| rs	| rd	|

ADD	W,Rd,Data		|0 0 0 0 0 0 0|w|0 0 0 0| rd	|
ADD	L,Rd,Data		|0 0 0 1 0 1 1 0|0 0 0 0| rd	|

ADD	W,Rd,Irs		|0 0 0 0 0 0 0|w| rs	| rd	|
ADD	L,Rd,Irs		|0 0 0 1 0 1 1 0| rs	| rd	|

# p59
ADD	W,Rd,Adr		|0 1 0 0 0 0 0|w|0 0 0 0| rd	|
ADD	L,Rd,Adr		|0 1 0 1 0 1 1 0|0 0 0 0| rd	|

ADD	W,Rd,Xrs		|0 1 0 0 0 0 0|w| rs	| rd	|
ADD	L,Rd,Xrs		|0 1 0 1 0 1 1 0| rs	| rd	|

# p60
AND	W,Rd,Rs			|1 0|0 0 0 1 1|w| rs	| rd	|

AND	W,Rd,Data		|0 0 0 0 0 1 1|w|0 0 0 0| rd	|

AND	W,Rd,Irs		|0 0 0 0 0 1 1|w| rs	| rd	|

AND	W,Rd,Adr		|0 1 0 0 0 1 1|w|0 0 0 0| rd	|

AND	W,Rd,Xrs		|0 1 0 0 0 1 1|w| rs	| rd	|

# p62
BIT	W,Rd,Bit		|1 0 1 0 0 1 1|w| rd	| bit	|

BIT	W,Ird,Bit		|0 0 1 0 0 1 1|w| rd	| bit	|

BIT	W,Adr,Bit		|0 1 1 0 0 1 1|w|0 0 0 0| bit	|

BIT	W,Xrd,Bit		|0 1 1 0 0 1 1|w| rd	| bit	|

# p63
BIT	Rd,Rs			|0 0 1 0 0 1 1|w|0 0 0 0| rs	|0 0 0 0| rd	|0 0 0 0 0 0 0 0|

# p64
CALL	Ird,>C			|0 0 0 1 1 1 1 1| rd	|0 0 0 0|

CALL	Dst,>C			|0 1 0 1 1 1 1 1|0 0 0 0|0 0 0 0|

CALL	Xrd,>C			|0 1 0 1 1 1 1 1| rd	|0 0 0 0|

# p65
CALR	Imm12			|1 1 0 1| disp			|

# p66
CLR	W,Rd			|1 0 0 0 1 1 0|w| rd	|1 0 0 0|

CLR	W,Ird			|0 0 0 0 1 1 0|w| rd	|1 0 0 0|

CLR	W,Adr			|0 1 0 0 1 1 0|w|0 0 0 0|1 0 0 0|

CLR	W,Xrd			|0 1 0 0 1 1 0|w| rd	|1 0 0 0|

# p67
COM	W,Rd			|1 0 0 0 1 1 0|w| rd	|0 0 0 0|

COM	W,Ird			|0 0 0 0 1 1 0|w| rd	|0 0 0 0|

COM	W,Adr			|0 1 0 0 1 1 0|w|0 0 0 0 0 0 0 0|

COM	W,Xrd			|0 1 0 0 1 1 0|w| rd	|0 0 0 0|

# p68
COMFLG	Flag			|1 0 0 0 1 1 0 1| flag	|0 1 0 1|

# p69
CP	W,Rd,Rs			|1 0|0 0 1 0 1|w| rs	| rd	|
CP	L,Rd,Rs			|1 0 0 1 0 0 0 0| rs	| rd	|

CP	W,Rd,Data		|0 0 0 0 1 0 1|w|0 0 0 0| rd	|
CP	L,Rd,Data		|0 0 0 1 0 0 0 0|0 0 0 0| rd	|

CP	W,Rd,Irs		|0 0 0 0 1 0 1|w| rs	| rd	|
CP	L,Rd,Irs		|0 0 0 1 0 0 0 0| rs	| rd	|

# p70
CP	W,Rd,Adr		|0 1 0 0 1 0 1|w|0 0 0 0| rd	|
CP	L,Rd,Adr		|0 1 0 1 0 0 0 0 0 0 0 0| rd	|

CP	W,Rd,Xrs		|0 1 0 0 1 0 1|w| rs	| rd	|
CP	L,Rd,Xrs		|0 1 0 1 0 0 0 0| rs	| rd	|

CP	W,Ird,Data		|0 0 0 0 1 1 0|w| rd	|0 0 0 1|

# p71
CP	W,Adr,Data		|0 1 0 0 1 1 0|w|0 0 0 0|0 0 0 1|

CP	W,Xrd,Data		|0 1 0 0 1 1 0|w| rd	|0 0 0 1|

# p72
CPD	W,Rd,Irs,R,Cc		|1 0 1 1 1 0 1|w| rs	|1 0 0 0|0 0 0 0| r	| rd	| cc	|

# p73
CPDR	W,Rd,Irs,R,Cc		|1 0 1 1 1 0 1|w| rs	|1 1 0 0|0 0 0 0| r	| rd	| cc	|

# p74
CPI	W,Rd,Irs,R,Cc		|1 0 1 1 1 0 1|w| rs	|0 0 0 0|0 0 0 0| r	| rd	| cc	|

# p76
CPIR	W,Rd,Irs,R,Cc		|1 0 1 1 1 0 1|w| rs	|0 1 0 0|0 0 0 0| r	| rd	| cc	|

# p78
CPSD	Ird,Irs,R,Cc		|1 0 1 1 1 0 1|w| rs	|1 0 1 1|0 0 0 0| r	| rd	| cc	|

# p79
CPSDR	Ird,Irs,R,Cc		|1 0 1 1 1 0 1|w| rs	|1 1 1 0|0 0 0 0| r	| rd	| cc	|

# p81
CPSI	Ird,Irs,R,Cc		|1 0 1 1 1 0 1|w| rs	|0 0 1 0|0 0 0 0| r	| rd	| cc	|

# p83
CPSIR	Ird,Irs,R,Cc		|1 0 1 1 1 0 1|w| rs	|0 1 1 0|0 0 0 0| r	| rd	| cc	|

# p85
DAB	B,Rd			|1 0 1 1 0 0 0 0| rd	|0 0 0 0|

# p87
DEC	W,Rd,N			|1 0 1 0 1 0 1|w| rd	| n	|

DEC	W,Ird,N			|0 0 1 0 1 0 1|w| rd	| n	|

DEC	W,Adr,N			|0 1 1 0 1 0 1|w|0 0 0 0| n	|

DEC	Xrd,N			|0 1 1 0 1 0 1|w| rd	| n	|

# p88
DI	Vi,Nvi			|0 1 1 1 1 1 0 0|0 0 0 0 0 0|v|n|

# p90
DIV	Q,Rd,Rs			|1 0 0 1 1 0 1|q| rs	| rd	|

DIV	Q,Rd,Data		|0 0 0 1 1 0 1|q|0 0 0 0| rd	|

DIV	Q,Rd,Irs		|0 0 0 1 1 0 1|q| rs	| rd	|

DIV	Q,Rd,Adr		|0 1 0 1 1 0 1|q|0 0 0 0| rd	|

DIV	Q,Rd,Xrs		|0 1 0 1 1 0 1|q| rs	| rd	|

# p92
DJNZ	W,Rd,Rel7,>JC		|1 1 1 1| rd	|w| disp	|

# p93
EI	Vi,Nvi			|0 1 1 1 1 1 0 0|0 0 0 0 0 1|v|n|

# p94
EX	W,Rd,Rs			|1 0 1 0 1 1 0|w| rs	| rd	|

EX	W,Rd,Irs		|0 0 1 0 1 1 0|w| rs	| rd	|

EX	W,Rd,Adr		|0 1 1 0 1 1 0|w|0 0 0 0| rd	|

EX	W,Rd,Xrs		|0 1 1 0 1 1 0|w| rs	| rd	|

# p95
EXTSB	Rd			|1 0 1 1 0 0 0 1| rd	|0 0 0 0|
EXTS	L,Rd			|1 0 1 1 0 0 0 1| rd	|1 0 1 0|
EXTSL	Q,Rd			|1 0 1 1 0 0 0 1| rd	|0 1 1 1|

# p96
HALT	-			|0 1 1 1 1 0 1 0 0 0 0 0 0 0 0 0|

# p97
IN	W,Rd,Irs		|0 0 1 1 1 1 0|w| rs	| rd	|

IN	W,S,Rd,Port		|0 0 1 1 1 0 1|w| rd	|0 1 0|s| port				|

# p98
INC	W,Rd,N			|1 0 1 0 1 0 0|w| rd	| n	|

INC	W,Ird,N			|0 0 1 0 1 0 0|w| rd	| n	|

INC	W,Adr,N			|0 1 1 0 1 0 0|w|0 0 0 0| n	|

INC	W,Xrd,N			|0 1 1 0 1 0 0|w| rd	| n	|

# p99
IND	W,Ird,Ird,R,S		|0 0 1 1 1 0 1|w| rs	|0 0 0|s|0 0 0 0| r	| rd	|1 0 0 0|

# p100
INDR	W,Ird,Ird,R,S		|0 0 1 1 1 0 1|w| rs	|1 0 0|s|0 0 0 0| r	| rd	|0 0 0 0|

# p102
INI	W,Ird,Irs,R,S		|0 0 1 1 1 0 1|w| rs	|1 0 0|s|0 0 0 0| r	| rd	|1 0 0 0|

# p103
INIR	W,Ird,Irs,R,S		|0 0 1 1 1 0 1|w| rs	|0 0 0|s|0 0 0 0| r	| rd	|0 0 0 0|

# p105
IRET	-,>R			|0 1 1 1 1 0 1 1|0 0 0 0 0 0 0 0|

# p106
JP	Ird,>JC,Cc		|0 0 0 1 1 1 1 0| rd	| cc	|
JP	Dst,>JC,Cc		|0 1 0 1 1 1 1 0|0 0 0 0| cc	|
JP	Xrd,>JC,Cc		|0 1 0 1 1 1 1 0| rd	| cc	|

# p107
JR	Rel8,>JC,Cc		|1 1 1 0| cc	| disp		|

# p108
LD	W,Rd,Rs			|1 0 1 0 0 0 0|w| rs	| rd	|
LD	L,Rd,Rs			|1 0 0 1 0 1 0 0| rs	| rd	|

LD	W,Rd,Irs		|0 0 1 0 0 0 0|w| rs	| rd	|
LD	L,Rd,Irs		|0 0 0 1 0 1 0 0| rs	| rd	|

LD	W,Rd,Adr		|0 1 1 0 0 0 0|w|0 0 0 0| rd	|
LD	L,Rd,Adr		|0 1 0 1 0 1 0 0|0 0 0 0| rd	|

# p109
LD	W,Rd,Xrs		|0 1 1 0 0 0 0|w| rs	| rd	|
LD	L,Rd,Xrs		|0 1 0 1 0 1 0 0| rs	| rd	|

LD	W,Rd,Bars		|0 0 1 1 0 0 0|w| rs	| rd	| disp				|
LD	L,Rd,Bars		|0 0 1 1 0 1 0 1| rs	| rd	| disp				|

LD	W,Rd,Bxrs		|0 1 1 1 0 0 0|w| rs	| rd	|0 0 0 0| rx	|0 0 0 0 0 0 0 0|
LD	L,Rd,Bxrs		|0 1 1 1 0 1 0|1| rs	| rd	|0 0 0 0| rx	|0 0 0 0 0 0 0 0|

LD	W,Ird,Rs		|0 0 1 0 1 1 1|w| rd	| rs	|
LD	L,Ird,Rs		|0 0 0 1 1 1 0 1| rd	| rs	|

LD	W,Adr,Rs		|0 1 1 0 1 1 1|w|0 0 0 0| rs	|

# p110
LD	L,Adr,Rs		|0 1 0 1 1 1 0 1|0 0 0 0| rs	|

LD	W,Xrd,Rs		|0 1 1 0 1 1 1|w| rd	| rs	|
LD	L,Xrd,Rs		|0 1 0 1 1 1 0 1| rd	| rs	|

LD	W,Bard,Rs		|0 0 1 1 0 0 1|w| rd	| rs	| disp				|
LD	L,Bard,Rs		|0 0 1 1 0 1 1 1| rd	| rs	| disp				|

LD	W,Bxrd,Rs		|0 1 1 1 0 0 1|w| rd	| rs	|0 0 0 0| rx	|0 0 0 0 0 0 0 0|
LD	L,Bxrd,Rs		|0 1 1 1 0 1 1 1| rd	| rs	|0 0 0 0| rx	|0 0 0 0 0 0 0 0|

# p111
LD	W,Rd,Data		|0 0 1 0 0 0 0|w|0 0 0 0| rd	|
LD	B,Rd,Imm8		|1 1 0 0| rd	| imm8          |
LD	L,Rd,Data		|0 0 0 1 0 1 0 0 0 0 0 0| rd	|

LD	W,Ird,Data		|0 0 0 0 1 1 0|w| rd	|0 1 0 1|

LD	W,Adr,Data		|0 1 0 0 1 1 0|w|0 0 0 0|0 1 0 1|

# p112
LD	W,Xrd,Data		|0 1 0 0 1 1 0|w| rd	|0 1 0 1|

# p113
LDA	Rd,Adr			|0 1 1 1 0 1 1 0|0 0 0 0| rd	|

LDA	Rd,Xrs			|0 1 1 1 0 1 1 0| rs	| rd	|

LDA	Rd,Bars			|0 0 1 1 0 1 0 0| rs	| rd	| disp				|

LDA	Rd,Bxrs			|0 1 1 1 0 1 0 0| rs	| rd	|0 0 0 0| rx	|0 0 0 0 0 0 0 0|

# p115
LDAR	Sd,Disp			|0 0 1 1 0 1 0 0|0 0 0 0| rd	| disp				|

# p120
LDCTL	Ctl,Rs			|0 1 1 1 1 1 0 1| rs	|1|ctl	|

LDCTL	Rd,Ctl			|0 1 1 1 1 1 0 1| rd	|0|ctl	|

# p122
LDCTLB	FLAGS,Rb		|1 0 0 0 1 1 0 0| rb	|1 0 0 1|

LDCTLB	Rb,FLAGS		|1 0 0 0 1 1 0 0| rb	|0 0 0 1|

# p123
LDD	Irs,IRd,R		|1 0 1 1 1 0 1|w| rs	|1 0 0 1|0 0 0 0| r	| rd	|1 0 0 0|

# p123
LDDR	Irs,IRd,R		|1 0 1 1 1 0 1|w| rs	|1 0 0 1|0 0 0 0| r	| rd	|0 0 0 0|

# p126
LDI	W,Ird,Irs,R		|1 0 1 1 1 0 1|w| rs	|0 0 0 1|0 0 0 0| r	| rd	|1 0 0 0|

# p127
LDIR	W,Ird,Irs,R		|1 0 1 1 1 0 1|w| rs	|0 0 0 1|0 0 0 0| r	| rd	|0 0 0 0|

# p129
LDK	Rd,Imm4			|1 0 1 1 1 1 0 1| rd	| imm4	|

# p130
LDM	Rd,Irs,N		|0 0 0 1 1 1 0 0| rs	|0 0 0 1|0 0 0 0| rd	|0 0 0 0| n	|

LDM	Rd,Adr,N		|0 1 0 1 1 1 0 0 0 0 0 0 0 0 0 1|0 0 0 0| rd	|0 0 0 0| n	|

# p131
LDM	Rd,Xrs,N		|0 1 0 1 1 1 0 0| rs	|0 0 0 1|0 0 0 0| rd	|0 0 0 0| n	|

LDM	Ird,Rs,N		|0 0 0 1 1 1 0 0| rd	|1 0 0 1|0 0 0 0| rs	|0 0 0 0| n	|

LDM	Adr,Rs,N		|0 1 0 1 1 1 0 0 0 0 0 0 1 0 0 1|0 0 0 0| rs	|0 0 0 0| n	|

LDM	Xrd,Rs,N		|0 1 0 1 1 1 0 0| rd	|1 0 0 1|0 0 0 0| rs	|0 0 0 0| n	|

# p132
LDPS	Irs			|0 0 1 1 1 0 0 1| rs	|0 0 0 0|

LDPS	Adr			|0 1 1 1 1 0 0 1 0 0 0 0 0 0 0 0|

LDPS	Xrs			|0 1 1 1 1 0 0 1| rs	|0 0 0 0|

# p133
LDR	W,Rd,Rel		|0 0 1 1 0 0 0|w|0 0 0 0|rd	| disp				|

# p136
MBIT	-			|0 1 1 1 1 0 1 1 0 0 0 0 1 0 1 0|

# p138
MREQ	Rd			|0 1 1 1 1 0 1 1| rd	|1 1 0 1|

# p139
MRES	-			|0 1 1 1 1 0 1 1 0 0 0 0 1 0 0 1|

# p140
MSET	-			|0 1 1 1 1 0 1 1 0 0 0 0 1 0 0 0|

# p142
MULT	Q,Qd,Rs			|1 0 0 1 1 0 0|q| rs	| rd	|

MULT	Q,Qd,Data		|0 0 0 1 1 0 0|q|0 0 0 0| rd	|

MULT	Q,Qd,Irs		|0 0 0 1 1 0 0|q| rs	| rd	|

MULT	Q,Qd,Adr		|0 1 0 1 1 0 0|q|0 0 0 0| rd	|

MULT	Q,Qd,Xrs		|0 1 0 1 1 0 0|q| rs	| rd	|

# p144
NEG	W,Rd			|1 0 0 0 1 1 0|w| rd	|0 0 1 0|

NEG	W,Ird			|0 0 0 0 1 1 0|w| rd	|0 0 1 0|

NEG	W,Adr			|0 1 0 0 1 1 0|w|0 0 0 0|0 0 1 0|

NEG	W,Xrd			|0 1 0 0 1 1 0|w| rd	|0 0 1 0|

# p145
NOP	-			|1 0 0 0 1 1 0 1|0 0 0 0 0 1 1 1|

# p146
OR	W,Rd,Rs			|1 0 0 0 0 1 0|w| rs	| rd	|

OR	W,Rd,Data		|0 0 0 0 0 1 0|w|0 0 0 0| rd	|

OR	W,Rd,Irs		|0 0 0 0 0 1 0|w| rs	| rd	|

OR	W,Rd,Adr		|0 1 0 0 0 1 0|w|0 0 0 0| rd	|

OR	W,Rd,Xrs		|0 1 0 0 0 1 0|w| rs	| rd	|

# p148
OTDR	W,S,Ird,Irs,R		|0 0 1 1 1 0 1|w| rs	|1 0 1|s|0 0 0 0| r	| rd	|0 0 0 0|

# p150
OTIR	W,S,Ird,Irs,R		|0 0 1 1 1 0 1|w| rs	|0 0 1|s|0 0 0 0| r	| rd	|0 0 0 0|

# p152
OUT	W,Ird,Rs		|0 0 1 1 1 1 1|w| rd	| rs	|

OUT	W,S,Port,Rs		|0 0 1 1 1 0 1|w| rs	|0 1 1|s| port				|

# p153
OUTD	W,S,Ird,Irs,R		|0 0 1 1 1 0 1|w| rs	|1 0 1|s|0 0 0 0| r	| rd	|1 0 0 0|

# p154
OUTI	W,S,Ird,Irs,R		|0 0 1 1 1 0 1|w| rs	|0 0 1|s|0 0 0 0| r	| rd	|1 0 0 0|

# p156
POP	Rd,Irs			|1 0 0 1 0 1 1 1| rs	| rd	|
POP	L,Rd,Irs		|1 0 0 1 0 1 0 1| rs	| rd	|

POP	IRd,Irs			|0 0 0 1 0 1 1 1| rs	| rd	|
POP	L,Ird,Irs		|0 0 0 1 0 1 0 1| rs	| rd	|

POP	Adr,Irs			|0 1 0 1 0 1 1 1| rs	|0 0 0 0|
POP	L,Adr,Irs		|0 1 0 1 0 1 0 1| rs	|0 0 0 0|

# p157
POP	Xrd,Irs			|0 1 0 1 0 1 1 1| rs	| rd	|
POP	L,Xrd,Irs		|0 1 0 1 0 1 0 1| rs	| rd	|

# p158 NB: page has mistakes
PUSH	Ird,Rs			|1 0 0 1 0 0 1 1| rd	| rs	|
PUSH	L,Ird,Rs		|1 0 0 1 0 0 0 1| rd	| rs	|

PUSH	Ird,Data		|0 0 0 0 1 1 0 1| rd	|1 0 0 1|

PUSH	Ird,Irs			|0 0 0 1 0 0 1 1| rd	| rs	|
PUSH	L,Ird,Irs		|0 0 0 1 0 0 0 1| rd	| rs	|

PUSH	Ird,Adr			|0 1 0 1 0 0 1 1| rd	|0 0 0 0|
PUSH	L,Ird,Adr		|0 1 0 1 0 0 0 1| rd	|0 0 0 0|

# p159
PUSH	Ird,Xrs			|0 1 0 1 0 0 1 1| rd	| rs	|
PUSH	L,Ird,Xrs		|0 1 0 1 0 0 0 1| rd	| rs	|

# p160
RES	W,Rd,Bit		|1 0 1 0 0 0 1|w| rd	| bit	|

RES	W,Ird,Bit		|0 0 1 0 0 0 1|w| rd	| bit	|

RES	W,Adr,Bit		|0 1 1 0 0 0 1|w|0 0 0 0| bit	|

RES	W,Xrd,Bit		|0 1 1 0 0 0 1|w| rd	| bit	|

# p161
RES	Rd,Rs			|0 0 1 0 0 0 1|w|0 0 0 0| rs	|0 0 0 0| rd	|0 0 0 0 0 0 0 0|

# p162
RESFLG	Flags			|1 0 0 0 1 1 0 1| flags	|0 0 1 1|

# p163
RET	>RC,Cc			|1 0 0 1 1 1 1 0 0 0 0 0| cc	|

# p164
RL	W,Rd,Y			|1 0 1 1 0 0 1|w| rd	|0 0|s|0|

# p165
RLC	W,Rd,Y			|1 0 1 1 0 0 1|w| rd	|1 0|s|0|

# p166
RLDB	B,Rbl,Rbs		|1 0 1 1 1 1 1 0| rbs	| rbl	|

# p168
RR	W,Rd,Y			|1 0 1 1 0 0 1|w| rd	|0 1|s|0|

# p169/178
RRC	W,Rd,Y			|1 0 1 1 0 0 1|w| rd	|1 1|s|0|

# p170
RRDB	B,Rbl,Rbs		|1 0 1 1 1 1 0 0| rbs	| rbl	|

# p172
SBC	W,Rd,Rs			|1 0 1 1 0 1 1|w| rs	| rd	|

# p174
SC	Imm8			|0 1 1 1 1 1 1 1| imm8		|

# p176
SDA	W,Rd,Rs			|1 0 1 1 0 0 1|w| rd	|1 0 1 1|0 0 0 0| rs	|0 0 0 0 0 0 0 0|
SDA	L,Rd,Rs			|1 0 1 1 0 0 1 1| rd	|1 1 1 1|0 0 0 0| rs	|0 0 0 0 0 0 0 0|

# p178
SDL	W,Rd,Rs			|1 0 1 1 0 0 1|w| rd	|0 0 1 1|0 0 0 0| rs	|0 0 0 0 0 0 0 0|
SDL	L,Rd,Rs			|1 0 1 1 0 0 1 1| rd	|0 1 1 1|0 0 0 0| rs	|0 0 0 0 0 0 0 0|

# p179
SET	W,Rd,Bit		|1 0 1 0 0 1 0|w| rd	| bit	|

SET	W,Ird,Bit		|0 0 1 0 0 1 0|w| rd	| bit	|

SET	W,Adr,Bit		|0 1 1 0 0 1 0|w|0 0 0 0| bit	|

SET	W,Xrd,Bit		|0 1 1 0 0 1 0|w| rd	| bit	|

# p180
SET	W,Rd,Bit		|0 0 1 0 0 1 0|w|0 0 0 0| rs	|0 0 0 0| rd	|0 0 0 0 0 0 0 0|

# p181
SETFLG	Flags			|1 0 0 0 1 1 0 1| flags	|0 0 0 1|

# p183
SxA	W,Rd,Sbit		|1 0 1 1 0 0 1|w| rd	|1 0 0 1| b				|
SxA	L,Rd,Sbit		|1 0 1 1 0 0 1 1| rd	|1 1 0 1| b				|

# p185
SxL	W,Rd,Sbit		|1 0 1 1 0 0 1|w| rd	|0 0 0 1| b				|
SxL	L,Rd,Sbit		|1 0 1 1 0 0 1 1| rd	|0 1 0 1| b				|

# p187 see p183 "SxA"

# p189 see p185 "SxL"

# p190
SUB	W,Rd,Rs			|1 0 0 0 0 0 1|w| rs	| rd	|
SUB	L,Rd,Rs			|1 0 0 1 0 0 1 0| rs	| rd	|

SUB	W,Rd,Data		|0 0 0 0 0 0 1|w|0 0 0 0| rd	|
SUB	L,Rd,Data		|0 0 0 1 0 0 1 0 0 0 0 0| rd	|

SUB	W,Rd,Irs		|0 0 0 0 0 0 1|w| rs	| rd	|
SUB	L,Rd,Irs		|0 0 0 1 0 0 1 0| rs	| rd	|

# p191
SUB	W,Rd,Adr		|0 1 0 0 0 0 1|w|0 0 0 0| rd	|
SUBL	L,Rd,Adr		|0 1 0 1 0 0 1 0|0 0 0 0| rd	|

SUB	W,Rd,Xrs		|0 1 0 0 0 0 1|w| rs	| rd	|
SUB	L,Rd,Xrs		|0 1 0 1 0 0 1 0| rs	| rd	|

# p192
TCC	Cc,Rd			|1 0 1 0 1 1 1|w| rd	| cc	|

# p193
TEST	W,Rd			|1 0 0 0 1 1 0|w| rd	|0 1 0 0|
TEST	L,Rd			|1 0 0 1 1 1 0 0| rd	|1 0 0 0|

TEST	W,Ird			|0 0 0 0 1 1 0|w| rd	|0 1 0 0|
TEST	L,Ird			|0 0 0 1 1 1 0 0| rd	|1 0 0 0|

TEST	W,Adr			|0 1 0 0 1 1 0|w|0 0 0 0|0 1 0 0|
TEST	L,Adr			|0 1 0 1 1 1 0 0 0 0 0 0 1 0 0 0|

# p194
TEST	W,Xrd			|0 1 0 0 1 1 0|w| rd	|0 1 0 0|
TEST	L,Xrd			|0 1 0 1 1 1 0 0| rd	|1 0 0 0|

# p195
TRDB	Ird,Irs,R		|1 0 1 1 1 0 0 0| rd	|1 0 0 0|0 0 0 0| r	| rs	|0 0 0 0|

# p196
TRDRB	Ird,Irs,R		|1 0 1 1 1 0 0 0| rd	|1 1 0 0|0 0 0 0| r	| rs	|0 0 0 0|

# p198
TRIB	Ird,Irs,R		|1 0 1 1 1 0 0 0| rd	|0 0 0 0|0 0 0 0| r	| rs	|0 0 0 0|

# p200
TRIRB	Ird,Irs,R		|1 0 1 1 1 0 0 0| rd	|0 1 0 0|0 0 0 0| r	| rs	|0 0 0 0|

# p202
TRTDB	Irs,Irs2,R		|1 0 1 1 1 0 0 0| rs	|1 0 1 0|0 0 0 0| r	| rs2	|0 0 0 0|

# p203
TRTDRB	Irs,Irs2,R		|1 0 1 1 1 0 0 0| rs	|1 1 1 0|0 0 0 0| r	| rs2	|1 1 1 0|

# p205
TRTIB	Ird,Irs,R		|1 0 1 1 1 0 0 0| rd	|0 0 1 0|0 0 0 0| r	| rs	|0 0 0 0|

# p207
TRTIRB	Ird,Irs,R		|1 0 1 1 1 0 0 0| rd	|0 1 1 0|0 0 0 0| r	| rs	|1 1 1 0|

# p209
TSET	W,Rd			|1 0 0 0 1 1 0|w| rd	|0 1 1 0|

TSET	W,Ird			|0 0 0 0 1 1 0|w| rd	|0 1 1 0|

TSET	W,Adr			|0 1 0 0 1 1 0|w|0 0 0 0|0 1 1 0|

TSE	W,Xrd			|0 1 0 0 1 1 0|w| rd	|0 1 1 0|

# p211
XOR	W,Rd,Rs			|1 0 0 0 1 0 0|w| rs	| rd	|

XOR	W,Rd,Data		|0 0 0 0 1 0 0|w|0 0 0 0| rd	|

XOR	W,Rd,Irs		|0 0 0 0 1 0 0|w| rs	| rd	|

XOR	W,Rd,Adr		|0 1 0 0 1 0 0|w|0 0 0 0| rd	|

XOR	W,Rd,Xrs		|0 1 0 0 1 0 0|w| rs	| rd	|

# p213
E2M	-			|mod|0 0 1 1 1 1| dst	|1 1|x1	|x2			| n	|
M2E	-			|mod|0 0 1 1 1 1| src	|0 1|x1	|x2			| n	|
E2C	-			|1 0 0 0 1 1 1 1| x1	|0 0|x2	|x3	| dst	| x4	| n	|
C2E	-			|1 0 0 0 1 1 1 1|0| x1	|1 0|x2	|x3	| src	| x4	| n	|
E2F	-			|1 0 0 0 1 1 1 0| x1	|0 0|x2	|x3	|0 0 0 0| x4	|0 0 0 0|
F2E	-			|1 0 0 0 1 1 1 0| x1	|1 0|x2	|x3	|0 0 0 0| x4	|0 0 0 0|
E2E	-			|1 0 0 0 1 1 1 0| x1	|0 1|x2 |x3			| n	|

##				|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|
'''

class z8000_ins(assy.Instree_ins):

    def __init__(self, lim, lang):
        super().__init__(lim, lang)
        self.word = 1

    def assy_Adr(self):
        return self.adr()

    def assy_B(self):
        self.word = 0
        self.mne += "B"

    def assy_Bard(self):
        return self.dreg(self['rd']) + "(#0x%x)" % self['disp']

    def assy_Bars(self):
        return self.dreg(self['rs']) + "(#0x%x)" % self['disp']

    def assy_Bit(self):
        return "#%d" % self['bit']

    def assy_Cc(self):
        cc = {
            0: False,
            8: True,
            1: "LT",
            9: "GE",
            2: "LE",
            10: "GT",
            3: "UGT",
            11: "ULE",
            4: "OV",
            12: "NOV",
            5: "MI",
            13: "PL",
            6: "Z",
            14: "NZ",
            7: "C",
            15: "NC",
        }.get(self['cc'])
        if isinstance(cc, str):
            return cc
        elif cc is False:
            for i in range(len(self.flow_out)):
                if self.flow_out[i].to != self.hi:
                    self.flow_out.pop(i)
                    break
        else:
            for i in range(len(self.flow_out)):
                if self.flow_out[i].to == self.hi:
                    self.flow_out.pop(i)
                    break

    def assy_Ctl(self):
        n = {
            0x2: "FCW",
            0x3: "REFRESH",
            0x4: "PSAPSEG",
            0x5: "PSAPOFF",
            0x6: "NSPSEG",
            0x7: "NSPOFF",
        }.get(self['ctl'])
        if n:
            return n
        raise assy.Invalid("CTL REG 0x%x" % self['ctl'])

    def assy_Data(self):
        d = self.lang.as_mem.bu16(self.hi)
        self.hi += 2
        if not self.word:
            #if (d >> 8) != (d & 0xff):
            #    raise assy.Invalid("dataL != dataH")
            return "#0x%x" % (d & 0xff)
        if self.word == 2:
            d <<= 16
            d |= self.lang.as_mem.bu16(self.hi)
            self.hi += 2
        return "#0x%x" % d

    def assy_Disp(self):
        d = self['disp']
        if d & 0x8000:
            d -= 0x10000
        return "0x%x" % (d + self.hi)

    def assy_Imm4(self):
        return "#0x%x" % self['imm4']

    def assy_Imm8(self):
        return "#0x%x" % self['imm8']

    def assy_Ird(self):
        r = self['rd']
        if not r:
            raise assy.Invalid("RD = 0")
        return "@RR%d" % r

    def assy_Irs(self):
        r = self['rs']
        if not r:
            raise assy.Invalid("RS = 0")
        return "@RR%d" % r

    def assy_L(self):
        self.mne += "L"
        self.word = 2

    def assy_N(self):
        return "#0x%x" % (self['n'] + 1)

    def assy_Nvi(self):
        if not self['n']:
            return "NVI"

    def assy_Port(self):
        if self['s']:
            return assy.Arg_dst(self.lang.as_sio, self['port'])
        return assy.Arg_dst(self.lang.as_io, self['port'])

    def reg(self, r):
        if self.word == 2:
            return "RR%d" % r
        if self.word:
            return "R%d" % r
        if r & 8:
            return "RL%d" % (r & 7)
        return "RH%d" % (r & 7)

    def assy_Q(self):
        if not self['q']:
            self.word = 2

    def assy_Qd(self):
        if self.word == 2:
            return "RQ%d" % self['rd']
        else:
            return "RR%d" % self['rd']

    def assy_R(self):
        return "R%d" % self['r']

    def assy_Rd(self):
        return self.reg(self['rd'])

    def assy_Rel7(self):
        d = self['disp'] << 1
        self.dstadr = self.hi - d
        return assy.Arg_dst(self.lang.as_mem, self.dstadr)

    def assy_Rel8(self):
        d = self['disp']
        if d & 0x80:
            d -= 0x100
        self.dstadr = self.hi + d * 2
        return assy.Arg_dst(self.lang.as_mem, self.dstadr)

    def assy_Rs(self):
        return self.reg(self['rs'])

    def assy_S(self):
        if self['s']:
            self.mne = "S" + self.mne

    def assy_Sbit(self):
        d = self['b']
        if d & 0x8000:
            self.mne = self.mne.replace('x', 'R')
            return '#%d' % ((1<<16) - d)
        self.mne = self.mne.replace('x', 'L')
        return '#%d' % d

    def assy_Sd(self):
        return 'R' + self.reg(self['rd'])

    def assy_Vi(self):
        if not self['v']:
            return "VI"

    def assy_W(self):
        self.word = self['w']
        if not self.word:
            self.mne += "B"

    def assy_Xrd(self):
        return self.adr() + "(R%d)" % self['rd']

    def assy_Xrs(self):
        return self.adr() + "(R%d)" % self['rs']

    def assy_Y(self):
        return "#%d" % (self['s'] + 1)


class z8001_ins(z8000_ins):

    def dreg(self, rn):
        return "RR%d" % rn

    def seg(self):
        a1 = self.lang.as_mem.bu16(self.hi)
        self.hi += 2
        if a1 < 0x8000:
            return (a1 >> 8, a1 & 0xff)
        a2 = self.lang.as_mem.bu16(self.hi)
        self.hi += 2
        return ((a1 >> 8) & 0x7f, a2)

    def adr(self):
        a1, a2 = self.seg()
        return "0x%x:0x%x" % (a1, a2)

    def assy_Dst(self):
        a1, a2 = self.seg()
        self.dstadr = a2    # XXX
        return assy.Arg_dst(self.lang.as_mem, self.dstadr)


class z8001(assy.Instree_disass):

    def __init__(self):
        super().__init__(
            "z8001",
            ins_word=16,
            mem_word=8,
            endian=">",
            abits=7+16,
        )
        self.add_as("io", "I/O", 16)
        self.add_as("sio", "Special I/O", 16)
        self.add_ins(z8000_desc, z8001_ins)

    def dataptr(self, adr):
        y = data.Dataptr(self.m, adr, adr + 4, self.m.bu32(adr) & 0x7f00ffff)
        return y

    def codeptr(self, adr):
        y = data.Codeptr(self.m, adr, adr + 4, self.m.bu32(adr) & 0x7f00ffff)
        self.disass(y.dst)
        return y

    def vector(self, a, n):
        self.m.set_label(a, n + "_RSV")
        data.Const(self.m, a, a + 2, func=self.as_mem.bu16, size=2, fmt="0x%04x")
        a += 2
        self.m.set_label(a, n + "_PSW")
        data.Const(self.m, a, a + 2, func=self.as_mem.bu16, size=2, fmt="0x%04x")
        a += 2
        y = self.codeptr(a)
        self.m.set_label(y.dst, n + "_VEC")
        return y.dst

    def vectors(self, adr=0, psap=0):
        self.vector(adr, "RESET")

    def z8010_mmu(self, adrlo):
        ''' Add Z8010 MMU symbols for SIO instructions '''
        p = "Z8010_%02X_" % adrlo
        self.as_sio.set_label(0x0000 + adrlo, p + "MODE_REG")
        self.as_sio.set_label(0x0100 + adrlo, p + "SEG_ADR")
        self.as_sio.set_label(0x0200 + adrlo, p + "VIOLATION_TYPE")
        self.as_sio.set_label(0x0300 + adrlo, p + "VIOLATION_SEG")
        self.as_sio.set_label(0x0400 + adrlo, p + "VIOLATION_OFF")
        self.as_sio.set_label(0x0500 + adrlo, p + "BUS_STATUS")
        self.as_sio.set_label(0x0600 + adrlo, p + "INS_SEG")
        self.as_sio.set_label(0x0700 + adrlo, p + "INS_OFF_HI")
        self.as_sio.set_label(0x0800 + adrlo, p + "BASE")
        self.as_sio.set_label(0x0900 + adrlo, p + "LIMIT")
        self.as_sio.set_label(0x0a00 + adrlo, p + "ATTR")
        self.as_sio.set_label(0x0b00 + adrlo, p + "DESC")
        self.as_sio.set_label(0x0c00 + adrlo, p + "BASE++")
        self.as_sio.set_label(0x0d00 + adrlo, p + "LIMIT++")
        self.as_sio.set_label(0x0e00 + adrlo, p + "ATTR++")
        self.as_sio.set_label(0x0f00 + adrlo, p + "DESCRIPTOR++")
        self.as_sio.set_label(0x1100 + adrlo, p + "RESET_VIOLATION_TYPE")
        self.as_sio.set_label(0x1300 + adrlo, p + "RESET_SWW_IN_VTR")
        self.as_sio.set_label(0x1400 + adrlo, p + "RESET_FATL_IN_VTR")
        self.as_sio.set_label(0x1500 + adrlo, p + "SET_ALL_CPU_INHIBIT")
        self.as_sio.set_label(0x1600 + adrlo, p + "SET_ALL_DMA_INHIBIT")
        self.as_sio.set_label(0x2000 + adrlo, p + "DESC_SEL_CTR")
