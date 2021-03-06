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

from pyreveng import data, assy
import pyreveng.cpu.m68020 as m68020

import dfs_experiments
import ioc_m200_exports

M200_SYSCALL_DESC = '''
SYSJMP		sc		| 4E | F9 | 00 | 01 |
SYSJMP		sc		| 4E | F9 | 80 | 00 |
SYSCALL		sc		| 4E | B9 | 00 | 01 |
SYSCALL		sc		| 4E | B9 | 80 | 00 |
STACKCHECK	-		| BF | D5 | 62 | 06 | 44 | FC | 00 | 02 | 4E | 76 |
'''

class M200SyscallIns(m68020.m68020_ins):
    ''' Syscall pseudo-instructions '''

    def assy_sc(self):
        ''' Call into FS (or KERNEL via FS) '''
        self.syscall = self.lang.m.bu16(self.hi)
        self.syscall |= self.lang.m.bu16(self.hi - 2) << 16
        self.hi += 2
        self.mne = ioc_m200_exports.fscall_name(self.syscall)
        j = "syscall_%x" % self.syscall
        if hasattr(self, j):
            return getattr(self, j)()

        if self.lang.m[self.lo + 1] == 0xf9:
            self.flow_J()
        return None

    def syscall_10284(self):
        ''' Does not seem to come back '''
        self.flow_J()
        return "0x%x" % self.syscall

    def syscall_10568(self):
        ''' Generated wrappers to call an experiment with parameters? '''
        exp_name_len = self.lang.m[self.hi + 2]
        self.oper.append(assy.Arg_dst(self.lang.m, self.syscall))
        for _i in range(3):
            self.oper.append(assy.Arg_imm(self.lang.m[self.hi]))
            self.hi += 1
        _j, txt = data.stringify(self.lang.m, self.hi, exp_name_len)
        self.oper.append(assy.Arg_verbatim("'" + txt + "'"))
        self.hi += exp_name_len
        narg = self.lang.m[self.hi + 2] + self.lang.m[self.hi + 3]
        for _i in range(4 + narg):
            self.oper.append(assy.Arg_imm(self.lang.m[self.hi]))
            self.hi += 1
        self.flow_J()
        lbl = "exp_" + txt + "("
        args = dfs_experiments.EXPERIMENTS.get(txt)
        if args:
            lbl += ", ".join(b + "{" + a + "}" for a, b in args)
        self.lang.m.set_label(self.lo, lbl + ")")
        self.compact = True
        if self.hi & 1 and not self.lang.m[self.hi]:
            self.hi += 1

def add_syscall(cx):
    ''' Add ourselves to a m68k disassembler '''
    cx.add_ins(M200_SYSCALL_DESC, M200SyscallIns)
