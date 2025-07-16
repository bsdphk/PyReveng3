#!/usr/bin/env python3
#
# Copyright (c) 2012-2025 Poul-Henning Kamp <phk@phk.freebsd.dk>
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
This class implements a basic recursive split-in-the-middle-interval-tree

An interval-tree is a tree of intervals (duh!) which is useful here
for keeping track of the bits we have taken apart.

Leafs must have numerical .lo and .hi attributes.

Instantiating the tree you must provide the valid [lo...hi] interval.

There is also an optional parameter to limit how narrow ranges we
create subtrees for.  If it ever needs changing, we should probably
change the algorithm to split trees based on actual number of nodes,
rather than the interval they cover, but for now it seems to work
pretty ok.
'''

class BinTreeLeaf():
    '''
    Base-class for the leaves of the tree
    -------------------------------------

    You will be creating a LOT of these, so keep them cheap.
    '''
    def __init__(self, lo: int, hi: int):
        assert lo < hi
        self.lo = lo
        self.hi = hi

    def __len__(self):
        return self.hi - self.lo

    def __repr__(self):
        return "<Leaf 0x%x-0x%x>" % (self.lo, self.hi)

    def __lt__(self, other):
        if self.lo != other.lo:
            return self.lo < other.lo
        return self.hi < other.hi

    def __eq__(self, other):
        if other is None:
            return False
        return self.lo == other.lo and self.hi == other.hi

    def __contains__(self, adr):
        return self.lo <= adr < self.hi

class BinTreeBranch():

    '''
    Root&branch class of the tree
    -----------------------------
    '''

    # Tuning: Do not create branches smaller than this.
    LOWER_LIMIT = 128

    def __init__(self, lo, hi):
        self.lo = lo
        self.mid = (lo + hi) // 2
        self.hi = hi
        self.less = None
        self.more = None
        self.cuts = []
        self.isbranch = (hi - lo) > self.LOWER_LIMIT

    def __repr__(self):
        return "<Branch 0x%x-0x%x-0x%x>" % (self.lo, self.mid, self.hi)

    def insert(self, leaf):
        ''' You guessed it... '''
        assert isinstance(leaf, BinTreeLeaf)
        assert leaf.lo < leaf.hi
        if not self.isbranch:
            self.cuts.append(leaf)
        elif leaf.hi <= self.mid:
            if self.less is None:
                self.less = BinTreeBranch(self.lo, self.mid)
            self.less.insert(leaf)
        elif leaf.lo >= self.mid:
            if self.more is None:
                self.more = BinTreeBranch(self.mid, self.hi)
            self.more.insert(leaf)
        else:
            self.cuts.append(leaf)

    def find(self, lo=None, hi=None):
        ''' Find leaves between lo and hi '''
        assert lo is not None or hi is not None
        if hi is None:
            hi = lo + 1
        if lo is None:
            lo = hi - 1
        if lo <= self.mid and self.less:
            yield from self.less.find(lo, hi)
        for i in self.cuts:
            if i.lo < hi and lo < i.hi:
                yield i
        if hi >= self.mid and self.more:
            yield from self.more.find(lo, hi)

    def __iter__(self):
        ''' Iterate in order of .lo and narrow before wider. '''
        stk = [self]
        lst = []
        while stk:
            cur = stk.pop()
            while lst and lst[0].lo < cur.lo:
                yield lst.pop(0)
            lst.extend(cur.cuts)
            lst.sort()
            if cur.more:
                stk.append(cur.more)
            if cur.less:
                stk.append(cur.less)
            else:
                while lst and lst[0].lo < cur.mid:
                    yield lst.pop(0)
        yield from lst

class BinTree(BinTreeBranch):
    ''' The root of the tree '''

    def __repr__(self):
        return "<Tree 0x%x-0x%x-0x%x>" % (self.lo, self.mid, self.hi)

    def gaps(self):
        ''' Yield all the gaps in the tree '''
        last = 0
        for i in self:
            if i.lo > last:
                yield (last, i.lo)
            last = i.hi
        if last < self.hi:
            yield (last, self.hi)

def test_tree():
    ''' Minimal test cases '''

    print("Testing tree class")
    oak = BinTree(0, 0x500)

    # Super items
    oak.insert(BinTreeLeaf(0x100, 0x400))
    oak.insert(BinTreeLeaf(0x100, 0x300))
    oak.insert(BinTreeLeaf(0x200, 0x400))

    # Same items
    oak.insert(BinTreeLeaf(0x200, 0x300))

    # Sub items
    oak.insert(BinTreeLeaf(0x210, 0x290))
    oak.insert(BinTreeLeaf(0x200, 0x299))
    oak.insert(BinTreeLeaf(0x201, 0x300))

    # Skew items
    oak.insert(BinTreeLeaf(0x100, 0x299))
    oak.insert(BinTreeLeaf(0x201, 0x400))

    low = 0
    length = 0
    slo = set()
    shi = set()
    dlo = {}
    dhi = {}

    for i in oak:
        assert i.lo > low or i.hi - i.lo >= length
        low = i.lo
        length = i.hi - i.lo
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

    for j in oak.find(0x200, 0x299):
        assert j.lo < 0x299
        assert j.hi > 0x200
    print("  .find() OK")

    print("Happy")

if __name__ == "__main__":

    test_tree()
