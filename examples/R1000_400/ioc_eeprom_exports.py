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
    0x80002014: "IOC_EEPROM_PART2_EXPORT_INCHAR()",
    0x80002018: "IOC_EEPROM_PART2_EXPORT_OUTCHAR(D0)",
    0x80002028: "IOC_EEPROM_PART2_EXPORT_OUTTEXT()",
    0x8000202c: "IOC_EEPROM_PART2_EXPORT_OUTTEXT(A3)",
    0x80002030: "IOC_EEPROM_PART2_EXPORT_OUTCRNL()",
    0x8000203c: "IOC_EEPROM_PART2_EXPORT_203c",
    0x8000204c: "IOC_EEPROM_PART2_EXPORT_BREAK_KEY_MENU()",
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
