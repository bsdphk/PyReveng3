#!/usr/bin/env python3
#
# SPDX-License-Identifier: BSD-2-Clause
#
# See LICENSE file for full text of license

'''
'''

class Struct():
    '''
        A composite data structure

        A trivial example:

                leaf = Struct(
                    tree,
                    some_address,
                    naked=True,
                    vertical=True,
                    first_field_=Le32,
                    second_field__=7,
                    last_field_=text_field(8),
                    size=0x100,
                )

        Note the trailing underscores which designates arguments
        as field names.

	The fields definition can be either an integer, which creates
	a predefined filed typ that wide or it can be a class which
	will be instantiated with arguments of

                Le32(tree, some_address + field_offset)

        Which allows fields to be defined with all the classes in
        this file, notably including subclasses of Struct itself.

        Each field creates an attribute without the trailing
        underscore, holding the instance of the class, so for
        instance:

                leaf.first_field.val

        is the 32 bit little-endian value and

                leaf.last_field.txt

        is the decoded text-string.

        The extra underscore on the second field name hides the
        field when rendering but still adds the attribute
        '.second_field_'

        If 'naked' is true, fields which have a "val" attribute
        will be represented by that, so that you can get that
        value with ``mystruct.field`` instead of ``mystruct.field.val``

        The 'vertical' argument controls rendering (one line vs one
        line per field)

        The 'size' defines the total size for cases where the fields
        do not add up.

        Variant structs can be built incrementally, but must then be
        explicitly completed:

                leaf = Struct(
                    tree,
                    some_address,
                    n_elem_=Le16,
                    incomplete=True,
                )
                for i in range(leaf.n_elem.val):
                    leaf.add_field("f%d" % i, Le32)
                leaf.complete(size = 512);

    '''

    def __init__(self, tree, lo, vertical=False, more=False, pad=0, naked=False, **kwargs):
        self.fields = []
        self.vertical = vertical
        self.lo = lo
        self.hi = lo
        self.tree = tree
        self.args = {}
        self.naked = naked
        self.pseudofields = []
        for name, width in kwargs.items():
            if name[-1] == "_":
                self.add_field(name[:-1], width)
            else:
                self.args[name] = width

        if not more:
            self.done(pad=pad)

    def __getattr__(self, what):
        ''' Silence pylint E1101 '''
        raise AttributeError(
            "'" + self.__class__.__name__ + "' has no attribute '" + str(what) + "'"
        )

    def done(self, pad=0):
        ''' Struct is complete, finish up '''
        if pad != 0:
            if pad < 0:
                pad = -pad
                visible = True
            else:
                visible = False
            end = self.lo + pad
            if end < self.hi:
                print(
                    self.__class__.__name__,
                    [ hex(self.lo), hex(self.hi) ],
                    "Padding to less than current size",
                    hex(pad),
                    "vs",
                    hex(self.hi - self.lo),
                )
            elif end == self.hi:
                pass
            elif visible:
                self.add_field("pad_at_%x" % (self.hi - self.lo), end - self.hi)
            else:
                self.add_field("pad_at_%x_" % (self.hi - self.lo), end - self.hi)
        self.base_init(**self.args)
        del self.args

    def add_field(self, name, what):
        ''' add a field to the structure '''
        assert hasattr(self, "args")
        if name is None:
            name = "at%04x" % (self.hi - self.lo)
        if isinstance(what, int):
            y = self.number_field(self.hi, what)
            z = y
        elif isinstance(what, tuple):
            cls, kwargs = what
            y = cls(self.tree, self.hi, **kwargs)
            z = y
        else:
            y = what(self.tree, self.hi)
            z = y
        self.hi = y.hi
        if self.naked and hasattr(z, "val"):
            setattr(self, name, z.val)
        else:
            setattr(self, name, z)
        self.fields.append((name, y))
        return y

    def suffix(self, adr):
        ''' Suffix in vertical mode is byte offset of field '''
        return "\t// @0x%x" % (adr - self.lo)

    def commit(self):
        for _name, obj in self.fields:
            obj.commit()

    def render(self):
        assert not hasattr(self, "args")
        if not self.vertical:
            i = []
            for name, obj in self.pseudofields:
                if name[-1] != "_":
                    i.append(name + "=" + str(obj))
            for name, obj in self.fields:
                if name[-1] != "_":
                    i.append(name + "=" + "|".join(obj.render()))
            yield self.__class__.__name__ + " {" + ", ".join(i) + "}"
        else:
            yield self.__class__.__name__ + " {"
            for name, obj in self.fields:
                if name[-1] != "_":
                    j = list(obj.render())
                    j[0] += self.suffix(obj.lo)
                    yield "  " + name + " = " + j[0]
                    if len(j) > 1:
                        for i in j[1:-1]:
                            yield "    " + i
                        yield "  " + j[-1]
            yield "}"

    def dot_edges(self, dot, src=None):
        if src is None:
            src = self
        for name, fld in self.fields:
            fld.dot_edges(dot, src)

def Array(struct_class, count, what, vertical=None, naked=False):
    ''' An array of things '''

    if count > 0:

        class Array_Class(struct_class):
            WHAT = what
            COUNT = count
            NAKED = naked

            def __init__(self, *args, **kwargs):
                if vertical:
                    kwargs["vertical"] = vertical
                super().__init__(*args, more = True, **kwargs)
                self.array = []
                self.items = []
                for i in range(self.COUNT):
                    f = self.add_field("f%d" % i, self.WHAT)
                    self.items.append(f)
                    if self.NAKED and hasattr(f, "val"):
                        self.array.append(f.val)
                    else:
                        self.array.append(f)
                self.done()

            def __getitem__(self, idx):
                return self.array[idx]

            def __iter__(self):
                yield from self.array

            def render(self):
                if not self.vertical:
                    yield '[' + ", ".join("".join(x.render()) for x in self.items) + "]"
                else:
                    yield '['
                    i = len("%x" % len(self.items))
                    fmt = "  [0x%%0%dx]: " % i
                    for n, i in enumerate(self.items):
                        for j in i.render():
                            yield fmt % n + j
                    yield ']'

            def commit(self):
                for obj in self.items:
                    obj.commit()

            def dot_edges(self, dot, src=None):
                if src is None:
                    src = self
                for fld in self.array:
                    fld.dot_edges(dot, src)

        return Array_Class

    class Array_Class():
        WHAT = what
        COUNT = count

        def __init__(self, tree, lo, *args, **kwargs):
            self.tree = tree
            self.lo = lo
            self.hi = lo
            self.array = []

        def __getitem__(self, idx):
            return self.array[idx]

        def __iter__(self):
            yield from self.array

        def render(self):
            yield '[]'

        def dot_edges(self, dot, src=None):
            if src is None:
                src = self
            for fld in self.array:
                fld.dot_edges(dot, src)


    return Array_Class
