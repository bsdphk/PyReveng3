#!/usr/bin/env python3
#
# SPDX-License-Identifier: BSD-2-Clause
#
# See LICENSE file for full text of license

'''
   This is a work-in-progress "partitioner" which divides code into
   what we will normally think of as individual functions.

   For now output is hardcoded to /tmp/H
'''

import os
import subprocess
import html

from pyreveng import code

INFLOW_SPLIT = 20

class Stretch():
    def __init__(self):
        self.nodes = []
        self.sliced = False
        self.lo = (1<<64)-1
        self.hi = 0

    def __str__(self):
        return "<Stretch 0x%x-0x%x #%d>" % (self.lo, self.hi, len(self.nodes))

    def __lt__(self, other):
        return self.lo < other.lo

    def add(self, node):
        self.lo = min(self.lo, node.lo)
        self.hi = max(self.hi, node.lo)
        if node.lo == self.lo:
            self.nodes.insert(0, node)
        else:
            self.nodes.append(node)
        node.stretch = self

    def dot_plot(self, pfx="/tmp/H/", filename=None):
        if not filename:
            filename = pfx + "/_%x.dot" % self.lo
            print(self, "Dot to", filename)
        fo = open(filename, "w+")
        fo.write("digraph {\n")
        fo.write('node [fontname="MonoSpace"]\n')
        for i in self.nodes:
            i.dot_node(fo)
        for i in self.nodes:
            i.dot_edges_in(fo)
        for i in self.nodes:
            i.dot_edges_out(fo)
        fo.write("}\n")
        fo.flush()

        svgn = pfx + '/_%x.svg' % self.lo
        x = subprocess.run([
	    "sh", "-ec",
            "dot -Gfontnames=svg -Tsvg > %s < " % svgn + filename
        ])

        fh = open(pfx + "/_%x.html" % self.lo, 'w')
        fh.write('<html>\n')
        fh.write('<head>\n')
        fh.write('<style>\n')
        if False:
            fh.write('''

.svg-container {
    display: inline-block;
    position: relative;
    width: 100%;
    height: 100%;
    padding-bottom: 100%;
    vertical-align: top;
}
''')

        fh.write('</style>\n')
        fh.write('</head>\n')
        fh.write('<body>\n')
        fh.write('<h1>Stretch ' + self.nodes[0].name + '</h1>\n')
        fh.write('<div>\n')
        fh.write(open(svgn).read().replace('xlink:href', 'href'))
        fh.write('</div>\n')
        fh.write('</body>\n')
        fh.write('</html>\n')


    def split(self, adr):
        ss = Stretch()
        i = self.nodes
        self.nodes = []
        self.lo = (1<<64)-1
        self.hi = 0
        for j in i:
            if j.lo < adr:
                self.add(j)
            else:
                ss.add(j)
        return ss

    def slice(self):
        for i in self.nodes:
            i.color = 0
        blank = list(self.nodes)
        ncolor = 0
        while blank:
            ncolor += 1
            todo = [blank.pop(0)]
            while todo:
                i = todo.pop(0)
                if i.color:
                    continue
                i.color = ncolor
                for j in i.edges_out:
                    if not j.dst or j.dst.stretch != self:
                        continue
                    if isinstance(j.flow, code.Call):
                        continue
                    if j.dst.color:
                        continue
                    j.color = i.color
                    todo.append(j.dst)
                for j in i.edges_in:
                    if not j.src or j.src.stretch != self:
                        continue
                    if isinstance(j.flow, code.Call):
                        continue
                    if j.src.color:
                        continue
                    j.color = i.color
                    todo.append(j.src)
        # print(self, "Colors", ncolor - 1)

        color_low = {}
        color_high = {}

        for i in self.nodes:
            lo = color_low.get(i.color, i.lo)
            color_low[i.color] = min(lo, i.lo)
            hi = color_high.get(i.color, i.lo)
            color_high[i.color] = max(lo, i.lo)

        for col, low in sorted(color_low.items()):
            if low in (self.lo, self.hi):
                continue
            good = True
            for j in self.nodes:
                if low <= j.lo <= color_high[col] and j.color != col:
                    good = False
                    break
            if good:
                yield color_low[col]

    def condense(self):
        for n in self.nodes:
            if len(n.edges_in) != 1:
                continue
            if not isinstance(n.edges_in[0].flow, code.Next):
                continue
            p = n.edges_in[0].src
            if len(p.edges_out) != 1:
                continue
            # print("Condense 0x%x, 0x%x" % (p.lo, n.lo))
            p.leaves += n.leaves
            p.edges_out = []
            for i in n.edges_out:
                i.src = p
                p.edges_out.append(i)
            n.edges_in = []
            p.stretch.nodes.remove(n)
            return True
        return False

class Node():
    def __init__(self, leaf, name=None):
        self.lo = leaf.lo
        self.leaves = [leaf]
        self.stretch = None
        self.edges_out = []
        self.edges_in = []
        self.dotnode = "N_%x" % leaf.lo
        assert name
        self.name = name
        self.color = 0

    def __str__(self):
        return "<N %x>" % self.lo

    def add_edge_out(self, edge):
        self.edges_out.append(edge)

    def add_edge_in(self, edge):
        self.edges_in.append(edge)

    def out_flows(self):
        for i in self.leaves:
            yield from i.flow_out

    def dot_node(self, fo):
        if ' ' in self.name:
            shape="folder"
        else:
            shape="box"
        fo.write(self.dotnode + '[shape=%s, label=<\n' % shape)
        fo.write('<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">\n')
        fo.write('<TR><TD ALIGN="left"><U>%s</U></TD></TR>\n' % self.name)
        for i in self.leaves:
            fo.write('<TR><TD ALIGN="left"')
            j = i.render().rstrip().expandtabs()
            f = None
            for x in i.flow_out:
                if not isinstance(x, code.Call):
                    continue
                for y in self.edges_out:
                    if y.flow == x and y:
                        f = x
                        y.rendered = True
                        break
            if f:
                fo.write(' BGCOLOR="#eeeeee" PORT="x%x"' % i.lo)
                if f.to:
                    fo.write(' HREF="_%x.html"' % f.to)
            fo.write('>' + html.escape(j) + '</TD></TR>\n')
        fo.write('</TABLE>>];\n')

    def dot_edges_in(self, fo):
        i_calls = []
        i_jumps = []
        e_calls = []
        e_jumps = []
        for i in self.edges_in:
            if isinstance(i.flow, code.Call):
                if i.local():
                    i_calls.append(i)
                else:
                    e_calls.append(i)
            if isinstance(i.flow, code.Jump):
                if i.local():
                    i_jumps.append(i)
                else:
                    e_jumps.append(i)

        if i_calls:
            n = 'IC_%s' % self.dotnode
            fo.write(n + ' [shape=plaintext, label=""]\n')
            fo.write(n + ' -> ' + self.dotnode + ' [dir=back,arrowtail="odot"]\n')
        if len(i_jumps) >= INFLOW_SPLIT:
            n = 'IJ_%s' % self.dotnode
            fo.write(n + ' [shape=plaintext, label=""]\n')
            fo.write(n + ' -> ' + self.dotnode + ' [dir=back,arrowtail="oinv"]\n')
            for i in i_jumps:
                i.split_arrow = True

        if e_calls:
            n = 'XC_%s' % self.dotnode
            t = '<table border="0">'
            seen = set()
            for i in e_calls:
                if i.src.stretch in seen:
                    continue
                seen.add(i.src.stretch)
                t += '<tr><td bgcolor="#eeeeee" align="left" href="_%x.html">' % i.src.stretch.lo
                t += html.escape(i.src.stretch.nodes[0].name)
                if i.flow.cond not in (True,):
                    t += " [%s]" % html.escape(i.flow.cond)
                t += "</td></tr>\n"
            t += "</table>"
            fo.write(n + ' [shape=plaintext, label=<%s>]\n' % t)
            fo.write(n + ' -> ' + self.dotnode + ' [arrowhead="dot"]\n')
        if e_jumps:
            n = 'XJ_%s' % self.dotnode
            t = '<table border="0">'
            for i in e_jumps:
                t += '<tr><td bgcolor="#eeeeee" href="_%x.html">' % i.src.stretch.lo
                t += html.escape(i.src.name)
                if i.flow.cond not in (True,):
                    t += " [%s]" % html.escape(i.flow.cond)
                t += "</td></tr>\n"
            t += "</table>"
            fo.write(n + ' [shape=plaintext, label=<%s>]\n' % t)
            fo.write(n + ' -> ' + self.dotnode + ' [arrowhead="normal"]\n')

    def dot_edges_out(self, fo):
        for i in self.edges_out:
            i.dot_edge_out(fo)

class Edge():
    def __init__(self, src, dst, flow):
        self.src = src
        self.dst = dst
        self.flow = flow
        self.split_arrow = False
        self.rendered = False

    def local(self):
        return self.dst and self.dst.stretch == self.src.stretch

    def dot_edge_out(self, fo):
        if self.rendered:
            return
        n = "O_" + self.src.dotnode
        n += "_" + str(self.flow.typ).encode('ascii').hex()

        a = []
        na = []
        if self.flow.cond not in (None, True):
            a.append('label="%s"' % str(self.flow.cond))

        if isinstance(self.flow, code.Return):
            na.append('shape=plaintext')
            na.append('label=""')
            a.append('arrowhead="tee"')
        elif isinstance(self.flow, (code.Next, code.Jump)):
            if self.local() and not self.split_arrow:
                n = self.dst.dotnode
            elif self.dst:
                na.append('shape=plain')
                na.append('style=filled')
                na.append('label="%s"' % "\\l".join(self.dst.name.split(' ', 1)))
                if not self.local():
                    na.append('color="#eeeeee"')
                    na.append('href="_%x.html"' % self.dst.stretch.lo)
            else:
                na.append('shape=plaintext')
                na.append('label="?"')
            a.append('arrowhead="onormal"')
        elif isinstance(self.flow, code.Call):
            if self.dst:
                na.append('shape=plain')
                na.append('style=filled')
                na.append('label="%s"' % "\\l".join(self.dst.name.split(' ', 1)))
                if not self.local():
                    na.append('color="#eeeeee"')
                    na.append('href="_%x.html"' % self.dst.lo)
            else:
                na.append('shape=plaintext')
                na.append('label="?"')
            if self.local():
                a.append('arrowhead="odot"')
            else:
                a.append('arrowhead="dot"')

        if na:
            fo.write('%s [%s]\n' % (n, ",".join(na)))
        fo.write('%s -> %s' % (self.src.dotnode, n))
        if a:
            fo.write(' [' + ','.join(a) + ']')
        fo.write('\n')


class Partition():

    def __init__(self, m):

        self.stretches = []
        self.nodes = {}
        self.edges = []

        for i in m:
            if getattr(i, "flow_out", None):
                n = m.afmt(i.lo)
                lbl = list(m.get_labels(i.lo))
                if lbl:
                    n += " " + lbl[0]
                self.nodes[i.lo] = Node(i, name=n)

        if not self.nodes:
            return

        s = Stretch()
        for i in self.nodes.values():
            s.add(i)
            for j in i.out_flows():
                d = self.nodes.get(j.to)
                k = Edge(i, d, j)
                self.edges.append(k)
                i.add_edge_out(k)
                n = self.nodes.get(j.to)
                if n:
                    n.add_edge_in(k)

        self.stretches.append(s)

        while True:
            did = False
            for s in self.stretches:
                if s.sliced:
                    continue
                i = list(s.slice())
                # print(s, len(i), "splits")
                if not i:
                    s.sliced = True
                    continue
                did = True
                for j in reversed(sorted(i)):
                    self.stretches.append(s.split(j))
            if not did:
                break

        for i in sorted(self.stretches):
            while i.condense():
                continue

    def dot_plot(self, pfx="/tmp/H/"):
        os.makedirs(pfx, exist_ok=True)
        for i in sorted(self.stretches):
            i.dot_plot(pfx)

        fo = open(pfx + "/index.html", "w")
        fo.write('<html>\n')
        fo.write('<head>\n')
        fo.write('<style>\n')
        fo.write('</style>\n')
        fo.write('</head>\n')
        fo.write('<body>\n')
        fo.write('<table>\n')
        for i in sorted(self.stretches):
            fo.write('<tr><td>')
            fo.write('<a href="_%x.html">%s</a>' % (i.lo, i.nodes[0].name))
            fo.write('</td><tr>\n')
        fo.write('</table>\n')
        fo.write('</body>\n')
        fo.write('</html>\n')

        print(len(self.stretches), "Stretches")
