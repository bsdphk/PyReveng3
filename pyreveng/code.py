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
Code leaf subclasses

The code object represents an amount of memory content which is executed
somehow.  Code objects tie together with "flow" objects, which tell
where execution will continue.

It is imortant to understand that 'code' is not just assembler code
but also semi-digested token-sequences in interpreted languages, for
instance the CHIP-8 'language' on RCA1802 CPUs or the RPN code of a
HP 48 Calculator.
'''

from . import pil

from . import mem

from .exception import Invalid
from .leaf import Leaf

#######################################################################

class Flow():
    '''
    Flows connect code leaves together and captures where
    execution can go next and under what condition.
    '''
    def __init__(self, fm, typ, cond=True, to=None, lang=None):
        if lang is None:
            lang = fm.lang
        self.fm = fm
        self.lang = lang
        self.typ = typ
        self.cond = cond
        self.to = to
        self.dst = None

        if typ is True:
            self.to = fm.hi

    def propagate(self, asp):

        if self.to is not None:
            self.lang.todo.append([asp, self.to, self])

    def __repr__(self):
        s = "<Flow @0x%x " % self.fm.lo + str(self.typ)
        if self.to is None:
            s += " -"
        else:
            s += " 0x%x" % self.to
        s += ">"
        return s

    def lcmt(self, leaf):
        if self.typ is True:
            return
        s = "Flow %s" % self.typ
        if self.cond is None:
            s += " cc=?"
        elif self.cond is not True:
            s += " cc=%s" % self.cond
        if not self.to is None:
            s += " 0x%x" % self.to
        leaf.lcmt += s + "\n"


#######################################################################

def lcmt_flows(asp):
    '''
    Add line-comments for all flow records
    '''
    for i in asp:
        if isinstance(i, Code):
            for j in i.flow_out:
                j.lcmt(i)

#######################################################################

class Code(Leaf):
    '''
    A single undivisible "instruction" in some language
    '''
    def __init__(self, lo, hi, lang):
        assert isinstance(lang, Decoder)
        self.lang = lang
        super().__init__(lo, hi, lang.name)
        self.flow_in = []
        self.flow_out = []

    def render(self):
        return "<Code %x-%x %s>" % (self.lo, self.hi, self.lang.name)

    def add_flow(self, typ, cond=True, to=None, lang=None):
        '''
        Add a flow record
        '''
        f = Flow(self, typ, cond, to, lang)
        self.flow_out.append(f)

    def commit(self, asp):
        '''
        Follow the flow records to find more code
        '''
        for f in self.flow_out:
            f.propagate(asp)
        asp.insert(self)

#######################################################################

class Decoder():
    '''
    Base class for decoding code.
    '''
    def __init__(self, lang):
        assert isinstance(lang, str)
        self.lang = lang
        self.name = lang
        self.todo = []
        self.pil = pil.PIL_State(self)
        self.busy = False

    def decode(self, _asp, _adr):
        '''
        Attempt to decode at adr.

        This should return a Code object or raise Invalid

        The object shall not be pj.insert()'ed, since this function
        is used for speculative disassembly.

        Default always fails
        '''
        raise Invalid("No decoder for " + self.lang)

    def disass(self, adr, asp=None):
        '''
        Decode at adr and run with it.
        Complain if it fails.
        '''
        if asp is None:
            asp = self.m
        a0 = adr
        x = None
        xx = None
        assert isinstance(asp, mem.AddressSpace)
        self.todo.append([asp, adr, None])
        if self.busy:
            return
        self.busy = True
        while self.todo:
            asp, adr, _from = self.todo.pop()
            z = list(filter(lambda j: isinstance(j, Code) and j.lang == self, asp.find_lo(adr)))
            if not z:
                try:
                    x = self.decode(asp, adr)
                    assert isinstance(x, Code)
                    x.commit(asp)
                except Invalid:
                    print("Failed decode", self.name, "0x%x" % adr, _from)
                except mem.MemError:
                    print("No Memory", self.name, "0x%x" % adr, _from)
            else:
                x = z[0]
            if adr == a0 and x:
                xx = x
        self.busy = False
        return xx
