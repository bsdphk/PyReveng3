#!/usr/bin/env python
#
# Copyright (c) 2012-2014 Poul-Henning Kamp <phk@phk.freebsd.dk>
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

'''Hewlett Packard Saturn (1LT8) CPU
'''

from pyreveng import assy

SATURN_INSTRUCTIONS = '''

# Page references to pdf-page asmtut.pdf

# 33.1.1/61
LA		v		|1 0 0 0|0 0 0 0|1 0 0 0|0 0 1 0| v	|
LC		v		|0 0 1 1| v	|

# 33.1.2/61
x=0		A,x		|1 1 0 1|0 0|r	|
x=0		f,x		|1 0 1 0|1| f	|0 0|r	|

# 33.1.3/64
ABIT=d		d,m		|1 0 0 0|0 0 0 0|1 0 0 0|0 1 0|d| m	|
CBIT=d		d,m		|1 0 0 0|0 0 0 0|1 0 0 0|1 0 0|d| m	|

# 33.1.4/66
xyEX		A,x,y		|1 1 0 1|1 1| r	|
xyEX		f,x,y		|1 0 1 0|1| f	|1 1| r	|

# 33.1.5/67
# NB: asmtut.pdf and SASM.DOC disagrees.
# The latter looks more systematic, so we follow that.
x=y		A,x,y		|1 1 0 1|0 1| r	|
x=y		f,x,y		|1 0 1 0|1| f	|0 1| r	|
y=x		A,x,y		|1 1 0 1|1 0| r	|
y=x		f,x,y		|1 0 1 0|1| f	|1 0| r	|

# 33.2.1/68
x=x+1		A,x		|1 1 1 0|0 1| r	|
x=x+1		f,x		|1 0 1 1|0| f	|0 1| r	|

# 33.2.3/70
x=x+y		A,x,y		|1 1 0 0|0 0| r	|
x=x+y		f,x,y		|1 0 1 0|0| f	|0 0| r	|
y=y+x		A,x,y		|1 1 0 0|1 0| r	|
y=y+x		f,x,y		|1 0 1 0|0| f	|1 0| r	|

# 33.2.4/71
x=x+x		A,x		|1 1 0 0|0 1| r	|
x=x+x		f,x		|1 0 1 0|0| f	|0 1| r	|

# 33.2.5/71
x=x+		A,n,x		|1 0 0 0|0 0 0 1|1 0 0 0|1 1 1 1|0 0| r	| n	|
x=x+		f,n,x		|1 0 0 0|0 0 0 1|1 0 0 0|0|  f	|0 0| r	| n	|

# 33.2.6/73
x=x-1		A,x		|1 1 0 0|1 1| r |
x=x-1		f,x		|1 0 1 0|0|  f	|1 1| r |

# 33.2.7/73
x=x-y		A,x,y		|1 1 1 0|0 0| r |
x=x-y		f,x,y		|1 0 1 1|0| f	|0 0| r	|
y=y-x		A,x,y		|1 1 1 0|1 0| r |
y=y-x		f,x,y		|1 0 1 1|0| f	|1 0| r	|
x=y-x		A,x,y		|1 1 1 0|1 1| r |
x=y-x		f,x,y		|1 0 1 1|0| f	|1 1| r	|

# 33.2.11/77
x=x-		A,n,x		|1 0 0 0|0 0 0 1|1 0 0 0|1 1 1 1|1 0| r | n	|
x=x-		f,n,x		|1 0 0 0|0 0 0 1|1 0 0 0|0| f	|1 0| r | n	|

# 33.2.12/77
x=-x-1		A,x		|1 1 1 1|1 1| r	|
x=-x-1		f,x		|1 0 1 1|1| f	|1 1| r	|

# 33.2.13/78
x=-x		A,x		|1 1 1 1|1 0| r	|
x=-x		f,x		|1 0 1 1|1|  f	|1 0| r	|

# 33.2.14.1/79
x=x!y		A,x,y		|0 0 0 0|1 1 1 0|1 1 1 1|1 0|r	|
x=x!y		f,x,y		|0 0 0 0|1 1 1 0|0|  f	|1 0|r	|
y=y!x		A,x,y		|0 0 0 0|1 1 1 0|1 1 1 1|1 1|r	|
y=y!x		f,x,y		|0 0 0 0|1 1 1 0|0|  f	|1 1|r	|

# 33.2.14.2/79
x=x&y		A,x,y		|0 0 0 0|1 1 1 0|1 1 1 1|0 0|r	|
x=x&y		f,x,y		|0 0 0 0|1 1 1 0|0|  f	|0 0|r	|
y=y&x		A,x,y		|0 0 0 0|1 1 1 0|1 1 1 1|0 1|r	|
y=y&x		f,x,y		|0 0 0 0|1 1 1 0|0|  f	|0 1|r	|

# 33.2.15/81
xSL		A,x		|1 1 1 1|0 0| r	|
xSL		f,x		|1 0 1 1|1| f	|0 0| r	|
xSR		A,x		|1 1 1 1|0 1| r	|
xSR		f,x		|1 0 1 1|1| f	|0 1| r	|

# 33.2.16/81
xSLC		x		|1 0 0 0|0 0 0 1|0 0| r	|
xSRC		x		|1 0 0 0|0 0 0 1|0 1| r	|

# 33.2.17/82
xSRB		x		|1 0 0 0|0 0 0 1|1 1| r	|

# 33.2.17.1/82
xSRB		A,x		|1 0 0 0|0 0 0 1|1 0 0 1|1 1 1 1|0 0| r	|
xSRB		f,x		|1 0 0 0|0 0 0 1|1 0 0 1|0|  f	|0 0| r	|

# 34.1/84
Rd=z		d,z		|0 0 0 1|0 0 0 0|r| d	|

# 34.2/85
Rd=z		A,d,z		|1 0 0 0|0 0 0 1|1 0 1 0|1 1 1 1|0 0 0 0|r|  d	|
Rd=z		f,d,z		|1 0 0 0|0 0 0 1|1 0 1 0|0| f	|0 0 0 0|r|  d	|

# 34.3/85
z=Rd		d,z		|0 0 0 1|0 0 0 1|r| d	|

# 34.4/86
z=Rd		A,z,d		|1 0 0 0|0 0 0 1|1 0 1 0|1 1 1 1|0 0 0 1|r| d	|
z=Rd		f,z,d		|1 0 0 0|0 0 0 1|1 0 1 0|0|  f  |0 0 0 1|r| d	|

# 34.5/86
zRdEX		z,d		|0 0 0 1|0 0 1 0|r| d	|

# 34.6/87
zRdEX		A,z,d		|1 0 0 0|0 0 0 1|1 0 1 0|1 1 1 1|0 0 1 0|r| d	|
zRdEX		f,z,d		|1 0 0 0|0 0 0 1|1 0 1 0|0| f	|0 0 1 0|r| d	|

# 35.1/88
Dd=		d,abs2		|0 0 0 1|1|d|0 1| c1	| c2	|
Dd=		d,abs4		|0 0 0 1|1|d|1 0| c1	| c2	| c3	| c4	|
Dd=		d,abs5		|0 0 0 1|1|d|1 1| c1	| c2	| c3	| c4	| c5	|

# 35.2/88
D0=D0+		n		|0 0 0 1|0 1 1 0| n	|
D0=D0-		n		|0 0 0 1|1 0 0 0| n	|
D1=D1+		n		|0 0 0 1|0 1 1 1| n	|
D1=D1-		n		|0 0 0 1|1 1 0 0| n	|

# 35.3/89
Dd=z		z,d		|0 0 0 1|0 0 1 1|0|r|0|d|
Dd=zS		z,d		|0 0 0 1|0 0 1 1|1|r|0|d|

# 35.4/89
zDdEX		z,d		|0 0 0 1|0 0 1 1|0|r|1|d|

# 35.5
zDdXS		z,d		|0 0 0 1|0 0 1 1|1|r|1|d|

# 36/94

z=DATd		A,z,d		|0 0 0 1|0 1 0 0|0|r|1|d|
z=DATd		B,z,d		|0 0 0 1|0 1 0 0|1|r|1|d|
z=DATd		f,z,d		|0 0 0 1|0 1 0 1|0|r|1|d| f	|

# 37/95
z=DATd		n,z,d		|0 0 0 1|0 1 0 1|1|r|1|d| n	|

# 38/95
DATd=z		A,d,z		|0 0 0 1|0 1 0 0|0|r|0|d|
DATd=z		B,d,z		|0 0 0 1|0 1 0 0|1|r|0|d|
DATd=z		f,d,z		|0 0 0 1|0 1 0 1|0|r|0|d|0|f	|

# 39/96
DATd=z		n,d,z		|0 0 0 1|0 1 0 1|1|r|0|d| n	|

# 41.1/98
GOC		rel2,>JC	|0 1 0 0| c1	| c2	|
GONC		rel2,>JC	|0 1 0 1| c1	| c2	|

# 41.2/98
GOTO		rel3,>J		|0 1 1 0| c1	| c2	| c3	|

# 41.2.2/99
GOLONG		rel4,>J		|1 0 0 0|1 1 0 0| c1	| c2	| c3	| c4	|

# 41.2.3/99
GOVLNG		abs5,>J		|1 0 0 0|1 1 0 1| c1	| c2	| c3	| c4	| c5	|

# 41.2.4/99
PC=z		z,>J		|1 0 0 0|0 0 0 1|1 0 1 1|0 0 1|r|

# 41.2.5/99
zPCEX		z,>J		|1 0 0 0|0 0 0 1|1 0 1 1|0 1 1|r|

# 41.2.6/99
PC=(z)		z,>J		|1 0 0 0|0 0 0 0|1 0 0 0|1 1|r|0|

# 41.2.7/99
# NB: fejl i asmtut.pdf
z=PC		z		|1 0 0 0|0 0 0 1|1 0 1 1|0 1 0|r|

# 42.1/100
GOSUB		rel3b,>C	|0 1 1 1| c1	| c2	| c3	|

# 42.2/100
GOSUBL		rel4b,>C	|1 0 0 0|1 1 1 0| c1	| c2	| c3	| c4	|

# 42.3/101
GOSBVL		abs5,>C		|1 0 0 0|1 1 1 1| c1	| c2	| c3	| c4	| c5	|

# 42.4/101
RTN		>R		|0 0 0 0|0 0 0 1|
RTNSC		>R		|0 0 0 0|0 0 1 0|
RTNCC		>RC		|0 0 0 0|0 0 1 1|
RTI		>R		|0 0 0 0|1 1 1 1|
RTNSXM		>R		|0 0 0 0|0 0 0 0|

# 42.5/101
RTNC		>RC		|0 1 0 0|0 0 0 0|0 0 0 0|
RTNNC		>RC		|0 1 0 1|0 0 0 0|0 0 0 0|

# 43.1.1/102
?x=0		A,x,rel2,>JC	|1 0 0 0|1 0 1 0|1 0| r	| c1	| c2	|
?x=0		f,x,rel2,>JC	|1 0 0 1|0|  f  |1 0| r	| c1	| c2	|

# 43.1.2/102
?x≠0		A,x,rel2,>JC	|1 0 0 0|1 0 1 0|1 1| r | c1	| c2	|
?x≠0		f,x,rel2,>JC	|1 0 0 1|0|  f	|1 1| r | c1	| c2	|

# 43.2/103
?x=y		A,x,y,rel2,>JC	|1 0 0 0|1 0 1 0|0 0| r	| c1	| c2	|
?x=y		f,x,y,rel2,>JC	|1 0 0 1|0| f	|0 0| r | c1	| c2	|

# 43.3/103
?x≠y		A,x,y,rel2,>JC	|1 0 0 0|1 0 1 0|0 1| r	| c1	| c2	|
?x≠y		f,x,y,rel2,>JC	|1 0 0 1|0| f	|0 1| r | c1	| c2	|

# 43.4/103
?x>y		A,rel2,x,y,>JC	|1 0 0 0|1 0 1 1|0 0| r	| c1	| c2	|
?x>y		f,rel2,x,y,>JC	|1 0 0 1|1|  f	|0 0| r	| c1	| c2	|
?y>x		A,rel2,x,y,>JC	|1 0 0 0|1 0 1 1|0 1| r	| c1	| c2	|
?y>x		f,rel2,x,y,>JC	|1 0 0 1|1|  f	|0 1| r	| c1	| c2	|

# 43.5/103
?x>=y		A,rel2,x,y,>JC	|1 0 0 0|1 0 1 1|1 0| r	| c1	| c2	|
?x>=y		f,rel2,x,y,>JC	|1 0 0 1|1|  f	|1 0| r	| c1	| c2	|
?y>=x		A,rel2,x,y,>JC	|1 0 0 0|1 0 1 1|1 1| r	| c1	| c2	|
?y>=x		f,rel2,x,y,>JC	|1 0 0 1|1|  f	|1 1| r	| c1	| c2	|

# 43.6/104
?ABIT=d		d,m,rel2,>JC	|1 0 0 0|0 0 0 0|1 0 0 0|0 1 1|d| m	| c1	| c2	|
?CBIT=d		d,m,rel2,>JC	|1 0 0 0|0 0 0 0|1 0 0 0|1 0 1|d| m	| c1	| c2	|

# 44/104
P=		m		|0 0 1 0| m	|
P=P+1		-		|0 0 0 0|1 1 0 0|
P=P+1		-		|0 0 0 0|1 1 0 1|
?P≠		m,rel2,>JC	|1 0 0 0|1 0 0 0| m	| c1	| c2	|
?P=		m,rel2,>JC	|1 0 0 0|1 0 0 1| m	| c1	| c2	|
C=P		m		|1 0 0 0|0 0 0 0|1 1 0 0| m	|
P=C		m		|1 0 0 0|0 0 0 0|1 1 0 1| m	|
C=C+P+1		-		|1 0 0 0|0 0 0 0|1 0 0 1|
CPEX		m		|1 0 0 0|0 0 0 0|1 1 1 1| m	|

# 45/106
RSTK=C		-		|0 0 0 0|0 1 1 0|
C=RSTK		-		|0 0 0 0|0 1 1 1|

# 46/106
OUT=CS		-		|1 0 0 0|0 0 0 0|0 0 0 0|
OUT=C		-		|1 0 0 0|0 0 0 0|0 0 0 1|
A=IN		-		|1 0 0 0|0 0 0 0|0 0 1 0|
C=IN		-		|1 0 0 0|0 0 0 0|0 0 1 1|

# 47/107
CLRST		-		|0 0 0 0|1 0 0 0|
C=ST		-		|0 0 0 0|1 0 0 1|
ST=C		-		|0 0 0 0|1 0 1 0|
CSTEX		-		|0 0 0 0|1 0 1 1|
ST=0		m		|1 0 0 0|0 1 0 0| m	|
ST=1		m		|1 0 0 0|0 1 0 1| m	|
?ST=0		m,rel2,>JC	|1 0 0 0|0 1 1 0| m	| c1	| c2	|
?ST=1		m,rel2,>JC	|1 0 0 0|0 1 1 1| m	| c1	| c2	|

# 48/108
CLRHST		-		|1 0 0 0|0 0 1 0|1 1 1 1|
XM=0		-		|1 0 0 0|0 0 1 0|0 0 0 1|
SB=0		-		|1 0 0 0|0 0 1 0|0 0 1 0|
SR=0		-		|1 0 0 0|0 0 1 0|0 1 0 0|
MP=0		-		|1 0 0 0|0 0 1 0|1 0 0 0|
HST=0		m		|1 0 0 0|0 0 1 0| m	|
?XM=0		rel2,>JC	|1 0 0 0|0 0 1 1|0 0 0 1| c1	| c2	|
?SB=0		rel2,>JC	|1 0 0 0|0 0 1 1|0 0 1 0| c1	| c2	|
?SR=0		rel2,>JC	|1 0 0 0|0 0 1 1|0 1 0 0| c1	| c2	|
?MP=0		rel2,>JC	|1 0 0 0|0 0 1 1|1 0 0 0| c1	| c2	|
?HS=0		m,rel2,>JC	|1 0 0 0|0 0 1 1| m	| c1	| c2	|

# 49/109
SETHEX		-		|0 0 0 0|0 1 0 0|
SETDEC		-		|0 0 0 0|0 1 0 1|

# 50/110
INTOFF		-		|1 0 0 0|0 0 0 0|1 0 0 0|1 1 1 1|
INTON		-		|1 0 0 0|0 0 0 0|1 0 0 0|0 0 0 0|
RSI		-		|1 0 0 0|0 0 0 0|1 0 0 0|0 0 0 1|0 0 0 0|

# 51/111
RESET		-		|1 0 0 0|0 0 0 0|1 0 1 0|
SREQ?		-		|1 0 0 0|0 0 0 0|1 1 1 0|
CONFIG		-		|1 0 0 0|0 0 0 0|0 1 0 1|
UNCNFG		-		|1 0 0 0|0 0 0 0|0 1 0 0|
C=ID		-		|1 0 0 0|0 0 0 0|0 1 1 0|
SHUTDN		-		|1 0 0 0|0 0 0 0|0 1 1 1|
BUSCB		-		|1 0 0 0|0 0 0 0|1 0 0 0|0 0 1 1|
BUSCC		-		|1 0 0 0|0 0 0 0|1 0 1 1|
BUSCD		-		|1 0 0 0|0 0 0 0|1 0 0 0|1 1 0 1|

# 52/112
NOP3		-		|0 1 0 0|0 0 1 0|0 0 0 0|
NOP4		-		|0 1 1 0|0 0 1 1|0 0 0 0|0 0 0 0|
NOP5		-		|0 1 1 0|0 1 0 0|0 0 0 0|0 0 0 0|0 0 0 0|

'''

class Saturn_Ins(assy.Instree_ins):

    def assy_abs2(self):
        self.dstadr = self['c1']
        self.dstadr |= self['c2'] << 4
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_abs4(self):
        self.dstadr = self['c1']
        self.dstadr |= self['c2'] << 4
        self.dstadr |= self['c3'] << 8
        self.dstadr |= self['c4'] << 12
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_abs5(self):
        self.dstadr = self['c1']
        self.dstadr |= self['c2'] << 4
        self.dstadr |= self['c3'] << 8
        self.dstadr |= self['c4'] << 12
        self.dstadr |= self['c5'] << 16
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_d(self):
        ''' Select {DAT}d '''
        d = self['d']
        if d > 4:
            raise assy.Invalid("R4 is last register")
        self.mne = self.mne.replace('d', '%d' % self['d'])

    def assy_f(self):
        ''' Select fields '''
        self.mne += "." + ["P", "WP", "XS", "X", "S", "M", "B", "W"][self['f']]

    def assy_n(self):
        return "0x%x" % (1 + self['n'])

    def assy_m(self):
        return "0x%x" % (self['m'])

    def assy_rel2(self):
        self.dstadr = self['c1']
        self.dstadr |= self['c2'] << 4
        if self.dstadr & 0x80:
            self.dstadr -= 0x100
        self.dstadr += (self.hi - 2)
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_rel3(self):
        self.dstadr = self['c1']
        self.dstadr |= self['c2'] << 4
        self.dstadr |= self['c3'] << 8
        if self.dstadr & 0x800:
            self.dstadr -= 0x1000
        self.dstadr += (self.hi - 3)
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_rel3b(self):
        self.dstadr = self['c1']
        self.dstadr |= self['c2'] << 4
        self.dstadr |= self['c3'] << 8
        if self.dstadr & 0x800:
            self.dstadr -= 0x1000
        self.dstadr += self.hi
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_rel4(self):
        self.dstadr = self['c1']
        self.dstadr |= self['c2'] << 4
        self.dstadr |= self['c3'] << 8
        self.dstadr |= self['c4'] << 12
        if self.dstadr & 0x8000:
            self.dstadr -= 0x10000
        self.dstadr += (self.hi - 4)
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_rel4b(self):
        self.dstadr = self['c1']
        self.dstadr |= self['c2'] << 4
        self.dstadr |= self['c3'] << 8
        self.dstadr |= self['c4'] << 12
        if self.dstadr & 0x8000:
            self.dstadr -= 0x10000
        self.dstadr += self.hi
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_v(self):
        ''' variable length constants '''
        v = self['v'] + 1
        s = 0
        j = 0
        for _i in range(v):
            j |= self.lang.m[self.hi] << s
            self.hi += 1
            s += 4
        f = "#0x%%0%dx" % v
        return f % j

    def assy_x(self):
        ''' Select x from [ABCD] '''
        self.mne = self.mne.replace('x', 'ABCD'[self['r']])

    def assy_y(self):
        ''' Select y from [BCAC] '''
        self.mne = self.mne.replace('y', 'BCAC'[self['r']])

    def assy_z(self):
        ''' Select z from [AC] '''
        self.mne = self.mne.replace('z', 'AC'[self['r']])

    def assy_A(self):
        self.mne += ".A"

    def assy_B(self):
        self.mne += ".B"


class Saturn(assy.Instree_disass):
    def __init__(self):
        super().__init__(
            "saturn",
            ins_word=4,
            abits=20,
        )
        self.m.ncol = 10
        self.add_ins(SATURN_INSTRUCTIONS, Saturn_Ins)
