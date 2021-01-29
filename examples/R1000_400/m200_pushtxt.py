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

'''
   Recognize pushing a text-string onto the stack
'''

from pyreveng import data, assy
import pyreveng.cpu.m68020 as m68020

M200_PUSHTXT_DESC = '''

+PTA		-		|0 0 1 0|sreg |0|0 1 0 0|1 1 1 1|
+PTB		-		|0 1 0 0|areg |1|1 1 1 1|1 0 1 0|x				|
+PTC		-		|0 1 1 1|dreg |0|0| y		|
+PTDB+		-		|0 0 0 1|sreg |0|1 1 0 1|1|areg |
+PTDW-		-		|0 0 1 1|sreg |1|0 0 1 0|0|areg |
+PTDL-		-		|0 0 1 0|sreg |1|0 0 1 0|0|areg |
PUSHTXT		pushtxt		|0 1 0 1|0 0 0 1|1 1 0 0 1|dreg | FF | FC |

'''

class M200PushtxtIns(m68020.m68020_ins):
    ''' pushtxt pseudo-instructions '''

    def assy_pushtxt(self):
        if len(self.lim) == 5 and self.lim[0].assy[0] == "+PTA":
            sreg = self.lim[0]['sreg']
            lim = self.lim[-4:]
            off = self.lo + 4
        elif len(self.lim) == 4:
            sreg = 7
            lim = self.lim
            off = self.lo + 2
        else:
            raise assy.Invalid()
        for i, j in zip(lim, ("+PTB", "+PTC", "+PTD", "PUSH")):
            if i.assy[0][:4] != j:
                raise assy.Invalid()
        if lim[0]['areg'] != lim[2]['areg']:
            raise assy.Invalid()
        if lim[1]['dreg'] != self['dreg']:
            raise assy.Invalid()
        if lim[2]['sreg'] != sreg:
            raise assy.Invalid()
        adr = off + lim[0]['x'] - (1<<16)
        length = lim[1]['y'] + 1
        length *= {
            'B': 1,
            'W': 2,
            'L': 4,
        }[lim[2].assy[0][4]]
        if lim[2].assy[0][-1] == '-':
            adr -= length
        elif lim[2].assy[0][-1] != '+':
            raise assy.Invalid()
        for i in range(adr, adr+length):
            j = self.lang.m[i]
            if 32 <= j <= 126:
                pass
            elif j in (9, 10, 13):
                pass
            else:
                print("BAD char 0x%02x" % j)
                raise assy.Invalid()
        y = data.Txt(self.lang.m, adr, adr+length, label=False)
        if True:
            return '"' + y.txt + '"'
        print("PUSHTXT 0x%x" % self.lo + " adr 0x%x" % adr + " len 0x%x" % length + " '" + y.txt + "'")
        self.lang.m.set_line_comment(
            self.lo,
            "PUSHTXT 0x%x" % self.lo + " adr 0x%x" % adr + " len 0x%x" % length + " '" + y.txt + "'"
        )
        raise assy.Invalid()

def add_pushtxt(cx):
    ''' Add ourselves to a m68k disassembler '''
    cx.add_ins(M200_PUSHTXT_DESC, M200PushtxtIns)
