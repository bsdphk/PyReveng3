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
   Render a bitmap using Unicode Block Elements and Box Drawing codepoints
'''

class BitMapError(Exception):
    pass

class BitMap():
    '''
       BitMap rendered with UniCode
    '''
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.sx = (x + 7) // 8
        self.sy = y
        if y & 1:
            self.sy += 1
        self.b = bytearray([0] * (self.sx * self.sy))
        self.xlat = " _▝_▘_▀_▗_▐_▚_▜_▖_▞_▌_▛_▄_▟_▙_█".replace("_", "")
        #            0 1 2 3 4 5 6 7 8 9 a b c d e f

    def set(self, x, y):
        ''' Set a pixel '''
        if x < 0 or y < 0 or x >= self.x or y >= self.y:
            raise BitMapError(
                "Coordinate outside canvas (0x%x, 0x%x)" % (x, y)
            )
        m = 0x80 >> (x & 7)
        i = y * self.sx + (x >> 3)
        self.b[i] |= m

    def clr(self, x, y):
        ''' Clear a pixel '''
        if x < 0 or y < 0 or x >= self.x or y >= self.y:
            raise BitMapError(
                "Coordinate outside canvas (0x%x, 0x%x)" % (x, y)
            )
        m = 0x80 >> (x & 7)
        i = y * self.sx + (x >> 3)
        self.b[i] |= m

    def __str__(self):
        nx = (self.x + 1) // 2
        t = "┌" + "─" * nx + "┐\n"
        p0 = 0
        for y in range(0, self.sy, 2):
            tt = ""
            p = p0
            for x in range(0, nx, 4):
                for m in (6, 4, 2, 0):
                    v = (self.b[p] >> m) & 3
                    v |= (self.b[p + self.sx] >> m) << 2
                    tt += self.xlat[v & 0xf]
                p += 1
            p0 += self.sx * 2
            t += "│" + tt[:nx] + "│\n"
        t += "└" + "─" * nx + "┘"
        return t
