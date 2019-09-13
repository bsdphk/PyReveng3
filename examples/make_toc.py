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

'''Build Table Of Contents
'''

import glob, os, sys, importlib
from pyreveng import code, listing

CPUS = {}

class cpu():

    def __init__(self, name, doc):
        self.name = name
        self.doc = doc.strip()
        self.examples = []
        CPUS[name] = self

    def add_example(self, example):
        self.examples.append(example)

    def render(self, fo):
        fo.write("* " + self.doc.split('\n')[0].strip() + '\n')
        fo.write("\n")
        if not self.examples:
            fo.write("(No in-project examples)\n\n")
        for i in sorted(self.examples):
            i.render(fo)

class example():
    def __init__(self, name, doc):
        self.name = name
        if doc:
            doc = doc.strip()
        self.doc = doc
        self.cpus = []

    def __lt__(self, other):
        return self.name < other.name

    def add_cpu(self, cpu):
        self.cpus.append(cpu)

    def render(self, fo):
        fo.write("  * `" + self.name + "`\n\n")
        if not self.doc:
            # print("Missing docstring in " + self.name)
            return
        fo.write("    " + self.doc.split('\n')[0].strip() + '\n\n')

for i in glob.glob("../pyreveng/cpu/*.py"):
    bn = os.path.basename(i)
    a, b = os.path.splitext(bn)
    y = importlib.import_module("pyreveng.cpu." + a)
    if y.__doc__:
        cpu(a, y.__doc__)

for j in glob.glob("*/example*.py"):
    a, b = os.path.splitext(j)
    y = importlib.import_module(a.replace('/', '.'))
    e = example(j, y.__doc__)

    for i in open(j):
        if i.find("import") == -1:
            continue
        if i.find(".cpu") == -1:
            continue
        i = i.split()
        assert i[0] == "import"
        assert i[2] == "as"
        i = i[1].split(".")
        if i[2] not in CPUS:
            print("Not in CPUS", i[2], j)
            continue
        CPUS[i[2]].add_example(e)
        e.add_cpu(CPUS[i[2]])

fo = open("/tmp/_toc", "w")
for i, j in sorted(CPUS.items()):
    j.render(fo)
