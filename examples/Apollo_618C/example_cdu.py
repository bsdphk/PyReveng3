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

'''II Morrow Apollo 618C Loran - Display Controller
'''

# P3.3 tied to P3.4 T0->INT1
# P3.2 INT0 probably from main CPU

import os
from pyreveng import job, mem, data, listing, code, charset
import pyreveng.cpu.mcs51 as mcs51

FILENAME = "618TCA_CDU_U20_U12_PN_138_0192_V_2_2_C_U5.bin"

NAME = "Apollo618c_cdu"

SYMBOLS = {
    0x028: "ZERO_RAM",
    0x039: "MAIN_LOOP",
    0x050: "SETUP",
    0x70e: "CHAR_XLAT",
    # 0x5b...0x5d are bits to blink characters
    0x72e: "CHAR_BLINK",
    0x76d: "WATCHDOG",
    0x600: "TIMER",
    0x800: "MAIN_CMD",
    0x845: "RESUME_@7D7E",
    0x84a: "SUSPEND_@7D7E",
    0x945: "SUSPEND_@7A7B",
    0x940: "RESUME_@7A7B",
    0x945: "SUSPEND_@7A7B",
    0x9ab: "RX_POLL",
    0xa2b: "CHECK_BUTTONS",
    0xa65: "CHECK_DIAL",
    0xa7e: "inner_dial",
    0xa90: "outher_dial",
    0xa9c: "common_dial",
    0xab9: "more_inner_dial",
    0xabb: "more_outher_dial",
    0xc8c: "RX_READY",
    0xc54: "TX_READY",
}

BIT_SYMBOLS = {
    0x08: "outher_dial",
    0x09: "inner_dial",
    0x0c: "rx_flag",
    0x12: "user_activation",
    0x98: "P1.0=OUTHER_DIAL_PH1",
    0x99: "P1.1=OUTHER_DIAL_PH2",
    0x9a: "P1.2=INNER_DIAL_PH1",
    0x9b: "P1.3=INNER_DIAL_PH2",
    0x9c: "P1.4=RIGHT_BUTTONS",
    0x9d: "P1.5=LEFT_BUTTONS",
}

DATA_SYMBOLS = {
    0x56: "scan_bits",
    0x57: "new_scan",
    0x58: "n_led",
    0x5e: "watchdog",
    0x60: "button_activation",
    0x61: "idial_activation",
    0x62: "odial_activation",
    0x63: "dial_bits",
    0x76: "rx_wptr",
    0x79: "rx_rptr",
}

def example():
    m = mem.Stackup((FILENAME,), nextto=__file__)
    cx = mcs51.I8032()
    cx.m.map(m, 0)

    cx.disass(0xb)
    cx.vectors(which=("RESET", "TF0"))

    cx.disass(0x600)

    for a, b in SYMBOLS.items():
        cx.m.set_label(a, b)

    for a, b in BIT_SYMBOLS.items():
        cx.as_bit.set_label(a, b)

    for a, b in DATA_SYMBOLS.items():
        cx.as_data.set_label(a, b)

    cx.m.set_line_comment(0xa31, "Mask Left/Right Buttons")
    cx.m.set_line_comment(0xa47, "Mask Left/Right Buttons")
    cx.m.set_line_comment(0xa67, "Mask Dials")

    for i in range(0, 0x18, 8):
        data.Txt(cx.m, 0x0a2 + i, 0x0a2 + i + 0x08, label=False)

    for i in range(0, 0x18, 8):
        data.Txt(cx.m, 0x78a + i, 0x78a + i + 0x08, label=False)


    #######################################################################
    def cmd_func(a1, a2, n):
        cx.m.set_label(a1, "DO_CMD%d" % n)
        a = a2
        while True:
            if cx.m[a] != 0xb4:
                break
            c = cx.m[a + 1]
            d = cx.m[a + 2]
            cx.m.set_label(a, "CMD%d_%02x" % (n, c))
            a += 3 + d


    cmd_func(0xbf3, 0xbf7, 1)
    cmd_func(0x823, 0x827, 2)
    cmd_func(0x84f, 0x851, 3)
    #######################################################################

    #######################################################################
    for a in range(0xba, 0x100, 2):
        x = data.Const(cx.m, a, a + 2)
        x.typ = ".WORD"
        x.val = cx.m.lu16(a)
        x.fmt = "0x%04x" % x.val

    #######################################################################

    x = data.Data(cx.m, 0x100, 0x600, "chargen")
    x.rendered = "*CHARGEN*"
    x.compact = True

    cs = charset.SVG_Charset(
        fn="/tmp/" + NAME + "_charset.svg",
        char_w = 5,
        char_h = 7,
        imargin = 1,
    )
    for n in range(0x100):
        ll = [0] * 7
        for i in range(7):
            for j in range(5):
                ll[6-i] |= ((cx.m[0x100 + j * 0x100 + n] >> i) & 1) << (4-j)
        cs.set_char(n // 16, n % 16, ll)
    cs.render()

    #######################################################################

    return NAME, (cx.m,)

if __name__ == '__main__':
    listing.Example(example)
