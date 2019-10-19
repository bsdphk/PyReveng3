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

'''HP8568A Spectrum Analyzer
'''

from pyreveng import mem, listing, data, code, assy
import pyreveng.cpu.m68000 as m68000
import pyreveng.cpu.hp85662a as hp85662a

import hp856x_cmds

NAME = "HP8568B"

SYMBOLS = {
    0x193da: "OLDCMDS",
    0x194b2: "KEYTAB",
    0x1951e: "IMEDBITS",
    0x1952c: "SFLGVAL",
    0x18c3a: "MNETABLE",
    0x0693c: "MSG_ADR_X_Y",
    0x6b84: "G_CTRL",
    0x6ba8: "G_CENTER",
    0x6bcc: "G_MARKER",
    0x6be2: "G_DSP_LINE",
    0x6bf8: "G_GRATICULE",
    0x6c4c: "G_HP_LOGO",
    0x6c5e: "G_ACT_FUNC",
    0x0e3be: "UNITS",
    0x4fac: "SCANTAB",
    0x19826: "PFXSCALE",
    0x009b8: "RESET",
    0x00c2e: "SELFTEST",
    0x00d7a: "CPUTEST_FAIL",
    0x00e9a: "epromsize",
    0x00ef2: "ramaddress",
    0x00e9e: "ROMSUM",
    0x00ec0: "ROMTEST",
    0x01ae2: "BCD_FMT(BCD, PTR)",
    0x01b34: "BCD_ABS(BCD)",
    0x01b38: "BCD_NEG(BCD)",
    0x01be6: "BCD_CMP(R01,R23)",
    0x01bea: "BCD_CMP(R23,R01)",
    0x01c00: "stk_64",
    0x01c14: "rel_64",
    0x01c28: "abs_64",
    0x01c3c: "loc_64",
    0x01b48: "BCD_NEG8(&A0)",
    0x01b62: "BCD_NEG(D23)",
    0x01b72: "BCD_ADD8(&A0,&A1)",
    0x01c60: "BCD_ADD(D01, D23)",
    0x01c98: "BCD_SUBR(D23, D01(order?)",
    0x01c9c: "BCD_SUB(D01, D23(order?)",
    0x01cb0: "BCD_SUB8(&A0,&A1)",
    0x0214c: "BCD_MUL5(D01)",
    0x0217e: "BCD_MUL3(D01)",
    0x0218c: "BCD_MUL6(D01)",
    0x021be: "BCD_MUL8(D01)",
    0x021c0: "BCD_MUL4(D01)",
    0x021c4: "BCD_MUL2(D01)",
    0x021f6: "BCD_DIV2(D01)",
    0x02224: "BCD_LD(D0.W)",
    0x0222c: "BCD_LD(D0.L)",
    0x023ec: "FD_ABS(R2+R3)",
    0x0287e: "rel_32",
    0x02892: "abs_32",
    0x028a4: "loc_32",
    0x02f38: "SWITCH",
    0x0320e: "BZERO(PTR,INT)",
    0x033fc: "SHOW_CHAR",
    0x03412: "SHOW_SEMI",
    0x0341a: "SHOW_COMMA",
    0x03422: "SHOW_CRNL",
    0x03428: "SHOW_NL",
    0x03430: "SHOW_MINUS",
    0x03438: "SHOW_2CHAR",
    0x03498: "SHOW_INT",
    0x03932: "DISP_RD(INT ADR)",
    0x03958: "SHOW_TXT_AT(ADR,STR)",
    0x03906: "DISP_WR(INT ADR, INT DATA)",
    0x039b0: "SHOW_WORD(INT)",
    0x03c0a: "FREQ_CNT_SET_PERIOD(INT)",
    0x03c26: "FREQ_CNT_WAIT()",
    0x03c3a: "FREQ_CNT_10MHZ(INT)",
    0x06936: "REVISION",
    0x0693a: "MODEL",
    0x06a2c: "MSG_TXT",
    0x06ce0: "SHOW_TXT(STR)",
    0x06cf2: "SHOW_CRNL",
    0x06cfc: "SET_IF_LEDS(INT)",
    0x06d20: "SHOW_MSG",
    0x070be: "UPD_DETECTOR",
    0x07b4e: "FILL_DISPLAY",
    0x08164: "SHOW_CR[NL]",
    0x0940c: "EXEC(INT KEY)",
    0x0e39a: "VAR_HEAD",
    0x0ed54: "EXEC2(INT KEY)",
    0x0eddc: "SEARCH(NAMLEN.W, CHAIN.L, HASH.L, NAME.L)",
    0x0ee6a: "FIND_OLDCMD(INT)",
    0x0f72c: "NAME2TRACE",
    0x0a986: "CALIBRATING",
    0x0aa7a: "AUTOCAL",
    0x13092: "WHICH(PTR TABLE, STR KEY, INT N)",
    0x14158: "TRACE_MATH(LONG, INT, STR, STR, STR)",
    0x17dce: "SHOW_COMMA",
    0x17e9e: "PL_MOVE",
    0x17eac: "PL_LINE",
    #cx.m.set_label(0x18d24, "MNEM",
    #cx.m.set_label(0x195c4, "PARMTYPE",
    #cx.m.set_label(0x196b6, "PRCADRS",
    #cx.m.set_label(0xffff4000, "PIT_PGCR",
    #cx.m.set_label(0xffff4002, "PIT_PSRR",
    #cx.m.set_label(0xffff4004, "PIT_PADDR",
    #cx.m.set_label(0xffff4006, "PIT_PBDDR",
    #cx.m.set_label(0xffff4008, "PIT_PCDDR",
    #cx.m.set_label(0xffff4010, "PIT_PADR",
    #cx.m.set_label(0xffff4012, "PIT_PBDR",
    0xffffa6d2: "ram_var_hash",
    0xffffaa2c: "ram_center_freq",
    0xffffaa34: "ram_freq_span",
    0xffffaa3c: "ram_rf_fp_leds",
    0xffffaa3e: "ram_if_fp_leds",
    0xffffaaf8: "ram_kbd_row",
    0xffffabd2: "func_ptr+a6+a7",
    0xffffbfe2: "ram_hpib_address",
    0xffffbfe3: "ram_not_hpib_address",

    # BIO/BOTTOM/RF
    ###############
    0xffffc000: "rf_50vto_lo_dac",
    0xffffc002: "rf_50vto_hi_dac",
    0xffffc006: "rf_yig_dac",
    0xffffc008: "rf_scan_atten_vto",
    0xffffc00a: "rf_scantime",
    0xffffc00c: "rf_yig_lock_scan",
    0xffffc00e: "rf_scan_mode",

    # A12
    #####
    0xffffc010: "rf_fp_leds",
    0xffffc012: "rf_kbd_row",
    0xffffc014: "rf_kbd_col",
    0xffffc016: "rf_rpg",
    0xffffc018: "rf_srq_resets",
    0xffffc01a: "rf_phase_lock",
    0xffffc01c: "rf_245_lock",
    0xffffc01e: "rf_attn",

    # A15
    #####
    0xffffc020: "dbus_test_0",
    0xffffc022: "dbus_test_2",
    0xffffc025: "dbus_test_5",

    # A17
    #####
    0xffffc028: "rf_freqcnt_ctrl",
    0xffffc02a: "rf_freqcnt_msb",
    0xffffc02c: "rf_freqcnt_lsb",
    0xffffc030: "rf_inputs_atten_20",
    0xffffc032: "rf_vunit_atten_30",
    0xffffc034: "rf_atten_40",
    0xffffc034: "rf_atten_50",
    0xffffc034: "rf_atten_60",
    0xffffc034: "rf_atten_70",

    # TIO/TOP/IF
    ############
    0xffffc040: "display_address",
    0xffffc042: "display_rd_store",
    0xffffc044: "display_wr_store",
    0xffffc046: "display_wr_offset",
    0xffffc048: "display_control",
    0xffffc04a: "display_rd_scan",
    0xffffc04c: "display_wr_marker",
    0xffffc04e: "display_wr_scan",

    # SWEEP
    #######
    0xffffc064: "if_sweep_src_trig",
    0xffffc066: "if_sweep_time",
    0xffffc068: "if_scale_gain",
    0xffffc06a: "if_bw_fine",
    0xffffc06c: "if_fp_leds",

    # HPIBSW
    0xffffc0e1: "adrsw_srq_display_ready",

    0xffffc0e5: "latr_test",
}

#
# Patent
# 4,244,024  Object code listing for 'A' CPU.
#	     IO-map, display microcode
#
# 4,253,152  Looks identical to 4,244,024, different pagination
#
# 4,257,104  Looks identical to 4,253,152, different pagination
#
# 4.264,958  Refers to 4,253,152 for "computer printout"
#
# 4,649,496  Wheelgol excerpts (typeset):
#	     Appendix I:  mkrsave, nxtpk, mkpk, mkasrch, slft, srgt,
#			  setavoid, newmrkrs,
#	     Appendix II: sertrcad, loadtrc, mkrtrc, mkrad, mkrspot,
#			  mkrdout, mkron, doeos, domrkr, newcmd,
#			  oldcmd, trcadrs, dostring, dosoftkey ...
#
# 4,660,150  Wheelgol excerpts (tty):
#	     same as 4,649,496 ?
#######################################################################
# 4,244,024
#	pg 248 ln 2363 -> 0x7366
#	pg 262 ln 3700 -> 0x4fac
#	pg 272 ln 4631 -> 0x54b0
#	pg 280 ln 5392 -> 0x7e86

class myins(m68000.m68000_ins):
    pass

class mycpu(m68000.m68000):
    def __init__(self):
        super().__init__()

    def macro(self, nm, l):
        s = nm + " - "
        for i in l:
            if i == " ":
                continue
            j = int(i, 16)
            s += "|%d %d %d %d" % (
                (j >> 3) & 1,
                (j >> 2) & 1,
                (j >> 1) & 1,
                (j >> 0) & 1
            )
        s += "|\n"
        self.add_ins(s, myins)
#######################################################################

KEYBOARD = (
    # Row, Column, Text
    (0, 0, "HZ_UV_USEC"),
    (0, 3, "MHZ_DBM_SEC"),
    (0, 5, "BACK_SPACE"),
    (0, 6, "KHZ_MV_MSEC"),

    (1, 0, "SAVE"),
    (1, 1, "RECALL"),
    (1, 2, "HOLD"),
    (1, 4, "0_1_5_GHZ"),
    (1, 6, "POINT"),
    (1, 7, "GHZ_DBM_DB"),

    (2, 0, "DIG_0"),
    (2, 1, "DIG_1"),
    (2, 2, "DIG_2"),
    (2, 3, "DIG_3"),
    (2, 4, "DIG_4"),
    (2, 5, "DIG_5"),
    (2, 6, "DIG_6"),
    (2, 7, "DIG_7"),

    (3, 0, "DIG_8"),
    (3, 1, "DIG_9"),
    (3, 4, "INPUT_1"),
    (3, 5, "FREQ_COUNT"),
    (3, 6, "INPUT_1"),

    (4, 1, "AUTO_RES_BW"),
    (4, 2, "AUTO_VIDEO_BW"),
    (4, 3, "AUTO_SWEEP_TIME"),
    (4, 4, "AUTO_ATTEN"),
    (4, 5, "AUTO_CF_STEP"),
    (4, 6, "RES_BW"),
    (4, 7, "VIDEO_BW"),

    (5, 0, "SWEEP_TIME"),
    (5, 1, "ATTEN"),
    (5, 2, "CF_STEP"),
    (5, 3, "PEAK_SEARCH"),
    (5, 4, "MARKER_OFF"),
    (5, 5, "MARKER_NORMAL"),
    (5, 6, "MARKER_CF"),
    (5, 7, "MARKER_DELTA"),

    (6, 0, "ZOOM"),
    (6, 1, "MKR_DELTA_STP_SIZE"),
    (6, 2, "MKR_REF_LVL"),
    (6, 3, "SIGNAL_TRACK"),
    (6, 4, "DOWN"),
    (6, 5, "UP"),
    (6, 6, "CENTER_FREQ"),
    (6, 7, "FREQ_SPAN"),

    (7, 0, "START_FREQ"),
    (7, 1, "STOP_FREQ"),
    (7, 2, "REF_LEVEL"),

    (8, 0, "NORMAL"),
    (8, 1, "CLEAR_A"),
    (8, 2, "MAX_A"),
    (8, 3, "OFF_A_B"),
    (8, 4, "VIEW_A"),
    (8, 5, "BLANK_A"),
    (8, 6, "A_B"),
    (8, 7, "CLEAR_B"),

    (9, 0, "MAX_B"),
    (9, 1, "A_EX_B"),
    (9, 2, "VIEW_B"),
    (9, 3, "BLANK_B"),
    (9, 4, "B-DL-B"),
    (9, 5, "LINE_OFF"),
    (9, 6, "LINE_ENTER"),
    (9, 7, "THRSH_OFF"),

    (10, 0, "THRSH_ENTER"),
    (10, 1, "ENTER_DB"),
    (10, 2, "LIN"),
    (10, 3, "SHIFT"),
    (10, 4, "CONT"),
    (10, 5, "SINGLE"),
    (10, 6, "TRIG_FREE_RUN"),
    (10, 7, "TRIG_LINE"),

    (11, 0, "TRIG_EXT"),
    (11, 1, "TRIG_VIDEO"),
    (11, 2, "LOWER_LEFT"),
    (11, 4, "LOWER_RIGHT"),
)

KEYNOS = {}
for r, c, t in KEYBOARD:
    n = 0x20 + r * 8 + c
    KEYNOS[n] = t



###############################################################
# Functions taking arguments after call instruction

post_arg = {
    0x1bc8: ("BCD_CMP", "brel", "D01"),
    0x1bcc: ("BCD_CMP", "babs", "D01"),
    0x1bd0: ("BCD_CMP", "bA6rel", "D01"),
    0x1bdc: ("BCD_CMP", "D01", "babs"),
    0x1be0: ("BCD_CMP", "D01", "bA6rel"),

    0x1c52: ("BCD_ADD", "brel", "D01"),
    0x1c56: ("BCD_ADD", "babs", "D01"),
    0x1c5a: ("BCD_ADD", "bA6rel", "D01"),
    0x1c5e: ("BCD_ADD", "stk", "D01"),

    0x1c76: ("BCD_SUB", "brel", "D01"),
    0x1c7a: ("BCD_SUB", "babs", "D01"),
    0x1c7e: ("BCD_SUB", "bA6rel", "D01"),

    0x1c88: ("BCD_SUB", "brel", "D01"),
    0x1c8c: ("BCD_SUB", "babs", "D01"),
    0x1c90: ("BCD_SUB", "bA6rel", "D01"),

    0x1ccc: ("", "dabs", "FPXXX"),
    0x2218: ("BCD_LD_D01", "bcd"),
    0x223c: ("BCD_LD_D23", "bcd"),
    0x238e: ("", "drel", "FPXXX"),
    0x239a: ("", "dA6rel", "FPXXX"),
    0x23f6: ("", "drel", "FPXXX"),
    0x2402: ("", "D0+D1", "dA6rel"),
    0x24ac: ("", "drel", "FPXXX"),
    0x24b8: ("", "dA6rel", "FPXXX"),
    0x24c4: ("", "drel", "FPXXX"),
    0x25b0: ("", "drel", "FPXXX"),
    0x25c8: ("", "drel", "FPXXX"),
    0x25fa: ("", "dA6rel", "FPXXX"),
    0x27ee: ("", "lrel", "FPXXX"),

    0x2862: ("", "lrel", "LFXXX"),
    0x28c2: ("", "lrel", "LFXXX"),
    0x28ce: ("", "fabs", "LFXXX"),
    0x297c: ("", "fA6rel", "LFXXX"),
    0x2982: ("", "fabs", "LFXXX"),
    0x2988: ("", "frel", "FFXXX"),
    0x29ba: ("", "fA6rel", "LFXXX"),
    0x29c6: ("", "frel", "FFXXX"),
    0x29ea: ("", "fA6rel", "LFXXX"),
    0x29f6: ("", "frel", "FFXXX"),
    0x2a02: ("", "fA6rel", "LFXXX"),
    0x2a0e: ("", "frel", "FFXXX"),
    0x2a34: ("", "frel", "FFXXX"),
    0x2a6e: ("", "frel", "FFXXX"),
    0x2b08: ("", "fA6rel", "LFXXX"),
    0x2b14: ("", "frel", "FFXXX"),
    0x2b2c: ("", "frel", "FFXXX"),
}

def flow_post_arg(asp, ins):
    z = post_arg.get(ins.dstadr)
    if z is None:
        return
    ins.flow_out.pop(-1)
    if len(z) <= 1:
        a = data.Pstruct(asp, ins.hi, ">h", "%d", ".INFIX").hi
        ins += code.Jump(to=a)
        return
    l = []
    for i in z[1:]:
        if i[1:] == "A6rel":
            r = asp.bs16(ins.hi)
            ins.hi += 2
            if r < 0:
                l.append("(A6-0x%x)" % -r)
            else:
                l.append("(A6+0x%x)" % r)
        elif i[1:] == "abs":
            r = asp.bu16(ins.hi)
            if r & 0x8000:
                r |= 0xffff0000
            ins.hi += 2
            l.append("0x%08x" % r)
        elif i == "drel":
            r = ins.hi + asp.bs16(ins.hi)
            ins.hi += 2
            ins.lcmt += " @0x%x\n" % r
            y = data_double(asp, r)
            l.append("%g" % y.data[0])
        elif i == "brel":
            r = ins.hi + asp.bs16(ins.hi)
            ins.hi += 2
            ins.lcmt += " @0x%x\n" % r
            y = data_bcd(asp, r);
            l.append("%x" % y.data[0])
        elif i == "lrel":
            r = ins.hi + asp.bs16(ins.hi)
            ins.hi += 2
            ins.lcmt += " @0x%x\n" % r
            if not asp.occupied(r):
                data.Pstruct(asp, r, ">L", "%d", ".LONG")
            l.append("%d" % asp.bu32(r))
        elif i == "frel":
            r = ins.hi + asp.bs16(ins.hi)
            ins.hi += 2
            ins.lcmt += " @0x%x\n" % r
            y = data_float(asp, r)
            l.append("%g" % y.val)
        elif i == "bcd":
            r = asp.bu16(ins.hi)
            # y = data.Pstruct(asp, ins.hi, ">H", "%x", ".BCD")
            l.append("%04x" % r)
            ins.hi += 2
        else:
            l.append(i)
    ins.oper.append(assy.Arg_verbatim("(" + ",".join(l) + ")"))
    ins += code.Flow()

###############################################################

switches = {
    0x13624: {
        0: "ALL",
        1: "ONEOS",
        2: "ONSWP",
        3: "TRMATH",
    },
}

def flow_switch(asp, ins):
    if ins.dstadr != 0x2f38:
        return
    ins.flow_out.pop(0)
    ins += code.Flow(cond="?")
    asp.set_label(ins.hi, "break_%04x" % ins.lo)

    y = data.Const(asp, ins.lo - 2, ins.lo)
    ncase = asp.bu16(ins.lo - 2)
    y.typ = ".NCASE"
    y.fmt = "%d" % ncase
    cs = switches.get(ins.lo)
    if cs is None:
        cs = {}
    a = ins.lo - 2
    for i in range(ncase):
        a -= 2
        ct = cs.get(i)
        if ct is None:
            ct = "_%d" % i

        w = data.Const(asp, a, a + 2)
        z = asp.bs16(a)
        w.typ = ".CASE"
        w.fmt = "0x%x, %d" % (i, z)

        w.fmt += ", 0x%04x" % (ins.hi + z)
        ins += code.Jump(cond="0x%x" % i, to=ins.hi + z)
        if z < 0:
            asp.set_label(ins.hi + z, ".case_%04x_%s" % (ins.lo, ct))

###############################################################

class oldcmd(data.Data):
    def __init__(self, asp, lo, n):
        super().__init__(asp, lo, lo + 2)
        x, self.name, y = data.stringify(asp, self.lo, 2)

        self.key = asp[0x194b2 + n]
        self.imm = (asp[0x1951e + (n >> 3)] >> (n & 7)) & 1
        if not self.imm:
            self.svf1 = asp.bu16(0x1952c + self.key * 4)
            self.svf2 = asp.bu16(0x1952c + self.key * 4 + 2)
            if not self.svf2 in KEYNOS:
                KEYNOS[self.svf2] = "CMD_" + self.name

    def render(self):
        t = ".OLDCMD\t"
        t += "'" + self.name + "'"
        t += " imm=%x" % self.imm
        t += " key=%02x" % self.key
        if self.imm and self.key in KEYNOS:
            t += " ('" + KEYNOS[self.key] + "')"
        if not self.imm:
            t += " svf=0x%04x,0x%04x" % (self.svf1, self.svf2)
            t += " xxx=%02x" % (self.svf1 & 0x1e)
        return t

###############################################################

class params(data.Data):
    def __init__(self, cx, nm, i, j):
        self.nm = nm
        self.b = 0x195c4
        self.i = i
        self.j = j
        self.fi = cx.m[self.b + i]
        self.args = []
        for a in range(j):
            self.args.append(cx.m[self.b + i + 1 + a])
        super().__init__(cx.m, self.b + i, self.b + i + 1 + j)

        self.fp = 0x196b6 + self.fi * 4
        self.fa = cx.m.bu32(self.fp)
        cx.codeptr(self.fp)
        cx.m.set_label(self.fa, "F_" + nm + "(" + self.summ() + ")")

    def render(self):
        t = ".PARAM\t"
        t += "func=%d" % self.fi
        t += " call=%s" % self.nm
        t += "(" + self.summ() + ")"
        return t

    def summ(self):
        t = []
        for i in self.args:
            if i == 0x03:
                t.append("STR")
            elif i == 0x16:
                t.append("int")
            elif i == 0x18:
                t.append("INT")
            elif i == 0x19:
                t.append("REAL")
            else:
                t.append("0x%02x" % i)
        return ",".join(t)

    def funcidx(self):
        return self.fi


###############################################################

class mnem(data.Data):
    def __init__(self, cx, hi):
        lo = hi
        lo -= 2
        self.c = cx.m.bu16(lo)
        lo -= 2
        self.b = cx.m.bu16(lo)
        lo -= 2
        self.a = cx.m.bu16(lo)

        self.len = self.c & 0xfff
        self.type = self.c >> 12

        lo -= (self.len + 1) & 0xffe
        super().__init__(cx.m, lo, hi)

        self.compact = True

        _a, b, _c = data.stringify(cx.m, self.lo, self.len)
        self.string = b

        self.hash = 0
        for i in bytearray(self.string, 'ascii'):
            self.hash += i
        self.hash %= 13

        self.pp = None
        self.args = None

        if self.type == 3:
            self.pp = params(cx, self.string, self.b, self.a >> 8)
        if self.type == 1:
            if self.b not in KEYNOS:
                KEYNOS[self.b] = "CMD_" + self.string


    def render(self):
        t = ".MNEM\t"
        t += "0x%04x" % self.a
        t += ", 0x%04x" % self.b
        t += ", 0x%x" % self.type
        t += ", len=0x%03x" % self.len
        t += ", hash=%2d" % self.hash
        t += ", '" + self.string + "'"
        return t

###############################################################

DATA = {}

def data_double(asp, a):
    y = DATA.get(a)
    if not y:
        y = data.Pstruct(asp, a, ">d", "%g", ".DOUBLE")
        y.val = y.data[0]
        DATA[a] = y
    return y

def data_float(asp, a):
    y = DATA.get(a)
    if not y:
        y = data.Data(asp, a, a + 4)
        x = asp.bu32(a)
        e = x & 0xff
        if e & 0x80:
            e -= 0x100
        m = x >> 8
        s = m >> 23
        m &= 0x7fffff
        y.val = m * (2.0 ** (e - 22.0))
        if s:
            y.val *= -1
        y.fmt = ".FLOAT\t%g" % y.val
        y.lcmt = "s=%d m=0x%06x e=%d" % (s, m, e)
        DATA[a] = y
    return y

def data_bcd(asp, a):
    y = DATA.get(a)
    if not y:
        y = data.Pstruct(asp, a, ">Q", "%016x", ".BCD")
        DATA[a] = y
    return y

#######################################################################

def example():
    m = mem.Stackup(
        (
            ("85680-80115.BIN", "85680-80116.BIN"),
            ("85680-80113.BIN", "85680-80114.BIN"),
        ),
        nextto=__file__
    )

    # Checum EPROMS
    # See 00e9e/ROMSUM
    s = [0xff, 0xff, 0xff, 0xff]
    for a in range(32768):
        s[0] += m[a * 2]
        s[1] += m[a * 2 + 1]
        s[2] += m[a * 2 + 65536]
        s[3] += m[a * 2 + 65536 + 1]
    for i in s:
        assert i & 0xff == 0

    cx = mycpu()
    cx.m.map(m, 0)
    cx.macro("DISPLAY_READY()", "0838 0007 c0e1 66f8")
    cx.flow_check.append(flow_post_arg)

    for a, b in SYMBOLS.items():
        cx.m.set_label(a, b)

    # Where ?
    # y = data.Const(cx.m, 0xfffe, 0x10000)
    # cx.m.set_label(y.lo, "eprom_lo_chksum")
    y = data.Const(cx.m, 0x19854, 0x19856)
    cx.m.set_label(y.lo, "eprom_hi_chksum")

    for i in post_arg:
        j = post_arg[i]
        if j and j[0] != "":
            cx.m.set_label(i, j[0])

    if True:
        for b, e in (
                (0x06936, 0x0693a),
                (0x06a2c, 0x06b84),
                (0x070ca, 0x070d6),
                (0x081ae, 0x081ba),
                (0x1357a, 0x1358a),
                (0x13e58, 0x13e70),
                (0x14960, 0x1497c),
                (0x14c94, 0x14cb4),
                (0x14f98, 0x14fa8),
                (0x15094, 0x150a4),
                (0x15140, 0x15150),
                (0x15e0e, 0x15e32),
                (0x172b8, 0x172c4),
                (0x17dbe, 0x17dce),
        ):
            for a in range(b, e, 4):
                x = cx.m.bu32(a)
                data.Dataptr(cx.m, a, a + 4, x)
                if not cx.m.occupied(x):
                    data.Txt(cx.m, x, pfx=1, align=2)

        data.Txt(cx.m, 0x15dfc, pfx=1, align=2)

    cx.flow_check.append(flow_switch)

    cx.vectors(hi=0xc0)

    if True:
        n = 0
        for a in range(0x193da, 0x194b2, 2):
            y = oldcmd(cx.m, a, n)
            n += 1
        # print("OLDCMDS %d" % ((0x194b2-0x193da)/2))

        for a in range(0x194b2, 0x1951e, 8):
            y = data.Const(cx.m, a, min(a + 8, 0x1951e), fmt="0x%02x")
        # print("KEYTAB %d" % ((0x1951e-0x194b2)/1))

        for a in range(0x1951e, 0x1952c, 8):
            y = data.Const(cx.m, a, min(a + 8, 0x1952c), fmt="0x%02x")
        # print("IMEDBITS %d" % ((0x1952c-0x1951e)/1))

        for a in range(0x1952c, 0x195c4, 16):
            y = data.Const(
                cx.m,
                a,
                min(a + 16, 0x195c4),
                "0x%08x",
                cx.m.bu32,
                4
            )
        # print("SFLGVAL %d" % ((0x195c4-0x1952c)/2))

    if True:
        a = 0x193a0
        while a > 0x18c3a:
            y = mnem(cx, a)
            x = cx.m.bu16(y.lo - 2)
            a = y.lo


    ###############################################################

    switches[0x09ae8] = {}
    switches[0x09d78] = {}
    switches[0x0a5de] = {}
    switches[0x0af5c] = {}
    switches[0x0b5ec] = {}
    switches[0x0bb4e] = {}
    switches[0x0bd5a] = {}
    switches[0x0bd6e] = {
        0: "KEYS_00_1f",
        1: "KEYS_20_3f",
        2: "KEYS_40_5f",
        3: "KEYS_60_7f",
        4: "KEYS_80_9f",
        5: "KEYS_a0_bf",
    }

    for n in KEYNOS:
        t = KEYNOS[n]
        # print("KEY_%02x" % n, t)
        sk = "KS%c" % n
        ksk = hp856x_cmds.cmds.get(sk)
        if ksk is not None and type(ksk) != str:
            ksk = ksk[1]
        if ksk is None:
            ksk = "==" + t
        if n < 0x20:
            switches[0x9ae8][n] = "KEY_%02x_" % n + t
        if n >= 0x20 and n < 0x30:
            switches[0x9d78][n - 0x20] = "KEY_%02x_" % n + t
        if n >= 0x40 and n < 0x60:
            switches[0xa5de][n - 0x41] = "KEY_%02x_" % n + t
            switches[0xaf5c][n - 0x41] = "KEY_S%02x_KS%c_" % (n, n) + ksk
        if n >= 0x60 and n < 0x80:
            switches[0xb5ec][n - 0x61] = "KEY_%02x_" % n + t
            switches[0xbb4e][n - 0x60] = "KEY_S%02x_KS%c_" % (n, n) + ksk
        if n >= 0xa0 and n <= 0xbf:
            switches[0xbd5a][n - 0xa0] = "KEY_%02x_" % n + t

    if True:
        for b, e in (
                (0x0e750, 0x0e778),
                (0x15ca4, 0x15cb4),
        ):
            for a in range(b, e, 8):
                data_double(cx.m, a)


    ###############################################################

    if True:

        cx.disass(0x2f38)

        #######################################################


        #######################################################


        for a in (
                0x0e2fa,
                0x0e308,
                0x0e318,
                0x12986,
                0x12988,
                0x1298c,
                0x12990,
                0x1694e,
                0x16954,
        ):
            y = data.Txt(cx.m, a, pfx=1, align=2)

        #######################################################

        data.Dataptr(cx.m, 0xe39a, 0xe39a + 4, cx.m.bu32(0xe39a))

        data.Const(cx.m, 0x2140, 0x2148, "%d", cx.m.bu64, 8)
        data.Const(cx.m, 0x2148, 0x214c, "%d", cx.m.bu32, 4)

        for a in (
                0x0645e,
                0x06476,
                0x0647e,
                0x0648a,
                0x06492,
                0x0649a,
                0x064a6,
                0x064be,
                0x0e2c4,
                0x0e2d4,
                0x0e2cc,
                0x0e32a,
                0x0e332,
                0x0e37c,
                0x0e384,
                0x128ca,
                0x15da0,
        ):
            if not cx.m.occupied(a):
                y = data_bcd(cx.m, a)
                cx.m.set_label(a, "BCD_%x" % y.data[0])



        #######################################################

        for a in range(0x693c, 0x6a2c, 6):
            data.Const(cx.m, a, a+6, "0x%04x", cx.m.bu16, 2)

        #######################################################

        a = 0x6b84

        dsp = hp85662a.hp85662a()
        while a < 0x6c98:
            x = cx.m.bs16(a)
            if x < 0:
                y = data.Data(cx.m, a, a + 2)
                y.fmt = ".DSPLOC\t0x%04x" % -x
                y.lcmt = "adr=%d" % -x
                dsp = hp85662a.hp85662a()
            else:
                y = dsp.disass(a, cx.m)
            a = y.hi

        #######################################################

        for a in range(0x0e3be, 0x0e3d4, 2):
            data.Txt(cx.m, a, a + 2, label=False)

        #######################################################
        # 0ee98  00 01 93 be
        # 0eeaa  00 01 93 da  |    |
        # 0ee8e  00 01 da ee  |    |
        #######################################################
        # Orphans ?

        if False:
            cx.disass(0x01b88)
            cx.disass(0x01b8e)
            cx.disass(0x01b94)
            cx.disass(0x01b9a)
            cx.disass(0x01b9e)
            cx.disass(0x01ba2)
            cx.disass(0x01ba8)
            cx.disass(0x01c76)
            cx.disass(0x01c82)
            cx.disass(0x01c90)
            cx.disass(0x01cd2)
            cx.disass(0x01d14)

            cx.disass(0x01578)
            cx.disass(0x01594)
            cx.disass(0x0171a)
            cx.disass(0x01906)
            cx.disass(0x02dee)
            cx.disass(0x02df4)
            cx.disass(0x03412)
            cx.disass(0x11e74)

        # from 0x2272
        cx.disass(0x2282)

        # filled in 0xffffabd2
        cx.disass(0x0ed98)

        cx.disass(0x0df5e) # Arg to 0x802
        cx.disass(0x3292)    # 0x3284

        #######################################################
        # pat 4,244,024 pg 262 lin 3700

        for a in range(0x4fac, 0x4fec, 2):
            y = data.Const(cx.m, a, a+2, "0x%04x", cx.m.bu16, 2)

        #######################################################

        y = data.Const(cx.m, 0x193a2, 0x193be, "%d", cx.m.bu16, 2)
        cx.m.set_label(y.lo, "HASHPTR2")
        y = data.Const(cx.m, 0x193be, 0x193da, "%d", cx.m.bu16, 2)
        cx.m.set_label(y.lo, "HASHPTR")



        #######################################################
        for a in range(0x19826, 0x19853, 1):
            y = data.Const(cx.m, a, a + 1, fmt="0x%02x")


    else:
        y = cx.disass(0xda1e)

        for i in y.__dict__:
            print("\t", i, y.__dict__[i])

    for i in cx.m:
        if i.tag != "m68000":
            continue
        if i.dstadr in (0x940c, 0xed54):
            y = list(cx.m.find(hi=i.lo))
            if len(y) != 1:
                continue
            y = y[0]
            if cx.m[y.lo] == 0x70:
                k = cx.m[y.lo + 1]
            elif cx.m.bu16(y.lo) == 0x103c:
                k = cx.m.bu16(y.lo + 2)
            else:
                continue
            if not k in KEYNOS:
                continue
            y.oper[0].txt = "#KEY_" + KEYNOS[k]

        if i.dstadr in (0xe4e8,):
            y = list(cx.m.find(hi=i.lo))
            if len(y) != 1:
                continue
            y = y[0]
            if y.mne != "PEA.L":
                continue
            z = data.Txt(cx.m, y.dstadr, pfx=1, align=2)
            y.lcmt = "'" + z.txt + "'"
        if i.dstadr in (0xe718, 0x3456, 0x6ce0):
            y = list(cx.m.find(hi=i.lo))
            if len(y) != 1:
                continue
            y = y[0]
            if cx.m.bu16(y.lo) != 0x203c:
                continue
            a = cx.m.bu32(y.lo + 2)
            z = data.Txt(cx.m, a, pfx=1, align=2)
            y.lcmt = "'" + z.txt + "'"
            if i.dstadr == 0xe718:
                w = list(cx.m.find(hi=y.lo))
                if len(w) != 1:
                    continue
                w = w[0]
                if w.mne != "PEA.L":
                    continue
                z = list(cx.m.find(w.dstadr))
                if not z:
                    z = [data.Txt(cx.m, w.dstadr, pfx=1, align=2)]
                w.lcmt = "'" + z[0].txt + "'"

    y = data.Const(cx.m, 0x693a, 0x693c, "%d", cx.m.bu16, 2)

    y = data.Const(cx.m, 0x00e9a, 0x00e9e, "%d", cx.m.bu32, 4)
    y = data.Const(cx.m, 0x00ef2, 0x00efe, "0x%08x", cx.m.bu32, 4)

    #cx.m.set_label(0x18d24, "MNEM")
    #cx.m.set_label(0x195c4, "PARMTYPE")
    #cx.m.set_label(0x196b6, "PRCADRS")


    # 0xffff0005
    # 0xffff0007
    # 0xffff0009
    # 0xffff0013
    # 0xffff0019
    # 0xffff0021
    # 0xffff0027
    # 0xffff0035

    #cx.m.set_label(0xffff4000, "PIT_PGCR")
    #cx.m.set_label(0xffff4002, "PIT_PSRR")
    #cx.m.set_label(0xffff4004, "PIT_PADDR")
    #cx.m.set_label(0xffff4006, "PIT_PBDDR")
    #cx.m.set_label(0xffff4008, "PIT_PCDDR")

    #cx.m.set_label(0xffff4010, "PIT_PADR")
    #cx.m.set_label(0xffff4012, "PIT_PBDR")

    # 0xffff8000

    # 0xffffa6ae = stack

    # I/O Decoding on A15
    #####################
    # 0x...00 BIO - BOTTOM/RF
    # 0x...20 DBCLK      #2
    # 0x...40 TIO - TOP/IF
    # 0x...64 LDBTEST    #7
    # 0x...80 LHPIB
    # 0x...a4 LDBTEST    #7
    # 0x...c0 LBUS
    # 0x...e0 HPIBSW     #1
    # 0x...e4 LATR       #5

    # HPIB
    ######
    # 0xffffc081
    # 0xffffc083
    # 0xffffc085
    # 0xffffc087
    # 0xffffc089
    # 0xffffc08b
    # 0xffffc08d
    # 0xffffc08f

    # LBUS
    ######

    # 0xffffc0e0 ?

    ###############################################################

    if False:
        for a in (
                0x01298,
                0x013a8,
                0x013d8,
                0x013de,
                0x013e4,
                0x01e12,
                0x01e94,
                0x0217e,
                0x0218c,
                0x02194,
                0x021a8,
                0x02268,
        ):
            # print("ORPHAN %x" % a)
            y = cx.disass(a)
            y.lcmt = "ORPHAN - "

        nondisc = {
            0x14ce:    0,
        }

        while True:
            l = []
            for b, e in cx.m.gaps():
                if b in nondisc:
                    continue
                if e - b < 2:
                    continue
                if cx.m.bu16(b) in (0x4eb8, 0x4e56):
                    l.append(b)
                elif cx.m[b] in (0x61,):
                    l.append(b)
            # print(l)
            for i in l:
                y = cx.disass(i)
                y.lcmt = "DISCOVER - "
            if l:
                break

    ###############################################################

    return NAME, (cx.m,)


if __name__ == '__main__':
    listing.Example(example)
