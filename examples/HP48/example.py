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
#

import os

from pyreveng import mem, listing, data
import pyreveng.cpu.saturn as saturn

import pyreveng.toolchest.bitmap as bitmap

from hp48_charset import rpl_chars
import entrydatabase


FIRMWARE_K = os.path.dirname(__file__) + "/gxrom-k.bin"
FIRMWARE_R = os.path.dirname(__file__) + "/gxrom-r.bin"

CMPMODE = False

##############################################################################

PRI_RPN_SPEC = 10
PRI_RPN = 5
PRI_ASSY = 1

class QueueItem():
    def __init__(self, *args):
        self.i = args
        self.j = str(args)

    def __lt__(self, other):
        return self.i[0] < other.i[0]

class Queue():
    def __init__(self):
        self.q1 = []
        self.q2 = []
        self.done = set()
        self.in_queue = False

    def queue(self, priority, func, *args, **kwargs):
        i = QueueItem(priority, func, args, kwargs)
        if i.j not in self.done:
            self.q1.append(i)
            self.done.add(i.j)

    def dequeue(self, level=0):
        if self.in_queue:
            return False
        if self.q1:
            self.q2 = list(sorted(self.q2 + self.q1, reverse=True))
            self.q1 = []
        elif not self.q2:
            return False
        self.in_queue = True
        rv = self.q2[0].i[0] >= level
        if rv:
            priority, func, args, kwargs = self.q2.pop(0).i
            func(*args, **kwargs)
        self.in_queue = False
        return rv

    def run(self, **kwargs):
        while self.dequeue(**kwargs):
            continue

#######################################################################

def real(asp, a):
    exp = asp.le(a, 3)
    mant = asp.le(a + 3, 12)
    sign = asp.le(a + 15, 1)
    try:
        e = int("%3x" % exp, 10)
        m = "%012x" % mant
        int(m, 10)
    except ValueError:
        return "S=%x M=%012x E=%03x" % (sign, mant, exp)
    if sign:
        t = "-"
    else:
        t = ""
    if e > 499:
         e -= 1000
    if -10 < e <= 0:
         m = "0" * -e + m
         t += m[:1] + "." + m[1:].rstrip('0')
    elif 0 < e < 10:
         m = m + "0" * e
         e = 0
         t += m[:-11] + "." + m[-11:].rstrip('0')
    else:
         t += m[:1] + "." + m[1:].rstrip('0') + "E%d" % e
    return t

#######################################################################

def longreal(asp, a):
    exp = asp.le(a, 5)
    mant = asp.le(a + 5, 15)
    sign = asp.le(a + 20, 1)
    try:
        e = int("%5x" % exp, 10)
        m = "%015x" % mant
        int(m, 10)
    except ValueError:
        return "S=%x M=%015x E=%05x" % (sign, mant, exp)
    if e > 49999:
         e -= 100000
    if sign:
        t = "-"
    else:
        t = ""
    if -10 < e <= 0:
        m = "0" * -e + m
        t += m[:1] + "." + m[1:].rstrip('0')
    elif 0 < e < 10:
        m = m + "0" * e
        t += m[:-14] + "." + m[-14:].rstrip('0')
    else:
        t += m[:1] + "." + m[1:].rstrip('0') + "E%d" % e
    return t + "L"

#######################################################################

def text(asp, a, n):
    t = ""
    for i in range(n):
        c = asp.le(a, 2)
        if 32 <= c <= 126:
            t += "%c" % c
        elif 0xa0 <= c:
            t += "%c" % c
        elif c in rpl_chars:
            t += rpl_chars[c]
        else:
            t += "\\x%02x" % c
        a += 2
    return t

#######################################################################

class Dataptr(data.Dataptr):
    def __init__(self, asp, lo, lcmt=None):
        v = asp.le(lo, 5)
        super().__init__(asp, lo, lo + 5, v)
        self.val = self.dst
        if lcmt:
            asp.set_line_comment(lo, lcmt)

class Relptr(data.Dataptr):
    def __init__(self, asp, lo, lcmt=None):
        v = asp.le(lo, 5)
        if v:
            v = (v + lo) & 0xfffff
        super().__init__(asp, lo, lo + 5, v)
        if lcmt:
            asp.set_line_comment(lo, lcmt)

    def render(self):
        if CMPMODE:
            return ".REL\t%+05x" % (self.dst - self.lo)
        else:
            return ".REL\t" + self.aspace.adr(self.dst)

class Const(data.Data):
    def __init__(self, asp, lo, n, lcmt=None):
        super().__init__(asp, lo, lo + n)
        self.val = asp.le(lo, n)
        fmt = ".CONST\t0x%%0%dx" % n
        self.rendered = fmt % self.val
        if lcmt:
            asp.set_line_comment(lo, lcmt)

#######################################################################

PFXS = {}

#######################################################################

class CachedInstance(type):
    ''' Only make a single instance of any one object '''
    _instances = {}
    def __call__(cls, *args, **kwargs):
        cx = args[0]
        lo = args[1]
        index = (cx, lo)
        if index not in cls._instances:
            cls._instances[index] = super(CachedInstance, cls).__call__(*args, **kwargs)
        return cls._instances[index]

class Object(metaclass=CachedInstance):
    ''' A HP48 Object.
    NB: .lo is the address of the object-body
    '''

    def __init__(
        self,
        cx,
        lo,
        siz=None,
        hi=None,
        prefixed=False,
        compact=False,
    ):
        self.lo = lo
        self.name = self.__class__.__name__
        if siz:
             assert hi == None or hi == lo + siz
             hi = lo + siz
        self.hi = hi
        self.prefixed = prefixed
        self.compact = compact
        if compact:
            if prefixed:
                self.y = data.Data(cx.m, self.lo - 5, self.hi)
            else:
                self.y = data.Data(cx.m, self.lo, self.hi)
            self.y.rendered = str(self)
            self.y.compact = True
        elif prefixed:
            self.pfx = data.Data(cx.m, self.lo - 5, self.lo)
            c = PFXS.get(cx.m.le(self.lo - 5, 5))
            t = "$" + self.__class__.__name__.upper()
            if c:
                pc = '$' + c.__name__.upper()
                if pc != t:
                    t = pc + " (" + t + ")"
            self.pfx.rendered = t
        if hi:
            self.set_hi(cx, hi)

    def set_hi(self, cx, hi):
        self.hi = hi
        if not self.compact:
            cx.m.add_range(
                self.lo,
                self.hi,
                txt=self.name,
                indent=not CMPMODE,
                visible=self.lo + 2000 < self.hi,
            )

    def __str__(self):
        t = "0x%05x" % self.lo
        if self.hi:
            t += "-0x%05x" % self.hi
        return t + " " + self.name

#######################################################################

class Int20(Object):

    def __init__(self, cx, lo, **kwargs):
        self.val = cx.m.le(lo, 5)
        super().__init__(cx, lo, siz=5, compact=True, **kwargs)

    def __str__(self):
        return "<%05xh>" % self.val

PFXS[0x02911] = Int20

#######################################################################

class Char(Object):

    def __init__(self, cx, lo, prefixed=False,**kwargs):
        self.txt = text(cx.m, lo, 1)
        super().__init__(cx, lo, siz=2, compact=True, prefixed=prefixed, **kwargs)

    def __str__(self):
        return "C「" + self.txt + "」"

PFXS[0x029bf] = Char

#######################################################################

class LibNam(Object):

    def __init__(self, cx, lo, prefixed=False,**kwargs):
        self.lib = cx.m.le(lo, 3)
        self.idx = cx.m.le(lo + 3, 3)
        super().__init__(cx, lo, siz=6, compact=True, prefixed=prefixed, **kwargs)

    def __str__(self):
        return "%03X%03Xh" % (self.lib, self.idx)

PFXS[0x02e92] = LibNam

#######################################################################
# 「 」

class String(Object):

    def __init__(self, cx, lo, **kwargs):
        ln = cx.m.le(lo, 5)
        self.txt = text(cx.m, lo + 5, (ln - 5) // 2)
        super().__init__(cx, lo, siz=ln, compact=True, **kwargs)

    def __str__(self):
        return "「" + self.txt + "」"

PFXS[0x02a2c] = String

#######################################################################

class LocName(Object):

    def __init__(self, cx, lo, **kwargs):
        ln = cx.m.le(lo, 2)
        self.txt = text(cx.m, lo + 2, ln)
        super().__init__(cx, lo, siz=2+2*ln, compact=True, **kwargs)

    def __str__(self):
        return "L「" + self.txt + "」"

PFXS[0x02e6d] = LocName

#######################################################################

class GlobName(Object):

    def __init__(self, cx, lo, **kwargs):
        ln = cx.m.le(lo, 2)
        self.txt = text(cx.m, lo + 2, ln)
        super().__init__(cx, lo, siz=2+2*ln, compact=True, **kwargs)

    def __str__(self):
        return "G「" + self.txt + "」"

PFXS[0x02e48] = GlobName

#######################################################################

class Real(Object):

    def __init__(self, cx, lo, **kwargs):
        self.txt = real(cx.m, lo)
        super().__init__(cx, lo, siz=16, compact=True, **kwargs)

    def __str__(self):
        return self.txt

PFXS[0x02933] = Real

#######################################################################

class Complex(Object):

    def __init__(self, cx, lo, **kwargs):
        self.txt1 = real(cx.m, lo)
        self.txt2 = real(cx.m, lo + 16)
        super().__init__(cx, lo, siz=32, compact=True, **kwargs)

    def __str__(self):
        return "(" + self.txt1 + ", i * " + self.txt2 + ")"

PFXS[0x02977] = Complex

#######################################################################

class LongReal(Object):

    def __init__(self, cx, lo, **kwargs):
        self.txt = longreal(cx.m, lo)
        super().__init__(cx, lo, siz=21, compact=True, **kwargs)

    def __str__(self):
        return self.txt

PFXS[0x02955] = LongReal

#######################################################################

class LongComplex(Object):
    def __init__(self, cx, lo, **kwargs):
        self.txt1 = longreal(cx.m, lo)
        self.txt2 = longreal(cx.m, lo + 21)
        super().__init__(cx, lo, siz=42, compact=True, **kwargs)

    def __str__(self):
        return "(" + self.txt1 + ", i * " + self.txt2 + ")"

PFXS[0x0299d] = LongComplex 

#######################################################################

class Ext1(Object):

    def __init__(self, cx, lo, **kwargs):
        self.ptr1 = cx.m.le(lo, 5)
        self.ptr2 = cx.m.le(lo + 5, 5)
        super().__init__(cx, lo, siz=10, compact=True, **kwargs)

    def __str__(self):
        return "EXT1\t0x%05x, 0x%05x" % (self.ptr1, self.ptr2)

PFXS[0x02baa] = Ext1 

#######################################################################

class LenObject(Object):
    def __init__(self, cx, lo, **kwargs):
        l = cx.m.le(lo, 5)
        y = Relptr(cx.m, lo)
        cx.m.set_line_comment(lo, "End")
        super().__init__(cx, lo, hi=lo+l, **kwargs)

#######################################################################

class Ext2(LenObject):
    pass
PFXS[0x02bcc] = Ext2 

class Ext3(LenObject):
    pass
PFXS[0x02bee] = Ext3 

class Ext4(LenObject):
    pass
PFXS[0x02c10] = Ext4 

#######################################################################

class Code(LenObject):

    def __init__(self, cx, lo, **kwargs):
        super().__init__(cx, lo, **kwargs)
        cx.m.q.queue(PRI_ASSY, cx.disass, lo + 5)

PFXS[0x02dcc] = Code

#######################################################################

class BinInt(LenObject):

    def __init__(self, cx, lo, **kwargs):
        super().__init__(cx, lo, **kwargs)
        a = lo + 5
        while a < self.hi:
            l = min(5, self.hi - a)
            a = Const(cx.m, a, l).hi

PFXS[0x02a4e] = BinInt

#######################################################################

class Library(LenObject):

    def __init__(self, cx, lo, **kwargs):
        # print("LIB 0x%05x" % lo)
        cx.m.set_block_comment(lo, "Library")
        super().__init__(cx, lo, **kwargs)
        self.links = self.names = self.msgs = self.config = None
        b = lo + 5
        nl = Const(cx.m, b, 2, "Name Length")
        b = nl.hi
        if nl.val:
            y = data.Data(cx.m, b, b + nl.val * 2)
            y.rendered = "'" + text(cx.m, b, nl.val) + "'"
            y.compact = True
            b = y.hi
            nl = Const(cx.m, b, 2, "Name Length")
            b = nl.hi
        ln = Const(cx.m, b, 3, "Library Number")
        b = ln.hi
        self.libno = ln.val

        y = Relptr(cx.m, b, "Name Table")
        b = y.hi
        if y.dst:
            self.names = Obj(cx, y.dst, cls=NameTable)
            cx.m.set_label(self.names.lo, "LIB_%03x_NAMES" % self.libno)

        y = Relptr(cx.m, b, "Message Table")
        b = y.hi
        if y.dst:
            self.msgs = Obj(cx, y.dst)
            cx.m.set_label(self.msgs.lo, "LIB_%03x_MESSAGES" % self.libno)

        y = Relptr(cx.m, b, "Link Table")
        b = y.hi
        if y.dst:
            self.links = Obj(cx, y.dst, cls=LinkTable)
            cx.m.set_label(self.links.lo, "LIB_%03x_LINKS" % self.libno)

        y = Relptr(cx.m, b, "Config object")
        b = y.hi
        if y.dst:
            self.config = Obj(cx, y.dst)
            cx.m.set_label(self.config.lo, "LIB_%03x_CONFIG" % self.libno)

        if self.links:
            for n, i in enumerate(self.links.links):
                cx.libobj[(self.libno, n)] = i
                if self.names:
                    t = self.names.names.get(n)
                else:
                    t = None
                if t:
                    cx.m.set_label(i, "LIB_%03x_%03x_%s" % (self.libno, n, t))
                else:
                    cx.m.set_label(i, "LIB_%03x_%03x" % (self.libno, n))
                n1 = cx.m.le(i - 3, 3)
                n2 = cx.m.le(i - 6, 3)
                if n1 == n and n2 == self.libno:
                    Const(cx.m, i - 6, 6)
                    cx.m.set_line_comment(i - 6, "XYZZY")
                cx.m.q.queue(PRI_RPN, Obj, cx, i)

PFXS[0x02b40] = Library

class NameTable(LenObject):
    def __init__(self, cx, lo, **kwargs):
        super().__init__(cx, lo, **kwargs)
        b = lo + 5
        for i in range(16):
            y = Relptr(cx.m, b, "NamLen=%d" % (i + 1))
            b = y.hi
        y = Relptr(cx.m, b, "End")
        b = y.hi
        e = y.dst
        h = {}
        while b < e:
            x = cx.m.le(b, 2)
            c = b + 2
            t = text(cx.m, c, x)
            h[b] = t
            c += 2 * x
            z = cx.m.le(c, 3)
            c += 3
            y = data.Data(cx.m, b, c)
            y.rendered = ".NAME\t0x%03x, 0x%x, '%s'" % (z, x, t)
            y.compact = True
            b = c
        self.names = {}
        n = 0
        y = data.Data(cx.m, b, self.hi)
        r = []
        while b < self.hi:
            x = cx.m.le(b, 5)
            if x:
                nm = h[b - x]
                self.names[n] = nm
                r.append(".IDX\t0x%03x: '%s'" % (n, nm))
            n += 1
            b += 5
        y.rendered = "\n".join(r) 
        y.compact = True
        assert b == self.hi

class LinkTable(LenObject):
    def __init__(self, cx, lo, **kwargs):
        super().__init__(cx, lo, **kwargs)
        self.links=[]
        for b in range(lo + 5, self.hi, 5):
            y = Relptr(cx.m, b)
            self.links.append(y.dst)

#######################################################################

class Array(LenObject):

    def __init__(self, cx, lo, **kwargs):
        super().__init__(cx, lo, **kwargs)

        y = Const(cx.m, lo + 5, 5, "Kind")
        b = y.hi
        self.kind = y.val

        y = Const(cx.m, b, 5, "Dimensions")
        b = y.hi
        self.ndim = y.val

        self.tot = 1
        self.dim = []
        for i in range(self.ndim):
            y = Const(cx.m, b, 5, "Dimension %d" % (i+1))
            b = y.hi
            self.dim.append(y.val)
            self.tot *= y.val
        for i in range(self.tot):
            o = Obj(cx, b, pfx=self.kind)
            b = o.hi
        assert b == self.hi

PFXS[0x029e8] = Array

#######################################################################

class RelRef(data.Data):

    def __init__(self, cx, lo, kind):
        super().__init__(cx.m, lo, lo + 5)
        self.dst = lo + cx.m.le(lo, 5)
        self.term = self.dst == 0x312b
        self.obj = Obj(cx, self.dst, pfx=kind)

    def render(self):
        if self.obj and self.obj.compact:
            return str(self.obj)
        return ".REF\t" + self.aspace.adr(self.dst)

class LinkedArray(LenObject):

    def __init__(self, cx, lo, **kwargs):
        super().__init__(cx, lo, **kwargs)

        y = Const(cx.m, lo + 5, 5, "Kind")
        b = y.hi
        self.kind = y.val

        y = Const(cx.m, b, 5, "Dimensions")
        b = y.hi
        self.ndim = y.val

        self.tot = 1
        self.dim = []
        for i in range(self.ndim):
            y = Const(cx.m, b, 5, "Dimension %d" % (i+1))
            b = y.hi
            self.dim.append(y.val)
            self.tot *= y.val
        for i in range(self.tot):
            y = RelRef(cx, b, self.kind)
            b = y.hi

PFXS[0x02a0a] = LinkedArray

#######################################################################

def do_bitmap(asp, b, cols, rows):
    bm = bitmap.BitMap(cols, rows)

    stride = 2 * ((cols + 7) // 8)
    for r in range(rows):
        bb = b
        for c in range(0, cols):
            if not c & 3:
                v = asp[bb]
                bb += 1
            if v & 1:
                bm.set(c, r)
            v = v >> 1
        b += stride
    return b, bm

class Grob(LenObject):

    def __init__(self, cx, lo, **kwargs):
        super().__init__(cx, lo, **kwargs)

        y = Const(cx.m, lo + 5, 5, "Rows")
        b = y.hi
        self.rows = y.val

        y = Const(cx.m, b, 5, "Cols")
        b = y.hi
        self.cols = y.val

        if self.rows and self.cols:
            b2, bm = do_bitmap(cx.m, b, self.cols, self.rows)
            y = data.Data(cx.m, b, b2)
            y.rendered = str(bm)
            y.compact = True

PFXS[0x02b1e] = Grob

#######################################################################

class Directory(LenObject):	# XXX: Wrong length method
    def __init__(self, cx, lo, **kwargs):
        super().__init__(cx, lo, siz=42, compact=True, **kwargs)

PFXS[0x02a96] = Directory 

class Tagged(LenObject):	# XXX: Wrong length method
    def __init__(self, cx, lo, **kwargs):
        super().__init__(cx, lo, siz=42, compact=True, **kwargs)

PFXS[0x02afc] = Tagged 

class Backup(LenObject):
    pass
PFXS[0x02b62] = Backup 

class LibData(LenObject):
    pass
PFXS[0x02b88] = LibData 

#######################################################################

class DupAndThen(Object):	
    def __init__(self, cx, lo, **kwargs):
        super().__init__(cx, lo, hi=lo, **kwargs)

PFXS[0x641cc] = DupAndThen 

#######################################################################

class Ref(data.Data):

    def __init__(self, cx, lo):
        super().__init__(cx.m, lo, lo + 5)
        self.dst = cx.m.le(lo, 5)
        self.term = self.dst == 0x312b

    def render(self):
        o = self.aspace.objects.get(self.dst)
        if o and o.compact:
            return str(o)
        return ".REF\t" + self.aspace.adr(self.dst)

#######################################################################

class ChainObject(Object):
    def __init__(self, cx, lo, **kwargs):
        super().__init__(cx, lo,  **kwargs)
        bb = lo
        while True:
            o = Obj(cx, bb)
            if o:
                assert o.hi
                bb = o.hi
            else:
                y = Ref(cx, bb)
                bb = y.hi
                if y.term:
                    break
                z = cx.m.le(y.dst, 5)
                if z in PFXS:
                    cx.m.q.queue(PRI_RPN, Obj, cx, y.dst)
                elif z == y.dst + 5:
                    cx.m.q.queue(PRI_RPN, Obj, cx, y.dst)
                elif not list(cx.m.find(z)):
                    z = Dataptr(cx.m, y.dst)
                    cx.m.set_line_comment(z.dst, "Ptr from 0x%05x" % y.dst)
                    cx.m.q.queue(PRI_ASSY, cx.disass, z.dst)
                if y.dst not in cx.m.objects:
                    cx.m.q.queue(PRI_RPN, Obj, cx, y.dst)
        self.set_hi(cx, bb)

#######################################################################

class RPN(ChainObject):
    pass

PFXS[0x02d9d] = RPN

#######################################################################

class List(ChainObject):
    pass

PFXS[0x02a74] = List

#######################################################################

class Unit(ChainObject):
    pass

PFXS[0x2ada] = Unit

#######################################################################

class Symbolic(ChainObject):
    pass

PFXS[0x2ab8] = Symbolic

#######################################################################

class PCO(Object):
    def __init__(self, cx, lo, **kwargs):
        ptr = cx.m.le(lo - 5, 5)
        # print("PCO 0x%x" % lo, "PTR %x" % ptr)
        assert ptr == lo
        super().__init__(cx, lo, compact=False, **kwargs)
        cx.m.q.queue(PRI_ASSY, cx.disass, lo)

    def __str__(self):
        return 'PCO 0x%05x' % self.lo

#######################################################################

def Obj(cx, adr, pfx=None, cls=None):
    assert pfx is None or cls is None
    # print("O 0x%05x" % adr, pfx, cls)
    o = None
    if pfx:
        cls = PFXS.get(pfx)
        o = cls(cx, adr, prefixed=False)
        assert o.hi is not None
    else:
        pfx = cx.m.le(adr, 5)
        if PFXS.get(pfx) == Ext1:
            oo = Ext1(cx, adr + 5, prefixed=True)
            cx.m.objects[adr] = oo
            adr = oo.ptr1
            pfx = cx.m.le(adr, 5)
        if not cls:
            cls = PFXS.get(pfx)
        if cls:
            o = cls(cx, adr + 5, prefixed=True)
            cx.m.objects[adr] = o

    if o and o.hi not in cx.m.objects and cx.m.le(o.hi, 5) in PFXS:
        cx.m.q.queue(PRI_RPN, Obj, cx, o.hi)
    assert not o or o.hi is not None
    return o

########################################################################
# Some of the libraries used Runlength encoded graphics.
# See LIB_0e3:063 for decompressor.
# Autodetection is not worth the effort.

class RllBitMap(LenObject):

    def __init__(self, cx, lo, **kwargs):
        super().__init__(cx, lo, **kwargs)

        b = self.lo + 5
        self.ny = cx.m.le(b, 2)
        b += 2
        self.nx = cx.m.le(b, 2)
        b += 2
        self.sx = self.nx // 4

        fbuf = []

        while b < self.hi:
            cmd = cx.m.le(b, 2)
            b += 2
            if cmd & 0x80:
                fbuf += [cx.m[b]] * (cmd - 0x7f)
                b += 1
            else:
                while cmd >= 0:
                    fbuf.append(cx.m[b])
                    b += 1
                    cmd -= 1
    
        bm = bitmap.BitMap(self.nx, self.ny)
        for i, n in enumerate(fbuf):
            i *= 4
            y = i // self.nx
            x = i % self.nx
            for b in (1, 2, 4, 8):
                if n & b:
                    bm.set(x ^ 4, y)
                x += 1
        y = data.Data(cx.m, self.lo + 5, self.hi)
        y.rendered = ".RLLBITMAP\n" + str(bm)
        y.compact = True

def rll_bitmaps(cx):
    for i in range(0x2b, 0x6a):
         a = cx.libobj[(0xe2, i)] + 15
         Obj(cx, a, cls=RllBitMap)
    for l, e, o, v in (
        (0xe7, 0x39, 0, "KR"),
        (0xe7, 0x3a, 0, "KR"),
        (0xe7, 0x59, 15, "K"),
    ):
         if cx.version in v:
             a = cx.libobj[(l, e)] + o
             Obj(cx, a, cls=RllBitMap)

########################################################################

class CharGen(data.Data):
    def __init__(self, asp, lo, x, y):
        a = lo
        if x is None:
            x = asp[a]
            a += 1
        hi, bm = do_bitmap(asp, a, x, y)
        super().__init__(asp, lo, hi)
        self.rendered = ".CHRGEN\t0x%x, 0x%x\n" % (x, y) + str(bm)

def char_gens(cx):
     ''' The three character generators '''
     for a, b, c, d in (
         (0x7a2b3, 0x7b447, 8, 10),
         (0x7b447, 0x7c257, 8, 8),
         (0x7c257, 0x7c795, None, 5),
     ):
         while a < b:
             y = CharGen(cx.m, a, c, d)
             a = y.hi

########################################################################

def do_libraries(cx):

    LIBTABLE = 0x702c4

    def dolib(a):
        nl = cx.m.le(a - 2, 2)
        if nl:
            a -= (4 + nl * 2)
        else:
            a -= 2
        a -= 5
        if cx.m.le(a - 5, 5) == 0x2b40:
            o = Obj(cx, a - 5)
        else:
            o = Obj(cx, a, pfx=0x2b40)

    cx.m.set_label(LIBTABLE, "LIBTABLE")
    # This table points to all libraries LibID
    a = LIBTABLE
    while True:
        y = Const(cx.m, a, 3)
        a = y.hi
        if y.val == 0xfff:
            break
        y = Dataptr(cx.m, a)
        a = y.hi
        dolib(y.dst)
        # cx.m.set_label(y.dst, "LIBPTR_%05x" % a)
        y = Dataptr(cx.m, a)
        a = y.hi
        if y.dst:
            cx.m.q.queue(PRI_ASSY, cx.disass, y.dst)

########################################################################

def hunt_objects(cx):

    def find_cand():
        for a, b in cx.m.gaps():
            if a > 0x4000 and a + 5 <= b and cx.m.le(a, 5) in PFXS:
                yield a

    n = 0
    while True:
        l = list(find_cand())
        if not l:
            break
        for c in l:
            n += 1
            o = Obj(cx, c)
            # print("Auto 0x%05x" % c, o)
            # cx.m.set_line_comment(c, "AutoDiscover")
    return n

########################################################################

def on_keys(cx):
    # Table for the various ON+something situations
    l = [
        "+",
        "-",
        "B?",
        "Right,F?",
        "/",
        "Left",
        "Warmstart",
        "D",
        "E",
        "SPC",
    ]
    for a in range(0xed5, 0xf93, 19):
        Const(cx.m, a, 14)
        a += 14
        y = Dataptr(cx.m, a)
        cx.m.q.queue(PRI_ASSY, cx.disass, y.dst)
        if l:
            cx.m.set_label(y.dst, "ON_" + l.pop(0))

########################################################################

def do_types(cx):

    cx.m.set_label(0x312b, "$END")
    cx.m.q.queue(PRI_RPN, PCO, cx, 0x3130, prefixed=True)

    for a in range(0x19128, 0x191b9, 5):
        y = Const(cx.m, a, 5)
        if y.val:
            cx.m.set_line_comment(a, PFXS[y.val].__name__)

    cx.m.set_label(0x0309a, "LEN_endptr")
    cx.m.set_label(0x03077, "LEN_chain")
    for i,j in PFXS.items():
        cx.m.set_block_comment(i - 10, "Class " + j.__name__)
        cx.m.set_label(i, "CLASS_" + j.__name__)
        cx.m.q.queue(PRI_ASSY, cx.disass, i)
        y = Dataptr(cx.m, i - 5, "class.length()")
        cx.m.set_label(y.dst, "LEN_" + j.__name__)
        cx.m.q.queue(PRI_ASSY, cx.disass, y.dst)
        y = Dataptr(cx.m, i - 10, "class.something()")
        cx.m.set_label(y.dst, "SOMETHING_" + j.__name__)
        cx.m.q.queue(PRI_ASSY, cx.disass, y.dst)

    # Table of dual pointers to LEN_$type and ???
    for a in range(0x0a69f, 0x0a71c, 5):
        y = Dataptr(cx.m, a)
        if y.dst:
            cx.m.q.queue(PRI_ASSY, cx.disass, y.dst)


########################################################################

def do_version(cx):
    Obj(cx, 0x7ffa0)
    cx.version = "%c" % cx.m.le(0x7ffc9, 2)
    print("ROM VERSION", cx.version)

########################################################################

HP48_INSTRUCTIONS = '''

# RPNCALL is:
#	LC	#0x_____
#	A=C.A
#	PC=(A)

RPNCALL		rpn,>R		|0 0 1 1|0 1 0 0| c1	| c2	| c3	| c4	| c5	|1 1 0 1|1 0 1 0|1 0 0 0|0 0 0 0|1 0 0 0|1 1 0 0|

'''

class HP48_Ins(saturn.Saturn_Ins):

    def assy_rpn(self):
        a = self.assy_abs5()
        Obj(self.lang, a.dst)
        return "#0x%05x" % a.dst

class HP48_Saturn(saturn.Saturn):
    def __init__(self):
        super().__init__()
        self.add_ins(HP48_INSTRUCTIONS, HP48_Ins)

########################################################################

def common(fwfile):

    cx = HP48_Saturn()

    m = mem.WordMem(0, 1<<20, bits=4)
    fw = open(fwfile, "rb").read()
    for i in range(len(fw)):
        m[0 + (i << 1)] = fw[i] & 0xf
        m[1 + (i << 1)] = fw[i] >> 4

    cx.m.map(m, 0)

    cx.m.objects = {}
    cx.m.q = Queue()
    cx.libobj = {}

    if False:
        return "HP48GX", (cx.m,)

    do_version(cx)
    do_types(cx)
    char_gens(cx)
    do_libraries(cx)
    rll_bitmaps(cx)
    on_keys(cx)

    if True:
        Obj(cx, 0x21c5)
        # Obj(cx, 0x21dd)

    # Find all PCOs not yet spotted
    for a, b in cx.m.gaps():
        while a < b - 6:
            if cx.m.le(a, 5) == a + 5:
                cx.m.q.queue(PRI_RPN, PCO, cx, a + 5, prefixed=True)
                # cx.m.set_line_comment(a, "Discover")
            a += 1

    # Find all RPNCALL
    for a, b in cx.m.gaps():
        while a < b - 13:
            if cx.m[a] == 0x3 and cx.m[a + 1] == 0x4:
                if cx.m[a + 7] == 0xd and cx.m[a + 8] == 0xa:
                    if cx.m[a + 9] == 0x8 and cx.m[a + 10] == 0:
                        if cx.m[a + 11] == 0x8 and cx.m[a + 12] == 0xc:
                            #print("RPNCALL 0x%05x" % a)
                            cx.m.q.queue(PRI_ASSY, cx.disass, a)
            a += 1

    for a in (
        0x00000,
        0x00006,
        0x00100,
    ):
        cx.m.q.queue(PRI_ASSY, cx.disass, a)

    return cx

def version_k(cx):
    return


def version_r(cx):
    return

def example():

    l = []
    for fw, vf in (
        (FIRMWARE_K, version_k),
        (FIRMWARE_R, version_r),
    ):
        cy = common(fw)
        l.append(cy.m)
        vf(cy)

        a = 0x15b4c
        while True:
            y = Dataptr(cy.m, a)
            if not y.dst:
                break
            a += 5
            y = Dataptr(cy.m, a)
            cy.m.q.queue(PRI_RPN, Obj, cy, y.dst)
            a += 5
            y = Dataptr(cy.m, a)
            cy.m.q.queue(PRI_RPN, Obj, cy, y.dst)
            a += 5


        for a in (
            0x21de7,
            0x3858e,
            0x385e8,
            0x648bd,
            0x72e87,
        ):
            Obj(cy, a)
            cy.m.set_line_comment(a, "Manual")

        for a in (
            0x0be2d,
            0x0c114,
            0x0c1d4,
            0x0c1e9,
            0x80000,
            0x8011c,
            0x80126,
            0x80133,
            0x80167,
            0x801a5,
            0x80215,
            0x80804,
            0x80821,
            0x80832,
            0x80965,
            0x80974,
            0x809d5,
            0x80a54,
            0x80a73,
            0x80b2d,
            0x80b43,
            0x80c20,
            0x80ec3,
            0x80f79,
            0x8107d,
            0x81374,
            0x818cb,
            0x81944,

            # see GOSUB 0x26ca
            0x81cad,
            0x81cbc,
            0x81ce2,
            0x81cfc,
            0x81d24,
        ):
            cy.m.q.queue(PRI_ASSY, cy.disass, a)

        for a in range(0x70601, 0x706a1, 5):
            y = Dataptr(cy.m, a)
            cy.disass(y.dst)

        # Table of week-days
        for a in range(0x0cf31, 0x0cf5b, 6):
            y = data.Data(cy.m, a, a + 6)
            t = text(cy.m, a, 3)
            y.rendered = ".TXT\t「" + t + "」"

        while True:
            cy.m.q.run()
            if hunt_objects(cy):
                break;

        if True:
            edb = entrydatabase.RPN_EDB()
            edb.decorate(cy.m, "48G")

    return "HP48GX", l

if __name__ == '__main__':
    listing.Example(example, wordspace='', charset=False)
