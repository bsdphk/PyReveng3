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
#
# INDEX CPU HP1345 Graphical Display Processor

'''HP1345A Vector Graphics Processor
'''

from pyreveng import assy

hp1345a_desc = """
_SET	i,l,s,>R	|0 1 1| i | ? | l |0|?| s | ?	|
_LOADX	c,>R		|0 0 0 0|p| c			|
_PLOTY	c,p,>R		|0 0 0 1|p| c			|
_DX	c,>R		|0 0 1 0|p| c			|
_GRAPH	c,p,>R		|0 0 1 1|p| c			|
_CHR	a,t,>R		|0 1 0| s | r |e| t		|
"""

class hp1345_ins(assy.Instree_ins):

    def assy_adr(self):
        self.dstadr = (self['ahi'] << 8) | self['alo']
        return assy.Arg_dst(self.dstadr)

    def assy_arg8(self):
        self.dstadr = (self.lo & ~0x0ff) | self['a8']
        return assy.Arg_dst(self.dstadr)

    def assy_c(self):
        return "#%d" % self['c']

    def assy_t(self):
        a = self['t']
        if a < 32 or a > 126:
            return "#0x%02x" % a
        else:
            return "'%c'" % a

    def assy_a(self):
        if not self['e']:
            return "-"
        s = ["1x", "1.5x", "2x", "2.5x"][self['s']]
        s += "@%d" % (self['r'] * 90)
        return s

    def assy_p(self):
        return ["OFF", "ON"][self['p']]

    def assy_im(self):
        return "#0x%02x" % self['im']

    def assy_i(self):
        return ("Blank", "Dim", "Half", "Full")[self['i']]

    def assy_l(self):
        return ("Solid", "Ends", "Long", "Short")[self['l']]

    def assy_s(self):
        return ("slow", "low", "med", "high")[self['s']]

class hp1345a(assy.Instree_disass):
    def __init__(self, lang="hp1345a"):
        super().__init__(
            name=lang,
            ins_word=16,
            mem_word=8,
            endian=">"
        )
        self.add_ins(hp1345a_desc, hp1345_ins)
