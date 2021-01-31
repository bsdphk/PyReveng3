#!/usr/bin/env python
#
# Copyright (c) 2020-2021 Poul-Henning Kamp <phk@phk.freebsd.dk>
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
    Motorola S-record tools
    -----------------------
'''

from pyreveng import mem

class IgnoredLine(Exception):
    ''' Bad Line, Ignored '''

class BadLine(Exception):
    ''' Bad Line '''

class BadSet(Exception):
    ''' Bad Set of S-records '''

def truncate(x):
    if len(x) < 20:
        return x
    return x[:20] + "…"

class SRecord():
    ''' A single S-Record '''
    def __init__(self, text):
        text = text.rstrip()
        if text[0] != 'S':
            raise IgnoredLine("S-rec line must start with 'S' (not '%s')" % truncate(text))
        if text[1] not in '012356789':
            raise IgnoredLine(
                "S-rec line must start with 'S[12356789]' (not '%s')" % truncate(text)
            )
        self.text = text
        self.stype = int(text[1])
        self.octets = bytes()
        self.length = 0
        self.address = 0
        self.end = 0
        if not self.stype:
            self.octets = bytes()
            self.length = 0
            self.address = 0
            return
        i = bytes.fromhex(text[2:])
        if len(i) == 2 and not max(i):
            raise IgnoredLine("S-rec placeholder ('%s')" % truncate(text))
        if sum(i) & 0xff != 0xff:
            raise BadLine("Checksum error on line '%s'" % truncate(text))
        length = i[0]
        if length + 1 != len(i):
            raise BadLine("Length does not match on line '%s'" % truncate(text))
        if self.stype in (1, 5, 9):
            self.address = int.from_bytes(i[1:3], "big")
            self.octets = i[3:-1]
        elif self.stype in (2, 6, 8):
            self.address = int.from_bytes(i[1:4], "big")
            self.octets = i[4:-1]
        else:
            self.address = int.from_bytes(i[1:5], "big")
            self.octets = i[5:-1]
        if self.isdata():
            self.end = self.address + len(self.octets)

    def __len__(self):
        return len(self.octets)

    def __iter__(self):
        yield from self.octets

    def __lt__(self, other):
        return self.address < other.address

    def isdata(self):
        ''' This is a data record '''
        return self.stype in (1, 2, 3)

    def isstart(self):
        ''' This is a start record '''
        return self.stype in (7, 8, 9)

    def iscount(self):
        ''' This is a count record '''
        return self.stype in (4, 5)

class SRecordSet():
    ''' A set of S-records '''
    def __init__(self, quiet=False):
        self.records = []
        self.quiet = quiet

    def __iter__(self):
        yield from self.records

    def from_file(self, filename):
        ''' Load S-records from file '''
        for i in open(filename):
            try:
                self.add_record(i)
            except IgnoredLine as err:
                if not self.quiet:
                    print(err)
        return self

    def from_string(self, string):
        ''' Load S-records from file '''
        for i in string.split('\n'):
            try:
                self.add_record(i)
            except IgnoredLine as err:
                if not self.quiet:
                    print(err)
        return self

    def from_mem(self, mem, lo=None, hi=None):
        ''' Load S-records from a pyreveng.mem '''
        if lo is None:
            lo = mem.lo
        if hi is None:
            hi = mem.hi
        self.from_string(mem.bytearray(lo, hi-lo).decode("ASCII"))
        return self

    def add_record(self, text):
        ''' Add a record '''
        self.records.append(SRecord(text))

    def start_address(self):
        ''' Return the start address '''
        retval = None
        for srec in self:
            if srec.isstart():
                if retval is not None:
                    raise BadSet("Multiple Start records")
                retval = srec.address
        return retval

    def range(self):
        ''' Return lowest and highest addresses in data records '''
        lo = 0xffffffff
        hi = 0x00000000
        for srec in self:
            if srec.isdata():
                lo = min(lo, srec.address)
                hi = max(hi, srec.address + len(srec.octets))
        return lo, hi

    def sections(self):
        ''' Yields range of contiguous sections '''
        a = None
        b = None
        for srec in sorted(self):
            if not srec.isdata():
                continue
            if a is None:
                a = srec.address
            elif b != srec.address:
                yield a, b
                a = srec.address
            b = srec.address + len(srec.octets)
        yield a, b

    def map(self, asp, lo=0, hi=(1<<32)):
        ''' Map a set of S-records into an address space '''
        chunks = []
        for slo, shi in self.sections():
            if shi <= lo or slo >= hi:
                continue
            slo = max(lo, slo)
            shi = min(hi, shi)
            m = mem.ByteMem(slo, shi)
            asp.map(m, slo, shi, slo)
            chunks.append(m)
        cur = chunks.pop(0)
        for srec in self:
            if not srec.isdata():
                continue
            if srec.end <= lo or srec.address >= hi:
                continue
            while not (cur.lo <= srec.address and srec.end <= cur.hi):
                chunks.append(cur)
                cur = chunks.pop(0)
            for n, i in enumerate(srec.octets):
                cur[srec.address + n] = i
