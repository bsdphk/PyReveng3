#!/usr/bin/env python
#
# Copyright (c) 2012-2021 Poul-Henning Kamp <phk@phk.freebsd.dk>
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

'''
   Entrypoints exported from IOC eeprom
   ------------------------------------
'''

from pyreveng import data, code

IOC_EEPROM_PART1_EXPORTS = {
}

IOC_EEPROM_PART2_EXPORTS = {
    0x80002004: "IOC_EEPROM_PART2_EXPORT_2004",
    0x80002008: "IOC_EEPROM_PART2_EXPORT_2008",
    0x8000200c: "IOC_EEPROM_PART2_EXPORT_200c",
    0x80002010: "IOC_EEPROM_PART2_EXPORT_2010",
    0x80002014: "IOC_EEPROM_PART2_EXPORT_2014",
    0x80002018: "IOC_EEPROM_PART2_EXPORT_2018",
    0x80002028: "IOC_EEPROM_PART2_EXPORT_2028",
    0x8000202c: "IOC_EEPROM_PART2_EXPORT_202c",
    0x80002030: "IOC_EEPROM_PART2_EXPORT_2030",
    0x8000203c: "IOC_EEPROM_PART2_EXPORT_203c",
    0x80002050: "IOC_EEPROM_PART2_EXPORT_2050",
    0x8000205c: "IOC_EEPROM_PART2_EXPORT_205c",
    0x80002060: "IOC_EEPROM_PART2_EXPORT_2060",
    0x80002064: "IOC_EEPROM_PART2_EXPORT_2064",
    0x80002068: "IOC_EEPROM_PART2_EXPORT_2068",
}

IOC_EEPROM_PART3_EXPORTS = {
    0x80004000: "IOC_EEPROM_PART3_EXPORT_4000",
}

def add_symbols(asp):
    ''' Add all exported symbols '''
    for a, b in IOC_EEPROM_PART2_EXPORTS.items():
        asp.set_label(a, b)
    for a, b in IOC_EEPROM_PART3_EXPORTS.items():
        asp.set_label(a, b)

def add_exports(asp, exports):
    ''' Mark up exported entrypoints '''
    for a, b in exports.items():
        asp.set_block_comment(a, "Exported Entrypoint")
        for i in asp.find(a):
            j = getattr(i, "dstadr", None)
            if j:
                asp.set_label(j, "_" + b)

def flow_check(asp, ins):
    ''' Flow-check to capture inline strings '''
    if ins.lo in (
        0x80002010,
        0x80002028,
    ):
        return
    for f in ins.flow_out:
        if f.to in (
           0x80002010,
           0x80002028,
           0x80002aa8
        ):
            y = data.Txt(asp, ins.hi, label=False, align=2, splitnl=True)
            ins.dstadr = y.hi
            ins.flow_out.pop(-1)
            ins += code.Jump(cond=True, to=ins.dstadr)

def add_flow_check(cx):
    ''' Add flow-check to capture inline strings '''
    cx.flow_check.append(flow_check)

"""

# Symbols in EEPROM used in KERNEL, FS etc.
EEPROM_EXPORT_SYMBOLS = {
    0x80002008: "EEPROM_EXPORT_2008",
    0x8000200c: "EEPROM_EXPORT_200c",
    0x80002010: "EEPROM_EXPORT_2010",
    0x8000202c: "EEPROM_EXPORT_202c",
    0x8000203c: "EEPROM_EXPORT_203c",
    0x8000205c: "EEPROM_EXPORT_205c",
    0x80002060: "EEPROM_EXPORT_2060",
    0x80002064: "EEPROM_EXPORT_2064",
    0x80002068: "EEPROM_EXPORT_2068",
    0x8000206c: "EEPROM_EXPORT_206c",
}

IOC_SYMBOLS = {
    0x8000000c: "REPORT_OK",
    0x80000010: "TEST_FAILED",
    0x80000014: "IOC_14_XXX",
    0x80000018: "iOUTSTR_PRESERVE_D0(A0)",
    0x8000001c: "OUTSTR_INLINE_CONTINUE()",
    0x80000020: "IOC_20_XXX",
    0x80000088: "_TEST_FAILED",
    0x800000d8: "OUTSTR_PRESERVE_D0(A0)",
    0x800000f8: "OUTSTR_SMASH_D0(A0)",
    0x80000142: "OUTSTR_OK()",
    0x8000014c: "OUTSTR_CRNL()",
    0x8000015e: "DELAY(D0)",
    0x8000016c: "CHECKSUM_FUNC",
    0x800001e4: "CHECKSUM_EEPROM",
    0x80002018: "OUT_CHAR(D0)",
    0x80002028: "OUT_STRING_INLINE()",
    0x80002a34: "ASK_YES_NO()",
}

# Calls into KERNEL through A-Line vectors in FS
KERNCALLS = {
    0x10: "Panic",
}

def kerncall_name(a):
    ''' Name of kerncall by vector number '''
    if 0x20 <= a:
        return "KERNCALL_%02x_UNIMPL" % a
    t = KERNCALLS.get(a)
    if t:
        return "KERNCALL_%02x_" % a + t
    return "KERNCALL_%02x" % a

FSCALLS = {
    0x10284: "string_lit2something",    # ref: DBUSULOAD.M200
    0x10384: "read_from_file",          # ref: DBUSULOAD.M200
    0x103d8: "flush_console?",          # ref: DBUSULOAD.M200
    0x1056e: "open_file",               # ref: BOOTINFO.M200
}

def fscall_name(a):
    ''' Name of fscall by address '''
    if 0x10200 <= a <= 0x10280:
        return kerncall_name((a - 0x10200) >> 1)
    t = FSCALLS.get(a)
    if t:
        return "FSCALL_%02x_" % a + t
    return "FSCALL_%02x" % a

def add_m200_symbols(cx):
    ''' Add symbols for .M200 binaries '''
    for a in range(0x10200, 0x10280, 2):
        cx.m.set_label(a, fs_syscall_name(a))
    for a in range(0x10280, 0x10460, 4):
        cx.m.set_label(a, fs_syscall_name(a))
    for a in range(0x10460, 0x1061c, 6):
        cx.m.set_label(a, fs_syscall_name(a))

def ioc_eeprom_flow_check(asp, ins):
    if ins.lo in (
        0x8000001c, 0x80002028,
    ):
        return
    for f in ins.flow_out:
        print("FC", f.to)
        if f.to in (
            0x8000001c,
            0x80002010,
            0x80002028,
            0x800000e2,
            0x80002aa8
        ):
            y = data.Txt(asp, ins.hi, label=False, align=2, splitnl=True)
            ins.dstadr = y.hi
            ins.flow_out = []
            ins += code.Jump(cond=True, to=ins.dstadr)
        elif f.to in (0x80001010, 0x80001122,):
            if asp.bu16(ins.lo - 6) == 0x43f9:
                a = asp.bu32(ins.lo - 4)
                y = data.Txt(asp, a, splitnl=True)
        elif f.to in (0x8000298e, ):
            if asp.bu16(ins.lo - 4) == 0x47fa:
                a = ins.lo - 2 + asp.bs16(ins.lo - 2)
                y = data.Txt(asp, a, splitnl=True)
            elif asp.bu16(ins.lo - 6) == 0x47f9:
                a = asp.bu32(ins.lo - 4)
                y = data.Txt(asp, a, splitnl=True)

def ioc_symbols(cx):
    ''' Add IOC labels to cx '''
    for a, b in IOC_SYMBOLS.items():
        cx.m.set_label(a, b)

"""
