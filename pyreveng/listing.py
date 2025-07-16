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

import sys
import random

from pyreveng import mem

def tabto(s, n):
    ln = len(s.expandtabs())
    if ln < n:
        s += "\t" * ((7 + n - ln) // 8)
    return s

def tolines(s):
    s = s.split('\n')
    while s and not s[0]:
        s.pop(0)
    while s and not s[-1]:
        s.pop(-1)
    return s

class List():
    def __init__(self, lst, lo, hi, pri):
        self.lst = lst
        self.lo = lo
        self.hi = hi
        self.pri = pri

    def __lt__(self, other):
        return (self.lo, self.pri) < (other.lo, other.pri)

    def __repr__(self):
        return "<List (%s) %x-%x>" % (str(self.__class__), self.lo, self.hi)

    def render(self, _fo, _lst):
        print("NO render", self)

    def afmt(self, a=None):
        if a is None:
            a = self.lo
        return self.lst.asp.afmt(a)

class ListSegmentStart(List):
    def __init__(self, lst, lo, asp):
        super().__init__(lst, lo, lo, 11)
        self.asp = asp

    def render(self, fo, _lst):
        self.lst.purge_lcmt()
        if self.lst.in_seg is not None:
            fo.write('\n')
            fo.write('-' * 80 + '\n')
            fo.write('\n')
        self.lst.in_seg = True

class ListSegmentEnd(List):
    def __init__(self, lst, hi, asp):
        super().__init__(lst, hi, hi, 10)
        self.asp = asp

    def render(self, _fo, _lst):
        self.lst.purge_lcmt()
        self.lst.in_seg = False

class ListRangeStart(List):
    def __init__(self, lst, rng):
        super().__init__(lst, rng.lo, rng.lo, 21)
        self.rng = rng

    def render(self, fo, lst):
        self.lst.purge_lcmt()
        if self.rng.indent:
            lst.nindent += 1
        r = self.rng
        if self.rng.visible:
            fo.write(
                "%s-%s\t%s\n" % (
                    self.afmt(r.lo),
                    self.afmt(r.hi),
                    r.txt,
                )
            )

class ListRangeEnd(List):
    def __init__(self, lst, rng):
        super().__init__(lst, rng.hi, rng.hi, 20)
        self.rng = rng

    def render(self, _fo, lst):
        self.lst.purge_lcmt()
        if self.rng.indent:
            lst.nindent -= 1

class ListBlockComment(List):
    def __init__(self, lst, lo):
        super().__init__(lst, lo, lo, 30)

    def render(self, fo, _lst):
        self.lst.purge_lcmt()
        fo.write(self.afmt() + " ; " + "-" * 86 + "\n")
        for i in self.lst.asp.get_block_comments(self.lo):
            for ln in tolines(i):
                fo.write(self.afmt() + " ; " + ln.rstrip() + "\n")
        fo.write(self.afmt() + " ; " + "-" * 86 + "\n")

class ListLineComment(List):
    def __init__(self, lst, lo, lcmt):
        super().__init__(lst, lo, lo, 50)
        self.lcmt = set(lcmt)

    def render(self, _fo, _lst):
        for i in sorted(self.lcmt):
            for j in tolines(i):
                self.lst.lcmts.append(j.rstrip())

class ListLabel(List):

    def __init__(self, lst, lo, lbl):
        super().__init__(lst, lo, lo, 40)
        self.lbl = lbl

    def render(self, fo, _lst):
        self.lst.purge_lcmt()
        for lbl in sorted(self.lst.asp.get_labels(self.lo)):
            fo.write(tabto(self.afmt(), self.lst.x_label) + lbl.strip() + ":" + "\n")

class ListLeaf(List):

    def __init__(self, lst, leaf):
        super().__init__(lst, leaf.lo, leaf.hi, 60)
        self.leaf = leaf

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.lo == other.lo and self.hi == other.hi and self.leaf.render() == other.leaf.render() and self.leaf.lcmt == other.leaf.lcmt

    def render(self, fo, _lst):
        if self.leaf.lcmt:
            self.lst.purge_lcmt()
            for i in tolines(self.leaf.lcmt):
                self.lst.lcmts.append(i.rstrip())

        if self.lst.pil and self.leaf.pil:
            pil = tolines(self.leaf.pil.render())
        else:
            pil = None

        g = self.leaf.render()
        if isinstance(g, str):
            lines = tolines(g)
        else:
            lines = list(g)
        return self.lst.format(
            fo,
            self.lo,
            self.hi,
            lines,
            pil,
            self.leaf.compact,
        )


class Listing():
    def __init__(self, asp, **kwargs):
        self.asp = asp

        for an, dv in dict(
            fn=None,
            fo=None,
            lo=None,
            hi=None,
            ncol=None,
            pil=False,
            charset=None,
            align_xxx=False,
            compact_xxx=False,
            align_blank=False,
            blanks=None,
            leaf_width=32,
            indent='┆ ',
            wordspace=' ',
        ).items():
            setattr(self, an, kwargs.pop(an) if an in kwargs else dv)
        assert not kwargs, "Surplus kwargs: " + str(kwargs)
        self.nindent = 0

        assert not self.fo or not self.fn

        if self.charset is None:
            self.charset = [' '] * 256
            for i in range(0x20, 0x7f):
                self.charset[i] = '%c' % i
        # assert len(self.charset) == 256    XXX: should be wordsize ?

        if self.lo is None:
            self.lo = asp.lo
        if self.hi is None:
            self.hi = asp.hi

        if not self.fo:
            print("Listing", asp, "to", self.fn, asp.afmt(self.lo) + "-" + asp.afmt(self.hi))
            self.fo = open(self.fn, "w")

        self.in_seg = None
        if self.ncol is None:
            self.ncol = 4
        if self.blanks is None:
            self.blanks = self.ncol * 2

        # Find the width of the address+data column by probing one leaf
        # in each mapped address space
        votes = set()
        votes.add(8)
        for map, i, j in self.asp.segments():
            for n, leaf in enumerate(map):
                a0 = leaf.lo + i
                try:
                    votes.add(
                        len(
                            (
                                self.fmt_adr(a0, a0 + self.ncol) +
                                "\t"
                            ).expandtabs()
                        )
                    )
                    break
                except mem.MemError:
                    continue
        self.x_label = max(votes)

        self.x_leaf = self.x_label + 8
        self.x_lcmt = self.x_leaf + self.leaf_width
        self.x_pil = self.x_lcmt + 16
        t = tabto("", self.x_label) + "|LABEL"
        t = tabto(t, self.x_leaf) + "|LEAF"
        t = tabto(t, self.x_lcmt) + "|LCMT"
        if self.pil:
            t = tabto(t, self.x_pil) + "|PIL"
        # fo.write(t + '\n')


        self.plan = [
            ListSegmentStart(self, lo, asp) for asp, lo, _hi in asp.segments()
        ] + [
            ListSegmentEnd(self, hi, asp) for asp, _lo, hi in asp.segments()
        ] + [
            ListRangeStart(self, r) for r in asp.ranges()
        ] + [
            ListRangeEnd(self, r) for r in asp.ranges()
        ] + [
            ListBlockComment(self, adr) for adr, _l in asp.get_all_block_comments() if adr in self
        ] + [
            ListLabel(self, adr, l) for adr, l in asp.get_all_labels() if adr in self
        ] + [
            # XXX: this unintentionally sorts linecomments by contents
            ListLineComment(self, adr, l) for adr, l in asp.get_all_line_comments() if adr in self
        ] + [
            ListLeaf(self, leaf) for leaf in asp if leaf.lo in self
        ]

        self.start = False
        last = 0
        self.lcmts = []
        prev = None
        for i in sorted(self.plan):
            if i == prev:
                # print("DUP", i, prev)
                continue
            if i.lo < last:
                print("")
                print("OVERLAP")
                print("prev:", prev)
                prev.render(sys.stdout, self)
                print("this:", i)
                i.render(sys.stdout, self)
                continue
            prev = i
            while i.lo > last:
                last = self.gap(last, i.lo)
            last = i.hi
            if self.lo <= i.lo and i.hi <= self.hi:
                i.render(self.fo, self)
        self.fo.flush()

    def fmt_adr(self, lo, hi):
        t = self.asp.afmt(lo) + " "
        s = []
        w = []
        for _k in range(self.ncol):
            if lo < hi:
                x = self.asp.dfmt(lo)
                w.append(x)
                y = self.asp.tfmt(lo)
                s += y
            else:
                w.append(" " * len(x))
                s += [None] * len(y)
            lo += 1
        t += self.wordspace.join(w)
        if self.charset:
            t += "  |"
            for j in s:
                if j is not None:
                    t += self.charset[j]
                else:
                    t += ' '
            t += "|"
        return t

    def format(self, fo, lo, hi, leaf, pil, compact=True):
        lines = len(leaf)
        if compact is None:
            pass
        elif not compact:
            lines = max(lines, ((self.ncol - 1) + hi - lo) // self.ncol)
        if pil:
            lines = max(lines, len(pil))
        assert lines > 0

        for _i in range(lines):
            if lo < hi:
                j = min(lo + self.ncol, hi)
                t = self.fmt_adr(lo, min(j, hi))
                lo = j
            else:
                t = ''
            if leaf:
                t = tabto(t, self.x_leaf) + self.indent * self.nindent + leaf.pop(0).rstrip()
            if self.lcmts:
                t = tabto(t, self.x_lcmt) + "; " + self.lcmts.pop(0)
            if pil:
                t = tabto(t, self.x_pil) + "| " + pil.pop(0)
            fo.write(t + '\n')
            self.purge_lcmt()
            fo.flush()
        return hi

    def gap1(self, lo, hi, c):
        assert lo != hi, "%x-%x" % (lo, hi)
        if c is None:
            self.format(self.fo, lo, hi, [".XXX" + "[0x%x]" % (hi - lo),], None, self.compact_xxx)
        else:
            self.format(self.fo, lo, hi, [".BLANK\t" + self.asp.dfmt(lo) + "[0x%x]" % (hi - lo),], None, True)

    def gap0(self, lo, hi, c):
        assert lo != hi, "%x-%x" % (lo, hi)
        if lo // self.ncol == hi // self.ncol:
            self.gap1(lo, hi, c)
            return
        if (c is None and self.align_xxx) or (c is not None and self.align_blank):
            if lo % self.ncol:
                a = lo + self.ncol - lo % self.ncol
                self.gap1(lo, a, c)
                lo = a
            if hi % self.ncol:
                a = hi - hi % self.ncol
                if lo < a:
                    self.gap1(lo, a, c)
                    lo = a
        if lo != hi:
            self.gap1(lo, hi, c)

    def gap_undef(self, lo, hi):
        self.format(self.fo, lo, hi, [".UNDEF\t0x%x" % (hi - lo),], None, True)

    def probe(self, lo):
        try:
            x = self.asp[lo]
            return x
        except mem.MemError:
            return None

    def gap(self, lo, hi):
        '''Render unaccounted for intervals of address space'''
        self.purge_lcmt()
        if not self.in_seg:
            return hi
        s = lo
        sr = lo
        r = 1
        c = self.probe(lo)
        while lo < hi:
            d = self.probe(lo)
            if d == c:
                r += 1
            elif c is None or d is None or r >= self.blanks:
                break
            else:
                c = d
                sr = lo
                r = 1
            lo += 1
        if c is None:
            self.gap_undef(s, lo)
            return lo
        lo2 = lo
        if self.align_blank and sr % self.ncol:
            sr = sr + self.ncol - sr % self.ncol
            lo2 -= lo2 % self.ncol
        if lo2 - sr >= self.blanks:
            if s != sr:
                self.gap0(s, sr, None)
            self.gap0(sr, lo2, c)
            return lo2
        self.gap0(s, lo, None)
        return lo

    def purge_lcmt(self):
        while self.lcmts:
            cmt = self.lcmts.pop(0)
            self.fo.write(tabto("", self.x_lcmt) + "; " + cmt + '\n')

    def __contains__(self, adr):
        return self.lo <= adr < self.hi

def Example(func, fn=None, **kwargs):
    nm, ms = func()
    rv = []
    if fn is not None:
        fo = open(fn, "w")
    else:
        fo = None
    for n, m in enumerate(ms):
        if fo is None:
            fno="/tmp/_%s.%02d.asm" % (nm, n)
            rv.append(fno)
            Listing(m, fn=fno, **kwargs)
        else:
            Listing(m, fo=fo, **kwargs)
    return rv
