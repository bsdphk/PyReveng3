#!/usr/bin/env python3
#
# SPDX-License-Identifier: BSD-2-Clause
#
# See LICENSE file for full text of license

'''
   Produce HTML, SVG and DOT files from a partitions

   Output directory defaults to /tmp/H
'''

import sys
import os
import subprocess
import html

from pyreveng import code

# Split jump arrows if a stretch has more than this many predecessors
INFLOW_SPLIT = 20

# Summarize same src-dst arrows with a count above this number
ONLY_COUNT_ARROWS = 7

class AddBlockComments():

    def __init__(self, partition):
        for cg in sorted(partition.groups):
            if len(cg.colors) > 1:
                continue
            cg.asp.set_block_comment(cg.lo, 'Comes from:')
            count = 0
            for stretch in cg.stretches:
                for edge in stretch.edges_in:
                    if edge.is_local():
                        continue
                    if not edge.src:
                        continue
                    count += 1
                    color = edge.src.color
                    l = [ "   " ]
                    l.append(cg.asp.adr(color.lo))
                    if color.lo != edge.flow.fm.lo:
                        l.append("@" + cg.asp.adr(edge.flow.fm.lo))
                    l.append(str(edge.flow.typ))
                    if edge.flow.cond not in (None, True):
                        l.append(str(edge.flow.cond))
                    cg.asp.set_block_comment(cg.lo, " ".join(l))
            if count == 0:
                cg.asp.set_block_comment(cg.lo, "    (unknown)")
           

class GraphVzPartition():

    ''' Emit HTML, SVG and (DOT) files for a partition '''

    def __init__(self, partition, output_dir="/tmp/H"):

        self.output_dir = output_dir
        self.partition = partition
        self.rendered = None
        self.split_arrows = None

        os.makedirs(self.output_dir, exist_ok=True)
        for cg in sorted(partition.groups):
            self.cg_dot_plot(cg, output_dir)

        self.make_index_html()
        self.make_top_dot(partition)

    def make_top_dot(self, partition):

        self.rendered = dict()
        self.incoming = dict()
        self.outgoing = dict()
        for cg in sorted(partition.groups):
            for color in cg.colors:
                for stretch in sorted(color.stretches):
                    for edge in stretch.edges_out:
                        if not edge.dst:
                            continue
                        if edge.dst.codegroup == cg:
                            continue
                        self.make_top_edge(cg, edge.dst.codegroup)

        limit = 10 
        self.hidden = set()

        self.make_top_prune_leaves()
        while self.make_top_prune():
            continue

        with open(self.output_dir + "/top.dot", "w", encoding="utf8") as fo:
            fo.write('digraph {\n')
            fo.write('rankdir=LR\n')
            for a, b in self.rendered.items():
                if b is not False:
                    continue
                assert a not in self.hidden
                fo.write('CG%x [shape=plaintext,label="%s"] # %d %d\n' % (a, cg.asp.adr(a), self.incoming[a], self.outgoing[a]))
            for a, b in self.rendered.items():
                if b is not True:
                    continue
                i, j = a
                assert j not in self.hidden
                if self.incoming[j] <= limit:
                    fo.write('CG%x -> CG%x\n' % (i, j))
            fo.write('}\n')
        self.rendered = None

    def make_top_prune_leaves(self):
        for a, b in self.outgoing.items():
            if b == 0:
                 self.hidden.add(a)
        for a, b in list(self.rendered.items()):
            if b is False and a in self.hidden:
                 del self.rendered[a]
            if b is True and a[1] in self.hidden:
                 
                 del self.rendered[a]

    def make_top_prune(self):
        retval = False
        return retval
        for a, b in list(self.rendered.items()):
            if b is False:
                if self.outgoing[a] == 0 and a not in self.hidden:
                     self.hidden.add(a)
                     retval = True
            elif 0:
                i, j = a
                if j in hidden:
                     del self.rendered[a]
                     retval = True
        return retval

    def make_top_edge(self, cg1, cg2):
        key = (cg1.lo, cg2.lo)
        if key in self.rendered:
            return
        self.rendered[key] = True
        self.make_top_cg(cg1)
        self.make_top_cg(cg2)
        self.outgoing[cg1.lo] += 1
        self.incoming[cg2.lo] += 1

    def make_top_cg(self, cg):
        if cg.lo in self.rendered:
            return
        self.rendered[cg.lo] = False
        self.incoming[cg.lo] = 0
        self.outgoing[cg.lo] = 0

    def make_index_html(self):
        ''' Make a very simple index.html file '''

        with open(self.output_dir + "/index.html", "w", encoding="utf8") as fo:
            fo.write('<!DOCTYPE html>\n')
            fo.write('<html>\n')
            fo.write('<head>\n')
            fo.write('<title>EyeCandy Index</title>\n')
            fo.write('<style>\n')
            fo.write('</style>\n')
            fo.write('<meta charset="utf-8">\n')
            fo.write('</head>\n')
            fo.write('<body>\n')
            fo.write('<table>\n')
            for cg in sorted(self.partition.groups):
                fo.write('<tr><td>')
                fo.write('<a href="_%x.html">' % cg.lo)
                fo.write('%s…%s' % (self.partition.asp.afmt(cg.lo), self.partition.asp.afmt(cg.hi)))
                fo.write(' ' + html.escape(' | '.join(sorted(cg.names()))))
                fo.write('</a></td><tr>\n')
            fo.write('</table>\n')
            fo.write('</body>\n')
            fo.write('</html>\n')

    def edge_dot_edge_out(self, edge, fo, label=None):
        ''' Render outgoing edge '''

        n = "O_%x" % edge.src.lo
        n += "_" + str(edge.flow.typ).encode('ascii').hex()

        a = []
        na = []
        if label is not None:
            a.append('label="%s"' % label)
        elif edge.flow.cond not in (None, True):
            a.append('label="%s"' % str(edge.flow.cond))

        if isinstance(edge.flow, code.Return):
            na.append('shape=plaintext')
            na.append('label=""')
            a.append('arrowhead="tee"')
        elif isinstance(edge.flow, (code.Next, code.Jump)):
            if edge.is_local() and edge not in self.split_arrows:
                n = "N_%x" % edge.dst.lo
            elif edge.dst:
                na.append('shape=plain')
                na.append('style=filled')
                i = "\\l".join(sorted(edge.dst.names()))
                if len(i) == 0:
                    i = edge.dst.asp.adr(edge.dst.lo)
                na.append('label="%s"' % i)
                if not edge.is_local():
                    na.append('color="#eeeeee"')
                    na.append('href="_%x.html"' % edge.dst.codegroup.lo)
            else:
                na.append('shape=plaintext')
                na.append('label="?"')
            a.append('arrowhead="onormal"')
        elif isinstance(edge.flow, code.Call):
            if edge.dst:
                na.append('shape=plain')
                na.append('style=filled')
                na.append('label="%s"' % "\\l".join(sorted(edge.dst.names())))
                if not edge.is_local():
                    na.append('color="#eeeeee"')
                    na.append('href="_%x.html"' % edge.dst.lo)
            else:
                na.append('shape=plaintext')
                na.append('label="?"')
            if edge.is_local():
                a.append('arrowhead="odot"')
            else:
                a.append('arrowhead="dot"')

        if na:
            fo.write('%s [%s]\n' % (n, ",".join(na)))
        fo.write('N_%x -> %s' % (edge.src.lo, n))
        if a:
            fo.write(' [' + ','.join(a) + ']')
        fo.write('\n')

    def stretch_dot_node(self, stretch, fo):
        ''' Render the node of a stretch '''

        stretch.get_name()
        names = list(stretch.names())
        if len(names) == 0:
            shape = "box"
        else:
            shape = "folder"
        stretch.get_name()
        fo.write("N_%x " % stretch.lo + '[shape=%s, label=<\n' % shape)
        fo.write('<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">\n')
        j = html.escape(stretch.asp.afmt(stretch.lo))
        fo.write('<TR><TD ALIGN="left"><U>%s</U></TD></TR>\n' % j)
        for name in sorted(stretch.names()):
            fo.write('<TR><TD ALIGN="left"><U>%s</U></TD></TR>\n' % html.escape(name))
        for i in stretch.leaves:
            j = ""
            if 0 and i.pil:
                for x in i.pil:
                    if j:
                        fo.write('<TR><TD align="left">' + j + '</TD></TR>\n')
                    j = html.escape(x.render())
                fo.write('<TR><TD ALIGN="left"')
            else:
                fo.write('<TR><TD ALIGN="left"')
                j = html.escape(i.render().rstrip().expandtabs())
            f = None
            for x in i.flow_out:
                if not isinstance(x, code.Call):
                    continue
                for y in stretch.edges_out:
                    if y.flow == x and y:
                        f = x
                        self.rendered.add(y)
                        break
            if f:
                fo.write(' BGCOLOR="#eeeeee" PORT="x%x"' % i.lo)
                if f.to:
                    fo.write(' HREF="_%x.html"' % f.to)
            fo.write('>' + j + '</TD></TR>\n')
        fo.write('</TABLE>>];\n')

    def stretch_dot_edges_in(self, stretch, fo):
        ''' Render edges going in '''

        i_calls = []
        i_jumps = []
        ci_jumps = set()
        e_calls = []
        e_jumps = []
        for i in stretch.edges_in:
            if isinstance(i.flow, code.Call):
                if i.is_local():
                    i_calls.append(i)
                else:
                    e_calls.append(i)
            if isinstance(i.flow, code.Jump):
                if i.is_local():
                    ci_jumps.add(i.src)
                    i_jumps.append(i)
                else:
                    e_jumps.append(i)

        if i_calls:
            n = 'IC_%x' % stretch.lo
            fo.write(n + ' [shape=plaintext, label=""]\n')
            fo.write(n + ' -> N_%x' % stretch.lo + ' [dir=back,arrowtail="odot"]\n')
        if len(ci_jumps) >= INFLOW_SPLIT:
            n = 'IJ_%x' % stretch.lo
            fo.write(n + ' [shape=plaintext, label=""]\n')
            fo.write(n + ' -> N_%x' % stretch.lo + ' [dir=back,arrowtail="oinv"]\n')
            for i in i_jumps:
                self.split_arrows.add(i)

        if e_calls:
            n = 'XC_%s' % stretch.lo
            t = '<table border="0">\n'
            seen = set()
            for i in e_calls:
                if i.src.color in seen:
                    continue
                seen.add(i.src.color)
                t += '<tr><td bgcolor="#eeeeee" align="left" href="_%x.html">' % i.src.codegroup.lo
                t += html.escape(i.src.color.get_name())
                if i.flow.cond not in (True,):
                    t += " [%s]" % html.escape(i.flow.cond)
                t += "</td></tr>\n"
            t += "</table>"
            fo.write(n + ' [shape=plaintext, label=<%s>]\n' % t)
            fo.write(n + ' -> N_%x' % stretch.lo + ' [arrowhead="dot"]\n')
        if e_jumps:
            n = 'XJ_%x' % stretch.lo
            t = '<table border="0">'
            for i in e_jumps:
                t += '<tr><td bgcolor="#eeeeee" href="_%x.html">' % i.src.codegroup.lo
                t += html.escape(i.src.name)
                if i.flow.cond not in (True,):
                    t += " [%s]" % html.escape(i.flow.cond)
                t += "</td></tr>\n"
            t += "</table>"
            fo.write(n + ' [shape=plaintext, label=<%s>]\n' % t)
            fo.write(n + ' -> N_%x' % stretch.lo + ' [arrowhead="normal"]\n')

    def stretch_dot_edges_out(self, stretch, fo):
        ''' Render any outgoing edges not yet rendered '''

        # If there are too many edges to the same destination
        # draw a single arrow, labled with the count
        dcount = {}
        for edge in stretch.edges_out:
            n = dcount.get(edge.dst, 0)
            dcount[edge.dst] = n + 1

        for edge in stretch.edges_out:
            if edge in self.rendered:
                continue
            self.rendered.add(edge)
            if edge.dst not in dcount:
                continue
            c = dcount[edge.dst]
            if c >= ONLY_COUNT_ARROWS:
                self.edge_dot_edge_out(edge, fo, "[*%d]" % c)
                del dcount[edge.dst]
                continue
            self.edge_dot_edge_out(edge, fo)

    def color_dot_plot(self, color, fo):
        ''' render the nodes of a color '''

        assert len(color.stretches) == len(set(color.stretches))
        for stretch in sorted(color.stretches):
            self.stretch_dot_node(stretch, fo)
        for stretch in sorted(color.stretches):
            self.stretch_dot_edges_in(stretch, fo)
        for stretch in sorted(color.stretches):
            self.stretch_dot_edges_out(stretch, fo)

    def cg_dot_plot(self, cg, pfx):
        '''
           Render a CodeGroup.

          If it has multiple colors, cluster them.
        '''

        self.rendered = set()
        self.split_arrows = set()
        cg.get_name()
        filename = pfx + "/_%x.dot" % cg.lo
        # print(cg, "Dot to", filename)
        with open(filename + ".tmp", "w", encoding="utf8") as fo:
            fo.write("digraph {\n")
            fo.write('node [fontname="MonoSpace"]\n')
            for n, color in enumerate(cg.colors):
                if len(cg.colors) > 1:
                    fo.write("subgraph cluster_%d {\n" % n)
                self.color_dot_plot(color, fo)
                if len(cg.colors) > 1:
                    fo.write("}\n")
            fo.write("}\n")
            fo.flush()
        self.rendered = None
        self.split_arrows = None

        svgn = pfx + '/_%x.svg' % cg.lo


        try:
            before = open(filename).read()
        except FileNotFoundError:
            before = ""

        after = open(filename + ".tmp").read()

        if before != after:
            os.rename(filename + ".tmp", filename)

            print("dot'ing", cg)
            sys.stdout.flush()
            sp = subprocess.run([
                "sh", "-ec",
                "dot -Gfontnames=svg -Tsvg > %s < " % svgn + filename
            ])
            if sp.returncode:
                print("dot failed on", cg)

        with open(pfx + "/_%x.html" % cg.lo, 'w', encoding="utf8") as fh:
            fh.write('<!DOCTYPE html>\n')
            fh.write('<html>\n')
            fh.write('<head>\n')
            fh.write('<title>EyeCandy ' + html.escape(cg.asp.afmt(cg.lo)) + '</title>\n')
            fh.write('<style>\n')
            fh.write('</style>\n')
            fh.write('<meta charset="utf-8">\n')
            fh.write('</head>\n')
            fh.write('<body>\n')
            fh.write('<h1>CodeGroup ' + cg.asp.afmt(cg.lo) + "…" + cg.asp.afmt(cg.hi) + '</h1>\n')
            for name in sorted(cg.names()):
                fh.write('<h2>' + html.escape(name) + '</h2>\n')
            fh.write('<div>\n')
            with open(svgn, encoding="utf8") as fs:
                fh.write(fs.read().replace('xlink:href', 'href'))
            fh.write('</div>\n')
            fh.write('</body>\n')
            fh.write('</html>\n')
