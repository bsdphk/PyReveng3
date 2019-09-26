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

from . import mem, misc

class Render_mem():
    def __init__(self, pj, fmt="x", ascii=True, ncol=None):

        self.ascii = ascii

        i = "%" + fmt
        j = i % (pj.m.hi - 1)
        self.apct = "%" + "0%d" % len(j) + fmt

        j = i % (1 << pj.m.bits - 1)
        self.dpct = "%" + "0%d" % len(j) + fmt
        self.undef = "-" * len(j)
        self.space = " " * len(j)
        self.aspace = " " * (pj.m.bits//8)

        if ncol is not None:
            self.ncol = ncol
        elif pj.m.bits == 8:
            self.ncol = 4
        else:
            self.ncol = 1

    def render_word(self, pj, lo, hi):
        s = ""
        t = ""
        s += self.apct % lo + " "
        for i in range(min(self.ncol, hi - lo)):
            try:
                v = pj.m[lo + i]
            except mem.MemError:
                v = None

            if v is None:
                s += " " + self.undef
            else:
                s += " " + self.dpct % v

            if self.ascii:
                b = pj.m.bits - 8
                while b >= 0:
                    if v is None:
                        t += " "
                    else:
                        x = (v >> b) & 0xff
                        if x > 32 and x < 127:
                            t += "%c" % x
                        else:
                            t += " "
                    b -= 8
        while i + 1 < self.ncol:
            s += " " + self.space
            t += self.aspace
            i += 1
        if self.ascii:
            s += "  |" + t + "|"
        return s

    def render(self, pj, lo, hi, nlin):
        """
        Render 'ncol' words per line
        """
        l = list()
        while lo < hi and nlin > 0:
            s = ""
            t = ""
            s += self.render_word(pj, lo, hi)
            l.append((lo, s))
            lo += self.ncol
            nlin -= 1
        return l

class Seg_Listing():
    def __init__(self, pj, fo, mem, low, high, ascii=True, pil=True, ncol=None, fmt="x"):
        self.pj = pj
        self.mem = mem
        self.fmt = fmt
        self.ncol = ncol
        self.ascii = ascii
        self.pil = pil
        self.pil_col = 132

        self.labels = sorted([adr for adr in mem.labels if low <= adr < high])
        self.lcmt = sorted([adr for adr in mem.line_comments if low <= adr < high])
        self.bcmt = sorted([adr for adr in mem.block_comments if low <= adr < high])
        self.render_mem = Render_mem(pj, fmt, ascii, ncol).render
        self.line_comment_col = mem.line_comment_col
        self.line_comment_prefix = mem.line_comment_prefix

        self.nxxx = 0
        self.cxxx = 0
        self.fo = fo

        misc.fill_gaps(pj)
        misc.fill_all_blanks(pj, all_vals=True, minsize=ncol * 2)
        a0 = low
        for i in pj.m:
            if i.hi < low:
                continue
            if i.lo >= high:
                break
            if i.lo > a0:
                self.fill_xxx(a0, i.lo)
                a0 = i.lo

            rx = i.render(pj)
            if rx is None:
                alo = pj.afmt(i.lo)
                ahi = pj.afmt(i.hi)
                self.fo.write(
                    "%s-%s [%s]\n" % (alo, ahi, i.tag))
            elif i.lo < a0:
                print("OVERLAP i.lo %x a0 %x" % (i.lo, a0), i)
                continue
            else:
                self.render_chunk(
                    i.lo, i.hi, rx=rx, lcmt=i.lcmt, pil=i.pil, compact=i.compact)
                a0 = i.hi

        if a0 < high:
            self.fill_xxx(a0, high)

        print("%d XXXs containing %d bytes" % (self.nxxx, self.cxxx))

    def fill_xxx(self, lo, hi):
        ''' Add a .XXX entry, respecting bcmt, lcmt and labels '''
        while lo < hi:
            a1 = hi
            a2 = a1
            if self.bcmt:
                a2 = min(a2, self.bcmt[0])
            if self.labels:
                a2 = min(a2, self.labels[0])
            if self.lcmt:
                a2 = min(a2, self.lcmt[0])
            if lo % self.ncol:
                a1 = min(a1, lo + self.ncol - lo % self.ncol)
            if a2 == lo:
                a1 = min(a1, lo + self.ncol)
            else:
                a1 = min(a1, a2)
            self.nxxx += 1
            self.cxxx += a1 - lo
            self.render_chunk(lo, a1, rx = ".XXX")
            lo = a1

    def render_chunk(
        self,
        lo,
        hi,
        rx=".XXX",
        lcmt="",
        pil=None,
        compact=False
    ):
        rx = rx.strip().split("\n")
        lx = lcmt.split("\n")
        px = []
        if self.pil and pil is not None:
            px = pil.render().split("\n")

        sc = set()
        while self.bcmt and self.bcmt[0] < hi:
            sc.add(self.bcmt.pop(0))
        while self.labels and self.labels[0] < hi:
            sc.add(self.labels.pop(0))
        while self.lcmt and self.lcmt[0] < hi:
            sc.add(self.lcmt.pop(0))
        if compact is not None:
            for a in sorted(sc):
                if a != lo:
                    self.render_subchunk(lo, a, False, compact, rx, px, lx)
                lo = a
        self.render_subchunk(lo, hi, True, compact, rx, px, lx)

    def render_subchunk(self, lo, hi, last, compact, rx, px, lx):
        cmt = self.pj.m.get_block_comments(lo)
        if cmt is not None:
            w = self.line_comment_col - len(self.line_comment_prefix)
            self.fo.write(self.line_comment_prefix + "-" * w + "\n")
            self.fo.write(self.line_comment_prefix)
            self.fo.write(cmt.replace("\n",
                "\n" + self.line_comment_prefix))
            self.fo.write("-" * w + "\n")

        alx = self.pj.m.get_line_comment(lo)
        if alx:
            lx =  alx.split("\n") + lx

        if last and (compact or compact is None):
            m = max(len(rx), len(px), len(lx), 1)
        else:
            m = 9e9

        hx = self.render_mem(self.pj, lo, hi, m)
        hl = len(hx[0][1] + "\t")
        shx = "\t" * (hl // 8)

        lbl = self.pj.get_labels(lo)
        if lbl:
            s = set()
            for x in lbl:
                if x not in s:
                    s.add(x)
                    self.fo.write("%s\t%s:\n" % (shx, x))
        while True:
            hy = hx.pop(0)[1] if hx else ""
            if not last and not hy:
                break
            ry = rx.pop(0).rstrip() if rx else ""
            py = px.pop(0).rstrip() if px else ""
            ly = lx.pop(0).rstrip() if lx else ""
            if not hy and not ry and not py and not ly:
                break
            if compact and not ry and not py and not ly:
                break
            if hy:
                t = hy + "\t\t"
            else:
                t = shx + "\t\t"

            t += ry + "\t"
            l = len(t.expandtabs())
            if l < 32:
                t += "\t" * ((32 - l) // 8)

            if ly:
                t += "\t"
                l = len(t.expandtabs()) 
                if l < self.pj.m.line_comment_col:
                    t += "\t" * ((self.pj.m.line_comment_col - l) // 8)
                t += self.line_comment_prefix + ly

            if self.pil and py:
                t += "\t"
                l = len(t.expandtabs()) 
                if l < self.pil_col:
                    t += "\t" * ((self.pil_col - l) // 8)
                t += "| " + py + "\t"

            self.fo.write(t + "\n")

def Listing(pj, fn=None, **kwargs):
    if fn is None:
        fn = "/tmp/_." + pj.name + ".txt"
    print("Listing into", fn)
    fo = open(fn, "w")
    sep = ""
    for mem, low, high in pj.m.segments():
        print("SEG %x-%x" % (low, high), mem)
        fo.write(sep)
        Seg_Listing(pj, fo, mem, low, high, **kwargs)
        sep = "\n" + "-" * 80 + "\n\n"
