#!/usr/bin/env python
#
# Copyright (c) 2016-2017 Poul-Henning Kamp <phk@phk.freebsd.dk>
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
PyReveng Intermediate Language

This is not exactly LLVM's IL.  The we use it as a "generic" assembly
language for human consumption, not for precise directives to code
generators.  However, it is the intent that conversion to proper
LLVM IL a trivial exercise in dumb text-processing

"""

#######################################################################


class PILSyntaxError(Exception):
    pass


#######################################################################


class PIL_Var():
    def __init__(self, nam):
        self.nam = nam
        self.read = set()
        self.write = set()

    def __repr__(self):
        return "<PIV %s>" % self.nam

#######################################################################


class PIL_State():
    ''' The common PIL state for a language '''
    def __init__(self, lang):
        self.vars = {}
        self.lang = lang

    def var(self, n):
        i = self.vars.get(n)
        if i is None:
            i = PIL_Var(n)
            self.vars[n] = i
        return i

#######################################################################


class PIL_Stmt():
    ''' A single IL statement '''
    def __init__(self, spec, state):
        assert isinstance(state, PIL_State)
        self.state = state
        self.spec = spec
        self.decorate = None

    def render(self):
        l = []
        for i in self.spec:
            l.append(str(i))
        return " ".join(l)

    def Xoutputs(self):
        l = []
        if self.spec[1] == "=":
            l.append(self.spec[0])
        return l

    def Xinputs(self):
        l = []
        if self.spec[1] == "=":
            for i in self.spec[2:]:
                if i[0] == "%":
                    l.append(i)
        else:
            for i in self.spec:
                if i[0] == "%":
                    l.append(i)
        return l

    def X__getitem__(self, i):
        return self.spec[i]

    def X__repr__(self):
        return "<PIL %s>" % self.render()

#######################################################################


class PIL_Stmt_Assign(PIL_Stmt):
    def __init__(self, spec, state):
        super().__init__(spec, state)
        v = state.var(spec[0])
        v.write.add(self)
        spec[0] = v
        for i in range(1, len(spec)):
            if spec[i][0] == '%':
                v = state.var(spec[i])
                v.read.add(self)
                spec[i] = v

class PIL_Stmt_Flow(PIL_Stmt):
    def __init__(self, spec, state):
        super().__init__(spec, state)
        for i in range(0, len(spec)):
            if spec[i][0] == '%':
                v = state.var(spec[i])
                v.read.add(self)
                spec[i] = v

class PIL_Stmt_Store(PIL_Stmt):
    def __init__(self, spec, state):
        super().__init__(spec, state)
        for i in range(0, len(spec)):
            if spec[i][0] == '%':
                v = state.var(spec[i])
                v.read.add(self)
                spec[i] = v


class PIL_Stmt_Shift(PIL_Stmt):
    def __init__(self, spec, state):
        super().__init__(spec, state)
        for i in range(0, len(spec)):
            if spec[i][0] == '%':
                v = state.var(spec[i])
                v.read.add(self)
                spec[i] = v


class PIL_Stmt_Split(PIL_Stmt):
    def __init__(self, spec, state):
        super().__init__(spec, state)
        v = state.var(spec[2])
        v.read.add(self)
        spec[2] = v
        for i in range(3, len(spec)):
            if spec[i][0] == '%':
                v = state.var(spec[i])
                v.write.add(self)
                spec[i] = v


#######################################################################


def pil_lex(t):
    s = 0
    l = []
    for c in t:
        if s == 1 and (c.isalnum() or c in ('%', '*', '_', '.', ':')):
            w += c
            continue
        if s == 1:
            l.append(w)
            s = 0
        if s == 0 and c.isspace():
            continue
        if s == 0 and c in (',', '=', '(', ')', '-', '+'):
            l.append(c)
            continue
        if s == 0 and (c.isalnum() or c in ('%', '_', '.')):
            s = 1
            w = c
            continue
        raise PILSyntaxError(
            "PIL syntax error at '%s' state %d\n\t%s" % (c, s, t))
    if s == 1:
        l.append(w)
    return l

#######################################################################

STYP = {
    'br':       PIL_Stmt_Flow,
    'left':     PIL_Stmt_Shift,
    'right':    PIL_Stmt_Shift,
    'split':    PIL_Stmt_Split,
    'store':    PIL_Stmt_Store,
    'switch':   PIL_Stmt_Flow,
}

def pil_parse(v, state):
    x = STYP.get(v[0])
    if x is not None:
        return x(v, state)
    if len(v) > 1 and v[1] == '=':
        return PIL_Stmt_Assign(v, state)
    # print("UNP", v)
    return PIL_Stmt(v, state)

#######################################################################


class PIL_Ins():
    ''' IL statements related to a single assy/code object '''
    def __init__(self, ins):
        self.ins = ins
        self.pil = []
        self.pil_c = 0

    def pil_reg(self, r, d):
        if r[0] != "%":
            return r
        if r[1:].isdigit():
            n = "%%_i%x_%d" % (self.ins.lo, self.pil_c)
            d[r] = n
            self.pil_c += 1
            return n
        return r

    def add_il(self, ins, ll, ret=None):
        '''
        Add IL's in 'll', translating "%0" .. "%99" to unique
        names along the way.  'ret' can be one of these and
        the new unique name will be returned.
        '''
        assert isinstance(ins.lang.pil, PIL_State)
        if ll is None:
            assert ret is None
            return
        d = {}
        for l in ll:
            if l is None:
                continue
            if isinstance(l, str):
                f = pil_lex(l)
            else:
                f = l
                for i in f:
                    assert i == i.strip()
            if not f:
                continue
            v = []
            for i in f:
                j = d.get(i)
                if j is not None:
                    v.append(j)
                    continue
                j = self.pil_reg(i, d)
                if j != i:
                    v.append(j)
                    continue
                try:
                    j = getattr(ins, "pilmacro_" + i)
                except AttributeError:
                    v.append(i)
                    continue
                # self.pil.append(["/* MACRO " + i + " */"])
                k = j()
                if isinstance(k, list):
                    for x in k:
                        y = self.pil_reg(x, d)
                        v.append(y)
                elif k is not None:
                    assert isinstance(k, str)
                    x = self.pil_reg(k, d)
                    v.append(x)
            if not v:
                continue

            try:
                j = getattr(ins, "pilfunc_" + v[0])
            except AttributeError:
                self.pil.append(pil_parse(v, ins.lang.pil))
                continue
            j(v[1:])
        return d.get(ret)

    def render(self):
        t = ""
        for i in self.pil:
            t += "IL " + i.render() + "\n"
        return t

#######################################################################


class PIL_BB():
    def __init__(self):
        self.lo = None
        self.hi = None
        self.pilins = []
        self.pils = []
        self.goto = []
        self.comefrom = []
        self.doa = set()

    def __repr__(self):
        return "<BB 0x%x-0x%x>" % (self.lo, self.hi)

    def dot_flow(self, fo, pj):
        fo.write('L%x [shape="plaintext",label="%04x"]\n' % (self.lo, self.lo))
        for i in self.goto:
            if isinstance(i, PIL_BB):
                fo.write("L%x -> L%x\n" % (self.lo, i.lo))

    def dot_def(self, fo, pj):

        def bb():
            fo.write('<TR><TD ALIGN="left" BALIGN="left">\n')
            fo.write('<FONT FACE="Courier">\n')

        def ee():
            fo.write('</FONT>\n')
            fo.write("</TD></TR>\n")

        fo.write('IL%x [shape="none",label=<\n' % self.lo)
        fo.write('<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"')
        fo.write(' ALIGN="left">\n')
        fo.write('<TR><TD>0x%x-0x%x</TD></TR>\n' % (self.lo, self.hi))

        bb()
        for i in self.pilins:
            fo.write(i.render(pj).expandtabs())
            fo.write('<BR/>\n')
        ee()

        bb()
        fo.write("DOA:<BR/>\n")
        l = list(self.doa)
        l.sort()
        for i in l:
            fo.write('%s<BR/>\n' % i)
        ee()

        bb()
        fo.write("From:<BR/>\n")
        for i in self.comefrom:
            fo.write('0x%x-0x%x <BR/>\n' % (i.lo, i.hi))
        ee()

        bb()
        for i in self.pils:
            if i.decorate is not None:
                fo.write('<FONT color="%s">' % i.decorate)
            fo.write('%s' % i.render())
            if i.decorate is not None:
                fo.write('</FONT>')
            fo.write('<BR/>\n')
        ee()

        bb()
        fo.write("To:<BR/>\n")
        for i in self.goto:
            if isinstance(i, PIL_BB):
                fo.write("0x%x-0x%x<BR/>\n" % (i.lo, i.hi))
            else:
                fo.write("%s<BR/>\n" % i)
        ee()

        fo.write('</TABLE>\n')
        fo.write('>]\n')

    def whereto(self):
        j = self.pils[-1]
        if j[0] != "br":
            return [self.hi]
        l = []
        for x in range(len(j.spec)):
            if j[x] != "label":
                continue
            x += 1
            if j[x][0] == "i":
                x += 1
            if j[x][:3] == "0x-":
                continue
            if j[x][:2] == "0x":
                l.append(int(j[x], 0))
            else:
                l.append(j[x])
        return l

    def build_doa(self, init=None, color="blue"):
        nn = 0
        # print("DOA", self, color, init)
        doa = {}
        if init is not None:
            for j in init:
                doa[j] = True

        for j in self.pils:
            for x in j.outputs():
                if x[:2] == "%1":
                    doa[x] = True

        for j in reversed(self.pils):
            if j[0] == "pyreveng.void":
                doa = {}
                continue
            n = 0
            m = 0
            for x in j.outputs():
                m += 1
                z = doa.get(x)
                if z is not True:
                    n += 1
                doa[x] = True
            if n == 0 and m > 0:
                if j.decorate is None:
                    j.decorate = color
                    nn += 1
            else:
                for x in j.inputs():
                    doa[x] = False
        for i in doa:
            if i[:2] != "%1" and doa[i] is True:
                self.doa.add(i)
        return nn


if False:
    #######################################################################
    # XXX Stuff below probably belongs in separate source file(s)

    from . import assy

    #######################################################################

    class Syntax_Check():
        def __init__(self, pj, ptr):
            self.pj = pj
            self.regs = {"%A": "i8"}
            self.ptr = ptr
            self.uverbs = set()

            for j in pj.m:
                if isinstance(j, assy.Assy):
                    self.check_ins(j)

        def check_ins(self, j):
            for x in j.pil.pil:
                try:
                    self.check_il(x)
                except PILSyntaxError as bug:
                    print("")
                    print("TROUBLE:")
                    print("\t", j)
                    print("\t", x)
                    print("\t", bug)

        def do_reg(self, rn, w):
            if rn[0] != "%":
                raise PILSyntaxError(
                    "Expected register got '" + rn + "'")
            a = self.regs.get(rn)
            if a is None:
                self.regs[rn] = w
            elif a != w:
                raise PILSyntaxError(
                    "Inconsistent width " + rn + " " + a + " vs " + w)

        def expect_value(self, l, wid):
            v = l.pop(0)
            if v == "void":
                w = wid
            elif v[:9] == "pyreveng.":
                # XXX
                w = wid
                while l.pop(0) != ")":
                    continue
            elif v[:2] == "0x":
                w = int(v[2:], 16)
            elif v[0].isdigit():
                w = int(v, 10)
            elif v[0] == "%" and wid[-1] == "*":
                self.do_reg(v, self.ptr)
            elif v[0] == "%":
                self.do_reg(v, wid)
            else:
                raise PILSyntaxError(
                    ("Expected " + wid + " value got '" + v + "'"))

        def expect(self, a, b):
            if a != b:
                raise PILSyntaxError(
                    "Expected '" + a + "' got '" + b + "'")

        def expect_type(self, a):
            if a[0] != 'i':
                raise PILSyntaxError("Expected type got '" + a + "'")
            b = a[1:]
            if b[-1] == "*":
                b = b[:-1]
            w = int(b, 10)
            if w not in (1, 8, 16, 32):
                raise PILSyntaxError(
                    "Unexpected type width '" + a + "'")
            return a

        def check_br(self, l):
            self.expect('br', l.pop(0))
            if l[0] == "i1":
                l.pop(0)
                self.do_reg(l.pop(0), "i1")
                self.expect(',', l.pop(0))
                self.expect('label', l.pop(0))
                l.pop(0)
                self.expect(',', l.pop(0))
                self.expect('label', l.pop(0))
                l.pop(0)
            else:
                self.expect('label', l.pop(0))
                l.pop(0)
            if l:
                raise PILSyntaxError("Extra stuff on 'br' <%s>" % str(l))

        def check_store(self, l):
            self.expect('store', l.pop(0))
            ty = self.expect_type(l.pop(0))
            self.expect_value(l, ty)
            self.expect(',', l.pop(0))
            ty2 = self.expect_type(l.pop(0))
            if ty2 != ty + "*":
                raise PILSyntaxError(
                    "Inconsistent types in 'store' %s vs %s" % (ty, ty2))
            self.expect_value(l, ty2)
            if l:
                raise PILSyntaxError("Extra stuff on 'store' <%s>" % str(l))

        def verb_type(self, v, l):
            ty = self.expect_type(v)
            self.expect_value(l, ty)
            if l:
                raise PILSyntaxError(
                    "Extra stuff on verb '" + v + "' <%s>" % str(l))

        def verb_binary(self, v, l):
            t = self.expect_type(l.pop(0))
            self.expect_value(l, t)
            self.expect(',', l.pop(0))
            self.expect_value(l, t)
            if l:
                raise PILSyntaxError(
                    "Extra stuff on binary verb '" + v + "' <%s>" % str(l))

        def verb_load(self, v, l):
            ty = self.expect_type(l.pop(0))
            self.expect(',', l.pop(0))
            ty2 = self.expect_type(l.pop(0))
            if ty2 != ty + "*":
                raise PILSyntaxError(
                    "Inconsistent types in 'load' %s vs %s" % (ty, ty2))
            self.expect_value(l, ty2)
            if l:
                raise PILSyntaxError("Extra stuff on 'load' <%s>" % str(l))

        def verb_shift(self, v, l):
            ty = self.expect_type(l.pop(0))
            self.expect_value(l, ty)
            self.expect(',', l.pop(0))
            self.expect_value(l, ty)
            if l:
                raise PILSyntaxError(
                    "Extra stuff on shift verb '" + v + "' <%s>" % str(l))

        def verb_size(self, v, l):
            ty = self.expect_type(l.pop(0))
            self.expect_value(l, ty)
            self.expect('to', l.pop(0))
            ty2 = self.expect_type(l.pop(0))
            if l:
                raise PILSyntaxError(
                    "Extra stuff on resize verb '" + v + "' <%s>" % str(l))

        def verb_cond(self, v, l):
            cc = l.pop(0)
            if cc not in ('eq', 'ne'):
                raise PILSyntaxError(
                    "Unknown conditional '" + cc + "' <%s>" % str(l))
            ty = self.expect_type(l.pop(0))
            self.expect_value(l, ty)
            self.expect(',', l.pop(0))
            self.expect_value(l, ty)
            if l:
                raise PILSyntaxError(
                    "Extra stuff on conditional verb '" + v + "' <%s>" % str(l))

        def check_assign(self, l):
            dst = l.pop(0)
            self.expect('=', l.pop(0))

            d = {
                "i1":       self.verb_type,
                "i8":       self.verb_type,
                "i16":      self.verb_type,
                "i32":      self.verb_type,
                "and":      self.verb_binary,
                "add":      self.verb_binary,
                "sub":      elf.verb_binary,
                "or":       self.verb_binary,
                "mul":      self.verb_binary,
                "xor":      self.verb_binary,
                "load":     self.verb_load,
                "lshr":     self.verb_shift,
                "ashr":     self.verb_shift,
                "shl":      self.verb_shift,
                "trunc":    self.verb_size,
                "zext":     self.verb_size,
                "icmp":     self.verb_cond,
            }
            v = l.pop(0)
            h = d.get(v)
            if h is None and v in self.uverbs:
                return
            if h is None:
                self.uverbs.add(v)
                raise PILSyntaxError(("Unknown verb '%s'" % v))
            h(v, l)

        def check_il(self, il):
            i = 0
            l = list(il.spec)
            if l[0] == "br":
                return self.check_br(l)
            if l[0] == "store":
                return self.check_store(l)
            if l[0][0] == '%' and l[1] == '=':
                return self.check_assign(l)
            raise PILSyntaxError("No idea what this is")

    #######################################################################


    class analysis():
        def __init__(self, pj):
            self.pilbbs = {}
            self.pj = pj

            noil = {}

            # XXX: This is kind of silly

            for j in pj.m:
                if not isinstance(j, assy.Assy):
                    continue
                y = PIL_BB()
                for x in j.pil.pil:
                    y.pils.append(x)
                if not y.pils:
                    a = j.render(pj).expandtabs()
                    b = j.lim[-1].assy[0]
                    if b not in noil:
                        noil[b] = 1
                    else:
                        noil[b] += 1
                    z = PIL_Stmt(["pyreveng.void", "(", '"' + a + '"', ")"],
                                 j.lang.pil)
                    z.decorate = "magenta"
                    y.pils.append(z)
                y.lo = j.lo
                y.hi = j.hi
                y.pilins.append(j)
                self.pilbbs[j.lo] = y

            #l = list(noil.iteritems())
            l = list(noil.items())
            l.sort(key=lambda x: -x[1])
            print("Top twenty IL-deficient instructions:")
            for i, j in l[:20]:
                print("\t", i, j)

            self.build_flow()
            #for a,x in self.pilbbs.iteritems():
            for a, x in self.pilbbs.items():
                x.build_doa()
            self.propagate_doa("red")
            self.propagate_doa("green")
            for i in range(10):
                if self.propagate_doa("brown") == 0:
                    break

        def dump_bbs(self, fo):
            l = list(self.pilbbs.keys())
            l.sort()
            for j in l:
                x = self.pilbbs[j]
                fo.write("digraph {\n")
                x.dot_def(fo, self.pj)
                fo.write("}\n")
            fo.write("digraph {\n")
            for j in l:
                x = self.pilbbs[j]
                x.dot_flow(fo, self.pj)
            fo.write("}\n")

        def build_flow(self):
            #for a,x in self.pilbbs.iteritems():
            for a, x in self.pilbbs.items():
                d = x.whereto()
                for j in d:
                    if isinstance(j, int):
                        y = self.pilbbs.get(j)
                        if y is None:
                            print("None bbs", j)
                            continue
                        assert y is not None
                        y.comefrom.append(x)
                        x.goto.append(y)
                    else:
                        x.goto.append(None)
                        # print(x, j)
            l = list(self.pilbbs.keys())
            l.sort()
            for j in l:
                while True:
                    x = self.pilbbs.get(j)
                    if x is None:
                        break
                    if len(x.goto) > 1:
                        break
                    if not x.goto:
                        print("No goto", x)
                        break
                    z = x.goto[0]
                    if z is None:
                        break
                    if z.lo != x.hi:
                        break
                    y = self.pilbbs.get(x.hi)
                    assert y is not None
                    if len(y.comefrom) != 1:
                        break
                    assert y.comefrom[0] == x
                    x.pils += y.pils
                    x.hi = y.hi
                    x.pilins += y.pilins
                    for i in y.goto:
                        if isinstance(i, PIL_BB):
                            i.comefrom.remove(y)
                            i.comefrom.append(x)
                    x.goto = y.goto
                    del self.pilbbs[y.lo]

        def propagate_doa(self, color):
            n = 0
            for a, x in self.pilbbs.items():
                #print("PROP", x)
                if not x.gogo:
                    continue
                if None in x.goto:
                    continue
                dd = x.goto[0].doa
                for j in x.goto:
                    #print("\t", j, j.doa)
                    dd = dd.intersection(j.doa)
                if not dd:
                    continue
                #print("  ", dd)
                n += x.build_doa(dd, color)
            print("PROP eliminated", n)
            return n


def pil_debug(state):
    for i in state.vars.values():
        if not i.write or not i.read:
            print(i, "W", len(i.write), "R", len(i.read))
