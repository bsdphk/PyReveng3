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
'''
   DFS system calls
'''

from pyreveng import data
import pyreveng.cpu.m68020 as m68020

M200_SYSCALL_DESC = '''
SYSJMP		sc		| 4E | F9 | 00 | 01 |
SYSJMP		sc		| 4E | F9 | 80 | 00 |
SYSCALL		sc		| 4E | B9 | 00 | 01 |
SYSCALL		sc		| 4E | B9 | 80 | 00 |
'''

class M200SyscallIns(m68020.m68020_ins):
    ''' Syscall pseudo-instructions '''
    def assy_sc(self):
        self.syscall = self.lang.m.bu16(self.hi)
        self.syscall |= self.lang.m.bu16(self.hi - 2) << 16
        self.hi += 2
        j = "syscall_%x" % self.syscall
        if hasattr(self, j):
            return getattr(self, j)()
        if self.lang.m[self.lo + 1] == 0xf9:
            self.flow_J()
        return "0x%x" % self.syscall

    def syscall_10284(self):
        self.flow_J()
        return "0x%x" % self.syscall

    def syscall_102c4(self):
        return "0x%x = something_string" % self.syscall

    def syscall_10384(self):
        return "0x%x = read_from_file" % self.syscall

    def syscall_103d8(self):
        return "0x%x = flush_console?" % self.syscall

    def syscall_10568(self):
        l = self.lang.m[self.hi + 2]
        data.Txt(self.lang.m, self.hi + 3, self.hi + 3 + l, label=False)
        self.flow_J()
        return "0x%x" % self.syscall

def add_syscall(cx):
    ''' Add ourselves to a m68k disassembler '''
    cx.add_ins(M200_SYSCALL_DESC, M200SyscallIns)
