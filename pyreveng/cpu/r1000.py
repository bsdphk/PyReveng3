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

from pyreveng import assy, data, code


r1000_desc = """

################
# Ref: FEH p269
#INDIRECT_LITERAL	DISCRETE,0x20					| 6004 |
DECLARE_VARIABLE	DISCRETE,WITH_VALUE,WITH_CONSTRAINT		| 03EC |
# CALL			0,0						| 8000 |

################
# Ref: GC1 p88
#JUMP			1						| 7801	|
DECLARE_SUBPROGRAM	subp,FOR_OUTHER_CALL,IS_VISIBLE			|0 0 0 0|0 0 1 0|1 0 0 1|1 1 0 0| subp				|
# CALL			2,2						| 8402 |
BREAK_UNCONDITIONAL	-						| 006F |
EXECUTE			EXCEPTION_CLASS,RAISE_OP,>R			| 0100 |

# RERAISE_OP at 0x0101 is a guess, based on it occuring right before 0x0000
# and being subsequent to RAISE_OP (0x0100) in the Machine_Code.ada
EXECUTE			EXCEPTION_CLASS,RERAISE_OP,>R			| 0101 |

#INDIRECT_LITERAL	57						| 6039 |
#INDIRECT_LITERAL	52						| 6034 |
EXECUTE			MODULE_CLASS,ACTIVATE_OP			| 020F |
# CALL			3,3						| 8603 |

################
# Ref: GC1 p28
#RAISE			>R						| 0100 |

################
# Ref: GC1 p41-46
BREAK_OPTIONAL	-							| 0007 |
SIGNAL_COMPLETION	>R						| 00BB |
SIGNAL_ACTIVATED	-						| 00BC |
ACCEPT_ACTIVATION	-						| 00BF |
ELABORATE_SUBPROGRAM	-						| 00C7 |
unknown_return		>R						| 00CA |
LOAD_TOP_0		-						| 00D8 |

EXECUTE_VECTOR_CLASS	CHECK_IN_TYPE_OP				| 01C3 |
EXECUTE_VECTOR_CLASS	CATENATE_OP					| 01CC |
EXECUTE_VECTOR_CLASS	FIELD_WRITE_OP					| 01D6 |
EXECUTE_MODULE_CLASS	AUGMENT_IMPORTS_OP				| 020E |
EXECUTE_MODULE_CLASS	ALL_REFERENCE_OP				| 0217 |
# unknown_return		>R						| 0257 |
DECLARE_VARIABLE	ARRAY_CLASS					| 0337 |
DECLARE_TYPE		ARRAY_CLASS,DEFINED				| 035D |
DECLARE_VARIABLE	PACKAGE_CLASS					| 0387 |
DECLARE_TYPE		PACKAGE_CLASS,DEFINED				| 038E |
DECLARE_VARIABLE	HEAP_ACCESS_CLASS,BY_ALLOCATION,WITH_VALUE	| 0396 |
DECLARE_TYPE		ACCESS_CLASS,DEFINED				| 03AD |
DECLARE_VARIABLE	ACCESS_CLASS,BY_ALLOCATION,WITH_VALUE		| 03B6 |

# XXX: Fra Allan
DECLARE_TYPE		DISCRETE_CLASS,DEFINED				| 03FE |
DECLARE_TYPE		RECORD_CLASS,DEFINED				| 032E |

zero_is_invalid_ins	>R						| 0000 |
push			abs,maybe_subprog				|0 0 0 0|0 0 0 0|1 0 0 1|0 0 1 1| abs				|
unknown_return		XXX,>R						|0 0 0 0|1 0 0 0| unknown	|

PUSH_STRING_INDEXED	pse						|0 0 0 0|0 0 0 0|1 0 0 1|0 0 0 1| pse				|
PUSH_STRING		pse						|0 0 0 0|0 0 0 0|1 0 0 1|0 0 1 0| pse				|
XXXa2			abs,literal					|0 0 0 0|0 0 0 0|1 0 1 0|0 0 1 0| abs				|
# XXX: a4 could be djnz or similar, always seem to jump backwards to a LOAD_TOP_0
XXXa4			abs,>JC						|0 0 0 0|0 0 0 0|1 0 1 0|0 1 0 0| abs				|
# XXX: a7 may be unconditional, (see fad6fc6b and dfb9935e)
XXXa7			abs,>JC						|0 0 0 0|0 0 0 0|1 0 1 0|0 1 1 1| abs				|
unknown_skip_cond	skip						|0 0 0 0|0 0 0 0|1 1 0 0|1 1 1 1|
LOAD_ENCACHED		eon						|0 0 0 0|0 0 0 0|1 1 1| eon	|
unknown_return		>R						|0 0 0 0|0 0 1 0|0 1 0 1|0 1 1 1|
DECLARE_SUBPROGRAM	subp,FOR_OUTHER_CALL,IS_VISIBLE,NOT_ELABORATED	|0 0 0 0|0 0 1 0|1 0 0 1|1 0 1 0| subp				|
DECLARE_SUBPROGRAM	subp,XXX					|0 0 0 0|0 0 1 0|1 0 0 1|1| how | subp				|
DECLARE_SUBPROGRAM	subp,FOR_OUTHER_CALL				|0 0 0 0|0 0 1 0|1 0 0 1|1 1 0 1| subp				|
DECLARE_SUBPROGRAM	subp,FOR_CALL					|0 0 0 0|0 0 1 0|1 0 0 1|1 1 1 1| subp				|
DECLARE_SUBPROGRAM	NULL_SUBPROGRAM					|0 0 0 0|0 0 1 0|1 0 1 0|0 0 0 0|
EXECUTE_IMMEDIATE	SET_VALUE_UNCHECKED_OP				|0 0 0 0|0 1 1 0|0 0|     x	|
EXECUTE_IMMEDIATE	REFERENCE_LEX_1_OP				|0 0 0 1|1 1 0 1|0 0 0 0| x	|
EXECUTE_PACKAGE_CLASS	FIELD_EXECUTE_OP				|0 0 0 1|1 0 0 0|0|       x	|
LOOP_INCREASING		pcrelneg,>JC					|0 0 1 1|1 1 1| pcrelneg	|
unknown_return		>R						|0 1 0 0|0 0 0 1|0 0 0| x	|
unknown_return		>R						|0 1 0 0|0 0 1 0|0 0 0| x	|
unknown_return		>R						|0 1 0 0|0 0 1 1|0 0 0| x	|
unknown_return		>R						|0 1 0 0|0 1 0 0|0 0 0| x	|
EXIT_SUBPROGRAM		>R						|0 1 0 0|0 1 0 1|0 0|   x	|
JUMP_CASE		case_max					|0 1 0 0|0 1 1|   case_max	|
SHORT_LITERAL		slit						|0 1 0 0|1| slit		|
jump_cond		pcrel,>JC					|0 1 1 0|1| pcrel		|
INDIRECT_LITERAL	pcrel,literal					|0 1 1 0|0| pcrel		|
JUMP			pcrel,>J					|0 1 1 1|1| pcrel		|
CALL			llvl,ldelta					|1 0 0| llvl  | ldelta		|
STORE_UNCHECKED		llvl,ldelta					|1 0 1| llvl  | ldelta		|
STORE			llvl,ldelta					|1 1 0| llvl  | ldelta		|
LOAD			llvl,ldelta					|1 1 1| llvl  | ldelta		|
unknown_instruction	-						| unknown			|
"""

class r1000_ins(assy.Instree_ins):
    ''' '''

    def assy_case_max(self):
        i = self['case_max']
        self += code.Jump(cond="default", to=self.hi)
        self.lang.m.set_line_comment(self.hi, "case default")
        for j in range(i + 1):
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

    def assy_literal(self):
        y = self.lang.literal(self.dstadr)
        return y.repr

    def assy_eon(self):
        # EncachedObjectNumber: 0..31
        v = self['eon']
        return "0x%x" % v

    def assy_slit(self):
        # Short_Literal_Value [-2**10..2**10-1]
        v = self['slit']
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


class r1000(assy.Instree_disass):
    def __init__(self, abits=16):
        super().__init__(
            "Rational 1000 Ada Processor",
            mem_word=16,
            ins_word=16,
            abits=abits,
            endian=">",
        )
        self.add_ins(r1000_desc, r1000_ins)
        self.verbatim += (
            'ACCESS_CLASS',
            'ALL_REFERENCE_OP',
            'ARRAY_CLASS',
            'AUGMENT_IMPORTS_OP',
            'BY_ALLOCATION',
            'CATENATE_OP',
            'CHECK_IN_TYPE_OP',
            'DEFINED',
            'FIELD_EXECUTE_OP',
            'FIELD_WRITE_OP',
            'FOR_CALL',
            'FOR_OUTHER_CALL',
            'HEAP_ACCESS_CLASS',
            'IS_VISIBLE',
            'NOT_ELABORATED',
            'NULL_SUBPROGRAM',
            'PACKAGE_CLASS',
            'REFERENCE_LEX_1_OP',
            'SET_VALUE_UNCHECKED_OP',
            'WITH_VALUE',
            'MODULE_CLASS',
            'WITH_CONSTRAINT',
            'ACTIVATE_OP',
            'DISCRETE',
            'RAISE_OP',
            'RERAISE_OP',
            'EXCEPTION_CLASS',
            'DISCRETE_CLASS',
            'RECORD_CLASS',
            'XXX',
        )
        self.literals = {}
        self.strtabs = {}

        self.subprograms = set()

    def subprogram(self, adr):
        if not self.m[adr]:
            print("ZERO at SUBPROGRAM+3 (0x%04x)" % adr)
            return
        if adr in self.subprograms:
            return
        assert adr & 3 == 3
        a0 = adr & ~3
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
