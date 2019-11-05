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

'''Intel 4004/MCS-4

"Worlds First Micro Processor"

address_space(1) = data_ram_character
address_space(2) = data_ram_status
address_space(3) = rom_port
address_space(4) = ram_port
address_space(5) = TEST pin on i4004
'''

from pyreveng import assy

mcs4_desc = """
NOP	-		|0 0 0 0|0 0 0 0|
JCN	cc,adr,>JC	|0 0 0 1| cc    | adr		| {
	JCN
}
FIM	rr,data		|0 0 1 0| rr  |0| data		| {
	RR = i8 DATA
}
SRC	rr		|0 0 1 0| rr  |1| {
	%SRC = i8 RR
}
FIN	rr,(rr0)	|0 0 1 1| rr  |0| {
	%0 = i12 PCT
	%1 = zext i8 %RR0 to i12
	%2 = add i12 %0 , %1
	RR = load i8 , i8* %2
}
JIN	rr		|0 0 1 1| rr  |1|
JUN	ladr,>J		|0 1 0 0| ahi	| alo		| {
	br label ADR
}
JMS	ladr,>C		|0 1 0 1| ahi	| alo		| {
	call label ADR
}
INC	r		|0 1 1 0| r	| {
	R = add i4 R , 1
}
ISZ	r,adr,isz,>JC	|0 1 1 1| r	| adr		| {
	R = add i4 R , 1
	%0 = icmp i4 R , 0
	br i1 %0 , SKIP , NEXT
}
ADD	r		|1 0 0 0| r	| {
	%0 = zext i1 %C to i4
	%C = pyreveng.carry.add ( %A , R , %0 )
	%1 = add i4 %A , %0
	%A = add i4 %1, R
}
# XXX: IL: %C inverted ?
SUB	r		|1 0 0 1| r	| {
	%0 = zext i1 %C to i4
	%1 = xor i4 %0 , 0x1
	%2 = xor i4 R , 0xf
	%C = pyreveng.carry.add ( %A , %2 , %1 )
	%3 = add i4 %A , %1
	%A = add i4 %3, R
}
LD	r		|1 0 1 0| r	| {
	%A = i4 R
}
XCH	r		|1 0 1 1| r	| {
	%0 = i4 %A
	%A = i4 R
	R = i4 %0
}
BBL	d,>R		|1 1 0 0| d	| {
	%A = i4 D
	return
}
LDM	d		|1 1 0 1| d	| {
	%A = i4 D
}
WRM	-		|1 1 1 0|0 0 0 0| {
	store i4 %A, i4 addrspace(1) * %SPC
}
WMP	-		|1 1 1 0|0 0 0 1| {
	store i4 %A, i4 addrspace(4) * %SPC
}
WRR	-		|1 1 1 0|0 0 1 0| {
	store i4 %A, i4 addrspace(3) * %SPC
}
WPM	-		|1 1 1 0|0 0 1 1|
WR	-		|1 1 1 0|0 1|sr | {
	%0 = zext i1 %SPC to i10
	%1 = %0 or i10 %0 , SR
	store i4 %A, i4 addrspace(2) * %1
}
SBM	-		|1 1 1 0|1 0 0 0| {
	%0 = load i4 addrspace(1)* %SPC
	%1 = zext i1 %C to i4
	%2 = xor i4 %1 , 0x1
	%3 = xor i4 %0 , 0xf
	%C = pyreveng.carry.add ( %A , %3 , %2 )
	%4 = add i4 %A , %1
	%A = add i4 %4, %0
}
RDM	-		|1 1 1 0|1 0 0 1| {
	%A = load i4 addrspace(1)* %SPC
}
RDR	-		|1 1 1 0|1 0 1 0| {
	%A = load i4 addrspace(3)* %SPC
}
ADM	-		|1 1 1 0|1 0 1 1| {
	%0 = load i4 addrspace(1)* %SPC
	%1 = zext i1 %C to i4
	%C = pyreveng.carry.add ( %A , %0 , %1 )
	%2 = add i4 %A , %0
	%A = add i4 %1, %2
}
RD	sr		|1 1 1 0|1 1|sr | {
	%0 = zext i1 %SPC to i10
	%1 = %0 or i10 %0 , SR
	%A = load i4 addrspace(2)* %1
}
CLB	-		|1 1 1 1|0 0 0 0| {
	%A = i4 0
	%C = i1 0
}
CLC	-		|1 1 1 1|0 0 0 1| {
	%C = i1 0
}
IAC	-		|1 1 1 1|0 0 1 0| {
	%0 = zext i1 %C to i4
	%C = pyreveng.carry.add ( %A , %0 , 1 )
	%1 = add i4 %A , 1
	%A = add i4 %1 , %0
}
CMC	-		|1 1 1 1|0 0 1 1| {
	%C = xor i1 %C , 1
}
CMA	-		|1 1 1 1|0 1 0 0| {
	%A = xor i4 %A , 0xf
}
RAL	-		|1 1 1 1|0 1 0 1| {
	%0 = shr i4 %A , 3
	%1 = shl i4 %A , 1
	%2 = zext i1 %C to i4
	%C = trunc i4 %0 , i1
	%A = or i4 %1 , %2
}
RAR	-		|1 1 1 1|0 1 1 0| {
	%1 = zext i1 %C to i4
	%C = trunc i4 %A to i1
	%2 = shr i4 %A , 1
	%3 = shl i4 %1 , 3
	%A = or i4 %2 , %3
}
TCC	-		|1 1 1 1|0 1 1 1| {
	%A = zext i1 %C to i4
	%C = i1 0
}
DAC	-		|1 1 1 1|1 0 0 0| {
	%C = icmp ne i4 %A 0xf 
	%A = sub i4 %A , 1
}
TCS	-		|1 1 1 1|1 0 0 1|
STC	-		|1 1 1 1|1 0 1 0| {
	%C = i1 1
}
DAA	-		|1 1 1 1|1 0 1 1| {
	%0 = icmp gt i4 %A , 9
	%1 = or i1 %C , %0
	br %1 label %2 , NEXT
%2:
	%3 = pyreveng.carry.add ( %A , 6 )
	%A = add i4 %A , 6
	%C = or i1 %C , %3
}
KBP	-		|1 1 1 1|1 1 0 0|
DCL	-		|1 1 1 1|1 1 0 1|
"""

class mcs4_ins(assy.Instree_ins):

    def assy_data(self):
        return assy.Arg_imm(self['data'], 8)

    def assy_d(self):
        return assy.Arg_imm(self['d'], 4)

    def assy_cc(self):
        self.cc = {
            0x1: "JNT",
            0x2: "JC",
            0x4: "JZ",
            0x9: "JT",
            0xa: "JNC",
            0xc: "JNZ",
        }.get(self['cc'])
        if self.cc is None:
            self.cc = "CC#0x%x" % self['cc']
        return self.cc

    def assy_sr(self):
        self.mne += "%d" % self['sr']

    def assy_r(self):
        return "r%d" % self['r']

    def assy_rr(self):
        return "rr%d" % (self['rr'] << 1)

    def assy_adr(self):
        self.dstadr = (self.lo & ~0xff) | self['adr']
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_ladr(self):
        self.dstadr = (self['ahi'] << 8) | self['alo']
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_isz(self):
        self.cc = "Z"

    def pilmacro_R(self):
        return "%%R%d" % self['r']

    def pilmacro_RR(self):
        return "%%RR%d" % (self['rr'] << 1)

    def pilmacro_PCT(self):
        return "0x%03x" % (self.lo & 0xf00)

    def pilmacro_DATA(self):
        return "0x%02x" % self['data']

    def pilmacro_D(self):
        return "0x%01x" % self['d']

    def pilmacro_ADR(self):
        return "0x%01x%02x" % (self['ahi'], self['alo'])

    def pilmacro_SR(self):
        return "0x%03x" % (self['sr'] << 8)

    def pilmacro_NEXT(self):
        return "0x%03x" % self.hi

    def pilmacro_SKIP(self):
        return "0x%01x%02x" % (self.hi >> 8, self['adr'])

    def pilmacro_JCN(self):
        cc = self['cc']
        l = []
        l.append(["%0", "=", "i1", "0"])
        if cc & 0x4:
            l.append(["%1", "=", "icmp", "eq", "i4", "%A", ",", "0"])
            l.append(["%0", "=", "or", "i1", "%0", ",", "%1"])
        if cc & 0x2:
            l.append(["%0", "=", "or", "i1", "%0", ",", "%C"])
        if cc & 0x1:
            l.append(["%2", "=", "load", "i1", "addrspace", "(", "5", ")", "*", "0"])
            l.append(["%0", "=", "or", "i1", "%0", ",", "%TEST"])
        if cc & 0x8:
            l.append(["br", "i1", "%0", ",", "NEXT", ",", "SKIP"])
        else:
            l.append(["br", "i1", "%0", ",", "SKIP", ",", "NEXT"])
        self.add_il(l)

class mcs4(assy.Instree_disass):
    def __init__(self):
        super().__init__(
            "mcs4",
            ins_word=8,
            abits=12,
        )
        self.it.load_string(mcs4_desc, mcs4_ins)
        self.verbatim += ("(rr0)",)
