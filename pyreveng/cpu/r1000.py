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


r1000_desc = """

# Noteworthy segments:
#   ⟦120ea4603⟧ - has unreach{ed|able} subprograms: 0x25b, 0x28b, 0x4fb

#-----------------------
# Make places we get to, but do not handle grep(1)able
QQunknown_instruction	-						| unknown			|

#-----------------------
# Very helpful, but only hypothesis /phk
zero_is_invalid_ins	>R						|0 0 0 0|0 0 0 0|0 0 0 0|0 0 0 0|

#-----------------------
# gc44,0076								|0 0 0 0|0 0 0 0|0 0 0 0|0 1 1 1|
ACTION			BREAK_OPTIONAL					|0 0 0 0|0 0 0 0|0 0 0 0|0 1 1 1|

#-----------------------
# ⟦85b414c73⟧ 0x34e..34f
STORE_TOP		x						|0 0 0 0|0 0 0 0|0 1 0 0|0|0| x |

#-----------------------
# ⟦36a4ea3d7⟧
# seems to store result to local variable. Both stores are used for same variable in 05e7 and 05ee
QQu_Unknown_Store_1	x						|0 0 0 0|0 0 0 0|0 1 0 1|0| x   |
QQu_Unknown_Store_2	x						|0 0 0 0|0 0 0 0|0 1 0 1|1| x   |


#-----------------------
# gc88,0025								|0 0 0 0|0 0 0 0|0 1 1 0|1 1 1 1|
ACTION			BREAK_UNCONDITIONAL				|0 0 0 0|0 0 0 0|0 1 1 0|1 1 1 1|

#-----------------------
ACTION			PUSH_STRING_INDEXED,pse				|0 0 0 0|0 0 0 0|1 0 0 1|0 0 0 1| pse				|

#-----------------------
# gc43,0029		PUSH_STRING					|0 0 0 0|0 0 0 0|1 0 0 1|0 0 1 0|
ACTION			PUSH_STRING,pse					|0 0 0 0|0 0 0 0|1 0 0 1|0 0 1 0| pse				|

#-----------------------
QQupush93		subp						|0 0 0 0|0 0 0 0|1 0 0 1|0 0 1 1| subp				|

#-----------------------
# See for instance ⟦2009596b6⟧ @b4
PUSH_STRING_EXTENDED	abs,mark					|0 0 0 0|0 0 0 0|1 0 1 0|0 0 0 0| abs				|

#-----------------------
# See for instance ⟦b66a7252c⟧  /phk
PUSH_FLOAT_EXTENDED	abs,dbl						|0 0 0 0|0 0 0 0|1 0 1 0|0 0 0 1| abs				|

#-----------------------
PUSH_DISCRETE_EXTENDED	abs,literal					|0 0 0 0|0 0 0 0|1 0 1 0|0 0 1 0| abs				|

#-----------------------
# XXX: a4 could be djnz or similar, always seem to jump backwards to a LOAD_TOP_0
QQujump_a4		abs,>JC						|0 0 0 0|0 0 0 0|1 0 1 0|0 1 0 0| abs				|

#-----------------------
# XXX: See 9739edd68 @0xf2e
QQujump_a5		abs,>JC						|0 0 0 0|0 0 0 0|1 0 1 0|0 1 0 1| abs				|

#-----------------------
# XXX: See f1ef8a8ae @0x57d
QQujump_a6		abs,>JC						|0 0 0 0|0 0 0 0|1 0 1 0|0 1 1 0| abs				|

#-----------------------
# ⟦ed62618ed⟧ @0x1cc confirms this is unconditional /phk
JUMP			abs,>J						|0 0 0 0|0 0 0 0|1 0 1 0|0 1 1 1| abs				|

#-----------------------
# gc43,003d								|0 0 0 0|0 0 0 0|1 0 1 1|1 0 1 1|
ACTION			SIGNAL_COMPLETION,>R				|0 0 0 0|0 0 0 0|1 0 1 1|1 0 1 1|

#-----------------------
# gc43,003c 		SIGNAL_ACTIVATED				|0 0 0 0|0 0 0 0|1 0 1 1|1 1 0 0|
ACTION			SIGNAL_ACTIVATED				|0 0 0 0|0 0 0 0|1 0 1 1|1 1 0 0|

#-----------------------
# gc42,000d		ACCEPT_ACTIVATION				|0 0 0 0|0 0 0 0|1 0 1 1|1 1 1 1|
ACTION			ACCEPT_ACTIVATION				|0 0 0 0|0 0 0 0|1 0 1 1|1 1 1 1|

#-----------------------
# gc42,000f		ELABORATE_SUBPROGRAM				|0 0 0 0|0 0 0 0|1 1 0 0|0 1 1 1|
ACTION			ELABORATE_SUBPROGRAM				|0 0 0 0|0 0 0 0|1 1 0 0|0 1 1 1|

#-----------------------
# 467 times followed by 0x0000
# many times last instruction before TRAP entry point /phk
QQunknown_return_ca	>R						|0 0 0 0|0 0 0 0|1 1 0 0|1 0 1 0|

#-----------------------
# ⟦ec043f33f⟧ @0x5f has this followed by a two-word instruction.
# May be conditional return? /phk
QQunknown_jump_cond	>RC						|0 0 0 0|0 0 0 0|1 1 0 0|1 1 1 1|

#-----------------------
# gc43,00027		0						|0 0 0 0|0 0 0 0|1 1 0 1|1 0 0 0|
# /aa
LOAD_TOP		x						|0 0 0 0|0 0 0 0|1 1 0 1|1|0| x |

#-----------------------
# feh269,1c		Value_02					|0 0 0 0|0 0 0 0|1 1 1 0|0 0 1 0|
# gc44,0046		1						|0 0 0 0|0 0 0 0|1 1 1 0|0 0 0 1|
# gc43,0036		2						|0 0 0 0|0 0 0 0|1 1 1 0|0 0 1 0|
LOAD_ENCACHED		eon						|0 0 0 0|0 0 0 0|1 1 1| eon	|

#-----------------------
# g88,001e		EXCEPTION_CLASS,RAISE_OP 			|0 0 0 0|0 0 0 1|0 0 0 0|0 0 0 0|
# g28, location 4 = raise instruction					|0 0 0 0|0 0 0 1|0 0 0 0|0 0 0 0|
EXECUTE			EXCEPTION_CLASS,RAISE_OP,>R			|0 0 0 0|0 0 0 1|0 0 0 0|0 0 0 0|

#-----------------------
# This is a guess, based on it occuring right before 0x0000
# and being subsequent to RAISE_OP (0x0100) in the Machine_Code.ada
# /phk
EXECUTE			EXCEPTION_CLASS,RERAISE_OP,>R			|0 0 0 0|0 0 0 1|0 0 0 0|0 0 0 1|

#-----------------------
# ⟦85b414c73⟧ @0x357
IS_NUMERIC_ERROR_OP	-						|0 0 0 0|0 0 0 1|0 0 0 0|1 1 0 1|

#-----------------------
# ⟦36a4ea3d7⟧ @0x0366	when Calendar.Time_Error =>
QQu_Is_Equal_Exception	-						|0 0 0 0|0 0 0 1|0 0 0 0|1 1 1 1|


#-----------------------
# ⟦36a4ea3d7⟧ @0x68d	Name : constant String := Months'Image (Month);
# Used for Image function, followed by 1c00 or 1c01
QQuImage		-						|0 0 0 0|0 0 0 1|0 0 0 1|1 1 0 0|

#-----------------------
# ⟦36a4ea3d7⟧ @0x000d	type Years  is new Calendar.Year_Number (in spec)
# ⟦cb8e43375⟧ @0x0023   Pi : Float (in spec)
QQu_Execute_make_visible_op	-					|0 0 0 0|0 0 0 1|0 0 1 0|1 0 0 1|

#-----------------------
# ⟦36a4ea3d7⟧ @0x68d	return Calendar."=" (Date, Nil);
QQu_is_equal_discrete	-						|0 0 0 0|0 0 0 1|0 0 1 0|1 1 1 1|

#-----------------------
# ⟦cb8e43375⟧ @0x7c
QQu_float_great_equal_zero	-					|0 0 0 0|0 0 0 1|0 1 0 0|1 0 1 0|

#-----------------------
# ⟦85b414c73⟧ @0x349
QQu_float_below_zero	-						|0 0 0 0|0 0 0 1|0 1 0 0|1 0 1 1|

#-----------------------
# ⟦85b414c73⟧ @0x337
QQu_float_greater_zero	-						|0 0 0 0|0 0 0 1|0 1 0 0|1 1 0 0|

#-----------------------
# ⟦36a4ea3d7⟧, @0x05bf/aa	T  : Time    := Get_Time;
# May be EXECUTE RECORD_CLASS,STRUCTURE_WRITE_OP
QQuWrite_RECORD		-						|0 0 0 0|0 0 0 1|0 1 1 1|1 1 0 1|

#-----------------------
# ⟦36a4ea3d7⟧ @0x37d   return Date = Nil
QQu_is_equal_record     -                                               |0 0 0 0|0 0 0 1|0 1 1 1|1 1 1 1|

#-----------------------
# ⟦36a4ea3d7⟧, @0x01a7/aa	Write full 2 dim array
# May be EXECUTE MATRIX_CLASS,STRUCTURE_WRITE_OP
QQuWrite_Full_Matrix	-						|0 0 0 0|0 0 0 1|1 0 1 0|0 1 0 0|

#-----------------------
# ⟦36a4ea3d7⟧, @0x0132/aa	Write 2 dim array value
# May be EXECUTE MATRIX_CLASS,FIELD_WRITE_OP
QQuWrite_Matrix_element	-						|0 0 0 0|0 0 0 1|1 0 1 0|0 1 1 0|

#-----------------------
# gc44,005f		VECTOR_CLASS,CHECK_IN_TYPE_OP			|0 0 0 0|0 0 0 1|1 1 0 0|0 0 1 1|
EXECUTE			VECTOR_CLASS,CHECK_IN_TYPE_OP			|0 0 0 0|0 0 0 1|1 1 0 0|0 0 1 1|

#-----------------------
# ⟦36a4ea3d7⟧, @0x06ff	Load previous result?
# Used after call to CATENATE_OP or call to Image function returning string
QQuLoad_Vector_Result	-						|0 0 0 0|0 0 0 1|1 1 0 0|1 0 1 1|

#-----------------------
# gc44,007c		VECTOR_CLASS,CATENATE_OP			|0 0 0 0|0 0 0 1|1 1 0 0|1 1 0 0|
# gc45,008f		VECTOR_CLASS,CATENATE_OP			|0 0 0 0|0 0 0 1|1 1 0 0|1 1 0 0|
EXECUTE			VECTOR_CLASS,CATENATE_OP			|0 0 0 0|0 0 0 1|1 1 0 0|1 1 0 0|

#-----------------------
# ⟦36a4ea3d7⟧, @0x06a0	return Name (Name'First .. Name'First + 2);
# Used to get a subarray
QQuEXECUTE		VECTOR_CLASS,SUBARRAY_OP			|0 0 0 0|0 0 0 1|1 1 0 0|1 1 1 1|

#-----------------------
# ⟦36a4ea3d7⟧, @0x01e4
# Used after writing all fields in vector
QQuEXECUTE		VECTOR_CLASS,STRUCTURE_WRITE_OP			|0 0 0 0|0 0 0 1|1 1 0 1|0 1 0 0|


#-----------------------
# gc44,006b		VECTOR_CLASS,FIELD_WRITE_OP			|0 0 0 0|0 0 0 1|1 1 0 1|0 1 1 0|
# gc45,00a6		VECTOR_CLASS,FIELD_WRITE_OP			|0 0 0 0|0 0 0 1|1 1 0 1|0 1 1 0|
EXECUTE			VECTOR_CLASS,FIELD_WRITE_OP			|0 0 0 0|0 0 0 1|1 1 0 1|0 1 1 0|

#-----------------------
# ⟦93b91846e⟧, @0x00fa		Char := S (Position);
# read vector value
QQuEXECUTE		VECTOR_CLASS,FIELD_READ_OP			|0 0 0 0|0 0 0 1|1 1 0 1|0 1 1 1|

#-----------------------
# ⟦93b91846e⟧, @0x00d5		Last := S'Last;
QQuExecute_vector_class_last	-					|0 0 0 0|0 0 0 1|1 1 0 1|1 1 0 0|

#-----------------------
# ⟦36a4ea3d7⟧, @0x696, 		return Name (Name'First .. Name'First + 2);
QQuExecute_vector_class_first	-					|0 0 0 0|0 0 0 1|1 1 0 1|1 1 0 1|

#-----------------------
# gc43,0026		MODULE_CLASS,AUGMENT_IMPORTS_OP			|0 0 0 0|0 0 1 0|0 0 0 0|1 1 1 0|
EXECUTE			MODULE_CLASS,AUGMENT_IMPORTS_OP			|0 0 0 0|0 0 1 0|0 0 0 0|1 1 1 0|

#-----------------------
EXECUTE			MODULE_CLASS,ACTIVATE_OP			|0 0 0 0|0 0 1 0|0 0 0 0|1 1 1 1|

#-----------------------
# gc45,00a5		HEAP_ACCESS_CLASS,ALL_REFERENCE_OP		|0 0 0 0|0 0 1 0|0 0 0 1|0 1 1 1|
EXECUTE			HEAP_ACCESS_CLASS,ALL_REFERENCE_OP		|0 0 0 0|0 0 1 0|0 0 0 1|0 1 1 1|

#-----------------------
# ⟦93b91846e⟧ @0x0149	if Ptr.Kind = Number_Kind then
QQu_EXECUTE		HEAP_ACCESS_CLASS,FIELD_REFERENCE_OP		|0 0 0 0|0 0 1 0|0 0 1 0|0 1 1 1|


#-----------------------
# ⟦cb8e43375⟧ @0xc4
ROUND_TO_DISCRETE_OP	-						|0 0 0 0|0 0 1 0|0 0 1 1|0 1 0 1|

#-----------------------
# ⟦cb8e43375⟧ @0xc7
CONVERT_FROM_DISCRETE_OP -						|0 0 0 0|0 0 1 0|0 0 1 1|0 1 1 1|

#-----------------------
# ⟦85b414c73⟧ @0x463 looks like a classical polynomial expansion
FLOAT_**		-						|0 0 0 0|0 0 1 0|0 0 1 1|1 0 0 1|
FLOAT_DIVIDE		-						|0 0 0 0|0 0 1 0|0 0 1 1|1 0 1 0|
FLOAT_MULTIPLY		-						|0 0 0 0|0 0 1 0|0 0 1 1|1 0 1 1|
FLOAT_SUBTRACT		-						|0 0 0 0|0 0 1 0|0 0 1 1|1 1 0 0|
FLOAT_ADD		-						|0 0 0 0|0 0 1 0|0 0 1 1|1 1 0 1|
FLOAT_ABS		-						|0 0 0 0|0 0 1 0|0 0 1 1|1 1 1 0|
FLOAT_NEGATE		-						|0 0 0 0|0 0 1 0|0 0 1 1|1 1 1 1|

#-----------------------
# ⟦cb8e43375⟧ @0xb5
QQu_float_less_equal_than	-					|0 0 0 0|0 0 1 0|0 1 0 0|0 0 1 0|

#-----------------------
# ⟦cb8e43375⟧ @0xa5
QQu_float_greater_equal_than	-					|0 0 0 0|0 0 1 0|0 1 0 0|0 0 1 1|

QQu_float_less_than	-						|0 0 0 0|0 0 1 0|0 1 0 0|0 1 0 0|
QQu_float_greater_than	-						|0 0 0 0|0 0 1 0|0 1 0 0|0 1 0 1|

#-----------------------
# ⟦cb8e43375⟧ @0xc9
QQu_float_equal_to	-						|0 0 0 0|0 0 1 0|0 1 0 0|0 1 1 1|

#-----------------------
# 196 times followed by 0x0000
# a dozen times right before TRAP entry /phk
QQunknown_return_257	>R						|0 0 0 0|0 0 1 0|0 1 0 1|0 1 1 1|

#-----------------------
# ⟦cb8e43375⟧ @0x54
# ⟦36a4ea3d7⟧ 0x048f	May be Convert_Duration_To_Int 	Rest : Integer32 := Integer32 (D) * Milliseconds_Per_Second
QQu_CONVERT_TO_FLOAT	-						|0 0 0 0|0 0 1 0|0 1 0 1|1 1 1 0|

#-----------------------
# /aa (2fa0095f7 1c9e)
QQuEXECUTE		BELOW_BOUND					|0 0 0 0|0 0 1 0|0 1 1 0|0 0 0 0|

#-----------------------
# /aa (3bf0c159 0236)
QQuEXECUTE		IN_RANGE					|0 0 0 0|0 0 1 0|0 1 1 0|0 0 1 0|

#-----------------------
# /aa (36a4ea3d7 008b)		type Number_Array is array (Positive range <>) of Natural;
# May be EXECUTE		BOUNDS_OP
QQuDefine_Array_Full_Range	-					|0 0 0 0|0 0 1 0|0 1 1 0|0 1 1 0|

#-----------------------
# /aa (3f2fe70c1 002b)		type Width_List is array (Column_Index) of Natural;
QQuDefine_Array_subtype_Range	-					|0 0 0 0|0 0 1 0|0 1 1 0|1 0 0 1|

#-----------------------
# /aa (3bf0c159 00d9)
QQuEXECUTE		EXPONENTIATE					|0 0 0 0|0 0 1 0|0 1 1 0|1 1 0 1|

#-----------------------
# ⟦cb8e43375⟧ @0x100 /phk  not sure.
QQu_int_mod		-						|0 0 0 0|0 0 1 0|0 1 1 0|1 1 1 0|

#-----------------------
# ⟦36a4ea3d7⟧ @0x02ed 		Total_Seconds := Total_Seconds rem Seconds_Per_Hour;
QQu_int_rem             -                                               |0 0 0 0|0 0 1 0|0 1 1 0|1 1 1 1|

#-----------------------
# ⟦cb8e43375⟧ @0x107 /phk
QQu_int_divide		-						|0 0 0 0|0 0 1 0|0 1 1 1|0 0 0 0|

#-----------------------
# ⟦cb8e43375⟧ @0x103 /phk  not sure.
QQu_int_multiply	-						|0 0 0 0|0 0 1 0|0 1 1 1|0 0 0 1|

#-----------------------
# ⟦cb8e43375⟧ @0x109 /phk  not sure.
QQu_int_subtract	-						|0 0 0 0|0 0 1 0|0 1 1 1|0 0 1 0|

#-----------------------
# ⟦cb8e43375⟧ @0x113 /phk  not sure.
QQu_int_add		-						|0 0 0 0|0 0 1 0|0 1 1 1|0 0 1 1|

#-----------------------
# ⟦85b414c73⟧ @0x171 /phk AND ?
QQu_float_neg		-						|0 0 0 0|0 0 1 0|0 1 1 1|0 1 0 1|

#-----------------------
# ⟦85b414c73⟧ @0x8e  integer AND ?
QQu_integer_and		-						|0 0 0 0|0 0 1 0|0 1 1 1|1 0 0 1|

#-----------------------
#  ⟦36a4ea3d7⟧, @0x00cc		if Total_Seconds < Integer32 (Seconds_Per_Half_Day) then
QQu_less_than		-						|0 0 0 0|0 0 1 0|0 1 1 1|1 1 0 0|

#-----------------------
#  ⟦93b91846e⟧, @0x00ce		if Position <= S'Last then
QQu_less_equal		-						|0 0 0 0|0 0 1 0|0 1 1 1|1 0 1 0|

#-----------------------
# /aa (3bf0c159 00da)
QQuEXECUTE		MINUS						|0 0 0 0|0 0 1 0|0 1 1 1|1 1 0 1|

#-----------------------
# ⟦37717da67⟧ @0x5ce4 indicates this takes an extension /phk
QQunknown		subp						|0 0 0 0|0 0 1 0|1 0 0 1|1 0 0 1| subp				|

#-----------------------
# gc42,000b		FOR_OUTER_CALL,IS_VISIBLE,NOT_ELABORATED	|0 0 0 0|0 0 1 0|1 0 0 1|1 0 1 0|
DECLARE_SUBPROGRAM	subp,FOR_OUTER_CALL,IS_VISIBLE,NOT_ELABORATED	|0 0 0 0|0 0 1 0|1 0 0 1|1 0 1 0| subp				|

#-----------------------
# ⟦a88379b5f⟧ indicates this takes an extension # /phk
QQudeclare_subprogram	x						|0 0 0 0|0 0 1 0|1 0 0 1|1 0 1 1| x				|

#-----------------------
# gc87,000b		subp,FOR_OUTER_CALL,IS_VISIBLE			|0 0 0 0|0 0 1 0|1 0 0 1|1 1 0 0| subp				|
DECLARE_SUBPROGRAM	subp,FOR_OUTER_CALL,IS_VISIBLE			|0 0 0 0|0 0 1 0|1 0 0 1|1 1 0 0| subp				|

#-----------------------
# gc43,0038		FOR_OUTER_CALL					|0 0 0 0|0 0 1 0|1 0 0 1|1 1 0 1|
DECLARE_SUBPROGRAM	subp,FOR_OUTER_CALL				|0 0 0 0|0 0 1 0|1 0 0 1|1 1 0 1| subp				|

#-----------------------
# ⟦89b72b217⟧ @0x2abd indicates this takes an extension # /phk
QQudeclare_subprogram	subp						|0 0 0 0|0 0 1 0|1 0 0 1|1 1 1 0| subp				|

#-----------------------
# gc44,0077		FOR_CALL					|0 0 0 0|0 0 1 0|1 0 0 1|1 1 1 1|
DECLARE_SUBPROGRAM	subp,FOR_CALL					|0 0 0 0|0 0 1 0|1 0 0 1|1 1 1 1| subp				|

#-----------------------
# gc43,001e		NULL_SUBPROGRAM					|0 0 0 0|0 0 1 0|1 0 1 0|0 0 0 0|
DECLARE_SUBPROGRAM	NULL_SUBPROGRAM					|0 0 0 0|0 0 1 0|1 0 1 0|0 0 0 0|

#-----------------------
# See ⟦657d85b18⟧ @0x12d
# See ⟦eecee3432⟧ @0x2f2/phk
# See ⟦826a261d9⟧ @0x8a7/phk
QQunknown_2cf		-						|0 0 0 0|0 0 1 0|1 1 0 0|1 1 1 1|

#-----------------------
# (3f2fe70c1, 004b)/aa	type An_Item (Subitem_Length : Natural) is...  (completing an incomplete variant record)
QQuDECLARE_TYPE		VARIANT_RECORD_CLASS				|0 0 0 0|0 0 1 1|0 0 0 0|0 1 1 1|

#-----------------------
# (3f2fe70c1, 0039)/aa		type An_Item (Subitem_Length : Natural); (incomplete variant record)
QQuDECLARE_TYPE		VARIANT_RECORD_CLASS,INCOMPLETE			|0 0 0 0|0 0 1 1|0 0 0 1|1 0 0 0|

#-----------------------
# /aa
QQuDECLARE_TYPE		VARIANT_RECORD_CLASS				|0 0 0 0|0 0 1 1|0 0 0 1|1 1 1 0|

#-----------------------
# ⟦36a4ea3d7⟧, @0x00fa/aa	Null_Time : constant Time := Time'(Year => Years'First...
QQuDECLARE_VARIABLE	RECORD_CLASS					|0 0 0 0|0 0 1 1|0 0 1 0|0 0 1 0|

#-----------------------
# (3f2fe70c1, 0067)/aa	type Line is record...	Completing an incomplete record type
QQuDECLARE_TYPE		RECORD_CLASS,DEFINED				|0 0 0 0|0 0 1 1|0 0 1 0|0 1 1 0|

#-----------------------
# (3f2fe70c1, 0054)/aa	type Line;	Incomplete record type in body
QQuDECLARE_TYPE		RECORD_CLASS,DEFINED,INCOMPLETE			|0 0 0 0|0 0 1 1|0 0 1 0|1 0 1 0|

#-----------------------
# /aa
QQuDECLARE_TYPE		RECORD_CLASS,DEFINED				|0 0 0 0|0 0 1 1|0 0 1 0|1 1 1 0|

#-----------------------
# ⟦36a4ea3d7⟧, @0x012c	Military_Hour : constant array (Sun_Positions, Hours) of Military_Hours :=
QQu_DECLARE_VARIABLE_tmp_val	ARRAY_CLASS				|0 0 0 0|0 0 1 1|0 0 1 1|0 1 0 1|

#-----------------------
# gc44,004b		ARRAY_CLASS					|0 0 0 0|0 0 1 1|0 0 1 1|0 1 1 1|
DECLARE_VARIABLE	ARRAY_CLASS					|0 0 0 0|0 0 1 1|0 0 1 1|0 1 1 1|

#-----------------------
# ⟦36a4ea3d7⟧, @0x008f/aa	type Number_Array is array (Positive range <>) of Natural; (in package body)
QQuDECLARE_TYPE		ARRAY_CLASS,UNCONSTRAINED			|0 0 0 0|0 0 1 1|0 1 0 1|0 0 0 0|

#-----------------------
# ⟦3f2fe70c1⟧, @0x001f/aa	type Field_List is array (Integer range <>) of Positive; (in package spec)
QQuDECLARE_TYPE		ARRAY_CLASS,UNCONSTRAINED,IS_VISIBLE		|0 0 0 0|0 0 1 1|0 1 0 1|0 0 0 1|

#-----------------------
# gc44,0049		ARRAY_CLASS,DEFINED				|0 0 0 0|0 0 1 1|0 1 0 1|1 1 0 1|
DECLARE_TYPE		ARRAY_CLASS,DEFINED				|0 0 0 0|0 0 1 1|0 1 0 1|1 1 0 1|

#-----------------------
# gc43,0020		PACKAGE_CLASS					|0 0 0 0|0 0 1 1|1 0 0 0|0 1 1 1|
DECLARE_VARIABLE	PACKAGE_CLASS					|0 0 0 0|0 0 1 1|1 0 0 0|0 1 1 1|

#-----------------------
# gc43,001f		PACKAGE_CLASS,DEFINED				|0 0 0 0|0 0 1 1|1 0 0 0|1 1 1 0|
DECLARE_TYPE		PACKAGE_CLASS,DEFINED				|0 0 0 0|0 0 1 1|1 0 0 0|1 1 1 0|

#-----------------------
# gc44,0074		HEAP_ACCESS_CLASS,BY_ALLOCATION,WITH_VALUE	|0 0 0 0|0 0 1 1|1 0 0 1|0 1 1 0|
DECLARE_VARIABLE	HEAP_ACCESS_CLASS,BY_ALLOCATION,WITH_VALUE	|0 0 0 0|0 0 1 1|1 0 0 1|0 1 1 0|

#-----------------------
# gc44,0052		HEAP_ACCESS_CLASS,DEFINED			|0 0 0 0|0 0 1 1|1 0 1 0|1 1 0 1|
DECLARE_TYPE		HEAP_ACCESS_CLASS,DEFINED			|0 0 0 0|0 0 1 1|1 0 1 0|1 1 0 1|

#-----------------------
# gc44,0061		ACCESS_CLASS,BY_ALLOCATION,WITH_VALUE		|0 0 0 0|0 0 1 1|1 0 1 1|0 1 1 0|
DECLARE_VARIABLE	ACCESS_CLASS,BY_ALLOCATION,WITH_VALUE		|0 0 0 0|0 0 1 1|1 0 1 1|0 1 1 0|

#-----------------------
# (3f2fe70c1, 0033)/aa		type A_String    is access String; (in body)
QQu_DECLARE_TYPE	ACCESS_CLASS,DEFINED                            |0 0 0 0|0 0 1 1|1 1 0 1|0 0 1 1|

#-----------------------
# gc44,004f		ACCESS_CLASS,DEFINED				|0 0 0 0|0 0 1 1|1 1 0 1|0 1 0 1|
#			Type PA is access A; (in procedure)
DECLARE_TYPE		ACCESS_CLASS,DEFINED				|0 0 0 0|0 0 1 1|1 1 0 1|0 1 0 1|

#-----------------------
# ⟦85b414c73⟧ @0x48 /aa
DECLARE_VARIABLE	FLOAT_CLASS					|0 0 0 0|0 0 1 1|1 1 0 1|1 0 0 0|

#-----------------------
# ⟦cb8e43375⟧ @0xe /aa	(In visible part of spec) Zero : Float = ...
DECLARE_VARIABLE	FLOAT_CLASS,WITH_VALUE,IS_VISIBLE		|0 0 0 0|0 0 1 1|1 1 0 1|1 0 1 1|

#-----------------------
# ⟦85b414c73⟧ @0x57 /aa
DECLARE_VARIABLE	FLOAT_CLASS,WITH_VALUE				|0 0 0 0|0 0 1 1|1 1 0 1|1 1 1 1|

#-----------------------
# ⟦36a4ea3d7⟧ @0x02a0 /aa	Junk, Min, Sec : Integer32;
QQuDECLARE_VARIABLE	DISCRETE					|0 0 0 0|0 0 1 1|1 1 1 0|1 0 0 1|

#-----------------------
# feh269,1d		DISCRETE,WITH_VALUE,WITH_CONSTRAINT		|0 0 0 0|0 0 1 1|1 1 1 0|1 1 0 0|
DECLARE_VARIABLE	DISCRETE,WITH_VALUE,WITH_CONSTRAINT		|0 0 0 0|0 0 1 1|1 1 1 0|1 1 0 0|

#-----------------------
# ⟦36a4ea3d7⟧ @0x05c3 /aa      Hr : Natural := Natural (H);
QQuDECLARE_VARIABLE	DISCRETE_CLASS,WITH_VALUE			|0 0 0 0|0 0 1 1|1 1 1 1|0 0 0 1|

#-----------------------
# ⟦36a4ea3d7⟧ @0297/aa 	subtype Region is Integer range 0 .. 3;
QQuDECLARE_TYPE		DISCRETE_CLASS,WITH_CONSTRAINT			|0 0 0 0|0 0 1 1|1 1 1 1|1 0 0 0|

#-----------------------
# /aa
QQuDECLARE_TYPE		DISCRETE_CLASS,DEFINED				|0 0 0 0|0 0 1 1|1 1 1 1|1 0 0 1|

#-----------------------
# (93b91846e, 0025)/aa		type Kind_Value is (Day, Hour, Minute, Second, Millisecond, Number); (in procedure)
QQuDECLARE_TYPE		DISCRETE_CLASS,DEFINED,ENUM			|0 0 0 0|0 0 1 1|1 1 1 1|1 1 0 1|

#-----------------------
# /aa
QQuDECLARE_TYPE		DISCRETE_CLASS,DEFINED,ENUM			|0 0 0 0|0 0 1 1|1 1 1 1|1 1 1 0|

#-----------------------
# g43,0037		SET_VALUE_UNCHECKED_OP,33			|0 0 0 0|0 1 1 0|0 0 1 0|0 0 0 1|
EXECUTE_IMMEDIATE	SET_VALUE_UNCHECKED_OP,x			|0 0 0 0|0 1 1 0|0 0|     x	|

#-----------------------
# ⟦28af5d09d⟧ @0xd2
# ⟦36a4ea3d7⟧ @0x0c9e/aa	May be raise Constraint_Error
QQu_return_imm_exception	s8,>R						|0 0 0 0|1 0 0 0| 	s8	|

#-----------------------
# ⟦cb8e43375⟧ @0x108
# ⟦85b414c73⟧ @0x0170 /phk
BINARY_SCALE_OP		s8						|0 0 0 0|1 0 0 1|	s8	|

#-----------------------
# /aa (3bf0c159 00da )
QQu_add_imm		s8						|0 0 0 0|1 0 1 0|	s8	|

#-----------------------
# See ⟦a53169a08⟧ @0x64, some kind of comparison/test
# Almost always followed by 0x70xx conditional jump /phk
QQu_comparison_1	s8						|0 0 0 0|1 0 1 1|	s8	|

#-----------------------
# See ⟦657fb377c⟧ @0x1d7c, some kind of comparison/test
# Almost always followed by 0x70xx or 0x68xx conditional jump /phk
# Maybe Greater_Equal_Op  ⟦36a4ea3d7⟧ @0x0609   if Months'Pos (T.Month) >= 3 then
QQu_comparison_2	s8						|0 0 0 0|1 1 0 0| 	s8	|

#-----------------------
# ⟦cb8e43375⟧ @0x144
QQu_int_less_than	s8						|0 0 0 0|1 1 0 1|	s8	|

#-----------------------
# ⟦36a4ea3d7⟧ @0x0344	if Date.Hour /= 12 then
QQu_int_not_equal	s8						|0 0 0 0|1 1 1 0|       s8      |

#-----------------------
# ⟦36a4ea3d7⟧ @0x06bc	if Time_Style = Ada then
QQu_int_is_equal	s8						|0 0 0 0|1 1 1 1|       s8      |

#-----------------------
# g43,002c		PACKAGE_CLASS,FIELD_EXECUTE_OP,13		|0 0 0 1|1 0 0 0|0 0 0 0|1 1 0 1|
# g44,0071		PACKAGE_CLASS,FIELD_EXECUTE_OP,17		|0 0 0 1|1 0 0 0|0 0 0 1|0 0 0 1|
# g45,008e		PACKAGE_CLASS,FIELD_EXECUTE_OP,24		|0 0 0 1|1 0 0 0|0 0 0 1|1 0 0 0|
# g45,0091		PACKAGE_CLASS,FIELD_EXECUTE_OP,100		|0 0 0 1|1 0 0 0|0 1 1 0|0 1 0 0|
EXECUTE			PACKAGE_CLASS,FIELD_EXECUTE_OP,x		|0 0 0 1|1 0 0 0|0|       x	|

#-----------------------
# g88,0032		PACKAGE_CLASS,FIELD_REFERENCE_OP,13		|0 0 0 1|1 0 0 1|0 0 0 0|1 1 0 1|
EXECUTE			PACKAGE_CLASS,FIELD_REFERENCE_OP,x		|0 0 0 1|1 0 0 1|0|       x     |


#-----------------------
# ⟦cb8e43375⟧ @0x10b
QQu_field_store		x						|0 0 0 1|1 0 1 0|0|       x	|

#-----------------------
# ⟦cb8e43375⟧ @0xfe
QQu_field_load		x						|0 0 0 1|1 0 1 1|0|       x	|

#-----------------------
# ⟦36a4ea3d7⟧ @0x068e
QQu_structure_Store	x						|0 0 0 1|1 1 0 0|0|       x     |

#-----------------------
# g42,000e		REFERENCE_LEX_1_OP,13				|0 0 0 1|1 1 0 1|0 0 0 0|1 1 0 1|
EXECUTE_IMMEDIATE	REFERENCE_LEX_1_OP,x				|0 0 0 1|1 1 0 1|0|       x	|

#-----------------------
# ⟦36a4ea3d7⟧ @0x00fa-010f, write record field values
QQu_EXECUTE		RECORD_CLASS,FIELD_WRITE_OP,x			|0 0 1 1|1 0 0 0|0|       x     |

#-----------------------
# ⟦36a4ea3d7⟧ @0x0608, read record field values in function Day_Of_Week
QQu_EXECUTE		RECORD_CLASS,FIELD_READ_OP,x			|0 0 1 1|1 1 0 0|0|       x     |

#-----------------------
# g44,005d		-5						|0 0 1 1|1 1 1 1|1 1 1 1|1 0 1 1|
LOOP_INCREASING		pcrelneg,>JC					|0 0 1 1|1 1 1| pcrelneg	|

#-----------------------
# phk
QQunknown_return_1	>R,x						|0 1 0 0|0 0 0 1|0 0 0| x	|

#-----------------------
# phk
QQunknown_return_2	>R,x						|0 1 0 0|0 0 1 0|0 0 0| x	|

#-----------------------
# phk
QQunknown_return_3	>R,x						|0 1 0 0|0 0 1 1|0 0 0| x	|

#-----------------------
# phk
QQunknown_return_4	>R,x						|0 1 0 0|0 1 0 0|0 0 0| x	|

#-----------------------
# g43,002d		1						|0 1 0 0|0 1 0 1|0 0 0 0|0 0 0 1|
# g44,0080		2						|0 1 0 0|0 1 0 1|0 0 0 0|0 0 1 0|
# feh269,1e		1						|0 1 0 0|0 1 0 1|0 0 0 0|0 0 0 1|
EXIT_SUBPROGRAM		>R						|0 1 0 0|0 1 0 1|0 0|   x	|

#-----------------------
# ⟦fad6fc6ba⟧ limits the argument to 8 bits
# /phk
JUMP_CASE		case_max					|0 1 0 0|0 1 1|0| case_max	|

#-----------------------
# g43,001b		0						|0 1 0 0|1 0 0 0|0 0 0 0 0 0 0 0|
# g43,0024		3						|0 1 0 0|1 0 0 0|0 0 0 0 0 0 1 1|
# g44,0045		10						|0 1 0 0|1 0 0 0|0 0 0 0 1 0 1 1|
# g44,004e		24						|0 1 0 0|1 0 0 0|0 0 0 1 1 0 0 0|
SHORT_LITERAL		slit						|0 1 0 0|1| slit		|

#-----------------------
# ⟦85b414c73⟧ (sin/cos/tan) @0x42b...
PUSH_DOUBLE		pcrel,dbl					|0 1 0 1|1| pcrel		|

#-----------------------
# g88,0026		Discrete_Class,57				|0 1 1 0|0 0 0 0|0 0 1 1 1 0 0 1|
# g88,0027		Discrete_Class,52				|0 1 1 0|0 0 0 0|0 0 1 1 0 1 0 0|
# g88,002d		Discrete_Class,42				|0 1 1 0|0 0 0 0|0 0 1 0 1 0 1 0|
# feh269,1b		Discrete, #0020					|0 1 1 0|0 0 0 0|0 0 0 0 0 1 0 0|
INDIRECT_LITERAL	pcrel,literal					|0 1 1 0|0| pcrel		|

#-----------------------
QQujump_if_not		pcrel,>JC					|0 1 1 0|1| pcrel		|

#-----------------------
# /aa Sandsynligvis jump_zero
# ⟦85b414c73⟧ @0x326
QQu_jump_non_zero	pcrel,>JC					|0 1 1 1|0| pcrel		|

#-----------------------
# XXX: Not obvious if "1" and "2" is count of extension words or if and why those words are jumped over
# g88,001a		1						|0 1 1 1|1 0 0 0|0 0 0 0|0 0 0 1|
# g88,0047		2						|0 1 1 1|1 0 0 0|0 0 0 0|0 0 1 0|
JUMP			pcrel,>J					|0 1 1 1|1| pcrel		|

#-----------------------
# g44,007d		1,15						|1 0 0 0|0 0 1|0 0 0 0 0 1 1 1 1|
# g44,007f		2,9						|1 0 0 0|0 1 0|0 0 0 0 0 1 0 0 1|
# feh269,22		0						|1 0 0 0|0 0 0|0 0 0 0 0 0 0 0 0|
CALL			llvl,ldelta					|1 0 0| llvl  | ldelta		|

#-----------------------
# g45,009d		2,2						|1 0 1 0|0 1 0|0 0 0 0 0 0 0 1 0|
# g45,009f		3,2						|1 0 1 0|0 1 1|0 0 0 0 0 0 0 1 0|
# g45,00a1		1,14						|1 0 1 0|0 0 1|0 0 0 0 0 1 1 1 0|
STORE_UNCHECKED		llvl,ldelta					|1 0 1| llvl  | ldelta		|

#-----------------------
# g44,0062		2,7						|1 1 0 0|0 1 0 0|0 0 0 0|0 1 1 1|
# g44,0075		2,8						|1 1 0 0|0 1 0 0|0 0 0 0|1 0 0 0|
STORE			llvl,ldelta					|1 1 0| llvl  | ldelta		|

#-----------------------
# g43,0021		0,1						|1 1 1 0|0 0 0|0 0 0 0 0 0 0 0 1|
# g43,0022		0,2						|1 1 1 0|0 0 0|0 0 0 0 0 0 0 1 0|
# g43,0023		0,3						|1 1 1 0|0 0 0|0 0 0 0 0 0 0 1 1|
# g43,0025		2,2						|1 1 1 0|0 1 0|0 0 0 0 0 0 0 1 0|
# g44,004c		2,3						|1 1 1 0|0 1 0|0 0 0 0 0 0 0 1 1|
# g44,0079		2,-1						|1 1 1 0|0 1 0|1 1 1 1 1 1 1 1 1|
# g45,00a0		3,-1						|1 1 1 0|0 1 1|1 1 1 1 1 1 1 1 1|
LOAD			llvl,ldelta					|1 1 1| llvl  | ldelta		|
"""

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
        self.mne = "QQu_02CF"
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
            'FIELD_READ_OP',
            'FIELD_WRITE_OP',
            'FOR_CALL',
            'FOR_OUTER_CALL',
            'HEAP_ACCESS_CLASS',
            'INCOMPLETE',
            'IS_VISIBLE',
            'NOT_ELABORATED',
            'NULL_SUBPROGRAM',
            'PACKAGE_CLASS',
            'REFERENCE_LEX_1_OP',
            'SET_VALUE_UNCHECKED_OP',
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
        if adr in self.subprograms:
            return
        self.subprograms.add(adr)
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
