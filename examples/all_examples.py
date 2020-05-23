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
Run all examples
"""

import glob, os, sys, importlib
sys.path.insert(0, "..")
from pyreveng import code, listing

import cProfile

l = []
if len(sys.argv) == 1:
    l += glob.glob("*/example*.py")
else:
    for i in sys.argv[1:]:
        if i[:2] == "./":
            i = i[2:]
        if os.path.isdir(i):
            l += glob.glob(i + "/example*.py")
        else:
            l += glob.glob(i)

try:
    os.mkdir("_output")
except:
    pass

l.sort()

def one_example(dir, example):
    sys.path.append(dir)
    y = importlib.import_module(dir + "." + example)
    sys.path.pop(-1)
    nm, ms = y.example()
    for i, j in enumerate(ms):
        if len(ms) == 1:
            fn = "_output/" + nm
        else:
            fn = "_output/" + nm + ".%02d" % i
        print(i, j, fn)

        listing.Listing(
            j,
            ncol = 8,
            fn = fn + ".asm",
            pil=False,
            align_blank=True,
            align_xxx=True,
            compact_xxx=True,
        )
        if j.has_pil:
            listing.Listing(
                j,
                ncol = 8,
                fn = fn + ".pil",
                pil=True,
                align_blank=True,
                align_xxx=True,
                compact_xxx=True,
            )
    sys.stdout.flush()

def all_examples():
    for i in l:
        j = i.split("/")
        k = j[1].replace(".py", "")
        print(j[0], k)
        one_example(j[0], k)

#cProfile.run("all_examples()", sort=1)
all_examples()
