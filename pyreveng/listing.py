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

import random

from pyreveng import mem, data, leaf

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
        ).items():
            setattr(self, an, kwargs.pop(an) if an in kwargs else dv)
        assert not kwargs, "Surplus kwargs: " + str(kwargs)

        assert not self.fo or not self.fn

        if self.charset is None:
            self.charset = [' '] * 256
            for i in range(0x20, 0x7f):
                self.charset[i] = '%c' % i
        assert len(self.charset) == 256

        if self.lo is None:
            self.lo = asp.lo
        if self.hi is None:
            self.hi = asp.hi

        if not self.fo:
            print("Listing", asp, "to", self.fn, asp.afmt(self.lo) + "-" + asp.afmt(self.hi))
            self.fo = open(self.fn, "w")

        self.in_seg = None
        if self.ncol is None:
            self.ncol = self.asp.ncol
        if self.blanks is None:
            self.blanks = self.ncol * 2

        self.x_label = None
        for _n in range(10):
            for _mem, i, j in self.asp.segments():
                try:
                    t = int(random.uniform(i, j))
                    self.x_label = len((self.fmt_adr(t, t + self.ncol) + "\t").expandtabs())
                    break
                except mem.MemError:
                    continue
            if self.x_label is not None:
                break
        self.x_leaf = self.x_label + 8
        self.x_lcmt = self.x_leaf + 32
        self.x_pil = self.x_lcmt + 40
        t = tabto("", self.x_label) + "|LABEL"
        t = tabto(t, self.x_leaf) + "|LEAF"
        t = tabto(t, self.x_lcmt) + "|LCMT"
        if self.pil:
            t = tabto(t, self.x_pil) + "|PIL"
        # fo.write(t + '\n')


        self.plan = [
            [lo, 10, self.plan_seg, 1, asp] for asp, lo, _hi in asp.segments()
        ] + [
            [hi, 10, self.plan_seg, 0, asp] for asp, _lo, hi in asp.segments()
        ] + [
            [r.lo, 20, self.plan_range, 0, r] for r in asp.ranges()
        ] + [
            [r.hi, 20, self.plan_range, 1, r] for r in asp.ranges()
        ] + [
            [adr, 30, self.plan_bcmt] for adr, _l in asp.get_all_block_comments() if adr in self
        ] + [
            [adr, 40, self.plan_label, l] for adr, l in asp.get_all_labels() if adr in self
        ] + [
            [adr, 50, self.plan_lcmt] for adr, _l in asp.get_all_line_comments() if adr in self
        ] + [
            [leaf.lo, 60, self.plan_leaf, leaf] for leaf in asp if leaf.lo in self
        ]

        self.start = False
        last = 0
        self.lcmts = []
        prev = None
        for i in sorted(self.plan):
            a = self.asp.afmt(i[0])
            if i[0] < last:
                print("OVERLAP")
                print(" last ", self.asp.afmt(last))
                print(" prev ", prev[2].__doc__, prev[3:])
                if len(prev) > 3 and isinstance(prev[3], leaf.Leaf):
                    print("\t", prev[3].render())
                print(" this ", a)
                print(" what ", i[2].__doc__, i[3:])
                if len(i) > 3 and isinstance(i[3], leaf.Leaf):
                    print("\t", i[3].render())
                if len(i) > 3 and len(prev) > 3:
                    print(" same", i[3] == i[3])
                continue
            prev = i
            while i[0] > last:
                last = self.gap(last, i[0])
            last = i[0]
            r = i[2](i[0], a, i[3:])
            if r is False:
                break
            if r is not None:
                last = r
        self.fo.flush()

    def fmt_adr(self, lo, hi):
        t = self.asp.afmt(lo) + " "
        s = []
        for _k in range(self.ncol):
            if lo < hi:
                x = self.asp.dfmt(lo)
                t += " " + x
                y = self.asp.tfmt(lo)
                s += y
            else:
                t += " " + " " * len(x)
                s += [None] * len(y)
            lo += 1
        t += "  |"
        for j in s:
            if j is not None:
                t += self.charset[j]
            else:
                t += ' '
        return t + "|"

    def format(self, lo, hi, leaf, pil, compact=True):
        lines = len(leaf)
        if compact is None:
            lines = lines
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
                t = tabto(t, self.x_leaf) + leaf.pop(0).rstrip()
            if self.lcmts:
                t = tabto(t, self.x_lcmt) + "; " + self.lcmts.pop(0)
            if pil:
                t = tabto(t, self.x_pil) + "| " + pil.pop(0)
            self.fo.write(t + '\n')
            self.fo.flush()
        return hi

    def gap1(self, lo, hi, c):
        assert lo != hi, "%x-%x" % (lo, hi)
        if c is None:
            self.format(lo, hi, [".XXX" + "[0x%x]" % (hi - lo),], None, self.compact_xxx)
        else:
            self.format(lo, hi, [".BLANK\t" + self.asp.dfmt(lo) + "[0x%x]" % (hi - lo),], None, True)

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
        self.format(lo, hi, [".UNDEF\t0x%x" % (hi - lo),], None, True)

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

    def plan_bcmt(self, adr, afmt, *_args):
        '''P:Bcmt'''
        self.purge_lcmt()
        self.fo.write(afmt + " ; " + "-" * 86 + "\n")
        for i in self.asp.get_block_comments(adr):
            for ln in tolines(i):
                self.fo.write(afmt + " ; " + ln.rstrip() + "\n")
        self.fo.write(afmt + " ; " + "-" * 86 + "\n")

    def plan_label(self, adr, afmt, *_args):
        '''P:Label'''
        self.purge_lcmt()
        s = {}
        for lbl in self.asp.get_labels(adr):
            if lbl in s:
                print("Duplicate label", afmt, lbl, s[adr])
            else:
                self.fo.write(tabto(afmt, self.x_label) + lbl.strip() + ":" + "\n")
                s[adr] = lbl

    def plan_lcmt(self, adr, _afmt, *_args):
        '''P:Lcmt'''
        self.purge_lcmt()
        for i in self.asp.get_line_comments(adr):
            for j in tolines(i):
                self.lcmts.append(i.rstrip())

    def plan_seg(self, _adr, _afmt, *args):
        '''P::Seg'''
        if args[0][0]:
            if self.in_seg is False:
                self.fo.write('\n')
                self.fo.write('-' * 80 + '\n')
                self.fo.write('\n')
            self.in_seg = True
        else:
            self.in_seg = False

    def plan_range(self, _adr, _afmt, *args):
        '''P:Range'''
        if not args[0][0]:
            r = args[0][1]
            self.fo.write(
                "%s-%s\t%s\n" % (
                    self.asp.afmt(r.lo),
                    self.asp.afmt(r.hi),
                    r.txt,
                )
            )

    def plan_leaf(self, _adr, _afmt, *args):
        '''P::Leaf'''
        leaf = args[0][0]

        if leaf.lcmt:
            self.purge_lcmt()
            for i in tolines(leaf.lcmt):
                self.lcmts.append(i.rstrip())

        if self.pil and leaf.pil:
            pil = tolines(leaf.pil.render())
        else:
            pil = None

        # print("\t", leaf.__dict__)
        return self.format(
            leaf.lo,
            leaf.hi,
            tolines(leaf.render()),
            pil,
            leaf.compact,
        )

def Example(func, **kwargs):
    nm, ms = func()
    for n, m in enumerate(ms):
        Listing(m, fn="/tmp/_%s.%02d.asm" % (nm, n), **kwargs)
