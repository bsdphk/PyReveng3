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

Leafs must have numerical .lo and .hi attributes.

Instantiating the tree you must provide the valid [lo...hi] interval.

There is also an optional parameter to limit how narrow ranges we
create subtrees for.  If it ever needs changing, we should probably
change the algorithm to split trees based on actual number of nodes,
rather than the interval they cover, but for now it seems to work
pretty ok.
"""

class TreeLeaf():
    """
    These are the leaves we hang into the tree class.

    Many datatypes will sub-type this class and add functionality
    """
    def __init__(self, lo, hi):
        assert isinstance(lo, int)
        assert isinstance(hi, int)
        assert lo < hi
        self.lo = lo
        self.hi = hi

    def __repr__(self):
        s = "<tree_leaf 0x%x-0x%x" % (self.lo, self.hi)
        return s + ">"

    def __lt__(self, other):
        if self.lo != other.lo:
            return self.lo < other.lo
        return self.hi < other.hi

    def __eq__(self, other):
        return self.lo == other.lo and self.hi != other.hi

    def __contains__(self, a):
        return self.lo <= a < self.hi

class Tree():

    limit = 128

    def __init__(self, lo, hi):
        # lim is only a performance parameter, it does not change
        # funcationality in any way.
        self.lo = lo
        self.mid = (lo + hi) // 2
        self.hi = hi
        self.less = None
        self.more = None
        self.cuts = list()
        self.isbranch = (hi - lo) > self.limit

    def __repr__(self):
        return "<Tree 0x%x-0x%x-0x%x>" % (self.lo, self.mid, self.hi)

    def insert(self, leaf):
        """
        You guessed it...
        """
        assert isinstance(leaf, TreeLeaf)
        assert leaf.lo < leaf.hi
        if not self.isbranch:
            self.cuts.append(leaf)
        elif leaf.hi <= self.mid:
            if self.less is None:
                self.less = Tree(self.lo, self.mid)
            self.less.insert(leaf)
        elif leaf.lo >= self.mid:
            if self.more is None:
                self.more = Tree(self.mid, self.hi)
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
            lst.sort()
            if cur.more:
                stk.append(cur.more)
            if cur.less:
                stk.append(cur.less)
            else:
                while lst and lst[0].lo < cur.mid:
                    yield lst.pop(0)
        yield from lst

def test_tree():
    # Minimal test cases

    print("Testing tree class")
    it = Tree(0, 0x500)

    # Super items
    it.insert(TreeLeaf(0x100, 0x400))
    it.insert(TreeLeaf(0x100, 0x300))
    it.insert(TreeLeaf(0x200, 0x400))

    # Same items
    it.insert(TreeLeaf(0x200, 0x300))

    # Sub items
    it.insert(TreeLeaf(0x210, 0x290))
    it.insert(TreeLeaf(0x200, 0x299))
    it.insert(TreeLeaf(0x201, 0x300))

    # Skew items
    it.insert(TreeLeaf(0x100, 0x299))
    it.insert(TreeLeaf(0x201, 0x400))

    la = 0
    ll = 0
    slo = set()
    shi = set()
    dlo = dict()
    dhi = dict()

    for i in it:
        assert i.lo > la or i.hi - i.lo >= ll
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

    for j in it.find(0x200, 0x299):
        assert j.lo < 0x299
        assert j.hi > 0x200
    print("  .find() OK")

    print("Happy")

if __name__ == "__main__":

    test_tree()
