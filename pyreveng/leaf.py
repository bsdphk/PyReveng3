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
The Leaf class used everywhere
"""

class Leaf():
    """
    These are the leaves we hang into the tree class.

    Many datatypes will sub-type this class and add functionality
    """
    def __init__(self, lo, hi, tag):
        self.lo = lo
        self.hi = hi
        self.tag = tag
        self.pil = None
        self.lcmt = ""
        self.rendered = None
        self.compact = False
        self.aspace = None

    def __repr__(self):
        s = "<leaf 0x%x-0x%x %s" % (self.lo, self.hi, self.tag)
        return s + ">"

    def __lt__(self, other):
        if self.lo != other.lo:
            return self.lo < other.lo
        if self.hi != other.hi:
            return self.hi > other.hi

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        if self.lo != other.lo:
            return False
        if self.hi != other.hi:
            return False
        return True

    def __contains__(self, a):
        return self.lo <= a < self.hi

    def render(self):
        return self.rendered

    def arg_render(self):
        return ""
