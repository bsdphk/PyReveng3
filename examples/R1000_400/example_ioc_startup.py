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
   DFS STARTUP (~ "/sbin/init")  binary files
   ------------------------------------------
'''

import os

from pyreveng import mem, listing
import pyreveng.cpu.m68020 as m68020
import pyreveng.cpu.m68000_switches as m68000_switches

import ioc_utils
import ioc_hardware
import ioc_eeprom_exports
import ioc_m200_exports
import m200_pushtxt
import m200_syscall

FILENAME = os.path.join(os.path.split(__file__)[0], "PROGRAM_0.M200")
NAME="IOC_PROGRAM_0"
BASE = 0x20000

def head1_indir(cx, adr):
    if cx.m[adr] != 0x4f:
        return
    adr += 1
    if cx.m[adr] != 0xfa:
        return
    adr += 1
    b = cx.m.bs16(adr)
    cx.disass(adr + b)

def artifact_f15447000232a02a(cx):
    head = []
    for a in range(BASE, BASE+0x20, 4):
        head.append(cx.dataptr(a))

    for i in (1, 6, 7):
        cx.disass(head[i].dst)
        cx.m.set_label(head[i].dst, "HEAD.%d" % i)
    head1_indir(cx, head[1].dst)

    for a in (
        0x2418e,
        0x241b8,
        0x241e2,
        0x2420c,
        0x24238,
        0x2425c,
    ):
        cx.disass(a)
        cx.m.set_line_comment(a, "MANUAL")

    # Last seen:
    # 00023be8  JSR     0x21902
    # 0002194c  JSR	102c4
    # 00021950	FSCALL_103d8_flush_console?
    # 0002195c  FSCALL_103d0
    # 0002196c  KERNCALL_00
    # 000219c0  FSCALL_10394
    # 00010394  bra 00013ee4
    # 00013f06  jsr     $14740.l
    # 0001aff8  jsr     $10238.l
    # 00010238  dc.w    $a01c; opcode 1010
    # 00008370: 48e7 8004           : movem.l D0/A5, -(A7)
    # 0001affe
    # 0001b01e  rts
    # 000127f4
    # 000128d0: 4eb9 0001 0204      : jsr     $10204.
    # 00010204: a002                : dc.w    $a002; opcode 1010
    # 00008370: 48e7 8004           : movem.l D0/A5, -(A7)
    # 00008374: 3037 0161 000a      : move.w  ([$a,A7]), D0
    # 0000837a: 0440 a000           : subi.w  #-$6000, D0
    # 0000837e: 41bc 0020           : chk.w   #$20, D0
    # 00008382: 4e6d                : move    USP, A5
    # 00008384: 2f5d 000a           : move.l  (A5)+, ($a,A7)
    # 00008388: 4e65                : move    A5, USP
    # 0000838a: 4eb0 05b1 0000 a7f4 : jsr     ([$a7f4,D0.w*4])
    # 000084b2: 48e7 80c0           : movem.l D0/A0-A1, -(A7)
    # 000084b6: 3015                : move.w  (A5), D0
    # 000084b8: 41bc 001f           : chk.w   #$1f, D0
    # 000084bc: eb48                : lsl.w   #5, D0
    # 000084be: 41f0 01b0 0000 e800 : lea     ($e800,D0.w), A0
    # 000084c6: 226d 0006           : movea.l ($6,A5), A1
    # 000084ca: 236d 0002 0001      : move.l  ($2,A5), ($1,A1)
    # 000084d0: 4eb9 0000 8da2      : jsr     $8da2.l
    # 00008da2: 48e7 4060           : movem.l D1/A1-A2, -(A7)
    # 00008da6: 08a8 0005 000e      : bclr    #$5, ($e,A0)
    # 00008dac: 57fa 083c           : trapeq  #$83c; (2+)
    # 00008db0: 08e8 0006 000e      : bset    #$6, ($e,A0)
    # 00008db6: 56fa 065a           : trapne  #$65a; (2+)
    # 00008dba: 45e8 0010           : lea     ($10,A0), A2
    # 00008dbe: 24d9                : move.l  (A1)+, (A2)+
    # 00008dc0: 24d9                : move.l  (A1)+, (A2)+
    # 00008dc2: 24d9                : move.l  (A1)+, (A2)+
    # 00008dc4: 2491                : move.l  (A1), (A2)
    # 00008dc6: 08e8 0002 0019      : bset    #$2, ($19,A0)
    # 00008dcc: 42a8 0008           : clr.l   ($8,A0)
    # 00008dd0: 1228 0015           : move.b  ($15,A0), D1
    # 00008dd4: 0241 0007           : andi.w  #$7, D1
    # 00008dd8: 43bc 0007           : chk.w   #$7, D1
    # 00008ddc: 03f9 0000 04ea      : bset    D1, $4ea.l
    # 00008de2: 4eb0 15b1 0000 a8a0 : jsr     ([$a8a0,D1.w*4])
    # 00004b0a: 46fc 2200           : move    #$2200, SR
    # 00004b0e: 4241                : clr.w   D1
    # 00004b10: 1228 001b           : move.b  ($1b,A0), D1
    # 00004b14: 43bc 0020           : chk.w   #$20, D1
    # 00004b18: 4ef0 15b1 0000 a68c : jmp     ([$a68c,D1.w*4])
    # 00004d32: 4eb8 49e0           : jsr     $49e0.w
    # 000049e0: 48e7 8020           : movem.l D0/A2, -(A7)
    # 000049e4: 4280                : clr.l   D0
    # 000049e6: 1028 001a           : move.b  ($1a,A0), D0
    # 000049ea: 41bc 0003           : chk.w   #$3, D0
    # 000049ee: 2470 05a0 092e      : movea.l ($92e,D0.w*4), A2
    # 000049f4: 4a2a 001b           : tst.b   ($1b,A2)
    # 000049f8: 56fa 0806           : trapne  #$806; (2+)
    # 0000a090: 0817 0005           : btst    #$5, (A7)




def m200_file(m0, ident=None):
    ''' A generic .M200 file '''
    cx = m68020.m68020()
    m68000_switches.m68000_switches(cx)
    m200_syscall.add_syscall(cx)
    m200_pushtxt.add_pushtxt(cx)
    cx.m.map(m0, BASE)

    digest = hashlib.sha256(m0.bytearray(m0.lo, m0.hi - m0.lo)).hexdigest()[:16]
    print("DD", __file__, digest, ident)

    if digest == "f15447000232a02a":
        artifact_f15447000232a02a(cx)
    else:
        head = []
        for a in range(BASE, BASE+0x20, 4):
            head.append(cx.dataptr(a))

        for i in (1, 6, 7):
            cx.disass(head[i].dst)
            cx.m.set_label(head[i].dst, "HEAD.%d" % i)

        head1_indir(cx, head[1].dst)

        while True:
            stop = True
            for i, _j in cx.m.gaps():
                if not i & 1 and cx.m.bu16(i) in (
                    0x4cdf,
                    0x4e56,
                    0x4eb9,
                ):
                    # print("0x%x" % i, "0x%x" % cx.m.bu16(i))
                    cx.m.set_line_comment(i, "(discovered)")
                    cx.disass(i)
                    stop = False
                    break
            if stop:
                break

    return cx

#######################################################################

class IocStartup(ioc_utils.IocJob):
    ''' The "/sbin/init" of IOC '''

    def __init__(self, **kwargs):
        super().__init__(BASE, name=NAME, **kwargs)

    def default_image(self):
        ''' Load default image '''
        self.map(mem.Stackup((FILENAME,)))

    def config_cx(self):
        ''' Add global symbol sets etc. '''
        cx = self.cx
        ioc_hardware.add_symbols(cx.m)
        ioc_eeprom_exports.add_symbols(cx.m)
        ioc_m200_exports.add_symbols(cx.m)
        m200_pushtxt.add_pushtxt(cx)

    def round_0(self):
        ''' Things to do before the disassembler is let loose '''
        cx = self.cx
 
    def round_1(self):
        ''' Let the disassembler loose '''
        cx = self.cx
        y = cx.codeptr(0x20004)
        cx.disass(y.dst + 10)
        cx.m.set_label(y.dst, "MAIN()")

#######################################################################
 
def example():
    ''' Follow the example protocol '''
    return IocStartup().example()
 
#######################################################################
 
if __name__ == '__main__':
    ioc_utils.mainfunc(__file__, example, IocStartup)

