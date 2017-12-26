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

+	PFX10	|0 0 0 1 0 0 0 0|

+	PFX11	|0 0 0 1 0 0 0 1|

NEG	d	|0 0 0 0 0 0 0 0| d		| {
	%1 = load i8 , i8* D
	%2 = sub i8 %1 , 1
	store i8 %2 , i8* D
	FLG UXXXX %2 sub %1 1
}

COM	d	|0 0 0 0 0 0 1 1| d		| {
	%1 = load i8 , i8* D
	%2 = xor i8 %1 , 0xff
	store i8 %2 , i8* D
	FLG UXX01 %2
}

LSR	d	|0 0 0 0 0 1 0 0| d		|

ROR	d	|0 0 0 0 0 1 1 0| d		|

ASR	d	|0 0 0 0 0 1 1 1| d		|

ASL	d	|0 0 0 0 1 0 0 0| d		|

ROL	d	|0 0 0 0 1 0 0 1| d		|

DEC	d	|0 0 0 0 1 0 1 0| d		| {
	%1 = load i8 , i8* D
	%2 = sub i8 %1 , 1
	store i8 %2 , i8* D
	FLG -XXX- %2 sub %1 1
}

INC	d	|0 0 0 0 1 1 0 0| d		| {
	%1 = load i8 , i8* D
	%2 = add i8 %1 , 1
	store i8 %2 , i8* D
	FLG -XXX- %2 add %1 1
}

TST	d	|0 0 0 0 1 1 0 1| d		| {
	%1 = load i8 , i8* D
	FLG -XX0- %1
}

JMP	d,>J	|0 0 0 0 1 1 1 0| d		| {
	br label D
}

CLR	d	|0 0 0 0 1 1 1 1| d		| {
	store i8 0 , i8* D
	FLG -0100
}

B	R,CC	|0 0 0 1 0 0 0 0|0 0 1 0| cc    | R1		| R2		| {
	BR
}

SWI2	>J	|0 0 0 1 0 0 0 0|0 0 1 1 1 1 1 1|

CMPD	I	|0 0 0 1 0 0 0 0|1 0 0 0 0 0 1 1| I1		| I2		|

CMPD	d	|0 0 0 1 0 0 0 0|1 0 0 1 0 0 1 1| d		|

CMPD    P	|0 0 0 1 0 0 0 0|1 0 1 0 0 0 1 1|X| R |i| m     |
CMPD	E	|0 0 0 1 0 0 0 0|1 0 1 1 0 0 1 1| e1		| e2		|

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

BRA	R,>J	|0 0 0 1 0 1 1 0| R1            | R2		| {
	br label DST
}

BSR	R,>C	|0 0 0 1 0 1 1 1| R1            | R2		| {
	%S = sub i16 %S , 2
	store i16 HI, i16* %S
	br label DST
}

DAA	-	|0 0 0 1 1 0 0 1|

ORCC	i	|0 0 0 1 1 0 1 0| i		|

ANDCC	i	|0 0 0 1 1 1 0 0| i		| {
	%CC = and i8 %CC , I
}

SEX	-	|0 0 0 1 1 1 0 1|

EXG	t	|0 0 0 1 1 1 1 0| t		|

TFR	t	|0 0 0 1 1 1 1 1| t		| {
	TFR
}

B	r,CC	|0 0 1 0| cc    | r		| {
	BR
}

LEA	XY,P	|0 0 1 1 0 0 0 0|X| R |i| m	|

LEAY	P	|0 0 1 1 0 0 0 1|X| R |i| m	|

LEAS	P	|0 0 1 1 0 0 1 0|X| R |i| m     |

LEAU	P	|0 0 1 1 0 0 1 1|X| R |i| m     |

PSHS	s	|0 0 1 1 0 1 0 0| i		| {
	PUSH S
}

PULS	s	|0 0 1 1 0 1 0 1| i		| {
	PULL S
}

PSHU	s	|0 0 1 1 0 1 1 0| i		| {
	PUSH U
}

PULU	s	|0 0 1 1 0 1 1 1| i		| {
	PULL U
}

RTS	>R	|0 0 1 1 1 0 0 1| {
	%0 = load i16 , i16* %S
	%S = add i16 %S , 2
	br label %0
}

AB	XY,-	|0 0 1 1 1 0 1 0|

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

INCA	-	|0 1 0 0 1 1 0 0| {
	%1 = i8 %A
	%A = add i8 %A , 1
	FLG -XXX- %A add %1 1
}

TSTA	-	|0 1 0 0 1 1 0 1|

CLRA	-	|0 1 0 0 1 1 1 1| {
	%A = i8 0
	FLG -0100
}

NEGB	-	|0 1 0 1 0 0 0 0|

COMB	-	|0 1 0 1 0 0 1 1|

LSRB	-	|0 1 0 1 0 1 0 0|

RORB	-	|0 1 0 1 0 1 1 0|

ASRB	-	|0 1 0 1 0 1 1 1|

ASLB	-	|0 1 0 1 1 0 0 0|

ROLB	-	|0 1 0 1 1 0 0 1|

DECB	-	|0 1 0 1 1 0 1 0|

INCB	-	|0 1 0 1 1 1 0 0| {
	%1 = i8 %B
	%B = add i8 %B , 1
	FLG -XXX- %B add %1 1
}

TSTB	-	|0 1 0 1 1 1 0 1|

CLRB	-	|0 1 0 1 1 1 1 1| {
	%B = i8 0
	FLG -0100
}

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

SUBA	i	|1 0 0 0 0 0 0 0| i		| {
	%1 = i8 %A
	%A = sub i8 %A , I
	FLG UXXXX %A sub %1 I
}

CMPA	i	|1 0 0 0 0 0 0 1| i		| {
	%2 = sub i8 %A , I
	FLG UXXXX %2 sub %A I
}

SBCA	i	|1 0 0 0 0 0 1 0| i		|

SUBD	I	|1 0 0 0 0 0 1 1| I1		| I2		|

ANDA	i	|1 0 0 0 0 1 0 0| i		| {
	%A = and i8 %A , I
	FLG -XX0- %A
}

BITA	i	|1 0 0 0 0 1 0 1| i		|

LDA	i	|1 0 0 0 0 1 1 0| i		| {
	%A = I
	FLG -XX0- %A
}

EORA	i	|1 0 0 0 1 0 0 0| i		| {
	%A = xor i8 %A , I
	FLG -XX0- %A
}

ADCA	i	|1 0 0 0 1 0 0 1| i		|

ORA	i	|1 0 0 0 1 0 1 0| i		| {
	%A = or i8 %A , I
	FLG -XX0- %A
}

ADDA	i	|1 0 0 0 1 0 1 1| i		| {
	%1 = i8 %A
	%A = add i8 %A , I
	FLG XXXXX %A add %1 I
}

CMP	XY,I	|1 0 0 0 1 1 0 0| I1		| I2		|

BSR	r,>C	|1 0 0 0 1 1 0 1| r		| {
	%S = sub i16 %S , 2
	store i16 HI, i16* %S
	br label DST
}

LD	XY,I	|1 0 0 0 1 1 1 0| I1		| I2		| {
	XY = i16 I16
	FLG -XX0- I16
}

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

CMP	XY,d	|1 0 0 1 1 1 0 0| d		|

JSR	d,>C	|1 0 0 1 1 1 0 1| d		|

LD	XY,d	|1 0 0 1 1 1 1 0| d		|

ST	XY,d	|1 0 0 1 1 1 1 1| d		|

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

CMP	XY,P	|1 0 1 0 1 1 0 0|X| R |i| m	|

JSR	P,>C	|1 0 1 0 1 1 0 1|X| R |i| m	|

LD	XY,P	|1 0 1 0 1 1 1 0|X| R |i| m     |

ST	XY,P	|1 0 1 0 1 1 1 1|X| R |i| m     |

SUBA	E	|1 0 1 1 0 0 0 0| e1		| e2		|

CMPA	E	|1 0 1 1 0 0 0 1| e1		| e2		|

SBCA	E	|1 0 1 1 0 0 1 0| e1		| e2		|

SUBD	E	|1 0 1 1 0 0 1 1| e1		| e2		|

ANDA	E	|1 0 1 1 0 1 0 0| e1		| e2		|

BITA	E	|1 0 1 1 0 1 0 1| e1		| e2		|

LDA	E	|1 0 1 1 0 1 1 0| e1		| e2		| {
	%A = load i8, i8* DST
	FLG -XX0- %A
}

STA	E	|1 0 1 1 0 1 1 1| e1		| e2		| {
	store i8* DST , i8 %A
	FLG -XX0- %A
}

EORA	E	|1 0 1 1 1 0 0 0| e1		| e2		|

ADCA	E	|1 0 1 1 1 0 0 1| e1		| e2		|

ORA	E	|1 0 1 1 1 0 1 0| e1		| e2		|

ADDA	E	|1 0 1 1 1 0 1 1| e1		| e2		|

CMP	XY,E	|1 0 1 1 1 1 0 0| e1		| e2		|

JSR	E,>C	|1 0 1 1 1 1 0 1| e1		| e2		|

LD	XY,E	|1 0 1 1 1 1 1 0| e1		| e2		| {
	%X = load i16, i16* DST
	FLG -XX0- %X
}

ST	XY,E	|1 0 1 1 1 1 1 1| e1		| e2		|

SUBB	i	|1 1 0 0 0 0 0 0| i		|

CMPB	i	|1 1 0 0 0 0 0 1| i		|

SBCB	i	|1 1 0 0 0 0 1 0| i		|

ADDD	I	|1 1 0 0 0 0 1 1| I1		| I2		|

ANDB	i	|1 1 0 0 0 1 0 0| i		|

BITB	i	|1 1 0 0 0 1 0 1| i		|

LDB	i	|1 1 0 0 0 1 1 0| i		| {
	%B = i8 I
	FLG -XX0- I
}

EORB	i	|1 1 0 0 1 0 0 0| i		|

ADCB	i	|1 1 0 0 1 0 0 1| i		|

ORB	i	|1 1 0 0 1 0 1 0| i		| {
	%B = or i8 %B , I
	FLG -XX0- %B
}

ADDB	i	|1 1 0 0 1 0 1 1| i		| {
	%1 = i8 %B
	%B = add i8 %B , I
	FLG XXXXX %B add %1 I
}

LDD	I	|1 1 0 0 1 1 0 0| I1		| I2		| {
	%A = i8 I1
	%B = i8 I2
	FLG -XX0- I16
}

LD	SU,I	|1 1 0 0 1 1 1 0| I1		| I2		| {
	SU = I16
	FLG -XX0- I16
}

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

LD	SU,d	|1 1 0 1 1 1 1 0| d		|

ST	SU,d	|1 1 0 1 1 1 1 1| d		|

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

LD	SU,P	|1 1 1 0 1 1 1 0|X| R |i| m     |

ST	SU,P	|1 1 1 0 1 1 1 1|X| R |i| m     |

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

STD	E	|1 1 1 1 1 1 0 1| e1		| e2		| {
	MKD
	store i16* DST , %D
	FLG -XX0- %D
}
LD	SU,E	|1 1 1 1 1 1 1 0| e1		| e2		|

ST	SU,E	|1 1 1 1 1 1 1 1| e1		| e2		|

"""

mc6809_macro_instructions = """
LDDx	i	|1 1 0 0 0 1 1 0| i		|0 1 0 0 1 1 1 1| {
	%B = i8 I
	%A = i8 0
	FLG -0100
}

ANDD	I	|1 0 0 0 0 1 0 0| I1		|1 1 0 0 0 1 0 0| I2		| {
	%A = and i8 %A , I1
	%B = and i8 %A , I2
	FLG -XX0- %B
}

ORD	I	|1 0 0 0 1 0 1 0| I1		|1 1 0 0 1 0 1 0| I2		| {
	%A = or i8 %A , I1
	%B = or i8 %A , I2
	FLG -XX0- %B
}

CLRD	-	|0 1 0 1 1 1 1 1|0 1 0 0 1 1 1 1| {
	%A = i8 0
	%B = i8 0
	FLG -0100
}

CLRD	-	|0 1 0 0 1 1 1 1|0 1 0 1 1 1 1 1| {
	%A = i8 0
	%B = i8 0
	FLG -0100
}

"""


class mc6809_ins(assy.Instree_ins):
	def __init__(self, pj, lim, lang):
		super(mc6809_ins, self).__init__(pj, lim, lang)
		self.isz = "i8"
		self.icache = {}
		self.pfx = None

	def assy_PFX10(self, pj):
		self.pfx = 0x10

	def assy_PFX11(self, pj):
		self.pfx = 0x11

	def assy_XY(self, pj):
		if self.pfx == 0x10:
			self.mne += "Y"
		else:
			self.mne += "X"

	def assy_SU(self, pj):
		if self.pfx == 0x10:
			self.mne += "S"
		else:
			self.mne += "U"

	def assy_d(self, pj):
		return "$0x%02x" % self['d']

	def assy_i(self, pj):
		return "#0x%02x" % self['i']

	def assy_CC(self, pj):
		self.cc = [
			"RA", "RN", "HI", "LS", "CC", "CS", "NE", "EQ",
			"VC", "VS", "PL", "MI", "GE", "LT", "GT", "LE"
		][self['cc']]
		self.mne += self.cc
		if self['cc'] == 0:
			self.flow_J(pj)
		elif self['cc'] > 1:
			self.flow_JC(pj)

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
		# XXX: if PULL PC fix flow record
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
		sr = val >> 4
		dr = val & 0xf
		r = [
			"D", "X",  "Y", "U",
			"S", "PC", "?6?", "?7?",
			"A", "B", "CCR", "DPR",
			"?c?", "?d?", "?e?", "?f?"
		]
		if r[sr][0] == "?" or r[dr][0] == "?":
			raise assy.Wrong("Wrong arg to TFR (0x%02x)" % val)
		return r[sr] + "," + r[dr]

	def ilmacro_BR(self):
		cc = self['cc']
		if cc == 0:
			self.add_il([["br", "label", "0x%04x" % self.dstadr]])
			return
		if cc == 1:
			self.add_il([["%0", "=", "i8", "0"]])
			return
		if cc & 1:
			d1 = "0x%04x" % self.dstadr
			d2 = "HI"
		else:
			d1 = "HI"
			d2 = "0x%04x" % self.dstadr
		l = []
		cc &= 0xe
		if cc == 2:
			l.append(["%0", "=", "or", "i1", "%CC.z", ",", "%CC.c"])
			bb = "%0"
		elif cc == 4:
			bb = "%CC.c"
		elif cc == 6:
			bb = "%CC.z"
		elif cc == 8:
			bb = "%CC.v"
		elif cc == 10:
			bb = "%CC.n"
		elif cc == 12:
			l.append(["%0", "=", "xor", "i1", "%CC.n", ",", "%CC.v"])
			bb = "%0"
		else:
			l.append(["%0", "=", "xor", "i1", "%CC.n", ",", "%CC.v"])
			l.append(["%1", "=", "or", "i1", "%CC.z", ",", "%0"])
			bb = "%1"
		l.append(["br", "i1", bb, "label", d1, ",", "label", d2])

		self.add_il(l)

	def ilmacro_D(self):
		j = self.icache.get("d")
		if j is None:
			j = self.add_il([
				["%1", "=", "add", "i16", "%DP", ",", "0x%02x" % self['d']]
			], "%1")
		self.icache["d"] = j
		return j

	def ilmacro_DST(self):
		return "0x%04x" % self.dstadr

	def ilmacro_HI(self):
		return "0x%x" % self.hi

	def ilmacro_I(self):
		return "0x%02x" % (self['i'])

	def ilmacro_I1(self):
		return "0x%02x" % (self['I1'])

	def ilmacro_I2(self):
		return "0x%02x" % (self['I2'])

	def ilmacro_I(self):
		return "0x%02x" % (self['i'])

	def ilmacro_I16(self):
		self.isz = "i16"
		return "0x%02x%02x" % (self['I1'], self['I2'])

	def ilmacro_MKD(self):
		self.isz = "i16"
		self.add_il([
			["%0", "=", "zext", "i8", "%A", "to", "i16"],
			["%1", "=", "shl", "i16", "%0", ",", "8"],
			["%2", "=", "zext", "i8", "%B", "to", "i16"],
			["%D", "=", "or", "i16", "%1", ",", "%2"],
		])

	def ilmacro_SU(self):
		if self.pfx == 0x10:
			return "%S"
		else:
			return "%U"

	def ilmacro_XY(self):
		if self.pfx == 0x10:
			return "%Y"
		else:
			return "%X"

	def ilfunc_TFR(self, arg):
		val = self['t']
		sr = val >> 4
		dr = val & 0xf
		sz = ["i16", "i8"][sr >> 3]
		r = [
			"?0?", "%X",  "%Y", "%U",
			"%S", "%PC", "?6?", "?7?",
			"%A", "%B", "%CC", "%DP",
			"?c?", "?d?", "?e?", "?f?"
		]
		if sr == 0:
			r[0] = self.add_il([
				["%1", "=", "zext", "i16", "%A"],
				["%2", "=", "zext", "i16", "%B"],
				["%3", "=", "shl", "i16", "8", "%2"],
				["%0", "=", "or", "i16", "%1", ",", "%3"],
			], "%0")
		elif dr == 0:
			r[0] = "%0"
		self.add_il([
			[r[dr], "=", sz, r[sr]]
		])
		if dr == 0:
			self.add_il([
				["%A", "=", "trunc", "i16", r[0], "to", "i8"],
				["%0", "=", "shr", "i16", r[0], "8"],
				["%B", "=", "trunc", "i16", "%0", "to", "i8"],
			])

	def ilfunc_FLG_N(self, arg):
		c = "0x80"
		if self.isz == "i16":
			c += "00"
		self.add_il([
			["%1", "=", "and", self.isz, arg[0], ",", c],
			["%CC.n", "=", "icmp", "eq", self.isz, "%1", ",", c]
		])

	def ilfunc_FLG_V(self, arg):
		# XXX "Set if the carry from the MSB in the ALU does not match
		# XXX the carry from the MSB-1"
		assert len(arg) == 4
		self.add_il([
			["%CC.v", "=", "i1",
			    "pyreveng.overflow." + arg[1], "(", arg[2], ",", arg[3], ")"]
		])

	def ilfunc_FLG_Z(self, arg):
		self.add_il([
			["%CC.z", "=", "icmp", "eq", self.isz, arg[0], ",", "0"]
		])

	def ilfunc_FLG_H(self, arg):
		# XXX
		self.add_il([
			["%CC.h", "=", "i1", "void"]
		])

	def ilfunc_FLG_C(self, arg):
		assert len(arg) == 4
		self.add_il([
			["%CC.c", "=", "i1",
			    "pyreveng.carry." + arg[1], "(", arg[2], ",", arg[3], ")"]
		])

	def ilfunc_FLG(self, arg):
		f = {
			"H": self.ilfunc_FLG_H,
			"N": self.ilfunc_FLG_N,
			"Z": self.ilfunc_FLG_Z,
			"V": self.ilfunc_FLG_V,
			"C": self.ilfunc_FLG_C,
		}
		a1 = arg.pop(0)
		for j in "HNZVC":
			if a1[0] == "0":
				self.add_il([["%CC." + j.lower(), "=", "i1", "0"]])
			elif a1[0] == "1":
				self.add_il([["%CC." + j.lower(), "=", "i1", "1"]])
			elif a1[0] == "U":
				self.add_il([["%CC." + j.lower(), "=", "i1", "void"]])
			elif a1[0] != "-":
				assert len(arg) > 0
				f[j](arg)
			a1 = a1[1:]

	def ilfunc_PULL(self, arg):
		i = self['i']
		s = "%" + arg[0]
		if s == "%S":
			sa = "%U"
		else:
			sa = "%S"
		j = 0x01
		for r in ('%CC', '%A', '%B', '%DP'):
			if i & j:
				self.add_il([
					["load", r, "i8*", ",", s],
					[s, "=", "add", "i16", s, ",", "1"],
				])
			j <<= 1
		for r in ('%X', '%Y', sa):
			if i & j:
				self.add_il([
					["load", r, "i16*", ",", s],
					[s, "=", "add", "i16", s, ",", "2"],
				])
			j <<= 1
		if i & j:
			self.add_il([
				["load", "%0", "i16*", ",", s],
				[s, "=", "add", "i16", s, ",", "2"],
				["br", "label", "%0"],
			])

	def ilfunc_PUSH(self, arg):
		i = self['i']
		s = "%" + arg[0]
		if s == "%S":
			sa = "%U"
		else:
			sa = "%S"
		j = 0x80
		for r in ('HI', sa, '%Y', '%X'):
			if i & j:
				self.add_il([
					[s, "=", "sub", "i16", s, ",", "2"],
					["store", "i16*", s, ",", r],
				])
			j >>= 1
		for r in ('%DP', '%B', '%A', '%CC'):
			if i & j:
				self.add_il([
					[s, "=", "sub", "i16", s, ",", "1"],
					["store", "i16*", s, ",", r],
				])
			j >>= 1


class mc6809(assy.Instree_disass):
	def __init__(self, mask=0xffff, macros=True):
		super(mc6809, self).__init__("mc6809", 8)
		self.it.load_string(mc6809_instructions)
		self.il = None
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
