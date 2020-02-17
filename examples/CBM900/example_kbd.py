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

'''Commodore CBM900 - Keyboard EPROM

See also: https://datamuseum.dk/wiki/Commodore/CBM900
'''

from pyreveng import mem, data, listing
import pyreveng.cpu.mos6500 as mos6500
import pyreveng.toolchest.chargen as chargen

NAME = "CBM900_KBD"

LABELS = {
    # [0x015...0x01e] bitmap
    0x00b:	"LIST2",
    0x015:	"LIST1",
    0x034:	"KEYTIMER",
    0x035:	"CURKEY",
    0x036:	"KEYS_WAS",
    0x037:	"KEYS_ARE",
    0x03b:	"TMP",
    0x03c:	"BUFPTR",
    0x03d:	"LIST1PTR",
    0x03e:	"PORTB_COPY",
    0x03f:	"PORTC_COPY",
    0x08f:	"CONTROL_REG",
    0x08a:	"CLEAR_PA1_NEG_EDGE",
    0x089:	"CLEAR_PA0_POS_EDGE",
    0x088:	"UPPER_LATCH_AND_LATCH_TO_COUNTER",
    0x087:	"LOWER_COUNT",
    0x086:	"UPPER_COUNT",
    0x085:	"LOWER_LATCH",
    0x084:	"UPPER_LATCH",
    0x083:	"PORT_D",
    0x082:	"PORT_C",
    0x081:	"PORT_B",
    0x080:	"PORT_A",
    0x80e:	"TEST_RAM_AA",
    0x81d:	"TEST_RAM_55",
    0x82c:	"TEST_ROM_SUM",
    0x84c:	"RAM_ERROR",
    0x850:	"ROM_ERROR",
    0x88b:	"MAIN",
    0x8d1:	"MAIN_LOOP",
    0x8e6:	"send(X)",
    0x951:	"SCAN_PART1",
    0x997:	"KEY_HELD",
    0x9b3:	"NEXT_Y",
    0x9c0:	"XLAT_REPORT(Y)",
    0x9dd:	"BUF_OVERFLOW",
    0x9df:	"PLA_RETI",
    0x9e3:	"SCAN_PART2",
    0x9f9:	"CHECK_ROW",
    0x9fe:	"NEXT_BIT",
    0xa18:	"NO_PRESS",
    0xa1c:	"NEXT_ROW",
    0xa2d:	"SCAN_DONE",
    0xa31:	"NEXT_LIST2",
    0xa37:	"NEXT_LIST1",
    0xa41:	"IN_BOTH_LISTS",
    0xa65:	"CONTINUE_LIST2",
    0xa84:	"REPORT_RELEASED",
    0xa9a:	"REPORT_PRESSED",
    0xab2:	"RETI",
    0xaba:	"A=debounce_port_d()",
    0xad2:	"queue(A,X)",
    0xac6:	"delay()",
    0xf8c:	"TABLE",
    0xff3:	"XLAT",
}

def romsum(m):
    cs = 8
    for p in range(0x8, 0x10):
        for a in range(0x100):
            cc = cs >> 8
            assert cc in (0, 1)
            cs &= 0xff
            cs += m[(p << 8) + a] + cc
        cs &= 0xff

    cs |= 0x100
    cc = cs >> 8
    assert cc in (0, 1)
    cs &= 0xff
    cs += 0xff + cc
    return cs & 0xff

def example():
    m0 = mem.Stackup(
        files=(
            ("EPROM_C900KBD_R2_3_29_05_84.bin",),
        ),
        nextto=__file__,
    )

    cx = mos6500.rockwell6500()
    cx.m.map(m0, 0x800)

    print("CS1 0x%02x" % romsum(cx.m))

    for i, j in LABELS.items():
        cx.m.set_label(i, j)

    for a in range(0xf8c, 0xfec, 8):
        data.Const(cx.m, a, min(a + 8, 0xff4))
    data.Const(cx.m, 0xfec, 0xff3)
    data.Const(cx.m, 0xff3, 0xff9)

    cx.m.set_line_comment(0x88e, "Counter & PA0 IRQ enable")
    cx.m.set_line_comment(0x892, "Counter rate 20k = 50 Hz")
    cx.m.set_line_comment(0x8db, "Race-condition")
    cx.m.set_line_comment(0x967, "Ignore dangling input ?")
    cx.m.set_line_comment(0xad2, "Caps-Lock released ?")

    cx.m.set_block_comment(0x80, 'PORT A - BIT 7 - TXC')
    cx.m.set_block_comment(0x80, 'PORT A - BIT 6 - TXD')
    cx.m.set_block_comment(0x80, 'PORT A - BIT 5 - some key')
    cx.m.set_block_comment(0x80, 'PORT A - BIT 4 - some key')
    cx.m.set_block_comment(0x80, 'PORT A - BIT 3 - CAPS LOCK LED')
    cx.m.set_block_comment(0x80, 'PORT A - BIT 2 - some key')
    cx.m.set_block_comment(0x80, 'PORT A - BIT 1 - in')
    cx.m.set_block_comment(0x80, 'PORT A - BIT 0 - in Host Precense Detect')

    cx.m.set_block_comment(0x81, 'PORT B - KEY MATRIX STROBE')

    cx.m.set_block_comment(0x82, 'PORT C - BIT 7 - some key')
    cx.m.set_block_comment(0x82, 'PORT C - BIT 6 - some key')
    cx.m.set_block_comment(0x82, 'PORT C - BIT 5 -')
    cx.m.set_block_comment(0x82, 'PORT C - BIT 4 -')
    cx.m.set_block_comment(0x82, 'PORT C - BIT 3 -')
    cx.m.set_block_comment(0x82, 'PORT C - BIT 2 -')
    cx.m.set_block_comment(0x82, 'PORT C - BIT 1 -')
    cx.m.set_block_comment(0x82, 'PORT C - BIT 0 -')

    cx.m.set_block_comment(0x83, 'PORT D - KEY MATRIX SENSE')

    cx.m.set_block_comment(0x000, '''CBM900 Keyboard controller

There seems to be two parts to the keyboard:

Five real keys are attached directly to port A&C ("some key").

A matrix of keys are strobed by port B and sensed by port D.

Reporting is by scancode, with key release marked by bit 7.

''')

    cx.m.set_block_comment(0x942, '''PA0 edge detect
Send 0xaa, 0x38 to host
''')
    cx.m.set_block_comment(0x951, '''Scan first part of key matrix
''')
    cx.m.set_block_comment(0x9e3, '''Scan second part of key matrix
Scan up to 0x68 (@a29) keys
List first ten (@a09) activated keys in LIST1.
''')
    cx.m.set_block_comment(0xa2d, '''Compare LIST1 with LIST2
Report key-release
Perform auto-repeat on CURKEY
''')
    cx.m.set_block_comment(0xa6a, '''Report new key-presses
''')

    cx.m.set_line_comment(0xa4e, '''Key-repeat''')

    cx.vectors()

    return NAME, (cx.m,)

if __name__ == '__main__':
    listing.Example(example)
