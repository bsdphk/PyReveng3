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

'''Commodore CBM900 - Boot EPROM

See also: https://datamuseum.dk/wiki/Commodore/CBM900
'''

from pyreveng import mem, data, listing, charset
import pyreveng.cpu.z8000 as z8000

NAME = "CBM900_BOOT"

LABELS = {
    0x0090: "size_ram",
    0x00ca: "ram_sized",
    0x00f4: "copy_dataseg",
    0x020a: "INB(adr)",
    0x0214: "INW(adr)",
    0x021c: "OUTB(adr,data)",
    0x0228: "OUTW(adr,data)",
    0x0234: "JMP(adr)",
    0x023a: "SetMMU(int seg, int base1, int base2)",
    0x0274: "LDIRB(src,dst,len)",
    0x0286: "bzero(void *, int)",
    0x0326: "ResetHandler",
    0x0582: "mainmenu()",
    0x06e4: "long hex2int(char *)",
    0x074c: "DiskParam(char *)",
    0x07d4: "ShowRam(void)",
    0x08b0: "int HexDigit(char)",
    0x0900: "puts(char *)",
    0x092c: "readline(char *)",
    0x0998: "ShowMenu(void)",
    0x09d8: "Floppy(char *)",
    0x0a1c: "floppy_format",
    0x0ac0: "ParkDisk(char *)",
    0x0b26: "puthex(long val,int ndig)",
    0x0ccc: "Detect_HiRes",
    0x0ce4: "Found_HiRes",
    0x0cf0: "Detect_LoRes",
    0x0d06: "Found_LoRes",
    0x0d1c: "MMU_Video_Setup",
    0x0d56: "Hello_HiRes",
    0x0d7a: "Hello_LoRes",
    0x0d96: "No_Video",
    0x0d9c: "Hello_Serial",
    0x0db8: "RAM_check",
    0x0e28: "ram_error",
    0x0e74: "hires_ram_error",
    0x0eb6: "hires_ram_error",
    0x0f0a: "serial_ram_error",
    0x0fc2: "putchar(char)",
    0x104a: "int getchar()",
    0x111e: "FD_cmd(void *)",
    0x11a6: "wdread([0..3])",
    0x134a: "InitDrives(?)",
    0x1420: "FD_Format([0..1])",
    0x1548: "HD_Park(?)",
    0x1768: "char *Boot(char *)",
    0x2040: "TrapHandler",
    0x20b8: "Debugger(void)",
    0x20cc: "HiResPutChar(char *)",
    0x20e4: "hires_putc(RL0,>R10)",
    0x20ee: "hires_clear",
    0x216a: "hires_stamp_char",
    0x21b6: "hires_NL",
    0x21fc: "hires_scroll",
    0x2244: "hires_CR",
    0x225e: "hires_FF",
    0x226c: "hires_BS",
    0x231e: "Debugger_Menu()",
    0x2bb6: "Debugger_MainLoop()",
    0x3b28: "OutStr(char*)",
    0x420c: "LoResPutChar(char *)",
    0x4224: "lores_putc(RL0,>R10)",
    0x422c: "lores_setup",
    0x4276: "lores_dochar",
    0x4296: "lores_stamp_char",
    0x42b6: "lores_NL",
    0x42c2: "lores_scroll",
    0x42ee: "lores_CR",
    0x4304: "lores_cursor",
    0x431e: "lores_FF",
    0x4326: "lores_BS",
}

def fc_outstr(asp, ins):
    ''' Spot string arguments to OutStr() and puts() '''
    for f in ins.flow_out:
        if f.to not in (0x3b28, 0x0900):
            continue
        if asp.bu16(ins.lo - 2) != 0x91e0:
            continue
        if asp.bu16(ins.lo - 8) != 0x1400:
            continue
        y = data.Txt(asp, asp.bu32(ins.lo - 6), align=1, label=False)
        asp.set_line_comment(ins.lo, '"' + y.txt + '"')


def chargen(asp, a):
    asp.set_label(0x45fe, "CHARGEN")
    s = charset.SVG_Charset(
        "/tmp/cbm900_hires.svg",
        cols=8,
        char_w=14,
        char_h=26,
        imargin=1,
        linewidth=2,
    )
    for i in range(128):
        l = []
        for j in range(26):
            l.append(asp.bu16(a + 10 + i * 66 + j * 2))
        s.set_char(i // 16, i % 16, l)
        y = data.Pstruct(asp, a + 8 + i * 66, ">BB32H")
        y.compact = True
    s.render()

def hd6845_tab(asp):
    hd6845reg = (
        "Horizontal Total",
        "Horizontal Displayed",
        "Horizontal Sync Position",
        "Sync Width",
        "Vertical Total",
        "Vertical Total Adjust",
        "Vertical Displayed",
        "Vertical Sync Position",
        "Interlace & Skew",
        "Maximum Raster Address",
        "Cursor Start Raster",
        "Cursor End Raster",
        "Start Address (H)",
        "Start Address (L)",
        "Cursor (H)",
        "Cursor (L)",
        "Light Pen (H)",
        "Light Pen (L)",
    )
    a = 0x434a
    asp.set_label(a, "HD6845_PARAMS[]")
    while a < 0x436a:
        x = data.Pstruct(asp, a, "BB")
        y = asp[a]
        if y < len(hd6845reg):
            x.lcmt += hd6845reg[y]
        a += 2
    data.Pstruct(asp, a, ">H")

def switch(cx, a, n):
    for i in range(n):
        y = data.Pstruct(cx.m, a + i * 2, ">H")
        b = a + n * 2 + i * 4
        z = cx.codeptr(b)
        cx.m.set_label(z.dst, "CASE_0x%x_0x%02x" % (a, y.data[0]))

def example():
    m0 = mem.Stackup(
        files=(
            ("EPROM_C_900_boot-L_V_1.0.bin", "EPROM_C_900_boot-H_V_1.0.bin"),
        ),
        nextto=__file__,
    )

    cx = z8000.z8001()
    cx.m.map(m0, 0x00000000)
    cx.m.map(m0, 0x01000000, 0x01001016, 0x00006800)
    cx.flow_check.append(fc_outstr)
    cx.z8010_mmu(0xf8)
    cx.z8010_mmu(0xfc)

    for i, j in LABELS.items():
        cx.m.set_label(i, j)

    y = data.Data(cx.m, 0x6800, 0x6800 + 0x1016, "MAP SEG1")
    y.compact = None
    y.rendered = str(y)
    cx.m.insert(y)

    # const.w32(p, 0x01000614)
    # cx.m.set_label(0x01000614, "screen_ptr")
    #cx.m.set_label(0x01001800, "is_lores")
    #cx.m.set_label(0x010017ff, "is_hires")
    #cx.m.set_label(0x01001562, "input_buffer")
    #cx.m.set_label(0x01001562, "input_buffer")

    if True:
        cx.vectors()

    if True:
        for v, a in (
                ("VEC0", 0x0008,),
                ("VEC1", 0x0010,),
                ("VEC2", 0x0018,),
                ("VEC3", 0x0020,),
                ("VEC4", 0x0028,),
                ("VEC5", 0x0030,),
        ):
            b = cx.vector(a, v)

    if True:
        switch(cx, 0x69e, 0xa)
        switch(cx, 0x31c4, 0x4)
        switch(cx, 0x39ba, 0x10)

    if True:
        for a in range(0x419e, 0x4202, 4):
            y = cx.codeptr(a)
            cx.m.set_label(y.dst, "PTR_%x" % a)

        cx.disass(0x20bc)
        cx.disass(0x3ec6)

        cx.disass(0x06da)
        cx.disass(0x0214)
        cx.disass(0x10ec)
        cx.disass(0x11a6)
        cx.disass(0x2028)
        cx.disass(0x2034)
        cx.disass(0x3bd2)

        for a in (
                0x01c0,
                0x0c0a,
                0x0c44,
                0x0e9e,
                0x0ee0,
                0x0eae,
                0x0ef0,
        ):
            cx.m.set_line_comment(a, "CALL_RR10_%x" % a)
            cx.disass(a)

        for a in range(0x3e90, 0x3ea0, 4):
            y = cx.codeptr(a)
            cx.m.set_label(y.dst, "PTR_%x" % a)

        chargen(cx.m, 0x45fe + 0)

        for a, b, c in (
                (0x01000006, 0x0100000e, 4),
                (0x0100003e, 0x01000076, 14),
                (0x01000010, 0x0100003c, 4),
                (0x01000618, 0x01000658, 4),
                (0x01000766, 0x010007ae, 4),
                (0x010007b4, 0x010007c4, 4),
                (0x01000c1a, 0x01000c26, 4),
        ):
            while a < b:
                y1 = cx.dataptr(a)
                y2 = data.Txt(cx.m, y1.dst, align=1, label=False)
                cx.m.set_line_comment(y1.lo, '"' + y2.txt + '"')
                a += c

        for a in range(0x0100065a, 0x01000708, 6):
            data.Txt(cx.m, a, label=False, align=2)

        for a in range(0x01000c26, 0x01000e19, 6):
            y1 = data.Pstruct(cx.m, a, ">HHH")

        data.Txt(cx.m, 0x0c75, align=1, label=False)
        data.Txt(cx.m, 0x0cb1, align=1, label=False)
        for a in range(0xc4a, 0xc74, 2):
            data.Pstruct(cx.m, a, "BB")

        hd6845_tab(cx.m)

    return NAME, (cx.m,)

if __name__ == '__main__':
    listing.Example(example)
