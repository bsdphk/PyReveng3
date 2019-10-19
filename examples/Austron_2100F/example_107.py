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

'''Austron 2100F Loran-C Frequency Receiver
'''

from pyreveng import mem, listing, discover, data
import pyreveng.cpu.mc6800 as mc6800

NAME = "Austron2100F_107"

SYMBOLS = {
    0xe7dd: "?mul2(ce_d2)",
    0xe7ae: "?mul10(ce_d2)",
    0xe965: "?mul2(b3_b8)",
    0xea83: "?zero(ce_d2)",
    0xeaf4: "?divide()",
    0xf101: "queue(X)",
    0xf11f: "dispatch()",
    0xf45d: "ramtest_280_29f()",
    0xf4bd: "test_and_init_ram()",
    0xf598: "check_sum_rom()",

    0xd34f: "TIMER_SECOND()",

    0xe34c: "KEYPRESS",
    0xe51d: "DO_KEY_CLEAR",
    0xe02b: "KEY_HANDLER_1",
    0xe05e: "KEY_HANDLER_2",
    0xe3c1: "DO_KEY_STATUS",
    0xe542: "DO_KEY_BACKLIGHT",
    0xe37e: "KEY_HANDLER_3",
    0xdf41: "KEY_HANDLER_4",
    0xf429: "KEY_HANDLER_5",
    0xf377: "KEY_HANDLER_6",
    0xf6bd: "KEY_SOMETHING",

    0xe1c4: "BA=BCD([X++])",
    0xe127: "SHOW_TIME",
    0xe180: "SHOW_TIME_X",
    0xe514: "MEMSET(X, A, 8)",
    0xe516: "MEMSET(X, A, -B)",
    0xe572: "__HELP__()",

    0xe4d7: "PREP_IEEE_STRING()",
    0xd089: "IEEE_INIT",
    0xd3a2: "IEEE_TALK_ONLY",
    0xe4b6: "IEEE_SEND()",
    0xe2e3: "IEEE_RECV",
    0xe32b: "IEEE_RECV_NO_CMD_YET",

    ###############################################################
    # RAM
    0x0012: "hours",
    0x0013: "minutes",
    0x0014: "seconds",
    0x0015: "backlight_timer",
    0x002c: "status_low_copy",
    0x007f: "status_high_copy",
    0x011c: "ieee_len",
    0x0080: "ieee_busy",
    0x0082: "ieee_ptr",
    0x0086: "ieee_cmd",

    0x0055: "key_press",
    0x0081: "has_ieee488",
    0x008f: "key_press2",

    ###############################################################
    # I/O space
    # Charset: '0123456789-EHLP "

    0xe08: "STATUS_LOW",
    0xe0c: "STATUS_HIGH",
    0xe10: "SWITCH_LOW",
    0xe14: "SWITCH_HIGH",

}

def symbols(asp):
    for a, b in SYMBOLS.items():
        asp.set_label(a, b)
    for a in range(10):
        asp.set_label(0x0069 + a, "ascii_%d" % a)
    for a in range(12):
        asp.set_label(0x0073 + a, "ieee_%d" % a)
    for a in range(8):
        asp.set_label(0xe00 + a, "LCD_%d" % a)
    for a in range(8):
        asp.set_label(0xa000 + a, "IEEE488_R%d" % a)


class w8(data.Const):
    def __init__(self, asp, a):
        super().__init__(asp, a, a + 1)
        self.typ = ".BYTE"
        self.val = asp[a]
        self.fmt = "0x%02x" % self.val

class w16(data.Const):
    def __init__(self, asp, a):
        super().__init__(asp, a, a + 2)
        self.typ = ".WORD"
        self.val = asp.bu16(a)
        self.fmt = "0x%04x" % self.val

class w32(data.Const):
    def __init__(self, asp, a):
        super().__init__(asp, a, a + 4)
        self.typ = ".LWORD"
        self.val = asp.bu32(a)
        self.fmt = "0x%08x" % self.val
        self.fmt = "%d" % self.val

def w8t(asp, lo, hi):
    for a in range(lo, hi, 1):
        w8(asp, a)

def w16t(asp, lo, hi):
    for a in range(lo, hi, 2):
        w16(asp, a)

def w32t(asp, lo, hi):
    for a in range(lo, hi, 4):
        w32(asp, a)

def codet(cx, lo, hi):
    for a in range(lo, hi, 2):
        x = cx.m.bu16(a)
        if x >= cx.m.lo and x < cx.m.hi:
            cx.codeptr(a)
            if not list(cx.m.get_labels(x)):
                cx.m.set_label(x, "L%04x" % x)
        else:
            w16(cx.m, a)

def mem_setup():
    m = mem.Stackup(
        (
        ("Rev107f2.BIN",),
        ("Rev107f1.BIN",),
        ("Rev107f0.BIN",),
        ),
        nextto=__file__,
    )
    return m

def example():
    cx = mc6800.mc6800()
    cx.m.map(mem_setup(), 0xd000)

    symbols(cx.m)

    cx.vectors()

    codet(cx, 0xd94b, 0xd9b1)

    # Checksum
    w8(cx.m, 0xd000)

    # End address of checksum calc
    w16(cx.m, 0xd001)

    # Check checksum
    s = 0
    for a in range(0xd001, cx.m.bu16(0xd001)):
        s ^= cx.m[a]
    print("SUM", s, cx.m[0xd000])
    assert s == cx.m[0xd000]

    ##################################################################
    # Tables
    w16t(cx.m, 0xd8fb, 0xd903)
    w32t(cx.m, 0xd903, 0xd90b)


    # IEEE cmd+digit -> keycode
    # d935  53 0c     |S  | 'S0' -> KEY_CLEAR
    # d937  54 0d     |T  | 'S1' -> KEY_TEST
    # d939  55 0f     |U  | 'S2' -> KEY_STATUS
    # d93b  56 11     |V  | 'S3' -> KEY_GRI
    # d93d  57 1c     |W  | 'S4' -> KEY_?
    # d93f  41 13     |A  | 'A0' -> KEY_STATION_ADVANCE
    # d941  42 14     |B  | 'A1' -> KEY_ACQ
    # d943  4d 16     |M  | 'M0' -> KEY_PHASE_O_FS
    # d945  4e 17     |N  | 'M1' -> KEY_PHASE_RANGE
    # d947  4f 18     |O  | 'M2' -> KEY_FREQ_OFF
    # d949  50 1b     |P  | 'M3' -> KEY_BACK_LIGHT
    w16t(cx.m, 0xd935, 0xd94b)


    w16t(cx.m, 0xdce7, 0xdceb)

    w8t(cx.m, 0xde38, 0xde3a)

    w16t(cx.m, 0xe0b0, 0xe0c6)

    w32t(cx.m, 0xeb37, 0xeb4e)

    w16t(cx.m, 0xed1f, 0xed2b)

    # 128 entries approx X*X>>2
    # Table duplicated ?
    w16t(cx.m, 0xec1f, 0xed1f)
    w16t(cx.m, 0xee3b, 0xef3b)

    w16(cx.m, 0xee39)

    codet(cx, 0xf3c3, 0xf3d3)

    w16t(cx.m, 0xf580, 0xf598)

    # XXX: Startup display data ?
    w8t(cx.m, 0xf685, 0xf697)

    ##################################################################
    # Code

    # Addresses stored into 0x0010
    cx.disass(0xd401)
    cx.disass(0xde3a)

    # Addresses stored into 0x0033
    cx.disass(0xdaaa)
    cx.disass(0xdceb)
    cx.disass(0xdd0d)

    # Addresses stored into 0x003a
    cx.disass(0xf284)

    # Addresses stored into 0x008d (Key-handlers ?)
    cx.disass(0xe02b)
    cx.disass(0xe05e)
    cx.disass(0xe37e)
    cx.disass(0xdf41)
    cx.disass(0xf429)
    cx.disass(0xf377)

    # Addresses stored into 0x010c
    cx.disass(0xdb26)
    cx.disass(0xdb32)

    # LDS-JMP-TSX calls
    cx.disass(0xd033)
    cx.disass(0xf44d)



    # Things discover gets wrong
    #cx.disass(0xdee2)
    #cx.disass(0xde3a)

    done = set()
    while True:

        # Find queue'd entry points
        stop = True
        for i in cx.m:
            if i.tag != cx.name:
                continue
            if cx.m[i.lo] != 0xce:
                continue
            j = cx.m[i.lo + 3]
            if j != 0xbd and j != 0x7e:
                continue
            if cx.m[i.lo + 4] != 0xf1:
                continue
            if cx.m[i.lo + 5] != 0x01:
                continue
            a = cx.m.bu16(i.lo + 1)
            if a not in done:
                print("Queued: 0x%04x" % a)
                cx.disass(a)
                cx.m.set_label(a, "Q%04x" % a)
                stop = False
                done.add(a)
        if stop:
            break

    discover.Discover(cx)

    return NAME, (cx.m,)

if __name__ == '__main__':
    listing.Example(example)
