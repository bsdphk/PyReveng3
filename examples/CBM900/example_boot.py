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
This is the boot EPROM(s) from the Commodore 900.

See also: https://datamuseum.dk/wiki/Commodore/CBM900
'''

import os
from pyreveng import job, mem, code, data, misc, listing, charset
import pyreveng.cpu.z8000 as z8000

def mem_setup():
    m = mem.byte_mem(0x0, 0x8000)
    fn = os.path.join(os.path.dirname(__file__), "EPROM_C_900_boot-")
    m.load_binfile(0x1, 2, fn + "L_V_1.0.bin")
    m.load_binfile(0x0, 2, fn + "H_V_1.0.bin")
    return m

def setup():
    pj = job.Job(mem_setup(), "CBM900_BOOT")
    cx = z8000.z8001()
    return pj, cx

def chargen(pj, a):
    pj.m.set_label(0x45fe, "CHARGEN")
    s = charset.SVG_Charset(
        "/tmp/_.svg",
        cols=8,
        char_w=14,
        char_h=26,
        imargin=1,
        linewidth=2,
    )
    for i in range(128):
        l = []
        for j in range(26):
            l.append(pj.m.bu16(a + 10 + i * 66 + j * 2))
        s.set_char(i // 16, i % 16, l)
        y = data.Pstruct(pj, a + 8 + i * 66, ">BB32H")
        y.compact = True
    s.render()

def hd6845_tab(pj):
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
    pj.set_label(a, "HD6845_PARAMS[]")
    while a < 0x436a:
        x = data.Pstruct(pj, a, "BB")
        y = pj.m.rd(a)
        if y < len(hd6845reg):
            x.lcmt += hd6845reg[y]
        a += 2
    data.Pstruct(pj, a, ">H")


def task(pj, cx):
    # const.w32(p, 0x01000614)
    # pj.set_label(0x01000614, "screen_ptr")
    #pj.set_label(0x01001800, "is_lores")
    #pj.set_label(0x010017ff, "is_hires")
    #pj.set_label(0x01001562, "input_buffer")
    #pj.set_label(0x01001562, "input_buffer")

    pj.set_label(0x0090, "size_ram")
    pj.set_label(0x00ca, "ram_sized")
    pj.set_label(0x00f4, "copy_dataseg")
    pj.set_label(0x020a, "INB(adr)")
    pj.set_label(0x0214, "INW(adr)")
    pj.set_label(0x021c, "OUTB(adr,data)")
    pj.set_label(0x0228, "OUTW(adr,data)")
    pj.set_label(0x0234, "JMP(adr)")
    pj.set_label(0x023a, "SetMMU(int seg, int base1, int base2)")
    pj.set_label(0x0274, "LDIRB(src,dst,len)")
    pj.set_label(0x0286, "bzero(void *, int)")
    pj.set_label(0x0326, "ResetHandler")
    pj.set_label(0x0582, "mainmenu()")
    pj.set_label(0x06e4, "long hex2int(char *)")
    pj.set_label(0x074c, "DiskParam(char *)")
    pj.set_label(0x07d4, "ShowRam(void)")
    pj.set_label(0x08b0, "int HexDigit(char)")
    pj.set_label(0x0900, "puts(char *)")
    pj.set_label(0x092c, "readline(char *)")
    pj.set_label(0x0998, "ShowMenu(void)")
    pj.set_label(0x09d8, "Floppy(char *)")
    pj.set_label(0x0a1c, "floppy_format")
    pj.set_label(0x0ac0, "ParkDisk(char *)")
    pj.set_label(0x0b26, "puthex(long val,int ndig)")
    pj.set_label(0x0ccc, "Detect_HiRes")
    pj.set_label(0x0ce4, "Found_HiRes")
    pj.set_label(0x0cf0, "Detect_LoRes")
    pj.set_label(0x0d06, "Found_LoRes")
    pj.set_label(0x0d1c, "MMU_Video_Setup")
    pj.set_label(0x0d56, "Hello_HiRes")
    pj.set_label(0x0d7a, "Hello_LoRes")
    pj.set_label(0x0d96, "No_Video")
    pj.set_label(0x0d9c, "Hello_Serial")
    pj.set_label(0x0db8, "RAM_check")
    pj.set_label(0x0e28, "ram_error")
    pj.set_label(0x0e74, "hires_ram_error")
    pj.set_label(0x0eb6, "hires_ram_error")
    pj.set_label(0x0f0a, "serial_ram_error")
    pj.set_label(0x0fc2, "putchar(char)")
    pj.set_label(0x104a, "int getchar()")
    pj.set_label(0x111e, "FD_cmd(void *)")
    pj.set_label(0x11a6, "wdread([0..3])")
    pj.set_label(0x134a, "InitDrives(?)")
    pj.set_label(0x1420, "FD_Format([0..1])")
    pj.set_label(0x1548, "HD_Park(?)")
    pj.set_label(0x1768, "char *Boot(char *)")
    pj.set_label(0x2040, "TrapHandler")
    pj.set_label(0x20b8, "Debugger(void)")
    pj.set_label(0x20cc, "HiResPutChar(char *)")
    pj.set_label(0x20e4, "hires_putc(RL0,>R10)")
    pj.set_label(0x20ee, "hires_clear")
    pj.set_label(0x216a, "hires_stamp_char")
    pj.set_label(0x21b6, "hires_NL")
    pj.set_label(0x21fc, "hires_scroll")
    pj.set_label(0x2244, "hires_CR")
    pj.set_label(0x225e, "hires_FF")
    pj.set_label(0x226c, "hires_BS")
    pj.set_label(0x231e, "Debugger_Menu()")
    pj.set_label(0x2bb6, "Debugger_MainLoop()")
    pj.set_label(0x3b28, "OutStr(char*)")
    pj.set_label(0x420c, "LoResPutChar(char *)")
    pj.set_label(0x4224, "lores_putc(RL0,>R10)")
    pj.set_label(0x422c, "lores_setup")
    pj.set_label(0x4276, "lores_dochar")
    pj.set_label(0x4296, "lores_stamp_char")
    pj.set_label(0x42b6, "lores_NL")
    pj.set_label(0x42c2, "lores_scroll")
    pj.set_label(0x42ee, "lores_CR")
    pj.set_label(0x4304, "lores_cursor")
    pj.set_label(0x431e, "lores_FF")
    pj.set_label(0x4326, "lores_BS")

    cx.vectors(pj)
    hd6845_tab(pj)
    for v, a in (
	("VEC0", 0x0008,),
	("VEC1", 0x0010,),
	("VEC2", 0x0018,),
	("VEC3", 0x0020,),
	("VEC4", 0x0028,),
	("VEC5", 0x0030,),
    ):
        cx.vector(pj, a, v)

    for a in range(0x06b2, 0x06da, 4):
        y = cx.codeptr(pj, a)
        pj.set_label(y.dst, "PTR_%x" % a)

    for a in range(0x31cc, 0x31dc, 4):
        y = cx.codeptr(pj, a)
        pj.set_label(y.dst, "PTR_%x" % a)

    for a in range(0x39da, 0x3a18, 4):
        y = cx.codeptr(pj, a)
        pj.set_label(y.dst, "PTR_%x" % a)

    for a in range(0x419e, 0x4202, 4):
        y = cx.codeptr(pj, a)
        pj.set_label(y.dst, "PTR_%x" % a)

    pj.todo(0x20bc, cx.disass)
    pj.todo(0x3ec6, cx.disass)

    for a in (
        0x01c0,
        0x0c0a,
        0x0c44,
        0x0e9e,
        0x0ee0,
    ):
        pj.m.set_block_comment(a, "CALL_RR10_%x" % a)
        pj.todo(a, cx.disass)

    pj.m.set_block_comment(0x6800, "DATA SEGMENT, len=0x1016")

    chargen(pj, 0x45fe + 0)

    while pj.run():
        pass

    misc.fill_all_blanks(pj, minsize=2)

    while pj.run():
        pass


if __name__ == '__main__':
    pj, cx = setup()
    task(pj, cx)
    code.lcmt_flows(pj)
    listing.Listing(pj, ncol=8)
