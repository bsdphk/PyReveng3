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

IOC_RAM_EXPORTS = {
    0x0000fc07: "MACHINE_TYPE",
    0x0000fc64: "CLIENT_IP_ADDRESS",
    0x0000fc68: "SERVER_IP_ADDRESS",
    0x0000fc6c: "TAPE_DRIVE_CONFIG",
    0x0000fc70: "SERVER_UDP_PORT",
    0x00078800: "EEPROM_WRITER_TRAMPOLINE",
}

IOC_EEPROM_PART1_EXPORTS = {
    0x8000000c: "IOC_EEPROM_PART1_REPORT_OK",
    0x80000014: "IOC_EEPROM_PART1_EXPORT_0014",
    0x80000018: "IOC_EEPROM_PART1_OUTSTR_PRESERVE_D0(A0)",
    0x8000001c: "IOC_EEPROM_PART1_OUTSTR_INLINE",
}

IOC_EEPROM_PART2_EXPORTS = {
    0x80002000: "IOC_EEPROM_PART2_CPU_RESET",
    0x80002004: "IOC_EEPROM_PART2_EXPORT_2004",
    0x80002008: "IOC_EEPROM_PART2_EXPORT_2008",
    0x8000200c: "IOC_EEPROM_PART2_RESTART_MACHINE()",
    0x80002010: "IOC_EEPROM_PART2_EXPORT_2010",
    0x80002014: "IOC_EEPROM_PART2_IN_CHAR()",
    0x80002018: "IOC_EEPROM_PART2_OUT_CHAR(D0)",
    0x8000201c: "IOC_EEPROM_PART2_OUT_HEX_DIGIT(D0)",
    0x80002020: "IOC_EEPROM_PART2_OUT_DIGIT(D0)",
    0x80002024: "IOC_EEPROM_PART2_OUT_NUMBER(D0)",
    0x80002028: "IOC_EEPROM_PART2_OUT_TEXT()",
    0x8000202c: "IOC_EEPROM_PART2_OUT_TEXT(A3)",
    0x80002030: "IOC_EEPROM_PART2_OUT_CRNL()",
    0x80002034: "IOC_EEPROM_PART2_ASK(A3=PROMPT->A0)",
    0x80002038: "IOC_EEPROM_PART2_ASK_YES_OR_NO(A2=PROMPT)",
    0x8000203c: "IOC_EEPROM_PART2_ATOI(*A0->D0)",
    0x80002040: "IOC_EEPROM_PART2_OUT_MAC_ADDRESS(A0)",
    0x80002044: "IOC_EEPROM_PART2_OUT_CLIENT_IP()",
    0x80002048: "IOC_EEPROM_PART2_OUT_SERVER_IP()",
    0x8000204c: "IOC_EEPROM_PART2_EXPORT_BREAK_KEY_MENU()",
    0x80002050: "IOC_EEPROM_PART2_EXPORT_2050",
    0x80002054: "IOC_EEPROM_PART2_EXPORT_2054",
    0x80002058: "IOC_EEPROM_PART2_EXPORT_2058",
    0x8000205c: "IOC_EEPROM_PART2_DOWNLOAD_RESHA_EEPROM_SECTION",
    0x80002060: "IOC_EEPROM_PART2_EXPORT_2060",
    0x80002064: "IOC_EEPROM_PART2_EXPORT_2064",
    0x80002068: "IOC_EEPROM_PART2_CALL_RESHA",
    0x8000206c: "IOC_EEPROM_PART2_EXPORT_206c",
    0x80002070: "IOC_EEPROM_PART2_EEPROM_WRITE(A0,D0)",
}

IOC_EEPROM_PART3_EXPORTS = {
    0x80004000: "IOC_EEPROM_PART3_EXPORT_4000",
}

IOC_EEPROM_PART4_EXPORTS = {
    0x80007e0b: "PHONE_NUMBER",
    0x80007f60: "EE_CLIENT_IP_NUMBER",
    0x80007f64: "EE_SERVER_IP_NUMBER",
    0x80007f68: "EE_TAPE_DRIVE_CONFIG",
    0x80007f6d: "EE_SERVER_UDP_PORT",
    0x80007f6e: "NV_MACHINE_TYPE",
}

RESHA_PROGRAMS = {
    0x0100: "Selftest VMEGEM",
    0x0200: "Selftest Diag Modem",
    0x0300: "Selftest LANCE",
    0x0400: "Selftest Disk SCSI",
    0x0500: "Selftest Tape SCSI",
    0x0600: "Selftext SCSI loop-back",
    0x0101: "Network Boot",
    0x0201: "",
    0x0301: "Crash Dump",
    0x0401: "",
    0x0102: "Disk Boot",
    0x0202: "",
    0x0103: "Tape Boot",
    #0x0203: "9-Track Tape Boot",
}

def add_symbols(asp):
    ''' Add all exported symbols '''
    for a, b in IOC_RAM_EXPORTS.items():
        asp.set_label(a, b)
    for a, b in IOC_EEPROM_PART1_EXPORTS.items():
        asp.set_label(a, b)
    for a, b in IOC_EEPROM_PART2_EXPORTS.items():
        asp.set_label(a, b)
    for a, b in IOC_EEPROM_PART3_EXPORTS.items():
        asp.set_label(a, b)
    for a, b in IOC_EEPROM_PART4_EXPORTS.items():
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
        elif f.to in (
            0x80000018,
        ):
            if asp.bu16(ins.lo - 6) == 0x41f9:
                a = asp.bu32(ins.lo - 4)
                y = data.Txt(asp, a, splitnl=True)
        elif f.to in (
            0x80002034,
        ):
            if asp.bu16(ins.lo - 6) == 0x47f9:
                a = asp.bu32(ins.lo - 4)
                y = data.Txt(asp, a, splitnl=True)
        elif f.to in (
            0x8000001c,
            0x800000e2
        ):
            y = data.Txt(asp, ins.hi, label=False, align=2, splitnl=True)
            ins.dstadr = y.hi
            ins.flow_out.pop(-1)
            ins += code.Jump(cond=True, to=ins.dstadr)
        elif f.to in (
            0x80002068,
        ):
            if asp.bu16(ins.lo - 4) == 0x303c:
                a = asp.bu16(ins.lo - 2)
                t = RESHA_PROGRAMS.get(a)
                if t:
                    asp.set_line_comment(ins.lo - 4, t)

def add_flow_check(cx):
    ''' Add flow-check to capture inline strings '''
    cx.flow_check.append(flow_check)
