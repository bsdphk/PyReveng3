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


"""
This class implements a basic recursive split-in-the-middle-interval-tree

An interval-tree is a tree of intervals (duh!) which is useful here
for keeping track of the bits we have taken apart.

The objects you put into the tree must come with numerical .lo and
.hi attributes, but you get to define the class(es) for that in
your own code.

Instantiating the tree you must provide the valid [lo...hi] interval.

There is also an optional parameter to limit how narrow ranges we
create subtrees for.  If it ever needs changing, we should probably
change the algorithm to split trees based on actual number of nodes,
rather than the interval they cover, but for now it seems to work
pretty ok.
"""

class Tree():
    def __init__(self, lo, hi, lim=128):
        # lim is only a performance parameter, it does not change
        # funcationality in any way.
        self.lo = lo
        self.mid = (lo + hi) // 2
        self.hi = hi
        self.lim = lim
        self.less = None
        self.more = None
        self.cuts = list()
        self.leaf = (hi - lo) <= lim

    def __repr__(self):
        return "<Tree 0x%x-0x%x-0x%x>" % (self.lo, self.mid, self.hi)

    def insert(self, o):
        """
        You guessed it...
        """
        assert o.lo < o.hi
        if o.hi <= self.mid and not self.leaf:
            if self.less is None:
                self.less = Tree(self.lo, self.mid, self.lim)
            self.less.insert(o)
        elif o.lo >= self.mid and not self.leaf:
            if self.more is None:
                self.more = Tree(self.mid, self.hi, self.lim)
            self.more.insert(o)
        else:
            self.cuts.append(o)

    def find(self, lo=None, hi=None):
        ''' iterate over leaves between lo and hi '''
        assert lo is not None or hi is not None
        if hi is None:
            hi = lo + 1
        if lo is None:
            lo = hi - 1
        if lo <= self.mid and self.less is not None:
            yield from self.less.find(lo, hi)
        for i in self.cuts:
            if i.lo < hi and i.hi > lo:
                yield i
        if hi >= self.mid and self.more is not None:
            yield from self.more.find(lo, hi)

    def find_range(self, lo, hi, lst=None):
        """
        Return four lists of objects:
            Objects which the range is inside
            Objects identical to the range
            Objects inside than the range
            Objects which are both inside and outside the range
        """
        assert lo < hi
        if lst is None:
            lst = [[], [], [], []]
        if lo < self.mid and self.less is not None:
            self.less.find_range(lo, hi, lst)
        for i in self.cuts:
            if i.hi <= lo or i.lo >= hi:
                continue
            if lo == i.lo and hi == i.hi:
                lst[1].append(i)
            elif lo >= i.lo and hi <= i.hi:
                lst[0].append(i)
            elif lo <= i.lo and hi >= i.hi:
                lst[2].append(i)
            else:
                lst[3].append(i)
        if hi > self.mid and self.more is not None:
            self.more.find_range(lo, hi, lst)
        return lst

    def find_hi(self, hi, lst=None):
        """
        Return list of objects with given .hi
        """
        if lst is None:
            lst = []
        if hi <= self.mid and self.less is not None:
            self.less.find_hi(hi, lst)
        for i in self.cuts:
            if hi == i.hi:
                lst.append(i)
        if hi > self.mid and self.more is not None:
            self.more.find_hi(hi, lst)
        return lst

    def __iter__(self):
        """
        Iterate in order of .lo and narrow before wider.
        """
        stk = [self]
        lst = []
        while stk:
            cur = stk.pop()
            while lst and lst[0].lo < cur.lo:
                yield lst.pop(0)
            lst.extend(cur.cuts)
            if cur.more is not None:
                stk.append(cur.more)
            if cur.less is not None:
                stk.append(cur.less)
            else:
                lst.sort(key=lambda x: (x.lo, x.lo - x.hi))
                while lst and lst[0].lo < cur.mid:
                    yield lst.pop(0)
        while lst:
            yield lst.pop(0)

def test_tree():
    # Minimal test cases

    class Leaf():
        def __init__(self, lo, hi, tag):
            self.lo = lo
            self.hi = hi
            self.tag = tag

        def __repr__(self):
            return "%x..%x %s" % (self.lo, self.hi, self.tag)

    print("Testing tree class")
    it = Tree(0, 0x500, 1)

    # Super items
    it.insert(Leaf(0x100, 0x400, 0))
    it.insert(Leaf(0x100, 0x300, 0))
    it.insert(Leaf(0x200, 0x400, 0))

    # Same items
    it.insert(Leaf(0x200, 0x300, 1))

    # Sub items
    it.insert(Leaf(0x210, 0x290, 2))
    it.insert(Leaf(0x200, 0x299, 2))
    it.insert(Leaf(0x201, 0x300, 2))

    # Skew items
    it.insert(Leaf(0x100, 0x299, 3))
    it.insert(Leaf(0x201, 0x400, 3))

    la = 0
    ll = 0
    slo = set()
    shi = set()
    dlo = dict()
    dhi = dict()
    for i in it:
        assert i.lo > la or i.hi - i.lo < ll
        la = i.lo
        ll = i.hi - i.lo
        slo.add(i.lo)
        shi.add(i.hi)
        if i.lo not in dlo:
            dlo[i.lo] = 1
        else:
            dlo[i.lo] += 1
        if i.hi not in dhi:
            dhi[i.hi] = 1
        else:
            dhi[i.hi] += 1

    print("  .__iter__() OK")

    for i in slo:
        lst = it.find_lo(i)
        for j in lst:
            assert j.lo == i
        assert len(lst) == dlo[i]
    print("  .find_lo() OK")

    for i in shi:
        lst = it.find_hi(i)
        for j in lst:
            assert j.hi == i
        assert len(lst) == dhi[i]
    print("  .find_hi() OK")

    lst = it.find_range(0x200, 0x300)
    for i in range(4):
        for j in lst[i]:
            assert j.tag == i
    print("  .find_range() OK")

    print("Happy")

if __name__ == "__main__":

    test_tree()
