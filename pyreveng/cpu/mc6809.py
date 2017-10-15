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
Disassembler for MC6809 familiy CPUs.

Presently supported variants:
	6809
"""

from __future__ import print_function

from pyreveng import assy, data

mc6809_instructions = """
NEG	-	|0 0 0 0 0 0 0 0| d		|
COM	d	|0 0 0 0 0 0 1 1| d		|
LSR	d	|0 0 0 0 0 1 0 0| d		|
ROR	d	|0 0 0 0 0 1 1 0| d		|
ASR	d	|0 0 0 0 0 1 1 1| d		|
ASL	d	|0 0 0 0 1 0 0 0| d		|
ROL	d	|0 0 0 0 1 0 0 1| d		|
DEC	d	|0 0 0 0 1 0 1 0| d		|
INC	d	|0 0 0 0 1 1 0 0| d		|
TST	d	|0 0 0 0 1 1 0 1| d		|
JMP	d,>J	|0 0 0 0 1 1 1 0| d		|
CLR	d	|0 0 0 0 1 1 1 1| d		|

BRN	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 0 0 0 1| R1		| R2		|
BHI	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 0 0 1 0| R1		| R2		|
BLS	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 0 0 1 1| R1		| R2		|
BCC	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 0 1 0 0| R1		| R2		|
BCS	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 0 1 0 1| R1		| R2		|
BNE	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 0 1 1 0| R1		| R2		|
BEQ	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 0 1 1 1| R1		| R2		|
BVC	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 1 0 0 0| R1		| R2		|
BVS	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 1 0 0 1| R1		| R2		|
BPL	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 1 0 1 0| R1		| R2		|
BMI	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 1 0 1 1| R1		| R2		|
BGE	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 1 1 0 0| R1		| R2		|
BLT	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 1 1 0 1| R1		| R2		|
BGT	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 1 1 1 0| R1		| R2		|
BLT	R,>JC	|0 0 0 1 0 0 0 0|0 0 1 0 1 1 1 1| R1		| R2		|

SWI2	>J	|0 0 0 1 0 0 0 0|0 0 1 1 1 1 1 1|

CMPD	I	|0 0 0 1 0 0 0 0|1 0 0 0 0 0 1 1| I1		| I2		|
CMPY    I	|0 0 0 1 0 0 0 0|1 0 0 0 1 1 0 0| I1		| I2		|
LDY     I	|0 0 0 1 0 0 0 0|1 0 0 0 1 1 1 0| I1		| I2		|

CMPD	d	|0 0 0 1 0 0 0 0|1 0 0 1 0 0 1 1| d		|
CMPY	d	|0 0 0 1 0 0 0 0|1 0 0 1 1 1 0 0| d		|
LDY	d	|0 0 0 1 0 0 0 0|1 0 0 1 1 1 1 0| d		|
STY	d	|0 0 0 1 0 0 0 0|1 0 0 1 1 1 1 1| d		|

CMPD    P	|0 0 0 1 0 0 0 0|1 0 1 0 0 0 1 1|X| R |i| m     |
CMPY    P	|0 0 0 1 0 0 0 0|1 0 1 0 1 1 0 0|X| R |i| m     |
LDY     P	|0 0 0 1 0 0 0 0|1 0 1 0 1 1 1 0|X| R |i| m     |
STY     P	|0 0 0 1 0 0 0 0|1 0 1 0 1 1 1 1|X| R |i| m     |
CMPD	E	|0 0 0 1 0 0 0 0|1 0 1 1 0 0 1 1| e1		| e2		|
CMPY	E	|0 0 0 1 0 0 0 0|1 0 1 1 1 1 0 0| e1		| e2		|
LDY	E	|0 0 0 1 0 0 0 0|1 0 1 1 1 1 1 0| e1		| e2		|
STY	E	|0 0 0 1 0 0 0 0|1 0 1 1 1 1 1 1| e1		| e2		|

LDS     I	|0 0 0 1 0 0 0 0|1 1 0 0 1 1 1 0| I1		| I2		|

LDS	d	|0 0 0 1 0 0 0 0|1 1 0 1 1 1 1 0| d		|
STS	d	|0 0 0 1 0 0 0 0|1 1 0 1 1 1 1 1| d		|

LDS	P	|0 0 0 1 0 0 0 0|1 1 1 0 1 1 1 0|X| R |i| m     |
STS	P	|0 0 0 1 0 0 0 0|1 1 1 0 1 1 1 1|X| R |i| m     |

SWI3	>J	|0 0 0 1 0 0 0 1|0 0 1 1 1 1 1 1|
CMPU	I	|0 0 0 1 0 0 0 1|1 0 0 0 0 0 1 1| I1		| I2		|
CMPS	I	|0 0 0 1 0 0 0 1|1 0 0 0 1 1 0 0| I1		| I2		|
CMPU	I	|0 0 0 1 0 0 0 1|1 0 0 1 0 0 1 1| d		|
CMPS	I	|0 0 0 1 0 0 0 1|1 0 0 1 1 1 0 0| d		|
CMPU	P	|0 0 0 1 0 0 0 1|1 0 1 0 0 0 1 1|X| R |i| m     |
CMPS	P	|0 0 0 1 0 0 0 1|1 0 1 0 1 1 0 0|X| R |i| m     |
CMPU	E	|0 0 0 1 0 0 0 1|1 0 1 1 0 0 1 1| e1		| e2		|
CMPS	E	|0 0 0 1 0 0 0 1|1 0 1 1 1 1 0 0| e1		| e2		|

NOP	-	|0 0 0 1 0 0 1 0|
SYNC	-	|0 0 0 1 0 0 1 1|
BRA	R,>J	|0 0 0 1 0 1 1 0| R1            | R2		|
BSR	R,>C	|0 0 0 1 0 1 1 1| R1            | R2		|
DAA	-	|0 0 0 1 1 0 0 1|
ORCC	i	|0 0 0 1 1 0 1 0| i		|
ANDCC	i	|0 0 0 1 1 1 0 0| i		|
SEX	-	|0 0 0 1 1 1 0 1|
EXG	t	|0 0 0 1 1 1 1 0| t		|
TFR	t	|0 0 0 1 1 1 1 1| t		|

BRA	r,>J	|0 0 1 0 0 0 0 0| r		|
BRN	r,>JC	|0 0 1 0 0 0 0 1| r		|
BHI	r,>JC	|0 0 1 0 0 0 1 0| r		|
BLS	r,>JC	|0 0 1 0 0 0 1 1| r		|
BCC	r,>JC	|0 0 1 0 0 1 0 0| r		|
BCS	r,>JC	|0 0 1 0 0 1 0 1| r		|
BNE	r,>JC	|0 0 1 0 0 1 1 0| r		|
BEQ	r,>JC	|0 0 1 0 0 1 1 1| r		|
BVC	r,>JC	|0 0 1 0 1 0 0 0| r		|
BVS	r,>JC	|0 0 1 0 1 0 0 1| r		|
BPL	r,>JC	|0 0 1 0 1 0 1 0| r		|
BMI	r,>JC	|0 0 1 0 1 0 1 1| r		|
BGE	r,>JC	|0 0 1 0 1 1 0 0| r		|
BLT	r,>JC	|0 0 1 0 1 1 0 1| r		|
BGT	r,>JC	|0 0 1 0 1 1 1 0| r		|
BLE	r,>JC	|0 0 1 0 1 1 1 1| r		|

LEAX	P	|0 0 1 1 0 0 0 0|X| R |i| m	|
LEAY	P	|0 0 1 1 0 0 0 1|X| R |i| m	|
LEAS	P	|0 0 1 1 0 0 1 0|X| R |i| m     |
LEAU	P	|0 0 1 1 0 0 1 1|X| R |i| m     |
PSHS	s	|0 0 1 1 0 1 0 0| i		|
PULS	s	|0 0 1 1 0 1 0 1| i		|
PSHU	s	|0 0 1 1 0 1 1 0| i		|
PULU	s	|0 0 1 1 0 1 1 1| i		|
RTS	>R	|0 0 1 1 1 0 0 1|
ABX	-	|0 0 1 1 1 0 1 0|
RTI	>R	|0 0 1 1 1 0 1 1|
CWAI	i	|0 0 1 1 1 1 0 0| i		|
MUL	-	|0 0 1 1 1 1 0 1|
SWI	-	|0 0 1 1 1 1 1 1|

NEGA	-	|0 1 0 0 0 0 0 0|
COMA	-	|0 1 0 0 0 0 1 1|
LSRA	-	|0 1 0 0 0 1 0 0|
RORA	-	|0 1 0 0 0 1 1 0|
ASRA	-	|0 1 0 0 0 1 1 1|
ASLA	-	|0 1 0 0 1 0 0 0|
ROLA	-	|0 1 0 0 1 0 0 1|
DECA	-	|0 1 0 0 1 0 1 0|
INCA	-	|0 1 0 0 1 1 0 0|
TSTA	-	|0 1 0 0 1 1 0 1|
CLRA	-	|0 1 0 0 1 1 1 1|

NEGB	-	|0 1 0 1 0 0 0 0|
COMB	-	|0 1 0 1 0 0 1 1|
LSRB	-	|0 1 0 1 0 1 0 0|
RORB	-	|0 1 0 1 0 1 1 0|
ASRB	-	|0 1 0 1 0 1 1 1|
ASLB	-	|0 1 0 1 1 0 0 0|
ROLB	-	|0 1 0 1 1 0 0 1|
DECB	-	|0 1 0 1 1 0 1 0|
INCB	-	|0 1 0 1 1 1 0 0|
TSTB	-	|0 1 0 1 1 1 0 1|
CLRB	-	|0 1 0 1 1 1 1 1|

NEG	P	|0 1 1 0 0 0 0 0|X| R |i| m	|
COM	P	|0 1 1 0 0 0 1 1|X| R |i| m	|
LSR	P	|0 1 1 0 0 1 0 0|X| R |i| m	|
ROR	P	|0 1 1 0 0 1 1 0|X| R |i| m	|
ASR	P	|0 1 1 0 0 1 1 1|X| R |i| m	|
ASL	P	|0 1 1 0 1 0 0 0|X| R |i| m	|
ROL	P	|0 1 1 0 1 0 0 1|X| R |i| m	|
DEC	P	|0 1 1 0 1 0 1 0|X| R |i| m	|
INC	P	|0 1 1 0 1 1 0 0|X| R |i| m	|
TST	P	|0 1 1 0 1 1 0 1|X| R |i| m	|
JMP	P,>J	|0 1 1 0 1 1 1 0|X| R |i| m	|
CLR	P	|0 1 1 0 1 1 1 1|X| R |i| m	|

NEG	E	|0 1 1 1 0 0 0 0| e1		| e2		|
COM	E	|0 1 1 1 0 0 1 1| e1		| e2		|
LSR	E	|0 1 1 1 0 1 0 0| e1		| e2		|
ROR	E	|0 1 1 1 0 1 1 0| e1		| e2		|
ASR	E	|0 1 1 1 0 1 1 1| e1		| e2		|
ASL	E	|0 1 1 1 1 0 0 0| e1		| e2		|
ROL	E	|0 1 1 1 1 0 0 1| e1		| e2		|
DEC	E	|0 1 1 1 1 0 1 0| e1		| e2		|
INC	E	|0 1 1 1 1 1 0 0| e1		| e2		|
TST	E	|0 1 1 1 1 1 0 1| e1		| e2		|
JMP	E,>J	|0 1 1 1 1 1 1 0| e1		| e2		|
CLR	E	|0 1 1 1 1 1 1 1| e1		| e2		|

SUBA	i	|1 0 0 0 0 0 0 0| i		|
CMPA	i	|1 0 0 0 0 0 0 1| i		|
SBCA	i	|1 0 0 0 0 0 1 0| i		|
SUBD	I	|1 0 0 0 0 0 1 1| I1		| I2		|
ANDA	i	|1 0 0 0 0 1 0 0| i		|
BITA	i	|1 0 0 0 0 1 0 1| i		|
LDA	i	|1 0 0 0 0 1 1 0| i		|
EORA	i	|1 0 0 0 1 0 0 0| i		|
ADCA	i	|1 0 0 0 1 0 0 1| i		|
ORA	i	|1 0 0 0 1 0 1 0| i		|
ADDA	i	|1 0 0 0 1 0 1 1| i		|
CMPX	I	|1 0 0 0 1 1 0 0| I1		| I2		|
BSR	r,>C	|1 0 0 0 1 1 0 1| r		|
LDX	I	|1 0 0 0 1 1 1 0| I1		| I2		|

SUBA	d	|1 0 0 1 0 0 0 0| d		|
CMPA	d	|1 0 0 1 0 0 0 1| d		|
SBCA	d	|1 0 0 1 0 0 1 0| d		|
SUBD	d	|1 0 0 1 0 0 1 1| d		|
ANDA	d	|1 0 0 1 0 1 0 0| d		|
BITA	d	|1 0 0 1 0 1 0 1| d		|
LDA	d	|1 0 0 1 0 1 1 0| d		|
STA	d	|1 0 0 1 0 1 1 1| d		|
EORA	d	|1 0 0 1 1 0 0 0| d		|
ADCA	d	|1 0 0 1 1 0 0 1| d		|
ORA	d	|1 0 0 1 1 0 1 0| d		|
ADDA	d	|1 0 0 1 1 0 1 1| d		|
CMPX	d	|1 0 0 1 1 1 0 0| d		|
JSR	d,>C	|1 0 0 1 1 1 0 1| d		|
LDX	d	|1 0 0 1 1 1 1 0| d		|
STX	d	|1 0 0 1 1 1 1 1| d		|

SUBA	P	|1 0 1 0 0 0 0 0|X| R |i| m	|
CMPA	P	|1 0 1 0 0 0 0 1|X| R |i| m	|
SBCA	P	|1 0 1 0 0 0 1 0|X| R |i| m	|
SUBD	P	|1 0 1 0 0 0 1 1|X| R |i| m	|
ANDA	P	|1 0 1 0 0 1 0 0|X| R |i| m	|
BITA	P	|1 0 1 0 0 1 0 1|X| R |i| m	|
LDA	P	|1 0 1 0 0 1 1 0|X| R |i| m	|
STA	P	|1 0 1 0 0 1 1 1|X| R |i| m	|
EORA	P	|1 0 1 0 1 0 0 0|X| R |i| m	|
ADCA	P	|1 0 1 0 1 0 0 1|X| R |i| m	|
ORA	P	|1 0 1 0 1 0 1 0|X| R |i| m	|
ADDA	P	|1 0 1 0 1 0 1 1|X| R |i| m	|
CMPX	P	|1 0 1 0 1 1 0 0|X| R |i| m	|
JSR	P,>C	|1 0 1 0 1 1 0 1|X| R |i| m	|
LDX	P	|1 0 1 0 1 1 1 0|X| R |i| m     |
STX	P	|1 0 1 0 1 1 1 1|X| R |i| m     |

SUBA	E	|1 0 1 1 0 0 0 0| e1		| e2		|
CMPA	E	|1 0 1 1 0 0 0 1| e1		| e2		|
SBCA	E	|1 0 1 1 0 0 1 0| e1		| e2		|
SUBD	E	|1 0 1 1 0 0 1 1| e1		| e2		|
ANDA	E	|1 0 1 1 0 1 0 0| e1		| e2		|
BITA	E	|1 0 1 1 0 1 0 1| e1		| e2		|
LDA	E	|1 0 1 1 0 1 1 0| e1		| e2		|
STA	E	|1 0 1 1 0 1 1 1| e1		| e2		|
EORA	E	|1 0 1 1 1 0 0 0| e1		| e2		|
ADCA	E	|1 0 1 1 1 0 0 1| e1		| e2		|
ORA	E	|1 0 1 1 1 0 1 0| e1		| e2		|
ADDA	E	|1 0 1 1 1 0 1 1| e1		| e2		|
CMPX	E	|1 0 1 1 1 1 0 0| e1		| e2		|
JSR	E,>C	|1 0 1 1 1 1 0 1| e1		| e2		|
LDX	E	|1 0 1 1 1 1 1 0| e1		| e2		|
STX	E	|1 0 1 1 1 1 1 1| e1		| e2		|

SUBB	i	|1 1 0 0 0 0 0 0| i		|
CMPB	i	|1 1 0 0 0 0 0 1| i		|
SBCB	i	|1 1 0 0 0 0 1 0| i		|
ADDD	I	|1 1 0 0 0 0 1 1| I1		| I2		|
ANDB	i	|1 1 0 0 0 1 0 0| i		|
BITB	i	|1 1 0 0 0 1 0 1| i		|
LDB	i	|1 1 0 0 0 1 1 0| i		|
EORB	i	|1 1 0 0 1 0 0 0| i		|
ADCB	i	|1 1 0 0 1 0 0 1| i		|
ORB	i	|1 1 0 0 1 0 1 0| i		|
ADDB	i	|1 1 0 0 1 0 1 1| i		|
LDD	I	|1 1 0 0 1 1 0 0| I1		| I2		|
LDU	I	|1 1 0 0 1 1 1 0| I1		| I2		|

SUBB	d	|1 1 0 1 0 0 0 0| d		|
CMPB	d	|1 1 0 1 0 0 0 1| d		|
SBCB	d	|1 1 0 1 0 0 1 0| d		|
ADDD	d	|1 1 0 1 0 0 1 1| d		|
ANDB	d	|1 1 0 1 0 1 0 0| d		|
BITB	d	|1 1 0 1 0 1 0 1| d		|
LDB	d	|1 1 0 1 0 1 1 0| d		|
STB	d	|1 1 0 1 0 1 1 1| d		|
EORB	d	|1 1 0 1 1 0 0 0| d		|
ADCB	d	|1 1 0 1 1 0 0 1| d		|
ORB	d	|1 1 0 1 1 0 1 0| d		|
ADDB	d	|1 1 0 1 1 0 1 1| d		|
LDD	d	|1 1 0 1 1 1 0 0| d		|
STD	d	|1 1 0 1 1 1 0 1| d		|
LDU	d	|1 1 0 1 1 1 1 0| d		|
STU	d	|1 1 0 1 1 1 1 1| d		|

SUBB	P	|1 1 1 0 0 0 0 0|X| R |i| m     |
CMPB	P	|1 1 1 0 0 0 0 1|X| R |i| m     |
SBCB	P	|1 1 1 0 0 0 1 0|X| R |i| m     |
ADDD	P	|1 1 1 0 0 0 1 1|X| R |i| m     |
ANDB	P	|1 1 1 0 0 1 0 0|X| R |i| m     |
BITB	P	|1 1 1 0 0 1 0 1|X| R |i| m     |
LDB	P	|1 1 1 0 0 1 1 0|X| R |i| m     |
STB	P	|1 1 1 0 0 1 1 1|X| R |i| m     |
EORB	P	|1 1 1 0 1 0 0 0|X| R |i| m     |
ADCB	P	|1 1 1 0 1 0 0 1|X| R |i| m     |
ORB	P	|1 1 1 0 1 0 1 0|X| R |i| m     |
ADDB	P	|1 1 1 0 1 0 1 1|X| R |i| m     |
LDD	P	|1 1 1 0 1 1 0 0|X| R |i| m     |
STD	P	|1 1 1 0 1 1 0 1|X| R |i| m     |
LDU	P	|1 1 1 0 1 1 1 0|X| R |i| m     |
STU	P	|1 1 1 0 1 1 1 1|X| R |i| m     |

SUBB	E	|1 1 1 1 0 0 0 0| e1		| e2		|
CMPB	E	|1 1 1 1 0 0 0 1| e1		| e2		|
SBCB	E	|1 1 1 1 0 0 1 0| e1		| e2		|
ADDD	E	|1 1 1 1 0 0 1 1| e1		| e2		|
ANDB	E	|1 1 1 1 0 1 0 0| e1		| e2		|
BITB	E	|1 1 1 1 0 1 0 1| e1		| e2		|
LDB	E	|1 1 1 1 0 1 1 0| e1		| e2		|
STB	E	|1 1 1 1 0 1 1 1| e1		| e2		|
EORB	E	|1 1 1 1 1 0 0 0| e1		| e2		|
ADCB	E	|1 1 1 1 1 0 0 1| e1		| e2		|
ORB	E	|1 1 1 1 1 0 1 0| e1		| e2		|
ADDB	E	|1 1 1 1 1 0 1 1| e1		| e2		|
LDD	E	|1 1 1 1 1 1 0 0| e1		| e2		|
STD	E	|1 1 1 1 1 1 0 1| e1		| e2		|
LDU	E	|1 1 1 1 1 1 1 0| e1		| e2		|
STU	E	|1 1 1 1 1 1 1 1| e1		| e2		|
"""

mc6809_macro_instructions = """
LDD	i	|1 1 0 0 0 1 1 0| i		|0 0 0 1 1 1 0 1|
CLRD	-	|0 1 0 1 1 1 1 1|0 0 0 1 1 1 0 1|
ANDD	I	|1 0 0 0 0 1 0 0| I1		|1 1 0 0 0 1 0 0| I2		|
ORD	I	|1 0 0 0 1 0 1 0| I1		|1 1 0 0 1 0 1 0| I2		|
CLRD	-	|0 1 0 1 1 1 1 1|0 1 0 0 1 1 1 1|
CLRD	-	|0 1 0 0 1 1 1 1|0 1 0 1 1 1 1 1|
"""

class mc6809_ins(assy.Instree_ins):
	pass

	def assy_d(self, pj):
		return "$0x%02x" % self['d']

	def assy_i(self, pj):
		return "#0x%02x" % self['i']

	def assy_I(self, pj):
		self.dstadr = (self['I1'] << 8) | self['I2']
		return assy.Arg_dst(pj, self.dstadr, "#")

	def assy_E(self, pj):
		self.dstadr = (self['e1'] << 8) | self['e2']
		return assy.Arg_dst(pj, self.dstadr)

	def assy_r(self, pj):
		a = self['r']
		if a & 0x80:
			a += 0xff00
		self.dstadr = (self.hi + a) & 0xffff
		return assy.Arg_dst(pj, self.dstadr)

	def assy_R(self, pj):
		a = self['R1'] << 8 | self['R2']
		self.dstadr = (self.hi + a) & 0xffff
		return assy.Arg_dst(pj, self.dstadr)

	def assy_s(self, pj):
		x = self['i']
		l = []
		r = ["CCR", "A", "B", "DPR", "X", "Y", "_", "PC"]
		if self.mne[-1] == "S":
			r[6] = "U"
		if self.mne[-1] == "U":
			r[6] = "S"
		for i in r:
			if x & 1:
				l.append(i)
			x >>= 1
		if self.mne[:3] == "PSH":
			l = reversed(l)
		return ",".join(l)


	def assy_P(self, pj):
		if self['X'] == 1:
			self.hi += [
			    0, 0, 0, 0, 0, 0, 0, 0,
			    1, 2, 0, 0, 1, 2, 0, 2][self['m']]
		if self['X'] == 1 and self['m'] == 0xf:
			self.dstadr = pj.m.bu16(self.hi - 2)
		r = ["X", "Y", "U", "S"][self['R']]
		if self['X'] == 0:
			o = self['m']
			if self['i']:
				o -= 16
			return("%s%+d" % (r, o))
		if self['m'] == 0x0:
			s = r + "+"
		elif self['m'] == 0x1:
			s = r + "++"
		elif self['m'] == 0x2:
			s = "-" + r
		elif self['m'] == 0x3:
			s = "--" + r
		elif self['m'] == 0x4:
			s = r
		elif self['m'] == 0x5:
			s = r + "+B"
		elif self['m'] == 0x6:
			s = r + "+A"
		elif self['m'] == 0x8:
			o = pj.m.s8(self.hi - 1)
			s = r + "%+d" % o
		elif self['m'] == 0x9:
			o = pj.m.bs16(self.hi - 2)
			s = r + "%+d" % o
		elif self['m'] == 0xb:
			s = r + "+D"
		elif self['m'] == 0xd:
			o = pj.m.bs16(self.hi - 2)
			s = "0x%x" % ((0x10000 + self.hi + o & 0xffff))
		elif self['m'] == 0xf:
			o = pj.m.bs16(self.hi - 2)
			s = "0x%x" % o
		else:
			raise assy.Wrong("somehow... @ 0x%x" % self.lo + " %d" % self['m'])
		if self['i']:
			return "[" + s + "]"
		return s

	def assy_t(self, pj):
		val = self['t']
		r = [
			"D", "X",  "Y", "U",
			"S", "PC", "?6?", "?7?",
			"A", "B", "CCR", "DPR",
			"?c?", "?d?", "?e?", "?f?"
		]
		s = r[val >> 4] + "," + r[val & 0xf]
		return s

class mc6809(assy.Instree_disass):
	def __init__(self, mask=0xffff, macros=True):
		super(mc6809, self).__init__("mc6809", 8)
		self.it.load_string(mc6809_instructions)
		self.myleaf = mc6809_ins
		if macros:
			self.it.load_string(mc6809_macro_instructions)
		self.mask = mask

	def codeptr(self, pj, adr):
		t = pj.m.bu16(adr)
		c = data.Codeptr(pj, adr, adr + 2, t)
		pj.todo(t, self.disass)
		return c

	def vectors(self, pj, adr=0xfff0):
		for v in (
			"V??", "SWI3", "SWI2", "FIRQ",
			"IRQ", "SWI", "NMI", "RST"
		):
			c = self.codeptr(pj, adr)
			pj.set_label(c.dst, "VEC" + v)
			adr += 2
