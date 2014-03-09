#!/usr/bin/env python
#

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
import listing
import data
import code
import cpu.tms9900


m = mem.byte_mem(0x0000, 0x2000)

fi = open("HP6034A_U25.hex")
for i in fi:
	j = i.split()
	m.wr(int(j[0], 16), int(j[1], 16))

pj = pyreveng.job(m, "HP6034A")

cx = cpu.tms9900.tms9981()
cx.vectors(pj, xops = 6)

for i in range(0, 12, 2):
	data.dataptr(pj, 0x230 + i, 0x232 + i, pj.m.bu16(0x230 + i))
	data.dataptr(pj, 0x248 + i, 0x24a + i, pj.m.bu16(0x248 + i))
	data.dataptr(pj, 0x254 + i, 0x256 + i, pj.m.bu16(0x254 + i))
	cx.codeptr(pj, 0x23c + i)

while pj.run():
        pass

code.lcmt_flows(pj)

listing.listing(pj, "/tmp/_.hp6034a.out", ncol = 4, fmt = "x", ascii = True)

