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

from pyreveng import mem, listing, data, assy, code

from pyreveng.cpu import hp_hybrid

import pat4244024

NAME = "HP8566A"
FILENAME = "HP8566A.ROM"

SYMBOLS = {
    0x0010:	"AR2",
    0x0011:	"AR2+1",
    0x0012:	"AR2+2",
    0x0013:	"AR2+3",
    0x0023:	"AR0D",
    0x0024:	"AR1D",
    0x0025:	"AR2D",
    # 0x3eae:	".WSTR",
    0x7fee:	"INDX",
    0x7fef:	"TMP",
    0x7ff0:	"CNTR",
    0x7ff1:	"TMPB",
    0x7ff3:	"E",
    0x7ff4:	"AR3",
    0x7ff8:	"AR1",
    0x7ff9:	"AR1+1",
    0x7ffa:	"AR1+2",
    0x7ffb:	"AR1+3",
    0x7ffc:	"AR0",
    0x7ffd:	"AR0+1",
    0x7ffe:	"AR0+2",
    0x7fff:	"AR0+3",
}
#######################################################################

class wgstring(data.Data):

    def __init__(self, asp, lo):
        l = asp[lo]
        s = ""
        p = lo + 1
        for n in range(0, l):
            if n & 1:
                c = asp[p] & 0xff
                p += 1
            else:
                c = asp[p] >> 8
            if 0x20 <= c <= 0x7e:
                s += "%c" % c
            else:
                s += "\\x%02x" % c
        self.txt = '"' + s + '"'
            
        super().__init__(asp, lo, lo + ((3 + l) >> 1))
        self.rendered = '.TXT\t%d, "%s"' % (l, s)

def rom_checksum(asp):
    sl = -1
    sh = -1
    for a in range(0x20, 0x4000):
        sh += asp[a] >> 8
        sl += asp[a] & 0xff
        if (a & 0x7ff) == 0x7ff:
            sh &= 0xffff
            sl &= 0xffff
            d = 0x8000 + (a + 1)
            d = d >> 10
            d += 6
            y = data.Const(asp, d, d + 2)
            y.lcmt += "ROM Checksum"
            assert sh == asp[d]
            assert sl == asp[d + 1]
            sl = -1
            sh = -1
    print("ROM Checksum good")

def fc_arg(asp, ins, arg):
    ins.flow_out.pop(-1)
    for c in arg:
        b = asp[ins.hi]
        ins.hi += 1
        if c == "T":
            try:
                y = wgstring(asp, b)
                ins.oper.append(assy.Arg_verbatim(y.txt))
            except mem.MemError:
                ins.oper.append(assy.Arg_verbatim("T@0x%x" % b))
        elif c == "F":
            ins.oper.append(assy.Arg_verbatim("FP@0x%x" % b))
            try:
                x = asp[b]
                y = data.Const(asp, b, b + 4)
                y.typ = ".FP"
            except mem.MemError:
                pass
        elif c == "P":
            ins.oper.append(assy.Arg_verbatim("P@0x%x" % b))
        else:
            assert False, "BAD fc_arg spec: " + c
    ins += code.Flow()

def fc_case(asp, ins, _arg):
    ins.flow_out.pop(-1)
    a = ins.lo - 1
    n = asp[a]
    data.Const(asp, a, a + 1)
    while n < 65535:
        a -= 1
        y = data.Const(asp, a, a + 1)
        ins += code.Jump(cond="?", to=asp[a])
        n += 1

def fc_call(asp, ins):
    f = {
        0x3e78: (fc_case, None),	# .CASE
        0x3eae:	(fc_arg, "T"),		# .WSTR
        0x3a49:	(fc_arg, "F"),		# SUB1
        0x3a55:	(fc_arg, "F"),		# MIN1
        0x3a56:	(fc_arg, "F"),		# ADD1
        0x3a94:	(fc_arg, "F"),		# MPY1
        0x3aab:	(fc_arg, "F"),		# DIV1
	0x3ac8: (fc_arg, "P"),		# SUB2
	0x3cb1: (fc_arg, "F"),		# .LDBI
	0x3d51: (fc_arg, "P"),		# .ARAY
	0x3cc5: (fc_arg, "P"),		# .STBD
	0x3cba: (fc_arg, "PP"),		# .MVE4
	0x3ad7: (fc_arg, "P"),		# MIN2
        0x3b08: (fc_arg, "P"),		# MPY2
        0x3ad8: (fc_arg, "P"),		# ADD2
        0x3d19: (fc_arg, "P"),		# LDS1
        0x3c1d: (fc_arg, "P"),		# MPY3
        0x3c16: (fc_arg, "P"),		# MIN3
        0x3d4f: (fc_arg, "P"),		# .LRAY
        0x3e52: (fc_arg, "PP"),		# .TURN
        0x3b41: (fc_arg, "P"),		# DIV2
        0x3c17: (fc_arg, "P"),		# ADD3
        0x3c3d: (fc_arg, "P"),		# DIV4
        0x3eaa: (fc_arg, "PT"),		# .WSTP
	# .LDSI
	# .CLBI
	# .STRD
	# .TEST (possibly 2 args, pg 264)
    }.get(ins.dstadr)
    if f:
        f[0](asp, ins, f[1])

def example():

    m = mem.Stackup((FILENAME,), nextto=__file__)
    m2 = mem.WordMem(0, m.hi >> 1, bits=16)
    for a in range(m.lo, m.hi, 2):
       m2[a >> 1] = m.bu16(a)
    cx = hp_hybrid.hp_hybrid()
    cx.m.map(m2, 0x20, offset=0x20)
    cx.flow_check.append(fc_call)

    rom_checksum(cx.m)

    for a, b in SYMBOLS.items():
        if b[0] == '_':
            cx.m.set_label(a, b[1:])
            cx.disass(a)
        elif b[0] == '#':
            cx.m.set_label(a, b[1:])
            y = data.Data(cx.m, a, a + 1)
            y.rendered = ".CONST\t0x%04x" % cx.m[a]
        else:
            cx.m.set_label(a, b)

    pat4244024.appendix_b_1(cx, 0x3a49)
    pat4244024.appendix_b_2(cx, 0x3ac2)
    pat4244024.appendix_b_3(cx, 0x3ca5)
    pat4244024.appendix_b_4(cx, 0x3d2c)
    pat4244024.appendix_b_5(cx, 0x3d4b)
    pat4244024.appendix_b_7(cx, 0x3df0)
    pat4244024.appendix_b_8(cx, 0x3e02)
    pat4244024.appendix_b_9(cx, 0x3e13)
    pat4244024.appendix_b_10(cx, 0x3e30)
    pat4244024.appendix_b_11(cx, 0x3e4a)
    pat4244024.appendix_b_12(cx, 0x3e6c)
    pat4244024.appendix_b_13(cx, 0x3e78)
    pat4244024.appendix_b_15(cx, 0x3e86)
    pat4244024.appendix_b_16(cx, 0x3ebc)
    pat4244024.appendix_b_17(cx, 0x3ebf)
    pat4244024.appendix_b_18(cx, 0x3ec2)
    pat4244024.appendix_b_21(cx, 0x3a35)
    pat4244024.appendix_b_28a(cx, 0x0020)
    pat4244024.appendix_b_28b(cx, 0x0200)

    if True:
        for a in range(0x3ef, 0x40a):
            data.Const(cx.m, a, a + 1)
            y = wgstring(cx.m, cx.m[a])
            y.compact = True
        for a in range(0x1ebb, 0x1ec6):
            data.Const(cx.m, a, a + 1)
            y = wgstring(cx.m, cx.m[a])
            y.compact = True

    cx.disass(0x20)

    code.lcmt_flows(cx.m)

    return NAME, (cx.m,)

if __name__ == '__main__':
    listing.Example(example)
