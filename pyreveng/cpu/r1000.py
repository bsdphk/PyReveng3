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

from pyreveng import assy, data, code, mem


r1000_desc = """

################
# Ref: FEH p269
INDIRECT_LITERAL	DISCRETE,0x20					| 6004 |
DECLARE_VARIABLE	DISCRETE,WITH_VALUE,WITH_CONSTRAINT		| 03EC |
CALL			0,0						| 8000 |

################
# Ref: GC1 p88
JUMP			1						| 7801	|
DECLARE_SUBPROGRAM	subp,FOR_OUTHER_CALL,IS_VISIBLE			|0 0 0 0|0 0 1 0|1 0 0 1|1 1 0 0| subp				|
CALL			2,2						| 8402 |
BREAK_UNCONDITIONAL	-						| 006F |
EXECUTE			EXCEPTION_CLASS,RAISE_OP			| 0100 |
INDIRECT_LITERAL	57						| 6039 |
INDIRECT_LITERAL	52						| 6034 |
EXECUTE			MODULE_CLASS,ACTIVATE_OP			| 020F |
CALL			3,3						| 8603 |

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
unknown_return		>R						| 0257 |
DECLARE_VARIABLE	ARRAY_CLASS					| 0337 |
DECLARE_TYPE		ARRAY_CLASS,DEFINED				| 035D |
DECLARE_VARIABLE	PACKAGE_CLASS					| 0387 |
DECLARE_TYPE		PACKAGE_CLASS,DEFINED				| 038E |
DECLARE_VARIABLE	HEAP_ACCESS_CLASS,BY_ALLOCATION,WITH_VALUE	| 0396 |
DECLARE_TYPE		ACCESS_CLASS,DEFINED				| 03AD |
DECLARE_VARIABLE	ACCESS_CLASS,BY_ALLOCATION,WITH_VALUE		| 03B6 |

EXIT_SUBPROGRAM		>R						|0 1 0 0|0 1 0 1|0 0 0| x	|
unknown_return		>R						|0 1 0 0|0 1 0 0|0 0 0| x	|
unknown_return		>R						|0 1 0 0|0 0 1 0|0 0 0| x	|
unknown_return		>R						|0 1 0 0|0 0 1 1|0 0 0| x	|

DECLARE_SUBPROGRAM	subp,FOR_OUTHER_CALL,IS_VISIBLE,NOT_ELABORATED	|0 0 0 0|0 0 1 0|1 0 0 1|1 0 1 0| subp				|
DECLARE_SUBPROGRAM	subp,FOR_OUTHER_CALL				|0 0 0 0|0 0 1 0|1 0 0 1|1 1 0 1| subp				|
DECLARE_SUBPROGRAM	subp,FOR_CALL					|0 0 0 0|0 0 1 0|1 0 0 1|1 1 1 1| subp				|
DECLARE_SUBPROGRAM	NULL_SUBPROGRAM					|0 0 0 0|0 0 1 0|1 0 1 0|0 0 0 0|
PUSH_STRING_EXTENDED	pse						|0 0 0 0 0 0 0 0 1 0 0 1 0 0 1 0| pse				|
PUSH_STRING_XXX		pse						|0 0 0 0 0 0 0 0 1 0 0 1 0 0 0 1| pse				|
LOAD_ENCACHED		eon						|0 0 0 0 0 0 0 0 1 1 1| eon	|
SHORT_LITERAL		slit						|0 1 0 0 1| slit		|
CALL			llvl,ldelta					|1 0 0| llvl  | ldelta		|
STORE_UNCHECKED		llvl,ldelta					|1 0 1| llvl  | ldelta		|
STORE			llvl,ldelta					|1 1 0| llvl  | ldelta		|
LOAD			llvl,ldelta					|1 1 1| llvl  | ldelta		|
LOAD_INCREASING		-						| 3FFB |
EXECUTE_IMMEDIATE	REFERENCE_LEX_1_OP				|0 0 0 1|1 1 0 1|0 0 0 0| x	|
EXECUTE_PACKAGE_CLASS	FIELD_EXECUTE_OP				|0 0 0 1|1 0 0 0|0|       x	|
EXECUTE_IMMEDIATE	SET_VALUE_UNCHECKED_OP				|0 0 0 0|0 1 1 0|0 0|     x	|
unknown_instruction	-						| unknown			|
"""

class r1000_ins(assy.Instree_ins):
   ''' '''

   def assy_subp(self):
       self.lang.subprogram(self['subp'])

   def assy_pse(self):
       v = self['pse']
       b1 = (v<<1) + self.lang.m[v]
       b2 = ((v + 1)<<1) + self.lang.m[v + 1]
       data.Const(self.lang.m, v, fmt="0x%%04x->0x%04x" % b1)
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
       self.lang.m.set_line_comment(v, t)
       return "@0x%x: %s" % (v, t)

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
        )

        self.subprograms = set()

    def subprogram(self, adr):
        if adr in self.subprograms:
            return
        assert adr & 3 == 3
        a0 = adr & ~3
        self.m.set_block_comment(a0, "SUBPROGRAM")
        data.Const(self.m, a0, fmt="0x%04x")
        self.m.set_line_comment(a0, "Address of begin")
        data.Const(self.m, a0+1, fmt="0x%04x")
        self.m.set_line_comment(a0+1, "Address of exception handler")
        data.Const(self.m, a0+2, fmt="0x%04x")
        self.m.set_line_comment(a0+1, "Number of locals")
        self.disass(adr)
        self.m.set_label(self.m[a0], "BODY_%04x" % a0)
        if self.m[a0] != adr:
            self.disass(self.m[a0])
