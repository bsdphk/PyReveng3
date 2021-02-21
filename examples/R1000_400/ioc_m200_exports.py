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
   IOC KERNEL and FS exports
   -------------------------
'''

# Calls into KERNEL through A-Line vectors in FS
KERNCALLS = {
    0x02: "Disk_I_O",
    0x05: "WriteConsole",
    0x10: "Panic",
    0x15: "DiagBus",
    0x16: "ClockMargin",
    0x17: "PsuMargin",
    0x1c: "memcpy_protected(src, dst, len)",
}

def kerncall_name(a):
    ''' Name of kerncall by vector number '''
    if a >= 0x20:
        return "KERNCALL_%02x_UNIMPL" % a
    t = KERNCALLS.get(a)
    if t:
        return "KERNCALL_%02x_" % a + t
    return "KERNCALL_%02x" % a

FSCALLS = {
    0x10284: "string_lit2something",    # ref: DBUSULOAD.M200
    0x1028c: "muls_d3_d4_to_d3",    	# ref: FS.0 0x107ea
    0x10290: "mulu_d3_d4_to_d3",    	# ref: FS.0 0x107f4
    0x10294: "divs_d3_d4",    		# ref: FS.0 0x1080a
    0x10298: "divu_d3_d4",    		# ref: FS.0 0x10816
    0x1029c: "malloc(LONG)",   		# ref: FS.0 0x10816
    0x102a8: "free(LONG, PTR)",
    0x102b8: "alloc_str()",
    0x102c4: "fill_str(WORD, WORD, PTR)",
    0x102d0: "strcat(STR, STR)",
    0x10384: "read_from_file",          # ref: DBUSULOAD.M200
    0x103b0: "exec_command()",          # 
    0x103d0: "wr_console_c(CHAR)",
    0x103d8: "wr_console_s(STR)",
    0x1047e: "send_experiment",
    0x10496: "experiment_close",        # ref: FS.0 0x18f4e
    0x1056e: "open_file",               # ref: BOOTINFO.M200
}

def fscall_name(a):
    ''' Name of fscall by address '''
    if 0x10200 <= a < 0x10280:
        return kerncall_name((a - 0x10200) >> 1)
    t = FSCALLS.get(a)
    if t:
        return "FSCALL_%02x_" % a + t
    return "FSCALL_%02x" % a

def fs_entrypoints():
    ''' Yield FS's entrypoints '''
    for a in range(0x10200, 0x10280, 2):
        yield a
    for a in range(0x10280, 0x10460, 4):
        yield a
    for a in range(0x10460, 0x1061c, 6):
        yield a

def add_symbols(asp):
    ''' Add symbols for .M200 binaries '''
    for a in fs_entrypoints():
        asp.set_label(a, fscall_name(a))
