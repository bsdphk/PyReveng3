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

'''
Access functions for the RPN entry-database (version 2.11)

See: https://www.hpcalc.org/hp48/programming/entries/

Errors in database 2.11:

	!TurnOff - 041DA [U]
		Should be 041d4

'''

DBDIR = "/critter/Doc/HP48/EDB"

from hp48_charset import rpl_chars as C

SUBST = (
    ( "\\<)", C[0x80]),  # angle symbol
    ( "\\x-", C[0x81]),   # x with a bar
    ( "\\.V", C[0x82]),   # nabla operator
    ( "\\v/", C[0x83]),   # square root
    ( "\\.S", C[0x84]),  # integral sign
    ( "\\..", C[0x1f]), # dots/ellipsis
    ( "\\GS", C[0x85]),   # SIGMA
    ( "\\|>", C[0x86]),  # Bold triangle right
    ( "\\pi", C[0x87]),   # pi
    ( "\\.d", C[0x88]),  # partial derivative
    ( "\\<=", C[0x89]),   # <=
    ( "\\>=", C[0x8a]),   # >=
    ( "\\=/", C[0x8b]),   # !=
    ( "\\Ga", C[0x8c]),   # alpha
    ( "\\->", C[0x8d]),   # rightarrow
    ( "\\<-", C[0x8e]),   # leftarrow
    ( "\\|v", C[0x8f]), # downarrow

    ( "\\<>", "\u2094"),  # leftright arrow

    ( "\\|^", C[0x90]), # uparrow
    ( "\\Gg", C[0x91]),   # gamma
    ( "\\Gd", C[0x92]),   # delta
    ( "\\Ge", C[0x93]),   # epsilon
    ( "\\Gn", C[0x94]),   # eta
    ( "\\Gh", C[0x95]),   # theta
    ( "\\Gl", C[0x96]),   # lambda
    ( "\\Gr", C[0x97]),   # rho
    ( "\\Gs", C[0x98]),   # sigma
    ( "\\Gt", C[0x99]),   # tau
    ( "\\Gw", C[0x9a]),   # omega
    ( "\\GD", C[0x9b]),   # Delta
    ( "\\PI", C[0x9c]),   # Pi
    ( "\\GW", C[0x9d]),   # Omega
    ( "\\[]", C[0x9e]), # block cursor
    ( "\\oo", C[0x9f]),   # infinity

    # ( "\\oX", _),       # BINT symbol (NON-STANDRAD)
    ( "\\<<", "«"),       # program open
    ( "\\^o", "°"),       # degree
    ( "\\Gm", "µ"),       # mu
    ( "\\>>", "»"),       # program close
    ( "\\.x", "×"),      # times
    ( "\\0/", "\u2205"), # empty set
    ( "\\Gb", "\u03b2"),  # beta
    ( "\\:-", "\u00f7"),  # divide
    ( "\\ ", "\u2423"),   # protected whitespace

    ( "\\->", "→"),
)

class Symbol():
    def __init__(self, lines):
        self.diagram = []
        self.comment = []
        self.address = {}
        self.aka = []

        l = lines.pop(0)
        j = l.split(maxsplit=1)
        self.name = self.subst(j[0])
        if len(j) > 1:
            self.diagram.append(j[1])
            while self.diagram[-1][-1] == '\\':
                if lines[0][0] in ('.', ';'):
                    break
                self.diagram.append(lines.pop(0)[27:])
        while lines:
             l = lines.pop(0)
             if l[0] == ' ':
                self.diagram.append(l[27:])
             elif l[0] == '.':
                 j = l.split()
                 if j[1] in ("48G:", "49G:", "38G:", "39G:"):
                     if len(j[2]) == 4:
                         print("4-digit address", j)
                         continue
                     try:
                         n = int(j[2], 16)
                         self.address[j[1][:-1]] = j[2:]
                     except ValueError:
                         print("Bad address in database:", j)
                         pass
                 elif j[1] == "AKA":
                     self.aka.append(j[1:])
                 else:
                     self.comment.append(l[80:])
             elif l[0] == ';':
                 self.comment.append(l[80:])
             else:
                 assert False, ("	「" + l + "」")

    def subst(self, s):
        for i, j in SUBST:
            s = s.replace(i, j)
        return s

    def __str__(self):
        return "<SYMBOL %s>" % self.name

    def block_comment(self, pfx=""):
        t = []
        for i in self.diagram:
            i = i.rstrip('\\')
            for j in i.split("\\n"):
                j = self.subst(j)
                t.append("\t" + j.rstrip())
        if self.comment:
            t.append("")
            for i in self.comment:
                t.append(i)
        return pfx + ("\n" + pfx).join(t)
        

class RPN_EDB():

    def __init__(self, dbd=DBDIR):
        self.dir = dbd
        self.symbols = {}

        self.ingest()


    def get_lines(self):
        fi = open(self.dir + "/" + "entries.db", "r", encoding="ISO8859-15")
        for line in [x.rstrip() for x in fi.readlines()]:
            if line and line[0] not in ('*', '@',):
                yield line

    def ingest(self):
        ll = []
        for line in self.get_lines():
             if ll and line[0] not in ('.', ';', ' '):
                  s = Symbol(ll)
                  self.symbols[s.name] = s
                  ll = []
             ll.append(line)
        s = Symbol(ll)
        self.symbols[s.name] = s

    def decorate(self, m, model):
        for nm, sym in sorted(self.symbols.items()):
            a = sym.address.get(model)
            if not a:
                continue
            if '[RAM]' in a:
                continue
            adr = int(a[0], 16)
            t = nm
            if len(a) > 1:
                t += " - " + " ".join(a[1:])
            t += "\n" + "=" * len(t) + "\n"
            t += sym.block_comment("")
            if not m:
                print()
                print(t)
            for x in m.find(adr):
                if x.lo == adr:
                    m.set_label(adr, nm)
                    m.set_block_comment(adr, t)
                    break
    

if __name__ == "__main__":

   d = RPN_EDB()
   d.decorate(None, "48G")
