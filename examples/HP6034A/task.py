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
cx.vectors(pj, xops = 0)

def dptr(pj, a):
	v = pj.m.bu16(a)
	data.dataptr(pj, a, a + 2, v)
	return v
	

i_args = {
	0x79c:	"ii",
	0x936:	"i",
}

def inline_args(ins):
	for f in ins.flow_out:
		i = i_args.get(f.to)
		if i == None:
			continue
		ins.flow_out = []
		ins.add_flow(pj, "C", True, f.to)
		a = ins.hi
		for j in i:
			if j == "i":
				d = pj.m.bu16(a)
				data.dataptr(pj, a, a + 2, d)
				a += 2
			else:
				print("IARG:", j)
				assert False
		ins.add_flow(pj, ">", True, a)
		return

cx.flow_check.append(inline_args)

if True:

	for i in range(0, 12, 2):
		dptr(pj, 0x230 + i)
		dptr(pj, 0x248 + i)
		dptr(pj, 0x254 + i)
		cx.codeptr(pj, 0x23c + i)

if True:
	cx.vector(pj, 0x364)
	cx.vector(pj, 0x368)
	pj.todo(0x037c, cx.disass)
	pj.todo(0x038e, cx.disass)
	pj.todo(0x03aa, cx.disass)
	pj.todo(0x03ba, cx.disass)
	pj.todo(0x03ca, cx.disass)
	pj.todo(0x0406, cx.disass)
	pj.todo(0x0428, cx.disass)
	pj.todo(0x044a, cx.disass)
	pj.todo(0x0458, cx.disass)
	pj.todo(0x052e, cx.disass)

if True:
	# Pure guesswork
	for a in range(0xcee, 0xd0c, 2):
		cx.codeptr(pj, a)
	pj.todo(0x0e1e, cx.disass)

if True:
	pj.todo(0x0d18, cx.disass)
	
if True:
	pj.todo(0x0e50, cx.disass)
	pj.todo(0x0e80, cx.disass)

if True:
	pj.todo(0x10b2, cx.disass)

if True:
	for a in range(0xf4e, 0xf54, 2):
		cx.codeptr(pj, a)

if True:
	for a in range(0xf3e, 0xf42, 2):
		cx.codeptr(pj, a)

if True:
	for a in range(0x468, 0x474, 2):
		v = dptr(pj, a)
		cx.vector(pj, v)

while pj.run():
        pass

code.lcmt_flows(pj)

listing.listing(pj, "/tmp/_.hp6034a.out", ncol = 4, fmt = "x", ascii = True)

