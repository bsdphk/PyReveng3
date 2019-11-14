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
#

'''Rational R1000/400 - IOC EEPROM
'''

from pyreveng import mem, listing, data, assy, discover
import pyreveng.cpu.m68020 as m68020

NAME = "R1000_400"

FILENAMES = ("IOC_EEPROM.bin", "RESHA_EEPROM.bin",)

SYMBOLS = {
    0x00070000: "RESHA_TEST_EEPROM_DEST",
    0x00072000: "RESHA_LANCE_EEPROM_DEST",
    0x00074000: "RESHA_DISK_EEPROM_DEST",
    0x000741b8: "err_scsi_error[0]",
    0x00074238: "err_scsi_error[1]",
    0x00074448: "err_scsi_error[1]",
    0x00074244: "scsi_disk_hard_reset()",
    0x000743dc: "scsi_disk_soft_reset()",
    0x000745d2: "D1=scsi_disk_get_status()",
    0x00076000: "RESHA_TAPE_EEPROM_DEST",
    0x8000000c: "print_OK()",
    0x80000010: "failure()",
    0x80000014: "delay()",
    0x80000018: "puts(A0)",
    0x8000001c: "puts(inline)",
    0x80000020: "print_CRLF()",
    0x80000024: "RESET",
    0x80000072: "txt_FAILURE",
    0x80000088: "failure",
    0x800000d8: "_puts(A0)",
    0x800000e2: "_puts(inline)",
    0x800000f8: "_outstring(A0)",
    0x80000142: "_print_OK()",
    0x8000014c: "_print_CRLF()",
    0x8000015e: "_delay()",
    0x8000016c: "checksum",
    0x8000038a: "ramtest",
    0x800003aa: "ramtest_1",
    0x800003e4: "ramtest_2",
    0x8000040e: "ramtest_3",
    0x8000043a: "ramtest_4",
    0x80000464: "ramtest_5",
    0x800004fe: "ramtest_6",
    0x80001010: "resha_download_part(DO=part, A1=name)",
    0x80002054: "resha_download_target_address()",
    0x8000205c: "resha_download()",
    0x80003a40: "resha_download_target_address()",
    0x80003a9a: "resha_download()",
    0x9303e800: "SCSI_00_OWN_ID_CDB_SIZE",
    0x9303e801: "SCSI_01_CONTROL",
    0x9303e802: "SCSI_02_TIMEOUT_PERIOD",
    0x9303e803: "SCSI_03_CDB1_TOTSECT",
    0x9303e804: "SCSI_04_CDB2_TOTHEAD",
    0x9303e805: "SCSI_05_CDB3_TOTCYL1",
    0x9303e806: "SCSI_06_CDB4_TOTCYL0",
    0x9303e807: "SCSI_07_CDB5_LBA3",
    0x9303e808: "SCSI_08_CDB6_LBA2",
    0x9303e809: "SCSI_09_CDB7_LBA1",
    0x9303e80a: "SCSI_0a_CDB8_LBA0",
    0x9303e80b: "SCSI_0b_CDB9_SECT",
    0x9303e80c: "SCSI_0c_CDB10_HEAD",
    0x9303e80d: "SCSI_0d_CDB11_CYL1",
    0x9303e80e: "SCSI_0e_CDB12_CYL2",
    0x9303e80f: "SCSI_0f_LUN",
    0x9303e810: "SCSI_10_CMD_PHASE",
    0x9303e811: "SCSI_11_SYNC_XFER",
    0x9303e812: "SCSI_12_COUNT2",
    0x9303e813: "SCSI_13_COUNT1",
    0x9303e814: "SCSI_14_COUNT0",
    0x9303e815: "SCSI_15_DEST_ID",
    0x9303e816: "SCSI_16_SRC_ID",
    0x9303e817: "SCSI_17_SCSI_STATUS",
    0x9303e818: "SCSI_18_CMD",
    0x9303e819: "SCSI_19_DATA",
    0x9303e81f: "SCSI_1f_AUX_STATUS",
    0xffff9000: "IO_UART",
}

my68k20_instructions = """
#               src,dst         ea      |_ _ _ _|_ _ _v_|_ _v_ _|_v_ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|

INLTXT		inltxt		0	|0 1 0 0 1 1 1 0 1 0 0 1 0 1 1 0| a1            | a2            |
"""

class my68k20_ins(m68020.m68020_ins):

    def assy_inltxt(self):
        y = data.Txt(self.lang.m, self.lo + 2, label=False, splitnl=True, align=2)
        self.lang.disass(y.hi)
        raise assy.Invalid("Inline text hack")

class my68k20(m68020.m68020):
    def __init__(self, lang="my68k20"):
        super().__init__(lang)
        self.add_ins(my68k20_instructions, my68k20_ins)

def inline_text(asp, ins):
    if not ins.dstadr in (
        0x8000001c,
        0x800000e2,
        0x80002028,
        0x80002aa8,
    ):
        return
    if ins.lo in (
        0x8000001c,
        0x80002028,
    ):
        return
    y = data.Txt(asp, ins.hi, label=False, splitnl=True, align=2)
    ins.lang.disass(y.hi, asp=asp)

def resha_section(asp, a, handle):

    y = data.Pstruct(asp, a + 1, "B", fmt="RESHA_SECTION_MARKER=0x%02x")
    assert y.data[0] == 0xa5

    y = data.Pstruct(asp, a + 0x1ffa, "B", fmt="RESHA_CHECKSUM_OFFSET=0x%02x")
    s = 0x56
    for i in range(0x2000):
        s += asp[a + i]
    s &= 0xff
    s -= y.data[0]
    print("resha_sum 0x%x = 0x%x" % (a, s))
    assert s == 0, "SUM 0x%x" % s

    y = data.Pstruct(asp, a + 0, "B", fmt="RESHA_NENTRY=0x%02x")
    for i in range(y.data[0]):
        z = data.Pstruct(asp, a + 2 + 2 * i, ">H", fmt="0x%04x")
        b = a + z.data[0]
        asp.set_block_comment(b, "RESHA 0x%x ENTRY[0x%x]" % (a, i))
        c = handle.get(i)
        if c and c[0]:
            asp.set_label(b, c[0])
        if c and c[1]:
            c[1](b)

def example():
    m0 = mem.Stackup(FILENAMES, nextto=__file__)

    cx = my68k20()

    cx.flow_check.append(inline_text)
    cx.trap_returns[0] = True

    cx.m.map(m0, 0x0, 0x8)
    cx.m.map(m0, 0x80000000, 0x80002000, 0x0000)
    cx.m.map(m0, 0x80004000, 0x80006000, 0x2000)
    cx.m.map(m0, 0x80002000, 0x80004000, 0x4000)
    cx.m.map(m0, 0x80006000, 0x80008000, 0x6000)
    cx.m.map(m0, 0x00070000, 0x00072000, 0x8000)
    cx.m.map(m0, 0x00072000, 0x00074000, 0xa000)
    cx.m.map(m0, 0x00074000, 0x00076000, 0xc000)
    cx.m.map(m0, 0x00076000, 0x00078000, 0xe000)

    for a, b in SYMBOLS.items():
        cx.m.set_label(a, b)

    resha_section(
        cx.m,
        0x70000,
        {
            0: ( None, cx.disass ),
            1: ( None, cx.disass ),
            2: ( None, cx.disass ),
            3: ( None, cx.disass ),
            4: ( None, cx.disass ),
            5: ( None, cx.disass ),
        }
    )
    resha_section(
        cx.m,
        0x72000,
        {
            0: ( None, cx.disass ),
            2: ( None, cx.disass ),
            3: ( None, cx.disass ),
        }
    )
    resha_section(
        cx.m,
        0x74000,
        {
            0: ( None, cx.disass ),
            1: ( None, cx.disass ),
        }
    )
    resha_section(
        cx.m,
        0x76000,
        {
            0: ( None, cx.disass ),
        }
    )

    cx.disass(0x80000024)
    for a in (
        0x80000072,
        0x80000156,
        0x800001c4,
        0x80000314,
        0x80000374,
        0x80000552,
        0x80002a24,
        0x80002a2c,
        0x800033ce,
        0x80003690,
        0x80004afe,
        0x80004b42,
        0x80004b68,
        0x80007e0b,
    ):
        data.Txt(cx.m, a, label=False, align=2)

    def txts(a, b, align=2, label=False):
        while a < b:
            y = data.Txt(cx.m, a, label=label, align=align, splitnl=True)
            a = y.hi

    txts(0x7063e, 0x70708, align=1)
    txts(0x712a6, 0x71308, align=1)
    txts(0x719f2, 0x71ab8, align=1)
    txts(0x74006, 0x7412c, align=1, label=True)
    txts(0x76248, 0x763b0, align=1)

    for a in range(0x76084, 0x760c8, 4):
        y = cx.dataptr(a)
        data.Txt(cx.m, y.dst)

    for a in range(0x76a4c, 0x76a54, 4):
        y = cx.dataptr(a)
        data.Txt(cx.m, y.dst)

    a = 0x765e4
    while a < 0x76656:
        w = data.Pstruct(cx.m, a, "<H", fmt="0x%x")
        y = cx.dataptr(w.hi)
        if y.dst:
            data.Txt(cx.m, y.dst)
        a = y.hi

    a = 0x7351e
    while True:
        w = data.Pstruct(cx.m, a, "<H", fmt="0x%x")
        if not w.data[0]:
            break
        y = cx.codeptr(w.hi)
        a = y.hi

    for a in range(0x7352e, 0x7353c, 4):
        y = cx.codeptr(a)
        cx.m.set_line_comment(y.dst, "VIA 0x%x" % a)

    for a in range(0x734ea, 0x7351e, 4):
        y = cx.codeptr(a)
        cx.m.set_line_comment(y.dst, "VIA 0x%x" % a)

    for a in range(0x76040, 0x76080, 4):
        y = cx.codeptr(a)
        cx.m.set_line_comment(y.dst, "VIA 0x%x" % a)

    for a in (
        0x7051c,
        0x70554,
        0x705d4,
        0x705df,
        0x705e8,
        0x705f5,
        0x70628,
        0x70746,
        0x709ea,
        0x71010,
        0x71025,
        0x71039,
        0x7104c,
        0x71b10,
        0x7200a,
        0x76128,
        0x762b0,
        0x76a0a,
        0x76a28,
        0x76a46,
        0x76990,
        0x76a46,
        0x76220,
        # 0x77666,
    ):
        data.Txt(cx.m, a)

    txts(0x800010cc, 0x80001122, align=1, label=True)
    txts(0x80001bb0, 0x80001bc2)
    txts(0x80002c14, 0x80002e04, align=1)
    txts(0x80004ece, 0x80004fbf, align=1)
    txts(0x800027ee, 0x800028ca, align=1)

    ##########
    data.Txt(cx.m, 0x8000221c, align=1)
    data.Txt(cx.m, 0x80002232, align=1, splitnl=True)
    data.Txt(cx.m, 0x8000223d, align=1, splitnl=True)
    l = []
    for a in range(0x8000228f, 0x800024a8):
        x = cx.m[a]
        if not x:
            l.append(a)
            break
        if x & 0x80:
            l.append(a)
    for i in range(len(l)-1):
        data.Txt(cx.m, l[i], l[i+1], align=1, label=not i)
    data.Txt(cx.m, l[-1] + 1, align=1, label=False)

    # 0x8000298e
    y = data.Txt(cx.m, 0x8000240c, splitnl=True, align=1)
    y = data.Txt(cx.m, 0x80002481, splitnl=True, align=1)
    y = data.Txt(cx.m, 0x8000254e, splitnl=True, align=1)
    y = data.Txt(cx.m, 0x8000256e, splitnl=True, align=1)
    y = data.Txt(cx.m, 0x8000257d, splitnl=True, align=1)
    y = data.Txt(cx.m, 0x8000258c, splitnl=True, align=1)
    y = data.Txt(cx.m, 0x8000259b, splitnl=True, align=1)

    for a, b in (
        (0x704e8, None),
        (0x70708, None),
        (0x72c5e, None),
        (0x730a8, None),       # via 0x734f2
        (0x73134, None),       # via 0x734ee
        (0x73258, None),       # via 0x731b2
        (0x7338a, None),
        (0x73396, None),       # via 0x731b2
        (0x734ca, None),
        (0x733a2, None),
        (0x731b6, None),
        (0x7412e, None),
        (0x7665a, None),
        (0x74208, None),
        (0x74212, None),
        (0x77662, None),

        (0x8000000c, None,),
        (0x80000010, None,),
        (0x80000014, None,),
        (0x80000018, None,),
        (0x8000001c, None,),
        (0x80000020, None,),
        (0x800001f6, None,),
        (0x80000208, None,),
        (0x8000021a, None,),
        (0x80001524, None,),
        (0x80001566, None,),
        (0x800015a8, None,),
        (0x80001628, None,),
        (0x800016c2, None,),
        (0x80002796, None,),
        (0x800027ca, None,),
        (0x80002bbe, None,),
        (0x80002bc4, None,),
        (0x800040a0, None,),
    ):
        cx.disass(a)
        if not b:
            b = "MANUAL"
        cx.m.set_line_comment(a, b)

    for a in range(0x80002000, 0x80002074, 4):
        cx.disass(a)

    for a in range(0x8000310e, 0x80003122, 4):
        cx.codeptr(a)

    for a in range(0x800038ce, 0x800038ee, 4):
        cx.codeptr(a)

    for a in range(0x80004000, 0x80004008, 4):
        cx.disass(a)

    for a in range(0x800043aa, 0x80004492, 6):
        y = data.Const(cx.m, a, a + 4, func=cx.m.bu32, size=4)
        z = data.Const(cx.m, y.hi, y.hi + 2, func=cx.m.bu16, size=2)
        w = cx.m.bu16(a + 4)
        w >>= 4
        w &= 0xffe
        d = 0x800043aa + w
        cx.disass(d)


    for a in range(0x80004a7a, 0x80004a98, 4):
        d = cx.m.bu32(a)
        data.Dataptr(cx.m, a, a + 4, d)
        data.Txt(cx.m, d, align=1)

    for a in range(0x800036e8, 0x800036fc, 4):
        d = cx.m.bu32(a)
        data.Dataptr(cx.m, a, a + 4, d)
        data.Txt(cx.m, d)

    data.Const(cx.m, 0x80001ffa, 0x80002000)
    data.Const(cx.m, 0x80003ffa, 0x80004000)
    data.Const(cx.m, 0x80005ffa, 0x80006000)
    data.Const(cx.m, 0x80007dfa, 0x80007e00)

    # See 0x800039e0
    data.Const(cx.m, 0x80003a2a, 0x80003a2a + 0x16)

    y = data.Pstruct(cx.m, 0x80007e84, ">L")
    y.lcmt = "Machine Number"

    d = discover.Discover(cx)

    return NAME, (cx.m,)

#######################################################################

if __name__ == '__main__':
    listing.Example(example, ncol=8)
