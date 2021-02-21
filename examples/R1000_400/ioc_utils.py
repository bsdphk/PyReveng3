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
   Base class for modular IOC jobs
   -------------------------------
'''

import os
import sys
import hashlib

from pyreveng import mem, listing, discover
import pyreveng.cpu.m68020 as m68020
import pyreveng.cpu.m68000_switches as m68000_switches
import pyreveng.toolchest.srecords as srecords

class IocJob():

    ''' A baseclass for IOC jobs '''

    def __init__(self,
        lo=None,
        hi=None,
        name=None,
        ident=None,
        cx=None,
        digest=None,
        image=None,
    ):
        self.lo = lo
        self.hi = hi
        self.name = name
        self.ident = ident
        self.cx = cx
        self.digest = digest
        self.had_specific = False
        if not self.cx:
            self.cx = m68020.m68020()
            m68000_switches.m68000_switches(self.cx)
        if image:
            self.map(image)
            self.ponder()

    def default_image(self):
        ''' Load default image '''
        raise Exception(".default_image() method override missing")

    def example(self):
        ''' example protocol function '''
        self.default_image()
        self.ponder()
        return self.name, (self.cx.m,)

    def augment_cx(self):
        ''' Add Capabilities to cx '''

    def config_cx(self):
        ''' Add global symbol sets etc. '''

    def map(self, m0, offset=None):
        ''' Map m0 according to self.lo and self.hi '''
        if m0[0] == 0x53 and 0x30 <= m0[1] <= 0x39:
            print("SRECS!")
            srec = srecords.SRecordSet().from_mem(m0)
            srec.map(self.cx.m, lo=self.lo, hi=self.hi)
            if not self.hi:
                _i, self.hi = srec.range()
        else:
            if not self.hi:
                self.hi = self.lo + m0.hi - m0.lo
            self.cx.m.map(m0, self.lo, self.hi, offset=offset)
        self.digest = hashlib.sha256(
            self.cx.m.bytearray(self.lo, self.hi - self.lo)
        ).hexdigest()[:16]
        print("Digest", self.digest, self.ident)

        if False:
            d2 = 0x56
            a = self.lo
            for i in range(0x1ffa):
                d2 += self.cx.m[a]
                a += 1
            print("D2_1 0x%x" % d2, "A %x" % a)
            a += 1
            for i in range(0x5):
                print("a %x" % a)
                d2 += self.cx.m[a]
                a += 1
            print("CHECKSUM 0x%x" % (d2 & 0xff))


    def ponder_round(self, turnus):
        ''' Ponder one round, generic [and specific] '''
        i = "round_%d" % turnus
        j = getattr(self, i)
        j()
        i += "_" + self.digest
        j = getattr(self, i, None)
        if j is not None:
            self.had_specific = True
            j()

    def ponder(self):
        ''' Four rounds, generic [and specific] '''
        self.augment_cx()
        self.config_cx()
        for i in range(4):
            self.ponder_round(i)

    def round_0(self):
        ''' Things to do before the disassembler is let loose '''

    def round_1(self):
        ''' Let the disassembler loose '''

    def round_2(self):
        ''' Spelunking in what we alrady found '''

    def round_3(self):
        ''' Discovery, if no specific hints were encountered '''
        if not self.had_specific:
            discover.Discover(self.cx)

def mainfunc(jobfile, example, jobclass):
    ''' Standard __main__ function '''

    if len(sys.argv) == 5 and sys.argv[1] == "-AutoArchaeologist":
        print("PyReveng3", os.path.basename(jobfile))
        mb = mem.Stackup((sys.argv[3],))
        cx = jobclass(ident=sys.argv[2], image=mb).cx
        listing.Listing(cx.m, fn=sys.argv[4], ncol=8, leaf_width=72)
    else:
        assert "-AutoArchaeologist" not in sys.argv
        listing.Example(example, ncol=8)
