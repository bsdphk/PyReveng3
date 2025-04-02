#!/usr/bin/env python3
#
# SPDX-License-Identifier: BSD-2-Clause
#
# See LICENSE file for full text of license

'''
   This is a work-in-progress "partitioner" which divides code into
   what we will normally think of as individual functions.
'''

from pyreveng import code

INFLOW_SPLIT = 20

class Edge():
    '''
       An edge represents transfer of control in and/or out
       of stretches and are built from the code.Flow records.
    '''

    def __init__(self, src, dst, flow):
        self.src = src
        self.dst = dst
        self.flow = flow

    def __str__(self):
        return "<Edge " + str(self.src) + " -> " + str(self.dst) + ">"

    def is_local(self):
        ''' ... as in "Both ends have same color" '''
        return self.dst and self.dst.color == self.src.color

class Stretch():
    '''
        An unbroken stretch of instructions with no external
        influence on state.  Said another way:  Jumps, calls,
        returns, traps etc. can only occur as the last instruction
        in a stretch.
    '''

    def __init__(self, leaf, asp, number):
        self.lo = leaf.lo
        self.leaves = [leaf]
        self.codegroup = None
        self.color = None
        self.edges_out = []
        self.edges_in = []
        self.asp = asp
        self.color = 0
        self.myname = None
        self.number = number

    def __str__(self):
        return "<Stretch %x %d>" % (self.lo, self.number)

    def __lt__(self, other):
        return self.lo < other.lo

    def add_edge_out(self, edge):
        ''' ... '''
        self.edges_out.append(edge)

    def add_edge_in(self, edge):
        ''' ... '''
        self.edges_in.append(edge)

    def out_flows(self):
        ''' ... '''
        for i in self.leaves:
            yield from i.flow_out

    def names(self):
        ''' ... '''
        yield from self.asp.get_labels(self.leaves[0].lo)

    def get_name(self):
        ''' ... '''
        if not self.myname:
            self.myname = ' | '.join(sorted(self.names()))
        if not self.myname:
            self.myname = self.asp.adr(self.lo)
        return self.myname


class Color():
    '''
       A group of stretches connected by non-Call Edges.

       Most colors, the ones we like best, occupy a compact stretch
       of address space into which no other colors intrude.
    '''

    def __init__(self, number, asp):
        self.lo = (1<<64)-1
        self.hi = 0
        self.stretches = []
        self.number = number
        self.myname = None
        self.asp = asp

    def __str__(self):
        return "<Color %d 0x%x-0x%x #%d>" % (self.number, self.lo, self.hi, len(self.stretches))

    def __lt__(self, other):
        return self.lo < other.lo

    def add(self, stretch):
        ''' ... '''
        if stretch.color is not None:
            print("Recoloring", stretch, stretch.color, "->", stretch.color)
            assert False
        self.stretches.append(stretch)
        self.lo = min(self.lo, stretch.lo)
        self.hi = max(self.hi, stretch.lo)
        stretch.color = self

    def names(self):
        '''
           All names given to the first stretch and any other stetches
           called from outside.  The first stretch gets a free pass
           because execution may get here through pointer gymnastics
           undocumented by flow records.
        '''
        interior = False
        for stretch in sorted(self.stretches):
            for edge in stretch.edges_in:
                if not edge.is_local():
                    interior = False
                    break

            if not interior:
                yield from stretch.names()
            interior = True

    def get_name(self):
        ''' ... '''
        if not self.myname:
            self.myname = ' | '.join(sorted(self.names()))
        if not self.myname:
            self.myname = self.asp.adr(self.lo)
        return self.myname

    def condense(self):
        ''' Merge stretches connected by code.Next records '''
        for stretch in sorted(self.stretches):
            if len(stretch.edges_in) != 1:
                continue
            if not isinstance(stretch.edges_in[0].flow, code.Next):
                continue
            successor = stretch.edges_in[0].src
            if len(successor.edges_out) != 1:
                continue
            successor.leaves += stretch.leaves
            successor.edges_out = []
            for edge in stretch.edges_out:
                edge.src = successor
                successor.edges_out.append(edge)
            stretch.edges_in = []
            successor.color.stretches.remove(stretch)
            return True
        return False

class CodeGroup():
    '''
       A group of instructions
       =======================

       A group of instructions which it makes sense to considered together,
       for instance the instructions which make up a function or procedure.
    '''

    def __init__(self, asp):
        self.stretches = set()
        self.lo = (1<<64)-1
        self.hi = 0
        self.colors = set()
        self.myname = None
        self.asp = asp

    def __str__(self):
        return "<CodeGroup 0x%x-0x%x,%d,%d>" % (
            self.lo, self.hi, len(self.stretches), len(self.colors)
        )

    def __lt__(self, other):
        return self.lo < other.lo

    def names(self):
        '''
           All names from all colors
        '''
        for color in self.colors:
             yield from color.names()

    def get_name(self):
        ''' ... '''
        if not self.myname:
            self.myname = ' | '.join(sorted(self.names()))
        if not self.myname:
            self.myname = self.asp.adr(self.lo)
        return self.myname

    def add(self, stretch):
        ''' Add a stretch to this group '''
        self.lo = min(self.lo, stretch.lo)
        self.hi = max(self.hi, stretch.lo)
        self.stretches.add(stretch)
        stretch.codegroup = self

    def paint_by_numbers(self):
        '''
           Flood-fill all connected sets of stretches with individual "colors"

           Only non-Call flows are considered
        '''

        self.colors = set()
        for stretch in self.stretches:
            stretch.color = None

        for stretch in sorted(self.stretches):
            if stretch.color:
                continue

            next_color = Color(len(self.colors), self.asp)
            self.colors.add(next_color)
            next_color.add(stretch)
            todo = [stretch]
            while todo:
                stretch = todo.pop(0)
                assert stretch.color == next_color
                for edge in stretch.edges_out:
                    if isinstance(edge.flow, code.Call):
                        continue
                    if not edge.dst:
                        continue
                    if edge.dst.color is not None:
                        assert edge.dst.color == next_color
                    else:
                        next_color.add(edge.dst)
                        todo.append(edge.dst)
                        # print("C DST", next_color, edge.src, edge.dst)
                for edge in stretch.edges_in:
                    if isinstance(edge.flow, code.Call):
                        continue
                    if not edge.src:
                        continue
                    if edge.src.color is not None:
                        assert edge.src.color == next_color
                    else:
                        next_color.add(edge.src)
                        todo.append(edge.src)
                        # print("C SRC", next_color, edge.src, edge.dst)

    def color_can_be_evicted(self, color):
        ''' A color can be evicted if there are no miscolored stretches inside '''

        if color.lo in (self.lo, self.hi):
            return False
        for stretch in self.stretches:
            if stretch.color != color and color.lo <= stretch.lo <= color.hi:
                print("Stranger in color", color, stretch, stretch.color)
                return False
        return True

    def evict_colors(self):
        ''' Evict all well-shaped colors '''

        for color in list(sorted(self.colors)):
            if not self.color_can_be_evicted(color):
                continue
            new_cg = CodeGroup(self.asp)
            for stretch in color.stretches:
                self.stretches.remove(stretch)
                new_cg.add(stretch)
            self.colors.remove(color)
            new_cg.colors.add(color)
            yield new_cg
        self.lo = min(stretch.lo for stretch in self.stretches)
        self.hi = max(stretch.lo for stretch in self.stretches)

    def condense(self):
        ''' Condense code.Next connected in stretches '''
        for color in self.colors:
            while color.condense():
                continue


class Partition():
    '''
       Partition the code.Code leaves on an address space into
       "sensible" code groups.

       "sensible" means a group of instructions which occupy a
       compact range of the address space, into which other such
       groups do not intrude.

       This is of course not always possible. (See also: spaghetti
       code) and we leave the "dross", in the first group.
    '''

    def __init__(self, asp):

        self.groups = []
        self.stretches = {}
        self.edges = []
        self.asp = asp

        # Create a single codegroup with all instructions
        # each in their own stretch.
        self.residual_cg = CodeGroup(asp)
        self.groups.append(self.residual_cg)
        n = 0
        for leaf in asp:
            if hasattr(leaf, "flow_out"):
                stretch = Stretch(leaf, asp, n)
                n += 1
                self.stretches[leaf.lo] = stretch
                self.residual_cg.add(stretch)

        if not self.stretches:
            return

        # Create Edges for all out-flows
        for stretch in self.stretches.values():
            for oflow in stretch.out_flows():
                dst = self.stretches.get(oflow.to)
                edge = Edge(stretch, dst, oflow)
                self.edges.append(edge)
                stretch.add_edge_out(edge)
                dstretch = self.stretches.get(oflow.to)
                if dstretch:
                    dstretch.add_edge_in(edge)

        self.residual_cg.paint_by_numbers()
        for new_cg in self.residual_cg.evict_colors():
            self.groups.append(new_cg)

        for cg in sorted(self.groups):
            cg.condense()
