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
# 2. Redistributions in binary fo rm  must reproduce the above copyright
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
Disassembler for Intel i8086 microprocessor
"""

from __future__ import print_function

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join("..")))

import pyreveng
import instree
import assy
import binutils

i8086_instructions="""
#		|- - - - - - - -|- - - - - - - -|- - - - - - - -|
MOV	r,ea	|1 0 0 0 1 0|0|w|mod| reg | rm  |
MOV	ea,r	|1 0 0 0 1 0|1|w|mod| reg | rm  |
MOV	i1,ea	|1 1 0 0 0 1 1|0|mod|0 0 0| rm  | i1		|
MOV	i2,ea	|1 1 0 0 0 1 1|1|mod|0 0 0| rm  | i1		| i2		|
MOV	i1,r1	|1 0 1 1|0| reg | i1		|
MOV	i2,r2	|1 0 1 1|1| reg | i1		| i2		|
MOV	da,a	|1 0 1 0 0 0 0|w| alo		| ahi		|
MOV	a,da	|1 0 1 0 0 0 1|w| alo		| ahi		|
MOV	W,ea,sr	|1 0 0 0 1 1 1 0|mod|0| sr| rm  |
MOV	W,sr,ea	|1 0 0 0 1 1 0 0|mod|0| sr| rm  |
PUSH	W,ea	|1 1 1 1 1 1 1 1|mod|1 1 0| rm  |
PUSH	r2	|0 1 0 1 0| reg |
PUSH	sr	|0 0 0|sr |1 1 0|
POP	W,ea	|1 0 0 0 1 1 1 1|mod|0 0 0| rm  |
POP	r2	|0 1 0 1 1| reg |
POP	sr	|0 0 0|sr |1 1 1|
XCHG	r,ea	|1 0 0 0 0 1 1|w|mod| reg | rm  |
XCHG	W,a,r2	|1 0 0 1 0| reg	|
NOP	-	|1 0 0 1 0 0 0 0|
IN	i1,a	|1 1 1 0 0 1 0|w| i1		|
IN	dx,a	|1 1 1 0 1 1 0|w|
OUT	a,i1	|1 1 1 0 0 1 1|w| i1		|
OUT	a,dx	|1 1 1 0 1 1 1|w|
XLAT	-	|1 1 0 1 0 1 1 1|
LEA	W,ea,r	|1 0 0 0 1 1 0 1|mod| reg | rm  |
LDS	W,ea,r	|1 1 0 0 0 1 0 1|mod| reg | rm  |
LES	W,ea,r	|1 1 0 0 0 1 0 0|mod| reg | rm  |
LAHF	-	|1 0 0 1 1 1 1 1|
SAHF	-	|1 0 0 1 1 1 1 0|
PUSHF	-	|1 0 0 1 1 1 0 0|
POPF	-	|1 0 0 1 1 1 0 1|
#
ADD	S,r,ea	|0 0 0 0 0 0|0|w|mod| reg | rm  |
ADD	S,ea,r	|0 0 0 0 0 0|1|w|mod| reg | rm  |
ADD	W,i2,ea	|1 0 0 0 0 0|0|1|mod|0 0 0| rm  | i1		| i2		|
ADD	i1,ea	|1 0 0 0 0 0|s|w|mod|0 0 0| rm  | i1		|
ADD	W,i2,a	|0 0 0 0 0 1 0|1| i1		| i2		|
ADD	B,i1,a	|0 0 0 0 0 1 0|0| i1		|
#
ADC	r,ea	|0 0 0 1 0 0|0|w|mod| reg | rm  |
ADC	ea,r	|0 0 0 1 0 0|1|w|mod| reg | rm  |
ADC	W,i2,ea	|1 0 0 0 0 0|0|1|mod|0 1 0| rm  | i1		| i2		|
ADC	i1,ea	|1 0 0 0 0 0|s|w|mod|0 1 0| rm  | i1		|
ADC	W,i2,a	|0 0 0 1 0 1 0|1| i1		| i2		|
ADC	B,i1,a	|0 0 0 1 0 1 0|0| i1		|
#
INC	ea	|1 1 1 1 1 1 1|w|mod|0 0 0| rm  |
INC	r2	|0 1 0 0 0| reg |
#
AAA	-	|0 0 1 1 0 1 1 1|
BAA	-	|0 0 1 0 0 1 1 1|
#
SUB	r,ea	|0 0 1 0 1 0|0|w|mod| reg | rm  |
SUB	ea,r	|0 0 1 0 1 0|1|w|mod| reg | rm  |
SUB	W,i2,ea	|1 0 0 0 0 0|0|1|mod|1 0 1| rm  | i1		| i2		|
SUB	i1,ea	|1 0 0 0 0 0|s|w|mod|1 0 1| rm  | i1		|
SUB	W,i2,a	|0 0 1 0 1 1 0|1| i1		| i2		|
SUB	B,i1,a	|0 0 1 0 1 1 0|0| i1		|
#
SBB	r,ea	|0 0 0 1 1 0|0|w|mod| reg | rm  |
SBB	ea,r	|0 0 0 1 1 0|1|w|mod| reg | rm  |
SBB	W,i2,ea	|1 0 0 0 0 0|0|1|mod|0 1 1| rm  | i1		| i2		|
SBB	i1,ea	|1 0 0 0 0 0|s|w|mod|0 1 1| rm  | i1		|
SBB	W,i2,a	|0 0 0 1 1 1 0|1| i1		| i2		|
SBB	B,i1,a	|0 0 0 1 1 1 0|0| d1		|
#
DEC	S,ea	|1 1 1 1 1 1 1|w|mod|0 0 1| rm  |
DEC	r2	|0 1 0 0 1| reg |
NEG	ea	|1 1 1 1 0 1 1|w|mod|0 1 1| rm  |
#
CMP	r,ea	|0 0 1 1 1 0|0|w|mod| reg | rm  |
CMP	ea,r	|0 0 1 1 1 0|1|w|mod| reg | rm  |
CMP	W,i2,ea	|1 0 0 0 0 0|0|1|mod|1 1 1| rm  | i1		| i2		|
CMP	i1,ea	|1 0 0 0 0 0|s|w|mod|1 1 1| rm  | i1		|
CMP	W,i2,a	|0 0 1 1 1 1 0|1| i1		| i2		|
CMP	B,i1,a	|0 0 1 1 1 1 0|0| i1		|
#
AAS	-	|0 0 1 1 1 1 1 1|
DAS	-	|0 0 1 0 1 1 1 1|
MUL	S,ea	|1 1 1 1 0 1 1|w|mod|1 0 0| rm  |
IMUL	S,ea	|1 1 1 1 0 1 1|w|mod|1 0 1| rm  |
AAM	-	|1 1 0 1 0 1 0 0|0 0 0 0 1 0 1 0|
DIV	S,ea	|1 1 1 1 0 1 1|w|mod|1 1 0| rm  |
IDIV	S,ea	|1 1 1 1 0 1 1|w|mod|1 1 1| rm  |
AAD	-	|1 1 0 1 0 1 0 1|0 0 0 0 1 0 1 0|
CBW	-	|1 0 0 1 1 0 0 0|
CWD	-	|1 0 0 1 1 0 0 1|
#
NOT	ea	|1 1 1 1 0 1 1|w|mod|0 1 0| rm	|
SHL	v,ea	|1 1 0 1 0 0|v|w|mod|1 0 0| rm  |
SHR	v,ea	|1 1 0 1 0 0|v|w|mod|1 0 1| rm  |
SAR	v,ea	|1 1 0 1 0 0|v|w|mod|1 1 1| rm  |
ROL	v,ea	|1 1 0 1 0 0|v|w|mod|0 0 0| rm  |
ROR	v,ea	|1 1 0 1 0 0|v|w|mod|0 0 1| rm  |
RCL	v,ea	|1 1 0 1 0 0|v|w|mod|0 1 0| rm  |
RCR	v,ea	|1 1 0 1 0 0|v|w|mod|0 1 1| rm  |
#
AND	r,ea	|0 0 1 0 0 0|0|w|mod| reg | rm  |
AND	ea,r	|0 0 1 0 0 0|1|w|mod| reg | rm  |
AND	W,i2,ea	|1 0 0 0 0 0|0|1|mod|1 0 0| rm  | i1		| i2		|
AND	i1,ea	|1 0 0 0 0 0|s|w|mod|1 0 0| rm  | i1		|
AND	W,i2,a	|0 0 1 0 0 1 0|1| i1		| i2		|
AND	B,i1,a	|0 0 1 0 0 1 0|0| i1		|
#
TEST	r,ea	|1 0 0 0 0 1|0|w|mod| reg | rm  |
TEST	W,i2,ea	|1 1 1 1 0 1|1|1|mod|0 0 0| rm  | i1		| i2		|
TEST	B,i1,ea	|1 1 1 1 0 1|1|0|mod|0 0 0| rm  | i1		|
TEST	W,i2,a	|1 0 1 0 1 0 0|1| i1		| i2		|
TEST	B,i1,a	|1 0 1 0 1 0 0|0| i1		|
#
OR	r,ea	|0 0 0 0 1 0|0|w|mod| reg | rm  |
OR	ea,r	|0 0 0 0 1 0|1|w|mod| reg | rm  |
OR	W,i2,ea	|1 0 0 0 0 0|0|1|mod|0 0 1| rm  | i1		| i2		|
OR	i1,ea	|1 0 0 0 0 0|s|w|mod|0 0 1| rm  | i1		|
OR	W,i2,a	|0 0 0 0 1 1 0|1| i1		| i2		|
OR	B,i1,a	|0 0 0 0 1 1 0|0| i1		|
#
XOR	r,ea	|0 0 1 1 0 0|0|w|mod| reg | rm  |
XOR	ea,r	|0 0 1 1 0 0|1|w|mod| reg | rm  |
#XOR	-	|1 0 0 0 0 0|0|1|mod|1 1 0| rm  | d1		| d2		|
#XOR	-	|1 0 0 0 0 0|s|w|mod|1 1 0| rm  | d1		|
XOR	W,i2,a	|0 0 1 1 0 1 0|1| i1		| i2		|
XOR	B,ii,a	|0 0 1 1 0 1 0|0| i1		|
#
REPNZ	-	|1 1 1 1 0 0 1|0|
REP	-	|1 1 1 1 0 0 1|1|
MOVS	S	|1 0 1 0 0 1 0|w|
CMPS	S	|1 0 1 0 0 1 1|w|
SCAS	S	|1 0 1 0 1 1 1|w|
LODS	S	|1 0 1 0 1 1 0|w|
STOS	S	|1 0 1 0 1 0 1|w|
#
CALL	Rel,>C	|1 1 1 0 1 0 0 0| i1		| i2		|
CALL	ea,>C	|1 1 1 1 1 1 1 1|mod|0 1 0| rm  |
CALL	ipcs,>C	|1 0 0 1 1 0 1 0| alo		| ahi		| slo		| shi		|
CALL	ea,>C	|1 1 1 1 1 1 1 1|mod|0 1 1| rm	|
#
JMP	Rel,>J	|1 1 1 0 1 0 0 1| i1		| i2		|
JMP	rel,>J	|1 1 1 0 1 0 1 1| disp		|
JMP	W,ea,>J	|1 1 1 1 1 1 1 1|mod|1 0 0| rm  |
JMP	ipcs,>J	|1 1 1 0 1 0 1 0| alo		| ahi		| slo		| shi		|
LJMP	W,ea,>J	|1 1 1 1 1 1 1 1|mod|1 0 1| rm	|
#
RET	>R	|1 1 0 0 0 0 1 1|
RET	i2,>R	|1 1 0 0 0 0 1 0| i1		| i2		|
LRET	>R	|1 1 0 0 1 0 1 1|
LRET	i2,>R	|1 1 0 0 1 0 1 0| i1		| i2		|
#
JZ	rel,>JC	|0 1 1 1 0 1 0 0| disp		|
JL	rel,>JC	|0 1 1 1 1 1 0 0| disp		|
JLE	rel,>JC	|0 1 1 1 1 1 1 0| disp		|
JB	rel,>JC	|0 1 1 1 0 0 1 0| disp		|
JBE	rel,>JC	|0 1 1 1 0 1 1 0| disp		|
JP	rel,>JC	|0 1 1 1 1 0 1 0| disp		|
JO	rel,>JC	|0 1 1 1 0 0 0 0| disp		|
JS	rel,>JC	|0 1 1 1 1 0 0 0| disp		|
JNZ	rel,>JC	|0 1 1 1 0 1 0 1| disp		|
JGE	rel,>JC	|0 1 1 1 1 1 0 1| disp		|
JG	rel,>JC	|0 1 1 1 1 1 1 1| disp		|
JAE	rel,>JC	|0 1 1 1 0 0 1 1| disp		|
JA	rel,>JC	|0 1 1 1 0 1 1 1| disp		|
JNP	rel,>JC	|0 1 1 1 1 0 1 1| disp		|
JNO	rel,>JC	|0 1 1 1 0 0 0 1| disp		|
JNS	rel,>JC	|0 1 1 1 1 0 0 1| disp		|
LOOP	rel,>JC	|1 1 1 0 0 0 1 0| disp		|
LOOPZ	rel,>JC	|1 1 1 0 0 0 0 1| disp		|
LOOPNZ	rel,>JC	|1 1 1 0 0 0 0 0| disp		|
JCXZ	rel,>JC	|1 1 1 0 0 0 1 1| disp		|
INT	>C	|1 1 0 0 1 1 0 1| type		|
INT3	>C	|1 1 0 0 1 1 0 0|
INTO	>C	|1 1 0 0 1 1 1 0|
IRET	>R	|1 1 0 0 1 1 1 1|
#
CLC	-	|1 1 1 1 1 0 0 0|
CMC	-	|1 1 1 1 0 1 0 1|
STC	-	|1 1 1 1 1 0 0 1|
CLD	-	|1 1 1 1 1 1 0 0|
STD	-	|1 1 1 1 1 1 0 1|
CLI	-	|1 1 1 1 1 0 1 0|
STI	-	|1 1 1 1 1 0 1 1|
HLT	-	|1 1 1 1 0 1 0 0|
WAIT	-	|1 0 0 1 1 0 1 1|
ESC	-	|1 1 0 1 1| xxx |mod| yyy | rm  |
#LOCK	-	|1 1 1 1 0 0 0 0|

+	es		|0 0 1|0 0|1 1 0|
+	cs		|0 0 1|0 1|1 1 0|
+	ss		|0 0 1|1 0|1 1 0|
+	ds		|0 0 1|1 1|1 1 0|

"""

i8087_instructions = """
FLDa	mf,ea	|1 1 0 1 1|mf |1|mod|0 0 0| rm	|
FLDb	ea	|1 1 0 1 1|1 1 1|mod|1 0 1| rm	|
FLDc	ea	|1 1 0 1 1|0 1 1|mod|1 0 1| rm	|
FLDd	ea	|1 1 0 1 1|1 1 1|mod|1 0 0| rm	|
FLDe	st	|1 1 0 1 1|0 0 1|1 1 0 0 0| st  |

FSTa	mf,ea	|1 1 0 1 1|mf |1|mod|0 1 0| rm	|
FSTb	st	|1 1 0 1 1|1 0 1|1 1 0 1 0| st  |

FSTPa	mf,ea	|1 1 0 1 1|mf |1|mod|0 1 1| rm	|
FSTPb	ea	|1 1 0 1 1|1 1 1|mod|1 1 1| rm	|
FSTPc	ea	|1 1 0 1 1|0 1 1|mod|1 1 1| rm	|
FSTPd	ea	|1 1 0 1 1|1 1 1|mod|1 1 0| rm	|
FSTPe	st	|1 1 0 1 1|1 0 1|1 1 0 1 1| st  |

FXCH	st	|1 1 0 1 1|0 0 1|1 1 0 0 1| st	|

FCOMa	mf,ea	|1 1 0 1 1|mf |0|mod|0 1 0| rm	|
FCOMb	st	|1 1 0 1 1|0 0 0|1 1 0 1 0| st  |

FCOMPa	mf,ea	|1 1 0 1 1|mf |0|mod|0 1 1| rm	|
FCOMPb	st	|1 1 0 1 1|0 0 0|1 1 0 1 1| st	|

FCOMPP	-	|1 1 0 1 1|1 1 0|1 1 0 1 1 0 0 1|
FTST	-	|1 1 0 1 1|0 0 1|1 1 1 0 0 1 0 0|
FXAM	-	|1 1 0 1 1|0 0 1|1 1 1 0 0 1 0 1|

FLDZ	-	|1 1 0 1 1|0 0 1|1 1 1 0 1 1 1 0|
FLD1	-	|1 1 0 1 1|0 0 1|1 1 1 0 1 0 0 0|
FLPI	-	|1 1 0 1 1|0 0 1|1 1 1 0 1 0 1 1|
FLDL2T	-	|1 1 0 1 1|0 0 1|1 1 1 0 1 0 0 1|
FLDL2E	-	|1 1 0 1 1|0 0 1|1 1 1 0 1 0 1 0|
FLDLG2	-	|1 1 0 1 1|0 0 1|1 1 1 0 1 1 0 0|
FLDLN2	-	|1 1 0 1 1|0 0 1|1 1 1 0 1 1 0 1|

FADDa	mf,ea	|1 1 0 1 1|mf |0|mod|0 0 0| rm	|
FADDb	st	|1 1 0 1 1|d|P|0|1 1 0 0 0| st	|

FSUBa	mf,ea	|1 1 0 1 1|mf |0|mod|1 0|R| rm	|
FSUBb	st	|1 1 0 1 1|d|P|0|1 1 1 0|R| st	|

FMULa	mf,ea	|1 1 0 1 1|mf |0|mod|0 0 1| rm	|
FMULb	st	|1 1 0 1 1|d|P|0|1 1 0 0 1| st	|

FDIVa	mf,ea	|1 1 0 1 1|mf |0|mod|1 1|R| rm	|
FDIVb	st	|1 1 0 1 1|d|P|0|1 1 1 1|R| st	|

FSQRT	-	|1 1 0 1 1|0 0 1|1 1 1 1 1 0 1 0|
FSCALE	-	|1 1 0 1 1|0 0 1|1 1 1 1 1 1 0 1|
FPREM	-	|1 1 0 1 1|0 0 1|1 1 1 1 1 0 0 0|
FRNDINT	-	|1 1 0 1 1|0 0 1|1 1 1 1 1 1 0 0|
FXTRACT	-	|1 1 0 1 1|0 0 1|1 1 1 1 0 1 0 0|
FABS	-	|1 1 0 1 1|0 0 1|1 1 1 0 0 0 0 1|
FCHS	-	|1 1 0 1 1|0 0 1|1 1 1 0 0 0 0 0|

FPTAN	-	|1 1 0 1 1|0 0 1|1 1 1 1 0 0 1 0|
FPATAN	-	|1 1 0 1 1|0 0 1|1 1 1 1 0 0 1 1|
F2XM1	-	|1 1 0 1 1|0 0 1|1 1 1 1 0 0 0 0|
FYL2X	-	|1 1 0 1 1|0 0 1|1 1 1 1 0 0 0 1|
FYL2XP1	-	|1 1 0 1 1|0 0 1|1 1 1 1 1 0 0 1|

FINIT	-	|1 1 0 1 1|0 1 1|1 1 1 0 0 0 1 1|
FENI	-	|1 1 0 1 1|0 1 1|1 1 1 0 0 0 0 0|
FDISI	-	|1 1 0 1 1|0 1 1|1 1 1 0 0 0 0 1|
FLDCW	ea	|1 1 0 1 1|0 0 1|mod|1 0 1| rm	|
FSTCW	ea	|1 1 0 1 1|0 0 1|mod|1 1 1| rm	|
FSTSW	ea	|1 1 0 1 1|1 0 1|mod|1 1 1| rm	|
FCLEX	-	|1 1 0 1 1|0 1 1|1 1 1 0 0 0 1 0|
FSTENV	ea	|1 1 0 1 1|0 0 1|mod|1 1 0| rm	|
FLDENV	ea	|1 1 0 1 1|0 0 1|mod|1 0 0| rm	|
FSAVE	ea	|1 1 0 1 1|1 0 1|mod|1 1 0| rm	|
FRSTOR	ea	|1 1 0 1 1|1 0 1|mod|1 0 0| rm	|

FINCSTP	-	|1 1 0 1 1|0 0 1|1 1 1 1 0 1 1 1|
FDECSTP	-	|1 1 0 1 1|0 0 1|1 1 1 1 0 1 1 0|

FFREE	st	|1 1 0 1 1|1 0 1|1 1 0 0 0| st	|
FNOP	-	|1 1 0 1 1|0 0 1|1 1 0 1 0 0 0 0|

# FWAIT	-	|1 0 0 1 1 0 1 1|
"""

def fixup_mod_reg_rm(ins):
	ins_list = []
	for i in ins.split("\n"):
		if len(i) == 0 or i[0] == "#":
			continue
		i = i.expandtabs()
		j = i.find("|mod|")
		ins_list.append(i)
		if j >= 0:

			k = i.replace("|mod|", "|0 1|")
			k = k.replace("ea", "e1")
			k = k[:j+16] + "|  dlo          " + k[j+16:]
			ins_list.append(k)

			k = i.replace("|mod|", "|1 0|")
			k = k.replace("ea", "e2")
			k = k[:j+16] + "|  dlo          |  dhi          " + k[j+16:]
			ins_list.append(k)

			k = i.replace("|mod|", "|0 0|")
			k = k.replace("| rm  |", "|1 1 0|")
			k = k.replace("ea", "e3")
			k = k[:j+16] + "|  dlo          |  dhi          " + k[j+16:]
			ins_list.append(k)
	return "\n".join(ins_list)

i8086_instructions = fixup_mod_reg_rm(i8086_instructions)
i8087_instructions = fixup_mod_reg_rm(i8087_instructions)
if __name__ == "__main__":
	import instree
	print(i8086_instructions)
	print(i8087_instructions)
	it = instree.instree(8)
	it.load_string(i8086_instructions)
	it.load_string(i8087_instructions)
	it.print()

wreg = ["%ax","%cx","%dx","%bx","%sp","%bp","%si","%di"]
breg = ["%al","%cl","%dl","%bl","%ah","%ch","%dh","%bh"]
ireg = ["%bx+%si", "%bx+%di", "%bp+%si", "%bp+%di","%si","%di","%bp","%bx"]

class arg_i1(object):
	""" Immediate 8 bit """
	def __init__(self, pj, ins):
		self.value = ins.im.F_i1

	def render(self, pj):
		return "#0x%02x" % self.value

class arg_i2(object):
	""" Immediate 16 bit """
	def __init__(self, pj, ins):
		self.value = ins.im.F_i1 | ins.im.F_i2 << 8

	def render(self, pj):
		return "#0x%04x" % self.value

class arg_da(object):
	""" Direct address """
	def __init__(self, pj, ins):
		self.value = ins.im.F_alo | ins.im.F_ahi << 8

	def render(self, pj):
		return "0x%04x" % self.value


class arg_ipcs(assy.arg_dst):
	""" Long address (seg:off) """
	def __init__(self, pj, ins):
		self.seg = ins.im.F_slo | (ins.im.F_shi << 8)
		ins.dseg = self.seg
		self.off = ins.im.F_alo | (ins.im.F_ahi << 8)
		ins.dstadr = (self.seg << 4) + self.off
		super(arg_ipcs, self).__init__(pj, ins.dstadr)

	def render(self, pj):
		return "0x%04x:0x%04x" % (self.seg, self.off)

class arg_Rel(assy.arg_dst):
	""" Relative address """
	def __init__(self, pj, ins):
		d = ins.im.F_i1 | (ins.im.F_i2 << 8)
		if d & 0x8000:
			d -= 65536
		ins.dstadr = ins.hi + d
		super(arg_Rel, self).__init__(pj, ins.dstadr)

class arg_rel(assy.arg_dst):
	""" Relative address """
	def __init__(self, pj, ins):
		d = ins.im.F_disp
		if d & 0x80:
			d -= 256
		ins.dstadr = ins.hi + d
		super(arg_rel, self).__init__(pj, ins.dstadr)

def arg_cs(pj, ins):
	ins.seg = "%cs:"

def arg_es(pj, ins):
	ins.seg = "%es:"

def arg_ss(pj, ins):
	ins.seg = "%ss:"

def arg_ds(pj, ins):
	ins.seg = "%ds:"

class arg_ea(object):
	""" Effective address """
	def __init__(self, pj, ins):
		self.im = ins.im
		self.seg = ins.seg

	def render(self, pj):
		print("R", self.im)
		s = ""
		s += self.seg
		if self.im.F_mod == 0 and self.im.F_rm == 6:
			dst = self.im.F_dlo | (self.im.F_dhi << 8)
			s += "0x%04x" % dst
		elif self.im.F_mod == 0:
			s += "(" + ireg[self.im.F_rm] + ")"
		elif self.im.F_mod == 1:
			v = self.im.F_dlo
			if v & 0x80:
				s += "-0x%02x+(" % (-v + 256)
			else:
				s += "0x%02x+(" % v
			s += ireg[self.im.F_rm]
			s += ")"
		elif self.im.F_mod == 2:
			v = self.im.F_dlo | self.im.F_dhi << 8
			if v & 0x8000:
				s += "-0x%04x+(" % (-v + 65536)
			else:
				s += "0x%04x+(" % (v)
			s += ireg[self.im.F_rm]
			s += ")"
		elif self.im.F_mod == 3:
			try:
				if self.im.F_w:
					s += wreg[self.im.F_rm]
				else:
					s += breg[self.im.F_rm]
			except:
				s += "*FAIL*miss_w*"
				print(self.im, "missing w")
		else:
			s += "<EA mod=%d r/m=%d>" % (self.im.F_mod, self.im.F_rm)
		return s

class arg_e1(arg_ea):
	""" Effective address 8 bit offset """
	def __init__(self, pj, ins):
		ins.im.F_mod = 1
		super(arg_e1, self).__init__(pj, ins)

class arg_e2(arg_ea):
	""" Effective address 16 bit offset """
	def __init__(self, pj, ins):
		ins.im.F_mod = 2
		super(arg_e2, self).__init__(pj, ins)

class arg_e3(arg_ea):
	""" Effective address -- direct address """
	def __init__(self, pj, ins):
		ins.im.F_mod = 0
		ins.im.F_rm = 6
		super(arg_e3, self).__init__(pj, ins)

def arg_sr(pj, ins):
	""" Segment register """
	return ["%es","%cs","%ss","%ds"][ins.im.F_sr]

def arg_r1(pj, ins):
	""" Byte register """
	return breg[ins.im.F_reg]

def arg_r2(pj, ins):
	""" Word register """
	return wreg[ins.im.F_reg]

def arg_a(pj, ins):
	""" Accumulator """
	if ins.im.F_w:
		return "%ax"
	else:
		return "%al"

def arg_r(pj, ins):
	""" Register """
	if ins.im.F_w:
		return wreg[ins.im.F_reg]
	else:
		return breg[ins.im.F_reg]

def arg_v(pj, ins):
	if ins.im.F_v:
		return "%cl"
	return None

def arg_W(pj, ins):
	""" Instruction is Word sized """
	ins.im.F_w = 1

def arg_B(pj, ins):
	""" Instruction is Byte sized """
	ins.im.F_w = 9

def arg_S(pj, ins):
	""" Mark Byte sized instrustions"""
	if not ins.im.F_w:
		ins.mne += "B"

def arg_dx(pj, ins):
	return "(%dx)"


def arg7_st(pj, ins):
	return "%%st(%d)" % ins.im.F_st

def arg7_mf(pj, ins):
	ins.mne += "fids" [ins.im.F_mf]

import binutils

class i8086(assy.instree_disass):
	def __init__(self):
		super(i8086, self).__init__("i8086", 8)
		self.it.load_string(i8086_instructions)
		self.args.update( {
			"W":	arg_W,
			"B":	arg_B,
			"S":	arg_S,
			"ipcs":	arg_ipcs,
			"cs":	arg_cs,
			"ds":	arg_ds,
			"es":	arg_es,
			"ss":	arg_ss,
			"sr":	arg_sr,
			"e1":	arg_e1,
			"e2":	arg_e2,
			"e3":	arg_e3,
			"ea":	arg_ea,
			"i1":	arg_i1,
			"i2":	arg_i2,
			"da":	arg_da,
			"a":	arg_a,
			"r":	arg_r,
			"v":	arg_v,
			"r1":	arg_r1,
			"r2":	arg_r2,
			"rel":	arg_rel,
			"Rel":	arg_Rel,
			"dx":	arg_dx,
		})

	def has_8087(self):
		self.it.load_string(i8087_instructions)
		self.args.update( {
			"st":	arg7_st,
			"mf":	arg7_mf,
		})

	def init_ins(self, pj, ins):
		ins.seg = ""

	def disass(self, pj, adr):
		y = pj.find(adr, self.name)
		if y != None:
			return False
		if (pj.m.rd(adr) & 0xf8) == 0xd8 or (pj.m.rd(adr + 1) & 0xf8) == 0xd8:
			x = binutils.ask_objdump(pj, adr, "i8086", "i8086")
			ll = len(x[10:30].split())
		else:
			x = ""
			ll = 0
		# print("%05x" % adr)
		b = super(i8086, self).disass(pj, adr)
		if not b:
			y = pj.add(adr, adr + 1, "XXX")
			y.rendered = "FAIL_DISASS"
			if x != "":
				y.lcmt += x + "\n"
			return False
		return (b)
		y = pj.find(adr, self.name)
		if y != "":
			y.lcmt += x + "\n"
		if ll > 0 and y.hi - y.lo != ll:
			print("FAIL", y.render(pj), x)
			return False
		return b
