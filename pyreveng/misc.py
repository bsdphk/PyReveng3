#!/usr/local/bin/python
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
Misc generally usable functions which don't reallly belong anywhere else
"""

from __future__ import print_function

import mem

def fill_gaps(pj):
	# First GAPs, where mem cannot be read

	def add_gap(pj, lo, hi):
		print("... adding .GAP 0x%x-0x%x" % ( lo, hi))
		x = pj.add(lo, hi, "gap")
		x.rendered = ".GAP 0x%x" % (hi - lo)
		x.compact = True

	gaps = 0
	ngaps = 0
	for i in pj.gaps():
		a = i[0]
		b = i[1]
		g0 = a
		g1 = False
		for j in range(a, b):
			try:
				x = pj.m.rd(j)
				if g1:
					add_gap(pj, g0, j)
					ngaps += 1
					gaps += j - g0
				g1 = False
			except mem.MemError:
				if not g1:
					g1 = True
					g0 = j
		if g1:
			add_gap(pj, g0, b)
			ngaps += 1
			gaps += b - g0

	if ngaps:
		print("%d GAPs containing %d bytes" % (ngaps, gaps))
