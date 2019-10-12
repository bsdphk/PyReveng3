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

from . import mem, data

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
    def __init__(
        self,
        asp,
        fn=None,
        fo=None,
        lo=None,
        hi=None,
        ncol=None,
        pil=False,
        hide_undone=False,
    ):
        self.asp = asp

        if lo is None:
            lo = asp.lo
        if hi is None:
            hi = asp.hi
        self.lo = lo
        self.hi = hi
        self.pil = pil
        self.hide_undone = hide_undone

        assert not fo or not fn
        if not fo:
            print("Listing", asp, "to", fn, asp.afmt(self.lo) + "-" + asp.afmt(self.hi))
            fo = open(fn, "w")
        self.fo = fo

        self.in_seg = None
        if ncol is None:
            ncol = self.asp.ncol
        self.ncol = ncol
        self.blanks = ncol * 2

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

        self.plan = []
        self.plan += [[lo, 0, self.plan_seg, 1, asp] for asp, lo, _hi in asp.segments()]
        self.plan += [[hi, 0, self.plan_seg, 0, asp] for asp, _lo, hi in asp.segments()]
        self.plan += [[adr, 1, self.plan_bcmt] for adr, _l in asp.get_all_block_comments() if self.inside(adr)]
        self.plan += [[adr, 2, self.plan_label, l] for adr, l in asp.get_all_labels() if self.inside(adr)]
        self.plan += [[adr, 3, self.plan_lcmt] for adr, _l in asp.get_all_line_comments() if self.inside(adr)]
        self.plan += [[leaf.lo, 4, self.plan_leaf, leaf] for leaf in asp if self.inside(leaf.lo) and isinstance(leaf, data.Range)]
        self.plan += [[leaf.lo, 5, self.plan_leaf, leaf] for leaf in asp if self.inside(leaf.lo) and not isinstance(leaf, data.Range)]

        self.start = False
        last = 0
        self.lcmts = []
        prev = None
        for i in sorted(self.plan):
            a = self.asp.afmt(i[0])
            # print("P", a, i[2].__doc__, i[3:])
            if i[0] < last:
                print("OVERLAP")
                print(" last ", self.asp.afmt(last))
                print(" prev ", prev[2].__doc__, prev[3:])
                print(" this ", a)
                print(" what ", i[2].__doc__, i[3:])
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
        fo.flush()

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
            if j is None or not 0x20 < j < 0x7f:
                t += ' '
            else:
                t += '%c' % j
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

    def gap2(self, lo, hi):
        if self.hide_undone:
            self.format(lo, hi, [".XXX[0x%x]" % (hi - lo),], None, True)
        else:
            r = lo % self.ncol
            if r:
                i = min(lo + self.ncol - r, hi)
                self.format(lo, i, [".XXX",], None, False)
                lo = i
            if lo != hi:
                self.format(lo, hi, [".XXX",], None, False)

    def gap1(self, s, r, lo, a):
        if a is None:
            self.format(s, lo, [".UNDEF\t0x%x" % (lo - s),], None, True)
        elif lo - r >= self.blanks:
            if s != r:
                self.gap2(s, r)
            self.format(r, lo, [".BLANK\t" + self.asp.dfmt(r) + "[0x%x]" % (lo - r),], None, True)
        else:
            self.gap2(s, lo)

    def gap(self, lo, hi):
        self.purge_lcmt()
        if not self.in_seg:
            return hi
        try:
            c = self.asp[lo]
            a = c * 0
        except mem.MemError:
            c = None
            a = None
        s = lo
        r = lo
        while lo < hi:
            try:
                d = self.asp[lo]
                b = d * 0
            except mem.MemError:
                d = None
                b = None
            if a != b:
                self.gap1(s, r, lo, a)
                a = b
                s = lo
                r = lo
                c = d
            elif c != d:
                if lo - r >= self.blanks:
                    self.gap1(s, r, lo, a)
                    s = lo
                r = lo
                c = d
            lo += 1
        if s != hi:
            self.gap1(s, r, lo, a)
        return hi

    def purge_lcmt(self):
        while self.lcmts:
            cmt = self.lcmts.pop(0)
            self.fo.write(tabto("", self.x_lcmt) + "; " + cmt + '\n')

    def inside(self, adr):
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

    def plan_leaf(self, _adr, _afmt, *args):
        '''P::Leaf'''
        leaf = args[0][0]

        if isinstance(leaf, data.Range):
            self.fo.write(self.asp.afmt(leaf.lo) + "-")
            self.fo.write(self.asp.afmt(leaf.hi) + "\t" + leaf.render() + "\n")
            return leaf.lo

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
