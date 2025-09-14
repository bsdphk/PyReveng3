#!/usr/bin/env python
#
# Copyright (c) 2012-2019 Poul-Henning Kamp <phk@phk.freebsd.dk>
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

'''
'''

from pyreveng import assy, data, code

switches = '''

# f6053 83 f8 1e                 |        |               CMP     #0x1e,%ax
# f6056 76 03                    |v       |               JBE     0xf605b
# f6058 e9 44 01                 | D      |               JMP     0xf619f
# f605b 03 c0                    |        |               ADD     %ax,%ax
# f605d 8b d8                    |        |               MOV     %ax,%bx
# f605f 2e ff a7 b4 10           |.       |               JMP     %cs:0x10b4+(%bx)

SWITCH sw0,a	| 83		| F8		| high		| &
		| 76		| 03		| &
		| e9		| def_l		| def_h		| &
		| 03		| C0		| &
		| 8B		| D8		| &
		| 2E		| FF		| A7		| &
		| tbl_l		| tbl_h		|

# eca93 83 f8 05                 |        |               CMP     #0x05,%ax
# eca96 77 33                    |w3      |               JA      0xecacb
# eca98 03 c0                    |        |               ADD     %ax,%ax
# eca9a 8b d8                    |        |               MOV     %ax,%bx
# eca9c 2e ff a7 61 26           |.  a&   |               JMP     %cs:0x2661+(%bx)

SWITCH sw1,a	| 83		| F8		| high		| &
		| 77		| disp		| &
		| 03		| C0		| &
		| 8B		| D8		| &
		| 2E		| FF		| A7		| &
		| tbl_l		| tbl_h		|

# e0bdc 83 fb 10                 |        |               CMP     #0x10,%bx
# e0bdf 77 5f                    |w_      |               JA      0xe0c40
# e0be1 03 db                    |        |               ADD     %bx,%bx
# e0be3 2e ff a7 e8 0b           |.       |               JMP     %cs:0x0be8+(%bx)

SWITCH sw1,b	| 83		| Fb		| high		| &
		| 77		| disp		| &
		| 03		| db		| &
		| 2E		| FF		| A7		| &
		| tbl_l		| tbl_h		|


# e9334 83 f9 0e                 |        |               CMP     #0x0e,%cx
# e9337 77 76                    |wv      |               JA      0xe93af
# e9339 03 c9                    |        |               ADD     %cx,%cx
# e933b 8b d9                    |        |               MOV     %cx,%bx
# e933d 2e ff a7 82 31           |.   1   |               JMP     %cs:0x3182+(%bx)

SWITCH sw1,c	| 83		| F9		| high		| &
		| 77		| disp		| &
		| 03		| C9		| &
		| 8B		| D9		| &
		| 2E		| FF		| A7		| &
		| tbl_l		| tbl_h		|

#eb711 3d 91 00                 |=       |               CMP     #0x91,%ax
#eb714 76 03                    |v       |               JBE     0xeb719
#eb716 e9 30 02                 | 0      |               JMP     0xeb949
#eb719 03 c0                    |        |               ADD     %ax,%ax
#eb71b 8b d8                    |        |               MOV     %ax,%bx
#eb71d 2e ff a7 e2 12           |.       |               JMP     %cs:0x12e2+(%bx)

SWITCH sw2,a	| 3D		| high_l	| high_h	| &
		| 76		| 03		| &
		| E9		| def_l		| def_h		| &
		| 03		| C0		| &
		| 8B		| D8		| &
		| 2E		| FF		| A7		| &
		| tbl_l		| tbl_h		|

'''

class i8086_switch_ins(assy.Instree_ins):
    ''' ... '''

    def assy_a(self):
        """ ... """
        return "%ax"

    def assy_b(self):
        """ ... """
        return "%bx"

    def assy_c(self):
        """ ... """
        return "%cx"

    def assy_sw0(self):
        num = self['high']
        tbl = (self['tbl_h']<<8) | self['tbl_l']
        cs = self.hi - tbl
        defl = self.lo + 8 + (self['def_h'] << 8) + self['def_l']
        self += code.Jump(cond="default", to=defl)
        y = data.Array(num + 1, data.Lu16, vertical=True)(self.lang.m, self.hi).insert()
        for idx, off in enumerate(y):
            dst = cs + off.val
            self.lang.m.set_line_comment(dst, "<- Switch@0x%x #0x%x" % (self.hi, idx))
            self += code.Jump(cond="#0x%x" % idx, to=dst)

    def assy_sw1(self):
        num = self['high']
        tbl = (self['tbl_h']<<8) | self['tbl_l']
        cs = self.hi - tbl
        defl = self.lo + 5 + self['disp']
        self += code.Jump(cond="default", to=defl)
        y = data.Array(num + 1, data.Lu16, vertical=True)(self.lang.m, self.hi).insert()
        for idx, off in enumerate(y):
            dst = cs + off.val
            self.lang.m.set_line_comment(dst, "<- Switch@0x%x #0x%x" % (self.hi, idx))
            self += code.Jump(cond="#0x%x" % idx, to=dst)

    def assy_sw2(self):
        num = (self['high_h'] << 8) | self['high_l']
        tbl = (self['tbl_h']<<8) | self['tbl_l']
        cs = self.hi - tbl
        defl = self.lo + 8 + (self['def_h'] << 8) + self['def_l']
        self += code.Jump(cond="default", to=defl)
        y = data.Array(num + 1, data.Lu16, vertical=True)(self.lang.m, self.hi).insert()
        for idx, off in enumerate(y):
            dst = cs + off.val
            self.lang.m.set_line_comment(dst, "<- Switch@0x%x #0x%x" % (self.hi, idx))
            self += code.Jump(cond="#0x%x" % idx, to=dst)

def i8086_switches(disass):
    disass.add_ins(switches, i8086_switch_ins)

if __name__ == "__main__":

    from pyreveng import instree

    IT = instree.InsTree(8)
    IT.load_string(switches)
    IT.dump()
