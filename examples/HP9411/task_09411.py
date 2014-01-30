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
HP9411 series VHF switche
"""

from __future__ import print_function

import os
import sys

#######################################################################
# Set up a search path to two levels below

sys.path.insert(0, os.path.abspath(os.path.join("..", "..", "pyreveng")))

#######################################################################
# Stuff we need...

import pyreveng
import mem
import code
import listing

import cpu.hp_nanoproc

def do_one(fn, alist):

	print("--------------", fn)

	m = mem.byte_mem(0x000, 0x800)

	orig_src = dict()

	labels = dict()

	def load_xx(m):
		fi = open(fn)
		for i in fi:
			if i[0] != ' ':
				continue
			j = i.strip()
			if j == "":
				continue
			j = i.split('*', 1)[0].rstrip()
			if len(j) < 15:
				continue
			if j[8] != "-":
				continue
			if not j[14].isdigit():
				continue
			if j[14:18] == '    ':
				continue
			a = int(j[14:18], 8)
			d = int(j[20:23], 8)
			orig_src[a] = j
			m.wr(a, d)
			lb = j[25:30].strip()
			if lb != "":
				labels[a] = lb
		fi.close()

	load_xx(m)

	pj = pyreveng.job(m, "HP-9411")

	dx = cpu.hp_nanoproc.hp_nanoproc()

	if True:
		for i in alist:
			pj.todo(i, dx.disass)

	pj.apct = "%04o"
	pj.apct = "%03x"

	while pj.run():
		pass

	def fixit(i, a, b):
		if i == a.lo:
			# Check if there are instructions our disass don't know
			if a.mne != b[31:34]:
				print(a.im, b)
		a.lcmt += b + "\n"

	for i,j in orig_src.items():
		x = pj.t.find_range(i, i + 1)
		if len(x[1]) > 0:
			fixit(i, x[1][0], j)
		elif len(x[0]) > 0:
			fixit(i, x[0][0], j)
		else:
			x = pj.add(i, i + 1, "origsrc")
			x.lcmt += j + "\n"
			# print(x)

	for i in labels:
		pj.set_label(i, labels[i])

	if True:
		code.lcmt_flows(pj)
	listing.listing(pj, fn="/tmp/_.HP" + fn, fmt="o", ncol=1)

do_one("09411-17002_Rev-2640.src",
	[0x0, 0xff, 0x37a, 0x387, 0x38b, 0x38e, 0x391, 0x39b, 0x3a3, 0x4e4]
)
do_one("09411-17003_Rev-2640.src",
	[0x0, 0x1d, 0xff, 0x110, 0x113, 0x1b0, 0x1b5, 0x1ba,
	0x287, 0x2e9, 0x31a, 0x400, 0x3de, 0x528]
)
do_one("09411-17004_Rev-2640.src",
	[0x0, 0x1d, 0xff, 0x110, 0x113, 0x1b0, 0x1b5, 0x1ba,
	0x2cd, 0x2e9, 0x31a, 0x344, 0x400]
)
do_one("09411-17005_Rev-2650.src",
	[0x0, 0xff, 0x37a, 0x382, 0x387, 0x38b, 0x38e, 0x39b,
	0x3a3, 0x4e4, 0x587, 0x5e8]
)
do_one("09411-17006_Rev-2650.src",
	[0x0, 0x20, 0xff, 0x110, 0x113, 0x1b0, 0x1b5, 0x1ba,
	0x2e9, 0x31a, 0x400, 0x528]
)
do_one("09411-17007_Rev-2650.src",
	[0x0, 0x20, 0xff, 0x110, 0x113, 0x1b0, 0x1b5, 0x1ba,
	0x2cd, 0x2e9, 0x31a, 0x344, 0x400]
)
