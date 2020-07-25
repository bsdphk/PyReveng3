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

'''HP8904 Synthesizer/Level Generator
'''

from pyreveng import mem, listing, data, assy
import pyreveng.cpu.mc6809 as mc6809
import pyreveng.cpu.banked as banked
import pyreveng.toolchest.bitmap as bitmap

NAME = "HP8904_BANKED"
FILENAME1 = "08904-87011.BIN"
DIR = "/critter/Doc/TestAndMeasurement/HP8904A/FW/"
NPG = 6

CHARSET = dict(data.ASCII.items())
CHARSET[0x00] = "f̲"
CHARSET[0x01] = "1̲"
CHARSET[0x02] = "2̲"
CHARSET[0x03] = "3̲"
CHARSET[0x04] = "4̲"
CHARSET[0x05] = "φ"
CHARSET[0x06] = "µ"
CHARSET[0xff] = "▒"

class Txt(data.Txt):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, charset=CHARSET, **kwargs)

SYMBOLS = (
    (0, 0x0100, "SERVICE_SWITCH"),
    (0, 0x0200, "NSMIC"),
    (0, 0x0300, "LCD_CTL"),
    (0, 0x0301, "LCD_DATA"),
    (0, 0x0400, "HPIB_0"),
    (0, 0x0401, "HPIB_1"),
    (0, 0x0402, "HPIB_2"),
    (0, 0x0403, "HPIB_3"),
    (0, 0x0404, "HPIB_4"),
    (0, 0x0405, "HPIB_5"),
    (0, 0x0406, "HPIB_6"),
    (0, 0x0407, "HPIB_7"),
    (0, 0x0600, "IO_600"),
    (0, 0x0900, "LEDS"),
    (0, 0x0a00, "KBD_SCAN"),
    (0, 0x0b00, "HOPLATCH"),
    (0, 0x0c00, "OUTPUT_1"),
    (0, 0x0d00, "OUTPUT_2"),
    (0, 0x0e00, "OUTPUT_3"),
    (0, 0x0f00, "OUTPUT_4"),
    (0, 0x1000, "PTM_0"),
    (0, 0x1001, "PTM_1"),
    (0, 0x1002, "PTM_TIMER1"),
    (0, 0x1003, "PTM_TIMER2"),
    (0, 0x1004, "PTM_TIMER3"),

    (0, 0x3ff6, "ram_firmware_copy"),
    (0, 0x3ffc, "ram_options"),
    (0, 0x4000, "page_no_latch"),
    (0, 0x4027, "ERROR_MSG(B)"),

    (0, 0x8dba, "SETUP_MENU(2, U)"),
    (0, 0x8efe, "MENU_EXIT()"),
    (0, 0x8d5c, "MENU_SHOW_PAGE(0)"),
    (0, 0x8de1, "MENU_HANDLE_KEY(0)"),

    (0, 0x8f6a, "KEY_HANDLER_DEFAULT(0)"),
    (0, 0x8f9a, "do_key_0x01"),
    (0, 0x8f76, "do_key_0x10"),
    (0, 0x8f83, "do_key_0x13_f1"),
    (0, 0x8f9a, "do_key_0x14_f2"),
    (0, 0x8f9d, "do_key_0x15_f3"),
    (0, 0x8f9a, "do_key_0x16_f4"),
    (0, 0x8fb4, "do_key_0x17_next"),
    (0, 0x8fd9, "do_key_0x18_prev"),
    (0, 0x8f9a, "do_key_0x3c"),

    (0, 0xc52a, "MENU_NOP()"),
    (0, 0xc533, "MEMCMP(6, len, src, dst)"),
    (0, 0xc579, "MEMCPY(6, len, src, dst)"),

    (0, 0xd7be, "LCD_CHARGEN(4, int charno, void *chardef)"),
    (0, 0xd963, "LCD_INIT(0)"),
    (0, 0xd68f, "LCD_WR_CTL(2, int)"),
    (0, 0xd6b1, "LCD_WR_DATA(2, int)"),
    (0, 0xd71c, "LCD_SET_ADR(2, int)"),
    (0, 0xd6d3, "LCD_RD_DATA()"),
    (0, 0xd6f8, "LCD_RD_CTL()"),
    (0, 0xd867, "LCD_WRITE(6, pos, len, ptr)"),
    (0, 0xd822, "LCD_WRITE_DIRECT(6, pos, len, ptr)"),
    (0, 0xdd5d, "PG_JMP"),
    (0, 0xd9fc, "SET_PAGE(2, pgno)"),
    (0, 0xd906, "LCD_WRITE_ENTIRE(2, ptr)"),
    (0, 0x246a, "pg_jmp_page"),
    (0, 0x246b, "pg_jmp_offset"),
    (0, 0x24c6, "nmi_vector"),
    (0, 0x24c8, "firq_vector"),
    (0, 0x2202, "interrupt_vector_flags"),
    (0, 0x2206, "irq_happened_flag"),
    (0, 0xf065, "SET_NMI_VECTOR"),
    (0, 0xf07f, "SET_FIRQ_VECTOR"),
    (0, 0xf0dc, "FIRQ_HANDLER"),
    (0, 0xf18f, "IRQ_HANDLER"),
    (0, 0xf099, "NMI_HANDLER"),
    (0, 0xec93, "firmware_version"),

    (1, 0x4170, "IRQ_HANDLER_0"),
    (1, 0x411f, "IRQ_HANDLER_1"),
    (2, 0x444c, "IRQ_HANDLER_2"),
    (2, 0x42d1, "IRQ_HANDLER_3"),
    (4, 0x419d, "IRQ_HANDLER_4"),

    (0, 0x221b, "menu_key_to_handle"),
    (0, 0x2244, "menu_ptr"),
    (0, 0x2246, "menu_last_pg"),
    (0, 0x2682, "menu_cur_pg"),
    (0, 0x223c, "menu_f1_func"),
    (0, 0x223e, "menu_f2_func"),
    (0, 0x2240, "menu_f3_func"),
    (0, 0x2242, "menu_f4_func"),

    (0, 0x8e82, "INJECT_KEY_PRESS(2, keyno)"),
)

def romsum(m, lo, hi):
    '''XXX: this looks bogus'''
    b = 0
    c = 0
    for j in range(0x4000, 0x8000):
        b += m.m[j] + c
        c = b >> 8
        c = 1
        b &= 0xff
    print("Bank sum %x %x" % (b, c))

def dataptr(cx, a):
    y = data.Dataptr(cx.m, a, a + 2, cx.m.bu16(a))
    return y

def textptr(cx, a):
    y = dataptr(cx, a)
    Txt(cx[0].m, y.dst, pfx=1, label=False)
    return y

def menuxxx(cx, a):
    s = set()
    for i in range(0, 5):
        y = dataptr(cx, a + i * 2)
        if y.dst not in s:
            s.add(y.dst)
            Txt(cx.m, y.dst, y.dst + 40, label=False)

class MenuPage(data.Data):

    def __init__(self, cx, adr):
        super().__init__(cx.m, adr, adr + 10)
        self.tp = []
        x = cx.m.bu16(adr)
        self.tp.append(Txt(cx.m, x, x + 40, label=False))
        self.tp.append(Txt(cx.m, x + 40, x + 80, label=False))
        self.fp = []
        for i in range(1, 5):
            self.fp.append(cx.m.bu16(adr + i * 2))
            cx.m.set_block_comment(self.fp[-1], "Menu@%x[f%d]" % (adr, i))
            cx.disass(self.fp[-1])

    def render(self):
        t = ".MENU {\n"
        for i in self.tp:
            t += "\t.txt =\t'" + i.txt + "'\n"
        for i, j in enumerate(self.fp):
            t += "\t.f%d =\t" % (i + 1) + self.aspace.adr(j) + "\n"
        t += "}"
        return t

class Menu():
    def __init__(self, cx, adr):
        y = data.Const(cx.m, adr - 1, adr)
        for i in range(cx.m[adr - 1] + 1):
            y = MenuPage(cx, adr)
            adr = y.hi

class lex(data.Data):

    def __init__(self, cx, lo, pfx):
        assert cx.m[lo]
        hi = lo + 4
        if cx.m[lo + 1]:
            hi += 1
        super().__init__(cx.m, lo, hi)
        self.pfx = pfx
        self.token = '%c' % cx.m[lo]
        self.args = []
        if cx.m[lo + 1]:
            self.args.append(cx.m[lo + 1])
            self.args.append(cx.m[lo + 4])
        self.dst = cx.m.bu16(lo + 2)
        if cx.m[lo + 1]:
            cx.disass(self.dst)
            cx.m.set_block_comment(self.dst, self.render())

    def render(self):
        return ".LEX\t'%s%s', 0x%x, %s" % (self.pfx, self.token, self.dst, str(self.args))

def lextab(cx, a, pfx):
    cx.m.set_label(a, "LEX_HPIB_CMD_" + pfx)
    while cx.m[a]:
        y = lex(cx, a, pfx)
        if not y.args:
            lextab(cx, y.dst, pfx + y.token)
        a = y.hi
    y = data.Data(cx.m, a, a + 1)
    y.rendered = ".LEX\tEND"

def pgc(cx):
    for a in (
        0x93fc,
        0x9412,
    ):
        cx.disass(a)
        cx.m.set_line_comment(a, "MANUAL:pgc()")

    for n, a in enumerate(range(0x9ab3, 0x9ae7, 2)):
        print("NA", n, "0x%x" % a)
        y = dataptr(cx, a)
        lextab(cx, y.dst, "%c" % (0x41 + n))

    cx.m.set_block_comment(0x8de1, '''
Process Key-press in Menu Context
    0x13 = f1
    0x14 = f2
    0x15 = f3
    0x16 = f4
    0x17 = Next
    0x18 = Prev
''')

    for a, b in (
        (0xea5f, 0x28),
        (0xea87, 0x23),
        (0xeaaa, 0x28),
        (0xeadf, 0x28),
        (0xeb07, 0x28),
        (0xeb7f, 0x28),
        (0xeba7, 0x15),
        (0xebbc, 0x15),
        (0xebd1, 0x28),
        (0xebf9, 0x28),
        (0xec21, 0x28),
        (0xec93, 0x06),
        (0xec99, 0x28),
        (0xecc1, 0x28),
        (0xece9, 0x28),
        (0xeda0, 0x28),
        (0xedc8, 0x28),
        (0xedf0, 0x28),
        (0xee18, 0x28),
    ):
        Txt(cx.m, a, a + b)
   

def pg0(cx):
    menuxxx(cx, 0x4018)
    cx.codeptr(0x4004)
    cx.codeptr(0x4006)
    cx.codeptr(0x4008)
    cx.codeptr(0x400a)
    cx.codeptr(0x400c)
    cx.codeptr(0x400e)
    cx.codeptr(0x4010)
    cx.codeptr(0x4012)
    cx.codeptr(0x4014)
    cx.codeptr(0x4016)
    cx.codeptr(0x4022)
    cx.codeptr(0x4024)
    cx.codeptr(0x4027)
    cx.codeptr(0x4029)

    for a in range(0x40ce, 0x410b, 7):
        x = cx.m[a + 1]
        y = cx.m.bu16(a + 3)
        print(cx, " -> %x" % a, "%x" % x, "%x" % y)
        cx[x].disass(y)


def pg1(cx):
    for a in range(0x43af, 0x43bf, 2):
        cx.codeptr(a)
    cx.disass(0x4170)	# IRQ handler
    cx.disass(0x411f)	# IRQ handler

def pg2(cx):
    cx.disass(0x42d1)	# IRQ handler
    cx.disass(0x444c)	# IRQ handler

def pg3(cx):
    for a, b in (
        (0x4012, 0x18),
        (0x42ba, 0x28),
        (0x42e2, 0x1a),
        (0x42fc, 0x28),
        (0x4324, 0x28),
        (0x434c, 0x10),
        (0x436c, 0x18),
        (0x4384, 0x28),
        (0x43ac, 0x1a),
        (0x43c6, 0x28),
        (0x43ee, 0x1a),
        (0x4408, 0x1a),
        (0x4422, 0x28),
        (0x444a, 0x28),
        (0x4472, 0x28),
        (0x44a0, 0x1a),
        (0x44ba, 0x28),
        (0x44e2, 0x6),
        (0x5647, 0x28),
        (0x566f + 0 * 0x28, 0x28),
        (0x566f + 1 * 0x28, 0x28),
        (0x566f + 2 * 0x28, 0x28),
        (0x566f + 3 * 0x28, 0x28),
        (0x566f + 4 * 0x28, 0x28),
        (0x566f + 5 * 0x28, 0x28),
        (0x566f + 6 * 0x28, 0x28),
        (0x566f + 7 * 0x28, 0x28),
        (0x57af, 0x28),
        (0x57d7, 0x28),
        (0x57ff, 0x28),
        (0x5827, 0x28),
        (0x584f, 0x10),
        (0x585f, 0x28),
        (0x5887, 0x28),
        (0x58af, 0x28),
        (0x58d7, 0x28),
        (0x58ff, 0x28),
        (0x5927, 0x28),
        (0x594f, 0x28),
        (0x5977, 0x28),
        (0x664f, 0x03),
    ):
        Txt(cx.m, a, a + b)
    cx.m.set_label(0x44e2, "SERVICE_CODE")

    for a in range(0x4502, 0x45e2, 4):
        b = cx.m.bu16(a + 2)
        data.Pstruct(cx.m, a, ">BBH", fmt="0x%02x, 0x%02x, 0x%04x")
        Txt(cx.m, b, b + cx.m[a + 1], label=False)

    for a in range(0x6654, 0x6760, 4):
        b = cx.m.bu16(a + 2)
        data.Pstruct(cx.m, a, ">BBH", fmt="0x%02x, 0x%02x, 0x%04x")
        Txt(cx.m, b, b + cx.m[a + 1], label=False)

    a = 0x5344
    while a < 0x5382:
        y = Txt(cx.m, a)
        a = y.hi

def pg4(cx):
    cx.disass(0x419d)	# IRQ handler

    for a in range(0x424c, 0x425c, 2):
        y = cx.codeptr(a)
        cx.m.set_label(y.dst, "FROM_0x%x" % a)

    for a in range(0x4337, 0x4347, 2):
        y = cx.codeptr(a)
        cx.m.set_label(y.dst, "FROM_0x%x" % a)

def pg5(cx):
    for a in range(0x514a, 0x519a, 8):
        data.Pstruct(cx.m, a, ">d")
    for a in (
        0x77bc,
        0x77c3,
    ):
        l = cx.m.bu16(a)
        data.Txt(cx.m, a + 2, a + 2 + l)
    for a in (
        0x41ca,
        0x7417,
        0x7419,
        0x7488,
    ):
        cx.disass(a)
        cx.m.set_line_comment(a, "MANUAL:pg5()")


def flow_out_ffed(a, b):
    if b.mne == "BSR" and b.dstadr == 0xffed:
        print("FFED", a, b.render(), b.flow_out)
        b.flow_out.pop(1)

mc6809_prologue = '''
PROLOGUE	a	|1 1 1 1 1 1 0 0|a		|b		|0 0 0 1 0 1 1 1| c		| d		|
PROLOGUE	b	|1 1 0 0 1 1 0 0|a		|b		|0 0 0 1 0 1 1 1| c		| d		|
'''

class mc6809_prologue_ins(assy.Instree_ins):

    def __init__(self, lim, lang):
        super().__init__(lim, lang)
        i = (self['c'] << 8) | self['d']
        i = (self.hi + i) & 0xffff
        if i != 0xfd89:
            raise assy.Invalid("6809 PROLOGUE wrong dest")

    def assy_a(self):
        i = (self['a'] << 8) | self['b']
        self.heap = self.lang.m.bu16(i)
        if self.heap:
            y = data.Const(self.lang.m, i, i + 2, func=self.lang.m.bu16, size=2)
        else:
            y = data.Const(self.lang.m, i, i + 1, size=1)
        return assy.Arg_imm(self.heap)

    def assy_b(self):
        i = (self['a'] << 8) | self['b']
        self.heap = i
        return assy.Arg_imm(self.heap)


mc6809_switches = '''
SWITCH	-	|1 0 0 0 1 1 1 0| a		| b		| 58 | 49 | 6E | 9B |
SWITCH	-	|1 0 0 0 1 1 1 0| a		| b		| 4F | 58 | 49 | 6E | 9B |
'''

class mc6809_switch_ins(assy.Instree_ins):

    def __init__(self, lim, lang):
        super().__init__(lim, lang)
        tbl = self['a'] << 8
        tbl |= self['b']
        if tbl != self.hi:
            raise assy.Invalid("Not a recognized 6809 SWITCH ")
        # print("6809SW", lim, tbl - self.hi)
        a = self.hi
        n = 0
        while True:
            if lang.m.occupied(a):
                break
            d = lang.m.bu16(a)
            if d - self.hi > 0x800:
                # print("SW", "0x%x" % self.hi, n, "%x" % a, "%x" % d, self.hi - d, lang.m.occupied(a), "BAIL")
                break
            if self.hi - d > 0x800:
                # print("SW", "0x%x" % self.hi, n, "%x" % a, "%x" % d, self.hi - d, lang.m.occupied(a), "BAIL")
                break
            #print("SW", "0x%x" % self.hi, n, "%x" % a, "%x" % d, self.hi - d, lang.m.occupied(a))
            y = lang.codeptr(a)
            lang.m.set_label(y.dst, "SWITCH_0x%x_0x%x" % (self.hi, n))
            a += 2
            n += 1
        raise assy.Invalid("6809 SWITCH incomplete")

mc6809_c_call = '''
NO_ARG  d       | CE | 00 | 00 | 34 | 40 | 17 | a             | b             | 32 | 62 |
'''

class mc6809_c_call_ins(assy.Instree_ins):

    def __init__(self, lim, lang):
        super().__init__(lim, lang)
        dst = (self['a'] << 8) | self['b']
        self.dst = (self.hi + dst - 2) & 0xffff
        lang.disass(self.dst)
        self.mne = "CALL"

    def assy_d(self):
        return assy.Arg_dst(self.lang.m, self.dst, sfx="()")
        

class mycpu(mc6809.mc6809):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, macros=True)
        self.flow_check.append(flow_out_ffed)
        self.add_ins(mc6809_switches, mc6809_switch_ins)
        self.add_ins(mc6809_prologue, mc6809_prologue_ins)
        self.add_ins(mc6809_c_call, mc6809_c_call_ins)

def lcd_config(cx):

    a = 0xea03
    for ch in range(8):
        bm = bitmap.BitMap(8, 8)
        for y in range(8):
            for x in range(8):
                if cx[1].m[a + y] & (1<<x):
                    bm.set(7 - x, y)
        z = data.Data(cx[1].m, a, a + 8, fmt = str(bm))
        a = z.hi

def example():
    rv = []
    m1 = mem.Stackup((FILENAME1,), prefix=DIR)
    m3 = mem.ByteMem(lo=0x0000, hi=0x4000)

    cx = banked.BankedCPU(NPG, mycpu)
    for i in range(NPG):
        cx[i].m.map(m3, 0x0000, 0x4000, shared=True)
        cx[i].m.map(m1, 0x4000, 0x8000, offset=i * 0x4000)
        cx[i].m.map(m1, 0x8000, 0x10000, shared=True, offset=6 * 0x4000)
        rv.append(cx[i].m)

        romsum(cx[i], 0x4000, 0x8000)

    rv.append(m1)

    for b in cx.bank:
        print(b, b.m)
        y = data.Const(b.m, 0x4000, 0x4001)
        y.lcmt = "Bank#"
        y = data.Const(b.m, 0x4001, 0x4002)
        y.lcmt = "Checksum Adjust"

    lcd_config(cx)

    for p, a, t in SYMBOLS:
        cx[p].m.set_label(a, t)

    cx[0].vectors()

    for a, b in (
            (0xee5b, 0xee91),
            (0xef1f, 0xef41),
    ):
        for i in range(a, b, 2):
            y = data.Dataptr(cx[0].m, i, i + 2, cx[0].m.bu16(i))
            Txt(cx[0].m, y.dst, pfx=1, label=False)

    for p, a, b in (
            (1, 0x449a, 0x44aa),
    ):
        for i in range(a, b, 2):
            cx[p].codeptr(i)

    pgc(cx[0])
    pg0(cx[0])
    pg1(cx[1])
    pg2(cx[2])
    pg3(cx[3])
    pg4(cx[4])
    pg5(cx[5])

    # Probably mode-vectoring
    for p, a, v in (

        (0, 0x506e, 0x2213),
        (0, 0x4d99, 0x2217),

        (1, 0x4634, 0x2213),
        (1, 0x5114, 0x2215),

        (1, 0x516c, 0x2217),

        (2, 0x4c22, 0x2213),
        (2, 0x51a6, 0x2215),

        (2, 0x5204, 0x2217),

        (3, 0x4b5a, 0x2213),

        (3, 0x4f40, 0x2213),

        (3, 0x538c, 0x2213),

        (3, 0x5efb, 0x2211),

        (3, 0x6118, 0x2211),

        (3, 0x5b8a, 0x2211),

        (4, 0x6acb, 0x2213),
        (4, 0x6f5b, 0x2215),
        (4, 0x6fb9, 0x2217),

        (5, 0x65b5, 0x2213),
        (5, 0x42b7, 0x2217),

        (0, 0x8f6a, 0x2213),

        (0, 0xa45b, 0x2211),

        (0, 0xa5c9, 0x2211),

        (0, 0xf212, 0x2211),

        (0, 0xf42c, 0x2211),

        (0, 0xfa0d, 0x2211),

    ):
        cx[p].m.set_block_comment(a, "via 0x%04x" % v)
        cx[p].disass(a)

    Menu(cx[0], 0x4257)
    Menu(cx[1], 0x437d)
    Menu(cx[2], 0x416b)
    Menu(cx[2], 0x4234)
    Menu(cx[3], 0x4292)
    Menu(cx[4], 0x4172)
    Menu(cx[5], 0x4144)

    ads = set()
    while True:
        l = []
        for p in range(NPG):
            for a, b in cx[p].m.gaps():
                try:
                    if not cx[p].m[a]:
                        a += 1
                    #print("G", p, "0x%x" % a, "0x%x" % b, "0x%04x" % cx[p].m.bu16(a))
                    if cx[p].m[a] in (0xcc, 0xfc,) and cx[p].m[a + 3] == 0x17:
                        j = (p, a)
                        if j not in ads:
                            l.append(j)
                            ads.add(j)
                except mem.MemError:
                    pass
        if not l:
            break
        for p, a in l:
            cx[p].disass(a)
            cx[p].m.set_line_comment(a, "AUTODISC")

    return NAME, rv

if __name__ == '__main__':
    listing.Example(example, ncol=8, pil=False)
