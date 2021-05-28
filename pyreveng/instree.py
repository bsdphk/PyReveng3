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
    InsTree -- A class for disassembling
    ====================================

    This is the fundamental syntax in Bill Fenner approved ABNF:

	spec = *(blankline / comment / specline)
	blankline = *WSP LF
	comment = *WSP "#" *(VCHAR / WSP) LF
	specline = mnemonic 1*WSP operands 1*WSP wordspec 1*WSP [ pilspec ] LF
	mnemonic = 1*VCHAR
	operands = operand *( "," operand )
	operand = 1*( %x21-2B / %x2D-7E )
	wordspec = "|" 1*field
	field = bitfield / hexfield / varfield / linebreak
	bit = ( "0" / "1" / "?" )
	bitfield = bit *( " " bit ) "|"
	hexfield = *WSP 1*( DIGIT / %x41-46 ) *WSP "|"
	varfield = *WSP %x61-7A 1*( %x61-7A / %x30-39 / "_" ) *WSP "|"
	linebreak = *WSP "&" LF *WSP "|"
	pilspec = *WSP "{" LF *pillines "}" LF
	pillines = (HTAB / %x20-7C / "~") 1*(WSP / VCHAR ) LF

    On top of this are other requirements, in particular the widths of fields.

'''

import sys
import re

class UsageTrouble(Exception):
    pass

class SyntaxTrouble(Exception):
    def __init__(self, last, msg):
        j = " ".join(last.split())
        super().__init__(
            "\nAfter '%s':\n    %s" % (j, msg))

def bcount(i):
    i = i - ((i >> 1) & 0x55555555)
    i = (i & 0x33333333) + ((i >> 2) & 0x33333333)
    return (((i + (i >> 4) & 0xF0F0F0F) * 0x1010101) & 0xffffffff) >> 24

#######################################################################
# Parse a "(([01?] )*[01?])(*HEXDIG)" string into a mask + bits

def parse_match(fmt):
    x = fmt.split()
    if len(x) == 1 and len(x[0]) > 1:
        x = x[0]
        if x.upper() != x:
            a = -2
        else:
            a = -1
            try:
                a = int(x, 16)
            except ValueError:
                pass
        if a >= 0:
            return (
                4 * len(x),
                (1 << (4 * len(x))) - 1,
                a)
    mask = 0
    bits = 0
    width = 0
    fl = len(fmt)
    if fl & 1 == 0:
        return None, None, None
    i = 0
    while i < fl:
        mask <<= 1
        bits <<= 1
        width += 1
        if fmt[i] == "0":
            mask |= 1
        elif fmt[i] == "1":
            mask |= 1
            bits |= 1
        elif fmt[i] == "?":
            pass
        else:
            return (fl+1)//2, None, None
        i += 1
        if i < fl and fmt[i] != " ":
            return (fl+1)//2, None, None
        i += 1
    return (width, mask, bits)

#######################################################################
# A single entry from the specification

class InsLine():
    def __init__(self, wordsize, assy, bits, pilspec=None, handler=None):
        self.assy = assy.split()
        self.raw_bits = bits
        self.pilspec = pilspec
        self.handler = handler

        s = bits.split("|")
        s.pop(0)
        s.pop(-1)

        b = 0
        fspec = list()
        for i in s:
            w, fm, fb = parse_match(i)
            if fm is None and len(i.split()) != 1:
                raise SyntaxTrouble(assy,
                    "Multiple words in this field:\n" +
                    "\t|" + i + "|")
            if w is None:
                raise SyntaxTrouble(assy,
                    "Field from bit %d has a half bit:\n" % b +
                    "\t|%s|\n" % i)
            if b // wordsize != (b + w - 1) // wordsize:
                raise SyntaxTrouble(assy,
                    "Field from bit %d spans words:\n" % b +
                    "\t|%s|\n" % i)
            fspec.append((b, w, i, fm, fb))
            b += w

        if b % wordsize != 0:
            raise SyntaxTrouble(assy,
                "Missing bits to fill wordsize\n" +
                "\t%s\n" % bits)

        self.words = b // wordsize

        self.mask = [0] * self.words
        self.bits = [0] * self.words
        self.flds = dict()

        self.init_fields(wordsize, fspec)

    def init_fields(self, wordsize, fspec):

        for b, w, i, fm, fb in fspec:
            j = b // wordsize
            o = (10 * wordsize - (b + w)) % wordsize
            #print("B", b, "W", w, "I", i, "J", j, "O", o, "X", x)
            if fm is None:
                self.flds[i.split()[0]] = (j, o, (1 << w) - 1)
            else:
                self.mask[j] |= fm << o
                self.bits[j] |= fb << o

    def get_field(self, fld, words):
        if fld not in self.flds:
            raise UsageTrouble('In %s:\n' % self.assy + '    No field "%s"\n' % fld)
        x = self.flds[fld]
        return (words[x[0]] >> x[1]) & x[2]

    def __repr__(self):
        s = '<InsLine "'
        s += ' '.join(self.assy)
        s += '" ['
        t = ""
        for i in range(len(self.mask)):
            s += t + '%02x:%02x' % (self.mask[i], self.bits[i])
            t = ", "
        s += '] ['
        t = ""
        for i in self.flds:
            j = self.flds[i]
            s += t + i
            s += '@%d.%d:%x' % (j[0], j[1], j[2])
            t = ", "
        s += ']'
        if self.pilspec:
            s += ' PIL'
        return s + '>'

#######################################################################
#  Branch-point

class InsBranch():
    def __init__(self, lvl):
        self.lvl = lvl
        self.t = list()
        self.mask = 0
        self.wildcard = None

    def __iter__(self):
        for i, x in self.t:
            for j in sorted(x.keys()):
                y = x[j]
                if isinstance(y, InsLine):
                    yield [i, j], y
                else:
                    for a, b in y:
                        yield [i, j] + a, b

    def insert(self, last, x):
        #print("?  ", self.lvl, "%02x" % self.mask, x)
        if len(x.mask) == self.lvl:
            if self.wildcard is not None:
                raise SyntaxTrouble(last,
                    "Colliding entries:\n" +
                    "\t" + str(self.wildcard) + "\n" +
                    "\t" + str(x))
            self.wildcard = x
            return
        xm = x.mask[self.lvl]
        xb = x.bits[self.lvl]
        for i, d in self.t:
            if i != xm:
                continue
            if xb not in d:
                d[xb] = x
                return
            y = d[xb]
            if isinstance(y, InsBranch):
                y.insert(last, x)
                return
            z = InsBranch(self.lvl + 1)
            z.insert(last, x)
            z.insert(last, y)
            d[xb] = z
            return
        d = dict()
        d[xb] = x
        self.t.append((xm, d))
        #print("T", self.t)
        self.t.sort(key=lambda x: -bcount(x[0]))
        return

    def dump(self, fo, fmt="%x", pfx=""):
        fo.write(pfx + '[%d]' % self.lvl + '\n')
        for i, x in self.t:
            fo.write(pfx + '    &' + fmt % i + '\n')
            a = list(x.keys())
            a.sort()
            for j in a:
                y = x[j]
                if isinstance(y, InsLine):
                    fo.write(pfx + '      =' + fmt % j + '\t' + str(y) + '\n')
                else:
                    fo.write(pfx + '      =' + fmt % j + ':\n')
                    y.dump(fo, fmt, pfx + '        ')
        if self.wildcard is None:
            fo.write(pfx + '    *\n')
            fo.write(pfx + '      =' + '?' * len(fmt % 0) + '\t')
            fo.write(str(self.wildcard) + '\n')

    def __repr__(self):
        return "<Branch %d>" % self.lvl

    def find(self, v):
        for i, d in self.t:
            x = v & i
            if x in d:
                yield d[x]
        if self.wildcard is not None:
            yield self.wildcard


#######################################################################
#

class InsMatch():
    def __init__(self, pil, adr, words):
        self.pil = pil
        self.handler = pil.handler
        self.assy = pil.assy
        self.words = words[0:self.pil.words]
        self.adr = adr
        self.flds = {}
        self.il = None
        for i in pil.flds:
            self.flds[i] = pil.get_field(i, self.words)

    def get(self, f):
        return self.flds.get(f)

    def __getitem__(self, f):
        return self.flds[f]

    def __setitem__(self, f, v):
        self.flds[f] = v

    def __repr__(self):
        s = "<InsMatch"
        s += " @0x%x: [" % self.adr
        words = []
        for i in self.words:
            words.append("0x%x" % i)
        s += ", ".join(words)
        s += "] " + " ".join(self.assy)
        if self.il:
            for i in self.il.flds:
                s += " | " + i + "=" + str(self.__dict__["F_" + i])
        s += ">"
        return s

#######################################################################

class InsTree():

    '''
    An Instruction Tree is used to find the descriptions
    of all instruction patterns which match a particular
    memory address.

    The matching patterns are returned in most-to-least specific
    order, where more specific is defined as "more words and
    bits examined".

    Templates are always [1:N]*wordsize wide.
    '''

    def __init__(self, wordsize=8):
        self.wordsize = wordsize
        self.root = InsBranch(0)

    def __iter__(self):
        for i in self.root:
            yield i

    def load_string(self, s, handler=None):
        i = 0
        banned = False
        s = s.expandtabs()

        # Join continuation lines
        s = re.sub("\\|\\s*&\n\\s*\\|", "|", s)

        last = ''
        while i < len(s):

            # Skip whitespace
            if s[i] in (' ', '\t'):
                i += 1
                continue

            # Skip comments to NL
            if s[i] == '#':
                j = s.find('\n', i)
                if j == -1:
                    break
                i = j + 1
                banned = False
                continue

            # Skip NL
            if s[i] in ('\n',):
                i += 1
                banned = False
                continue

            # }-lines cannot contain anything but comments
            if banned:
                raise SyntaxTrouble(last,
                    "}-line can only contain comments")

            # Find the assy part
            j = s.find('|', i)
            if j == -1:
                raise SyntaxTrouble(last,
                    "no '|' on this line")
            last = assy = s[i:j].strip()
            i = j
            j = s.find('\n', i)
            if j == -1:
                j = len(s)

            # find the map part
            bm = s[i:j]
            i = j
            j = bm.rfind('{')
            if j == -1:
                self.root.insert(last,
                    InsLine(self.wordsize, assy, bm, handler=handler))
                continue

            # Isolate tail-part
            tail = bm[j+1:]
            bm = bm[:j]
            if tail.strip() != "":
                raise SyntaxTrouble(last, "junk after '{'")
            j = s.find('\n}', i)
            if j == -1:
                raise SyntaxTrouble(last, "no }-line found")
            tail = s[i:j]
            i = j + 2
            banned = True

            self.root.insert(last,
                InsLine(self.wordsize, assy, bm, tail, handler=handler))

        assert i == len(s)

    def load_file(self, filename, handler=None):
        self.load_string(open(filename).read(), handler)

    def dump(self, fo=sys.stdout):
        fmt = "%0" + "%dx" % ((self.wordsize + 3) // 4)
        self.root.dump(fo, fmt)

    def dive(self, priv, adr, lvl, v, getmore, r):
        while len(v) <= lvl:
            getmore(priv, adr, v)
        b = v[lvl]

        for i in r.find(b):
            if isinstance(i, InsBranch):
                for x in self.dive(priv, adr, lvl + 1, v, getmore, i):
                    yield x
                continue
            while len(v) < len(i.mask):
                getmore(priv, adr, v)
            m = True
            for j in range(lvl, len(i.mask)):
                if i.mask[j] & v[j] != i.bits[j]:
                    m = False
                    break
            if m:
                yield i

    def find(self, priv, adr, getmore):
        a = []
        for x in self.dive(priv, adr, 0, a, getmore, self.root):
            yield InsMatch(x, adr, a)

#######################################################################

if __name__ == "__main__":

    IT = InsTree(8)
    IT.load_string("""

    # This is a comment line
Foo_00	|1 1 0 0| reg	| imm		|
Foo_02a	|1 0 0 0| reg	|x1		|0| imm		|
Foo_02b	|1 0 0 0| reg	|x1		|1| imm		|
Foo_04	|1 0 0 1| reg	| imm		| {
blabla
} # Comment
Foo_03	|0 0|aaa| reg   | AB| CD | BC | {
}
Foo_01	|1 1 0 0|1 0 0 1| data		|0 0 0 0|foo	| {
}
Foo   |0 1 0 1 0 1 0 1|1 1 1 1 1 1 1 1|
Foo2  |0 ? 0 1 0 1 0 1|1 1 1 1 1 1 1 1|
#Foo_05	| ca | data		|0 0 0 0|foo	|
Foo5  |0 ? 0 1 0 1 0 1| \
	|1 1 1 1 1 1 1 1|
""")
    IT.dump()
