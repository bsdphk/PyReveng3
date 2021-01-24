#!/usr/bin/env python #
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

'''Rational R1000 - Ada Processor

This is very much a research project as we have next to no documentation
of the machine code.

What we have are pages 27-48 inclusive in the GC1 document reference
listed below.

That document contains a very interesting Ada defition of "package
Machine_Code" (p35-39) but so far attempts to reduce that to numerical
values corresponding to the example (p41-46) has failed, and to
complicate matters, it is not obvious how much hand-editing the
example has been subject to.

A few instructions have revealed themselves to be return instructions,
by dint of making a mess of things if they are not.

Apart from that, new researchers can start here...

Document references:
--------------------

   GC1:
	R1000_Guru_Course_01_Basic.pdf
	https://datamuseum.dk/wiki/Bits:30000916

   FEH:
	R1000_FE_Handbook.pdf
	https://datamuseum.dk/wiki/Bits:30000964


'''

import struct

from pyreveng import assy, data, code

# This is the instruction set as partitioned by the two "decode rams"
# mentioned on pdf page 69 of "R1000_HARDWARE_FUNCTIONAL_SPECIFICATION"
#	https://datamuseum.dk/bits/30000971
# using the content of 'M207_54.M200_UCODE'
#
# Comment entries out as the are "overtaken" by "real" entries in r1000_desc below

ucode_desc = '''
#QQucode_0x0000		-	|0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0| zero_is_invalid_ins
QQucode_0x0001		-	|0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1|
QQucode_0x0002		-	|0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0|
QQucode_0x0003		-	|0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1|
QQucode_0x0004		-	|0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0|
QQucode_0x0005		-	|0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 1|
QQucode_0x0006		-	|0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 0|
#QQucode_0x0007		-	|0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 1| ACTION BREAK_OPTIONAL
QQucode_0x0008		-	|0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0|
QQucode_0x0009		-	|0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 1|
QQucode_0x0009		-	|0 0 0 0 0 0 0 0 0 0 0 0 1 0 1 1|
QQucode_0x0009		-	|0 0 0 0 0 0 0 0 0 0 0 0 1 1 0 1|
QQucode_0x000a		-	|0 0 0 0 0 0 0 0 0 0 0 0 1 0 1 0|
QQucode_0x000a		-	|0 0 0 0 0 0 0 0 0 0 0 0 1 1 0 0|
QQucode_0x000a		-	|0 0 0 0 0 0 0 0 0 0 0 0 1 1 1 0|
QQucode_0x000f		-	|0 0 0 0 0 0 0 0 0 0 0 0 1 1 1 1|
QQucode_0x0010		-	|0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0|
QQucode_0x0011		-	|0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1|
QQucode_0x0012		-	|0 0 0 0 0 0 0 0 0 0 0 1 0 0 1 0|
QQucode_0x0013		-	|0 0 0 0 0 0 0 0 0 0 0 1 0 0 1 1|
QQucode_0x0014		-	|0 0 0 0 0 0 0 0 0 0 0 1 0 1 0 0|
QQucode_0x0015		-	|0 0 0 0 0 0 0 0 0 0 0 1 0 1 0 1|
QQucode_0x0016		-	|0 0 0 0 0 0 0 0 0 0 0 1 0 1 1 0|
QQucode_0x0017		-	|0 0 0 0 0 0 0 0 0 0 0 1 0 1 1 1|
QQucode_0x0018		-	|0 0 0 0 0 0 0 0 0 0 0 1 1 0 0 0|
QQucode_0x0019		-	|0 0 0 0 0 0 0 0 0 0 0 1 1 0 0 1|
QQucode_0x001a		-	|0 0 0 0 0 0 0 0 0 0 0 1 1 0 1 0|
QQucode_0x001b		-	|0 0 0 0 0 0 0 0 0 0 0 1 1 0 1 1|
QQucode_0x001c		-	|0 0 0 0 0 0 0 0 0 0 0 1 1 1 0 0|
QQucode_0x001d		-	|0 0 0 0 0 0 0 0 0 0 0 1 1 1 0 1|
QQucode_0x001e		-	|0 0 0 0 0 0 0 0 0 0 0 1 1 1 1 0|
QQucode_0x001f		-	|0 0 0 0 0 0 0 0 0 0 0 1 1 1 1 1|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 0 0 0 1 0|x      |
QQucode_bogus		i	|0 0 0 0 0 0 0 0 0 0 1 1 0 0 0 0|
QQucode_bogus		i	|0 0 0 0 0 0 0 0 0 0 1 1 0 1 1 1|
QQucode_bogus		i	|0 0 0 0 0 0 0 0 0 0 1 1 1 0 0 0|
QQucode_bogus		i	|0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1|
QQucode_bogus		i	|0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0|
QQucode_bogus		i	|0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1|
QQucode_bogus		i	|0 0 0 0 0 0 0 0 0 1 0 0 1 0 0 0|
QQucode_bogus		i	|0 0 0 0 0 0 0 0 0 1 0 0 1 1 1 1|
QQucode_bogus		i	|0 0 0 0 0 0 0 0 0 1 0 1 0 0 0 0|
QQucode_bogus		i	|0 0 0 0 0 0 0 0 0 1 0 1 0 1 1 1|
QQucode_bogus		i	|0 0 0 0 0 0 0 0 0 1 0 1 1 0 0 0|
QQucode_bogus		i	|0 0 0 0 0 0 0 0 0 1 0 1 1 1 1 1|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 0 0 1 1 0 0|x    |
QQucode_bogus		i	|0 0 0 0 0 0 0 0 0 1 1 1 0 1 1 1|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 0 0 1 1 1 1|x    |
QQucode_bogus		i	|0 0 0 0 0 0 0 0 1 0 0 0 0 0 1 1|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 0 1 0 0 0 0 1 0|x|
QQucode_bogus		i	|0 0 0 0 0 0 0 0 1 0 0 0 0 1 1 0|
QQucode_bogus		i	|0 0 0 0 0 0 0 0 1 0 0 1 0 1 0 0|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 0 1 0 1 0 1 1 1|x|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 0 1 0 1 1 0 0 0|x|
QQucode_bogus		i	|0 0 0 0 0 0 0 0 1 0 1 1 0 0 1 0|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 0 1 1 0 0 0 0|x  |
QQucode_bogus		i	|0 0 0 0 0 0 0 0 1 1 0 1 1 1 1 1|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 0 0 0 0 0 0 1|x|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 0 0 0 0 0 1 0|x|
QQucode_bogus		i	|0 0 0 0 0 0 0 1 0 0 0 0 1 0 0 0|
#QQucode_bogus		i	|0 0 0 0 0 0 0 1 0 0 0 1 0 0 1 1| # Check if valid???
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 0 0 1 1 0 0 0|x|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 0 0 1 1 0 1 0|x|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 0 0 1 1 1 0|x  |
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 0 1 0 1 0|x    |
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 0 1 0 1 1 0 0|x|
QQucode_bogus		i	|0 0 0 0 0 0 0 1 0 1 0 1 1 0 1 0|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 0 1 1 1 0 0|x  |
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 0 1 1 1 0 1 0|x|
QQucode_bogus		i	|0 0 0 0 0 0 0 1 0 1 1 1 0 1 1 0|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 1 0 0 0 0|x    |
#QQucode_bogus		i	|0 0 0 0 0 0 0 1 1 0 0 0 1 0 0 0| # ???
#QQucode_bogus		i	|0 0 0 0 0 0 0 1 1 0 0 0 1 1 0 0| # ???
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 1 0 0 1 0|x    |
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 1 0 0 1 1 0 0|x|
QQucode_bogus		i	|0 0 0 0 0 0 0 1 1 0 0 1 1 0 1 0|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 1 0 1 0 0 0 0|x|
QQucode_bogus		i	|0 0 0 0 0 0 0 1 1 0 1 0 0 0 1 0|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 1 0 1 1 0|x    |
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 1 0 1 1 1 0|x  |
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 1 0 1 1 1 1 0|x|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 1 1 0 0 1 0 0|x|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 1 1 1 0 0|x    |
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 1 1 1 0 1 0 0|x|
QQucode_bogus		i	|0 0 0 0 0 0 0 1 1 1 1 0 1 0 1 0|
QQucode_bogus		i,x	|0 0 0 0 0 0 0 1 1 1 1 1 0 0 0|x|
QQucode_bogus		i	|0 0 0 0 0 0 0 1 1 1 1 1 0 0 1 0|
QQucode_bogus		i,x	|0 0 0 0 0 0 1 0 0 0 0 0 0 0|x  |
QQucode_bogus		i	|0 0 0 0 0 0 1 0 0 0 0 0 0 1 0 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 0 0 0 0 0 0 1 1 1|
QQucode_bogus		i,x	|0 0 0 0 0 0 1 0 1 0 0 0|x      |
QQucode_bogus		i,x	|0 0 0 0 0 0 1 0 1 0 0 1 0|x    |
QQucode_bogus		i	|0 0 0 0 0 0 1 0 1 0 0 1 1 0 0 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 0 1 0 1 0 0 0 0 1|
QQucode_bogus		i	|0 0 0 0 0 0 1 0 1 0 1 0 0 0 1 1|
QQucode_bogus		i,x	|0 0 0 0 0 0 1 0 1 0 1 0 0 1 1|x|
QQucode_bogus		i,x	|0 0 0 0 0 0 1 0 1 0 1 0 1 1|x  |
QQucode_bogus		i,x	|0 0 0 0 0 0 1 0 1 0 1 1 0|x    |
QQucode_bogus		i,x	|0 0 0 0 0 0 1 0 1 0 1 1 1 0|x  |
QQucode_bogus		i,x	|0 0 0 0 0 0 1 0 1 0 1 1 1 1 0|x|
QQucode_bogus		i,x	|0 0 0 0 0 0 1 0 1 1 0 0 0 0|x  |
QQucode_bogus		i,x	|0 0 0 0 0 0 1 0 1 1 0 0 0 1 0|x|
QQucode_bogus		i	|0 0 0 0 0 0 1 0 1 1 0 0 1 0 0 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 0 1 1 0 0 1 0 1 0|
QQucode_bogus		i,x	|0 0 0 0 0 0 1 0 1 1 0 0 1 1 0|x|
QQucode_bogus		i,x	|0 0 0 0 0 0 1 0 1 1 0 1|x      |
QQucode_bogus		i,x	|0 0 0 0 0 0 1 0 1 1 1 0|x      |
QQucode_bogus		i,x	|0 0 0 0 0 0 1 0 1 1 1 1 0|x    |
QQucode_bogus		i,x	|0 0 0 0 0 0 1 0 1 1 1 1 1 0 0|x|
QQucode_bogus		i	|0 0 0 0 0 0 1 0 1 1 1 1 1 0 1 0|
QQucode_bogus		i,x	|0 0 0 0 0 0 1 1 0 0 0 0 0 0 0|x|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 0 0 0 0 0 1 0|
QQucode_bogus		i,x	|0 0 0 0 0 0 1 1 0 0 0 0 1|x    |
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 0 0 1 0 0 0 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 0 0 1 0 0 1 1|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 0 0 1 0 1 0 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 0 0 1 0 1 1 1|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 0 0 1 1 0 1 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 0 0 1 1 1 1 1|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 0 1 0 0 0 1 1|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 0 1 0 1 0 0 1|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 0 1 0 1 1 0 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 0 1 0 1 1 1 1|
QQucode_bogus		i,x	|0 0 0 0 0 0 1 1 0 0 1 1 0 0 0|x|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 0 1 1 0 0 1 0|
QQucode_bogus		i,x	|0 0 0 0 0 0 1 1 0 0 1 1 1|x    |
QQucode_bogus		i,x	|0 0 0 0 0 0 1 1 0 1 0 0 0 1 0|x|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 1 0 0 1 0 1 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 1 0 0 1 1 0 1|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 1 0 1 0 0 1 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 1 0 1 0 1 1 1|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 1 0 1 1 0 1 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 1 0 1 1 1 1 1|
QQucode_bogus		i,x	|0 0 0 0 0 0 1 1 0 1 1 0 0|x    |
QQucode_bogus		i,x	|0 0 0 0 0 0 1 1 0 1 1 0 1 0 0|x|
QQucode_bogus		i,x	|0 0 0 0 0 0 1 1 0 1 1 1 0 0|x  |
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 1 1 1 0 1 0 1|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 1 1 1 0 1 1 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 1 1 1 1 0 0 1|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 1 1 1 1 1 0 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 0 1 1 1 1 1 1 1|
QQucode_bogus		i,x	|0 0 0 0 0 0 1 1 1 0 0 0 0 0|x  |
QQucode_bogus		i,x	|0 0 0 0 0 0 1 1 1 0 0 0 1 0|x  |
QQucode_bogus		i,x	|0 0 0 0 0 0 1 1 1 0 0 1 0 0|x  |
QQucode_bogus		i	|0 0 0 0 0 0 1 1 1 0 0 1 0 1 0 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 1 0 1 0 1 0 1 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 1 0 1 0 1 1 1 1|
QQucode_bogus		i,x	|0 0 0 0 0 0 1 1 1 0 1 1 0 0|x  |
QQucode_bogus		i	|0 0 0 0 0 0 1 1 1 0 1 1 0 1 0 0|
QQucode_bogus		i,x	|0 0 0 0 0 0 1 1 1 1 0 0 0 0|x  |
QQucode_bogus		i,x	|0 0 0 0 0 0 1 1 1 1 0 0 1 0|x  |
QQucode_bogus		i	|0 0 0 0 0 0 1 1 1 1 0 1 0 0 0 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 1 1 0 1 0 1 1 1|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 1 1 1 0 0 0 1 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 1 1 1 0 0 1 1 1|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 1 1 1 1 0 1 0 0|
QQucode_bogus		i	|0 0 0 0 0 0 1 1 1 1 1 1 1 1 1 1|
#QQucode_0x0031		-	|0 0 0 0 0 0 0 0 0 0 1 1 0 0 0 1|
#QQucode_0x0032		-	|0 0 0 0 0 0 0 0 0 0 1 1 0 0 1 0|
#QQucode_0x0033		-	|0 0 0 0 0 0 0 0 0 0 1 1 0 0 1 1|
#QQucode_0x0034		-	|0 0 0 0 0 0 0 0 0 0 1 1 0 1 0 0|
#QQucode_0x0035		-	|0 0 0 0 0 0 0 0 0 0 1 1 0 1 0 1|
#QQucode_0x0036		-	|0 0 0 0 0 0 0 0 0 0 1 1 0 1 1 0|
#QQucode_0x0039		-	|0 0 0 0 0 0 0 0 0 0 1 1 1 0 0 1| STORE_TOP Access_TYPE, 1
#QQucode_0x003a		-	|0 0 0 0 0 0 0 0 0 0 1 1 1 0 1 0|
#QQucode_0x003b		-	|0 0 0 0 0 0 0 0 0 0 1 1 1 0 1 1|
#QQucode_0x003c		-	|0 0 0 0 0 0 0 0 0 0 1 1 1 1 0 0|
#QQucode_0x003d		-	|0 0 0 0 0 0 0 0 0 0 1 1 1 1 0 1|
#QQucode_0x003e		-	|0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 0|
#QQucode_0x0041		-	|0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 1| STORE_TOP_UNCHECKED FLOAT, 1
#QQucode_0x0042		-	|0 0 0 0 0 0 0 0 0 1 0 0 0 0 1 0|                          , 2 
#QQucode_0x0043		-	|0 0 0 0 0 0 0 0 0 1 0 0 0 0 1 1|
#QQucode_0x0044		-	|0 0 0 0 0 0 0 0 0 1 0 0 0 1 0 0|
#QQucode_0x0045		-	|0 0 0 0 0 0 0 0 0 1 0 0 0 1 0 1|
#QQucode_0x0046		-	|0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 0|
#QQucode_0x0049		-	|0 0 0 0 0 0 0 0 0 1 0 0 1 0 0 1|
#QQucode_0x004a		-	|0 0 0 0 0 0 0 0 0 1 0 0 1 0 1 0|
#QQucode_0x004b		-	|0 0 0 0 0 0 0 0 0 1 0 0 1 0 1 1|
#QQucode_0x004c		-	|0 0 0 0 0 0 0 0 0 1 0 0 1 1 0 0|
#QQucode_0x004d		-	|0 0 0 0 0 0 0 0 0 1 0 0 1 1 0 1|
#QQucode_0x004e		-	|0 0 0 0 0 0 0 0 0 1 0 0 1 1 1 0|
#QQucode_0x0051		-	|0 0 0 0 0 0 0 0 0 1 0 1 0 0 0 1|
#QQucode_0x0052		-	|0 0 0 0 0 0 0 0 0 1 0 1 0 0 1 0| QQu_Unknown_Store_1
#QQucode_0x0053		-	|0 0 0 0 0 0 0 0 0 1 0 1 0 0 1 1|
#QQucode_0x0054		-	|0 0 0 0 0 0 0 0 0 1 0 1 0 1 0 0|
#QQucode_0x0055		-	|0 0 0 0 0 0 0 0 0 1 0 1 0 1 0 1|
#QQucode_0x0056		-	|0 0 0 0 0 0 0 0 0 1 0 1 0 1 1 0|
#QQucode_0x0059		-	|0 0 0 0 0 0 0 0 0 1 0 1 1 0 0 1|
#QQucode_0x005a		-	|0 0 0 0 0 0 0 0 0 1 0 1 1 0 1 0| QQu_Unknown_Store_2
#QQucode_0x005b		-	|0 0 0 0 0 0 0 0 0 1 0 1 1 0 1 1|
#QQucode_0x005c		-	|0 0 0 0 0 0 0 0 0 1 0 1 1 1 0 0|
#QQucode_0x005d		-	|0 0 0 0 0 0 0 0 0 1 0 1 1 1 0 1|
#QQucode_0x005e		-	|0 0 0 0 0 0 0 0 0 1 0 1 1 1 1 0|
#QQucode_0x0068		-	|0 0 0 0 0 0 0 0 0 1 1 0 1 0 0 0|
#QQucode_0x0069		-	|0 0 0 0 0 0 0 0 0 1 1 0 1 0 0 1|
#QQucode_0x006a		-	|0 0 0 0 0 0 0 0 0 1 1 0 1 0 1 0|
#QQucode_0x006b		-	|0 0 0 0 0 0 0 0 0 1 1 0 1 0 1 1|
#QQucode_0x006c		-	|0 0 0 0 0 0 0 0 0 1 1 0 1 1 0 0|
#QQucode_0x006d		-	|0 0 0 0 0 0 0 0 0 1 1 0 1 1 0 1|
#QQucode_0x006e		-	|0 0 0 0 0 0 0 0 0 1 1 0 1 1 1 0|
#QQucode_0x006f		-	|0 0 0 0 0 0 0 0 0 1 1 0 1 1 1 1| ACTION BREAK_UNCONDITIONAL
#QQucode_0x0070		x	|0 0 0 0 0 0 0 0 0 1 1 1 0 0|x  |
#QQucode_0x0070		-	|0 0 0 0 0 0 0 0 0 1 1 1 0 1 0 0|
#QQucode_0x0075		-	|0 0 0 0 0 0 0 0 0 1 1 1 0 1 0 1|
#QQucode_0x0076		-	|0 0 0 0 0 0 0 0 0 1 1 1 0 1 1 0|
#QQucode_0x0080		-	|0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0|
#QQucode_0x0081		-	|0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1|
#QQucode_0x0082		-	|0 0 0 0 0 0 0 0 1 0 0 0 0 0 1 0|
#QQucode_0x0087		-	|0 0 0 0 0 0 0 0 1 0 0 0 0 1 1 1|
#QQucode_0x0088		-	|0 0 0 0 0 0 0 0 1 0 0 0 1 0 0 0|
#QQucode_0x0089		-	|0 0 0 0 0 0 0 0 1 0 0 0 1 0 0 1|
#QQucode_0x008a		-	|0 0 0 0 0 0 0 0 1 0 0 0 1 0 1 0|
#QQucode_0x008b		-	|0 0 0 0 0 0 0 0 1 0 0 0 1 0 1 1|
#QQucode_0x008c		-	|0 0 0 0 0 0 0 0 1 0 0 0 1 1 0 0|
#QQucode_0x008d		-	|0 0 0 0 0 0 0 0 1 0 0 0 1 1 0 1|
#QQucode_0x008e		-	|0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 0|
#QQucode_0x008f		-	|0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1|
#QQucode_0x0090		-	|0 0 0 0 0 0 0 0 1 0 0 1 0 0 0 0|
#QQucode_0x0091		-	|0 0 0 0 0 0 0 0 1 0 0 1 0 0 0 1|
#QQucode_0x0092		-	|0 0 0 0 0 0 0 0 1 0 0 1 0 0 1 0|
#QQucode_0x0093		-	|0 0 0 0 0 0 0 0 1 0 0 1 0 0 1 1|
#QQucode_0x0095		-	|0 0 0 0 0 0 0 0 1 0 0 1 0 1 0 1|
#QQucode_0x0096		-	|0 0 0 0 0 0 0 0 1 0 0 1 0 1 1 0|
#QQucode_0x0097		-	|0 0 0 0 0 0 0 0 1 0 0 1 0 1 1 1|
#QQucode_0x0098		-	|0 0 0 0 0 0 0 0 1 0 0 1 1 0 0 0|
#QQucode_0x0099		-	|0 0 0 0 0 0 0 0 1 0 0 1 1 0 0 1|
#QQucode_0x009a		-	|0 0 0 0 0 0 0 0 1 0 0 1 1 0 1 0|
#QQucode_0x009b		-	|0 0 0 0 0 0 0 0 1 0 0 1 1 0 1 1|
#QQucode_0x009c		-	|0 0 0 0 0 0 0 0 1 0 0 1 1 1 0 0|
#QQucode_0x009d		-	|0 0 0 0 0 0 0 0 1 0 0 1 1 1 0 1|
#QQucode_0x009e		-	|0 0 0 0 0 0 0 0 1 0 0 1 1 1 1 0|
#QQucode_0x009f		-	|0 0 0 0 0 0 0 0 1 0 0 1 1 1 1 1|
#QQucode_0x00a0		-	|0 0 0 0 0 0 0 0 1 0 1 0 0 0 0 0|
#QQucode_0x00a1		-	|0 0 0 0 0 0 0 0 1 0 1 0 0 0 0 1|
#QQucode_0x00a2		-	|0 0 0 0 0 0 0 0 1 0 1 0 0 0 1 0|
#QQucode_0x00a3		-	|0 0 0 0 0 0 0 0 1 0 1 0 0 0 1 1|
#QQucode_0x00a4		-	|0 0 0 0 0 0 0 0 1 0 1 0 0 1 0 0|
#QQucode_0x00a5		-	|0 0 0 0 0 0 0 0 1 0 1 0 0 1 0 1|
#QQucode_0x00a6		-	|0 0 0 0 0 0 0 0 1 0 1 0 0 1 1 0|
#QQucode_0x00a7		-	|0 0 0 0 0 0 0 0 1 0 1 0 0 1 1 1|
#QQucode_0x00a8		-	|0 0 0 0 0 0 0 0 1 0 1 0 1 0 0 0|
#QQucode_0x00a9		-	|0 0 0 0 0 0 0 0 1 0 1 0 1 0 0 1|
#QQucode_0x00aa		-	|0 0 0 0 0 0 0 0 1 0 1 0 1 0 1 0|
#QQucode_0x00ab		-	|0 0 0 0 0 0 0 0 1 0 1 0 1 0 1 1|
#QQucode_0x00ac		-	|0 0 0 0 0 0 0 0 1 0 1 0 1 1 0 0|
#QQucode_0x00ad		-	|0 0 0 0 0 0 0 0 1 0 1 0 1 1 0 1|
#QQucode_0x00b3		-	|0 0 0 0 0 0 0 0 1 0 1 1 0 0 1 1|
#QQucode_0x00b4		-	|0 0 0 0 0 0 0 0 1 0 1 1 0 1 0 0|
#QQucode_0x00b5		-	|0 0 0 0 0 0 0 0 1 0 1 1 0 1 0 1|
#QQucode_0x00b6		-	|0 0 0 0 0 0 0 0 1 0 1 1 0 1 1 0|
#QQucode_0x00b7		-	|0 0 0 0 0 0 0 0 1 0 1 1 0 1 1 1|
#QQucode_0x00b8		-	|0 0 0 0 0 0 0 0 1 0 1 1 1 0 0 0|
#QQucode_0x00b9		-	|0 0 0 0 0 0 0 0 1 0 1 1 1 0 0 1|
#QQucode_0x00ba		-	|0 0 0 0 0 0 0 0 1 0 1 1 1 0 1 0|
#QQucode_0x00bb		-	|0 0 0 0 0 0 0 0 1 0 1 1 1 0 1 1| ACTION SIGNAL_COMPLETION,>R
#QQucode_0x00bc		-	|0 0 0 0 0 0 0 0 1 0 1 1 1 1 0 0| ACTION SIGNAL_ACTIVATED
#QQucode_0x00bd		-	|0 0 0 0 0 0 0 0 1 0 1 1 1 1 0 1|
#QQucode_0x00be		-	|0 0 0 0 0 0 0 0 1 0 1 1 1 1 1 0|
#QQucode_0x00bf		-	|0 0 0 0 0 0 0 0 1 0 1 1 1 1 1 1| ACTION ACCEPT_ACTIVATION
#QQucode_0x00c4		-	|0 0 0 0 0 0 0 0 1 1 0 0 0 1 0 0|
#QQucode_0x00c5		-	|0 0 0 0 0 0 0 0 1 1 0 0 0 1 0 1|
#QQucode_0x00c6		-	|0 0 0 0 0 0 0 0 1 1 0 0 0 1 1 0|
#QQucode_0x00c7		-	|0 0 0 0 0 0 0 0 1 1 0 0 0 1 1 1| ACTION ELABORATE_SUBPROGRAM
#QQucode_0x00c8		-	|0 0 0 0 0 0 0 0 1 1 0 0 1 0 0 0| QQu_end_in_loop
#QQucode_0x00c9		-	|0 0 0 0 0 0 0 0 1 1 0 0 1 0 0 1| QQu_end_loop
#QQucode_0x00ca		-	|0 0 0 0 0 0 0 0 1 1 0 0 1 0 1 0| QQu_exit_nullary_function,>R
#QQucode_0x00cb		-	|0 0 0 0 0 0 0 0 1 1 0 0 1 0 1 1|
#QQucode_0x00cc		-	|0 0 0 0 0 0 0 0 1 1 0 0 1 1 0 0|
#QQucode_0x00cd		-	|0 0 0 0 0 0 0 0 1 1 0 0 1 1 0 1|
#QQucode_0x00ce		-	|0 0 0 0 0 0 0 0 1 1 0 0 1 1 1 0| QQ_reset_loop_counter
#QQucode_0x00cf		-	|0 0 0 0 0 0 0 0 1 1 0 0 1 1 1 1| QQu_loop_start
#QQucode_0x00d0		-	|0 0 0 0 0 0 0 0 1 1 0 1 0 0 0 0|
#QQucode_0x00d1		-	|0 0 0 0 0 0 0 0 1 1 0 1 0 0 0 1|
#QQucode_0x00d2		-	|0 0 0 0 0 0 0 0 1 1 0 1 0 0 1 0|
#QQucode_0x00d3		-	|0 0 0 0 0 0 0 0 1 1 0 1 0 0 1 1|
#QQucode_0x00d4		-	|0 0 0 0 0 0 0 0 1 1 0 1 0 1 0 0|
#QQucode_0x00d5		-	|0 0 0 0 0 0 0 0 1 1 0 1 0 1 0 1|
#QQucode_0x00d6		-	|0 0 0 0 0 0 0 0 1 1 0 1 0 1 1 0|
#QQucode_0x00d7		-	|0 0 0 0 0 0 0 0 1 1 0 1 0 1 1 1|
#QQucode_0x00d8		-	|0 0 0 0 0 0 0 0 1 1 0 1 1 0 0 0| LOAD_TOP
#QQucode_0x00d9		-	|0 0 0 0 0 0 0 0 1 1 0 1 1 0 0 1| LOAD_TOP
#QQucode_0x00da		-	|0 0 0 0 0 0 0 0 1 1 0 1 1 0 1 0| LOAD_TOP
#QQucode_0x00db		-	|0 0 0 0 0 0 0 0 1 1 0 1 1 0 1 1| LOAD_TOP
#QQucode_0x00dc		-	|0 0 0 0 0 0 0 0 1 1 0 1 1 1 0 0|
#QQucode_0x00dd		-	|0 0 0 0 0 0 0 0 1 1 0 1 1 1 0 1|
#QQucode_0x00de		-	|0 0 0 0 0 0 0 0 1 1 0 1 1 1 1 0|
#QQucode_0x00e0		-	|0 0 0 0 0 0 0 0 1 1 1 0 0 0 0 0| LOAD_ENCACHED
#QQucode_0x00e1		-	|0 0 0 0 0 0 0 0 1 1 1 0 0 0 0 1| LOAD_ENCACHED
#QQucode_0x00e2		-	|0 0 0 0 0 0 0 0 1 1 1 0 0 0 1 0| LOAD_ENCACHED
#QQucode_0x00e3		-	|0 0 0 0 0 0 0 0 1 1 1 0 0 0 1 1| LOAD_ENCACHED
#QQucode_0x00e4		-	|0 0 0 0 0 0 0 0 1 1 1 0 0 1 0 0| LOAD_ENCACHED
#QQucode_0x00e5		-	|0 0 0 0 0 0 0 0 1 1 1 0 0 1 0 1| LOAD_ENCACHED
#QQucode_0x00e6		-	|0 0 0 0 0 0 0 0 1 1 1 0 0 1 1 0| LOAD_ENCACHED
#QQucode_0x00e7		-	|0 0 0 0 0 0 0 0 1 1 1 0 0 1 1 1| LOAD_ENCACHED
#QQucode_0x00e8		-	|0 0 0 0 0 0 0 0 1 1 1 0 1 0 0 0| LOAD_ENCACHED
#QQucode_0x00e9		-	|0 0 0 0 0 0 0 0 1 1 1 0 1 0 0 1| LOAD_ENCACHED
#QQucode_0x00ea		-	|0 0 0 0 0 0 0 0 1 1 1 0 1 0 1 0| LOAD_ENCACHED
#QQucode_0x00eb		-	|0 0 0 0 0 0 0 0 1 1 1 0 1 0 1 1| LOAD_ENCACHED
#QQucode_0x00ec		-	|0 0 0 0 0 0 0 0 1 1 1 0 1 1 0 0| LOAD_ENCACHED
#QQucode_0x00ed		-	|0 0 0 0 0 0 0 0 1 1 1 0 1 1 0 1| LOAD_ENCACHED
#QQucode_0x00ee		-	|0 0 0 0 0 0 0 0 1 1 1 0 1 1 1 0| LOAD_ENCACHED
#QQucode_0x00ef		-	|0 0 0 0 0 0 0 0 1 1 1 0 1 1 1 1| LOAD_ENCACHED
#QQucode_0x00f0		-	|0 0 0 0 0 0 0 0 1 1 1 1 0 0 0 0| LOAD_ENCACHED
#QQucode_0x00f1		-	|0 0 0 0 0 0 0 0 1 1 1 1 0 0 0 1| LOAD_ENCACHED
#QQucode_0x00f2		-	|0 0 0 0 0 0 0 0 1 1 1 1 0 0 1 0| LOAD_ENCACHED
#QQucode_0x00f3		-	|0 0 0 0 0 0 0 0 1 1 1 1 0 0 1 1| LOAD_ENCACHED
#QQucode_0x00f4		-	|0 0 0 0 0 0 0 0 1 1 1 1 0 1 0 0| LOAD_ENCACHED
#QQucode_0x00f5		-	|0 0 0 0 0 0 0 0 1 1 1 1 0 1 0 1| LOAD_ENCACHED
#QQucode_0x00f6		-	|0 0 0 0 0 0 0 0 1 1 1 1 0 1 1 0| LOAD_ENCACHED
#QQucode_0x00f7		-	|0 0 0 0 0 0 0 0 1 1 1 1 0 1 1 1| LOAD_ENCACHED
#QQucode_0x00f8		-	|0 0 0 0 0 0 0 0 1 1 1 1 1 0 0 0| LOAD_ENCACHED
#QQucode_0x00f9		-	|0 0 0 0 0 0 0 0 1 1 1 1 1 0 0 1| LOAD_ENCACHED
#QQucode_0x00fa		-	|0 0 0 0 0 0 0 0 1 1 1 1 1 0 1 0| LOAD_ENCACHED
#QQucode_0x00fb		-	|0 0 0 0 0 0 0 0 1 1 1 1 1 0 1 1| LOAD_ENCACHED
#QQucode_0x00fc		-	|0 0 0 0 0 0 0 0 1 1 1 1 1 1 0 0| LOAD_ENCACHED
#QQucode_0x00fd		-	|0 0 0 0 0 0 0 0 1 1 1 1 1 1 0 1| LOAD_ENCACHED
#QQucode_0x00fe		-	|0 0 0 0 0 0 0 0 1 1 1 1 1 1 1 0| LOAD_ENCACHED
#QQucode_0x00ff		-	|0 0 0 0 0 0 0 0 1 1 1 1 1 1 1 1| LOAD_ENCACHED
#QQucode_0x0100		-	|0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0| EXECUTE EXCEPTION_CLASS,RAISE_OP,>R
#QQucode_0x0101		-	|0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 1| EXECUTE EXCEPTION_CLASS,RERAISE_OP,>R
#QQucode_0x0106		-	|0 0 0 0 0 0 0 1 0 0 0 0 0 1 1 0|
#QQucode_0x0107		-	|0 0 0 0 0 0 0 1 0 0 0 0 0 1 1 1|
#QQucode_0x0109		-	|0 0 0 0 0 0 0 1 0 0 0 0 1 0 0 1|
#QQucode_0x010a		-	|0 0 0 0 0 0 0 1 0 0 0 0 1 0 1 0|
#QQucode_0x010b		-	|0 0 0 0 0 0 0 1 0 0 0 0 1 0 1 1|
#QQucode_0x010c		-	|0 0 0 0 0 0 0 1 0 0 0 0 1 1 0 0|
#QQucode_0x010d		-	|0 0 0 0 0 0 0 1 0 0 0 0 1 1 0 1| IS_NUMERIC_ERROR_OP -
#QQucode_0x010e		-	|0 0 0 0 0 0 0 1 0 0 0 0 1 1 1 0|
#QQucode_0x010f		-	|0 0 0 0 0 0 0 1 0 0 0 0 1 1 1 1| QQu_Is_Equal_Exception -
#QQucode_0x0110		-	|0 0 0 0 0 0 0 1 0 0 0 1 0 0 0 0|
#QQucode_0x0111		-	|0 0 0 0 0 0 0 1 0 0 0 1 0 0 0 1|
#QQucode_0x0112		-	|0 0 0 0 0 0 0 1 0 0 0 1 0 0 1 0|
#QQucode_0x0114		-	|0 0 0 0 0 0 0 1 0 0 0 1 0 1 0 0|
#QQucode_0x0115		-	|0 0 0 0 0 0 0 1 0 0 0 1 0 1 0 1|
#QQucode_0x0116		-	|0 0 0 0 0 0 0 1 0 0 0 1 0 1 1 0|
#QQucode_0x0117		-	|0 0 0 0 0 0 0 1 0 0 0 1 0 1 1 1|
#QQucode_0x0118		-	|0 0 0 0 0 0 0 1 0 0 0 1 1 0 0 0|
#QQucode_0x0119		-	|0 0 0 0 0 0 0 1 0 0 0 1 1 0 0 1|
#QQucode_0x011a		-	|0 0 0 0 0 0 0 1 0 0 0 1 1 0 1 0|
#QQucode_0x011b		-	|0 0 0 0 0 0 0 1 0 0 0 1 1 0 1 1|
#QQucode_0x011c		-	|0 0 0 0 0 0 0 1 0 0 0 1 1 1 0 0| QQuImage -
#QQucode_0x011d		-	|0 0 0 0 0 0 0 1 0 0 0 1 1 1 0 1|
#QQucode_0x011e		-	|0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 0|
#QQucode_0x011f		-	|0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 1|
#QQucode_0x0120		-	|0 0 0 0 0 0 0 1 0 0 1 0 0 0 0 0|
#QQucode_0x0121		-	|0 0 0 0 0 0 0 1 0 0 1 0 0 0 0 1|
#QQucode_0x0122		-	|0 0 0 0 0 0 0 1 0 0 1 0 0 0 1 0|
#QQucode_0x0123		-	|0 0 0 0 0 0 0 1 0 0 1 0 0 0 1 1|
#QQucode_0x0124		-	|0 0 0 0 0 0 0 1 0 0 1 0 0 1 0 0|
#QQucode_0x0125		-	|0 0 0 0 0 0 0 1 0 0 1 0 0 1 0 1|
#QQucode_0x0126		-	|0 0 0 0 0 0 0 1 0 0 1 0 0 1 1 0|
#QQucode_0x0127		-	|0 0 0 0 0 0 0 1 0 0 1 0 0 1 1 1|
#QQucode_0x0128		-	|0 0 0 0 0 0 0 1 0 0 1 0 1 0 0 0|
#QQucode_0x0129		-	|0 0 0 0 0 0 0 1 0 0 1 0 1 0 0 1| QQu_Execute_make_visible_op -
#QQucode_0x012a		-	|0 0 0 0 0 0 0 1 0 0 1 0 1 0 1 0|
#QQucode_0x012b		-	|0 0 0 0 0 0 0 1 0 0 1 0 1 0 1 1|
#QQucode_0x012c		-	|0 0 0 0 0 0 0 1 0 0 1 0 1 1 0 0|
#QQucode_0x012d		-	|0 0 0 0 0 0 0 1 0 0 1 0 1 1 0 1|
#QQucode_0x012e		-	|0 0 0 0 0 0 0 1 0 0 1 0 1 1 1 0|
#QQucode_0x012f		-	|0 0 0 0 0 0 0 1 0 0 1 0 1 1 1 1| QQu_is_equal_discrete -
#QQucode_0x0132		-	|0 0 0 0 0 0 0 1 0 0 1 1 0 0 1 0|
#QQucode_0x0133		-	|0 0 0 0 0 0 0 1 0 0 1 1 0 0 1 1|
#QQucode_0x0136		-	|0 0 0 0 0 0 0 1 0 0 1 1 0 1 1 0|
#QQucode_0x0137		-	|0 0 0 0 0 0 0 1 0 0 1 1 0 1 1 1|
#QQucode_0x013c		-	|0 0 0 0 0 0 0 1 0 0 1 1 1 1 0 0|
#QQucode_0x013d		-	|0 0 0 0 0 0 0 1 0 0 1 1 1 1 0 1|
#QQucode_0x013e		-	|0 0 0 0 0 0 0 1 0 0 1 1 1 1 1 0|
#QQucode_0x013f		-	|0 0 0 0 0 0 0 1 0 0 1 1 1 1 1 1|
#QQucode_0x0140		-	|0 0 0 0 0 0 0 1 0 1 0 0 0 0 0 0|
#QQucode_0x0141		-	|0 0 0 0 0 0 0 1 0 1 0 0 0 0 0 1| QQu_int_multiply
#QQucode_0x0142		-	|0 0 0 0 0 0 0 1 0 1 0 0 0 0 1 0|
#QQucode_0x0143		-	|0 0 0 0 0 0 0 1 0 1 0 0 0 0 1 1|
#QQucode_0x0144		-	|0 0 0 0 0 0 0 1 0 1 0 0 0 1 0 0|
#QQucode_0x0145		-	|0 0 0 0 0 0 0 1 0 1 0 0 0 1 0 1|
#QQucode_0x0146		-	|0 0 0 0 0 0 0 1 0 1 0 0 0 1 1 0|
#QQucode_0x0147		-	|0 0 0 0 0 0 0 1 0 1 0 0 0 1 1 1|
#QQucode_0x0148		-	|0 0 0 0 0 0 0 1 0 1 0 0 1 0 0 0|
#QQucode_0x0149		-	|0 0 0 0 0 0 0 1 0 1 0 0 1 0 0 1|
#QQucode_0x014a		-	|0 0 0 0 0 0 0 1 0 1 0 0 1 0 1 0| QQu_float_great_equal_zero -
#QQucode_0x014b		-	|0 0 0 0 0 0 0 1 0 1 0 0 1 0 1 1| QQu_float_below_zero -
#QQucode_0x014c		-	|0 0 0 0 0 0 0 1 0 1 0 0 1 1 0 0| QQu_float_greater_zero -
#QQucode_0x014d		-	|0 0 0 0 0 0 0 1 0 1 0 0 1 1 0 1|
#QQucode_0x014e		-	|0 0 0 0 0 0 0 1 0 1 0 0 1 1 1 0|
#QQucode_0x014f		-	|0 0 0 0 0 0 0 1 0 1 0 0 1 1 1 1|
#QQucode_0x015b		-	|0 0 0 0 0 0 0 1 0 1 0 1 1 0 1 1|
#QQucode_0x015c		-	|0 0 0 0 0 0 0 1 0 1 0 1 1 1 0 0|
#QQucode_0x015d		-	|0 0 0 0 0 0 0 1 0 1 0 1 1 1 0 1|
#QQucode_0x015e		-	|0 0 0 0 0 0 0 1 0 1 0 1 1 1 1 0|
#QQucode_0x015f		-	|0 0 0 0 0 0 0 1 0 1 0 1 1 1 1 1|
#QQucode_0x0160		-	|0 0 0 0 0 0 0 1 0 1 1 0 0 0 0 0|
#QQucode_0x0161		-	|0 0 0 0 0 0 0 1 0 1 1 0 0 0 0 1|
#QQucode_0x0162		-	|0 0 0 0 0 0 0 1 0 1 1 0 0 0 1 0|
#QQucode_0x0163		-	|0 0 0 0 0 0 0 1 0 1 1 0 0 0 1 1|
#QQucode_0x0164		-	|0 0 0 0 0 0 0 1 0 1 1 0 0 1 0 0|
#QQucode_0x0165		-	|0 0 0 0 0 0 0 1 0 1 1 0 0 1 0 1|
#QQucode_0x0166		-	|0 0 0 0 0 0 0 1 0 1 1 0 0 1 1 0|
#QQucode_0x0167		-	|0 0 0 0 0 0 0 1 0 1 1 0 0 1 1 1|
#QQucode_0x0168		-	|0 0 0 0 0 0 0 1 0 1 1 0 1 0 0 0|
#QQucode_0x0169		-	|0 0 0 0 0 0 0 1 0 1 1 0 1 0 0 1|
#QQucode_0x016a		-	|0 0 0 0 0 0 0 1 0 1 1 0 1 0 1 0| # Undefined in disassembler
#QQucode_0x016b		-	|0 0 0 0 0 0 0 1 0 1 1 0 1 0 1 1|
#QQucode_0x016c		-	|0 0 0 0 0 0 0 1 0 1 1 0 1 1 0 0|
#QQucode_0x016d		-	|0 0 0 0 0 0 0 1 0 1 1 0 1 1 0 1|
#QQucode_0x016e		x	|0 0 0 0 0 0 0 1 0 1 1 0 1 1 1|x|
#QQucode_0x0177		-	|0 0 0 0 0 0 0 1 0 1 1 1 0 1 1 1|
#QQucode_0x0178		-	|0 0 0 0 0 0 0 1 0 1 1 1 1 0 0 0|
#QQucode_0x0179		-	|0 0 0 0 0 0 0 1 0 1 1 1 1 0 0 1|
#QQucode_0x017a		-	|0 0 0 0 0 0 0 1 0 1 1 1 1 0 1 0|
#QQucode_0x017b		-	|0 0 0 0 0 0 0 1 0 1 1 1 1 0 1 1|
#QQucode_0x017c		-	|0 0 0 0 0 0 0 1 0 1 1 1 1 1 0 0|
#QQucode_0x017d		-	|0 0 0 0 0 0 0 1 0 1 1 1 1 1 0 1| QQuWrite_RECORD -
#QQucode_0x017e		x	|0 0 0 0 0 0 0 1 0 1 1 1 1 1 1|x|
#QQucode_0x0189		-	|0 0 0 0 0 0 0 1 1 0 0 0 1 0 0 1|
#QQucode_0x018a		-	|0 0 0 0 0 0 0 1 1 0 0 0 1 0 1 0|
#QQucode_0x018b		-	|0 0 0 0 0 0 0 1 1 0 0 0 1 0 1 1|
#QQucode_0x018d		-	|0 0 0 0 0 0 0 1 1 0 0 0 1 1 0 1|
#QQucode_0x018e		-	|0 0 0 0 0 0 0 1 1 0 0 0 1 1 1 0|
#QQucode_0x018f		-	|0 0 0 0 0 0 0 1 1 0 0 0 1 1 1 1|
#QQucode_0x019b		-	|0 0 0 0 0 0 0 1 1 0 0 1 1 0 1 1|
#QQucode_0x019c		-	|0 0 0 0 0 0 0 1 1 0 0 1 1 1 0 0|
#QQucode_0x019d		-	|0 0 0 0 0 0 0 1 1 0 0 1 1 1 0 1|
#QQucode_0x019e		-	|0 0 0 0 0 0 0 1 1 0 0 1 1 1 1 0|
#QQucode_0x019f		-	|0 0 0 0 0 0 0 1 1 0 0 1 1 1 1 1|
#QQucode_0x01a3		-	|0 0 0 0 0 0 0 1 1 0 1 0 0 0 1 1|
#QQucode_0x01a4		-	|0 0 0 0 0 0 0 1 1 0 1 0 0 1 0 0| QQuWrite_Full_Matrix -
#QQucode_0x01a5		-	|0 0 0 0 0 0 0 1 1 0 1 0 0 1 0 1|
#QQucode_0x01a6		-	|0 0 0 0 0 0 0 1 1 0 1 0 0 1 1 0| QQuWrite_Matrix_element -
#QQucode_0x01a7		-	|0 0 0 0 0 0 0 1 1 0 1 0 0 1 1 1|
#QQucode_0x01a8		-	|0 0 0 0 0 0 0 1 1 0 1 0 1 0 0 0|
#QQucode_0x01a9		-	|0 0 0 0 0 0 0 1 1 0 1 0 1 0 0 1|
#QQucode_0x01aa		-	|0 0 0 0 0 0 0 1 1 0 1 0 1 0 1 0|
#QQucode_0x01ab		-	|0 0 0 0 0 0 0 1 1 0 1 0 1 0 1 1|
#QQucode_0x01ac		-	|0 0 0 0 0 0 0 1 1 0 1 0 1 1 0 0|
#QQucode_0x01ad		-	|0 0 0 0 0 0 0 1 1 0 1 0 1 1 0 1|
#QQucode_0x01ae		x	|0 0 0 0 0 0 0 1 1 0 1 0 1 1 1|x|
#QQucode_0x01be		-	|0 0 0 0 0 0 0 1 1 0 1 1 1 1 1 0|
#QQucode_0x01bf		-	|0 0 0 0 0 0 0 1 1 0 1 1 1 1 1 1|
#QQucode_0x01c0		-	|0 0 0 0 0 0 0 1 1 1 0 0 0 0 0 0|
#QQucode_0x01c1		-	|0 0 0 0 0 0 0 1 1 1 0 0 0 0 0 1| QQu_string_is_less_than
#QQucode_0x01c2		-	|0 0 0 0 0 0 0 1 1 1 0 0 0 0 1 0|
#QQucode_0x01c3		-	|0 0 0 0 0 0 0 1 1 1 0 0 0 0 1 1| EXECUTE VECTOR_CLASS,CHECK_IN_TYPE_OP
#QQucode_0x01c4		-	|0 0 0 0 0 0 0 1 1 1 0 0 0 1 0 0|
#QQucode_0x01c5		-	|0 0 0 0 0 0 0 1 1 1 0 0 0 1 0 1|
#QQucode_0x01c6		-	|0 0 0 0 0 0 0 1 1 1 0 0 0 1 1 0|
#QQucode_0x01c7		-	|0 0 0 0 0 0 0 1 1 1 0 0 0 1 1 1|
#QQucode_0x01ca		-	|0 0 0 0 0 0 0 1 1 1 0 0 1 0 1 0|
#QQucode_0x01cb		-	|0 0 0 0 0 0 0 1 1 1 0 0 1 0 1 1| QQuLoad_Vector_Result -
#QQucode_0x01cc		-	|0 0 0 0 0 0 0 1 1 1 0 0 1 1 0 0| EXECUTE VECTOR_CLASS,CATENATE_OP
#QQucode_0x01cd		-	|0 0 0 0 0 0 0 1 1 1 0 0 1 1 0 1|
#QQucode_0x01ce		-	|0 0 0 0 0 0 0 1 1 1 0 0 1 1 1 0|
#QQucode_0x01cf		-	|0 0 0 0 0 0 0 1 1 1 0 0 1 1 1 1| QQuEXECUTE VECTOR_CLASS,SUBARRAY_OP
#QQucode_0x01d0		-	|0 0 0 0 0 0 0 1 1 1 0 1 0 0 0 0|
#QQucode_0x01d1		-	|0 0 0 0 0 0 0 1 1 1 0 1 0 0 0 1|
#QQucode_0x01d1		x	|0 0 0 0 0 0 0 1 1 1 0 1 0 0 1|x|
#QQucode_0x01d4		-	|0 0 0 0 0 0 0 1 1 1 0 1 0 1 0 0| QQuEXECUTE VECTOR_CLASS,STRUCTURE_WRITE_OP
#QQucode_0x01d5		-	|0 0 0 0 0 0 0 1 1 1 0 1 0 1 0 1| QQuEXECUTE VECTOR_CLASS,FIELD_REFERENCE_OP
#QQucode_0x01d6		-	|0 0 0 0 0 0 0 1 1 1 0 1 0 1 1 0| EXECUTE VECTOR_CLASS,FIELD_WRITE_OP
#QQucode_0x01d7		-	|0 0 0 0 0 0 0 1 1 1 0 1 0 1 1 1| QQuEXECUTE VECTOR_CLASS,FIELD_READ_OP
#QQucode_0x01d8		-	|0 0 0 0 0 0 0 1 1 1 0 1 1 0 0 0|
#QQucode_0x01d9		-	|0 0 0 0 0 0 0 1 1 1 0 1 1 0 0 1| QQuExecute_range_op
#QQucode_0x01da		-	|0 0 0 0 0 0 0 1 1 1 0 1 1 0 1 0| QQu_vector_length
#QQucode_0x01db		-	|0 0 0 0 0 0 0 1 1 1 0 1 1 0 1 1| QQuExecute_vector_length_op
#QQucode_0x01dc		-	|0 0 0 0 0 0 0 1 1 1 0 1 1 1 0 0| QQuExecute_last_op -
#QQucode_0x01dd		-	|0 0 0 0 0 0 0 1 1 1 0 1 1 1 0 1| QQuExecute_first_op -
QQucode_0x01de		x	|0 0 0 0 0 0 0 1 1 1 0 1 1 1 1|x|
#QQucode_0x01eb		-	|0 0 0 0 0 0 0 1 1 1 1 0 1 0 1 1|
#QQucode_0x01ec		-	|0 0 0 0 0 0 0 1 1 1 1 0 1 1 0 0|
#QQucode_0x01ed		-	|0 0 0 0 0 0 0 1 1 1 1 0 1 1 0 1|
#QQucode_0x01ee		-	|0 0 0 0 0 0 0 1 1 1 1 0 1 1 1 0|
#QQucode_0x01ef		-	|0 0 0 0 0 0 0 1 1 1 1 0 1 1 1 1|
#QQucode_0x01f3		-	|0 0 0 0 0 0 0 1 1 1 1 1 0 0 1 1|
#QQucode_0x01f4		-	|0 0 0 0 0 0 0 1 1 1 1 1 0 1 0 0|
#QQucode_0x01f5		-	|0 0 0 0 0 0 0 1 1 1 1 1 0 1 0 1|
#QQucode_0x01f6		-	|0 0 0 0 0 0 0 1 1 1 1 1 0 1 1 0|
#QQucode_0x01f7		-	|0 0 0 0 0 0 0 1 1 1 1 1 0 1 1 1|
#QQucode_0x01f8		-	|0 0 0 0 0 0 0 1 1 1 1 1 1 0 0 0|
#QQucode_0x01f9		-	|0 0 0 0 0 0 0 1 1 1 1 1 1 0 0 1|
#QQucode_0x01fa		-	|0 0 0 0 0 0 0 1 1 1 1 1 1 0 1 0|
#QQucode_0x01fb		-	|0 0 0 0 0 0 0 1 1 1 1 1 1 0 1 1|
#QQucode_0x01fc		-	|0 0 0 0 0 0 0 1 1 1 1 1 1 1 0 0|
#QQucode_0x01fd		-	|0 0 0 0 0 0 0 1 1 1 1 1 1 1 0 1|
#QQucode_0x01fe		x	|0 0 0 0 0 0 0 1 1 1 1 1 1 1 1|x|
QQucode_0x0205		-	|0 0 0 0 0 0 1 0 0 0 0 0 0 1 0 1| #Not handled by disassembler
#QQucode_0x0206		-	|0 0 0 0 0 0 1 0 0 0 0 0 0 1 1 0|
#QQucode_0x0208		-	|0 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0|
#QQucode_0x0209		-	|0 0 0 0 0 0 1 0 0 0 0 0 1 0 0 1|
#QQucode_0x020a		-	|0 0 0 0 0 0 1 0 0 0 0 0 1 0 1 0|
#QQucode_0x020b		-	|0 0 0 0 0 0 1 0 0 0 0 0 1 0 1 1|
#QQucode_0x020c		-	|0 0 0 0 0 0 1 0 0 0 0 0 1 1 0 0|
#QQucode_0x020d		-	|0 0 0 0 0 0 1 0 0 0 0 0 1 1 0 1|
#QQucode_0x020e		-	|0 0 0 0 0 0 1 0 0 0 0 0 1 1 1 0| EXECUTE MODULE_CLASS,AUGMENT_IMPORTS_OP
#QQucode_0x020f		-	|0 0 0 0 0 0 1 0 0 0 0 0 1 1 1 1| EXECUTE MODULE_CLASS,ACTIVATE_OP
#QQucode_0x0210		-	|0 0 0 0 0 0 1 0 0 0 0 1 0 0 0 0|
#QQucode_0x0211		-	|0 0 0 0 0 0 1 0 0 0 0 1 0 0 0 1|
#QQucode_0x0212		-	|0 0 0 0 0 0 1 0 0 0 0 1 0 0 1 0|
#QQucode_0x0213		-	|0 0 0 0 0 0 1 0 0 0 0 1 0 0 1 1|
#QQucode_0x0214		-	|0 0 0 0 0 0 1 0 0 0 0 1 0 1 0 0|
#QQucode_0x0215		-	|0 0 0 0 0 0 1 0 0 0 0 1 0 1 0 1|
#QQucode_0x0216		-	|0 0 0 0 0 0 1 0 0 0 0 1 0 1 1 0|
#QQucode_0x0217		-	|0 0 0 0 0 0 1 0 0 0 0 1 0 1 1 1| EXECUTE Heap_Access,All_Reference
#QQucode_0x0218		-	|0 0 0 0 0 0 1 0 0 0 0 1 1 0 0 0|
#QQucode_0x0219		-	|0 0 0 0 0 0 1 0 0 0 0 1 1 0 0 1|
#QQucode_0x021a		-	|0 0 0 0 0 0 1 0 0 0 0 1 1 0 1 0|
#QQucode_0x021b		-	|0 0 0 0 0 0 1 0 0 0 0 1 1 0 1 1|
#QQucode_0x021c		-	|0 0 0 0 0 0 1 0 0 0 0 1 1 1 0 0|
#QQucode_0x021d		-	|0 0 0 0 0 0 1 0 0 0 0 1 1 1 0 1|
#QQucode_0x021e		-	|0 0 0 0 0 0 1 0 0 0 0 1 1 1 1 0|
#QQucode_0x021f		-	|0 0 0 0 0 0 1 0 0 0 0 1 1 1 1 1|
#QQucode_0x0220		-	|0 0 0 0 0 0 1 0 0 0 1 0 0 0 0 0|
#QQucode_0x0221		-	|0 0 0 0 0 0 1 0 0 0 1 0 0 0 0 1|
#QQucode_0x0222		-	|0 0 0 0 0 0 1 0 0 0 1 0 0 0 1 0|
#QQucode_0x0223		-	|0 0 0 0 0 0 1 0 0 0 1 0 0 0 1 1|
#QQucode_0x0224		-	|0 0 0 0 0 0 1 0 0 0 1 0 0 1 0 0|
#QQucode_0x0225		-	|0 0 0 0 0 0 1 0 0 0 1 0 0 1 0 1|
#QQucode_0x0226		-	|0 0 0 0 0 0 1 0 0 0 1 0 0 1 1 0|
#QQucode_0x0227		-	|0 0 0 0 0 0 1 0 0 0 1 0 0 1 1 1| QQu_EXECUTE Heap_Access,FIELD_REFERENCE_OP
#QQucode_0x0228		-	|0 0 0 0 0 0 1 0 0 0 1 0 1 0 0 0|
#QQucode_0x0229		-	|0 0 0 0 0 0 1 0 0 0 1 0 1 0 0 1|
#QQucode_0x022a		-	|0 0 0 0 0 0 1 0 0 0 1 0 1 0 1 0|
#QQucode_0x022b		-	|0 0 0 0 0 0 1 0 0 0 1 0 1 0 1 1|
#QQucode_0x022c		-	|0 0 0 0 0 0 1 0 0 0 1 0 1 1 0 0|
#QQucode_0x022d		-	|0 0 0 0 0 0 1 0 0 0 1 0 1 1 0 1|
#QQucode_0x022e		-	|0 0 0 0 0 0 1 0 0 0 1 0 1 1 1 0|
#QQucode_0x022f		-	|0 0 0 0 0 0 1 0 0 0 1 0 1 1 1 1|
#QQucode_0x0230		-	|0 0 0 0 0 0 1 0 0 0 1 1 0 0 0 0|
#QQucode_0x0231		-	|0 0 0 0 0 0 1 0 0 0 1 1 0 0 0 1|
#QQucode_0x0232		-	|0 0 0 0 0 0 1 0 0 0 1 1 0 0 1 0|
#QQucode_0x0233		-	|0 0 0 0 0 0 1 0 0 0 1 1 0 0 1 1|
#QQucode_0x0234		-	|0 0 0 0 0 0 1 0 0 0 1 1 0 1 0 0|
#QQucode_0x0235		-	|0 0 0 0 0 0 1 0 0 0 1 1 0 1 0 1| ROUND_TO_DISCRETE_OP -
#QQucode_0x0236		-	|0 0 0 0 0 0 1 0 0 0 1 1 0 1 1 0|
#QQucode_0x0237		-	|0 0 0 0 0 0 1 0 0 0 1 1 0 1 1 1| QQu_CONVERT_TO_FLOAT
#QQucode_0x0238		-	|0 0 0 0 0 0 1 0 0 0 1 1 1 0 0 0|
#QQucode_0x0239		-	|0 0 0 0 0 0 1 0 0 0 1 1 1 0 0 1| FLOAT_** -
#QQucode_0x023a		-	|0 0 0 0 0 0 1 0 0 0 1 1 1 0 1 0| FLOAT_DIVIDE -
#QQucode_0x023b		-	|0 0 0 0 0 0 1 0 0 0 1 1 1 0 1 1| FLOAT_MULTIPLY -
#QQucode_0x023c		-	|0 0 0 0 0 0 1 0 0 0 1 1 1 1 0 0| FLOAT_SUBTRACT -
#QQucode_0x023d		-	|0 0 0 0 0 0 1 0 0 0 1 1 1 1 0 1| FLOAT_ADD -
#QQucode_0x023e		-	|0 0 0 0 0 0 1 0 0 0 1 1 1 1 1 0| FLOAT_ABS -
#QQucode_0x023f		-	|0 0 0 0 0 0 1 0 0 0 1 1 1 1 1 1| FLOAT_NEGATE -
#QQucode_0x0240		-	|0 0 0 0 0 0 1 0 0 1 0 0 0 0 0 0|
#QQucode_0x0241		-	|0 0 0 0 0 0 1 0 0 1 0 0 0 0 0 1|
#QQucode_0x0242		-	|0 0 0 0 0 0 1 0 0 1 0 0 0 0 1 0| QQu_float_less_equal_than -
#QQucode_0x0243		-	|0 0 0 0 0 0 1 0 0 1 0 0 0 0 1 1| QQu_float_greater_equal_than -
#QQucode_0x0244		-	|0 0 0 0 0 0 1 0 0 1 0 0 0 1 0 0| QQu_float_less_than -
#QQucode_0x0245		-	|0 0 0 0 0 0 1 0 0 1 0 0 0 1 0 1| QQu_float_greater_than -
#QQucode_0x0246		-	|0 0 0 0 0 0 1 0 0 1 0 0 0 1 1 0|
#QQucode_0x0247		-	|0 0 0 0 0 0 1 0 0 1 0 0 0 1 1 1| QQu_float_equal_to -
#QQucode_0x0248		-	|0 0 0 0 0 0 1 0 0 1 0 0 1 0 0 0|
#QQucode_0x0249		-	|0 0 0 0 0 0 1 0 0 1 0 0 1 0 0 1|
#QQucode_0x024a		-	|0 0 0 0 0 0 1 0 0 1 0 0 1 0 1 0|
#QQucode_0x024b		-	|0 0 0 0 0 0 1 0 0 1 0 0 1 0 1 1|
#QQucode_0x024c		-	|0 0 0 0 0 0 1 0 0 1 0 0 1 1 0 0|
#QQucode_0x024d		-	|0 0 0 0 0 0 1 0 0 1 0 0 1 1 0 1|
#QQucode_0x024e		-	|0 0 0 0 0 0 1 0 0 1 0 0 1 1 1 0|
#QQucode_0x024f		-	|0 0 0 0 0 0 1 0 0 1 0 0 1 1 1 1|
#QQucode_0x0250		-	|0 0 0 0 0 0 1 0 0 1 0 1 0 0 0 0|
#QQucode_0x0251		-	|0 0 0 0 0 0 1 0 0 1 0 1 0 0 0 1|
#QQucode_0x0252		-	|0 0 0 0 0 0 1 0 0 1 0 1 0 0 1 0|
#QQucode_0x0253		-	|0 0 0 0 0 0 1 0 0 1 0 1 0 0 1 1|
#QQucode_0x0254		-	|0 0 0 0 0 0 1 0 0 1 0 1 0 1 0 0|
#QQucode_0x0255		-	|0 0 0 0 0 0 1 0 0 1 0 1 0 1 0 1|
#QQucode_0x0256		-	|0 0 0 0 0 0 1 0 0 1 0 1 0 1 1 0|
#QQucode_0x0257		-	|0 0 0 0 0 0 1 0 0 1 0 1 0 1 1 1| QQunknown_return_257 >R
#QQucode_0x0258		-	|0 0 0 0 0 0 1 0 0 1 0 1 1 0 0 0|
#QQucode_0x0259		-	|0 0 0 0 0 0 1 0 0 1 0 1 1 0 0 1|
#QQucode_0x025a		-	|0 0 0 0 0 0 1 0 0 1 0 1 1 0 1 0|
#QQucode_0x025b		-	|0 0 0 0 0 0 1 0 0 1 0 1 1 0 1 1| QQuDECLARE_TYPE ARRAY_CLASS,DEFINED
#QQucode_0x025c		-	|0 0 0 0 0 0 1 0 0 1 0 1 1 1 0 0|
#QQucode_0x025d		-	|0 0 0 0 0 0 1 0 0 1 0 1 1 1 0 1|
#QQucode_0x025e		-	|0 0 0 0 0 0 1 0 0 1 0 1 1 1 1 0| QQu_CONVERT_TO_INT -
#QQucode_0x025f		-	|0 0 0 0 0 0 1 0 0 1 0 1 1 1 1 1|
#QQucode_0x0260		-	|0 0 0 0 0 0 1 0 0 1 1 0 0 0 0 0| QQuEXECUTE BELOW_BOUND
#QQucode_0x0261		-	|0 0 0 0 0 0 1 0 0 1 1 0 0 0 0 1|
#QQucode_0x0262		-	|0 0 0 0 0 0 1 0 0 1 1 0 0 0 1 0| QQuEXECUTE IN_RANGE
#QQucode_0x0263		-	|0 0 0 0 0 0 1 0 0 1 1 0 0 0 1 1| QQu_is_in_range
#QQucode_0x0264		-	|0 0 0 0 0 0 1 0 0 1 1 0 0 1 0 0| QQu_not_in_range
#QQucode_0x0265		-	|0 0 0 0 0 0 1 0 0 1 1 0 0 1 0 1|
#QQucode_0x0266		-	|0 0 0 0 0 0 1 0 0 1 1 0 0 1 1 0| QQuDefine_Array_Full_Range -
#QQucode_0x0267		-	|0 0 0 0 0 0 1 0 0 1 1 0 0 1 1 1|
#QQucode_0x0268		-	|0 0 0 0 0 0 1 0 0 1 1 0 1 0 0 0|
#QQucode_0x0269		-	|0 0 0 0 0 0 1 0 0 1 1 0 1 0 0 1| QQuDefine_Array_subtype_Range -
#QQucode_0x026a		-	|0 0 0 0 0 0 1 0 0 1 1 0 1 0 1 0|
#QQucode_0x026b		-	|0 0 0 0 0 0 1 0 0 1 1 0 1 0 1 1|
#QQucode_0x026c		-	|0 0 0 0 0 0 1 0 0 1 1 0 1 1 0 0|
#QQucode_0x026d		-	|0 0 0 0 0 0 1 0 0 1 1 0 1 1 0 1| QQuEXECUTE EXPONENTIATE
#QQucode_0x026e		-	|0 0 0 0 0 0 1 0 0 1 1 0 1 1 1 0| QQu_int_mod -
#QQucode_0x026f		-	|0 0 0 0 0 0 1 0 0 1 1 0 1 1 1 1| QQu_int_rem -
#QQucode_0x0270		-	|0 0 0 0 0 0 1 0 0 1 1 1 0 0 0 0| QQu_int_divide -
#QQucode_0x0271		-	|0 0 0 0 0 0 1 0 0 1 1 1 0 0 0 1| QQu_int_multiply -
#QQucode_0x0272		-	|0 0 0 0 0 0 1 0 0 1 1 1 0 0 1 0| QQu_int_subtract -
#QQucode_0x0273		-	|0 0 0 0 0 0 1 0 0 1 1 1 0 0 1 1| QQu_int_add -
#QQucode_0x0274		-	|0 0 0 0 0 0 1 0 0 1 1 1 0 1 0 0|
#QQucode_0x0275		-	|0 0 0 0 0 0 1 0 0 1 1 1 0 1 0 1| QQu_int_neg -
#QQucode_0x0276		-	|0 0 0 0 0 0 1 0 0 1 1 1 0 1 1 0|
#QQucode_0x0277		-	|0 0 0 0 0 0 1 0 0 1 1 1 0 1 1 1|
#QQucode_0x0278		-	|0 0 0 0 0 0 1 0 0 1 1 1 1 0 0 0|
#QQucode_0x0279		-	|0 0 0 0 0 0 1 0 0 1 1 1 1 0 0 1| QQu_integer_and -
#QQucode_0x027a		-	|0 0 0 0 0 0 1 0 0 1 1 1 1 0 1 0| QQu_less_equal -
#QQucode_0x027b		-	|0 0 0 0 0 0 1 0 0 1 1 1 1 0 1 1| QQu_greater_equal
#QQucode_0x027c		-	|0 0 0 0 0 0 1 0 0 1 1 1 1 1 0 0| QQu_less_than -
#QQucode_0x027d		-	|0 0 0 0 0 0 1 0 0 1 1 1 1 1 0 1| QQu_greater_than
#QQucode_0x027e		-	|0 0 0 0 0 0 1 0 0 1 1 1 1 1 1 0| QQu_not_equal
#QQucode_0x027f		-	|0 0 0 0 0 0 1 0 0 1 1 1 1 1 1 1| QQu_is_equal
#QQucode_0x0299		-	|0 0 0 0 0 0 1 0 1 0 0 1 1 0 0 1|
#QQucode_0x029a		-	|0 0 0 0 0 0 1 0 1 0 0 1 1 0 1 0|
#QQucode_0x029b		-	|0 0 0 0 0 0 1 0 1 0 0 1 1 0 1 1|
#QQucode_0x029c		-	|0 0 0 0 0 0 1 0 1 0 0 1 1 1 0 0|
#QQucode_0x029d		-	|0 0 0 0 0 0 1 0 1 0 0 1 1 1 0 1|
#QQucode_0x029e		-	|0 0 0 0 0 0 1 0 1 0 0 1 1 1 1 0|
#QQucode_0x029f		-	|0 0 0 0 0 0 1 0 1 0 0 1 1 1 1 1|
#QQucode_0x02a0		-	|0 0 0 0 0 0 1 0 1 0 1 0 0 0 0 0| DECLARE_SUBPROGRAM NULL_SUBPROGRAM
#QQucode_0x02a2		-	|0 0 0 0 0 0 1 0 1 0 1 0 0 0 1 0|
#QQucode_0x02a4		-	|0 0 0 0 0 0 1 0 1 0 1 0 0 1 0 0|
#QQucode_0x02a5		-	|0 0 0 0 0 0 1 0 1 0 1 0 0 1 0 1|
#QQucode_0x02a8		-	|0 0 0 0 0 0 1 0 1 0 1 0 1 0 0 0|
#QQucode_0x02a9		-	|0 0 0 0 0 0 1 0 1 0 1 0 1 0 0 1|
#QQucode_0x02aa		-	|0 0 0 0 0 0 1 0 1 0 1 0 1 0 1 0|
#QQucode_0x02ab		-	|0 0 0 0 0 0 1 0 1 0 1 0 1 0 1 1|
#QQucode_0x02be		-	|0 0 0 0 0 0 1 0 1 0 1 1 1 1 1 0|
#QQucode_0x02bf		-	|0 0 0 0 0 0 1 0 1 0 1 1 1 1 1 1|
#QQucode_0x02c6		-	|0 0 0 0 0 0 1 0 1 1 0 0 0 1 1 0|
#QQucode_0x02c7		-	|0 0 0 0 0 0 1 0 1 1 0 0 0 1 1 1|
#QQucode_0x02c9		-	|0 0 0 0 0 0 1 0 1 1 0 0 1 0 0 1|
#QQucode_0x02cb		-	|0 0 0 0 0 0 1 0 1 1 0 0 1 0 1 1|
#QQucode_0x02ce		-	|0 0 0 0 0 0 1 0 1 1 0 0 1 1 1 0|
#QQucode_0x02cf		-	|0 0 0 0 0 0 1 0 1 1 0 0 1 1 1 1| QQunknown_2cf -
#QQucode_0x02fb		-	|0 0 0 0 0 0 1 0 1 1 1 1 1 0 1 1|
#QQucode_0x02fc		-	|0 0 0 0 0 0 1 0 1 1 1 1 1 1 0 0|
#QQucode_0x02fd		-	|0 0 0 0 0 0 1 0 1 1 1 1 1 1 0 1|
#QQucode_0x02fe		-	|0 0 0 0 0 0 1 0 1 1 1 1 1 1 1 0|
#QQucode_0x02ff		-	|0 0 0 0 0 0 1 0 1 1 1 1 1 1 1 1|
#QQucode_0x0303		-	|0 0 0 0 0 0 1 1 0 0 0 0 0 0 1 1|
#QQucode_0x0304		-	|0 0 0 0 0 0 1 1 0 0 0 0 0 1 0 0|
#QQucode_0x0305		-	|0 0 0 0 0 0 1 1 0 0 0 0 0 1 0 1|
#QQucode_0x0306		-	|0 0 0 0 0 0 1 1 0 0 0 0 0 1 1 0|
#QQucode_0x0307		-	|0 0 0 0 0 0 1 1 0 0 0 0 0 1 1 1| QQuDECLARE_TYPE_complete VARIANT_RECORD_CLASS
#QQucode_0x0311		-	|0 0 0 0 0 0 1 1 0 0 0 1 0 0 0 1|
#QQucode_0x0312		-	|0 0 0 0 0 0 1 1 0 0 0 1 0 0 1 0|
#QQucode_0x0315		-	|0 0 0 0 0 0 1 1 0 0 0 1 0 1 0 1|
#QQucode_0x0316		-	|0 0 0 0 0 0 1 1 0 0 0 1 0 1 1 0|
#QQucode_0x0318		-	|0 0 0 0 0 0 1 1 0 0 0 1 1 0 0 0| QQuDECLARE_TYPE VARIANT_RECORD_CLASS,INCOMPLETE
#QQucode_0x0319		-	|0 0 0 0 0 0 1 1 0 0 0 1 1 0 0 1|
#QQucode_0x031b		-	|0 0 0 0 0 0 1 1 0 0 0 1 1 0 1 1|
#QQucode_0x031c		-	|0 0 0 0 0 0 1 1 0 0 0 1 1 1 0 0|
#QQucode_0x031d		-	|0 0 0 0 0 0 1 1 0 0 0 1 1 1 0 1|
#QQucode_0x031e		-	|0 0 0 0 0 0 1 1 0 0 0 1 1 1 1 0| QQuDECLARE_TYPE VARIANT_RECORD_CLASS
#QQucode_0x0320		-	|0 0 0 0 0 0 1 1 0 0 1 0 0 0 0 0|
#QQucode_0x0321		-	|0 0 0 0 0 0 1 1 0 0 1 0 0 0 0 1|
#QQucode_0x0322		-	|0 0 0 0 0 0 1 1 0 0 1 0 0 0 1 0| QQuDECLARE_VARIABLE RECORD_CLASS
#QQucode_0x0324		-	|0 0 0 0 0 0 1 1 0 0 1 0 0 1 0 0|
#QQucode_0x0325		-	|0 0 0 0 0 0 1 1 0 0 1 0 0 1 0 1|
#QQucode_0x0326		-	|0 0 0 0 0 0 1 1 0 0 1 0 0 1 1 0| QQuDECLARE_TYPE_complete RECORD_CLASS,DEFINED
#QQucode_0x0327		-	|0 0 0 0 0 0 1 1 0 0 1 0 0 1 1 1|
#QQucode_0x0328		-	|0 0 0 0 0 0 1 1 0 0 1 0 1 0 0 0|
#QQucode_0x032a		-	|0 0 0 0 0 0 1 1 0 0 1 0 1 0 1 0| QQuDECLARE_TYPE RECORD_CLASS,DEFINED,INCOMPLETE
#QQucode_0x032b		-	|0 0 0 0 0 0 1 1 0 0 1 0 1 0 1 1|
#QQucode_0x032d		-	|0 0 0 0 0 0 1 1 0 0 1 0 1 1 0 1| QQuDECLARE_TYPE         RECORD_CLASS,DEFINED
#QQucode_0x032e		-	|0 0 0 0 0 0 1 1 0 0 1 0 1 1 1 0| QQuDECLARE_TYPE         RECORD_CLASS,DEFINED
#QQucode_0x0333		-	|0 0 0 0 0 0 1 1 0 0 1 1 0 0 1 1|
#QQucode_0x0334		-	|0 0 0 0 0 0 1 1 0 0 1 1 0 1 0 0|
#QQucode_0x0335		-	|0 0 0 0 0 0 1 1 0 0 1 1 0 1 0 1| QQu_DECLARE_VARIABLE_tmp_val ARRAY_CLASS
#QQucode_0x0336		-	|0 0 0 0 0 0 1 1 0 0 1 1 0 1 1 0|
#QQucode_0x0337		-	|0 0 0 0 0 0 1 1 0 0 1 1 0 1 1 1| DECLARE_VARIABLE ARRAY_CLASS
#QQucode_0x0340		-	|0 0 0 0 0 0 1 1 0 1 0 0 0 0 0 0|
#QQucode_0x0341		-	|0 0 0 0 0 0 1 1 0 1 0 0 0 0 0 1|
#QQucode_0x0342		-	|0 0 0 0 0 0 1 1 0 1 0 0 0 0 1 0|
#QQucode_0x0343		-	|0 0 0 0 0 0 1 1 0 1 0 0 0 0 1 1|
#QQucode_0x0346		-	|0 0 0 0 0 0 1 1 0 1 0 0 0 1 1 0|
#QQucode_0x0347		-	|0 0 0 0 0 0 1 1 0 1 0 0 0 1 1 1|
#QQucode_0x0348		-	|0 0 0 0 0 0 1 1 0 1 0 0 1 0 0 0|
#QQucode_0x0349		-	|0 0 0 0 0 0 1 1 0 1 0 0 1 0 0 1|
#QQucode_0x034b		-	|0 0 0 0 0 0 1 1 0 1 0 0 1 0 1 1|
#QQucode_0x034c		-	|0 0 0 0 0 0 1 1 0 1 0 0 1 1 0 0|
#QQucode_0x034e		-	|0 0 0 0 0 0 1 1 0 1 0 0 1 1 1 0|
#QQucode_0x034f		-	|0 0 0 0 0 0 1 1 0 1 0 0 1 1 1 1|
#QQucode_0x0350		-	|0 0 0 0 0 0 1 1 0 1 0 1 0 0 0 0| QQuDECLARE_TYPE ARRAY_CLASS,UNCONSTRAINED
#QQucode_0x0351		-	|0 0 0 0 0 0 1 1 0 1 0 1 0 0 0 1| QQuDECLARE_TYPE ARRAY_CLASS,UNCONSTRAINED,IS_VISIBLE
#QQucode_0x0353		-	|0 0 0 0 0 0 1 1 0 1 0 1 0 0 1 1|
#QQucode_0x0354		-	|0 0 0 0 0 0 1 1 0 1 0 1 0 1 0 0|
#QQucode_0x0355		-	|0 0 0 0 0 0 1 1 0 1 0 1 0 1 0 1|
#QQucode_0x0356		-	|0 0 0 0 0 0 1 1 0 1 0 1 0 1 1 0|
#QQucode_0x0358		-	|0 0 0 0 0 0 1 1 0 1 0 1 1 0 0 0|
#QQucode_0x0359		-	|0 0 0 0 0 0 1 1 0 1 0 1 1 0 0 1|
#QQucode_0x035b		-	|0 0 0 0 0 0 1 1 0 1 0 1 1 0 1 1| QQuDECLARE_TYPE ARRAY_CLASS,DEFINED
#QQucode_0x035c		-	|0 0 0 0 0 0 1 1 0 1 0 1 1 1 0 0|
#QQucode_0x035d		-	|0 0 0 0 0 0 1 1 0 1 0 1 1 1 0 1| DECLARE_TYPE ARRAY_CLASS,DEFINED
#QQucode_0x035e		-	|0 0 0 0 0 0 1 1 0 1 0 1 1 1 1 0|
#QQucode_0x036a		-	|0 0 0 0 0 0 1 1 0 1 1 0 1 0 1 0|
#QQucode_0x036b		-	|0 0 0 0 0 0 1 1 0 1 1 0 1 0 1 1|
#QQucode_0x036c		-	|0 0 0 0 0 0 1 1 0 1 1 0 1 1 0 0|
#QQucode_0x036d		-	|0 0 0 0 0 0 1 1 0 1 1 0 1 1 0 1|
#QQucode_0x036e		-	|0 0 0 0 0 0 1 1 0 1 1 0 1 1 1 0|
#QQucode_0x036f		-	|0 0 0 0 0 0 1 1 0 1 1 0 1 1 1 1|
#QQucode_0x0374		-	|0 0 0 0 0 0 1 1 0 1 1 1 0 1 0 0|
#QQucode_0x0377		-	|0 0 0 0 0 0 1 1 0 1 1 1 0 1 1 1|
#QQucode_0x0378		-	|0 0 0 0 0 0 1 1 0 1 1 1 1 0 0 0|
#QQucode_0x037a		-	|0 0 0 0 0 0 1 1 0 1 1 1 1 0 1 0|
#QQucode_0x037b		-	|0 0 0 0 0 0 1 1 0 1 1 1 1 0 1 1|
#QQucode_0x037d		-	|0 0 0 0 0 0 1 1 0 1 1 1 1 1 0 1|
#QQucode_0x037e		-	|0 0 0 0 0 0 1 1 0 1 1 1 1 1 1 0|
#QQucode_0x0384		-	|0 0 0 0 0 0 1 1 1 0 0 0 0 1 0 0|
#QQucode_0x0385		-	|0 0 0 0 0 0 1 1 1 0 0 0 0 1 0 1|
#QQucode_0x0386		-	|0 0 0 0 0 0 1 1 1 0 0 0 0 1 1 0|
#QQucode_0x0387		-	|0 0 0 0 0 0 1 1 1 0 0 0 0 1 1 1| DECLARE_VARIABLE PACKAGE_CLASS
#QQucode_0x038c		-	|0 0 0 0 0 0 1 1 1 0 0 0 1 1 0 0|
#QQucode_0x038d		-	|0 0 0 0 0 0 1 1 1 0 0 0 1 1 0 1|
#QQucode_0x038e		-	|0 0 0 0 0 0 1 1 1 0 0 0 1 1 1 0| DECLARE_TYPE PACKAGE_CLASS,DEFINED
#QQucode_0x038f		-	|0 0 0 0 0 0 1 1 1 0 0 0 1 1 1 1|
#QQucode_0x0395		-	|0 0 0 0 0 0 1 1 1 0 0 1 0 1 0 1|
#QQucode_0x0396		-	|0 0 0 0 0 0 1 1 1 0 0 1 0 1 1 0| DECLARE_VARIABLE Heap_Access,BY_ALLOCATION,WITH_VALUE
#QQucode_0x0397		-	|0 0 0 0 0 0 1 1 1 0 0 1 0 1 1 1|
#QQucode_0x0398		-	|0 0 0 0 0 0 1 1 1 0 0 1 1 0 0 0|
#QQucode_0x0399		-	|0 0 0 0 0 0 1 1 1 0 0 1 1 0 0 1|
#QQucode_0x039a		-	|0 0 0 0 0 0 1 1 1 0 0 1 1 0 1 0|
#QQucode_0x039b		-	|0 0 0 0 0 0 1 1 1 0 0 1 1 0 1 1|
#QQucode_0x039c		-	|0 0 0 0 0 0 1 1 1 0 0 1 1 1 0 0|
#QQucode_0x039d		-	|0 0 0 0 0 0 1 1 1 0 0 1 1 1 0 1|
#QQucode_0x039e		-	|0 0 0 0 0 0 1 1 1 0 0 1 1 1 1 0|
#QQucode_0x039f		-	|0 0 0 0 0 0 1 1 1 0 0 1 1 1 1 1|
#QQucode_0x03a0		-	|0 0 0 0 0 0 1 1 1 0 1 0 0 0 0 0|
#QQucode_0x03a1		-	|0 0 0 0 0 0 1 1 1 0 1 0 0 0 0 1|
#QQucode_0x03a2		-	|0 0 0 0 0 0 1 1 1 0 1 0 0 0 1 0|
#QQucode_0x03a3		-	|0 0 0 0 0 0 1 1 1 0 1 0 0 0 1 1|
#QQucode_0x03a4		-	|0 0 0 0 0 0 1 1 1 0 1 0 0 1 0 0|
#QQucode_0x03a5		-	|0 0 0 0 0 0 1 1 1 0 1 0 0 1 0 1|
#QQucode_0x03a6		-	|0 0 0 0 0 0 1 1 1 0 1 0 0 1 1 0|
#QQucode_0x03a7		-	|0 0 0 0 0 0 1 1 1 0 1 0 0 1 1 1|
#QQucode_0x03a8		-	|0 0 0 0 0 0 1 1 1 0 1 0 1 0 0 0|
#QQucode_0x03a9		-	|0 0 0 0 0 0 1 1 1 0 1 0 1 0 0 1|
#QQucode_0x03ab		-	|0 0 0 0 0 0 1 1 1 0 1 0 1 0 1 1|
#QQucode_0x03ac		-	|0 0 0 0 0 0 1 1 1 0 1 0 1 1 0 0|
#QQucode_0x03ad		-	|0 0 0 0 0 0 1 1 1 0 1 0 1 1 0 1| DECLARE_TYPE Heap_Access,DEFINED
#QQucode_0x03ae		-	|0 0 0 0 0 0 1 1 1 0 1 0 1 1 1 0|
#QQucode_0x03b5		-	|0 0 0 0 0 0 1 1 1 0 1 1 0 1 0 1|
#QQucode_0x03b6		-	|0 0 0 0 0 0 1 1 1 0 1 1 0 1 1 0| DECLARE_VARIABLE Access,BY_ALLOCATION,WITH_VALUE
#QQucode_0x03b7		-	|0 0 0 0 0 0 1 1 1 0 1 1 0 1 1 1|
#QQucode_0x03b8		-	|0 0 0 0 0 0 1 1 1 0 1 1 1 0 0 0|
#QQucode_0x03b9		-	|0 0 0 0 0 0 1 1 1 0 1 1 1 0 0 1|
#QQucode_0x03ba		-	|0 0 0 0 0 0 1 1 1 0 1 1 1 0 1 0|
#QQucode_0x03bb		-	|0 0 0 0 0 0 1 1 1 0 1 1 1 0 1 1|
#QQucode_0x03bc		-	|0 0 0 0 0 0 1 1 1 0 1 1 1 1 0 0| QQu_DECLARE_VARIABLE_with_null_value Access
#QQucode_0x03bd		-	|0 0 0 0 0 0 1 1 1 0 1 1 1 1 0 1|
#QQucode_0x03be		-	|0 0 0 0 0 0 1 1 1 0 1 1 1 1 1 0|
#QQucode_0x03bf		-	|0 0 0 0 0 0 1 1 1 0 1 1 1 1 1 1|
#QQucode_0x03c4		-	|0 0 0 0 0 0 1 1 1 1 0 0 0 1 0 0|
#QQucode_0x03c5		-	|0 0 0 0 0 0 1 1 1 1 0 0 0 1 0 1|
#QQucode_0x03c6		-	|0 0 0 0 0 0 1 1 1 1 0 0 0 1 1 0|
#QQucode_0x03c7		-	|0 0 0 0 0 0 1 1 1 1 0 0 0 1 1 1| QQu_DECLARE_TYPE Heap_Access
#QQucode_0x03cc		-	|0 0 0 0 0 0 1 1 1 1 0 0 1 1 0 0|
#QQucode_0x03cd		-	|0 0 0 0 0 0 1 1 1 1 0 0 1 1 0 1| QQu_DECLARE_TYPE Heap_Access,IS_VISIBLE,INCOMPLETE
#QQucode_0x03ce		-	|0 0 0 0 0 0 1 1 1 1 0 0 1 1 1 0| QQu_DECLARE_TYPE Heap_Access
#QQucode_0x03cf		-	|0 0 0 0 0 0 1 1 1 1 0 0 1 1 1 1|
#QQucode_0x03d1		-	|0 0 0 0 0 0 1 1 1 1 0 1 0 0 0 1|
#QQucode_0x03d2		-	|0 0 0 0 0 0 1 1 1 1 0 1 0 0 1 0|
#QQucode_0x03d3		-	|0 0 0 0 0 0 1 1 1 1 0 1 0 0 1 1| QQu_DECLARE_TYPE Access,DEFINED
#QQucode_0x03d4		-	|0 0 0 0 0 0 1 1 1 1 0 1 0 1 0 0|
#QQucode_0x03d5		-	|0 0 0 0 0 0 1 1 1 1 0 1 0 1 0 1| DECLARE_TYPE Access,DEFINED
#QQucode_0x03d6		-	|0 0 0 0 0 0 1 1 1 1 0 1 0 1 1 0|
#QQucode_0x03d8		-	|0 0 0 0 0 0 1 1 1 1 0 1 1 0 0 0| DECLARE_VARIABLE FLOAT_CLASS
#QQucode_0x03d9		-	|0 0 0 0 0 0 1 1 1 1 0 1 1 0 0 1|
#QQucode_0x03da		-	|0 0 0 0 0 0 1 1 1 1 0 1 1 0 1 0|
#QQucode_0x03db		-	|0 0 0 0 0 0 1 1 1 1 0 1 1 0 1 1| DECLARE_VARIABLE FLOAT_CLASS,WITH_VALUE,IS_VISIBLE
#QQucode_0x03dc		-	|0 0 0 0 0 0 1 1 1 1 0 1 1 1 0 0|
#QQucode_0x03dd		-	|0 0 0 0 0 0 1 1 1 1 0 1 1 1 0 1|
#QQucode_0x03de		-	|0 0 0 0 0 0 1 1 1 1 0 1 1 1 1 0|
#QQucode_0x03df		-	|0 0 0 0 0 0 1 1 1 1 0 1 1 1 1 1| DECLARE_VARIABLE FLOAT_CLASS,WITH_VALUE
#QQucode_0x03e0		-	|0 0 0 0 0 0 1 1 1 1 1 0 0 0 0 0|
#QQucode_0x03e1		-	|0 0 0 0 0 0 1 1 1 1 1 0 0 0 0 1|
#QQucode_0x03e3		-	|0 0 0 0 0 0 1 1 1 1 1 0 0 0 1 1|
#QQucode_0x03e4		-	|0 0 0 0 0 0 1 1 1 1 1 0 0 1 0 0|
#QQucode_0x03e5		-	|0 0 0 0 0 0 1 1 1 1 1 0 0 1 0 1|
#QQucode_0x03e6		-	|0 0 0 0 0 0 1 1 1 1 1 0 0 1 1 0|
#QQucode_0x03e8		-	|0 0 0 0 0 0 1 1 1 1 1 0 1 0 0 0|
#QQucode_0x03e9		-	|0 0 0 0 0 0 1 1 1 1 1 0 1 0 0 1| QQuDECLARE_VARIABLE DISCRETE
#QQucode_0x03ea		-	|0 0 0 0 0 0 1 1 1 1 1 0 1 0 1 0|
#QQucode_0x03eb		-	|0 0 0 0 0 0 1 1 1 1 1 0 1 0 1 1|
#QQucode_0x03ec		-	|0 0 0 0 0 0 1 1 1 1 1 0 1 1 0 0| DECLARE_VARIABLE DISCRETE,WITH_VALUE,WITH_CONSTRAINT
#QQucode_0x03ed		-	|0 0 0 0 0 0 1 1 1 1 1 0 1 1 0 1|
#QQucode_0x03ee		-	|0 0 0 0 0 0 1 1 1 1 1 0 1 1 1 0|
#QQucode_0x03ef		-	|0 0 0 0 0 0 1 1 1 1 1 0 1 1 1 1|
#QQucode_0x03f0		-	|0 0 0 0 0 0 1 1 1 1 1 1 0 0 0 0|
#QQucode_0x03f1		-	|0 0 0 0 0 0 1 1 1 1 1 1 0 0 0 1| QQuDECLARE_VARIABLE DISCRETE_CLASS,WITH_VALUE
#QQucode_0x03f2		-	|0 0 0 0 0 0 1 1 1 1 1 1 0 0 1 0|
#QQucode_0x03f3		-	|0 0 0 0 0 0 1 1 1 1 1 1 0 0 1 1|
#QQucode_0x03f5		-	|0 0 0 0 0 0 1 1 1 1 1 1 0 1 0 1|
#QQucode_0x03f6		-	|0 0 0 0 0 0 1 1 1 1 1 1 0 1 1 0|
#QQucode_0x03f7		-	|0 0 0 0 0 0 1 1 1 1 1 1 0 1 1 1|
#QQucode_0x03f8		-	|0 0 0 0 0 0 1 1 1 1 1 1 1 0 0 0| QQuDECLARE_TYPE DISCRETE_CLASS,WITH_CONSTRAINT
#QQucode_0x03f9		-	|0 0 0 0 0 0 1 1 1 1 1 1 1 0 0 1| QQuDECLARE_TYPE DISCRETE_CLASS,DEFINED
#QQucode_0x03fa		-	|0 0 0 0 0 0 1 1 1 1 1 1 1 0 1 0|
#QQucode_0x03fb		-	|0 0 0 0 0 0 1 1 1 1 1 1 1 0 1 1|
#QQucode_0x03fc		-	|0 0 0 0 0 0 1 1 1 1 1 1 1 1 0 0|
#QQucode_0x03fd		-	|0 0 0 0 0 0 1 1 1 1 1 1 1 1 0 1| QQuDECLARE_TYPE DISCRETE_CLASS,DEFINED,ENUM
#QQucode_0x03fe		-	|0 0 0 0 0 0 1 1 1 1 1 1 1 1 1 0| QQuDECLARE_TYPE DISCRETE_CLASS,DEFINED,ENUM
#QQucode_0x0400		x	|0 0 0 0 0 1 0 0|x              |
#QQucode_0x0500		x	|0 0 0 0 0 1 0 1|x              |
#QQucode_0x0600		x	|0 0 0 0 0 1 1 0|x              |
#QQucode_0x0700		x	|0 0 0 0 0 1 1 1|x              |
#QQucode_0x0800		x	|0 0 0 0 1 0 0 0|x              | QQu_return_imm_exception s8,>R
#QQucode_0x0900		x	|0 0 0 0 1 0 0 1 0 0|x          | BINARY_SCALE_OP
#QQucode_0x0940		x	|0 0 0 0 1 0 0 1 0 1|x          | BINARY_SCALE_OP
#QQucode_0x0940		x	|0 0 0 0 1 0 0 1 1 0|x          | BINARY_SCALE_OP
#QQucode_0x09c0		x	|0 0 0 0 1 0 0 1 1 1|x          | BINARY_SCALE_OP
#QQucode_0x0a00		x	|0 0 0 0 1 0 1 0 0|x            | QQu_add_imm
#QQucode_0x0a80		x	|0 0 0 0 1 0 1 0 1|x            | QQu_add_imm
#QQucode_0x0b00		x	|0 0 0 0 1 0 1 1|x              | QQu_is_equal s8
#QQucode_0x0c00		x	|0 0 0 0 1 1 0 0|x              | QQu_greater_equal s8
#QQucode_0x0d00		x	|0 0 0 0 1 1 0 1|x              | QQu_int_less_than s8
#QQucode_0x0e00		x	|0 0 0 0 1 1 1 0|x              | QQu_int_not_equal s8
#QQucode_0x0f00		x	|0 0 0 0 1 1 1 1|x              | QQu_int_is_equal s8
#QQucode_0x1000		x	|0 0 0 1 0 0 0 0|x              |
#QQucode_0x1100		x	|0 0 0 1 0 0 0 1|x              |
#QQucode_0x1200		x	|0 0 0 1 0 0 1 0|x              |
#QQucode_0x1300		x	|0 0 0 1 0 0 1 1|x              |
#QQucode_0x1400		x	|0 0 0 1 0 1 0 0|x              |
#QQucode_0x1500		x	|0 0 0 1 0 1 0 1|x              |
#QQucode_0x1600		x	|0 0 0 1 0 1 1 0|x              |
#QQucode_0x1700		x	|0 0 0 1 0 1 1 1|x              |
#QQucode_0x1800		x	|0 0 0 1 1 0 0 0|x              |
#QQucode_0x1900		x	|0 0 0 1 1 0 0 1|x              |
#QQucode_0x1a00		x	|0 0 0 1 1 0 1 0|x              |
#QQucode_0x1b00		x	|0 0 0 1 1 0 1 1|x              |
#QQucode_0x1c00		x	|0 0 0 1 1 1 0 0|x              |
#QQucode_0x1d00		x	|0 0 0 1 1 1 0 1|x              |
QQucode_0x1e00		x	|0 0 0 1 1 1 1|x                |
QQucode_0x1e00		x	|0 0 1 1 0 0 0 1|x              |
QQucode_0x1e00		x	|0 0 1 1 0 0 1|x                |
QQucode_0x1e00		x	|0 0 1 1 0 1 0 1|x              |
QQucode_0x1e00		x	|0 0 1 1 1 0 0 1|x              |
QQucode_0x1e00		x	|0 0 1 1 1 0 1|x                |
QQucode_0x1e00		x	|0 0 1 1 1 1 0 1|x              |
QQucode_0x1e00		x	|0 1 0 0 0 0 0 0|x              |
QQucode_0x2000		x	|0 0 1 0 0 0 0 0|x              |
QQucode_0x2100		x	|0 0 1 0 0 0 0 1|x              |
QQucode_0x2200		x	|0 0 1 0 0 0 1 0|x              |
QQucode_0x2300		x	|0 0 1 0 0 0 1 1|x              |
QQucode_0x2400		x	|0 0 1 0 0 1 0 0|x              |
QQucode_0x2500		x	|0 0 1 0 0 1 0 1|x              |
QQucode_0x2600		x	|0 0 1 0 0 1 1 0|x              |
QQucode_0x2700		x	|0 0 1 0 0 1 1 1|x              |
QQucode_0x2800		x	|0 0 1 0 1 0 0 0|x              |
QQucode_0x2900		x	|0 0 1 0 1 0 0 1|x              |
QQucode_0x2a00		x	|0 0 1 0 1 0 1 0|x              |
QQucode_0x2b00		x	|0 0 1 0 1 0 1 1|x              |
QQucode_0x2c00		x	|0 0 1 0 1 1 0 0|x              |
QQucode_0x2d00		x	|0 0 1 0 1 1 0 1|x              |
QQucode_0x2d00		x	|0 0 1 0 1 1 1 1|x              |
QQucode_0x2e00		x	|0 0 1 0 1 1 1 0|x              |
QQucode_0x3000		x	|0 0 1 1 0 0 0 0|x              |
#QQucode_0x3400		x	|0 0 1 1 0 1 0 0|x              |
#QQucode_0x3600		x	|0 0 1 1 0 1 1|x                | QQu_LOOP_DECREASING pcrelneg,>JC
QQucode_0x3800		x	|0 0 1 1 1 0 0 0|x              |
QQucode_0x3c00		x	|0 0 1 1 1 1 0 0|x              |
#QQucode_0x3e00		x	|0 0 1 1 1 1 1|x                | LOOP_INCREASING pcrelneg,>JC
QQucode_0x4100		x	|0 1 0 0 0 0 0 1|x              |
QQucode_0x4200		x	|0 1 0 0 0 0 1 0|x              |
QQucode_0x4300		x	|0 1 0 0 0 0 1 1|x              |
QQucode_0x4400		x	|0 1 0 0 0 1 0 0|x              |
QQucode_0x4500		x	|0 1 0 0 0 1 0 1|x              |
QQucode_0x4600		x	|0 1 0 0 0 1 1|x                |
#QQucode_0x4800		x	|0 1 0 0 1|x                    | SHORT_LITERAL slit
#QQucode_0x5000		x	|0 1 0 1 0|x                    |
#QQucode_0x5800		x	|0 1 0 1 1|x                    | PUSH_DOUBLE pcrel,dbl
#QQucode_0x6000		x	|0 1 1 0 0|x                    | INDIRECT_LITERAL pcrel,literal
#QQucode_0x6800		x	|0 1 1 0 1|x                    | QQujump_if_not pcrel,>JC
#QQucode_0x7000		x	|0 1 1 1 0|x                    | QQu_jump_if_true pcrel,>JC
#QQucode_0x7800		x	|0 1 1 1 1|x                    | JUMP pcrel,>J
#QQucode_0x8000		x	|1 0 0 0 0 0 0|x                | CALL
#QQucode_0x8200		x	|1 0 0 0 0 0 1|x                | CALL
#QQucode_0x8200		x	|1 0 0 0 0 1|x                  | CALL
#QQucode_0x8200		x	|1 0 0 0 1|x                    | CALL
#QQucode_0x8200		x	|1 0 0 1|x                      | CALL
#QQucode_0xa000		x	|1 0 1 0 0 0 0|x                | STORE_UNCHECKED
#QQucode_0xa200		x	|1 0 1 0 0 0 1|x                | STORE_UNCHECKED
#QQucode_0xa200		x	|1 0 1 0 0 1|x                  | STORE_UNCHECKED
#QQucode_0xa200		x	|1 0 1 0 1|x                    | STORE_UNCHECKED
#QQucode_0xa200		x	|1 0 1 1|x                      | STORE_UNCHECKED
#QQucode_0xc000		x	|1 1 0 0 0 0 0|x                | STORE
#QQucode_0xc200		x	|1 1 0 0 0 0 1|x                | STORE
#QQucode_0xc200		x	|1 1 0 0 0 1|x                  | STORE
#QQucode_0xc200		x	|1 1 0 0 1|x                    | STORE
#QQucode_0xc200		x	|1 1 0 1|x                      | STORE
#QQucode_0xe000		x	|1 1 1|x                        | LOAD llvl,ldelta
'''

r1000_desc = """

# Noteworthy segments:
#   ⟦120ea4603⟧ - has unreach{ed|able} subprograms: 0x25b, 0x28b, 0x4fb

#-----------------------
# Make places we get to, but do not handle grep(1)able
QQunknown_instruction	-						| unknown			|

#-----------------------
# Very helpful, but only hypothesis /phk
#zero_is_invalid_ins	>R						|0 0 0 0|0 0 0 0|0 0 0 0|0 0 0 0|

# BODY_0880 start
Action			Illegal						|0 0 0 0|0 0 0 0|0 0 0 0|0 0 0 0|

#-----------------------
# gc44,0076								|0 0 0 0|0 0 0 0|0 0 0 0|0 1 1 1|
ACTION			BREAK_OPTIONAL					|0 0 0 0|0 0 0 0|0 0 0 0|0 1 1 1|

#-----------------------
# 93b91846e, 011e+0125		(Access type)
Store_Top		Heap_Access,At_Offset_1				|0 0 0 0|0 0 0 0|0 0 1 1|0 0 0 1|
Store_Top		Heap_Access,At_Offset_2				|0 0 0 0|0 0 0 0|0 0 1 1|0 0 1 0|
Store_Top		Heap_Access,At_Offset_3				|0 0 0 0|0 0 0 0|0 0 1 1|0 0 1 1|
Store_Top		Heap_Access,At_Offset_4				|0 0 0 0|0 0 0 0|0 0 1 1|0 1 0 0|
Store_Top		Heap_Access,At_Offset_5				|0 0 0 0|0 0 0 0|0 0 1 1|0 1 0 1|
Store_Top		Heap_Access,At_Offset_6				|0 0 0 0|0 0 0 0|0 0 1 1|0 1 1 0|
Store_Top               Access,At_Offset_1				|0 0 0 0|0 0 0 0|0 0 1 1|1 0 0 1|
Store_Top               Access,At_Offset_2				|0 0 0 0|0 0 0 0|0 0 1 1|1 0 1 0|
Store_Top               Access,At_Offset_3				|0 0 0 0|0 0 0 0|0 0 1 1|1 0 1 1|
Store_Top               Access,At_Offset_4				|0 0 0 0|0 0 0 0|0 0 1 1|1 1 0 0|
Store_Top               Access,At_Offset_5				|0 0 0 0|0 0 0 0|0 0 1 1|1 1 0 1|
Store_Top               Access,At_Offset_6                         	|0 0 0 0|0 0 0 0|0 0 1 1|1 1 1 0|
Store_Top_Unchecked	Float,At_Offset_1                              	|0 0 0 0|0 0 0 0|0 1 0 0|0 0 0 1|
Store_Top_Unchecked	Float,At_Offset_2                              	|0 0 0 0|0 0 0 0|0 1 0 0|0 0 1 0|
Store_Top_Uncheched	Float,At_Offset_3                              	|0 0 0 0|0 0 0 0|0 1 0 0|0 0 1 1|
Store_Top_Unchecked	Float,At_Offset_4                              	|0 0 0 0|0 0 0 0|0 1 0 0|0 1 0 0|
Store_Top_Unchecked	Float,At_Offset_5                              	|0 0 0 0|0 0 0 0|0 1 0 0|0 1 0 1|
Store_Top_Unchecked	Float,At_Offset_6                              	|0 0 0 0|0 0 0 0|0 1 0 0|0 1 1 0|

#-----------------------
# ⟦85b414c73⟧ 0x34e..34f	(Float)
#STORE_TOP		x						|0 0 0 0|0 0 0 0|0 1 0 0|0|0| x |

Store_Top               Float,At_Offset_1                               |0 0 0 0|0 0 0 0|0 1 0 0|1 0 0 1|
Store_Top               Float,At_Offset_2                               |0 0 0 0|0 0 0 0|0 1 0 0|1 0 1 0|
Store_Top               Float,At_Offset_3                               |0 0 0 0|0 0 0 0|0 1 0 0|1 0 1 1|
Store_Top               Float,At_Offset_4                               |0 0 0 0|0 0 0 0|0 1 0 0|1 1 0 0|
Store_Top               Float,At_Offset_5                               |0 0 0 0|0 0 0 0|0 1 0 0|1 1 0 1|
Store_Top               Float,At_Offset_6                               |0 0 0 0|0 0 0 0|0 1 0 0|1 1 1 0|

Store_Top_Unchecked     Discrete,At_Offset_1                            |0 0 0 0|0 0 0 0|0 1 0 1|0 0 0 1|
Store_Top_Unchecked     Discrete,At_Offset_2                            |0 0 0 0|0 0 0 0|0 1 0 1|0 0 1 0|
Store_Top_Uncheched     Discrete,At_Offset_3                            |0 0 0 0|0 0 0 0|0 1 0 1|0 0 1 1|
Store_Top_Unchecked     Discrete,At_Offset_4                            |0 0 0 0|0 0 0 0|0 1 0 1|0 1 0 0|
Store_Top_Unchecked     Discrete,At_Offset_5                            |0 0 0 0|0 0 0 0|0 1 0 1|0 1 0 1|
Store_Top_Unchecked     Discrete,At_Offset_6                            |0 0 0 0|0 0 0 0|0 1 0 1|0 1 1 0|

Store_Top               Discrete,At_Offset_1                            |0 0 0 0|0 0 0 0|0 1 0 1|1 0 0 1|
Store_Top               Discrete,At_Offset_2                            |0 0 0 0|0 0 0 0|0 1 0 1|1 0 1 0|
Store_Top               Discrete,At_Offset_3                            |0 0 0 0|0 0 0 0|0 1 0 1|1 0 1 1|
Store_Top               Discrete,At_Offset_4                            |0 0 0 0|0 0 0 0|0 1 0 1|1 1 0 0|
Store_Top               Discrete,At_Offset_5                            |0 0 0 0|0 0 0 0|0 1 0 1|1 1 0 1|
Store_Top               Discrete,At_Offset_6                            |0 0 0 0|0 0 0 0|0 1 0 1|1 1 1 0|

Action			Establish_Frame					|0 0 0 0|0 0 0 0|0 1 1 0|1 0 0 0|
Action			Query_Frame					|0 0 0 0|0 0 0 0|0 1 1 0|1 0 0 1|
Action			Alter_Break_Mask				|0 0 0 0|0 0 0 0|0 1 1 0|1 0 1 0|
Action			Query_Break_Address				|0 0 0 0|0 0 0 0|0 1 1 0|1 0 1 1|
Action			Query_Break_Mask				|0 0 0 0|0 0 0 0|0 1 1 0|1 1 0 0|
Action			Query_Break_Cause				|0 0 0 0|0 0 0 0|0 1 1 0|1 1 0 1| #0917
Action			Exit_Break					|0 0 0 0|0 0 0 0|0 1 1 0|1 1 1 0| #0912
#-----------------------
# gc88,0025								|0 0 0 0|0 0 0 0|0 1 1 0|1 1 1 1|
ACTION			BREAK_UNCONDITIONAL				|0 0 0 0|0 0 0 0|0 1 1 0|1 1 1 1|

# End of BODY_0880

# Start of BODY_0a20

Action			Discrete,Diana_Spare2				|0 0 0 0|0 0 0 0|1 0 0 0|0 1 1 1|
Action			Heap_Access,Diana_Spare2			|0 0 0 0|0 0 0 0|1 0 0 0|1 0 0 0|
Action			Discrete,Diana_Spare1				|0 0 0 0|0 0 0 0|1 0 0 0|1 0 0 1|
Action			Discrete,Diana_Spare0				|0 0 0 0|0 0 0 0|1 0 0 0|1 0 1 0|
Action			Heap_Access,Diana_Seq_Type_Get_Head		|0 0 0 0|0 0 0 0|1 0 0 0|1 0 1 1|
Action			Heap_Access,Diana_Put_Node_On_Seq_Type		|0 0 0 0|0 0 0 0|1 0 0 0|1 1 0 0|
Action			Heap_Access,Family				|0 0 0 0|0 0 0 0|1 0 0 0|1 1 0 1|
Action			Discrete,Diana_Arity_For_Kind			|0 0 0 0|0 0 0 0|1 0 0 0|1 1 1 0|
Action			Discrete,Diana_Map_Kind_To_Vci			|0 0 0 0|0 0 0 0|1 0 0 0|1 1 1 1|
Action			Store_String_Extended,pse			|0 0 0 0|0 0 0 0|1 0 0 1|0 0 0 0| pse                           |

#-----------------------
ACTION			PUSH_STRING_INDEXED,pse				|0 0 0 0|0 0 0 0|1 0 0 1|0 0 0 1| pse				|
#Action			Push_String_Extended_Indexed			|0 0 0 0|0 0 0 0|1 0 0 1|0 0 0 1| pse                           |

#-----------------------
# gc43,0029		PUSH_STRING					|0 0 0 0|0 0 0 0|1 0 0 1|0 0 1 0|
ACTION			PUSH_STRING,pse					|0 0 0 0|0 0 0 0|1 0 0 1|0 0 1 0| pse				|
# 0c4c/aa
#Action			Push_String_Extended,pse			|0 0 0 0|0 0 0 0|1 0 0 1|0 0 1 0| pse                           |


#-----------------------
# gc43,001c comments this as "push full address of a location in current code segment"
# XXX: it may be a bit of a stretch to assume that is a subp /phk
push_full_address	subp						|0 0 0 0|0 0 0 0|1 0 0 1|0 0 1 1| subp				|
# 0c47/aa
#Action			Spare7_Action					|0 0 0 0|0 0 0 0|1 0 0 1|0 0 1 1|

Execute			Package,Field_Reference_Dynamic			|0 0 0 0|0 0 0 0|1 0 0 1|0 1 0 1|
Execute			Package,Entry					|0 0 0 0|0 0 0 0|1 0 0 1|0 1 1 0|
Execute			Package,Field_Write_Dynamic			|0 0 0 0|0 0 0 0|1 0 0 1|0 1 1 1|
Execute			Package,Field_Read_Dynamic			|0 0 0 0|0 0 0 0|1 0 0 1|1 0 0 0| #0c2f
Action			Reference_Dynamic				|0 0 0 0|0 0 0 0|1 0 0 1|1 0 0 1|
Action			Call_Dynamic					|0 0 0 0|0 0 0 0|1 0 0 1|1 0 1 0|
Action			Store_Dynamic					|0 0 0 0|0 0 0 0|1 0 0 1|1 0 1 1|
Action			Load_Dynamic					|0 0 0 0|0 0 0 0|1 0 0 1|1 1 0 0|
Action			Jump_Nonzero_Dynamic				|0 0 0 0|0 0 0 0|1 0 0 1|1 1 0 1|
Action			Jump_Zero_Dynamic				|0 0 0 0|0 0 0 0|1 0 0 1|1 1 1 0|
Action			Jump_Dynamic					|0 0 0 0|0 0 0 0|1 0 0 1|1 1 1 1|

#-----------------------
# See for instance ⟦2009596b6⟧ @b4
#Action			Push_Structure_Extended /aa
PUSH_STRING_EXTENDED	abs,mark					|0 0 0 0|0 0 0 0|1 0 1 0|0 0 0 0| abs				|

#-----------------------
# See for instance ⟦b66a7252c⟧  /phk
#Action 		Push_Float_Extended
PUSH_FLOAT_EXTENDED	abs,dbl						|0 0 0 0|0 0 0 0|1 0 1 0|0 0 0 1| abs				|

#-----------------------
#Action 		Push_Discrete_Extended
PUSH_DISCRETE_EXTENDED	abs,literal					|0 0 0 0|0 0 0 0|1 0 1 0|0 0 1 0| abs				|

Action			Loop_Decreasing_Extended,abs,>JC		|0 0 0 0|0 0 0 0|1 0 1 0|0 0 1 1| abs                           |

#-----------------------
# XXX: a4 could be djnz or similar, always seem to jump backwards to a LOAD_TOP_0
Action			Loop_Increasing_Extended,abs,>JC		|0 0 0 0|0 0 0 0|1 0 1 0|0 1 0 0| abs				|

#-----------------------
# XXX: See 9739edd68 @0xf2e
Action			Jump_Nonzero_Extended,abs,>JC			|0 0 0 0|0 0 0 0|1 0 1 0|0 1 0 1| abs				|

#-----------------------
# XXX: See f1ef8a8ae @0x57d
Action			Jump_Zero_Extended,abs,>JC			|0 0 0 0|0 0 0 0|1 0 1 0|0 1 1 0| abs				|

#-----------------------
# ⟦ed62618ed⟧ @0x1cc confirms this is unconditional /phk
Action			Jump_Extended,abs,>J				|0 0 0 0|0 0 0 0|1 0 1 0|0 1 1 1| abs				|

Action			Increase_Priority				|0 0 0 0|0 0 0 0|1 0 1 1|0 0 1 1|
Action			Name_Partner					|0 0 0 0|0 0 0 0|1 0 1 1|0 1 0 0|
Action			Make_Parent					|0 0 0 0|0 0 0 0|1 0 1 1|0 1 0 1|
Action			Make_Scope					|0 0 0 0|0 0 0 0|1 0 1 1|0 1 1 0|
Action			Make_Self					|0 0 0 0|0 0 0 0|1 0 1 1|0 1 1 1|
Action			Set_Priority					|0 0 0 0|0 0 0 0|1 0 1 1|1 0 0 0|
Action			Get_Priority					|0 0 0 0|0 0 0 0|1 0 1 1|1 0 0 1|
Action			Initiate_Delay					|0 0 0 0|0 0 0 0|1 0 1 1|1 0 1 0|

#-----------------------
# gc43,003d								|0 0 0 0|0 0 0 0|1 0 1 1|1 0 1 1|
ACTION			SIGNAL_COMPLETION,>R				|0 0 0 0|0 0 0 0|1 0 1 1|1 0 1 1|

#-----------------------
# gc43,003c 		SIGNAL_ACTIVATED				|0 0 0 0|0 0 0 0|1 0 1 1|1 1 0 0|
ACTION			SIGNAL_ACTIVATED				|0 0 0 0|0 0 0 0|1 0 1 1|1 1 0 0|

Action			Activate_Heap_Tasks				|0 0 0 0|0 0 0 0|1 0 1 1|1 1 0 1| #0b95
Action			Activate_Tasks					|0 0 0 0|0 0 0 0|1 0 1 1|1 1 1 0|

#-----------------------
# gc42,000d		ACCEPT_ACTIVATION				|0 0 0 0|0 0 0 0|1 0 1 1|1 1 1 1|
ACTION			ACCEPT_ACTIVATION				|0 0 0 0|0 0 0 0|1 0 1 1|1 1 1 1|

Action			Make_Default					|0 0 0 0|0 0 0 0|1 1 0 0|0 1 0 0|
Action			Set_Block_Start					|0 0 0 0|0 0 0 0|1 1 0 0|0 1 0 1|
Action			Check_Subprogram_Elaborated			|0 0 0 0|0 0 0 0|1 1 0 0|0 1 1 0|

#-----------------------
# gc42,000f		ELABORATE_SUBPROGRAM				|0 0 0 0|0 0 0 0|1 1 0 0|0 1 1 1| #0b77
ACTION			ELABORATE_SUBPROGRAM				|0 0 0 0|0 0 0 0|1 1 0 0|0 1 1 1|

#-----------------------
# (3f2fe70c1,02d3)	end of a loop		for J in X'range loop ... end loop;
Action			Pop_Auxiliary_Range				|0 0 0 0|0 0 0 0|1 1 0 0|1 0 0 0|

#-----------------------
# (3f2fe70c1,012e)	end of a loop
Action			Pop_Auxiliary_Loop				|0 0 0 0|0 0 0 0|1 1 0 0|1 0 0 1|

#-----------------------
# 467 times followed by 0x0000
# many times last instruction before TRAP entry point /phk
# Returning pointer or directly returning function result (36a4ea3d7, 0374 - return Null_Time)
Action			Exit_Nullary_Function,>R			|0 0 0 0|0 0 0 0|1 1 0 0|1 0 1 0|

Action			Pop_Block_With_Result				|0 0 0 0|0 0 0 0|1 1 0 0|1 0 1 1|
Action			Pop_Block					|0 0 0 0|0 0 0 0|1 1 0 0|1 1 0 0|
Action			Spare6_Action					|0 0 0 0|0 0 0 0|1 1 0 0|1 1 0 1|

#-----------------------
# Guess/aa Follows LOOP_INCREASING, but not LOOP_DECREASING
Action			Pop_Auxiliary					|0 0 0 0|0 0 0 0|1 1 0 0|1 1 1 0|

#-----------------------
# ⟦ec043f33f⟧ @0x5f has this followed by a two-word instruction.
# May be conditional return? /phk
# (93b91846e,0123)	start of a loop
Action			Mark_Auxiliary					|0 0 0 0|0 0 0 0|1 1 0 0|1 1 1 1|

Action			Swap_Control					|0 0 0 0|0 0 0 0|1 1 0 1|0 0 0 0|
Pop_Control		Pop_Count_1					|0 0 0 0|0 0 0 0|1 1 0 1|0 0 0 1|
Pop_Control		Pop_Count_2					|0 0 0 0|0 0 0 0|1 1 0 1|0 0 1 0|
Pop_Control		Pop_Count_3					|0 0 0 0|0 0 0 0|1 1 0 1|0 0 1 1|
Pop_Control		Pop_Count_4					|0 0 0 0|0 0 0 0|1 1 0 1|0 1 0 0|
Pop_Control		Pop_Count_5					|0 0 0 0|0 0 0 0|1 1 0 1|0 1 0 1|
Pop_Control		Pop_Count_6					|0 0 0 0|0 0 0 0|1 1 0 1|0 1 1 0|
Pop_Control		Pop_Count_7					|0 0 0 0|0 0 0 0|1 1 0 1|0 1 1 1|

#-----------------------
# gc43,00027		0						|0 0 0 0|0 0 0 0|1 1 0 1|1 0 0 0|
# /aa
#LOAD_TOP		x						|0 0 0 0|0 0 0 0|1 1 0 1|1|0| x |

Load_Top		At_Offset_0					|0 0 0 0|0 0 0 0|1 1 0 1|1 0 0 0|
Load_Top		At_Offset_1					|0 0 0 0|0 0 0 0|1 1 0 1|1 0 0 1|
Load_Top		At_Offset_2					|0 0 0 0|0 0 0 0|1 1 0 1|1 0 1 0|
Load_Top		At_Offset_3					|0 0 0 0|0 0 0 0|1 1 0 1|1 0 1 1|
Load_Top		At_Offset_4					|0 0 0 0|0 0 0 0|1 1 0 1|1 1 0 0|
Load_Top		At_Offset_5					|0 0 0 0|0 0 0 0|1 1 0 1|1 1 0 1|
Load_Top		At_Offset_6					|0 0 0 0|0 0 0 0|1 1 0 1|1 1 1 0|

#-----------------------
# feh269,1c		Value_02					|0 0 0 0|0 0 0 0|1 1 1 0|0 0 1 0|
# gc44,0046		1						|0 0 0 0|0 0 0 0|1 1 1 0|0 0 0 1|
# gc43,0036		2						|0 0 0 0|0 0 0 0|1 1 1 0|0 0 1 0|
LOAD_ENCACHED		eon						|0 0 0 0|0 0 0 0|1 1 1| eon	|

# end of BODY_0a20

# Start of BODY_0ca0


#-----------------------
# g88,001e		EXCEPTION_CLASS,RAISE_OP 			|0 0 0 0|0 0 0 1|0 0 0 0|0 0 0 0|
# g28, location 4 = raise instruction					|0 0 0 0|0 0 0 1|0 0 0 0|0 0 0 0|
EXECUTE			EXCEPTION_CLASS,RAISE_OP,>R			|0 0 0 0|0 0 0 1|0 0 0 0|0 0 0 0|

#-----------------------
EXECUTE			EXCEPTION_CLASS,RERAISE_OP,>R			|0 0 0 0|0 0 0 1|0 0 0 0|0 0 0 1|

Execute			Exception,Address				|0 0 0 0|0 0 0 1|0 0 0 0|0 1 1 0|
Execute			Exception,Get_Name				|0 0 0 0|0 0 0 1|0 0 0 0|0 1 1 1|
Execute			Exception,Is_Instruction_Error			|0 0 0 0|0 0 0 1|0 0 0 0|1 0 0 1|
Execute			Exception,Is_Tasking_Error			|0 0 0 0|0 0 0 1|0 0 0 0|1 0 1 0|
Execute			Exception,Is_Storage_Error			|0 0 0 0|0 0 0 1|0 0 0 0|1 0 1 1|
Execute			Exception,Is_Program_Error			|0 0 0 0|0 0 0 1|0 0 0 0|1 1 0 0|
Execute			Exception,Is_Numeric_Error			|0 0 0 0|0 0 0 1|0 0 0 0|1 1 0 1| #0ee0

#-----------------------
# ⟦85b414c73⟧ @0x357
#IS_NUMERIC_ERROR_OP	-						|0 0 0 0|0 0 0 1|0 0 0 0|1 1 0 1|

Execute			Exception,Is_Constraint_Error			|0 0 0 0|0 0 0 1|0 0 0 0|1 1 1 0|

#-----------------------
# ⟦36a4ea3d7⟧ @0x0366	when Calendar.Time_Error =>
Execute			Exception,Equal					|0 0 0 0|0 0 0 1|0 0 0 0|1 1 1 1| #0ed4

Execute			Any,Is_Initialization_Repeated			|0 0 0 0|0 0 0 1|0 0 0 1|0 0 0 0|
Execute			Any,Has_Repeated_Initialization			|0 0 0 0|0 0 0 1|0 0 0 1|0 0 0 1|
Execute			Any,Make_Constrained				|0 0 0 0|0 0 0 1|0 0 0 1|0 0 1 0|
Execute			Heap_Access,Size				|0 0 0 0|0 0 0 1|0 0 0 1|0 0 1 1|
Execute			Access,Size					|0 0 0 0|0 0 0 1|0 0 0 1|0 1 0 0|
Execute			Any,Structure_Clear				|0 0 0 0|0 0 0 1|0 0 0 1|0 1 0 1|
Execute			Any,Address_Of_Type				|0 0 0 0|0 0 0 1|0 0 0 1|0 1 1 0|
Execute			Any,Structure_Query				|0 0 0 0|0 0 0 1|0 0 0 1|0 1 1 1|
Execute			Any,Write_Unchecked				|0 0 0 0|0 0 0 1|0 0 0 1|1 0 0 0|
Execute			Any,Check_In_Formal_Type			|0 0 0 0|0 0 0 1|0 0 0 1|1 0 0 1|
Execute			Any,Not_In_Type					|0 0 0 0|0 0 0 1|0 0 0 1|1 0 1 0| #0e92
Execute			Any,In_Type					|0 0 0 0|0 0 0 1|0 0 0 1|1 0 1 1|
Execute			Any,Convert_Unchecked				|0 0 0 0|0 0 0 1|0 0 0 1|1 1 0 0|

#-----------------------
# ⟦36a4ea3d7⟧ @0x68d	Name : constant String := Months'Image (Month);
# Used for Image function, followed by 1c00 or 1c01
#QQuImage		-						|0 0 0 0|0 0 0 1|0 0 0 1|1 1 0 0|

Execute			Any,Convert_To_Formal				|0 0 0 0|0 0 0 1|0 0 0 1|1 1 0 1|
Execute			Any,Convert					|0 0 0 0|0 0 0 1|0 0 0 1|1 1 1 0|
Execute			Any,Is_Scalar					|0 0 0 0|0 0 0 1|0 0 0 1|1 1 1 1|
Execute			Any,Is_Value					|0 0 0 0|0 0 0 1|0 0 1 0|0 0 0 0|
Execute			Any,Is_Default					|0 0 0 0|0 0 0 1|0 0 1 0|0 0 0 1|
Execute			Any,Make_Root_Type				|0 0 0 0|0 0 0 1|0 0 1 0|0 0 1 0|
Execute			Any,Make_Alligned				|0 0 0 0|0 0 0 1|0 0 1 0|0 0 1 1|
Execute			Any,Is_Constrained				|0 0 0 0|0 0 0 1|0 0 1 0|0 1 0 0|
Execute			Any,Set_Constraint				|0 0 0 0|0 0 0 1|0 0 1 0|0 1 0 1|
Execute			Any,Has_Default_Initialization			|0 0 0 0|0 0 0 1|0 0 1 0|0 1 1 0|
Execute			Any,Run_Initialization_Utility			|0 0 0 0|0 0 0 1|0 0 1 0|0 1 1 1|

#-----------------------
# ⟦36a4ea3d7⟧ @0x000d	type Years  is new Calendar.Year_Number (in spec)
# ⟦cb8e43375⟧ @0x0023   Pi : Float (in spec)
Execute			Any,Make_Visible				|0 0 0 0|0 0 0 1|0 0 1 0|1 0 0 1| #0e3e

Execute			Any,Change_Utility				|0 0 0 0|0 0 0 1|0 0 1 0|1 0 1 0|
Execute			Any,Spare14					|0 0 0 0|0 0 0 1|0 0 1 0|1 0 1 1|
Execute			Any,Size					|0 0 0 0|0 0 0 1|0 0 1 0|1 1 0 0|
Execute			Any,Address					|0 0 0 0|0 0 0 1|0 0 1 0|1 1 0 1|
Execute			Any,Not_Equal					|0 0 0 0|0 0 0 1|0 0 1 0|1 1 1 0|
Execute			Any,Equal					|0 0 0 0|0 0 0 1|0 0 1 0|1 1 1 1|

Execute			Family,Count					|0 0 0 0|0 0 0 1|0 0 1 1|0 0 1 0|
Execute			Family,Rendezvous				|0 0 0 0|0 0 0 1|0 0 1 1|0 0 1 1|
Execute			Entry,Count					|0 0 0 0|0 0 0 1|0 0 1 1|0 1 1 0|
Execute			Entry,Rendezvous				|0 0 0 0|0 0 0 1|0 0 1 1|0 1 1 1|
Execute			Select,Terminate_Guard_Write			|0 0 0 0|0 0 0 1|0 0 1 1|1 1 0 0|
Execute			Select,Timed_Duration_Write			|0 0 0 0|0 0 0 1|0 0 1 1|1 1 0 1|
Execute			Select,Timed_Guard_Write			|0 0 0 0|0 0 0 1|0 0 1 1|1 1 1 0|
Execute			Select,Rendezvous				|0 0 0 0|0 0 0 1|0 0 1 1|1 1 1 1|

Execute			Discrete,Divide_And_Scale			|0 0 0 0|0 0 0 1|0 1 0 0|0 0 0 0|
#-----------------------
# ⟦36a4ea3d7⟧ @0x044d
Execute			Discrete,Multiply_And_Scale			|0 0 0 0|0 0 0 1|0 1 0 0|0 0 0 1|
Execute			Heap_Access,Diana_Find_Permanent_Attribute	|0 0 0 0|0 0 0 1|0 1 0 0|0 0 1 0|
Execute			Heap_Access,Adaptive_Balanced_Tree_Lookup	|0 0 0 0|0 0 0 1|0 1 0 0|0 0 1 1|
Execute			Heap_Access,Get_Name				|0 0 0 0|0 0 0 1|0 1 0 0|0 1 0 0|
Execute			Heap_Access,Diana_Tree_Kind			|0 0 0 0|0 0 0 1|0 1 0 0|0 1 0 1|
Execute			Heap_Access,Hash				|0 0 0 0|0 0 0 1|0 1 0 0|0 1 1 0|
Execute			Heap_Access,Construct_Segment			|0 0 0 0|0 0 0 1|0 1 0 0|0 1 1 1|
Execute			Heap_Access,Get_Offset				|0 0 0 0|0 0 0 1|0 1 0 0|1 0 0 0|
Execute			Float,Less_Equal_Zero				|0 0 0 0|0 0 0 1|0 1 0 0|1 0 0 1|
#-----------------------
# ⟦cb8e43375⟧ @0x7c
Execute			Float,Greater_Equal_Zero			|0 0 0 0|0 0 0 1|0 1 0 0|1 0 1 0|
#-----------------------
# ⟦85b414c73⟧ @0x349
Execute			Float,Less_Zero					|0 0 0 0|0 0 0 1|0 1 0 0|1 0 1 1|
#-----------------------
# ⟦85b414c73⟧ @0x337
Execute			Float,Greater_Zero				|0 0 0 0|0 0 0 1|0 1 0 0|1 1 0 0|
Execute			Float,Not_Equal_Zero				|0 0 0 0|0 0 0 1|0 1 0 0|1 1 0 1|
Execute			Float,Equal_Zero				|0 0 0 0|0 0 0 1|0 1 0 0|1 1 1 0|
Execute			Float,Not_In_Range				|0 0 0 0|0 0 0 1|0 1 0 0|1 1 1 1|

Execute			Variant_Record,Make_Constrained			|0 0 0 0|0 0 0 1|0 1 0 1|1 0 1 1|
Execute			Variant_Record,Is_Constrained_Object		|0 0 0 0|0 0 0 1|0 1 0 1|1 1 0 0|
Execute			Variant_Record,Field_Type_Dynamic		|0 0 0 0|0 0 0 1|0 1 0 1|1 1 0 1|
Execute			Variant_Record,Field_Reference_Dynamic		|0 0 0 0|0 0 0 1|0 1 0 1|1 1 1 0|
Execute			Variant_Record,Field_Write_Dynamic		|0 0 0 0|0 0 0 1|0 1 0 1|1 1 1 1|
Execute			Variant_Record,Field_Read_Dynamic		|0 0 0 0|0 0 0 1|0 1 1 0|0 0 0 0|
Execute			Variant_Record,Check_In_Formal_Type		|0 0 0 0|0 0 0 1|0 1 1 0|0 0 0 1|
Execute			Variant_Record,Check_In_Type			|0 0 0 0|0 0 0 1|0 1 1 0|0 0 1 0|
Execute			Variant_Record,Not_In_Type			|0 0 0 0|0 0 0 1|0 1 1 0|0 0 1 1|
Execute			Variant_Record,In_Type				|0 0 0 0|0 0 0 1|0 1 1 0|0 1 0 0|
Execute			Variant_Record,Convert				|0 0 0 0|0 0 0 1|0 1 1 0|0 1 0 1|
Execute			Variant_Record,Component_Offset			|0 0 0 0|0 0 0 1|0 1 1 0|0 1 1 0|
Execute			Variant_Record,Structure_Query			|0 0 0 0|0 0 0 1|0 1 1 0|0 1 1 1|
Execute			Variant_Record,Reference_Makes_Copy		|0 0 0 0|0 0 0 1|0 1 1 0|1 0 0 0|
Execute			Variant_Record,Read_Discriminant_Constraint	|0 0 0 0|0 0 0 1|0 1 1 0|1 0 0 1|
# 016a undefined in disassembler
QQ_execute		Variant_Record,XXX				|0 0 0 0|0 0 0 1|0 1 1 0|1 0 1 0|
# End of BODY_0ca0
# Start of BODY_0f60
Execute			Variant_Record,Read_Variant			|0 0 0 0|0 0 0 1|0 1 1 0|1 0 1 1|
Execute			Variant_Record,Is_Constrained			|0 0 0 0|0 0 0 1|0 1 1 0|1 1 0 0|
Execute			Variant_Record,Structure_Write			|0 0 0 0|0 0 0 1|0 1 1 0|1 1 0 1|
Execute			Variant_Record,Not_Equal			|0 0 0 0|0 0 0 1|0 1 1 0|1 1 1 0|
Execute			Variant_Record,Equal				|0 0 0 0|0 0 0 1|0 1 1 0|1 1 1 1|

Execute			Record,Field_Type_Dynamic			|0 0 0 0|0 0 0 1|0 1 1 1|0 1 1 1|
Execute			Record,Field_Reference_Dynamic			|0 0 0 0|0 0 0 1|0 1 1 1|1 0 0 0|
Execute			Record,Field_Write_Dynamic			|0 0 0 0|0 0 0 1|0 1 1 1|1 0 0 1|
Execute			Record,Field_Read_Dynamic			|0 0 0 0|0 0 0 1|0 1 1 1|1 0 1 0|
Execute			Record,Convert					|0 0 0 0|0 0 0 1|0 1 1 1|1 0 1 1|
Execute			Record,Component_Offset				|0 0 0 0|0 0 0 1|0 1 1 1|1 1 0 0|
Execute			Record,Structure_Write				|0 0 0 0|0 0 0 1|0 1 1 1|1 1 0 1|
Execute			Record,Not_Equal				|0 0 0 0|0 0 0 1|0 1 1 1|1 1 1 0|
Execute			Record,Equal					|0 0 0 0|0 0 0 1|0 1 1 1|1 1 1 1|
Execute			Record,Structure_Write				|0 0 0 0|0 0 0 1|1 0 0 0|1 0 0 0| # 1145
Execute			Record,Field_Reference				|0 0 0 0|0 0 0 1|1 0 0 0|1 0 0 1|
Execute			Record,Field_Write				|0 0 0 0|0 0 0 1|1 0 0 0|1 0 1 0|
Execute			Record,Field_Read				|0 0 0 0|0 0 0 1|1 0 0 0|1 0 1 1|
Execute			Subarray,Structure_Write			|0 0 0 0|0 0 0 1|1 0 0 0|1 1 0 0|
Execute			Subarray,Field_Reference			|0 0 0 0|0 0 0 1|1 0 0 0|1 1 0 1|
Execute			Subarray,Field_Write				|0 0 0 0|0 0 0 1|1 0 0 0|1 1 1 0|
Execute			Subarray,Field_Read				|0 0 0 0|0 0 0 1|1 0 0 0|1 1 1 1|
Execute			Matrix,Check_In_Type				|0 0 0 0|0 0 0 1|1 0 0 1|1 0 1 1|
Execute			Matrix,Not_In_Type				|0 0 0 0|0 0 0 1|1 0 0 1|1 1 0 0|
Execute			Matrix,In_Type					|0 0 0 0|0 0 0 1|1 0 0 1|1 1 0 1|
Execute			Matrix,Convert_To_Formal			|0 0 0 0|0 0 0 1|1 0 0 1|1 1 1 0|
Execute			Matrix,Convert					|0 0 0 0|0 0 0 1|1 0 0 1|1 1 1 1|
Execute			Matrix,Subarray					|0 0 0 0|0 0 0 1|1 0 1 0|0 0 1 1|
Execute			Matrix,Structure_Write				|0 0 0 0|0 0 0 1|1 0 1 0|0 1 0 0|
Execute			Matrix,Field_Reference				|0 0 0 0|0 0 0 1|1 0 1 0|0 1 0 1|
Execute			Matrix,Field_Write				|0 0 0 0|0 0 0 1|1 0 1 0|0 1 1 0|
Execute			Matrix,Field_Read				|0 0 0 0|0 0 0 1|1 0 1 0|0 1 1 1|
Execute			Matrix,Element_Type				|0 0 0 0|0 0 0 1|1 0 1 0|1 0 0 0|
Execute			Matrix,Reverse_Bounds				|0 0 0 0|0 0 0 1|1 0 1 0|1 0 0 1|
Execute			Matrix,Bounds					|0 0 0 0|0 0 0 1|1 0 1 0|1 0 1 0|
Execute			Matrix,Length					|0 0 0 0|0 0 0 1|1 0 1 0|1 0 1 1|
Execute			Matrix,Last					|0 0 0 0|0 0 0 1|1 0 1 0|1 1 0 0|
Execute			Matrix,First					|0 0 0 0|0 0 0 1|1 0 1 0|1 1 0 1|
Execute			Matrix,Not_Equal				|0 0 0 0|0 0 0 1|1 0 1 0|1 1 1 0|
Execute			Matrix,Equal					|0 0 0 0|0 0 0 1|1 0 1 0|1 1 1 1|
Execute			Vector,Hash					|0 0 0 0|0 0 0 1|1 0 1 1|1 1 1 0|
Execute			Vector,Less_Equal				|0 0 0 0|0 0 0 1|1 0 1 1|1 1 1 1|
Execute			Vector,Greater_Equal				|0 0 0 0|0 0 0 1|1 1 0 0|0 0 0 0|
Execute			Vector,Less					|0 0 0 0|0 0 0 1|1 1 0 0|0 0 0 1|
Execute			Vector,Greater					|0 0 0 0|0 0 0 1|1 1 0 0|0 0 1 0|

# gc44,005f		VECTOR_CLASS,CHECK_IN_TYPE_OP			|0 0 0 0|0 0 0 1|1 1 0 0|0 0 1 1|
Execute			Vector,Check_In_Type				|0 0 0 0|0 0 0 1|1 1 0 0|0 0 1 1|
Execute			Vector,Not_In_Type				|0 0 0 0|0 0 0 1|1 1 0 0|0 1 0 0|
Execute			Vector,In_Type					|0 0 0 0|0 0 0 1|1 1 0 0|0 1 0 1|
Execute			Vector,Convert_To_Formal			|0 0 0 0|0 0 0 1|1 1 0 0|0 1 1 0|
Execute			Vector,Convert					|0 0 0 0|0 0 0 1|1 1 0 0|0 1 1 1|
Execute			Vector,Prepend					|0 0 0 0|0 0 0 1|1 1 0 0|1 0 1 0|
Execute			Vector,Append					|0 0 0 0|0 0 0 1|1 1 0 0|1 0 1 1|
#-----------------------
# gc44,007c		VECTOR_CLASS,CATENATE_OP			|0 0 0 0|0 0 0 1|1 1 0 0|1 1 0 0|
# gc45,008f		VECTOR_CLASS,CATENATE_OP			|0 0 0 0|0 0 0 1|1 1 0 0|1 1 0 0|
Execute			Vector,Catenate					|0 0 0 0|0 0 0 1|1 1 0 0|1 1 0 0|
Execute			Vector,Slice_Reference				|0 0 0 0|0 0 0 1|1 1 0 0|1 1 0 1|
Execute			Vector,Slice_Write				|0 0 0 0|0 0 0 1|1 1 0 0|1 1 1 0|
#-----------------------
# ⟦36a4ea3d7⟧, @0x06a0	return Name (Name'First .. Name'First + 2);
# Used to get a subarray
Execute			Vector,Slice_Read				|0 0 0 0|0 0 0 1|1 1 0 0|1 1 1 1|
Execute			Vector,Complement				|0 0 0 0|0 0 0 1|1 1 0 1|0 0 0 0|
Execute			Vector,Xor					|0 0 0 0|0 0 0 1|1 1 0 1|0 0 0 1|
Execute			Vector,Or					|0 0 0 0|0 0 0 1|1 1 0 1|0 0 1 0|
Execute			Vector,And					|0 0 0 0|0 0 0 1|1 1 0 1|0 0 1 1|
Execute			Vector,Structure_Write				|0 0 0 0|0 0 0 1|1 1 0 1|0 1 0 0|
#-----------------------
# ⟦3f2fe70c1⟧, @0x0219	Max   : Natural     renames Max_Width (Current_Column);
Execute			Vector,Field_Reference				|0 0 0 0|0 0 0 1|1 1 0 1|0 1 0 1|
#-----------------------
# gc44,006b		VECTOR_CLASS,FIELD_WRITE_OP			|0 0 0 0|0 0 0 1|1 1 0 1|0 1 1 0|
# gc45,00a6		VECTOR_CLASS,FIELD_WRITE_OP			|0 0 0 0|0 0 0 1|1 1 0 1|0 1 1 0|
Execute			Vector,Field_Write				|0 0 0 0|0 0 0 1|1 1 0 1|0 1 1 0|
Execute			Vector,Field_Read				|0 0 0 0|0 0 0 1|1 1 0 1|0 1 1 1|
Execute			Vector,Element_Type				|0 0 0 0|0 0 0 1|1 1 0 1|1 0 0 0|
Execute			Vector,Reverse_Bounds				|0 0 0 0|0 0 0 1|1 1 0 1|1 0 0 1|
Execute			Vector,Bounds					|0 0 0 0|0 0 0 1|1 1 0 1|1 0 1 0|
Execute			Vector,Length					|0 0 0 0|0 0 0 1|1 1 0 1|1 0 1 1|
Execute			Vector,Last					|0 0 0 0|0 0 0 1|1 1 0 1|1 1 0 0|
Execute			Vector,First					|0 0 0 0|0 0 0 1|1 1 0 1|1 1 0 1|
Execute			Vector,Not_Equal				|0 0 0 0|0 0 0 1|1 1 0 1|1 1 1 0|
Execute			Vector,Equal					|0 0 0 0|0 0 0 1|1 1 0 1|1 1 1 1|
# End of BODY_0f60

#-----------------------
# Start of BODY_11a0
Execute			Array,Check_In_Type				|0 0 0 0|0 0 0 1|1 1 1 0|1 0 1 1| #1494
Execute			Array,Not_In_Type				|0 0 0 0|0 0 0 1|1 1 1 0|1 1 0 0|
Execute			Array,In_Type					|0 0 0 0|0 0 0 1|1 1 1 0|1 1 0 1|
Execute			Array,Convert_To_Formal				|0 0 0 0|0 0 0 1|1 1 1 0|1 1 1 0|
Execute			Array,Convert					|0 0 0 0|0 0 0 1|1 1 1 0|1 1 1 1|

Execute			Array,Sybarray					|0 0 0 0|0 0 0 1|1 1 1 1|0 0 1 1| #1476
Execute			Array,Structure_Write				|0 0 0 0|0 0 0 1|1 1 1 1|0 1 0 0|
Execute			Array,Field_Reference				|0 0 0 0|0 0 0 1|1 1 1 1|0 1 0 1|
Execute			Array,Field_Write				|0 0 0 0|0 0 0 1|1 1 1 1|0 1 1 0|
Execute			Array,Field_Read				|0 0 0 0|0 0 0 1|1 1 1 1|0 1 1 1|
Execute			Array,Element_Type				|0 0 0 0|0 0 0 1|1 1 1 1|1 0 0 0| #1458
Execute			Array,Reverse_Bounds				|0 0 0 0|0 0 0 1|1 1 1 1|1 0 0 1|
Execute			Array,Bounds					|0 0 0 0|0 0 0 1|1 1 1 1|1 0 1 0|
Execute			Array,Length					|0 0 0 0|0 0 0 1|1 1 1 1|1 0 1 1|
Execute			Array,Last					|0 0 0 0|0 0 0 1|1 1 1 1|1 1 0 0|
Execute			Array,First					|0 0 0 0|0 0 0 1|1 1 1 1|1 1 0 1| #143a
Execute			Array,Not_Equal					|0 0 0 0|0 0 0 1|1 1 1 1|1 1 1 0|
Execute			Array,Equal					|0 0 0 0|0 0 0 1|1 1 1 1|1 1 1 1| #142e
Execute			Module,Check_Elaborated				|0 0 0 0|0 0 1 0|0 0 0 0|0 1 1 0| #1428
Execute			Task,Abort_Multiple				|0 0 0 0|0 0 1 0|0 0 0 0|1 0 0 0| #1422
Execute			Task,Abort					|0 0 0 0|0 0 1 0|0 0 0 0|1 0 0 1|
Execute			Module,Get_Name					|0 0 0 0|0 0 1 0|0 0 0 0|1 0 1 0|
Execute			Module,Is_Terminated				|0 0 0 0|0 0 1 0|0 0 0 0|1 0 1 1|
Execute			Module,Is_Callable				|0 0 0 0|0 0 1 0|0 0 0 0|1 1 0 0|
Execute			Module,Elaborate				|0 0 0 0|0 0 1 0|0 0 0 0|1 1 0 1|

#-----------------------
# gc43,0026		MODULE_CLASS,AUGMENT_IMPORTS_OP			|0 0 0 0|0 0 1 0|0 0 0 0|1 1 1 0|
EXECUTE			MODULE_CLASS,AUGMENT_IMPORTS_OP			|0 0 0 0|0 0 1 0|0 0 0 0|1 1 1 0|

#-----------------------
#EXECUTE		MODULE_CLASS,ACTIVATE_OP			|0 0 0 0|0 0 1 0|0 0 0 0|1 1 1 1|
Execute			Module,Activate					|0 0 0 0|0 0 1 0|0 0 0 0|1 1 1 1|
Execute			Heap_Access,Get_Segment				|0 0 0 0|0 0 1 0|0 0 0 1|0 0 0 0|
Execute			Heap_Access,Convert_Reference			|0 0 0 0|0 0 1 0|0 0 0 1|0 0 0 1|
Execute			Heap_Access,Address				|0 0 0 0|0 0 1 0|0 0 0 1|0 0 1 0|
Execute			Heap_Access,Check_In_Type			|0 0 0 0|0 0 1 0|0 0 0 1|0 0 1 1|
Execute			Heap_Access,Not_In_Type				|0 0 0 0|0 0 1 0|0 0 0 1|0 1 0 0|
Execute			Heap_Access,In_Type				|0 0 0 0|0 0 1 0|0 0 0 1|0 1 0 1|
Execute			Heap_Access,Convert				|0 0 0 0|0 0 1 0|0 0 0 1|0 1 1 0|
#-----------------------
# gc45,00a5		Heap_Access,All_Reference			|0 0 0 0|0 0 1 0|0 0 0 1|0 1 1 1|
Execute			Heap_Access,All_Reference			|0 0 0 0|0 0 1 0|0 0 0 1|0 1 1 1|

Execute			Heap_Access,All_Write				|0 0 0 0|0 0 1 0|0 0 0 1|1 0 0 0|
Execute			Heap_Access,All_Read				|0 0 0 0|0 0 1 0|0 0 0 1|1 0 0 1|
Execute			Heap_Access,Element_Type			|0 0 0 0|0 0 1 0|0 0 0 1|1 0 1 0|
Execute			Heap_Access,Set_Null				|0 0 0 0|0 0 1 0|0 0 0 1|1 0 1 1|
Execute			Heap_Access,Not_Null				|0 0 0 0|0 0 1 0|0 0 0 1|1 1 0 0|
Execute			Heap_Access,Is_Null				|0 0 0 0|0 0 1 0|0 0 0 1|1 1 0 1|
Execute			Heap_Access,Maximum				|0 0 0 0|0 0 1 0|0 0 0 1|1 1 1 0|
Execute			Heap_Access,Equal				|0 0 0 0|0 0 1 0|0 0 0 1|1 1 1 1|
Execute			Access,Deallocate				|0 0 0 0|0 0 1 0|0 0 1 0|0 0 0 0|
Execute			Access,Allow_Deallocate				|0 0 0 0|0 0 1 0|0 0 1 0|0 0 0 1|
Execute			Access,Convert_Reference			|0 0 0 0|0 0 1 0|0 0 1 0|0 0 1 0|
Execute			Access,Check_In_Type				|0 0 0 0|0 0 1 0|0 0 1 0|0 0 1 1|
Execute			Access,Not_In_Type				|0 0 0 0|0 0 1 0|0 0 1 0|0 1 0 0|
Execute			Access,In_Type					|0 0 0 0|0 0 1 0|0 0 1 0|0 1 0 1|
Execute			Access,Convert					|0 0 0 0|0 0 1 0|0 0 1 0|0 1 1 0|
#-----------------------
# ⟦93b91846e⟧ @0x0149	if Ptr.Kind = Number_Kind then
Execute			Access,All_Reference				|0 0 0 0|0 0 1 0|0 0 1 0|0 1 1 1|

Execute			Access,All_Write				|0 0 0 0|0 0 1 0|0 0 1 0|1 0 0 0|
Execute			Access,All_Read					|0 0 0 0|0 0 1 0|0 0 1 0|1 0 0 1|
Execute			Access,Element_Type				|0 0 0 0|0 0 1 0|0 0 1 0|1 0 1 0|
Execute			Access,Set_Null					|0 0 0 0|0 0 1 0|0 0 1 0|1 0 1 1|
Execute			Access,Not_Null					|0 0 0 0|0 0 1 0|0 0 1 0|1 1 0 0|
Execute			Access,Is_Null					|0 0 0 0|0 0 1 0|0 0 1 0|1 1 0 1|
Execute			Access,Not_Equal				|0 0 0 0|0 0 1 0|0 0 1 0|1 1 1 0|
Execute			Access,Equal					|0 0 0 0|0 0 1 0|0 0 1 0|1 1 1 1|

Execute			Float,In_Range					|0 0 0 0|0 0 1 0|0 0 1 1|0 0 0 0|
Execute			Float,Write_Unchecked				|0 0 0 0|0 0 1 0|0 0 1 1|0 0 0 1|
Execute			Float,Check_In_Type				|0 0 0 0|0 0 1 0|0 0 1 1|0 0 1 0|
Execute			Float,Not_In_Type				|0 0 0 0|0 0 1 0|0 0 1 1|0 0 1 1|
Execute			Float,In_Type					|0 0 0 0|0 0 1 0|0 0 1 1|0 1 0 0|
#-----------------------
# ⟦cb8e43375⟧ @0xc4
Execute			Round_To_Discrete				|0 0 0 0|0 0 1 0|0 0 1 1|0 1 0 1|
Execute			Float,Truncate_To_Discrete			|0 0 0 0|0 0 1 0|0 0 1 1|0 1 1 0|
#-----------------------
# ⟦cb8e43375⟧ @0xc7
# 85b414c73 0x055	Ymax : Float := Float (Integer (Pi * Two ** (It / 2)));
#QQu_CONVERT_TO_FLOAT	-						|0 0 0 0|0 0 1 0|0 0 1 1|0 1 1 1|

Execute			Float,Convert_From_Discrete			|0 0 0 0|0 0 1 0|0 0 1 1|0 1 1 1|
Execute			Float,Convert					|0 0 0 0|0 0 1 0|0 0 1 1|1 0 0 0|

#-----------------------
# ⟦85b414c73⟧ @0x463 looks like a classical polynomial expansion
# Assembler instruction is EXECUTE, Float_Class, op
FLOAT_**		-						|0 0 0 0|0 0 1 0|0 0 1 1|1 0 0 1|
FLOAT_DIVIDE		-						|0 0 0 0|0 0 1 0|0 0 1 1|1 0 1 0|
FLOAT_MULTIPLY		-						|0 0 0 0|0 0 1 0|0 0 1 1|1 0 1 1|
FLOAT_SUBTRACT		-						|0 0 0 0|0 0 1 0|0 0 1 1|1 1 0 0|
FLOAT_ADD		-						|0 0 0 0|0 0 1 0|0 0 1 1|1 1 0 1|
FLOAT_ABS		-						|0 0 0 0|0 0 1 0|0 0 1 1|1 1 1 0|
FLOAT_NEGATE		-						|0 0 0 0|0 0 1 0|0 0 1 1|1 1 1 1|
FLOAT_FIRST		-						|0 0 0 0|0 0 1 0|0 1 0 0|0 0 0 0|
FLOAT_LAST		-						|0 0 0 0|0 0 1 0|0 1 0 0|0 0 0 1|
FLOAT_LESS_EQUAL	-						|0 0 0 0|0 0 1 0|0 1 0 0|0 0 1 0|
FLOAT_GREATER_EQUAL	-						|0 0 0 0|0 0 1 0|0 1 0 0|0 0 1 1|
FLOAT_LESS		-						|0 0 0 0|0 0 1 0|0 1 0 0|0 1 0 0|
FLOAT_GREATER		-						|0 0 0 0|0 0 1 0|0 1 0 0|0 1 0 1|
FLOAT_NOT_EQUAL		-						|0 0 0 0|0 0 1 0|0 1 0 0|0 1 1 0|
FLOAT_EQUAL		-						|0 0 0 0|0 0 1 0|0 1 0 0|0 1 1 1|

Execute			Discrete,Check_In_Integer			|0 0 0 0|0 0 1 0|0 1 0 0|1 0 0 0|
Execute			Discrete,Case_In_Range				|0 0 0 0|0 0 1 0|0 1 0 0|1 0 0 1|
Execute			Discrete,Is_Unsigned				|0 0 0 0|0 0 1 0|0 1 0 0|1 0 1 0|
Execute			Discrete,Count_Trailing_Zeros			|0 0 0 0|0 0 1 0|0 1 0 0|1 0 1 1|
Execute			Discrete,Count_Leading_Zeros			|0 0 0 0|0 0 1 0|0 1 0 0|1 1 0 0|
Execute			Discrete,Count_Nonzero_Bits			|0 0 0 0|0 0 1 0|0 1 0 0|1 1 0 1|
Execute			Discrete,Extract_Bits				|0 0 0 0|0 0 1 0|0 1 0 0|1 1 1 0|
Execute			Discrete,Insert_Bits				|0 0 0 0|0 0 1 0|0 1 0 0|1 1 1 1|
Execute			Discrete,Rotate					|0 0 0 0|0 0 1 0|0 1 0 1|0 0 0 0|
Execute			Discrete,Logical_Shift				|0 0 0 0|0 0 1 0|0 1 0 1|0 0 0 1|
Execute			Discrete,Aritmetic_Shift			|0 0 0 0|0 0 1 0|0 1 0 1|0 0 1 0|
Execute			Discrete,Binary_Scale				|0 0 0 0|0 0 1 0|0 1 0 1|0 0 1 1|
Execute			Discrete,Partial_Minus				|0 0 0 0|0 0 1 0|0 1 0 1|0 1 0 0|
Execute			Discrete,Partial_Plus				|0 0 0 0|0 0 1 0|0 1 0 1|0 1 0 1|
Execute			Discrete,Instruction_Read			|0 0 0 0|0 0 1 0|0 1 0 1|0 1 1 0|
Execute			Discrete,Raise,>R				|0 0 0 0|0 0 1 0|0 1 0 1|0 1 1 1|
#-----------------------
# 196 times followed by 0x0000
# a dozen times right before TRAP entry /phk
#QQunknown_return_257	>R						|0 0 0 0|0 0 1 0|0 1 0 1|0 1 1 1|

Execute			Discrete,Test_And_Set_Next			|0 0 0 0|0 0 1 0|0 1 0 1|1 0 0 0|
Execute			Discrete,Test_And_Set_Previous			|0 0 0 0|0 0 1 0|0 1 0 1|1 0 0 1|
Execute			Discrete,Write_Unchecked			|0 0 0 0|0 0 1 0|0 1 0 1|1 0 1 0|
Execute			Discrete,Check_In_Type				|0 0 0 0|0 0 1 0|0 1 0 1|1 0 1 1|
# End of BODY_11a0

# Start of BODY_14a0
Execute			Discrete,Bounds_Check				|0 0 0 0|0 0 1 0|0 1 0 1|1 1 0 1|
Execute			Discrete,Convert				|0 0 0 0|0 0 1 0|0 1 0 1|1 1 1 0|
Execute			Discrete,Not_In_Type				|0 0 0 0|0 0 1 0|0 1 0 1|1 1 1 1|
Execute			Discrete,In_Type				|0 0 0 0|0 0 1 0|0 1 1 0|0 0 0 0|
Execute			Discrete,Not_In_Range				|0 0 0 0|0 0 1 0|0 1 1 0|0 0 0 1|
Execute			Discrete,In_Range				|0 0 0 0|0 0 1 0|0 1 1 0|0 0 1 0|
Execute			Discrete,Above_Bound				|0 0 0 0|0 0 1 0|0 1 1 0|0 0 1 1|
Execute			Discrete,Below_Bound				|0 0 0 0|0 0 1 0|0 1 1 0|0 1 0 0|
Execute			Discrete,Reverse_Bounds				|0 0 0 0|0 0 1 0|0 1 1 0|0 1 0 1|
Execute			Discrete,Bounds					|0 0 0 0|0 0 1 0|0 1 1 0|0 1 1 0|
Execute			Discrete,Predecessor				|0 0 0 0|0 0 1 0|0 1 1 0|0 1 1 1|
Execute			Discrete,Successor				|0 0 0 0|0 0 1 0|0 1 1 0|1 0 0 0|
#-----------------------
# /aa (3f2fe70c1 002b)		type Width_List is array (Column_Index) of Natural;
Execute			Discrete,Last					|0 0 0 0|0 0 1 0|0 1 1 0|1 0 0 1|
Execute			Discrete,First					|0 0 0 0|0 0 1 0|0 1 1 0|1 0 1 0|
Execute			Discrete,Maximum				|0 0 0 0|0 0 1 0|0 1 1 0|1 0 1 1|
Execute			Discrete.Minimum				|0 0 0 0|0 0 1 0|0 1 1 0|1 1 0 0|
#-----------------------
# /aa (3bf0c159 00d9)
Execute			Discrete,Exponentiate				|0 0 0 0|0 0 1 0|0 1 1 0|1 1 0 1|
Execute			Discrete,Modulo					|0 0 0 0|0 0 1 0|0 1 1 0|1 1 1 0|
Execute			Discrete,Remainder				|0 0 0 0|0 0 1 0|0 1 1 0|1 1 1 1|

Execute			Discrete,Make_Visible				|0 0 0 0|0 0 1 0|0 1 1 1|0 0 0 0|
#-----------------------
# ⟦cb8e43375⟧ @0x107 /phk
#QQu_int_divide		-						|0 0 0 0|0 0 1 0|0 1 1 1|0 0 0 0|

#-----------------------
# ⟦cb8e43375⟧ @0x103 /phk  not sure.
Execute			Discrete,Times					|0 0 0 0|0 0 1 0|0 1 1 1|0 0 0 1|

#-----------------------
# ⟦cb8e43375⟧ @0x109 /phk  not sure.
Execute			Discrete,Minus					|0 0 0 0|0 0 1 0|0 1 1 1|0 0 1 0|

#-----------------------
# ⟦cb8e43375⟧ @0x113 /phk  not sure.
Execute			Discrete,Plus					|0 0 0 0|0 0 1 0|0 1 1 1|0 0 1 1|
Execute			Discrete,Load_Top				|0 0 0 0|0 0 1 0|0 1 1 1|0 1 0 0|

#-----------------------
# ⟦85b414c73⟧ @0x171 /phk AND ?
# Epsilon : Float := Beta ** (-It / 2); (-It, It is integer)
Execute			Discrete,Unary_Minus				|0 0 0 0|0 0 1 0|0 1 1 1|0 1 0 1|
Execute			Discrete,Complement				|0 0 0 0|0 0 1 0|0 1 1 1|0 1 1 0|
Execute			Discrete,Xor					|0 0 0 0|0 0 1 0|0 1 1 1|0 1 1 1|
Execute			Discrete,Or					|0 0 0 0|0 0 1 0|0 1 1 1|1 0 0 0|
Execute			Discrete,And					|0 0 0 0|0 0 1 0|0 1 1 1|1 0 0 1|
Execute			Discrete,Less_Equal				|0 0 0 0|0 0 1 0|0 1 1 1|1 0 1 0|
Execute			Discrete,Greater_Equal				|0 0 0 0|0 0 1 0|0 1 1 1|1 0 1 1|
Execute			Discrete,Less					|0 0 0 0|0 0 1 0|0 1 1 1|1 1 0 0|
Execute			Discrete,Greater				|0 0 0 0|0 0 1 0|0 1 1 1|1 1 0 1|
Execute			Discrete,Not_Equal				|0 0 0 0|0 0 1 0|0 1 1 1|1 1 1 0|
Execute			Discrete,Equal					|0 0 0 0|0 0 1 0|0 1 1 1|1 1 1 1|

#-----------------------
# ⟦37717da67⟧ @0x5ce4 indicates this takes an extension /phk
Declare_Subprogram	subp,For_Accept					|0 0 0 0|0 0 1 0|1 0 0 1|1 0 0 1| subp				|

#-----------------------
# gc42,000b		FOR_OUTER_CALL,IS_VISIBLE,NOT_ELABORATED	|0 0 0 0|0 0 1 0|1 0 0 1|1 0 1 0|
Declare_Subprogram	subp,For_Outer_Call,Visible,Unelaborated	|0 0 0 0|0 0 1 0|1 0 0 1|1 0 1 0| subp				|

#-----------------------
# ⟦a88379b5f⟧ indicates this takes an extension # /phk
Declare_Subprogram	subp,For_Outer_Call,Unelaborated		|0 0 0 0|0 0 1 0|1 0 0 1|1 0 1 1| subp				|

#-----------------------
# gc87,000b		subp,FOR_OUTER_CALL,IS_VISIBLE			|0 0 0 0|0 0 1 0|1 0 0 1|1 1 0 0| subp				|
Declare_Subprogram	subp,For_Outer_Call,Visible			|0 0 0 0|0 0 1 0|1 0 0 1|1 1 0 0| subp				|

#-----------------------
# gc43,0038		FOR_OUTER_CALL					|0 0 0 0|0 0 1 0|1 0 0 1|1 1 0 1|
Declare_Subprogram	subp,For_Outer_Call				|0 0 0 0|0 0 1 0|1 0 0 1|1 1 0 1| subp				|

#-----------------------
# ⟦89b72b217⟧ @0x2abd indicates this takes an extension # /phk
Declare_Subprogram	subp,For_Call,Unelaborated			|0 0 0 0|0 0 1 0|1 0 0 1|1 1 1 0| subp				|

#-----------------------
# gc44,0077		FOR_CALL					|0 0 0 0|0 0 1 0|1 0 0 1|1 1 1 1|
Declare_Subprogram	subp,For_Call					|0 0 0 0|0 0 1 0|1 0 0 1|1 1 1 1| subp				|

#-----------------------
# gc43,001e		NULL_SUBPROGRAM					|0 0 0 0|0 0 1 0|1 0 1 0|0 0 0 0|
Declare_Subprogram	Null_Subprogram					|0 0 0 0|0 0 1 0|1 0 1 0|0 0 0 0|

Declare_Subprogram	For_Accept,With_Address				|0 0 0 0|0 0 1 0|1 0 1 0|0 0 1 0|
Declare_Subprogram	For_Outer_Call,Visible,With_Address		|0 0 0 0|0 0 1 0|1 0 1 0|0 1 0 0|
Declare_Subprogram	For_Outer_Call,With_Address			|0 0 0 0|0 0 1 0|1 0 1 0|0 1 0 1|
Declare_Subprogram	For_Call,Visible,Unelaborated,With_Address	|0 0 0 0|0 0 1 0|1 0 1 0|1 0 0 0|
Declare_Subprogram	For_Call,Unelaborated,With_Address		|0 0 0 0|0 0 1 0|1 0 1 0|1 0 0 1|
Declare_Subprogram	For_Call,Visible,With_Address			|0 0 0 0|0 0 1 0|1 0 1 0|1 0 1 0|
Declare_Subprogram	For_Call,With_Address				|0 0 0 0|0 0 1 0|1 0 1 0|1 0 1 1|

Declare_Variable	Float,Visible,With_Value,With_Constraint	|0 0 0 0|0 0 1 0|1 0 1 1|1 1 1 0|
Declare_Variable	Float,With_Value,With_Constraint		|0 0 0 0|0 0 1 0|1 0 1 1|1 1 1 1|

Declare_Variable	Any,Visible					|0 0 0 0|0 0 1 0|1 1 0 0|0 1 1 0|
Declare_Variable	Any						|0 0 0 0|0 0 1 0|1 1 0 0|0 1 1 1|
Declare_Variable	Family						|0 0 0 0|0 0 1 0|1 1 0 0|1 0 0 1|
Declare_Variable	Entry						|0 0 0 0|0 0 1 0|1 1 0 0|1 0 1 1|
Declare_Variable	Select,Choice_Open				|0 0 0 0|0 0 1 0|1 1 0 0|1 1 1 0|

#-----------------------
# See ⟦657d85b18⟧ @0x12d
# See ⟦eecee3432⟧ @0x2f2/phk
# See ⟦826a261d9⟧ @0x8a7/phk
#QQunknown_2cf		-						|0 0 0 0|0 0 1 0|1 1 0 0|1 1 1 1|
Declare_Variable	Select						|0 0 0 0|0 0 1 0|1 1 0 0|1 1 1 1|
# End of BODY_14a0
# Start of BODY_16a8
Declare_Variable	Variant_Record,Visible,With_Constraint		|0 0 0 0|0 0 1 0|1 1 1 1|1 0 1 1|
Declare_Variable	Variant_Record,With_Constraint			|0 0 0 0|0 0 1 0|1 1 1 1|1 1 0 0|
Declare_Variable	Variant_Record,Duplicate			|0 0 0 0|0 0 1 0|1 1 1 1|1 1 0 1|
Declare_Variable	Variant_Record,Visible				|0 0 0 0|0 0 1 0|1 1 1 1|1 1 1 0|
Declare_Variable	Variant_Record					|0 0 0 0|0 0 1 0|1 1 1 1|1 1 1 1|

Complete_Type		Variant_Record,By_Component_Completion		|0 0 0 0|0 0 1 1|0 0 0 0|0 0 1 1|
Complete_Type		Variant_Record,By_Completing_Constraint		|0 0 0 0|0 0 1 1|0 0 0 0|0 1 0 0|
Complete_Type		Variant_Record,By_Constraining_Incomplete	|0 0 0 0|0 0 1 1|0 0 0 0|0 1 0 1|
Complete_Type		Variant_Record,By_Renaming			|0 0 0 0|0 0 1 1|0 0 0 0|0 1 1 0|
Complete_Type		Variant_Record,By_Defining			|0 0 0 0|0 0 1 1|0 0 0 0|0 1 1 1|

Declare_Type		Variant_Record,Constrained_Incomplete		|0 0 0 0|0 0 1 1|0 0 0 1|0 0 0 1|
Declare_Type		Variant_Record,Constrained_Incomplete,Visible	|0 0 0 0|0 0 1 1|0 0 0 1|0 0 1 0|
Declare_Type		Variant_Record,Defined_Incomplete		|0 0 0 0|0 0 1 1|0 0 0 1|0 1 0 1|
Declare_Type		Variant_Record,Defined_Incomplete,Visible	|0 0 0 0|0 0 1 1|0 0 0 1|0 1 1 0|
Declare_Type		Variant_Record,Incomplete			|0 0 0 0|0 0 1 1|0 0 0 1|1 0 0 0|
Declare_Type		Variant_Record,Incomplete,Visible		|0 0 0 0|0 0 1 1|0 0 0 1|1 0 0 1|
Declare_Type		Variant_Record,Constrained			|0 0 0 0|0 0 1 1|0 0 0 1|1 0 1 1|
Declare_Type		Variant_Record,Constrained,Visible		|0 0 0 0|0 0 1 1|0 0 0 1|1 1 0 0|
Declare_Type		Variant_Record,Defined				|0 0 0 0|0 0 1 1|0 0 0 1|1 1 0 1|
Declare_Type		Variant_Record,Defined,Visible			|0 0 0 0|0 0 1 1|0 0 0 1|1 1 1 0|

Declare_Variable	Record,Duplicate				|0 0 0 0|0 0 1 1|0 0 1 0|0 0 0 0|
Declare_Variable	Record,Visible					|0 0 0 0|0 0 1 1|0 0 1 0|0 0 0 1|
Declare_Variable	Record						|0 0 0 0|0 0 1 1|0 0 1 0|0 0 1 0|

Complete_Type		Record,By_Component_Completion			|0 0 0 0|0 0 1 1|0 0 1 0|0 1 0 0|
Complete_Type		Record,By_Renaming				|0 0 0 0|0 0 1 1|0 0 1 0|0 1 0 1|
Complete_Type		Record,By_Defining				|0 0 0 0|0 0 1 1|0 0 1 0|0 1 1 0|

Declare_Type		Record,Defined_Incomplete			|0 0 0 0|0 0 1 1|0 0 1 0|0 1 1 1|
Declare_Type		Record,Defined_Incomplete,Visible		|0 0 0 0|0 0 1 1|0 0 1 0|1 0 0 0|
Declare_Type		Record,Incomplete				|0 0 0 0|0 0 1 1|0 0 1 0|1 0 1 0|
Declare_Type		Record,Incomplete,Visible			|0 0 0 0|0 0 1 1|0 0 1 0|1 0 1 1|
Declare_Type		Record,Defined					|0 0 0 0|0 0 1 1|0 0 1 0|1 1 0 1|
Declare_Type		Record,Defined,Visible				|0 0 0 0|0 0 1 1|0 0 1 0|1 1 1 0|

Declare_Variable	Array,Visible,With_Constraint			|0 0 0 0|0 0 1 1|0 0 1 1|0 0 1 1|
Declare_Variable	Array,With_Constraint				|0 0 0 0|0 0 1 1|0 0 1 1|0 1 0 0|
Declare_Variable	Array,Duplicate					|0 0 0 0|0 0 1 1|0 0 1 1|0 1 0 1|
Declare_Variable	Array,Visible					|0 0 0 0|0 0 1 1|0 0 1 1|0 1 1 0|
#-----------------------
# gc44,004b		ARRAY_CLASS					|0 0 0 0|0 0 1 1|0 0 1 1|0 1 1 1|
Declare_Variable	Array						|0 0 0 0|0 0 1 1|0 0 1 1|0 1 1 1|

Complete_Type		Array,By_Component_Completion			|0 0 0 0|0 0 1 1|0 1 0 0|0 0 0 0|
Complete_Type		Array,By_Constraining				|0 0 0 0|0 0 1 1|0 1 0 0|0 0 0 1|
Complete_Type		Array,By_Renaming				|0 0 0 0|0 0 1 1|0 1 0 0|0 0 1 0|
Complete_Type		Array,By_Defining				|0 0 0 0|0 0 1 1|0 1 0 0|0 0 1 1|

Declare_Type		Array,Constrained_Incomplete,Bounds_With_Object	|1 0 0 0|0 0 1 1|0 1 0 0|0 1 1 0|
Declare_Type		Array,Constrained_Incomplete,Visible,Bounds_With_Object	|0 0 0 0|0 0 1 1|0 1 0 0|0 1 1 1|
Declare_Type		Array,Defined_Incomplete,Bounds_With_Object	|0 0 0 0|0 0 1 1|0 1 0 0|1 0 0 0|
Declare_Type		Array,Defined_Incomplete,Visible,Bounds_With_Object	|0 0 0 0|0 0 1 1|0 1 0 0|1 0 0 1|
Declare_Type		Array,Incomplete,Bounds_With_Object		|0 0 0 0|0 0 1 1|0 1 0 0|1 0 1 1|
Declare_Type		Array,Incomplete,Visible,Bounds_With_Object	|0 0 0 0|0 0 1 1|0 1 0 0|1 1 0 0|
# End of BODY_16a8
# Start of BODY_1868
Declare_Type		Array,Constrained,Visible,Bounds_With_Object	|0 0 0 0|0 0 1 1|0 1 0 0|1 1 1 1|
Declare_Type		Array,Defined,Bounds_With_Object		|0 0 0 0|0 0 1 1|0 1 0 1|0 0 0 0|
Declare_Type		Array,Defined,Visible,Bounds_With_Object	|0 0 0 0|0 0 1 1|0 1 0 1|0 0 0 1|
Declare_Type		Array,Constrained_Incomplete			|0 0 0 0|0 0 1 1|0 1 0 1|0 0 1 1|
Declare_Type		Array,Constrained_Incomplete,Visible		|0 0 0 0|0 0 1 1|0 1 0 1|0 1 0 0|
Declare_Type		Array,Defined_Incomplete			|0 0 0 0|0 0 1 1|0 1 0 1|0 1 0 1|#1ab4
Declare_Type		Array,Defined_Incomplete,Visible		|0 0 0 0|0 0 1 1|0 1 0 1|0 1 1 0|#1aad
Declare_Type		Array,Incomplete				|0 0 0 0|0 0 1 1|0 1 0 1|1 0 0 0|
Declare_Type		Array,Incomplete,Visible			|0 0 0 0|0 0 1 1|0 1 0 1|1 0 0 1|
Declare_Type		Array,Constrained				|0 0 0 0|0 0 1 1|0 1 0 1|1 0 1 1|
Declare_Type		Array,Constrained,Visible			|0 0 0 0|0 0 1 1|0 1 0 1|1 1 0 0|

#-----------------------
# gc44,0049		ARRAY_CLASS,DEFINED				|0 0 0 0|0 0 1 1|0 1 0 1|1 1 0 1|
Declare_Type		Array,Defined					|0 0 0 0|0 0 1 1|0 1 0 1|1 1 0 1|
Declare_Type		Array,Defined,Visible				|0 0 0 0|0 0 1 1|0 1 0 1|1 1 1 0|

Declare_Variable	Task,In_Processor,As_Component			|0 0 0 0|0 0 1 1|0 1 1 0|1 0 1 0|
Declare_Variable	Task,As_Component				|0 0 0 0|0 0 1 1|0 1 1 0|1 0 1 1|
Declare_Variable	Task,Visible,On_Processor			|0 0 0 0|0 0 1 1|0 1 1 0|1 1 0 0|
Declare_Variable	Task,On_Processor				|0 0 0 0|0 0 1 1|0 1 1 0|1 1 0 1|
Declare_Variable	Task,Visible					|0 0 0 0|0 0 1 1|0 1 1 0|1 1 1 0|
Declare_Variable	Task						|0 0 0 0|0 0 1 1|0 1 1 0|1 1 1 1|

Complete_Type		Task,By_Renaming				|0 0 0 0|0 0 1 1|0 1 1 1|0 1 0 0|
Declare_Type		Task,Incomplete					|0 0 0 0|0 0 1 1|0 1 1 1|0 1 1 1|
Declare_Type		Task,Incomplete,Visible				|0 0 0 0|0 0 1 1|0 1 1 1|1 0 0 0|
Declare_Type		Task,Defined,Not_Elaborated			|0 0 0 0|0 0 1 1|0 1 1 1|1 0 1 0|
Declare_Type		Task,Defined,Visible,Not_Elaborated		|0 0 0 0|0 0 1 1|0 1 1 1|1 0 1 1|
Declare_Type		Task,Defined					|0 0 0 0|0 0 1 1|0 1 1 1|1 1 0 1|
Declare_Type		Task,Defined,Visible				|0 0 0 0|0 0 1 1|0 1 1 1|1 1 1 0|

Declare_Variable	Package,Visible,On_Processor			|0 0 0 0|0 0 1 1|1 0 0 0|0 1 0 0|
Declare_Variable	Package,On_Processor				|0 0 0 0|0 0 1 1|1 0 0 0|0 1 0 1|
Declare_Variable	Package,Visible					|0 0 0 0|0 0 1 1|1 0 0 0|0 1 1 0|
#-----------------------
# gc43,0020		PACKAGE_CLASS					|0 0 0 0|0 0 1 1|1 0 0 0|0 1 1 1|
Declare_Variable	Package						|0 0 0 0|0 0 1 1|1 0 0 0|0 1 1 1|

Declare_Type		Package,Defined,Not_Elaborated			|0 0 0 0|0 0 1 1|1 0 0 0|1 1 0 0|
Declare_Type		Package,Defined,Visible,Not_Elaborated		|0 0 0 0|0 0 1 1|1 0 0 0|1 1 0 1|

#-----------------------
# gc43,001f		PACKAGE_CLASS,DEFINED				|0 0 0 0|0 0 1 1|1 0 0 0|1 1 1 0|
Declare_Type		Package,Defined					|0 0 0 0|0 0 1 1|1 0 0 0|1 1 1 0|
Declare_Type		Package,Defined,Visible				|0 0 0 0|0 0 1 1|1 0 0 0|1 1 1 1|

Declare_Variable	Heap_Access,Visible,By_Allocation,With_Value	|0 0 0 0|0 0 1 1|1 0 0 1|0 1 0 1|

#-----------------------
# gc44,0074		Heap_Access,BY_ALLOCATION,WITH_VALUE		|0 0 0 0|0 0 1 1|1 0 0 1|0 1 1 0|
Declare_Variable	Heap_Access,By_Allocation,With_Value		|0 0 0 0|0 0 1 1|1 0 0 1|0 1 1 0|
Declare_Variable	Heap_Access,Visible,By_Allocation,With_Subtype	|0 0 0 0|0 0 1 1|1 0 0 1|0 1 1 1|
Declare_Variable	Heap_Access,By_Allocation,With_Subtype		|0 0 0 0|0 0 1 1|1 0 0 1|1 0 0 0|
Declare_Variable	Heap_Access,Visible,By_Allocation,With_Constraint	|0 0 0 0|0 0 1 1|1 0 0 1|1 0 0 1|
Declare_Variable	Heap_Access,By_Allocation,With_Constraint	|0 0 0 0|0 0 1 1|1 0 0 1|1 0 1 0|
Declare_Variable	Heap_Access,Visible,By_Allocation		|0 0 0 0|0 0 1 1|1 0 0 1|1 0 1 1|
Declare_Variable	Heap_Access,By_Allocation			|0 0 0 0|0 0 1 1|1 0 0 1|1 1 0 0|
Declare_Variable	Heap_Access,Duplicate				|0 0 0 0|0 0 1 1|1 0 0 1|1 1 0 1|
Declare_Variable	Heap_Access,Visible				|0 0 0 0|0 0 1 1|1 0 0 1|1 1 1 0|
Declare_Variable	Heap_Access					|0 0 0 0|0 0 1 1|1 0 0 1|1 1 1 1|

Complete_Type		Heap_Access,By_Component_Completion				|0 0 0 0|0 0 1 1|1 0 1 0|0 0 0 0|
Complete_Type		Heap_Access,By_Constraining					|0 0 0 0|0 0 1 1|1 0 1 0|0 0 0 1|
Complete_Type		Heap_Access,By_Renaming						|0 0 0 0|0 0 1 1|1 0 1 0|0 0 1 0|
Complete_Type		Heap_Access,By_Defining						|0 0 0 0|0 0 1 1|1 0 1 0|0 0 1 1|
Declare_Type		Heap_Access,Indirect_Literal,Values_Relative,With_Size		|0 0 0 0|0 0 1 1|1 0 1 0|0 1 0 0|
Declare_Type		Heap_Access,Indirect_Literal,Values_Relative			|0 0 0 0|0 0 1 1|1 0 1 0|0 1 0 1|
Declare_Type		Heap_Access,Indirect_Literal,Visible,Values_Relative		|0 0 0 0|0 0 1 1|1 0 1 0|0 1 1 0|
Declare_Type		Heap_Access,Indirect_Literal,Visible,Values_Relative,With_Size	|0 0 0 0|0 0 1 1|1 0 1 0|0 1 1 1|
Declare_Type		Heap_Access,Indirect_Literal					|0 0 0 0|0 0 1 1|1 0 1 0|1 0 0 0|
Declare_Type		Heap_Access,Indirect_Literal,Visible				|0 0 0 0|0 0 1 1|1 0 1 0|1 0 0 1|
Declare_Type		Heap_Access,Constrained						|0 0 0 0|0 0 1 1|1 0 1 0|1 0 1 1|
Declare_Type		Heap_Access,Constrained,Visible					|0 0 0 0|0 0 1 1|1 0 1 0|1 1 0 0|

#-----------------------
# gc44,0052		Heap_Access,DEFINED				|0 0 0 0|0 0 1 1|1 0 1 0|1 1 0 1|
Declare_Type		Heap_Access,Defined				|0 0 0 0|0 0 1 1|1 0 1 0|1 1 0 1|
Declare_Type		Heap_Access,Defined,Visible			|0 0 0 0|0 0 1 1|1 0 1 0|1 1 1 0|

Declare_Variable	Access,Visible,By_Allocation,With_Value		|0 0 0 0|0 0 1 1|1 0 1 1|0 1 0 1|
Declare_Variable	Access,By_Allocation,With_Value			|0 0 0 0|0 0 1 1|1 0 1 1|0 1 1 0|
Declare_Variable	Access,Visible,By_Allocation,With_Subtype	|0 0 0 0|0 0 1 1|1 0 1 1|0 1 1 1|
Declare_Variable	Access,By_Allocation,With_Subtype		|0 0 0 0|0 0 1 1|1 0 1 1|1 0 0 0|
Declare_Variable	Access,Visible,By_Allocation,With_Constraint	|0 0 0 0|0 0 1 1|1 0 1 1|1 0 0 1|
Declare_Variable	Access,By_Allocation,With_Constraint		|0 0 0 0|0 0 1 1|1 0 1 1|1 0 1 0|
Declare_Variable	Access,Visible,By_Allocation			|0 0 0 0|0 0 1 1|1 0 1 1|1 0 1 1|
Declare_Variable	Access,By_Allocation				|0 0 0 0|0 0 1 1|1 0 1 1|1 1 0 0|
Declare_Variable	Access,Duplicate				|0 0 0 0|0 0 1 1|1 0 1 1|1 1 0 1|
Declare_Variable	Access,Visible					|0 0 0 0|0 0 1 1|1 0 1 1|1 1 1 0|
Declare_Variable	Access						|0 0 0 0|0 0 1 1|1 0 1 1|1 1 1 1|

Complete_Type		Access,By_Component_Completion			|0 0 0 0|0 0 1 1|1 1 0 0|0 1 0 0|
Complete_Type		Access,By_Constraining				|0 0 0 0|0 0 1 1|1 1 0 0|0 1 0 1|
Complete_Type		Access,By_Renaming				|0 0 0 0|0 0 1 1|1 1 0 0|0 1 1 0|
# End of BODY_1868

# Start of BODY_1ae0
Declare_Type		Access,Incomplete,Accesses_Protected		|0 0 0 0|0 0 1 1|1 1 0 0|1 1 0 0|
Declare_Type		Access,Incomplete,Visible,Accesses_Protected	|0 0 0 0|0 0 1 1|1 1 0 0|1 1 0 1|
Declare_Type		Access,Incomplete				|0 0 0 0|0 0 1 1|1 1 0 0|1 1 1 0|
Declare_Type		Access,Incomplete,Visible			|0 0 0 0|0 0 1 1|1 1 0 0|1 1 1 1|

Declare_Type		Access,Constrained				|0 0 0 0|0 0 1 1|1 1 0 1|0 0 0 1|
Declare_Type		Access,Constrained,Visible			|0 0 0 0|0 0 1 1|1 1 0 1|0 0 1 0|
Declare_Type		Access,Defined,Accesses_Protected		|0 0 0 0|0 0 1 1|1 1 0 1|0 0 1 1|
Declare_Type		Access,Defined,Visible,Accesses_Protected	|0 0 0 0|0 0 1 1|1 1 0 1|0 1 0 0|
#-----------------------
# gc44,004f		Access,DEFINED					|0 0 0 0|0 0 1 1|1 1 0 1|0 1 0 1|
#			Type PA is Access A; (in procedure)
Declare_Type		Access,Defined					|0 0 0 0|0 0 1 1|1 1 0 1|0 1 0 1|
Declare_Type		Access,Defined,Visible				|0 0 0 0|0 0 1 1|1 1 0 1|0 1 1 0|

Declare_Variable	Float,Duplicate					|0 0 0 0|0 0 1 1|1 1 0 1|1 0 0 0|
Declare_Variable	Float,Visible					|0 0 0 0|0 0 1 1|1 1 0 1|1 0 0 1|
Declare_Variable	Float						|0 0 0 0|0 0 1 1|1 1 0 1|1 0 1 0|
Declare_Variable	Float,Visible,With_Value			|0 0 0 0|0 0 1 1|1 1 0 1|1 0 1 1|
Complete_Type		Float,By_Constraining				|0 0 0 0|0 0 1 1|1 1 0 1|1 1 0 0|
Complete_Type		Float,By_Renaming				|0 0 0 0|0 0 1 1|1 1 0 1|1 1 0 1|
Complete_Type		Float,By_Defining				|0 0 0 0|0 0 1 1|1 1 0 1|1 1 1 0|
Declare_Variable	Float,With_Value				|0 0 0 0|0 0 1 1|1 1 0 1|1 1 1 1|

Declare_Type		Float,Incomplete				|0 0 0 0|0 0 1 1|1 1 1 0|0 0 0 0|
Declare_Type		Float,Incomplete,Visible			|0 0 0 0|0 0 1 1|1 1 1 0|0 0 0 1|
Declare_Type		Float,Constrained				|0 0 0 0|0 0 1 1|1 1 1 0|0 0 1 1|
Declare_Type		Float,Constrained,Visible			|0 0 0 0|0 0 1 1|1 1 1 0|0 1 0 0|
Declare_Type		Float,Defined					|0 0 0 0|0 0 1 1|1 1 1 0|0 1 0 1|
Declare_Type		Float,Defined,Visible				|0 0 0 0|0 0 1 1|1 1 1 0|0 1 1 0|
Declare_Variable	Discrete,Visible,With_Value,With_Constraint	|0 0 0 0|0 0 1 1|1 1 1 0|1 0 0 0|
Declare_Variable	Discrete,Duplicate				|0 0 0 0|0 0 1 1|1 1 1 0|1 0 0 1|
Declare_Variable	Discrete,Visible				|0 0 0 0|0 0 1 1|1 1 1 0|1 0 1 0|
Declare_Variable	Discrete					|0 0 0 0|0 0 1 1|1 1 1 0|1 0 1 1|

#-----------------------
# feh269,1d		DISCRETE,WITH_VALUE,WITH_CONSTRAINT		|0 0 0 0|0 0 1 1|1 1 1 0|1 1 0 0|
# ⟦36a4ea3d7⟧ @0x0717	Month : Integer := Months'Pos (Date.Month) + 1;
Declare_Variable	Discrete,With_Value,With_Constraint		|0 0 0 0|0 0 1 1|1 1 1 0|1 1 0 0|
Complete_Type		Discrete,By_Constraining			|0 0 0 0|0 0 1 1|1 1 1 0|1 1 0 1|
Complete_Type		Discrete,By_Renaming				|0 0 0 0|0 0 1 1|1 1 1 0|1 1 1 0|
Complete_Type		Discrete,By_Defining				|0 0 0 0|0 0 1 1|1 1 1 0|1 1 1 1|

Declare_Variable	Discrete,Visible,With_Value			|0 0 0 0|0 0 1 1|1 1 1 1|0 0 0 0|
Declare_Variable	Discrete,With_Value				|0 0 0 0|0 0 1 1|1 1 1 1|0 0 0 1|
Declare_Variable	Discrete,Incomplete,Unsigned			|0 0 0 0|0 0 1 1|1 1 1 1|0 0 1 0|
Declare_Variable	Discrete,Incomplete,Visible,Unsigned		|0 0 0 0|0 0 1 1|1 1 1 1|0 0 1 1|
Declare_Variable	Discrete,Incomplete				|0 0 0 0|0 0 1 1|1 1 1 1|0 1 0 1|
Declare_Variable	Discrete,Incomplete,Visible			|0 0 0 0|0 0 1 1|1 1 1 1|0 1 1 0|
Declare_Type		Discrete,Constrained				|0 0 0 0|0 0 1 1|1 1 1 1|1 0 0 0|
Declare_Type		Discrete,Constrained,Visible			|0 0 0 0|0 0 1 1|1 1 1 1|1 0 0 1|
Declare_Type		Discrete,Defined,With_Size			|0 0 0 0|0 0 1 1|1 1 1 1|1 0 1 0|
Declare_Type		Discrete,Defined,Visible,With_Size		|0 0 0 0|0 0 1 1|1 1 1 1|1 0 1 1|
#-----------------------
# (93b91846e, 0025)/aa		type Kind_Value is (Day, Hour, Minute, Second, Millisecond, Number); (in procedure)
Declare_Type		Discrete,Defined				|0 0 0 0|0 0 1 1|1 1 1 1|1 1 0 1|
# Not defined in disassembler (03fe)
QQuDECLARE_TYPE		DISCRETE_CLASS,DEFINED,ENUM			|0 0 0 0|0 0 1 1|1 1 1 1|1 1 1 0|

# End of BODY_1ae0
# Start of BODY_0588

Execute_Immediate	Set_Value_Visible_Unchecked,x			|0 0 0 0|0 1 0 0|       x       |
Execute_Immediate	Set_Value_Visible,x				|0 0 0 0|0 1 0 1|       x       |

#-----------------------
# g43,0037		SET_VALUE_UNCHECKED_OP,33			|0 0 0 0|0 1 1 0|0 0 1 0|0 0 0 1|
Execute_Immediate	Set_Value_Unchecked,x				|0 0 0 0|0 1 1 0|       x	|
Execute_Immediate	Set_Value,x					|0 0 0 0|0 1 1 1|       x       |
#-----------------------
# ⟦28af5d09d⟧ @0xd2
# ⟦36a4ea3d7⟧ @0x0c9e/aa	May be raise Constraint_Error
Execute_Immediate	Raise,s8,>R					|0 0 0 0|1 0 0 0| 	s8	|

#-----------------------
# ⟦cb8e43375⟧ @0x108
# ⟦85b414c73⟧ @0x0170 /phk
# NB: microcode splits this in four
# Execute_Immediate	Binary_Scale	0900
# Execute_Immediate	Logical_Shift	0940
# Execute_Immediate	Logical_Shift	0980
# Execute_Immedate	Binary_Scale	09c0
BINARY_SCALE_OP		s8						|0 0 0 0|1 0 0 1|	s8	|

#-----------------------
# /aa (3bf0c159 00da )
# NB: microcode splits this in two
Execute_Immediate	Plus,s8						|0 0 0 0|1 0 1 0|	s8	|

#-----------------------
# See ⟦a53169a08⟧ @0x64, some kind of comparison/test
# Almost always followed by 0x70xx conditional jump /phk
# 93b91846e @0x0168	case Colons_Observed is 	when 2 =>
Execute_Immediate	Compare,s8					|0 0 0 0|1 0 1 1|	s8	|

#-----------------------
# See ⟦657fb377c⟧ @0x1d7c, some kind of comparison/test
# Almost always followed by 0x70xx or 0x68xx conditional jump /phk
# Maybe Greater_Equal_Op  ⟦36a4ea3d7⟧ @0x0609   if Months'Pos (T.Month) >= 3 then
Execute_Immediate	Greater_Equal,s8				|0 0 0 0|1 1 0 0| 	s8	|

#-----------------------
# ⟦cb8e43375⟧ @0x144
Execute_Immediate	Less,s8						|0 0 0 0|1 1 0 1|	s8	|

#-----------------------
# ⟦36a4ea3d7⟧ @0x0344	if Date.Hour /= 12 then
Execute_Immediate	Not_Equal,s8					|0 0 0 0|1 1 1 0|       s8      |

#-----------------------
# ⟦36a4ea3d7⟧ @0x06bc	if Time_Style = Ada then
Execute_Immediate	Equal,s8					|0 0 0 0|1 1 1 1|       s8      |

Execute			Select,Guard_Write				|0 0 0 1|0 0 0 0|       s8      |
Execute			Select,Member_Write				|0 0 0 1|0 0 0 1|       s8      |
Execute			Task,Family_Timed				|0 0 0 1|0 0 1 0|       s8      |
Execute			Task,Family_Cond				|0 0 0 1|0 0 1 1|       s8      |
Execute			Task,Family_Call				|0 0 0 1|0 1 0 0|       s8      |
Execute			Task,Timed_Call					|0 0 0 1|0 1 0 1|       s8      |
Execute			Task,Conditional_Call				|0 0 0 1|0 1 1 0|       s8      |
Execute			Task,Entry_Call					|0 0 0 1|0 1 1 1|       s8      |


#-----------------------
# g43,002c		PACKAGE_CLASS,FIELD_EXECUTE_OP,13		|0 0 0 1|1 0 0 0|0 0 0 0|1 1 0 1|
# g44,0071		PACKAGE_CLASS,FIELD_EXECUTE_OP,17		|0 0 0 1|1 0 0 0|0 0 0 1|0 0 0 1|
# g45,008e		PACKAGE_CLASS,FIELD_EXECUTE_OP,24		|0 0 0 1|1 0 0 0|0 0 0 1|1 0 0 0|
# g45,0091		PACKAGE_CLASS,FIELD_EXECUTE_OP,100		|0 0 0 1|1 0 0 0|0 1 1 0|0 1 0 0|
Execute			Package,Field_Execute,x				|0 0 0 1|1 0 0 0|0|       x	|

#-----------------------
# g88,0032		PACKAGE_CLASS,FIELD_REFERENCE_OP,13		|0 0 0 1|1 0 0 1|0 0 0 0|1 1 0 1|
Execute			Packate,Field_Reference,x		|0 0 0 1|1 0 0 1|0|       x     |


#-----------------------
# ⟦cb8e43375⟧ @0x10b
Execute			Package,Field_Write,x				|0 0 0 1|1 0 1 0|0|       x	|

#-----------------------
# ⟦cb8e43375⟧ @0xfe
Execute			Package,Field_Read				|0 0 0 1|1 0 1 1|0|       x	|

#-----------------------
# ⟦36a4ea3d7⟧ @0x068e
Execute_Immediate	Run_Utility,x					|0 0 0 1|1 1 0 0|         x     |

#-----------------------
# g42,000e		REFERENCE_LEX_1_OP,13				|0 0 0 1|1 1 0 1|0 0 0 0|1 1 0 1|
Execute_Immeddate	Reference_Lex_1,x				|0 0 0 1|1 1 0 1|0|       x	|

Execute			Variant_Record,Set_Variant			|0 0 1 0|0 0 0 0|0|       x     |
Execute			Variant_Record,Set_Bounds			|0 0 1 0|0 0 0 1|0|       x     |
Execute			Variant_Record,Field_Constrain			|0 0 1 0|0 0 1 0|0|       x     |
Execute			Variant_Record,Field_Reference,Fixed,Direct,x	|0 0 1 0|0 1 0 0|0|       x     |
#-----------------------
# ⟦3f2fe70c1⟧ @0x0259	not sure /aa	return P.Subitem;	P.Subitem is a string
Execute			Variant_Record,Field_Reference,Indirect,x	|0 0 1 0|0 1 0 1|0|       x     |
Execute			Variant_Record,Field_Reference,Variant,Direct,x	|0 0 1 0|0 1 1 0|0|       x     |
Execute			Variant_Record,Field_Reference,Variant,Indirect,x	|0 0 1 0|0 1 1 1|0|       x     |
Execute			Variant_Record,Field_Write,Fixed,Direct,x	|0 0 1 0|1 0 0 0|0|       x     |
Execute			Variant_Record,Field_Write,Fixed,Indirect,x	|0 0 1 0|1 0 0 1|0|       x     |
Execute			Variant_Record,Field_Write,Variant,Direct,x	|0 0 1 0|1 0 1 0|0|       x     |
Execute			Varaint_Record,Field_Write,Variant,Indirect,x	|0 0 1 0|1 0 1 1|0|       x     |
#-----------------------
# ⟦3f2fe70c1⟧ @0x0245	not sure/aa		if P.Next = null then	P.Next = Access type
Execute			Variant_Record,Field_Read,Fixed,Direct,x	|0 0 1 0|1 1 0 0|0|       x     |
Execute			Variant_Record,Field_Append,Fixed,Indirect,x	|0 0 1 0|1 1 0 1|0|       x     |
Execute			Variant_Record,Field_Read,Variant,Direct,x	|0 0 1 0|1 1 1 0|0|       x     |
Execute			Variant_Record,Field_Append,Variant,Indirect,x	|0 0 1 0|1 1 1 1|0|       x     |

Execute			Record,Field_Type				|0 0 1 1|0 0 0 0|0|       x     |

#-----------------------
# ⟦3f2fe70c1⟧ @0x0275	Read record, not sure /aa
Execute			Record,Field_Reference,x			|0 0 1 1|0 1 0 0|         x     |
Loop_Decreasing		pcrelneg,>JC					|0 0 1 1|0 1 1| pcrelneg        |
#-----------------------
# ⟦36a4ea3d7⟧ @0x00fa-010f, write record field values
Execute			Record,Field_Write,x				|0 0 1 1|1 0 0 0|0|       x     |

#-----------------------
# ⟦36a4ea3d7⟧ @0x0608, read record field values in function Day_Of_Week
Execute			Record,Field_Read,x				|0 0 1 1|1 1 0 0|0|       x     |

#-----------------------
# g44,005d		-5						|0 0 1 1|1 1 1 1|1 1 1 1|1 0 1 1|
Loop_Increasing		pcrelneg,>JC					|0 0 1 1|1 1 1| pcrelneg	|

#-----------------------
# phk
End_Rendezvous		>R,x						|0 1 0 0|0 0 0 1|0 0 0| x	|

#-----------------------
# phk
Exit_Subprogram		From_Utility,With_Result,>R,x			|0 1 0 0|0 0 1 0|0 0 0| x	|

#-----------------------
# phk
Exit_Subprogram		From_Utility,>R,x				|0 1 0 0|0 0 1 1|0 0 0| x	|

#-----------------------
# phk
Exit_Subprogram		With_Value,>R,x					|0 1 0 0|0 1 0 0|0 0 0| x	|

#-----------------------
# g43,002d		1						|0 1 0 0|0 1 0 1|0 0 0 0|0 0 0 1|
# g44,0080		2						|0 1 0 0|0 1 0 1|0 0 0 0|0 0 1 0|
# feh269,1e		1						|0 1 0 0|0 1 0 1|0 0 0 0|0 0 0 1|
Exit_Suprogram		>R						|0 1 0 0|0 1 0 1|0 0|   x	|

#-----------------------
# ⟦fad6fc6ba⟧ limits the argument to 8 bits
# /phk
Jump_Case		case_max					|0 1 0 0|0 1 1|0| case_max	|

#-----------------------
# g43,001b		0						|0 1 0 0|1 0 0 0|0 0 0 0 0 0 0 0|
# g43,0024		3						|0 1 0 0|1 0 0 0|0 0 0 0 0 0 1 1|
# g44,0045		10						|0 1 0 0|1 0 0 0|0 0 0 0 1 0 1 1|
# g44,004e		24						|0 1 0 0|1 0 0 0|0 0 0 1 1 0 0 0|
Short_Literal		slit						|0 1 0 0|1| slit		|

# Any type
Indirect_Literal	Any,pcrel,literal				|0 1 0 1|0| pcrel               |

#-----------------------
# ⟦85b414c73⟧ (sin/cos/tan) @0x42b...
# Indirect_Literal	Float
PUSH_DOUBLE		pcrel,dbl					|0 1 0 1|1| pcrel		|

#-----------------------
# g88,0026		Discrete_Class,57				|0 1 1 0|0 0 0 0|0 0 1 1 1 0 0 1|
# g88,0027		Discrete_Class,52				|0 1 1 0|0 0 0 0|0 0 1 1 0 1 0 0|
# g88,002d		Discrete_Class,42				|0 1 1 0|0 0 0 0|0 0 1 0 1 0 1 0|
# feh269,1b		Discrete, #0020					|0 1 1 0|0 0 0 0|0 0 0 0 0 1 0 0|
INDIRECT_LITERAL	pcrel,literal					|0 1 1 0|0| pcrel		|

#-----------------------
# jump_if_not		pcrel,>JC
Jump_Zero		pcrel,>JC					|0 1 1 0|1| pcrel		|

#-----------------------
# ⟦85b414c73⟧ @0x326
# (93b91846e, 0087	function Is_Digit, case Char is when '0'..'9' => return True;
# jump_if_true
Jump_Nonzero		pcrel,>JC					|0 1 1 1|0| pcrel		|

#-----------------------
# XXX: Not obvious if "1" and "2" is count of extension words or if and why those words are jumped over
# g88,001a		1						|0 1 1 1|1 0 0 0|0 0 0 0|0 0 0 1|
# g88,0047		2						|0 1 1 1|1 0 0 0|0 0 0 0|0 0 1 0|
Jump			pcrel,>J					|0 1 1 1|1| pcrel		|

#-----------------------
# g44,007d		1,15						|1 0 0 0|0 0 1|0 0 0 0 0 1 1 1 1|
# g44,007f		2,9						|1 0 0 0|0 1 0|0 0 0 0 0 1 0 0 1|
# feh269,22		0						|1 0 0 0|0 0 0|0 0 0 0 0 0 0 0 0|
Call			llvl,ldelta					|1 0 0| llvl  | ldelta		|

#-----------------------
# g45,009d		2,2						|1 0 1 0|0 1 0|0 0 0 0 0 0 0 1 0|
# g45,009f		3,2						|1 0 1 0|0 1 1|0 0 0 0 0 0 0 1 0|
# g45,00a1		1,14						|1 0 1 0|0 0 1|0 0 0 0 0 1 1 1 0|
Sture_Unchecked		llvl,ldelta					|1 0 1| llvl  | ldelta		|

#-----------------------
# g44,0062		2,7						|1 1 0 0|0 1 0 0|0 0 0 0|0 1 1 1|
# g44,0075		2,8						|1 1 0 0|0 1 0 0|0 0 0 0|1 0 0 0|
Store			llvl,ldelta					|1 1 0| llvl  | ldelta		|

#-----------------------
# g43,0021		0,1						|1 1 1 0|0 0 0|0 0 0 0 0 0 0 0 1|
# g43,0022		0,2						|1 1 1 0|0 0 0|0 0 0 0 0 0 0 1 0|
# g43,0023		0,3						|1 1 1 0|0 0 0|0 0 0 0 0 0 0 1 1|
# g43,0025		2,2						|1 1 1 0|0 1 0|0 0 0 0 0 0 0 1 0|
# g44,004c		2,3						|1 1 1 0|0 1 0|0 0 0 0 0 0 0 1 1|
# g44,0079		2,-1						|1 1 1 0|0 1 0|1 1 1 1 1 1 1 1 1|
# g45,00a0		3,-1						|1 1 1 0|0 1 1|1 1 1 1 1 1 1 1 1|
Load			llvl,ldelta					|1 1 1| llvl  | ldelta		|
"""

class ucode_ins(assy.Instree_ins):
    ''' '''
    def assy_x(self):
        v = self['x']
        return "0x%x" % v

    def assy_i(self):
        print("microcode does not like", self)
        raise assy.Invalid("Invalid Instruction")

class r1000_ins(assy.Instree_ins):
    ''' '''

    def assy_case_max(self):
        i = self['case_max']
        self += code.Jump(cond="default", to=self.hi)
        self.lang.m.set_line_comment(self.hi, "case default")
        for j in range(i):
            self += code.Jump(cond="#0x%x" % j, to=self.hi + 1 + j)
            self.lang.m.set_line_comment(self.hi + 1 + j, "case 0x%x" % j)
        return "0x%x" % i

    def assy_skip(self):
        self += code.Jump(cond="?", to=self.hi)
        self += code.Jump(cond="!?x", to=self.hi + 1)

    def assy_subp(self):
        self.dstadr = self['subp']
        self.lang.subprogram(self.dstadr)
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_pse(self):
        self.dstadr = self['pse']
        y = self.lang.strtab(self.dstadr)
        self.lang.m.set_line_comment(self.lo, y.txt)
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_abs(self):
        self.dstadr = self['abs']
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_maybe_subprog(self):
        if self.lang.m[self.lo + 2] == 0x2a0 and (self.dstadr & 3) == 3:
            self.lang.subprogram(self.dstadr)

    def assy_pcrelneg(self):
        v = self['pcrelneg']
        self.dstadr = self.hi + v - 0x200
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_pcrel(self):
        v = self['pcrel']
        if v & 0x400:
            self.dstadr = self.hi + v - 0x800
        else:
            self.dstadr = self.hi + v
        return assy.Arg_dst(self.lang.m, self.dstadr)

    def assy_x(self):
        v = self['x']
        return "0x%x" % v

    def assy_s8(self):
        v = self['s8']
        if v & 0x80:
            return "-0x%x" % (0x100 - v)
        return "0x%x" % v

    def assy_literal(self):
        y = self.lang.literal(self.dstadr)
        return y.repr

    def assy_eon(self):
        # EncachedObjectNumber: 0..31
        v = self['eon']
        return [
            "Standard_Cache", "Boolean_Cache", "Integer_Cache", "Natural_Cache",
            "Positive_Cache", "Long_Integer_Cache", "Float_Cache", "Duration_Cache",
            "Character_Cache", "String_Cache", "Null_String_Cache", "Diana_Cache",
            "Diana_Tree_Cache", "Diana_Symbol_Rep_Cache", "Diana_Seq_Type_Cache", "Diana_Sequence_Cache",
            "Segment_Cache", "Diana_Temp_Seq", "Diana_Attr_List", "Diana_Tree_Node",
            "Diana_Seq_Type_Node", "Unused21", "Unused22", "Unused23",
            "Unused24", "Unused25", "Unused26", "Unused27",
            "Unused28", "Unused29", "Unused30", "Unused31",
        ][v]

    def assy_slit(self):
        if self.chk2cf():
            return
        # Short_Literal_Value [-2**10..2**10-1]
        v = self['slit']
        if v & (1<<10):
            v = v - (1<<11)
            return "-0x%x" % (-v)
        return "0x%x" % v

    def assy_llvl(self):
        # Lexical_Level [0..15]
        return "0x%x" % self['llvl']

    def assy_ldelta(self):
        # Lexical_Delta [-256..511]
        v = self['ldelta']
        if v & 0x100:
            return "-0x%x" % (0x200 - v)
        return "0x%x" % v

    def assy_mark(self):
        self.lang.m.set_line_comment(self.dstadr, "See at 0x%04x" % self.lo)

    def assy_dbl(self):
        y = data.Data(self.lang.m, self.dstadr, self.dstadr + 4)
        a = self.lang.m[self.dstadr] << 48
        a |= self.lang.m[self.dstadr + 1] << 32
        a |= self.lang.m[self.dstadr + 2] << 16
        a |= self.lang.m[self.dstadr + 3]
        b = a.to_bytes(8, 'big')
        c = struct.unpack(">d", b)
        y.rendered = ".DBL\t" + str(c[0])
        return str(c[0])

    def chk2cf(self):
        a = self.lo
        l = []
        while (self.lang.m[a] & 0xf800) == 0x4800:
            l.append(self.lang.m[a] & 0x7ff)
            a += 1
        if self.lang.m[a] != 0x02cf:
            return False
        if len(l) != 4 + 2 * l[-1]:
            return False
        self.mne = "Declare_Variable	Select"
        self.hi = a + 1
        self.oper.append(assy.Arg_verbatim("0x%03x, 0x%03x" % (l[-2], l[-1])))
        l.pop(-1)
        l.pop(-1)
        while l:
            self.oper.append(assy.Arg_verbatim("\n\t\t[0x%03x]: 0x%03x = 0x%04x" % (l[-2], l[-1], l[-1] << 3)))
            if l[-1]:
                self.lang.subprogram((l[-1] << 3) | 3)
                self.lang.m.set_block_comment(l[-1] << 3, "See instruction 0x02cf at 0x%x, index=0x%x" % (self.lo, l[-2]))
            l.pop(-1)
            l.pop(-1)
        return True

class r1000(assy.Instree_disass):
    def __init__(self, abits=16):
        super().__init__(
            "Rational 1000 Ada Processor",
            mem_word=16,
            ins_word=16,
            abits=abits,
            endian=">",
        )
        self.add_ins(ucode_desc, ucode_ins)
        self.add_ins(r1000_desc, r1000_ins)
        self.verbatim += (
            'ARRAY_CLASS',
            'AUGMENT_IMPORTS_OP',
            'BY_ALLOCATION',
            'CATENATE_OP',
            'CHECK_IN_TYPE_OP',
            'DEFINED',
            'FIELD_EXECUTE_OP',
            'FIELD_READ_OP',
            'FIELD_WRITE_OP',
            'FOR_CALL',
            'FOR_OUTER_CALL',
            'INCOMPLETE',
            'IS_VISIBLE',
            'NOT_ELABORATED',
            'NULL_SUBPROGRAM',
            'PACKAGE_CLASS',
            'REFERENCE_LEX_1_OP',
            'SET_VALUE_UNCHECKED_OP',
            'STRUCTURE_READ_OP',
            'STRUCTURE_WRITE_OP',
            'SUBARRAY_OP',
            'WITH_VALUE',
            'UNCONSTRAINED',
            'MODULE_CLASS',
            'WITH_CONSTRAINT',
            'ACTIVATE_OP',
            'DISCRETE',
            'RAISE_OP',
            'RERAISE_OP',
            'EXCEPTION_CLASS',
            'DISCRETE_CLASS',
            'RECORD_CLASS',
            'VECTOR_CLASS',
            'SIGNAL_ACTIVATED',
            'SIGNAL_COMPLETION',
            'ACCEPT_ACTIVATION',
            'ELABORATE_SUBPROGRAM',
            'BREAK_UNCONDITIONAL',
            'FIELD_REFERENCE_OP',
            'PUSH_STRING',
            'PUSH_STRING_INDEXED',
            'BREAK_OPTIONAL',
            'ENUM',
            'IN_RANGE',
            'BELOW_BOUND',
            'VARIANT_RECORD_CLASS',
            'EXPONENTIATE',
            'MINUS',
            'FLOAT_CLASS',
            'XXX',
            'Value_05',
            'Value_15',
            'Value_25',
            'Abort',
            'Constrained_Incomplete',
            'Make_Constrained',
            'Check_In_Integer',
            'Count_Leading_Zeros',
            'Predecessor',
            'Minus',
            'Null_Subprogram',
            'With_Address',
            'Entry',
            'Action',
            'Value_04',
            'Value_14',
            'Value_24',
            'Convert_Unchecked',
            'Adaptive_Balanced_Tree_Lookup',
            'Field_Read_Dynamic',
            'By_Constraining',
            'Address',
            'By_Allocation',
            'Reference_Lex_1',
            'Variant_Record',
            'From_Utility',
            'Value_06',
            'Value_16',
            'Value_26',
            'Is_Default',
            'Round_To_Discrete',
            'Modulo',
            'Defined',
            'Value_07',
            'Value_17',
            'Value_27',
            'Bounds',
            'Store_Top_Unchecked',
            'Make_Default',
            'Convert_To_Formal',
            'Minimum',
            'Declare_Subprogram',
            'Values_Relative',
            'Store_Dynamic',
            'Mark_Auxiliary',
            'Value_02',
            'Value_12',
            'Value_22',
            'Count_Nonzero_Bits',
            'Diana_Arity_For_Kind',
            'Value_03',
            'Value_13',
            'Value_23',
            'Vector',
            'Change_Utility',
            'Declare_Variable',
            'Equal',
            'Execute',
            'Value_01',
            'Value_11',
            'Value_21',
            'Value_31',
            'Timed_Guard_Write',
            'Defined_Incomplete',
            'Illegal',
            'Is_Constrained',
            'Length',
            'Variant',
            'Arithmetic_Shift',
            'Value_00',
            'Value_10',
            'Value_20',
            'Value_30',
            'First',
            'Unary_Minus',
            'Package',
            'Direct',
            'Jump_Zero_Dynamic',
            'Set_Constraint',
            'Jump',
            'Spare7_Action',
            'Spare6_Action',
            'Multiply_And_Scale',
            'With_Result',
            'Reference_Dynamic',
            'Value_09',
            'Value_19',
            'Value_29',
            'Timed_Duration_Write',
            'Make_Parent',
            'Access',
            'Plus',
            'Less',
            'Execute_Immediate',
            'Value_08',
            'Value_18',
            'Value_28',
            'Greater',
            'Select',
            'Loop_Decreasing',
            'Loop_Increasing',
            'Pop_Auxiliary_Loop',
            'Count',
            'Get_Offset',
            'Check_In_Formal_Type',
            'Array',
            'Activate_Heap_Tasks',
            'Set_Block_Start',
            'Prepend',
            'As_Component',
            'Exit_Subprogram',
            'On_Processor',
            'Run_Utility',
            'Establish_Frame',
            'Set_Priority',
            'Get_Priority',
            'Augment_Imports',
            'Last',
            'Push_Float_Extended',
            'Float',
            'Jump_Extended',
            'Allow_Deallocate',
            'Test_And_Set_Next',
            'Set_Value_Visible',
            'Pop_Auxiliary_Range',
            'Slice_Reference',
            'Is_Null',
            'And',
            'Set_Value_Unchecked',
            'Address_Of_Type',
            'Accept_Activation',
            'Diana_Tree_Kind',
            'Signal_Completion',
            'Check_Elaborated',
            'Times',
            'Jump_Nonzero_Dynamic',
            'Pop_Auxiliary',
            'Divide_And_Scale',
            'Accesses_Protected',
            'Reraise',
            'Truncate_To_Discrete',
            'Query_Break_Mask',
            'At_Offset_6',
            'In_Type',
            'Family',
            'Exit_Nullary_Function',
            'Reverse_Bounds_Check',
            'Convert',
            'Diana_Map_Kind_To_Vci',
            'Signal_Activated',
            'Field_Reference_Dynamic',
            'Structure_Write',
            'Maximum',
            'At_Offset_4',
            'Is_Program_Error',
            'For_Outer_Call',
            'Convert_From_Discrete',
            'Visible',
            'Conditional_Call',
            'Indirect_Literal',
            'At_Offset_5',
            'Construct_Segment',
            'Less_Equal_Zero',
            'Greater_Equal_Zero',
            'Not_Equal_Zero',
            'Structure_Query',
            'Indirects_Appended',
            'Convert_Reference',
            'Partial_Minus',
            'Field_Constrain',
            'Field_Reference',
            'Jump_Zero_Extended',
            'Spare14',
            'Matrix',
            'Logical_Shift',
            'Pop_Count_1',
            'Activate_Tasks',
            'Elaborate_Subprogram',
            'Is_Numeric_Error',
            'Reverse_Bounds',
            'With_Constraint',
            'Increase_Priority',
            'Is_Tasking_Error',
            'Partial_Plus',
            'Query_Break_Cause',
            'Jump_Nonzero_Extended',
            'Or',
            'Pop_Count_3',
            'Abort_Multiple',
            'Extract_Bits',
            'Instruction_Read',
            'Name_Partner',
            'Pop_Count_2',
            'Push_String_Extended',
            'End_Rendezvous',
            'Diana_Spare2',
            'Read_Variant',
            'Component_Offset',
            'Initiate_Delay',
            'Read_Discriminant_Constraint',
            'Diana_Spare1',
            'Is_Storage_Error',
            'Field_Write_Dynamic',
            'Xor',
            'Break_Unconditional',
            'Structure_Clear',
            'Diana_Spare0',
            'Alter_Break_Mask',
            'Field_Type_Dynamic',
            'Catenate',
            'Is_Constraint_Error',
            'Not_Elaborated',
            'By_Component_Completion',
            'Set_Variant',
            'Not_In_Range',
            'By_Completing_Constraint',
            'Short_Literal',
            'Less_Equal',
            'Family_Call',
            'Bounds_With_Object',
            'Raise',
            'Entry_Call',
            'Pop_Block_With_Result',
            'Pop_Block',
            'Element_Type',
            'Store',
            'Insert_Bits',
            'Declare_Type',
            'Constrained',
            'Push_Discrete_Extended',
            'Pop_Count_5',
            'Rendezvous',
            'Deallocate',
            'Any',
            'Discrete',
            'Pop_Count_4',
            'By_Renaming',
            'All_Reference',
            'Guard_Write',
            'Pop_Count_7',
            'Above_Bound',
            'By_Constraining_Incomplete',
            'Make_Root_Type',
            'By_Defining',
            'Pop_Count_6',
            'Jump_Case',
            'Push_Structure_Extended',
            'At_Offset_2',
            'Loop_Decreasing_Extended',
            'Loop_Increasing_Extended',
            'Check_In_Type',
            'Member_Write',
            'Field_Type',
            'Check_Subprogram_Elaborated',
            'At_Offset_3',
            'Is_Initialization_Repeated',
            'Unelaborated',
            'Timed_Call',
            'Field_Write',
            'At_Offset_0',
            'Equal_Zero',
            'Activate',
            'Below_Bound',
            'Set_Value',
            'Family_Cond',
            'Field_Append',
            'Is_Instruction_Error',
            'Query_Break_Address',
            'Field_Execute_Dynamic',
            'At_Offset_1',
            'All_Write',
            'Not_In_Type',
            'Unsigned',
            'Exponentiate',
            'Complete_Type',
            'Make_Visible',
            'Store_String_Extended',
            'Case_In_Range',
            'Absolute_Value',
            'Choice_Open',
            'Append',
            'Slice_Write',
            'Family_Timed',
            'Greater_Zero',
            'Binary_Scale',
            'Diana_Put_Node_On_Seq_Type',
            'Slice_Read',
            'Is_Unsigned',
            'Write_Unchecked',
            'Set_Value_Visible_Unchecked',
            'Is_Terminated',
            'Divide',
            'Is_Constrained_Object',
            'Jump_Dynamic',
            'For_Accept',
            'With_Subtype',
            'Greater_Equal',
            'Terminate_Guard_Write',
            'Rotate',
            'Store_Unchecked',
            'Pop_Control',
            'Complement',
            'Indirect',
            'Subarray',
            'Reference_Makes_Copy',
            'Break_Optional',
            'Heap_Access',
            'Has_Repeated_Initialization',
            'Get_Segment',
            'Load',
            'All_Read',
            'Query_Frame',
            'Get_Name',
            'Count_Trailing_Zeros',
            'With_Size',
            'Idle',
            'Store_Top',
            'Size',
            'Diana_Find_Permanent_Attribute',
            'Subvector',
            'Field_Read',
            'Load_Dynamic',
            'Has_Default_Initialization',
            'Incomplete',
            'Reference',
            'Module',
            'Test_And_Set_Previous',
            'With_Value',
            'Exit_Break',
            'Make_Self',
            'Not_Equal',
            'Call',
            'Diana_Seq_Type_Get_Head',
            'Load_Encached',
            'Is_Value',
            'Set_Null',
            'Not_Null',
            'For_Call',
            'Diana_Allocate_Tree_Node',
            'Make_Scope',
            'Make_Aligned',
            'Call_Dynamic',
            'Is_Scalar',
            'Hash',
            'Is_Callable',
            'Duplicate',
            'Case_Compare',
            'Less_Zero',
            'In_Range',
            'Set_Bounds',
            'Fixed',
            'Push_String_Extended_Indexed',
            'Swap_Control',
            'Elaborate',
            'Successor',
            'Remainder',
            'Jump_Zero',
            'Run_Initialization_Utility',
            'Load_Top',
            'Field_Execute',
            'Jump_Nonzero',
            'Bounds_Check',
            'Task',
            'Record',
            'Exception',
        )
        self.literals = {}
        self.strtabs = {}

        self.subprograms = set()

    def subprogram(self, adr):
        if not adr:
            print("ZERO SUBPROGRAM")
            return
        if not self.m[adr]:
            print("ZERO at SUBPROGRAM+3 (0x%04x)" % adr)
            return
        assert adr & 7 in (0, 3)
        a0 = adr & ~3
        if a0 in self.subprograms:
            return
        self.subprograms.add(adr)
        self.m.set_label(adr, "INIT_%04x" % a0)
        self.m.set_block_comment(a0, "SUBPROGRAM")
        data.Const(self.m, a0, fmt="0x%04x")
        self.m.set_line_comment(a0, "Address of begin")
        data.Const(self.m, a0+1, fmt="0x%04x")
        self.m.set_line_comment(a0+1, "Address of exception handler")
        data.Const(self.m, a0+2, fmt="0x%04x")
        self.m.set_line_comment(a0+2, "Number of locals")
        self.disass(adr)
        self.m.set_label(self.m[a0], "BODY_%04x" % a0)
        if self.m[a0] != adr:
            self.disass(self.m[a0])
        if self.m[a0+1] not in (0x4, adr):
            self.m.set_label(self.m[a0+1], "TRAP_%04x" % a0)
            self.disass(self.m[a0+1])

    def literal(self, adr):
        y = self.literals.get(adr)
        if not y:
            v1 = (self.m[adr] << 16) | self.m[adr+1]
            v2 = (self.m[adr + 2] << 16) | self.m[adr+3]
            y = data.Data(self.m, adr, adr + 4)
            y.repr = "{0x%08x, 0x%08x}" % (v1, v2)
            y.rendered = ".LITERAL\t" + y.repr
            y.value = [v1, v2]
            y.compact = True
            self.literals[adr] = y
        return y

    def strtab(self, adr):
        b1 = (adr<<1) + self.lang.m[adr]
        b2 = ((adr + 1)<<1) + self.lang.m[adr + 1]
        y = data.Const(self.lang.m, adr, fmt="0x%%04x->0x%04x" % (b1>>1))
        y.typ = ".STRTAB"
        y.strptr = b1
        self.strtabs[adr] = y

        t = '"'
        for aa in range(b1, b2):
            i = self.lang.m[aa >> 1]
            if aa & 1:
                i &= 0xff
            else:
                i >>= 8
            if 32 <= i <= 126 and i not in (0x22, 0x5c):
                t += "%c" % i
            else:
                t += "\\x%02x" % i
        t += '"'
        self.lang.m.set_line_comment(adr, t)
        y.txt = t
        return y

if __name__ == "__main__":

    cx = r1000()
    cx.it.dump()

    l = ""
    for i in r1000_desc.split("\n"):
        if not i or i[0] == '#':
            continue
        j = i.split("|", maxsplit=1)
        if j[1] < l:
            print("oo", p)
            print("OO", i)
            print("")
        l = j[1]
        p = i
