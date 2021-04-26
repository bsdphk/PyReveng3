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
Skeleton assembly code disassembler

Uses instree and handles canonical jumps, subroutine calls etc.

Prefix instructions are marked with mnemonic "+" and their
arguments are processed before the instruction.
"""

from . import instree, code, pil, mem, data

#######################################################################

Invalid = code.Invalid
Undefined = code.Undefined

class Wrong(Exception):
    pass

class Missing(Exception):
    pass

#######################################################################

class Assy(code.Code):
    def __init__(self, lo, hi, lang):
        super().__init__(lo, hi, lang)
        self.mne = "???"
        self.oper = []
        self.pil = pil.PIL_Ins(self)

    def add_il(self, ll, ret=None):
        return self.pil.add_il(self, ll, ret)

    def pildefault(self):
        return

    def render(self):
        s = self.mne + "\t"
        l = []
        for i in self.oper:
            if i is None:
                continue
            if not isinstance(i, Arg):
                print(self)
                print(self.lim)
                print(self.lang)
                print(self.mne)
                print(self.oper)
                raise Wrong("Not Arg, type '%s', str '%s'" %
                    (str(type(i)), str(i)))
            l.append(i.render())
        return s + ",".join(l)

#######################################################################

class Instree_ins(Assy):
    def __init__(self, lim, lang):
        lo = lim[0].adr
        hi = lim[-1].adr + len(lim[-1].words) * lang.scale
        super().__init__(lo, hi, lang)
        self.prefix = False
        self.cc = None
        self.dstadr = None
        self.lim = lim
        self.mne = lim[-1].assy[0]
        self.cache = {}
        self.verbatim = ()

    def args_done(self):
        return

    def flow_R(self):
        self += code.Return(cond=self.cc)

    def flow_J(self):
        self += code.Jump(to=self.dstadr)

    def flow_RC(self):
        if self.cc is not False:
            self += code.Return(cond=str(self.cc))
        if self.cc is not True:
            self += code.Next(to=self.hi, cond="!" + str(self.cc))

    def flow_JC(self):
        if self.cc is not False:
            self += code.Jump(cond=str(self.cc), to=self.dstadr)
        if self.cc is not True:
            self += code.Next(to=self.hi, cond="!" + str(self.cc))

    def flow_C(self):
        self += code.Call(to=self.dstadr)
        self += code.Next(to=self.hi)

    def arg(self, arg):
        if arg in self.lang.verbatim:
            self.oper.append(Arg_verbatim(arg))
            return

        if arg == "-":
            return

        if arg == ">U":
            raise Undefined()

        if arg == "?":
            for i in self.lim:
                self.oper.append(Arg_verbatim(str(i.flds)))
            return

        x = None
        if arg[0] == ">":
            try:
                x = getattr(self, "flow_" + arg[1:])
            except AttributeError:
                x = None
        if x is None:
            try:
                x = getattr(self, "assy_" + arg)
            except AttributeError:
                x = None
        if x is None:
            x = "?" + arg + "?"
            print(self.im, "ERROR: ARG <%s> not translated" % arg)
        if not isinstance(x, str):
            x = x()
        if isinstance(x, str):
            x = Arg_verbatim(x)
        if x is None:
            return
        if isinstance(x, list):
            for i in x:
                if isinstance(i, Arg):
                    self.oper.append(i)
                elif isinstance(i, str):
                    self.oper.append(Arg_verbatim(i))
                else:
                    print(self)
                    print(self.lim)
                    print(self.lang)
                    raise Wrong("Not Arg, type '%s', str '%s'" %
                        (str(type(i)), str(i)))

        elif not isinstance(x, Arg):
            print(self)
            print(self.lim)
            print(self.lang)
            raise Wrong("Not Arg, type '%s', str '%s'" %
                (str(type(x)), str(x)))
        else:
            self.oper.append(x)

    def parse(self):
        if self.mne[0] == "+":
            self.prefix = True
        self.oper = list()
        for self.im in self.lim:
            i = self.im.assy
            for j in i[1].split(","):
                try:
                    self.arg(j)
                except KeyError as e:
                    print("XXX Failure processing arg", j, "in", self.lim)
                    print("XXX", e)

        self.args_done()

        if not self.flow_out:
            self += code.Next(to=self.hi)

    def get(self, f):
        return self.lim[-1].get(f)

    def __getitem__(self, f):
        return self.lim[-1][f]

    def __setitem__(self, f, v):
        self.lim[-1][f] = v

#######################################################################

class Instree_disass(code.Decoder):
    def __init__(
        self,
        name,
        ins_word=8,
        mem_word=None,
        endian=None,
        abits=None,
        vectors=None,
        jmps=None,
    ):
        super().__init__(name)
        if mem_word is None:
            mem_word = ins_word

        self.ins_word = ins_word
        self.mem_word = mem_word
        self.endian = endian
        self.scale = ins_word // mem_word
        self.vectordat = vectors
        self.jmpdat = jmps

        if ins_word == mem_word:
            self.getmore = self.getmore_word
        elif ins_word == 16 and mem_word == 8 and endian == "<":
            self.getmore = self.getmore_lu16
        elif ins_word == 16 and mem_word == 8 and endian == ">":
            self.getmore = self.getmore_bu16
        elif ins_word == 32 and mem_word == 8 and endian == "<":
            self.getmore = self.getmore_lu32
        elif ins_word == 32 and mem_word == 8 and endian == ">":
            self.getmore = self.getmore_bu32
        else:
            raise Exception("XXX: No getmore() [%d/%d/%s]" %
                    (ins_word, mem_word, endian))

        if endian == "<" and abits == 16:
            self.codeptr = self.codeptr_lu16
        elif endian == ">" and abits == 16:
            self.codeptr = self.codeptr_bu16
        elif endian == "<" and abits == 32:
            self.codeptr = self.codeptr_lu32
        elif endian == ">" and abits == 32:
            self.codeptr = self.codeptr_bu32
        elif abits == 8:
            self.codeptr = self.codeptr_8

        self.flow_check = []
        self.verbatim = ()
        self.it = instree.InsTree(ins_word)
        self.m = None

        self.aspace = {}
        if abits is not None:
            self.add_as("mem", "Memory", bits = abits)

    def codeptr_8(self, adr, asp=None):
        if asp is None:
            asp = self.m
        t = asp[adr]
        c = data.Codeptr(asp, adr, adr + 1, t)
        self.disass(t, asp=asp)
        return c

    def codeptr_lu16(self, adr, asp=None):
        if asp is None:
            asp = self.m
        t = asp.lu16(adr)
        c = data.Codeptr(asp, adr, adr + 2, t)
        self.disass(t, asp=asp)
        return c

    def codeptr_bu16(self, adr, asp=None):
        if asp is None:
            asp = self.m
        t = asp.bu16(adr)
        c = data.Codeptr(asp, adr, adr + 2, t)
        self.disass(t, asp=asp)
        return c

    def codeptr_lu32(self, adr, asp=None):
        if asp is None:
            asp = self.m
        t = asp.lu32(adr)
        c = data.Codeptr(asp, adr, adr + 4, t)
        self.disass(t, asp=asp)
        return c

    def codeptr_bu32(self, adr, asp=None):
        if asp is None:
            asp = self.m
        t = asp.bu32(adr)
        c = data.Codeptr(asp, adr, adr + 4, t)
        self.disass(t, asp=asp)
        return c

    def vectors(self, which=None):
        if self.vectordat:
            for i, j in self.vectordat:
                if which is None or i in which or j in which:
                     y = self.codeptr(i)
                     y.lcmt = "Vector " + j
                     self.m.set_label(y.dst, j)
        if self.jmpdat:
            for i, j in self.jmpdat:
                if which is None or i in which or j in which:
                     self.m.set_label(i, j)
                     self.disass(i)

    def add_as(self, name, desc=None, bits=None, lo=None, hi=None, aspace=None):
        if bits is not None:
            lo = 0
            hi = 1 << bits
        if aspace is None:
            aspace = mem.MemMapper(lo, hi, name=desc)
        self.aspace[name] = aspace
        if name == "mem":
            self.m = aspace
        setattr(self, "as_" + name, aspace)

    def add_ins(self, desc, ins):
        assert issubclass(ins, Instree_ins)
        self.it.load_string(desc, ins)

    def getmore_word(self, asp, adr, v):
        v.append(asp[adr + len(v)])

    def getmore_lu16(self, asp, adr, v):
        v.append(asp.lu16(adr + len(v) * 2))

    def getmore_bu16(self, asp, adr, v):
        v.append(asp.bu16(adr + len(v) * 2))

    def getmore_lu32(self, asp, adr, v):
        v.append(asp.lu32(adr + len(v) * 4))

    def getmore_bu32(self, asp, adr, v):
        v.append(asp.bu32(adr + len(v) * 4))

    def decode(self, asp, adr, l=None):
        if l is None:
            l = []
        for x in self.it.find(asp, adr, getmore=self.getmore):
            assert x.handler is not None
            if l and not issubclass(x.handler, l[-1].handler):
                continue
            l.append(x)
            try:
                y = x.handler(l, self)
                y.parse()
            except Undefined as e:
                raise Invalid(asp.adr(adr) +
                    " Undefined " + self.name + " instruction")
            except Invalid as e:
                l.pop(-1)
                continue
            except:
                print(x)
                print(x.handler)
                raise
            if y.prefix:
                try:
                    y = self.decode(asp, adr + len(x.words) * self.scale, l)
                except Undefined as e:
                    raise Invalid(asp.adr(adr) +
                        " Undefined " + self.name + " instruction")
                except Invalid as e:
                    l.pop(-1)
                    continue
                assert y is not None
                return y

            z = y.im.pil.pilspec
            if z is not None:
                y.add_il(z.split("\n"))
            else:
                y.pildefault()
            for i in self.flow_check:
                i(asp, y)
            return y
        raise Invalid(asp.adr(adr) +
            " No matching " + self.name + " instruction")


#######################################################################

class Arg():

    def render(self):
        return str(self)

class Arg_verbatim(Arg):
    def __init__(self, txt):
        super().__init__()
        self.txt = txt

    def __str__(self):
        return self.txt

class Arg_dst(Arg):
    def __init__(self, asp, dst, pfx="", sfx=""):
        super().__init__()
        self.dst = dst
        self.asp = asp
        self.pfx = pfx
        self.sfx = sfx

    def __str__(self):
        if self.dst is None:
            return self.pfx + "0x?" + self.sfx
        l = list(self.asp.get_labels(self.dst))
        if l:
            return self.pfx + "%s" % l[0] + self.sfx
        return self.pfx + self.asp.adr(self.dst) + self.sfx

class Arg_ref(Arg):
    def __init__(self, asp, obj):
        super().__init__()
        self.obj = obj
        self.asp = asp

    def __str__(self):
        s = "(" + self.asp.adr(self.obj.lo) + ")"
        a = self.obj.arg_render()
        if a != "":
            s += "=" + a
        return s

class Arg_imm(Arg):
    def __init__(self, val, wid=0):
        super().__init__()
        self.val = val
        self.wid = wid
        assert wid & 3 == 0

    def __str__(self):
        s = "#0x%"
        if self.wid:
            s += "0%d" % (self.wid / 4)
        s += "x"
        return s % self.val
