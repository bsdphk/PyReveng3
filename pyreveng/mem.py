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

'''
Address Space and Memory Classes

These classes can be configured to act as memory for images to be
analysed.

In addition to the numerical value of each location, it is also
possible to associate up to seven attributes with each location.
These can be used to record structural information in the media,
for instance relocation flags, write-ability etc.

XXX: Better test-cases needed
XXX: Need resolution of who controls rendering...

'''

import os.path
import ctypes

from pyreveng import tree, leaf

DEFINED = (1 << 7)

def mapped(x):
    ''' Decorator to mark methods which should be "exported" up to MemMapper'''
    x.ismapped = True
    return x

class MemError(Exception):

    def __init__(self, adr, reason):
        super().__init__()
        self.adr = adr
        self.reason = reason
        self.value = ("0x%x:" % adr + str(self.reason),)

    def __str__(self):
        return repr(self.value)

class Range():
    ''' A range grouping '''
    def __init__(self, lo, hi, txt, indent=False, visible=True):
        self.lo = lo
        self.hi = hi
        self.txt = txt
        self.indent = indent
        self.visible = visible

    def __repr__(self):
        return "<range 0x%x-0x%x %s>" % (self.lo, self.hi, self.txt)

    def __lt__(self, other):
        return self.lo < other.lo

class AddressSpace():

    '''
    A vacuous address-space, memory-mapper and base-class for actual
    address-spaces and memory types.
    '''

    def __init__(self, lo, hi, name="", apfx="", asfx=""):
        assert lo <= hi
        self.lo = lo
        self.hi = hi
        self.name = name
        self.lbl_d = dict()
        self.bcmt_d = dict()
        self.lcmt_d = dict()
        self.rangelist = []
        self.t = tree.Tree(self.lo, self.hi)
        nxdig = max(len("%x" % self.lo), len("%x" % (self.hi - 1)))
        self.afmtpct = apfx + "%%0%dx" % nxdig + asfx
        self.apct = apfx + "0x%%0%dx" % nxdig + asfx
        self.apct = apfx + "0x%x" + asfx

    def __repr__(self):
        return "<address_space %s 0x%x-0x%x>" % (
            self.name, self.lo, self.hi
        )

    def __getitem__(self, adr):
        _b = self._off(adr)
        raise MemError(adr, "Undefined")

    def __setitem__(self, adr, data):
        _b = self._off(adr)
        raise MemError(adr, "Undefined")

    def __iter__(self):
        for i in self.t:
            yield i

    def adr(self, dst):
        ''' Render an address '''
        lbl = list(self.get_labels(dst))
        if lbl:
            return lbl[0]
        return self.apct % dst

    def afmt(self, adr):
        ''' Format address, fixed width, for addr col of listing '''
        return self.afmtpct % adr

    def dfmt(self, adr):
        ''' Format data word at address '''
        raise MemError(adr, "Undefined")

    def tfmt(self, adr):
        ''' Split data word at address into characters '''
        raise MemError(adr, "Undefined")

    def gaps(self):
        ll = self.lo
        for i in sorted(self):
            if i.lo > ll:
                yield ll, i.lo
            ll = i.hi
        if self.hi > ll:
            yield ll, self.hi

    def segments(self):
        yield self, self.lo, self.hi

    def _off(self, adr):
        if adr < self.lo:
            raise MemError(adr, "Address too low")
        if adr >= self.hi:
            raise MemError(adr, "Address too high")
        return adr - self.lo

    def set_label(self, adr, lbl):
        assert isinstance(lbl, str)
        self.lbl_d.setdefault(adr, []).append(lbl)

    def get_labels(self, adr):
        i = self.lbl_d.get(adr)
        if i:
            yield from i

    def get_all_labels(self):
        yield from self.lbl_d.items()

    def set_line_comment(self, adr, lcmt):
        assert isinstance(lcmt, str)
        self.lcmt_d.setdefault(adr, []).append(lcmt)

    def get_line_comments(self, adr):
        i = self.lcmt_d.get(adr)
        if i:
            yield from i

    def get_all_line_comments(self):
        yield from self.lcmt_d.items()

    def set_block_comment(self, adr, bcmt):
        assert isinstance(bcmt, str)
        self.bcmt_d.setdefault(adr, []).append(bcmt)

    def get_block_comments(self, adr):
        i = self.bcmt_d.get(adr)
        if i:
            yield from i

    def get_all_block_comments(self):
        yield from self.bcmt_d.items()

    def add_range(self, lo, hi, **kwargs):
        r = Range(lo, hi, **kwargs)
        self.rangelist.append(r)
        return r

    def ranges(self):
        yield from self.rangelist

    def insert(self, lf):
        lf.aspace = self
        return self.t.insert(lf)

    def find(self, *args, **kwargs):
        yield from self.t.find(*args, **kwargs)

    def occupied(self, *args, **kwargs):
        for _i in self.find(*args, **kwargs):
            return True
        return False

class MemMapper(AddressSpace):

    def __init__(self, lo, hi, **kwargs):
        super().__init__(lo, hi, **kwargs)
        self.mapping = []
        self.seglist = []
        self.bits = 0
        self.xlat = self.xlat0

    def __repr__(self):
        return "<MemMapper %s 0x%x-0x%x>" % (self.name, self.lo, self.hi)

    class Link(leaf.Leaf):

        def __init__(self, lo, hi, link):
            super().__init__(lo, hi, "LinkLeaf")
            self.link = link

        def __repr__(self):
            return "<" + super().__repr__() + " -> " + self.link.__repr__() + ">"

        def render(self):
            self.compact = self.link.compact
            return self.link.render()

        def __eq__(self, other):
            return super().__eq__(other) and self.link.__class__ == other.link.__class__

    class Alien(leaf.Leaf):
        def __init__(self, lo, hi, them):
            super().__init__(lo, hi, "Alien")
            self.them = them
            self.compact = True

        def render(self):
            t = "ALIEN"
            t += " %s" % self.them.aspace.afmt(self.them.lo)
            t += "-%s" % self.them.aspace.afmt(self.them.hi)
            t += " " + self.them.render()
            return t

    def map(self, mem, lo, hi=None, offset=None, shared=False):
        if offset is None:
            offset = 0
        if hi is None:
            hi = lo + mem.hi - offset
        assert hi > lo
        self.seglist.append([lo, hi, offset, mem, shared])
        self.mapping.append([lo, hi, offset, mem, shared])

        if len(self.mapping) == 1:
            self.xlat = self.xlat1
        if len(self.mapping) > 1:
            self.xlat = self.xlatn
        else:
            self.bits = mem.bits
        self.map_methods(mem)

    def map_methods(self, mem):
        ''' Create wrapper methods in this class, for the @mapped decorated
        methods of the memory we map.
        '''
        for f in dir(mem):
            if getattr(self, f, False):
                continue
            a = getattr(mem, f)
            if callable(a) and getattr(a, "ismapped", False):
                #print("MAP", f, "from", mem)
                src = "def %s(self, adr, *args, **kwargs):\n" % f
                src += "    ms, sa, _sh = self.xlat(adr)\n"
                src += "    return ms.%s(sa, *args, **kwargs)\n" % f
                src += "\n"
                d = {}
                exec(src, {}, d)
                setattr(self.__class__, f, d[f])


    def xlat0(self, adr, _fail=True):
        return self, adr, False

    def xlat1(self, adr, fail=True):
        low, high, offset, mem, shared = self.mapping[0]
        if low <= adr < high:
            return mem, (adr - low) + offset, shared
        if fail:
            raise MemError(adr, "Unmapped memory @0x%x" % adr)
        return self, adr, False

    def xlatn(self, adr, fail=True):
        for i, j in enumerate(self.mapping):
            low, high, offset, mem, shared = j
            if low <= adr < high:
                self.mapping.pop(i)
                self.mapping.insert(0, j)
                return mem, (adr - low) + offset, shared
        if fail:
            raise MemError(adr, "Unmapped memory @0x%x" % adr)
        return self, adr, False

    def dealienate(self, item, low, offset):
        j = item
        while isinstance(j, self.Link):
            j = j.link
        if j.lo != item.lo + low - offset:
            return self.Alien(item.lo + low - offset, item.hi + low - offset, item)
        return j

    def __iter__(self):
        for i in self.t:
            assert not isinstance(i, self.Link), i
            yield i
        for low, high, offset, mem, _shared in self.seglist:
            for i in mem.t:
                ll = i.lo + low - offset
                hh = i.hi + low - offset
                if low <= ll < high and low <= hh <= high:
                    j = self.dealienate(i, low, offset)
                    assert not isinstance(j, self.Link), j
                    yield j

    def __getitem__(self, adr):
        ms, sa, _sh = self.xlat(adr)
        return ms[sa]

    def __setitem__(self, adr, dat):
        ms, sa, _sh = self.xlat(adr)
        ms[sa] = dat

    def find(self, lo=None, hi=None, **kwargs):
        if hi is None:
            hi = lo + 1
        if lo is None:
            lo = hi - 1
        #print("FS", "%x" % lo, "%x" % hi)
        yield from super().find(lo=lo, hi=hi, **kwargs)
        for low, high, offset, mem, _shared in self.seglist:
            #print(" fs", "%x" % low, "%x" % high, "%x" % offset)
            if low <= hi or lo <= high:
                ll = max(lo, low) + offset - low
                hh = min(hi, high) + offset - low
                #print("  fs", "%x" % ll, "%x" % hh)
                for j in mem.find(lo=ll, hi=hh, **kwargs):
                    #print("   fs", j)
                    x = self.dealienate(j, low, offset)
                    #print("    fs", x)
                    yield x

    def set_something(self, what, adr, *args):
        ms, sa, _sh = self.xlat(adr, False)
        if ms == self:
            getattr(super(), what)(adr, *args)
        else:
            getattr(ms, what)(sa, *args)

    def get_something(self, what, adr, *args):
        ms, sa, _sh = self.xlat(adr, False)
        if ms == self:
            yield from getattr(super(), what)(adr, *args)
        else:
            yield from getattr(ms, what)(sa, *args)

    def get_all_somethings(self, what):
        yield from getattr(super(), what)()
        for low, high, offset, mem, _shared in self.seglist:
            for a, b in getattr(mem, what)():
                aa = a + low - offset
                if low <= aa < high:
                    yield aa, b

    def set_label(self, *args):
        self.set_something("set_label", *args)

    def get_labels(self, *args):
        yield from self.get_something("get_labels", *args)

    def get_all_labels(self):
        yield from self.get_all_somethings("get_all_labels")


    def set_line_comment(self, *args):
        self.set_something("set_line_comment", *args)

    def get_line_comments(self, *args):
        yield from self.get_something("get_line_comments", *args)

    def get_all_line_comments(self):
        yield from self.get_all_somethings("get_all_line_comments")


    def set_block_comment(self, *args):
        self.set_something("set_block_comment", *args)

    def get_block_comments(self, *args):
        yield from self.get_something("get_block_comments", *args)

    def get_all_block_comments(self):
        yield from self.get_all_somethings("get_all_block_comments")

    def add_range(self, lo, hi, **kwargs):
        ms, sa, _sh = self.xlat(lo, False)
        ms.add_range(sa, sa + hi - lo, **kwargs)
        return super().add_range(lo, hi, **kwargs)

    def segments(self):
        for low, high, _offset, mem, _shared in sorted(self.seglist):
            yield mem, low, high

    def get_attr(self, adr):
        ms, sa, _sh = self.xlat(adr)
        return ms.get_attr(sa)

    def set_attr(self, adr, aval):
        ms, sa, _sh = self.xlat(adr)
        return ms.set_attr(sa, aval)

    def dfmt(self, adr):
        ms, sa, _sh = self.xlat(adr, False)
        if ms == self:
            return super().dfmt(sa)
        return ms.dfmt(sa)

    def tfmt(self, adr):
        ms, sa, _sh = self.xlat(adr)
        return ms.tfmt(sa)

    def gaps(self):
        for glo, ghi in super().gaps():
            for slo, shi, _offset, _mem, _shared in sorted(self.seglist):
                if ghi <= slo or glo >= shi:
                    continue
                glo = max(glo, slo)
                ghi = min(ghi, shi)
                yield glo, ghi

    def insert(self, item):
        ms, sa, _sh = self.xlat(item.lo, False)
        if ms != self:
            item.aspace = self
            ll = self.Link(sa, item.hi - (item.lo - sa), item)
            ms.insert(ll)
        else:
            super().insert(item)

class WordMem(AddressSpace):

    """
    Word memory is characteristic for a lot of the earliest computers,
    they could access exactly one word at a time, or possibly fractions
    of a word, but the instruction set did not support any "super-size"
    data types or access spanning multiple words.

    Typical examples:  Pretty much any decendant of Von Neumans early
    computers down to most of the minicomputers from DEC and DG etc.

    Largest supported word-width is 64 bits and 8 attributes.
    """

    def __init__(self, lo, hi, bits=8, attr=0, **kwargs):
        assert lo < hi
        assert bits > 0
        assert bits <= 64
        assert attr >= 0
        assert attr <= 7

        super().__init__(lo, hi, **kwargs)

        self.bits = bits
        self.fmt = "%" + "0%dx" % ((bits + 3) // 4)
        self.undef = "-" * ((bits + 3) // 4)
        self.ascii = (bits & 7) == 0
        self.lo = lo
        self.hi = hi
        self.attr = attr
        ln = hi - lo

        self.msk = (1 << bits) - 1
        self.amsk = (1 << attr) - 1

        if bits <= 8:
            self.mt = ctypes.c_uint8
        elif bits <= 16:
            self.mt = ctypes.c_uint16
        elif bits <= 32:
            self.mt = ctypes.c_uint32
        else:
            self.mt = ctypes.c_uint64

        self.m = (self.mt * ln)()

        self.at = ctypes.c_uint8
        self.a = (self.at * ln)()

    def __repr__(self):
        return "<word_mem 0x%x-0x%x, @%d bits, %d attr>" % (
            self.lo, self.hi, self.bits, self.attr)

    def __getitem__(self, adr):
        """Read location"""
        b = self._off(adr)
        if not self.a[b] & DEFINED:
            raise MemError(adr, "Undefined")
        return self.m[b]

    def __setitem__(self, adr, dat):
        """Write location"""
        if dat & ~self.msk:
            raise MemError(adr, "Data too wide (0x%x)" % dat)
        b = self._off(adr)
        self.m[b] = self.mt(dat)
        self.a[b] |= DEFINED

    def wr(self, adr, dat):
        self[adr] = dat

    def dfmt(self, adr):
        try:
            return self.fmt % self[adr]
        except MemError:
            return self.undef

    def get_attr(self, adr):
        """Get attributes"""
        b = self._off(adr)
        return self.a[b] & self.amsk

    def set_attr(self, adr, x):
        """Set attributes"""
        if x & ~self.amsk:
            raise MemError(adr, "Attribute too wide (0x%x)" % x)
        b = self._off(adr)
        self.a[b] |= x

    def clr_attr(self, adr, x):
        """Clear attributes"""
        if x & ~self.amsk:
            raise MemError(adr, "Attribute too big (0x%x)" % x)
        b = self._off(adr)
        self.a[b] &= ~x

    def tfmt(self, adr):
        ll = []
        b = self.bits
        try:
            w = self[adr]
        except MemError:
            w = None
        while b >= 8:
            b -= 8
            if w is None:
                ll.append(None)
            else:
                ll.append((w >> b) & 0xff)
        return ll

    @mapped
    def be(self, adr, n=2):
        ''' Big endian multiword '''
        v = 0
        for a in range(adr, adr + n):
            v <<= self.bits
            v |= self[a]
        return v

    @mapped
    def le(self, adr, n=2):
        ''' Little endian multiword '''
        v = 0
        s = 0
        for a in range(adr, adr + n):
            v |= self[a] << s
            s += self.bits
        return v

class ByteMem(WordMem):

    """
    Byte memory is characteristic for microcomputers, which
    typically had very narrow busses, 4 or 8 bits, but instructions
    for operating on wider types than the width of the bus.

    This introduces the issue of "endianess" but this is not
    really attribute of the memory, it is an attribute of the
    CPU, instruction set or interpreted code, so we provide
    both "sexes" and leave it up to everybody else to use the
    right one.
    """

    def __init__(self, lo, hi, **kwargs):
        super().__init__(lo, hi, bits=8, **kwargs)

    def __repr__(self):
        return "<ByteMem 0x%x-0x%x, %d attr %s>" % (
            self.lo, self.hi, self.attr, self.name)

    @mapped
    def bytearray(self, lo, bcnt):
        i = self._off(lo)
        return bytearray(self.m[i:i+bcnt])

    def tfmt(self, adr):
        try:
            return (self[adr],)
        except MemError:
            return (None,)

    @mapped
    def u8(self, adr):
        """Unsigned 8-bit byte"""
        return self[adr]

    @mapped
    def bu16(self, adr):
        """Big Endian Unsigned 16-bit half-word"""
        retval = self[adr] << 8
        retval |= self[adr + 1]
        return retval

    @mapped
    def bu32(self, adr):
        """Big Endian Unsigned 32-bit word"""
        retval = self[adr] << 24
        retval |= self[adr + 1] << 16
        retval |= self[adr + 2] << 8
        retval |= self[adr + 3]
        return retval

    @mapped
    def bu64(self, adr):
        """Big Endian Unsigned 64-bit double-word"""
        retval = self[adr] << 56
        retval |= self[adr + 1] << 48
        retval |= self[adr + 2] << 40
        retval |= self[adr + 3] << 32
        retval |= self[adr + 4] << 24
        retval |= self[adr + 5] << 16
        retval |= self[adr + 6] << 8
        retval |= self[adr + 7]
        return retval

    @mapped
    def lu16(self, adr):
        """Little Endian Unsigned 16-bit half-word"""
        retval = self[adr]
        retval |= self[adr + 1] << 8
        return retval

    @mapped
    def lu32(self, adr):
        """Little Endian Unsigned 32-bit word"""
        retval = self[adr]
        retval |= self[adr + 1] << 8
        retval |= self[adr + 2] << 16
        retval |= self[adr + 3] << 24
        return retval

    @mapped
    def lu64(self, adr):
        """Little Endian Unsigned 64-bit double-word"""
        retval = self[adr]
        retval |= self[adr + 1] << 8
        retval |= self[adr + 2] << 16
        retval |= self[adr + 3] << 24
        retval |= self[adr + 4] << 32
        retval |= self[adr + 5] << 40
        retval |= self[adr + 6] << 48
        retval |= self[adr + 7] << 56
        return retval

    @mapped
    def s8(self, adr):
        """Signed 8-bit byte"""
        retval = self[adr]
        if retval & 0x80:
            retval -= 256
        return retval

    @mapped
    def bs16(self, adr):
        """Big Endian Signed 16-bit half-word"""
        retval = self.bu16(adr)
        if retval & 0x8000:
            retval -= 0x10000
        return retval

    @mapped
    def ls16(self, adr):
        """Little Endian Signed 16-bit half-word"""
        retval = self.lu16(adr)
        if retval & 0x8000:
            retval -= 0x10000
        return retval

    @mapped
    def bs32(self, adr):
        """Big Endian Signed 32-bit word"""
        retval = self.bu32(adr)
        if retval & 0x80000000:
            retval -= 0x100000000
        return retval

    @mapped
    def ls32(self, adr):
        """Little Endian Signed 32-bit word"""
        retval = self.lu32(adr)
        if retval & 0x80000000:
            retval -= 0x100000000
        return retval

    @mapped
    def bs64(self, adr):
        """Big Endian Signed 64-bit double-word"""
        retval = self.bu64(adr)
        if retval & 0x8000000000000000:
            retval -= 0x10000000000000000
        return retval

    @mapped
    def ls64(self, adr):
        """Little Endian Signed 64-bit double-word"""
        retval = self.lu64(adr)
        if retval & 0x8000000000000000:
            retval -= 0x10000000000000000
        return retval

    def load_data(self, first, step, dat):
        for i in dat:
            self[first] = i
            first += step

    def load_binfile(self, first, step, filename, lo=0, hi=None):
        fi = open(filename, "rb")
        d = bytearray(fi.read())
        fi.close()
        if hi:
            self.load_data(first, step, d[lo:hi])
        else:
            self.load_data(first, step, d[lo:])

class Stackup(ByteMem):
    """
    Convenience function to stack a set of eproms into ByteMem.
    'files' indicate the layout desired, and each element can be
    just a filename or an iterable of filenames:

        files = (
            "singlelane",
            ("highbyte", "lowbyte"),
            ("topbyte", "midhibyte", "midlobyte", "lobyte"),
        )

    'prefix' is used for all filenames.

    See also:
        examples/HP3335A
        examples/HP8568A

    """

    def __init__(self, files, lo=0, prefix="", nextto=None):
        if nextto is not None:
            prefix = os.path.dirname(nextto)
        ll = []
        hi = lo
        for r in files:
            ll.append([])
            if isinstance(r, str):
                b = open(os.path.join(prefix, r), "rb").read()
                hi += len(b)
                ll[-1].append(b)
            else:
                for i in r:
                    b = open(os.path.join(prefix, i), "rb").read()
                    hi += len(b)
                    ll[-1].append(b)
        super().__init__(lo, hi)
        p = lo
        for r in ll:
            stride = len(r)
            ln = len(r[0])
            o = stride
            for i in r:
                o -= 1
                pp = p + o
                for j in i:
                    self[pp] = j
                    pp += stride
            p += stride * ln

def do_test():
    mem = WordMem(0x0000, 0x1000, bits=64, attr=3)
    print(mem)
    print(type(mem.m), ctypes.sizeof(mem.m))
    mem.wr(0x100, 0x123456789)
    print("%x" % mem[0x100])
    print(mem.get_attr(0x100))
    print(mem.get_attr(0x101))
    print(mem.set_attr(0x101, 4))
    print(mem.get_attr(0x101))

if __name__ == "__main__":
    do_test()
