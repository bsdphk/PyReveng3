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

'''HP1347 - Prototype

This is a prototype HP1347A used to make the special effects of the
NORAD control center in the Hollywood summer blockbuster movie "Wargames".

This firmware does not match the 5957-7606 manual titled:
    1346A / 1347A IB Displays Operating and Programming Manual

See also:

    http://www.hp9845.net/9845/software/screenart/wargames/

    http://phk.freebsd.dk/hacks/Wargames/index.html
'''

from pyreveng import mem, listing, data
import pyreveng.cpu.mc6809 as mc6809
import pyreveng.cpu.hp1345a as hp1345a
import pyreveng.cpu.hp1345_render as hp1345_render

NAME = "HP1347A_proto"

FILENAMES = (
    "hp1347a_proto.low.rom",
    "hp1347a_proto.high.rom",
)

SYMBOLS = {
    0xfbed: "IMG_PIKES_PEAK",
    0xfd41: "IMG_FOCUS",
    0xe5a1: "BOGO_TEST_ROM",
    0xe5ed: "TEST_IMGRAM",
    0x0291: "A=GETCHAR()",
    0x02d0: "PUTCHAR(A)",
    0x0312: "Y=FIND_CMD()",
    0x0338: "CLEAR_SCREEN()",
    0x0395: "PUTSTR(',')",
    0x039a: "PUTSTR(CRNL)",
    0x03a9: "memcpy(Y,X+2,@X)",
    0x03b9: "GETNBR()",
    0x04a2: "PUTNBR(D)",
    0x0bcb: "ERR_1_UNKNOWN_INSN()",
    0x0bdc: "ERR_2_WRONG_NO_PARAMS()",
    0x0bed: "ERR_3_XXX_OUT_OF_RANGE()",
    0x0c2e: "ERR_4_ILLEGAL_CHAR()",
    0x0c41: "ERR_11_NO_PLOTTER_HANDSHAKE()",
    0x0c5d: "ERR_12_UNRECOG_PLOTTER()",
    0x0c79: "ERR_22_FILE_NOT_OPEN_ON()",
    0x0c8c: "ERR_24_NOT_IN_SCROLL_MODE()",
    0x0c9f: "ERR_25_MEMORY_NOT_INIT()",
    0x0cb2: "ERR_32_ALL_FILES_NOT_CONFIG()",
    0x0cc5: "ERR_33_NO_DATA_TO_SCROLL()",
    0x0cd8: "ERR_34_MEMORY_OVERFLOW_ON()",
    0x0ceb: "ERR_35_FILE_ALREADY_OPEN_ON()",
    0x0f4e: "SCR_MSG(X)",
    0x0f77: "X = PREP_SCREEN()",
    0x0f8e: "D = ADR2JMP(D)",
    0x0fac: "DELAY(@U)",
    0x2800: "dip_switch",
    0xe77e: "CMD_nop",
    0xef76: "PLOT_pu_sp_lt()",
    0xef90: "PLOT_SELECT_PEN(A)",
    0xefb9: "PLOT_LINE_TYPE(A)",
    0xf004: "PUTSTR(X+1,@X)",
    0xf0c0: "SPEC_CHAR()",
    0xf56e: "plotter_table",
    0xf7fd: "DIAG_MODE()",
    0xf825: "DIAG_HPIB_BACK2BACK()",
    0xf895: "HPIB_RESET_CHIPS()",
    0xf8ae: "HPIB_IFC()",
    0xfa9f: "DIAG_SIGNATURE_EPROM1()",
    0xfaaf: "DIAG_SIGNATURE_EPROM2()",
    0xfac2: "DIAG_SIGNATURE_3000()",
    0xfade: "DIAG_SIGNATURE_RAM()",
    0xfaee: "DIAG_RAM()",
    0xfb03: "DIAG_IMGRAM()",
    0xfbcb: "DIAG_PIKES_PEAK()",
    0xfbdc: "DIAG_FOCUS()",
}

# Notes:
#
#    0x0000-1fff    EPROM.low
#    0x2000-        TMS9914 chip for host interface
#    0x2800        DIP switch
#    0x3000        ?
#    0x3800        Signature-analysis ?
#    0x4000-        TMS9914 chip for plotter interface
#    0x6000-63ff    Scratch-pad RAM
#    0x8000-bfff    Image RAM
#    0xc000-dfff    ?
#    0xe000-ffff    EPROM.high
#
#    $0x09        End of image RAM
#    $0x02        HPIB chip address (0x2000 or 0x4000)
#    $0x18        "cursor"-pointer into image-RAM
#    $0xe1        Plotter-ID (last char in plotter_table)
#

CMDS = {
    "AF": [0, "???"],
    "AH": [0, "???"],
    "AP": [0, "Automatic Pen Pickup"],
    "BI": [0, "? Binary In"],
    "BO": [0, "? Binary Out"],
    "CA": [0, "Alternate Charset"],
    "CP": [0, "Character Plot"],
    "CS": [0, "Character Set"],
    "DC": [0, "Digitize Clear"],
    "DF": [0, "Set Default"],
    "DI": [0, "Absolute Direction"],
    "DP": [0, "Digitize Point"],
    "DR": [0, "Direction Relative"],
    "DS": [0, "Data Scroll"],
    "EC": [0, "Enable Cutter"],
    "FA": [0, "???"],
    "FB": [0, "? File Blank"],
    "FC": [0, "? File Close"],
    "FD": [0, "? File Delete"],
    "FE": [0, "? File Erase"],
    "FF": [0, "? File Find"],
    "FO": [0, "? File Open"],
    "FU": [0, "? File Unblank"],
    "GR": [0, "???"],
    "HA": [0, "Hardcopy Abort"],
    "IM": [0, "Input Mask"],
    "IN": [0, "Initialize"],
    "IP": [0, "Input P1&P2"],
    "IW": [0, "Input Window"],
    "LB": [0, "Label"],
    "LT": [0, "Line Type"],
    "MA": [0, "???"],
    "MJ": [0, "???"],
    "MU": [0, "???"],
    "OA": [0, "Output Actual Position"],
    "OC": [0, "Output Commanded Position & Beam Status"],
    "OD": [0, "Output Digitized Point"],
    "OE": [0, "Output Error"],
    "OF": [0, "Output Factors"],
    "OI": [0, "Output Identification"],
    "OO": [0, "Output Options"],
    "OP": [0, "Output P1&P2"],
    "OS": [0, "Output Status"],
    "PA": [0, "Plot Absolute"],
    "PD": [0, "Pen Down"],
    "PG": [0, "Page"],
    "PR": [0, "Plot Relative"],
    "PU": [0, "Pen Up"],
    "RA": [0, "? Read Address"],
    "RM": [0, "? Read Memory"],
    "SA": [0, "Select Alt Charset"],
    "SC": [0, "Scale"],
    "SI": [0, "Abs Char Size"],
    "SL": [0, "Char Slant"],
    "SM": [0, "Symbol Mode"],
    "SP": [0, "Select Pen"],
    "SR": [0, "Char Size Relative"],
    "SS": [0, "Select Standard Charset"],
    "SW": [0, "Scrolling Window"],
    "TA": [0, "Trace attribute"],
    "TC": [0, "???"],
    "TE": [0, "Self Test"],
    "TG": [0, "???"],
    "TL": [0, "Tick Length"],
    "TS": [0, "Trace spec"],
    "TQ": [0, "???"],
    "UC": [0, "User Def Char"],
    "VA": [0, "Adaptive Velocity"],
    "VN": [0, "Normal Velocity"],
    "VS": [0, "Select Velocity"],
    "WA": [0, "? Write Address <ADR>"],
    "WM": [0, "? Write Memory <DATA>[,<DATA>]*"],
    "XC": [0, "???"],
    "XT": [0, "X-Tick"],
    "YT": [0, "Y-Tick"],
    "ZC": [0, "Segment Close"],
    "ZD": [0, "Segment Delete"],
    "ZF": [0, "Segment Find"],
    "ZH": [0, "Segment Hardcopy"],
    "ZM": [0, "Segment Memory"],
    "ZO": [0, "Segment Open"],
    "ZR": [0, "Segment Read"],
    "ZS": [0, "Segment Scroll"],
    "ZV": [0, "Segment Visibility"],
    "ZW": [0, "Segment Write"],
    "ZZ": [0, "Segment Size"],
}

# Interrupts do not return
our_desc = '''
CWAI    x    | 3C        | FF        |
'''

class our_ins(mc6809.mc6809_ins):

    def assy_x(self):
        self.flow_J()
        return "#0xff"

def ttab(asp, a, b):
    while a < b:
        y = data.Txt(asp, a, pfx=1, align=1, label=True)
        a = y.hi

class Scrtxt(data.Data):
    def __init__(self, asp, lo):
        f = ""
        w = asp.bu16(lo)
        f += ".SCRTXT\tL, %d\n" % w
        hi = lo + 2
        t = ""
        l = []
        n = 0
        while w > 0:
            c = asp[hi]
            if c > 0x10:
                t += "%c" % c
                hi += 1
                w -= 1
                n += 1
            else:
                if n:
                    f += ".SCRTXT\tT, '" + t + "'\n"
                    l.append(t)
                    t = ""
                    n = 0
                hi += 1
                x = asp.bu16(hi)
                hi += 2
                y = asp.bu16(hi)
                hi += 2
                f += ".SCRTXT\tW, 0x%04x, 0x%04x\n" % (x, y)
        if n:
            f += ".SCRTXT\tT, '" + t + "'\n"
            l.append(t)

        ll = l[0].replace(" ", "_")
        asp.set_label(lo, "SCRTXT_" + ll)

        super().__init__(asp, lo, hi, "scrtxt")
        self.fmt = f
        self.compact = True

def example():
    cx = mc6809.mc6809()
    cx.m.map(
        mem.Stackup((FILENAMES[0],), nextto=__file__),
        0x0000,
    )
    cx.m.map(
        mem.Stackup((FILENAMES[1],), nextto=__file__),
        0xe000,
    )

    s = 0
    for a in range(0x0000, 0x2000, 2):
        s += cx.m.bu16(a)
    print("SUM 0x0000-0x1fff = 0x%x" % s)

    s = 0
    for a in range(0xe000, 0x10000, 2):
        s += cx.m.bu16(a)
    print("SUM 0xe000-0xffff = 0x%x" % s)

    cx.add_ins(our_desc, our_ins)

    for a, b in SYMBOLS.items():
        cx.m.set_label(a, b)

    gpu = hp1345a.hp1345a()
    gpu.m = cx.m

    cx.vectors(which=("RST", "NMI", "SWI", "IRQ", "FIRQ", "SWI2"))


    if True:
        # screen texts
        a = 0xd95
        while a < 0xf4d:
            z = Scrtxt(cx.m, a)
            a = z.hi

        Scrtxt(cx.m, 0x01db)
        Scrtxt(cx.m, 0xea56)
        Scrtxt(cx.m, 0xea6a)
        Scrtxt(cx.m, 0xea7d)
        Scrtxt(cx.m, 0xee37)
        Scrtxt(cx.m, 0xee51)
        Scrtxt(cx.m, 0xfa6d)

    if True:
        n = 0
        c = {}
        while cx.m.bu16(0xfd0 + n):
            y = data.Txt(cx.m, 0xfd0 + n, 0xfd0 + n + 2, align=1)
            ta = 0x1062 + n
            t = cx.m.bu16(ta)
            z = data.Codeptr(cx.m, ta, ta + 2, t)
            z.lcmt += y.txt
            cx.disass(t)
            if t not in c:
                c[t] = []
            if y.txt not in CMDS:
                print("Undoc command", y.txt)
                CMDS[y.txt] = [t, "???"]
            else:
                CMDS[y.txt][0] = t
            c[t].append(y.txt)
            n += 2
        for i in c:
            c[i].sort()
            cx.m.set_label(i, "CMD_" + "_".join(c[i]))

        for i in CMDS:
            c = CMDS[i]
            if c[0] == 0:
                print(i, "CMD not implemented (" + c[1] + ")")
                continue
            if c[1][0] == "?":
                print(i, "CMD not documented (%s)" % c[1][1:])
            cx.m.set_block_comment(
                c[0],
                " COMMAND " + i + " - " + c[1]
            )


    if True:
        for a in (0x129d, 0x17e3, 0x181e, 0xe0e3, 0xee7e):
            w = cx.m[a + 1] + 1
            t = cx.m.bu16(a + 4)
            for i in range(w):
                d = cx.m.bu16(t)
                data.Codeptr(cx.m, t, t + 2, d)
                cx.disass(d)
                t += 2

    if True:
        # Random strings
        ttab(cx.m, 0xf019, 0xf03b)
        ttab(cx.m, 0xf1d1, 0xf25c)
        ttab(cx.m, 0xf412, 0xf44c)
        ttab(cx.m, 0xefd7, 0xeff7)

    if True:
        a = 0xf56e
        while cx.m[a]:
            y = data.Txt(cx.m, a, a + 6, label=False, align=1)
            a = y.hi

    if True:
        for a in range(0xf811, 0xf825, 2):
            #d = cx.m.bu16(a)
            cx.codeptr(a)
            #cx.disass(d)

    if True:
        # HP1345 testpatterns
        cx.m.set_label(0xfbed, "IMG_PIKES_PEAK")
        cx.m.set_label(0xfd41, "IMG_FOCUS")
        for a0 in (0xfbed, 0xfd41):
            a = a0
            data.Const(cx.m, a, a + 2, func=cx.m.bu16, fmt="0x%x", size=2)
            l = cx.m.bu16(a)
            a += 2
            hp1345_render.svg(cx.m, a, a + l*2)
            while l > 0:
                gpu.disass(a, gpu.m)
                a += 2
                l -= 1

    if True:
        # No idea, possibly length error in IMG_FOCUS ?
        data.Const(cx.m, 0xff17, 0xff19, fmt="0x%04x", func=cx.m.bu16, size=2)

    if True:
        # Special character handling
        b = 0xf75b
        c = 0xf778
        cx.m.set_label(b, "CHR_TBL_KEY")
        cx.m.set_label(c, "CHR_TBL_PTR")
        data.Const(cx.m, b, c, fmt="0x%x")
        a = c
        while b < c:
            p = cx.m.bu16(a)
            y = data.Dataptr(cx.m, a, a + 2, p)
            cx.m.set_label(p, "CHR_TBL_%02x" % cx.m[b])
            while True:
                z = data.Const(cx.m, p, p + 2, func=cx.m.bu16, fmt="0x%x", size=2)
                if cx.m[p + 1] & 0x80:
                    break
                p += 2
            b += 1
            a += 2

    # Stuff not accessed from anywhere

    cx.disass(0xe5a1)
    cx.m.set_block_comment(0xe5a1, "Unused ROM checksum code")
    cx.m.set_block_comment(0xe5a1, "NB: Expects low rom at 0xc000")

    cx.disass(0x1acf)
    cx.disass(0xebf0)

    cx.m.set_block_comment(0x003b9, "Outputs $0x0c - Term (not comma)")
    cx.m.set_block_comment(0x003b9, "Outputs $0x12 - Error")
    cx.m.set_block_comment(0x003b9, "Outputs $0x1a = 0")
    cx.m.set_block_comment(0x003b9, "Outputs $0x1b - Digits")
    cx.m.set_block_comment(0x003b9, "Outputs $0x1f - Decimals")
    cx.m.set_block_comment(0x003b9, "Outputs $0x27 - Negative")
    cx.m.set_block_comment(0x003b9, "Outputs $0x31+32 - Number")
    cx.m.set_block_comment(0xf895, "Set reset, clear interrupt, Clr reset")

    return NAME, (cx.m,)

if __name__ == '__main__':
    listing.Example(example)
