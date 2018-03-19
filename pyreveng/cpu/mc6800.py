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
Disassembler for MC6800 familiy CPUs.

Presently supported variants:
        6800
        MC68HC11 (incomplete)
"""

from __future__ import print_function

from pyreveng import assy, data

mc6800_instructions = """
NOP     -       |01     | {
        %0 = i1 0
}
TAP     -       |06     | {
        SPLIT ( i8 %A , i1 %H , i1 %I , i1 %N , i1 %Z , i1 %V , i1 %C )
}
TPA     -       |07     | {
        CAT ( i8 %A , i1 1, i1 1, i1 %H , i1 %I , i1 %N , i1 %Z , i1 %V , i1 %C )
}
INX     -       |08     | {
        %X = add i16 %X , 1
        FLG UUUAUU %X
}
DEX     -       |09     | {
        %X = sub i16 %X , 1
        FLG UUUAUU %X
}
CLV     -       |0A     | {
        %V = i1 0
}
SEV     -       |0B     | {
        %V = i1 1
}
CLC     -       |0C     | {
        %C = i1 0
}
SEC     -       |0D     | {
        %C = i1 1
}
CLI     -       |0E     | {
        %I = i1 0
}
SEI     -       |0F     | {
        %I = i1 1
}
SBA     -       |10     | {
        %0 = sub i8 %A , %B
        FLG UUAAAA %0 - %A %B
        %A = i8 %0
}
CBA     -       |11     | {
        %0 = sub i8 %A , %B
        FLG UUAAAA %0 - %A %B
}
TAB     -       |16     | {
        %B = i8 %A
        FLG UUAARU %B
}
TBA     -       |17     | {
        %A = i8 %B
        FLG UUAARU %A
}
DAA     -       |19     | {
        DAA ( i8 %A )
}
ABA     -       |1B     | {
        %0 = add i8 %A , %B
        FLG AUAAAA %0 + %A %B
        %A = i8 %0
}
BRA     r,>J    |20     | r             | {
        br label DST
}
BHI     r,>JC   |22     | r             | {
        %0 = or i1 %C , %Z
        br i1 %0 , label HI , label DST
}
BLS     r,>JC   |23     | r             | {
        %0 = or i1 %C , %Z
        br i1 %0 , label DST , label HI
}
BCC     r,>JC   |24     | r             | {
        br i1 %C , label HI , label DST
}
BCS     r,>JC   |25     | r             | {
        br i1 %C , label DST , label HI
}
BNE     r,>JC   |26     | r             | {
        br i1 %Z , label HI , label DST
}
BEQ     r,>JC   |27     | r             | {
        br i1 %Z , label DST , label HI
}
BVC     r,>JC   |28     | r             | {
        br i1 %V , label HI , label DST
}
BVS     r,>JC   |29     | r             | {
        br i1 %V , label DST , label HI
}
BPL     r,>JC   |2A     | r             | {
        br i1 %N , label HI , label DST
}
BMI     r,>JC   |2B     | r             | {
        br i1 %N , label DST , label HI
}
BGE     r,>JC   |2C     | r             | {
        %0 = xor i1 %N , %V
        br i1 %0 , label HI , label DST
}
BLT     r,>JC   |2D     | r             | {
        %0 = xor i1 %N , %V
        br i1 %0 , label DST , label HI
}
BGT     r,>JC   |2E     | r             | {
        %0 = xor i1 %N , %V
        %1 = or i1 %0 , %Z
        br i1 %1 , label HI , label DST
}
BLE     r,>JC   |2F     | r             | {
        %0 = xor i1 %N , %V
        %1 = or i1 %0 , %Z
        br i1 %1 , label DST , label HI
}
TSX     -       |30     | {
        %X = add i16 %S , 1
}
INS     -       |31     | {
        %S = add i16 %S , 1
}
PULA    -       |32     | {
        %A = load i8 , i8* %S
        %S = add i16 %S , 1
}
PULB    -       |33     | {
        %A = load i8 , i8* %S
        %S = add i16 %S , 1
}
DES     -       |34     | {
        %S = sub i16 %S , 1
}
TXS     -       |35     | {
        %S = sub i16 %X , 1
}
PSHA    -       |36     | {
        %S = sub i16 %S , 1
        store i8 %A , i8* %S
}
PSHB    -       |37     | {
        %S = sub i16 %S , 1
        store i8 %B , i8* %S
}
RTS     >R      |39     | {
        %0 = load i16 , i16* %S
        %S = add i16 %S , 2
        br label %0
}
RTI     >R      |3B     | {
        %S = add i16 %S , 1
        %0 = load i8 , i8* %S
        SPLIT ( i8 %0 , i1 %H , i1 %I , i1 %N , i1 %Z , i1 %V , i1 %C )
        %S = add i16 %S , 1
        %B = load i8 , i8* %S
        %S = add i16 %S , 1
        %A = load i8 , i8* %S
        %S = add i16 %S , 2
        %X = load i16 , i16* %S
        %S = add i16 %S , 2
        %1 = load i16 , i16* %S
        br label %1
}
WAI     -       |3E     | {
        %I = i1 undef
}
SWI     -       |3F     | {
        store i16 HI , i16* %S
        %S = add i16 %S , 2
        store i16 %X , i16* %S
        %S = add i16 %S , 2
        store i8 %A , i16* %S
        %S = add i16 %S , 1
        store i8 %B , i16* %S
        %S = add i16 %S , 1
        CAT ( i8 %0 , i1 1, i1 1, i1 %H , i1 %I , i1 %N , i1 %Z , i1 %V , i1 %C )
        store i8 %0 , i16* %S
        %S = add i16 %S , 1
        %1 = load i16 , i16* 0xfffa
        br label %1
}
NEGA    -       |40     | {
        %0 = sub i8 0 , %A
        FLG UUAA12 %0 - 0 %A
        %A = i8 %0
}
COMA    -       |43     | {
        %A = xor i8 %A , 0xff
        FLG UUAARS %A
}
LSRA    -       |44     | {
        RIGHT ( 1 , i1 0 , i8 %A, i1 %C )
        FLG UURA6U %A
}
RORA    -       |46     | {
        RIGHT ( 1 , i1 %C , i8 %A, i1 %C )
        FLG UUAA6U %A
}
ASRA    -       |47     | {
        RIGHT ( 1 , i8 %A, i1 %C )
        FLG UUAA6U %A
}
ASLA    -       |48     | {
        LEFT ( 1 , i1 %C , i8 %A, i1 0 )
        FLG UUAA6U %A
}
ROLA    -       |49     | {
        LEFT ( 1 , i1 %C , i8 %A, i1 %C )
        FLG UUAA6U %A
}
DECA    -       |4A     | {
        %0 = sub i8 %A , 1
        FLG UUAA4U %0 - %A 1
        %A = i8 %0
}
INCA    -       |4C     | {
        %0 = add i8 %A , 1
        FLG UUAA4U %0 + %A 1
        %A = i8 %0
}
TSTA    -       |4D     | {
        FLG UUAARR %A
}
CLRA    -       |4F     | {
        %A = i8 0
        FLG UURSUU %A
}
NEGB    -       |50     | {
        %0 = sub i8 0 , %B
        FLG UUAA12 %0 - 0 %B
        %B = i8 %0
}
COMB    -       |53     | {
        %B = xor i8 %B , 0xff
        FLG UUAARS %B
}
LSRB    -       |54     | {
        RIGHT ( 1 , i1 0 , i8 %B, i1 %C )
        FLG UURA6U %B
}
RORB    -       |56     | {
        RIGHT ( 1 , i1 %C , i8 %B, i1 %C )
        FLG UUAA6U %B
}
ASRB    -       |57     | {
        RIGHT ( 1 , i8 %B, i1 %C )
        FLG UUAA6U %B
}
ASLB    -       |58     | {
        LEFT ( 1 , i1 %C , i8 %B, i1 0 )
        FLG UUAA6U %B
}
ROLB    -       |59     | {
        LEFT ( 1 , i1 %C , i8 %B, i1 %C )
        FLG UUAA6U %B
}
DECB    -       |5A     | {
        %0 = sub i8 %B , 1
        FLG UUAA4U %0 - %B 1
        %B = i8 %0
}
INCB    -       |5C     | {
        %0 = add i8 %B , 1
        FLG UUAA4U %0 + %B 1
        %B = i8 %0
}
TSTB    -       |5D     | {
        FLG UUAARR %B
}
CLRB    -       |5F     | {
        %B = i8 0
        FLG UURSUU %B
}
NEG     x       |60     | x             | {
        %0 = add i16 %X , i16 X
        %1 = load i8 , i8* %0
        %2 = sub i8 0 , %1
        FLG UUAA12 %0 - 0 %1
        store i8 %2 , i8* %0
}
COM     x       |63     | x             | {
        %0 = add i16 %X , i16 X
        %1 = load i8 , i8* %0
        %2 = xor i8 %1 , 0xff
        FLG UUAARS %2
        store i8 %2 , i8* %0
}
LSR     x       |64     | x             | {
        %0 = add i16 %X , i16 X
        %1 = load i8 , i8* %0
        RIGHT ( 1 , i1 0 , i8 %1, i1 %C )
        FLG UUAA6U %1
        store i8 %1 , i8* %0
}
ROR     x       |66     | x             | {
        %0 = add i16 %X , i16 X
        %1 = load i8 , i8* %0
        RIGHT ( 1 , i1 %C , i8 %1, i1 %C )
        FLG UUAA6U %0
        store i8 %1 , i8* %0
}
ASR     x       |67     | x             | {
        %0 = add i16 %X , i16 X
        %1 = load i8 , i8* %0
        RIGHT ( 1 , i8 %1, i1 %C )
        FLG UUAA6U %1
        store i8 %1 , i8* %0
}
ASL     x       |68     | x             | {
        %0 = add i16 %X , i16 X
        %1 = load i8 , i8* %0
        LEFT ( 1 , i1 %C , i8 %1, i1 0 )
        FLG UUAA6U %1
        store i8 %1 , i8* %0
}
ROL     x       |69     | x             | {
        %0 = add i16 %X , i16 X
        %1 = load i8 , i8* %0
        LEFT ( 1 , i1 %C , i8 %1, i1 %C )
        FLG UUAA6U %A
        store i8 %1 , i8* %0
}
DEC     x       |6A     | x             | {
        %1 = add i16 %X , i16 X
        %2 = load i8 , i8* %1
        %3 = sub i8 %2 , 1
        FLG UUAA4U %3 - %2 1
        store i8 %3 , i8* %1
}
INC     x       |6C     | x             | {
        %1 = add i16 %X , i16 X
        %2 = load i8 , i8* %1
        %3 = add i8 %2 , 1
        FLG UUAA4U %3 + %2 1
        store i8 %3 , i8* %1
}
TST     x       |6D     | x             | {
        %1 = add i16 %X , i16 X
        %2 = load i8 , i8* %1
        FLG UUAARR %2
}
JMP     x,>J    |6E     | x             | {
        %1 = add i16 %X , i16 X
        br label %1
}
CLR     x       |6F     | x             | {
        %1 = add i16 %X , i16 X
        store i8 0 , i8* %1
        FLG UURSUU 0
}
NEG     e       |70     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        %1 = sub i8 0 , %0
        FLG UUAA12 %0 - 0 %0
        store i8 %1 , i8* ED
}
COM     e       |73     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        %1 = xor i8 %0 , 0xff
        FLG UUAARS %1
        store i8 %0 , i8* ED
}
LSR     e       |74     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        RIGHT ( 1 , i1 0 , i8 %0, i1 %C )
        FLG UUAA6U %0
        store i8 %0 , i8* ED
}
ROR     e       |76     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        RIGHT ( 1 , i1 %C , i8 %0, i1 %C )
        FLG UUAA6U %0
        store i8 %0 , i8* ED
}
ASR     e       |77     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        RIGHT ( 1 , i8 %0, i1 %C )
        FLG UUAA6U %0
        store i8 %0 , i8* ED
}
ASL     e       |78     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        LEFT ( 1 , i1 %C , i8 %0, i1 0 )
        FLG UUAA6U %0
        store i8 %0 , i8* ED
}
ROL     e       |79     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        LEFT ( 1 , i1 %C , i8 %0, i1 %C )
        FLG UUAA6U %0
        store i8 %0 , i8* ED
}
DEC     e       |7A     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        %1 = sub i8 %0 , 1
        FLG UUAA4U %1 - %0 1
        store i8 %1 , i8* ED
}
INC     e       |7C     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        %1 = add i8 %0 , 1
        FLG UUAA4U %1 + %0 1
        store i8 %1 , i8* ED
}
TST     e       |7D     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        FLG UUAARR %0
}
JMP     e,>J    |7E     | e1            | e2            | {
        br label DST
}
CLR     e       |7F     | e1            | e2            | {
        store i8 0 , i8* ED
        FLG UURSUU 0
}
SUBA    i       |80     | i             | {
        %0 = sub i8 %A , IM
        FLG UUAAAA %0 - %A IM
        %A = i8 %0
}
CMPA    i       |81     | i             | {
        %0 = sub i8 %A , IM
        FLG UUAAAA %0 - %A IM
}
SBCA    i       |82     | i             | {
        SBC %A IM
}
ANDA    i       |84     | i             | {
        %A = and i8 %A , IM
        FLG UUAARU %A
}
BITA    i       |85     | i             | {
        %0 = and i8 %A , IM
        FLG UUAARU %0
}
LDAA    i       |86     | i             | {
        %A = i8 IM
        FLG UUAARU %A
}
EORA    i       |88     | i             | {
        %A = xor i8 %A , IM
        FLG UUAARU %A
}
ADCA    i       |89     | i             | {
        ADC %A IM
}
ORAA    i       |8A     | i             | {
        %A = or i8 %A , IM
        FLG UUAARU %A
}
ADDA    i       |8B     | i             | {
        %0 = add i8 %A , IM
        FLG AUAAAA %0 + %A IM
        %A = i8 %0
}
CPX     I       |8C     | I1            | I2            | {
        %0 = sub i16 %X , II
        FLG UU1A2U %0
}
BSR     r,>C    |8D     | r             | {
        %S = sub i16 %S , 2
        store i16 HI , i16* %S
        br label DST
}
LDS     I       |8E     | I1            | I2            | {
        %S = i16 II
        FLG UU3ARU %S
}
SUBA    d       |90     | d             | {
        %0 = load i8 , i8 * D
        %1 = sub i8 %A , %0
        FLG UUAAAA %1 - %A %0
        %A = i8 %1
}
CMPA    d       |91     | d             | {
        %0 = load i8 , i8 * D
        %1 = sub i8 %A , %0
        FLG UUAAAA %1 - %A %0
}
SBCA    d       |92     | d             | {
        %0 = load i8 , i8 * D
        SBC %A %0
}
ANDA    d       |94     | d             | {
        %0 = load i8 , i8 * D
        %A = and i8 %A , %0
        FLG UUAARU %A
}
BITA    d       |95     | d             | {
        %0 = load i8 , i8* D
        %1 = and i8 %A , %0
        FLG UUAARU %1
}
LDAA    d       |96     | d             | {
        %A = load i8 , i8* D
        FLG UUAARU %A
}
STAA    d       |97     | d             | {
        store i8 %A , i8* D
        FLG UUAARU %A
}
EORA    d       |98     | d             | {
        %0 = load i8 , i8 * D
        %A = xor i8 %A , %0
        FLG UUAARU %A
}
ADCA    d       |99     | d             | {
        %0 = load i8 , i8 * D
        ADC %A %0
}
ORAA    d       |9A     | d             | {
        %0 = load i8 , i8 * D
        %A = or i8 %A , %0
        FLG UUAARU %A
}
ADDA    d       |9B     | d             | {
        %0 = load i8 , i8* D
        %1 = add i8 %A , %0
        FLG AUAAAA %1 + %A %0
        %A = i8 %1
}
CPX     d       |9C     | d             | {
        %0 = load i16 , i16* D
        %1 = sub i16 %X , %0
        FLG UU1A2U %1
}
LDS     d       |9E     | d             | {
        %S = load i16 , i16* D
        FLG UU3ARU %S
}
STS     d       |9F     | d             | {
        store i16 %S , i16* D
        FLG UU3ARU %S
}
SUBA    x       |A0     | x             | {
        %0 = add i16 %X , i16 X
        %1 = load i8 , i8* %0
        %2 = sub i8 %A , %1
        FLG UUAAAA %2 - %A %1
        %A = i8 %2
}
CMPA    x       |A1     | x             | {
        %1 = add i16 %X , i16 X
        %2 = load i8 , i8* %1
        %3 = sub i8 %A , %2
        FLG UUAAAA %3 - %A %2
}
SBCA    x       |A2     | x             | {
        %0 = add i16 %X , i16 X
        %1 = load i8 , i8* %0
        SCB %A %1
}
ANDA    x       |A4     | x             | {
        %1 = add i16 %X , i16 X
        %2 = load i8 , i8* %1
        %A = and i8 %A , %2
        FLG UUAARU %A
}
BITA    x       |A5     | x             | {
        %0 = add i16 %X , i16 X
        %1 = load i8 , i8* %0
        %2 = and i8 %A , %1
        FLG UUAARU %2
}
LDAA    x       |A6     | x             | {
        %1 = add i16 %X , i16 X
        %A = load i8 , i8* %1
        FLG UUAARU %A
}
STAA    x       |A7     | x             | {
        %1 = add i16 %X , i16 X
        store i8 %A , i8* %1
        FLG UUAARU %A
}
EORA    x       |A8     | x             | {
        %1 = add i16 %X , i16 X
        %2 = load i8 , i8* %1
        %A = xor i8 %A , %2
        FLG UUAARU %A
}
ADCA    x       |A9     | x             | {
        %0 = add i16 %X , i16 X
        %1 = load i8 , i8* %0
        ADC %A %1
}
ORAA    x       |AA     | x             | {
        %1 = add i16 %X , i16 X
        %2 = load i8 , i8* %1
        %A = or i8 %A , %2
        FLG UUAARU %A
}
ADDA    x       |AB     | x             | {
        %1 = add i16 %X , i16 X
        %2 = load i8 , i8* %1
        %3 = add i8 %A , %2
        FLG AUAAAA %3 + %A %2
        %A = i8 %3
}
CPX     x       |AC     | x             | {
        %0 = add i16 %X , i16 X
        %1 = load i16 , i16* %0
        %2 = sub i16 %X , %1
        FLG UU1A2U %2
}
JSR     x,>C    |AD     | x             | {
        %1 = add i16 %X , i16 X
        %S = sub i16 %S , 2
        store i16 HI , i16* %S
        br label %X
}
LDS     x       |AE     | x             | {
        %1 = add i16 %X , i16 X
        %S = load i16 , i16* %1
        FLG UU3ARU %S
}
STS     x       |AF     | x             | {
        %0 = add i16 %X , i16 X
        store i16 %S , i16* %0
        FLG UU3ARU %S
}
SUBA    e       |B0     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        %1 = sub i8 %A , %0
        FLG UUAAAA %1 - %A %0
        %A = i8 %1
}
CMPA    e       |B1     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        %1 = sub i8 %A , %0
        FLG UUAAAA %1 - %A %0
}
SBCA    e       |B2     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        SBC %A %0
}
ANDA    e       |B4     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        %A = and i8 %A , %0
        FLG UUAARU %A
}
BITA    e       |B5     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        %1 = and i8 %A , %0
        FLG UUAARU %1
}
LDAA    e       |B6     | e1            | e2            | {
        %A = load i8 , i8* ED
        FLG UUAARU %A
}
STAA    e       |B7     | e1            | e2            | {
        store i8 %A , i8* ED
        FLG UUAARU %A
}
EORA    e       |B8     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        %A = xor i8 %A , %0
        FLG UUAARU %A
}
ADCA    e       |B9     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        ADC %A %0
}
ORAA    e       |BA     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        %A = or i8 %A , %0
        FLG UUAARU %A
}
ADDA    e       |BB     | e1            | e2            | {
        %0 = load i8 , i8* ED
        %1 = add i8 %A , %0
        FLG AUAAAA %1 + %A %0
        %A = i8 %1
}
CPX     e       |BC     | e1            | e2            | {
        %0 = load i16 , i16* ED
        %1 = sub i16 %X , %0
        FLG UU1A2U %1
}
JSR     e,>C    |BD     | e1            | e2            | {
        %S = sub i16 %S , 2
        store i16 HI , i16* %S
        br label DST
}
LDS     e       |BE     | e1            | e2            | {
        %S = load i16 , i16* ED
        FLG UU3ARU %S
}
STS     e       |BF     | e1            | e2            | {
        store i16 %S , i16* ED
        FLG UU3ARU %S
}
SUBB    i       |C0     | i             | {
        %0 = sub i8 %B , IM
        FLG UUAAAA %0 - %B IM
        %B = i8 %0
}
CMPB    i       |C1     | i             | {
        %0 = sub i8 %B , IM
        FLG UUAAAA %0 - %B IM
}
SBCB    i       |C2     | i             | {
        SBC %B IM
}
ANDB    i       |C4     | i             | {
        %B = and i8 %B , IM
        FLG UUAARU %B
}
BITB    i       |C5     | i             | {
        %0 = and i8 %B , IM
        FLG UUAARU %0
}
LDAB    i       |C6     | i             | {
        %B = i8 IM
        FLG UUAARU %B
}
EORB    i       |C8     | i             | {
        %B = xor i8 %B , IM
        FLG UUAARU %B
}
ADCB    i       |C9     | i             | {
        ADC %B IM
}
ORAB    i       |CA     | i             | {
        %B = or i8 %B , IM
        FLG UUAARU %B
}
ADDB    i       |CB     | i             | {
        %0 = add i8 %B , IM
        FLG AUAAAA %0 + %B IM
        %B = i8 %0
}
LDX     I       |CE     | I1            | I2            | {
        %X = i16 II
        FLG UU3ARU %X
}
SUBB    d       |D0     | d             | {
        %0 = load i8 , i8 * D
        %1 = sub i8 %B , %0
        FLG UUAAAA %1 - %B %0
        %B = i8 %1
}
CMPB    d       |D1     | d             | {
        %0 = load i8 , i8 * D
        %1 = sub i8 %B , %0
        FLG UUAAAA %1 - %B %0
}
SBCB    d       |D2     | d             | {
        %0 = load i8 , i8 * D
        SBC %B %0
}
ANDB    d       |D4     | d             | {
        %0 = load i8 , i8 * D
        %B = and i8 %B , %0
        FLG UUAARU %B
}
BITB    d       |D5     | d             | {
        %0 = load i8 , i8* D
        %1 = and i8 %B , %0
        FLG UUAARU %1
}
LDAB    d       |D6     | d             | {
        %B = load i8 , i8* D
        FLG UUAARU %B
}
STAB    d       |D7     | d             | {
        store i8 %B , i8* D
        FLG UUAARU %B
}
EORB    d       |D8     | d             | {
        %0 = load i8 , i8 * D
        %B = xor i8 %B , %0
        FLG UUAARU %B
}
ADCB    d       |D9     | d             | {
        %0 = load i8 , i8 * D
        ADC %B %0
}
ORAB    d       |DA     | d             | {
        %0 = load i8 , i8 * D
        %B = or i8 %B , %0
        FLG UUAARU %B
}
ADDB    d       |DB     | d             | {
        %0 = load i8 , i8* D
        %1 = add i8 %B , %0
        FLG AUAAAA %1 + %B %0
        %B = i8 %1
}
LDX     d       |DE     | d             | {
        %X = load i16 , i16* D
        FLG UU3ARU %X
}
STX     d       |DF     | d             | {
        store i16 %X , i16* D
        FLG UU3ARU %X
}
SUBB    x       |E0     | x             | {
        %0 = add i16 %X , i16 X
        %1 = load i8 , i8* %0
        %2 = sub i8 %B , %1
        FLG UUAAAA %2 - %B %1
        %B = i8 %2
}
CMPB    x       |E1     | x             | {
        %1 = add i16 %X , i16 X
        %2 = load i8 , i8* %1
        %3 = sub i8 %B , %2
        FLG UUAAAA %3 - %B %2
}
SBCB    x       |E2     | x             | {
        %0 = add i16 %X , i16 X
        %1 = load i8 , i8* %0
        SBC %B %1
}
ANDB    x       |E4     | x             | {
        %1 = add i16 %X , i16 X
        %2 = load i8 , i8* %1
        %B = and i8 %B , %2
        FLG UUAARU %B
}
BITB    x       |E5     | x             | {
        %0 = add i16 %X , i16 X
        %1 = load i8 , i8* %0
        %2 = and i8 %B , %1
        FLG UUAARU %2
}
LDAB    x       |E6     | x             | {
        %1 = add i16 %X , i16 X
        %B = load i8 , i8* %1
        FLG UUAARU %B
}
STAB    x       |E7     | x             | {
        %1 = add i16 %X , i16 X
        store i8 %B , i8* %1
        FLG UUAARU %B
}
EORB    x       |E8     | x             | {
        %1 = add i16 %X , i16 X
        %2 = load i8 , i8* %1
        %B = xor i8 %B , %2
        FLG UUAARU %B
}
ADCB    x       |E9     | x             | {
        %0 = add i16 %X , i16 X
        %1 = load i8 , i8* %0
        ADC %B %1
}
ORAB    x       |EA     | x             | {
        %1 = add i16 %X , i16 X
        %2 = load i8 , i8* %1
        %B = or i8 %B , %2
        FLG UUAARU %B
}
ADDB    x       |EB     | x             | {
        %1 = add i16 %X , i16 X
        %2 = load i8 , i8* %1
        %3 = add i8 %B , %2
        FLG AUAAAA %3 + %B %2
        %B = i8 %3
}
LDX     x       |EE     | x             | {
        %1 = add i16 %X , i16 X
        %X = load i16 , i16* %1
        FLG UU3ARU %X
}
STX     x       |EF     | x             | {
        %1 = add i16 %X , i16 X
        store i16 %X , i16* %1
        FLG UU3ARU %X
}
SUBB    e       |F0     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        %1 = sub i8 %B , %0
        FLG UUAAAA %1 - %B %0
        %B = i8 %1
}
CMPB    e       |F1     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        %1 = sub i8 %B , %0
        FLG UUAAAA %1 - %B %0
}
SBCB    e       |F2     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        SBC %B %0
}
ANDB    e       |F4     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        %B = and i8 %B , %0
        FLG UUAARU %B
}
BITB    e       |F5     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        %1 = and i8 %B , %0
        FLG UUAARU %1
}
LDAB    e       |F6     | e1            | e2            | {
        %B = load i8 , i8* ED
        FLG UUAARU %B
}
STAB    e       |F7     | e1            | e2            | {
        store i8 %B , i8* ED
        FLG UUAARU %B
}
EORB    e       |F8     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        %B = xor i8 %B , %0
        FLG UUAARU %B
}
ADCB    e       |F9     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        ADC %B %0
}
ORAB    e       |FA     | e1            | e2            | {
        %0 = load i8 , i8 * ED
        %B = or i8 %B , %0
        FLG UUAARU %B
}
ADDB    e       |FB     | e1            | e2            | {
        %0 = load i8 , i8* ED
        %1 = add i8 %B , %0
        FLG AUAAAA %1 + %B %0
        %B = i8 %1
}
LDX     e       |FE     | e1            | e2            | {
        %X = load i16 , i16* ED
        FLG UU3ARU %X
}
STX     e       |FF     | e1            | e2            | {
        store i16 %X , i16* ED
        FLG UU3ARU %X
}
"""


class mc6800_ins(assy.Instree_ins):
    def __init__(self, pj, lim, lang):
        self.idx = "X"
        super(mc6800_ins, self).__init__(pj, lim, lang)

    def assy_d(self, pj):
        self.dstadr = self['d']
        return assy.Arg_dst(pj, self.dstadr)

    def assy_e(self, pj):
        self.dstadr = (self['e1'] << 8) | self['e2']
        return assy.Arg_dst(pj, self.dstadr)

    def assy_i(self, pj):
        return assy.Arg_imm(pj, self['i'], 8)

    def assy_I(self, pj):
        self.dstadr = (self['I1'] << 8) | self['I2']
        return assy.Arg_dst(pj, self.dstadr, "#")

    def assy_r(self, pj):
        a = self['r']
        if a & 0x80:
            a -= 256
        self.dstadr = self.hi + a
        if self.mne != "BRA":
            self.cc = self.mne[1:]
        return assy.Arg_dst(pj, self.dstadr)

    def assy_x(self, pj):
        return "0x%02x+" % self['x'] + self.idx

    def pilmacro_D(self):
        return "0x%02x" % self['d']

    def pilmacro_DST(self):
        return "0x%04x" % self.dstadr

    def pilmacro_ED(self):
        return "0x%02x%02x" % (self['e1'], self['e2'])

    def pilmacro_HI(self):
        return "0x%04x" % self.hi

    def pilmacro_II(self):
        return "0x%02x%02x" % (self['I1'], self['I2'])

    def pilmacro_IM(self):
        return "0x%02x" % self['i']

    def pilmacro_X(self):
        return "0x%02x" % self['x']

    def pilfunc_ADC(self, arg):
        self.add_il([
            [arg[0], '=', 'i8', 'undef'],
            ["%C", '=', 'ii', 'undef'],
            ["%H", '=', 'ii', 'undef'],
            ["%V", '=', 'ii', 'undef'],
            ["%N", '=', 'ii', 'undef'],
            ["%Z", '=', 'ii', 'undef'],
        ])

    def pilfunc_FLG(self, arg):
        p = arg[0]
        if arg[1] in ("%S", "%X"):
            sz = 16
        else:
            sz = 8
        for i in ('H', 'I', 'N', 'Z', 'V', 'C'):
            a = p[0]
            p = p[1:]
            if a == 'U':
                continue
            if a == 'R':
                self.add_il([["%" + i, '=', 'i1', '0']])
            elif a == 'S':
                self.add_il([["%" + i, '=', 'i1', '1']])
            elif i == 'C':
                assert len(arg) == 5
                assert arg[2] in ('-', '+')
                self.add_il([["%" + i, '=', 'i1', 'undef']])
            elif i == 'H':
                self.add_il([["%" + i, '=', 'i1', 'undef']])
            elif i == 'V':
                self.add_il([["%" + i, '=', 'i1', 'undef']])
            elif i == 'Z' and a == 'A':
                self.add_il([
                    ["%Z", "=", "icmp", "eq", "i8", arg[1], ",", "0"],
                ])
            elif i == 'N' and a in ('A', '1', '3'):
                self.add_il([
                    ["%0", "=", "lshr", "i%d" % sz, arg[1], ",", "%d" % (sz-1)],
                    ["%N", "=", "trunc", "i%d" % sz, "%0", "to", "i1"],
                ])
            elif a != 'U':
                print(i, a, arg, self)
                self.add_il([["%" + i, '=', 'i1', 'undef']])


class mc6800(assy.Instree_disass):
    def __init__(self, mask=0xffff):
        super(mc6800, self).__init__("mc6800", 8)
        self.it.load_string(mc6800_instructions)
        self.mask = mask
        self.pil = True
        self.myleaf = mc6800_ins

    def codeptr(self, pj, adr):
        t = pj.m.bu16(adr)
        c = data.Codeptr(pj, adr, adr + 2, t)
        pj.todo(t, self.disass)
        return c

    def vectors(self, pj, adr=0xfff8):
        for v in ("IRQ", "SWI", "NMI", "RST"):
            c = self.codeptr(pj, adr)
            pj.set_label(c.dst, "VEC" + v)
            adr += 2


mc68hc11_instructions = """
IDIV    -               |02     |
FDIV    -               |03     |
LSRD    -               |04     |
ASLD    -               |05     |

+       Y               |18     |

BRSET   d,i,r,>C        |12     | d             | i             | r             |
BRCLR   d,i,r,>C        |13     | d             | i             | r             |
BSET    d,i             |14     | d             | i             |
BCLR    d,i             |15     | d             | i             |

CPD     I               |1A     |83     | I1            | I2            |
CPD     d               |1A     |93     | d             |
CPD     x               |1A     |A3     | x             |
CPD     e               |1A     |B3     | e1            | e2            |
CPD     y               |CD     |A3     | y             |

LDY     x               |1A     |EE     | x             |
STY     x               |1A     |EF     | x             |

LDX     y               |CD     |EE     | y             |
STX     y               |CD     |EF     | y             |


BSET    x,i             |1C     | x             | i             |
BCLR    x,i             |1D     | x             | i             |
BRSET   x,i,r,>C        |1E     | x             | i             | r             |
BRCLR   x,i,r,>C        |1F     | x             | i             | r             |

ABX     -               |3A     |

PSHX    -               |3C     |
MUL     -               |3D     |

PULX    -               |38     |

SUBD    I               |83     | I1            | I2            |
SUBD    d               |93     | d             |
SUBD    x               |A3     | x             |
SUBD    e               |B3     | e1            | e2            |

ADDD    I               |C3     | I1            | I2            |
ADDD    d               |D3     | d             |
ADDD    x               |E3     | x             |
ADDD    e               |F3     | e1            | e2            |

XGDX    -               |8F     |

LDD     I               |CC     | I1            | I2            |
LDD     d               |DC     | d             |
LDD     x               |EC     | x             |
LDD     e               |FC     | e1            | e2            |

STD     d               |DD     | d             |
STD     x               |ED     | x             |
STD     e               |FD     | e1            | e2            |

"""


class mc68hc11_ins(mc6800_ins):
    pass

    def assy_y(self, pj):
        return "0x%02x+Y" % self['y']

    def assy_Y(self, pj):
        if self.mne[-1] == "X":
            self.mne = self.mne[:-1] + "Y"
        self.idx = "Y"


class mc68hc11(mc6800):
    def __init__(self, mask=0xffff):
        super(mc68hc11, self).__init__(mask=mask)
        self.it.load_string(mc68hc11_instructions)
        self.myleaf = mc68hc11_ins

    def register_labels(self, pj):
        pj.set_label(0x1000, "PORTA")
        pj.set_label(0x1002, "PIOC")
        pj.set_label(0x1003, "PORTC")
        pj.set_label(0x1004, "PORTB")
        pj.set_label(0x1005, "PORTCL")
        pj.set_label(0x1007, "DDRC")
        pj.set_label(0x1008, "PORTD")
        pj.set_label(0x1009, "DDRD")
        pj.set_label(0x100A, "PORTE")
        pj.set_label(0x100B, "CFORC")
        pj.set_label(0x100C, "OC1M")
        pj.set_label(0x100D, "OC1D")
        pj.set_label(0x100E, "TCNTH")
        pj.set_label(0x100F, "TCNTL")

        pj.set_label(0x1010, "TIC1H")
        pj.set_label(0x1011, "TIC1L")
        pj.set_label(0x1012, "TIC2H")
        pj.set_label(0x1013, "TIC2L")
        pj.set_label(0x1014, "TIC3H")
        pj.set_label(0x1015, "TIC4L")
        pj.set_label(0x1016, "TOC1H")
        pj.set_label(0x1017, "TOC1L")
        pj.set_label(0x1018, "TOC2H")
        pj.set_label(0x1019, "TOC2L")
        pj.set_label(0x101A, "TOC3H")
        pj.set_label(0x101B, "TOC3L")
        pj.set_label(0x101C, "TOC4H")
        pj.set_label(0x101D, "TOC4L")
        pj.set_label(0x101E, "TI4_O5H")
        pj.set_label(0x101F, "TI4_O5L")

        pj.set_label(0x1020, "TCTL1")
        pj.set_label(0x1021, "TCTL2")
        pj.set_label(0x1022, "TMSK1")
        pj.set_label(0x1023, "TFLG1")
        pj.set_label(0x1024, "TMSK2")
        pj.set_label(0x1025, "TFLG2")
        pj.set_label(0x1026, "PACTL")
        pj.set_label(0x1027, "PACNT")
        pj.set_label(0x1028, "SPCR")
        pj.set_label(0x1029, "SPSR")
        pj.set_label(0x102A, "SPDR")
        pj.set_label(0x102B, "BAUD")
        pj.set_label(0x102C, "SCCR1")
        pj.set_label(0x102D, "SCCR2")
        pj.set_label(0x102E, "SCSR")
        pj.set_label(0x102F, "SCDR")

        pj.set_label(0x1030, "ADCTL")
        pj.set_label(0x1031, "ADR1")
        pj.set_label(0x1032, "ADR2")
        pj.set_label(0x1033, "ADR3")
        pj.set_label(0x1034, "ADR4")
        pj.set_label(0x1035, "BPROT")
        pj.set_label(0x1036, "EPROG")
        pj.set_label(0x1039, "OPTION")
        pj.set_label(0x103A, "COPRST")
        pj.set_label(0x103B, "PPROG")
        pj.set_label(0x103C, "HPRIO")
        pj.set_label(0x103D, "INIT")
        pj.set_label(0x103F, "CONFIG")

    def vectors(self, pj, adr=0xffd6):
        for v in (
          "SCI",
          "SPI",  "PAI", "PAO",  "TO",
          "I4O5", "OC4", "OC3",  "OC2",
          "OC1",  "IC3", "IC2",  "IC1",
          "RTI",  "IRQ", "XIRQ", "SWI",
          "ILL",  "COP", "CME",  "RESET"):
            c = self.codeptr(pj, adr)
            pj.set_label(c.dst, "VEC" + v)
            adr += 2
