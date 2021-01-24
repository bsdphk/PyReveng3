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
        OMTI 5200 SCSI/ST506/Floppy/QIC02 controller.
	bitsavers: 3001206_OMTI_5000_Series_Reference_Aug85.pdf
	EPROM marked 1002405-F
'''

from pyreveng import mem, data, listing, assy
import pyreveng.cpu.z8 as z8

FILENAME = "Z8_SCSI_CONTROLLER_128.bin"

NAME = "OMTI_5200"

MACROS = '''
DISKCTL		arg0		|0 0 0 1|1 1 0 0| adr		|1 1 1 0|1 1 0 0| data		|1 0 0 1|0 0 1 0|1 1 1 0|0 0 0 0|
'''

class Z8Macros(assy.Instree_ins):

    def assy_arg0(self):
        self.oper.append(assy.Arg_verbatim("[0x%x]" % self['adr']))
        self.oper.append(assy.Arg_imm(self['data']))

def example():

    m = mem.Stackup((FILENAME,), nextto=__file__)
    sl = sum(m[x] for x in range(m.lo, m.hi - 2, 2)) & 0xff
    sh = sum(m[x] for x in range(m.lo + 1, m.hi, 2)) & 0xff
    csum = (sl | sh) ^ 0xff
    if csum:
        print("BAD checksum: SUM_L 0x%x" % sl, "SUM_H 0x%x" % sh)
    else:
        print("Good checksum")

    cx = z8.Z8()
    cx.use_macros()
    cx.it.load_string(MACROS, Z8Macros)
    cx.m.map(m, 0)

    data.Const(cx.m, 0x3ffe, 0x4000)
    cx.m.set_line_comment(0x3ffe, "CHECKSUM ADJUSTMENTS")

    cx.vectors()

    for n, a in enumerate(range(0x1b57, 0x1b7f, 2)):
        y = cx.codeptr(a)
        cx.m.set_block_comment(y.dst, "Method[0x%x]" % n)
    cx.m.set_label(0x1b57, "DISPATCH_TABLE")
    cx.m.set_label(0x2f0, "DISPATCH_R10")
    cx.m.set_line_comment(0x2f0, "Jump to DISPATCH_TABLE[R10]")

    for a, b in (
        (0x1af2, 5),
        (0x1ba3, 16),
        (0x1e0d, 8),
        (0x1ffc, 4), # XXX: real length?
        (0x1b0f, 16),
        (0x2078, 4),
        (0x2924, 12),
    ):
        data.Const(cx.m, a, a + b)

    y = data.Txt(cx.m, 0x3ff0, 0x3ffe, label=False)
    cx.m.set_label(y.lo, "SCSI_IDENT")

    for a, b in (
        (0x0029, "ZERO_DISK_CTRL"),
        (0x0036, "INIT_DISK_CTRL"),
        (0x00de, "ROM_SUM_LOOP"),
        (0x022d, "RESTART?"),
        (0x20c6, "INIT_TIMER"),
    ):
        cx.m.set_label(a, b)

    cx.m.set_line_comment(0x54, "Load DISK_CTRL[0x13+0x14] = 0x131 (=305 ncyl?)")

    orphans = (
        0x316,
        0x870,
        0xc41,
        0xf61,
        0x1025,
        0x15be,
        0x2520,
        0x2559,
        0x255f,
        0x2560,
        0x2b2c,
    )
    for a in orphans[:0]:
        cx.disass(a)
        cx.m.set_line_comment(a, "<MANUAL>")

    cmds = {
        0x00: "TEST_DRIVE_UNIT",
        0x01: "RECALIBRATE",
        0x03: "REQUEST_SENSE",
        0x04: "FORMAT_UNIT",
        0x05: "CHECK_TRACK_FORMAT",
        0x06: "FORMAT_TRACK",
        0x08: "READ",
        0x0a: "WRITE",
        0x0b: "SEEK",
        0xc2: "ASSIGN_DISK_PARAMETERS",
        0xe0: "RAM_DIAGNOSTIC",
        0xe2: "READ_IDENTIFIER",
        0xec: "READ_DATA_BUFFER",
        0xef: "WRITE_DATA_BUFFER",
    }
    for n in range(14):
        x = data.Const(cx.m, 0x2b7c + n)
        y = cx.codeptr(0x2b8a + 2 * n)
        c = cx.m[x.lo]
        t = cmds.get(c)
        if t:
            cx.m.set_line_comment(x.lo, t)
            t = "CMD_0x%02x_" % c + t
        else:
            t = "CMD_0x%02x" % c
        cx.m.set_label(y.dst, t)

    return NAME, (m,)

if __name__ == '__main__':
    listing.Example(example, ncol=6)
