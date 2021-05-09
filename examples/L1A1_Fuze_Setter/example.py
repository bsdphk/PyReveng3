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
Royal Ordnance Fuze Setter Logic Unit L1A1
------------------------------------------
See:
	https://www.eevblog.com/forum/reviews/royal-ordnance-fuze-setter-logic-unit-l1a1-teardown
'''

from pyreveng import mem, listing, code, assy
import pyreveng.cpu.cdp1802 as cdp1802

MY_CALL = '''
MYCALL	mcl,>C	|1 1 0 1|0 1 0 0| hi		| lo		|
MYRET	>R	|1 1 0 1 0 1 0 1|
SEP0	-	|1 1 0 1 0 0 0 0|
'''

class My_Ins(cdp1802.CDP1802_Ins):

    def assy_mcl(self):
        self.dstadr = (self['hi'] << 8) | self['lo']
        self.lang.m.set_block_comment(self.dstadr, "MYCALL from 0x%04x" % self.lo)
        return assy.Arg_dst(self.lang.m, self.dstadr)

def example():
    m = mem.Stackup(('PROM1.BIN', 'PROM2.BIN'), nextto=__file__)
    cx = cdp1802.CDP1802()
    cx.add_ins(MY_CALL, My_Ins)
    cx.m.map(m, 0)
    cx.disass(0)

    for a, b in (
        (0x0009, "See 0x0009"),
        (0x01ce, "Guess"),
        (0x120f, "See 0x0884"),
        (0x1239, "See 0x049e"),
        (0x1297, "IRQ - see 0x001e"),
        (0x12aa, "IRQ - see 0x1297/12a9"),
        (0x14db, "See 0x0032"),
        (0x14ec, "See 0x0038"),
    ):
        cx.disass(a)
        cx.m.set_block_comment(a, b)

    code.lcmt_flows(cx.m)

    return ("L1A1", (cx.m,))

if __name__ == '__main__':
    listing.Example(example)
