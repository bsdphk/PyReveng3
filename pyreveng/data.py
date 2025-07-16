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
Data of various sorts
"""

import struct

from pyreveng import leaf
from pyreveng import datastruct

# Characters from text strings that go into their labels.
LABELCHAR = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789?_'

# Standard ASCII character set.
ASCII = {x : "%c" % x for x in range(32, 127)}
ASCII[10] = "\\n"
ASCII[13] = "\\r"

#######################################################################

class DataABC(leaf.Leaf):
    def __init__(self, asp, lo, hi, t="dataabc"):
        super().__init__(lo, hi, t)
        self.tree = asp

    def insert(self):
        self.tree.insert(self)
        self.commit()
        return self

    def commit(self):
        ''' called (also) when datastructure containing this is insert()'ed '''

    def render(self):
        yield "DataABC[" + ",".join(self.tree.dfmt(x) for x in range(self.lo, self.hi)) + "]"

    @classmethod
    def using(cls, **kwargs):
        return (cls, kwargs)

class Data(DataABC):
    def __init__(self, asp, lo, hi, t="data", fmt=None):
        super().__init__(asp, lo, hi, t)
        asp.insert(self)
        self.fmt = fmt

    def render(self):
        if self.rendered:
            return self.rendered
        if self.fmt:
            return self.fmt
        return "<Data %x-%x %s>" % (self.lo, self.hi, self.tag)

class Const(Data):
    def __init__(self, asp, lo, hi=None, fmt=None, func=None, size=1):
        if hi is None:
            hi = lo + 1
        super().__init__(asp, lo, hi, "const")
        if func is None:
            func = asp.__getitem__
        if fmt is None:
            fmt = "0x%x"
        self.val = []
        for a in range(lo, hi, size):
            self.val.append(func(a))
        self.fmt = ",".join(fmt % i for i in self.val)
        self.typ = ".CONST"
        self.compact = True

    def render(self):
        return self.typ + "\t" + self.fmt

class Pstruct(Data):
    ''' Uses python struct.* to untangle data '''
    def __init__(self, asp, lo, spec, fmt=None, typ=".PSTRUCT"):
        bcnt = struct.calcsize(spec)
        self.data = struct.unpack(spec, asp.bytearray(lo, bcnt))
        super().__init__(asp, lo, lo + bcnt, "const")
        self.spec = spec
        self.fmt = fmt
        self.typ = typ

    def render(self):
        if self.fmt is not None:
            return self.typ + "\t" + self.fmt % self.data
        return self.typ + "\t" + self.spec + " = " + str(self.data)

class Codeptr(Data):
    def __init__(self, asp, lo, hi, dst):
        super().__init__(asp, lo, hi, "codeptr")
        self.dst = dst

    def render(self):
        return ".CODE\t" + self.aspace.adr(self.dst)

    def arg_render(self):
        return self.aspace.adr(self.dst)

class Dataptr(Data):
    def __init__(self, asp, lo, hi, dst, dasp=None, pfx="", sfx=""):
        super().__init__(asp, lo, hi, "dataptr")
        self.dst = dst
        if dasp:
            self.dasp = dasp
        else:
            self.dasp = asp
        self.pfx = pfx
        self.sfx = sfx

    def render(self):
        return ".PTR\t" + self.pfx + self.dasp.adr(self.dst) + self.sfx

class StringPtr(Data):
    def __init__(self, asp, lo, hi, dst, *args, **kwargs):
        super().__init__(asp, lo, hi, "stringptr")
        self.dst = dst
        if dst == 0:
            self.txt = None
            return
        for i in asp.find(lo=self.dst):
            t = getattr(i, "txt", None)
            if t:
                self.txt = i.txt
                return
        t = Txt(asp, self.dst, *args, **kwargs)
        self.txt = t.txt

    def render(self):
        if self.txt is None:
            return ".STRPTR\tNULL"
        return ".STRPTR\t" + "»" + self.txt + "«"

def stringify(asp, lo, length=None, term=None, charset=None):
    if term is None:
        term = (0,)
    if not charset:
        charset = ASCII
    s = ""
    while True:
        x = asp[lo]
        lo += 1
        if length is None and x in term:
            return lo, s
        t = charset.get(x)
        if t:
            s += t
        else:
            s += "\\x%02x" % x
        if length is not None:
            length -= 1
            if length == 0:
                return lo, s

class Text(DataABC):

    def __init__(
        self,
        asp,
        lo,
        hi=None,
        width=None,
        label=False,
        pfx=None,
        align=1,
        splitnl=False,
        **kwargs
    ):
        self.splitnl = splitnl
        if hi is None and width is not None:
            hi = lo + width
        self.pre = ""
        if pfx == 1:
            x = asp[lo]
            self.pre = '%d,' % x
            hi, s = stringify(asp, lo + 1, length=x, **kwargs)
            while hi % align:
                hi += 1
        elif pfx is not None:
            raise Exception("unknown pfx")
        elif hi is None:
            hi, s = stringify(asp, lo, **kwargs)
            while hi % align:
                hi += 1
        else:
            hi, s = stringify(asp, lo, hi - lo, **kwargs)

        super().__init__(asp, lo, hi, "txt")
        self.txt = s
        self.fmt = "'" + s + "'"
        if label and s.strip() == "":
            lbl = 't_%d*SP' % len(s)
            asp.set_label(lo, lbl)
        elif label:
            lbl = 't_'
            for i in s:
                if i in LABELCHAR:
                    lbl += i
                elif lbl[-1] != '_':
                    lbl += '_'
            asp.set_label(lo, lbl)
        self.compact = True

    def render(self):
        if not self.splitnl:
            yield ".TXT\t" + self.pre + "'" + self.txt + "'"
            return

        l = self.txt.split('\\n')
        if len(l) == 1:
            yield ".TXT\t" + self.pre + "'" + self.txt + "'"
            return

        txt = ''
        p = self.pre

        for i in l[:]:
            yield '.TXT\t' + p + "'" + i + "\\n'"

    def arg_render(self):
        return "'" + self.txt + "'"

class Txt(Text):

    def __init__(self, *args, label=True, **kwargs):
        super().__init__(*args, label=label, **kwargs)
        self.insert()

    def render(self):
        return "\n".join(super().render())


#######################################################################

class Bu8(DataABC):
    def __init__(self, asp, lo):
        super().__init__(asp, lo, lo+1)
        self.val = asp[lo]

    def render(self):
        yield "0x%02x" % self.val

class Bu16(DataABC):
    def __init__(self, asp, lo):
        super().__init__(asp, lo, lo+2)
        self.val = self.tree.bu16(self.lo)

    def render(self):
        yield "0x%04x" % self.val

class Bu32(DataABC):
    def __init__(self, asp, lo):
        super().__init__(asp, lo, lo+4)
        self.val = self.tree.bu32(self.lo)

    def render(self):
        yield "0x%08x" % self.val

class Struct(datastruct.Struct, DataABC):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, naked=True, **kwargs)

    def number_field(self, offset, width):
        return DataABC(self.tree, offset, offset + width, t="struct")

    def base_init(self, **kwargs):
        DataABC.__init__(self, self.tree, self.lo, hi=self.hi, **kwargs)

def Array(count, what, **kwargs):
    return datastruct.Array(Struct, count, what, **kwargs)

class Pointer(DataABC):

    NOWHERE=(0,)

    def __init__(self, *args, target=None, **kwargs):
        assert isinstance(self.dst, int)
        super().__init__(*args, **kwargs)
        self.target = target

    def render(self):
        if self.dst in self.NOWHERE:
            yield self.tree.apct % self.dst
        else:
            yield self.tree.adr(self.dst)

    def commit(self):
        if self.target is None:
            return
        if self.dst in self.NOWHERE:
            return
        for obj in self.tree.find(self.dst):
            if isinstance(obj, self.target):
                return
        self.target(self.tree, self.dst).insert()

    @classmethod
    def to(cls, target):
        return (cls, {"target": target})
