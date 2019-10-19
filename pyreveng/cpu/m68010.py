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

'''Motorola M68010
'''

from pyreveng.cpu import m68000

m68010_desc = """
# 476/6-22
#		src,dst		ea	|_ _ _ _|_ _ _v_|_ _v_ _|_v_ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|
MOVEC           Rc,Dn           0000    |0 1 0 0|1 1 1 0|0 1 1 1|1 0 1|0|0| Dn  | Rc                    |
MOVEC           Rc,An           0000    |0 1 0 0|1 1 1 0|0 1 1 1|1 0 1|0|1| An  | Rc                    |
MOVEC           Dn,Rc           0000    |0 1 0 0|1 1 1 0|0 1 1 1|1 0 1|1|0| Dn  | Rc                    |
MOVEC           An,Rc           0000    |0 1 0 0|1 1 1 0|0 1 1 1|1 0 1|1|1| An  | Rc                    |

# 478/6.24
#		src,dst		ea	|_ _ _ _|_ _ _v_|_ _v_ _|_v_ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|
MOVES		Z,ea,Dn		037c	|0 0 0 0|1 1 1 0| sz| ea        |0| Dn  |0|0 0 0 0 0 0 0 0 0 0 0|
MOVES		Z,Dn,ea		037c	|0 0 0 0|1 1 1 0| sz| ea        |0| Dn  |1|0 0 0 0 0 0 0 0 0 0 0|
MOVES		Z,ea,An		037c	|0 0 0 0|1 1 1 0| sz| ea        |1| An  |0|0 0 0 0 0 0 0 0 0 0 0|
MOVES		Z,An,ea		037c	|0 0 0 0|1 1 1 0| sz| ea        |1| An  |1|0 0 0 0 0 0 0 0 0 0 0|

# 270/4.166
RTD		word		0	|0 1 0 0 1 1 1 0 0 1 1 1 0 1 0 0| word				|

"""

#######################################################################

class m68010_ins(m68000.m68000_ins):

    def assy_Rc(self):
        x = self.lang.cregs.get(self['Rc'])
        if x is None:
            return "RC_%03x" % self['Rc']
        self.lcmt += x[1]
        return x[0]



class m68010(m68000.m68000):
    def __init__(self, lang="m68010"):
        super().__init__(lang)
        self.add_ins(m68010_desc, m68010_ins)
        self.cregs = {
            0x000: ("SFC", "Source Function Code"),
            0x001: ("DFC", "Destination Function Code"),
            0x800: ("USP", "User Stack Pointer"),
            0x801: ("VBR", "Vector Base Register"),
        }
