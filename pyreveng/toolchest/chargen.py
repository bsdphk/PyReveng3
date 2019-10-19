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
Functions for rendering a character set as an SVG file.
"""

import cairo

DEFAULTS = {
    "margin": 10,    # Outside margin
    "cols": 16,      # Columns of characters
    "rows": 16,      # Rows of characters
    "imargin": 4,    # Per-cell margin
    "char_w": 7,     # Char width
    "char_h": 13,    # Char height
    "linewidth": 1,  # Thickness of lines
    "leftright": 1,  # Bit order
}

class SVG_Charset():

    def __init__(self, fn, **kwargs):
        self.fn = fn
        for i, j in DEFAULTS.items():
            self.__setattr__(i, j)
        for i, j in kwargs.items():
            if i not in DEFAULTS:
                raise Exception("Unknown arg %s" % i)
            self.__setattr__(i, j)
        self.char = [None] * self.rows * self.cols

    def set_char(self, x, y, b):
        self.char[x * self.rows + y] = b

    def calc_geom(self):
        self.cell_w = self.char_w + 2 * self.imargin + self.linewidth
        self.cell_h = self.char_h + 2 * self.imargin + self.linewidth
        self.width = self.margin * 2 + self.cell_w * self.cols
        self.height = self.margin * 2 + self.cell_h * self.rows

    def draw_grid(self):
        self.ctx.set_line_cap(cairo.LINE_CAP_SQUARE)
        self.ctx.set_line_width(self.linewidth)
        self.ctx.set_source_rgba(.5, .5, .5, 1.0)
        for i in range(self.cols + 1):
            x = self.margin + .5 * self.linewidth + i * self.cell_w
            y0 = self.margin + .5 * self.linewidth
            y1 = y0 + self.rows * self.cell_h
            self.ctx.move_to(x, y0)
            self.ctx.line_to(x, y1)
            self.ctx.stroke()
        for i in range(self.rows + 1):
            y = self.margin + .5 * self.linewidth + i * self.cell_h
            x0 = self.margin + .5 * self.linewidth
            x1 = x0 + self.cols * self.cell_w
            self.ctx.move_to(x0, y)
            self.ctx.line_to(x1, y)
            self.ctx.stroke()

    def draw_char(self, x, y, c):
        self.ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        self.ctx.set_line_width(1)
        self.ctx.set_source_rgba(0, 0, 0, 1.0)
        x0 = self.margin + self.linewidth + x * self.cell_w + self.imargin
        y0 = self.margin + self.linewidth + y * self.cell_h + self.imargin

        for j in c[:self.char_h]:
            if self.leftright:
                gx = x0
                gi = 1
            else:
                gx = x0 + self.char_w - 1
                gi = -1

            m = 1 << (self.char_w - 1)
            while m:
                if j & m:
                    self.ctx.move_to(gx + .5, y0)
                    self.ctx.line_to(gx + .5, y0 + 1)
                m >>= 1
                gx += gi
            y0 += 1
        self.ctx.stroke()

    def render(self):
        self.calc_geom()
        self.surf = cairo.SVGSurface(self.fn, self.width, self.height)
        self.ctx = cairo.Context(self.surf)
        self.draw_grid()
        for x in range(self.cols):
            for y in range(self.rows):
                c = self.char[x * self.rows + y]
                if c:
                    self.draw_char(x, y, c)

if __name__ == "__main__":

    rom = open("EPROM_380217-01_R.B_PC_CHAR._U2.bin", "rb").read()

    S = SVG_Charset("/tmp/_.svg", imargin=2)

    n = 0
    for i in range(0, len(rom), 16):
        S.set_char(n // 16, n % 16, rom[i:i+16])
        n += 1

    S.render()
