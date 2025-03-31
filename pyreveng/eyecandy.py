#!/usr/bin/env python3
#
# SPDX-License-Identifier: BSD-2-Clause
#
# See LICENSE file for full text of license

'''
   Produce dot-files from partitions

   Output directory defaults to /tmp/H
'''

import os
import subprocess
import html

from pyreveng import code 

INFLOW_SPLIT = 20


def edge_dot_edge_out(edge, fo):
    if edge.rendered:
        return
    n = "O_" + edge.src.dotnode
    n += "_" + str(edge.flow.typ).encode('ascii').hex()

    a = []
    na = []
    if edge.flow.cond not in (None, True):
        a.append('label="%s"' % str(edge.flow.cond))

    if isinstance(edge.flow, code.Return):
        na.append('shape=plaintext')
        na.append('label=""')
        a.append('arrowhead="tee"')
    elif isinstance(edge.flow, (code.Next, code.Jump)):
        if edge.local() and not edge.split_arrow:
            n = edge.dst.dotnode
        elif edge.dst:
            na.append('shape=plain')
            na.append('style=filled')
            na.append('label="%s"' % "\\l".join(sorted(edge.dst.names())))
            if not edge.local():
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
            if not edge.local():
                na.append('color="#eeeeee"')
                na.append('href="_%x.html"' % edge.dst.lo)
        else:
            na.append('shape=plaintext')
            na.append('label="?"')
        if edge.local():
            a.append('arrowhead="odot"')
        else:
            a.append('arrowhead="dot"')
        
    if na:
        fo.write('%s [%s]\n' % (n, ",".join(na)))
    fo.write('%s -> %s' % (edge.src.dotnode, n))
    if a:
        fo.write(' [' + ','.join(a) + ']')
    fo.write('\n')

def stretch_dot_node(stretch, fo):
    stretch.get_name()
    fo.write(stretch.dotnode + '[shape=%s, label=<\n' % stretch.shape)
    fo.write('<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">\n')
    fo.write('<TR><TD ALIGN="left"><U>%s</U></TD></TR>\n' % stretch.asp.afmt(stretch.lo))
    for name in sorted(stretch.names()):
        fo.write('<TR><TD ALIGN="left"><U>%s</U></TD></TR>\n' % name)
    for i in stretch.leaves:
        fo.write('<TR><TD ALIGN="left"')
        j = i.render().rstrip().expandtabs()
        f = None
        for x in i.flow_out:
            if not isinstance(x, code.Call):
                continue
            for y in stretch.edges_out:
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



def stretch_dot_edges_in(stretch, fo):
    i_calls = []
    i_jumps = []
    e_calls = []
    e_jumps = []
    for i in stretch.edges_in:
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
        n = 'IC_%s' % stretch.dotnode
        fo.write(n + ' [shape=plaintext, label=""]\n')
        fo.write(n + ' -> ' + stretch.dotnode + ' [dir=back,arrowtail="odot"]\n')
    if len(i_jumps) >= INFLOW_SPLIT:
        n = 'IJ_%s' % stretch.dotnode
        fo.write(n + ' [shape=plaintext, label=""]\n')
        fo.write(n + ' -> ' + stretch.dotnode + ' [dir=back,arrowtail="oinv"]\n')
        for i in i_jumps:
            i.split_arrow = True

    if e_calls:
        n = 'XC_%s' % stretch.dotnode
        t = '<table border="0">\n'
        seen = set()
        for i in e_calls:
            if i.src.codegroup in seen:
                continue
            seen.add(i.src.codegroup)
            t += '<tr><td bgcolor="#eeeeee" align="left" href="_%x.html">' % i.src.codegroup.lo
            t += html.escape(i.src.get_name())
            if i.flow.cond not in (True,):
                t += " [%s]" % html.escape(i.flow.cond)
            t += "</td></tr>\n"
        t += "</table>"
        fo.write(n + ' [shape=plaintext, label=<%s>]\n' % t)
        fo.write(n + ' -> ' + stretch.dotnode + ' [arrowhead="dot"]\n')
    if e_jumps:
        n = 'XJ_%s' % stretch.dotnode
        t = '<table border="0">'
        for i in e_jumps:
            t += '<tr><td bgcolor="#eeeeee" href="_%x.html">' % i.src.codegroup.lo
            t += html.escape(i.src.name)
            if i.flow.cond not in (True,):
                t += " [%s]" % html.escape(i.flow.cond)
            t += "</td></tr>\n"
        t += "</table>"
        fo.write(n + ' [shape=plaintext, label=<%s>]\n' % t)
        fo.write(n + ' -> ' + stretch.dotnode + ' [arrowhead="normal"]\n')

def stretch_dot_edges_out(stretch, fo):
    for edge in stretch.edges_out:
        edge_dot_edge_out(edge, fo)

def color_dot_plot(color, fo):
    assert len(color.stretches) == len(set(color.stretches))
    for stretch in sorted(color.stretches):
        stretch_dot_node(stretch, fo)
    for stretch in sorted(color.stretches):
        stretch_dot_edges_in(stretch, fo)
    for stretch in sorted(color.stretches):
        stretch_dot_edges_out(stretch, fo)

def cg_dot_plot(cg, pfx="/tmp/H/", filename=None):
    cg.get_name()
    if not filename:
        filename = pfx + "/_%x.dot" % cg.lo
        print(cg, "Dot to", filename)
    with open(filename, "w") as fo:
        fo.write("digraph {\n")
        fo.write('node [fontname="MonoSpace"]\n')
        for n, color in enumerate(cg.colors):
            if len(cg.colors) > 1:
                fo.write("subgraph cluster_%d {\n" % n)
            color_dot_plot(color, fo)
            if len(cg.colors) > 1:
                fo.write("}\n")
        fo.write("}\n")
        fo.flush()
        
    svgn = pfx + '/_%x.svg' % cg.lo
    x = subprocess.run([
        "sh", "-ec",
        "dot -Gfontnames=svg -Tsvg > %s < " % svgn + filename
    ])
    
    fh = open(pfx + "/_%x.html" % cg.lo, 'w')
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
    fh.write('<h1>CodeGroup ' + cg.asp.afmt(cg.lo) + "…" + cg.asp.afmt(cg.hi) + '</h1>\n')
    for name in sorted(cg.names()):
        fh.write('<h2>' + html.escape(name) + '</h2>\n')
    fh.write('<div>\n')
    fh.write(open(svgn).read().replace('xlink:href', 'href'))
    fh.write('</div>\n')
    fh.write('</body>\n')
    fh.write('</html>\n')



class GraphVzPartition():

    def __init__(self, partition, output_dir="/tmp/H"):

        self.output_dir = output_dir
        self.partition = partition

        os.makedirs(self.output_dir, exist_ok=True)
        for cg in sorted(partition.groups):
            cg_dot_plot(cg, output_dir)

        fo = open(output_dir + "/index.html", "w")
        fo.write('<html>\n')
        fo.write('<head>\n')
        fo.write('<style>\n')
        fo.write('</style>\n')
        fo.write('</head>\n')
        fo.write('<body>\n')
        fo.write('<table>\n')
        for cg in sorted(partition.groups):
            fo.write('<tr><td>')
            fo.write('<a href="_%x.html">%s…%s %s</a>' % (cg.lo, partition.asp.afmt(cg.lo), partition.asp.afmt(cg.hi), cg.myname))
            fo.write('</td><tr>\n')
        fo.write('</table>\n')
        fo.write('</body>\n')
        fo.write('</html>\n')

        print(len(partition.groups), "Groups")
