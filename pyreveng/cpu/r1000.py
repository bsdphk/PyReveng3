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

   OPCODE ASSIGNMENTS, July 16, 1986
	http://datamuseum.dk/aa/r1k_backup/a9/a9d4fb5bd.html


'''

import struct

from pyreveng import assy, data, code

r1000_desc = """

# Noteworthy segments:
#   ⟦120ea4603⟧ - has unreach{ed|able} subprograms: 0x25b, 0x28b, 0x4fb

#-----------------------
# Make places we get to, but do not handle grep(1)able
QQunknown_instruction	-						| unknown			|

Action			Illegal,>R					|0 0 0 0|0 0 0 0|0 0 0 0|0 0 0 0|

Action			Break_Optional					|0 0 0 0|0 0 0 0|0 0 0 0|0 1 1 1|
Action			Idle						|0 0 0 0|0 0 0 0|0 0 0 0|1 0 0 0|

Store_Top		Heap_Access,At_Offset_1				|0 0 0 0|0 0 0 0|0 0 1 1|0 0 0 1|
Store_Top		Heap_Access,At_Offset_2				|0 0 0 0|0 0 0 0|0 0 1 1|0 0 1 0|
Store_Top		Heap_Access,At_Offset_3				|0 0 0 0|0 0 0 0|0 0 1 1|0 0 1 1|
Store_Top		Heap_Access,At_Offset_4				|0 0 0 0|0 0 0 0|0 0 1 1|0 1 0 0|
Store_Top		Heap_Access,At_Offset_5				|0 0 0 0|0 0 0 0|0 0 1 1|0 1 0 1|
Store_Top		Heap_Access,At_Offset_6				|0 0 0 0|0 0 0 0|0 0 1 1|0 1 1 0|

Store_Top               Access,At_Offset_1				|0 0 0 0|0 0 0 0|0 0 1 1|1 0 0 1|
Store_Top               Access,At_Offset_2				|0 0 0 0|0 0 0 0|0 0 1 1|1 0 1 0|
Store_Top               Access,At_Offset_3				|0 0 0 0|0 0 0 0|0 0 1 1|1 0 1 1|
Store_Top               Access,At_Offset_4				|0 0 0 0|0 0 0 0|0 0 1 1|1 1 0 0|
Store_Top               Access,At_Offset_5				|0 0 0 0|0 0 0 0|0 0 1 1|1 1 0 1|
Store_Top               Access,At_Offset_6                         	|0 0 0 0|0 0 0 0|0 0 1 1|1 1 1 0|

Store_Top_Unchecked	Float,At_Offset_1                              	|0 0 0 0|0 0 0 0|0 1 0 0|0 0 0 1|
Store_Top_Unchecked	Float,At_Offset_2                              	|0 0 0 0|0 0 0 0|0 1 0 0|0 0 1 0|
Store_Top_Unchecked	Float,At_Offset_3                              	|0 0 0 0|0 0 0 0|0 1 0 0|0 0 1 1|
Store_Top_Unchecked	Float,At_Offset_4                              	|0 0 0 0|0 0 0 0|0 1 0 0|0 1 0 0|
Store_Top_Unchecked	Float,At_Offset_5                              	|0 0 0 0|0 0 0 0|0 1 0 0|0 1 0 1|
Store_Top_Unchecked	Float,At_Offset_6                              	|0 0 0 0|0 0 0 0|0 1 0 0|0 1 1 0|

Store_Top               Float,At_Offset_1                               |0 0 0 0|0 0 0 0|0 1 0 0|1 0 0 1|
Store_Top               Float,At_Offset_2                               |0 0 0 0|0 0 0 0|0 1 0 0|1 0 1 0|
Store_Top               Float,At_Offset_3                               |0 0 0 0|0 0 0 0|0 1 0 0|1 0 1 1|
Store_Top               Float,At_Offset_4                               |0 0 0 0|0 0 0 0|0 1 0 0|1 1 0 0|
Store_Top               Float,At_Offset_5                               |0 0 0 0|0 0 0 0|0 1 0 0|1 1 0 1|
Store_Top               Float,At_Offset_6                               |0 0 0 0|0 0 0 0|0 1 0 0|1 1 1 0|

Store_Top_Unchecked     Discrete,At_Offset_1                            |0 0 0 0|0 0 0 0|0 1 0 1|0 0 0 1|
Store_Top_Unchecked     Discrete,At_Offset_2                            |0 0 0 0|0 0 0 0|0 1 0 1|0 0 1 0|
Store_Top_Unchecked     Discrete,At_Offset_3                            |0 0 0 0|0 0 0 0|0 1 0 1|0 0 1 1|
Store_Top_Unchecked     Discrete,At_Offset_4                            |0 0 0 0|0 0 0 0|0 1 0 1|0 1 0 0|
Store_Top_Unchecked     Discrete,At_Offset_5                            |0 0 0 0|0 0 0 0|0 1 0 1|0 1 0 1|
Store_Top_Unchecked     Discrete,At_Offset_6                            |0 0 0 0|0 0 0 0|0 1 0 1|0 1 1 0|

Store_Top               Discrete,At_Offset_1                            |0 0 0 0|0 0 0 0|0 1 0 1|1 0 0 1|
Store_Top               Discrete,At_Offset_2                            |0 0 0 0|0 0 0 0|0 1 0 1|1 0 1 0|
Store_Top               Discrete,At_Offset_3                            |0 0 0 0|0 0 0 0|0 1 0 1|1 0 1 1|
Store_Top               Discrete,At_Offset_4                            |0 0 0 0|0 0 0 0|0 1 0 1|1 1 0 0|
Store_Top               Discrete,At_Offset_5                            |0 0 0 0|0 0 0 0|0 1 0 1|1 1 0 1|
Store_Top               Discrete,At_Offset_6                            |0 0 0 0|0 0 0 0|0 1 0 1|1 1 1 0|

Action			Establish_Frame					|0 0 0 0|0 0 0 0|0 1 1 0|1 0 0 0|
Action			Query_Frame					|0 0 0 0|0 0 0 0|0 1 1 0|1 0 0 1|
Action			Alter_Break_Mask				|0 0 0 0|0 0 0 0|0 1 1 0|1 0 1 0|
Action			Query_Break_Address				|0 0 0 0|0 0 0 0|0 1 1 0|1 0 1 1|
Action			Query_Break_Mask				|0 0 0 0|0 0 0 0|0 1 1 0|1 1 0 0|
Action			Query_Break_Cause				|0 0 0 0|0 0 0 0|0 1 1 0|1 1 0 1|
Action			Exit_Break					|0 0 0 0|0 0 0 0|0 1 1 0|1 1 1 0|
Action			Break_Unconditional				|0 0 0 0|0 0 0 0|0 1 1 0|1 1 1 1|

# a9d4fb5bd: unused
Action			Discrete,Diana_Spare2				|0 0 0 0|0 0 0 0|1 0 0 0|0 1 1 1|

# a9d4fb5bd: execute,heap_access,diana_module_table_lookup  !other_group
Action			Heap_Access,Diana_Spare2			|0 0 0 0|0 0 0 0|1 0 0 0|1 0 0 0|

# a9d4fb5bd: execute,discrete,diana_translate_sm_ptr  !other_group
Action			Discrete,Diana_Spare1				|0 0 0 0|0 0 0 0|1 0 0 0|1 0 0 1|

# a9d4fb5bd: execute,discrete,diana_is_id_node  !other_group
Action			Discrete,Diana_Spare0				|0 0 0 0|0 0 0 0|1 0 0 0|1 0 1 0|

Action			Heap_Access,Diana_Seq_Type_Get_Head		|0 0 0 0|0 0 0 0|1 0 0 0|1 0 1 1|
Action			Heap_Access,Diana_Put_Node_On_Seq_Type		|0 0 0 0|0 0 0 0|1 0 0 0|1 1 0 0|

Action			Heap_Access,Diana_Allocate_Tree_Node		|0 0 0 0|0 0 0 0|1 0 0 0|1 1 0 1|
Action			Discrete,Diana_Arity_For_Kind			|0 0 0 0|0 0 0 0|1 0 0 0|1 1 1 0|
Action			Discrete,Diana_Map_Kind_To_Vci			|0 0 0 0|0 0 0 0|1 0 0 0|1 1 1 1|

Action			Store_String_Extended,pse			|0 0 0 0|0 0 0 0|1 0 0 1|0 0 0 0| pse                           |
Action			Push_String_Extended_Indexed,pse		|0 0 0 0|0 0 0 0|1 0 0 1|0 0 0 1| pse                           |
Action			Push_String_Extended,pse			|0 0 0 0|0 0 0 0|1 0 0 1|0 0 1 0| pse                           |

#-----------------------
# a9d4fb5bd: unused
# 2fa0095f7: Action, Spare7_Action
# guru course at pg43,001c comments this as "push full address of a location in current code segment"
# XXX: it may be a bit of a stretch to assume that is a subp /phk
QQpush_full_address	subp						|0 0 0 0|0 0 0 0|1 0 0 1|0 0 1 1| subp				|

Execute			Package,Field_Reference_Dynamic			|0 0 0 0|0 0 0 0|1 0 0 1|0 1 0 1|
Execute			Package,Field_Execute_Dynamic			|0 0 0 0|0 0 0 0|1 0 0 1|0 1 1 0|
Execute			Package,Field_Write_Dynamic			|0 0 0 0|0 0 0 0|1 0 0 1|0 1 1 1|
Execute			Package,Field_Read_Dynamic			|0 0 0 0|0 0 0 0|1 0 0 1|1 0 0 0|
Action			Reference_Dynamic				|0 0 0 0|0 0 0 0|1 0 0 1|1 0 0 1|
Action			Call_Dynamic					|0 0 0 0|0 0 0 0|1 0 0 1|1 0 1 0|
Action			Store_Dynamic					|0 0 0 0|0 0 0 0|1 0 0 1|1 0 1 1|
Action			Load_Dynamic					|0 0 0 0|0 0 0 0|1 0 0 1|1 1 0 0|
Action			Jump_Nonzero_Dynamic				|0 0 0 0|0 0 0 0|1 0 0 1|1 1 0 1|
Action			Jump_Zero_Dynamic				|0 0 0 0|0 0 0 0|1 0 0 1|1 1 1 0|
Action			Jump_Dynamic					|0 0 0 0|0 0 0 0|1 0 0 1|1 1 1 1|

Action			Push_Structure_Extended,abs,mark		|0 0 0 0|0 0 0 0|1 0 1 0|0 0 0 0| abs                           |
Action			Push_Float_Extended				|0 0 0 0|0 0 0 0|1 0 1 0|0 0 0 1| abs                           |
Action			Push_Discrete_Extended				|0 0 0 0|0 0 0 0|1 0 1 0|0 0 1 0| abs                           |
Action			Loop_Decreasing_Extended,abs,>JC		|0 0 0 0|0 0 0 0|1 0 1 0|0 0 1 1| abs                           |
Action			Loop_Increasing_Extended,abs,>JC		|0 0 0 0|0 0 0 0|1 0 1 0|0 1 0 0| abs				|
Action			Jump_Nonzero_Extended,abs,>JC			|0 0 0 0|0 0 0 0|1 0 1 0|0 1 0 1| abs				|
Action			Jump_Zero_Extended,abs,>JC			|0 0 0 0|0 0 0 0|1 0 1 0|0 1 1 0| abs				|
Action			Jump_Extended,abs,>J				|0 0 0 0|0 0 0 0|1 0 1 0|0 1 1 1| abs				|

# Guess, Fits parameters, Field_Execute_Dynamic is not used elsewhere.
# Terminal_Essai.Recoit.Nouveau_Caractere (No, C); (785f3e358,2c9c18aad)
QQ_Action		Package,Field_Execute_Dynamic			|0 0 0 0|0 0 0 0|1 0 1 0|1 1 0 1|

Action			Increase_Priority				|0 0 0 0|0 0 0 0|1 0 1 1|0 0 1 1|
Action			Name_Partner					|0 0 0 0|0 0 0 0|1 0 1 1|0 1 0 0|
Action			Make_Parent					|0 0 0 0|0 0 0 0|1 0 1 1|0 1 0 1|
Action			Make_Scope					|0 0 0 0|0 0 0 0|1 0 1 1|0 1 1 0|
Action			Make_Self					|0 0 0 0|0 0 0 0|1 0 1 1|0 1 1 1|
Action			Set_Priority					|0 0 0 0|0 0 0 0|1 0 1 1|1 0 0 0|
Action			Get_Priority					|0 0 0 0|0 0 0 0|1 0 1 1|1 0 0 1|
Action			Initiate_Delay					|0 0 0 0|0 0 0 0|1 0 1 1|1 0 1 0|
Action			Signal_Completion,>R				|0 0 0 0|0 0 0 0|1 0 1 1|1 0 1 1|
Action			Signal_Activated				|0 0 0 0|0 0 0 0|1 0 1 1|1 1 0 0|
Action			Activate_Heap_Tasks				|0 0 0 0|0 0 0 0|1 0 1 1|1 1 0 1|
Action			Activate_Tasks					|0 0 0 0|0 0 0 0|1 0 1 1|1 1 1 0|
Action			Accept_Activation				|0 0 0 0|0 0 0 0|1 0 1 1|1 1 1 1|

Action			Make_Default					|0 0 0 0|0 0 0 0|1 1 0 0|0 1 0 0|
Action			Set_Block_Start					|0 0 0 0|0 0 0 0|1 1 0 0|0 1 0 1|
Action			Check_Subprogram_Elaborated			|0 0 0 0|0 0 0 0|1 1 0 0|0 1 1 0|
Action			Elaborate_Subprogram				|0 0 0 0|0 0 0 0|1 1 0 0|0 1 1 1|
Action			Pop_Auxiliary_Range				|0 0 0 0|0 0 0 0|1 1 0 0|1 0 0 0|
Action			Pop_Auxiliary_Loop				|0 0 0 0|0 0 0 0|1 1 0 0|1 0 0 1|
Action			Exit_Nullary_Function,>R			|0 0 0 0|0 0 0 0|1 1 0 0|1 0 1 0|
Action			Pop_Block_With_Result				|0 0 0 0|0 0 0 0|1 1 0 0|1 0 1 1|
Action			Pop_Block					|0 0 0 0|0 0 0 0|1 1 0 0|1 1 0 0|
Action			Spare6_Action					|0 0 0 0|0 0 0 0|1 1 0 0|1 1 0 1|
Action			Pop_Auxiliary					|0 0 0 0|0 0 0 0|1 1 0 0|1 1 1 0|
Action			Mark_Auxiliary					|0 0 0 0|0 0 0 0|1 1 0 0|1 1 1 1|
Action			Swap_Control					|0 0 0 0|0 0 0 0|1 1 0 1|0 0 0 0|

Pop_Control		Pop_Count_1					|0 0 0 0|0 0 0 0|1 1 0 1|0 0 0 1|
Pop_Control		Pop_Count_2					|0 0 0 0|0 0 0 0|1 1 0 1|0 0 1 0|
Pop_Control		Pop_Count_3					|0 0 0 0|0 0 0 0|1 1 0 1|0 0 1 1|
Pop_Control		Pop_Count_4					|0 0 0 0|0 0 0 0|1 1 0 1|0 1 0 0|
Pop_Control		Pop_Count_5					|0 0 0 0|0 0 0 0|1 1 0 1|0 1 0 1|
Pop_Control		Pop_Count_6					|0 0 0 0|0 0 0 0|1 1 0 1|0 1 1 0|
Pop_Control		Pop_Count_7					|0 0 0 0|0 0 0 0|1 1 0 1|0 1 1 1|

Load_Top		At_Offset_0					|0 0 0 0|0 0 0 0|1 1 0 1|1 0 0 0|
Load_Top		At_Offset_1					|0 0 0 0|0 0 0 0|1 1 0 1|1 0 0 1|
Load_Top		At_Offset_2					|0 0 0 0|0 0 0 0|1 1 0 1|1 0 1 0|
Load_Top		At_Offset_3					|0 0 0 0|0 0 0 0|1 1 0 1|1 0 1 1|
Load_Top		At_Offset_4					|0 0 0 0|0 0 0 0|1 1 0 1|1 1 0 0|
Load_Top		At_Offset_5					|0 0 0 0|0 0 0 0|1 1 0 1|1 1 0 1|
Load_Top		At_Offset_6					|0 0 0 0|0 0 0 0|1 1 0 1|1 1 1 0|

#-----------------------
# feh269,1c		Value_02					|0 0 0 0|0 0 0 0|1 1 1 0|0 0 1 0|
# gc44,0046		1						|0 0 0 0|0 0 0 0|1 1 1 0|0 0 0 1|
# gc43,0036		2						|0 0 0 0|0 0 0 0|1 1 1 0|0 0 1 0|
# 2fa0095f7: emulation skips value_17
# a9d4fb5bd: has value_00 to value_31
Load_Encached		eon						|0 0 0 0|0 0 0 0|1 1 1| eon	|

Execute			Exception,Raise,>R				|0 0 0 0|0 0 0 1|0 0 0 0|0 0 0 0|
Execute			Exception,Reraise,>R				|0 0 0 0|0 0 0 1|0 0 0 0|0 0 0 1|

Execute			Exception,Address				|0 0 0 0|0 0 0 1|0 0 0 0|0 1 1 0|
Execute			Exception,Get_Name				|0 0 0 0|0 0 0 1|0 0 0 0|0 1 1 1|

Execute			Exception,Is_Instruction_Error			|0 0 0 0|0 0 0 1|0 0 0 0|1 0 0 1|
Execute			Exception,Is_Tasking_Error			|0 0 0 0|0 0 0 1|0 0 0 0|1 0 1 0|
Execute			Exception,Is_Storage_Error			|0 0 0 0|0 0 0 1|0 0 0 0|1 0 1 1|
Execute			Exception,Is_Program_Error			|0 0 0 0|0 0 0 1|0 0 0 0|1 1 0 0|
Execute			Exception,Is_Numeric_Error			|0 0 0 0|0 0 0 1|0 0 0 0|1 1 0 1|
Execute			Exception,Is_Constraint_Error			|0 0 0 0|0 0 0 1|0 0 0 0|1 1 1 0|
Execute			Exception,Equal					|0 0 0 0|0 0 0 1|0 0 0 0|1 1 1 1|

Execute			Any,Is_Initialization_Repeated			|0 0 0 0|0 0 0 1|0 0 0 1|0 0 0 0|
Execute			Any,Has_Repeated_Initialization			|0 0 0 0|0 0 0 1|0 0 0 1|0 0 0 1|
Execute			Any,Make_Constrained				|0 0 0 0|0 0 0 1|0 0 0 1|0 0 1 0|
Execute			Heap_Access,Size				|0 0 0 0|0 0 0 1|0 0 0 1|0 0 1 1|
Execute			Access,Size					|0 0 0 0|0 0 0 1|0 0 0 1|0 1 0 0|
Execute			Any,Structure_Clear				|0 0 0 0|0 0 0 1|0 0 0 1|0 1 0 1|
Execute			Any,Address_Of_Type				|0 0 0 0|0 0 0 1|0 0 0 1|0 1 1 0|
Execute			Any,Structure_Query				|0 0 0 0|0 0 0 1|0 0 0 1|0 1 1 1|
Execute			Any,Write_Unchecked				|0 0 0 0|0 0 0 1|0 0 0 1|1 0 0 0|
Execute			Any,Check_In_Formal_Type			|0 0 0 0|0 0 0 1|0 0 0 1|1 0 0 1|
Execute			Any,Not_In_Type					|0 0 0 0|0 0 0 1|0 0 0 1|1 0 1 0|
Execute			Any,In_Type					|0 0 0 0|0 0 0 1|0 0 0 1|1 0 1 1|
Execute			Any,Convert_Unchecked				|0 0 0 0|0 0 0 1|0 0 0 1|1 1 0 0|
Execute			Any,Convert_To_Formal				|0 0 0 0|0 0 0 1|0 0 0 1|1 1 0 1|
Execute			Any,Convert					|0 0 0 0|0 0 0 1|0 0 0 1|1 1 1 0|
Execute			Any,Is_Scalar					|0 0 0 0|0 0 0 1|0 0 0 1|1 1 1 1|
Execute			Any,Is_Value					|0 0 0 0|0 0 0 1|0 0 1 0|0 0 0 0|
Execute			Any,Is_Default					|0 0 0 0|0 0 0 1|0 0 1 0|0 0 0 1|
Execute			Any,Make_Root_Type				|0 0 0 0|0 0 0 1|0 0 1 0|0 0 1 0|
Execute			Any,Make_Aligned				|0 0 0 0|0 0 0 1|0 0 1 0|0 0 1 1|
Execute			Any,Is_Constrained				|0 0 0 0|0 0 0 1|0 0 1 0|0 1 0 0|
Execute			Any,Set_Constraint				|0 0 0 0|0 0 0 1|0 0 1 0|0 1 0 1|
Execute			Any,Has_Default_Initialization			|0 0 0 0|0 0 0 1|0 0 1 0|0 1 1 0|
Execute			Any,Run_Initialization_Utility			|0 0 0 0|0 0 0 1|0 0 1 0|0 1 1 1|

Execute			Any,Make_Visible				|0 0 0 0|0 0 0 1|0 0 1 0|1 0 0 1|
Execute			Any,Change_Utility				|0 0 0 0|0 0 0 1|0 0 1 0|1 0 1 0|
Execute			Any,Spare14					|0 0 0 0|0 0 0 1|0 0 1 0|1 0 1 1|
Execute			Any,Size					|0 0 0 0|0 0 0 1|0 0 1 0|1 1 0 0|
Execute			Any,Address					|0 0 0 0|0 0 0 1|0 0 1 0|1 1 0 1|
Execute			Any,Not_Equal					|0 0 0 0|0 0 0 1|0 0 1 0|1 1 1 0|
Execute			Any,Equal					|0 0 0 0|0 0 0 1|0 0 1 0|1 1 1 1|

Execute			Family,Count					|0 0 0 0|0 0 0 1|0 0 1 1|0 0 1 0|
Execute			Family,Rendezvous				|0 0 0 0|0 0 0 1|0 0 1 1|0 0 1 1|

Execute			Entry,Count					|0 0 0 0|0 0 0 1|0 0 1 1|0 1 1 0|
Execute			Entry,Rendezvous				|0 0 0 0|0 0 0 1|0 0 1 1|0 1 1 1|

Execute			Select,Terminate_Guard_Write			|0 0 0 0|0 0 0 1|0 0 1 1|1 1 0 0|
Execute			Select,Timed_Duration_Write			|0 0 0 0|0 0 0 1|0 0 1 1|1 1 0 1|
Execute			Select,Timed_Guard_Write			|0 0 0 0|0 0 0 1|0 0 1 1|1 1 1 0|
Execute			Select,Rendezvous				|0 0 0 0|0 0 0 1|0 0 1 1|1 1 1 1|

Execute			Discrete,Divide_And_Scale			|0 0 0 0|0 0 0 1|0 1 0 0|0 0 0 0|
Execute			Discrete,Multiply_And_Scale			|0 0 0 0|0 0 0 1|0 1 0 0|0 0 0 1|

Execute			Heap_Access,Diana_Find_Permanent_Attribute	|0 0 0 0|0 0 0 1|0 1 0 0|0 0 1 0|
Execute			Heap_Access,Adaptive_Balanced_Tree_Lookup	|0 0 0 0|0 0 0 1|0 1 0 0|0 0 1 1|
Execute			Heap_Access,Get_Name				|0 0 0 0|0 0 0 1|0 1 0 0|0 1 0 0|
Execute			Heap_Access,Diana_Tree_Kind			|0 0 0 0|0 0 0 1|0 1 0 0|0 1 0 1|
Execute			Heap_Access,Hash				|0 0 0 0|0 0 0 1|0 1 0 0|0 1 1 0|
Execute			Heap_Access,Construct_Segment			|0 0 0 0|0 0 0 1|0 1 0 0|0 1 1 1|
Execute			Heap_Access,Get_Offset				|0 0 0 0|0 0 0 1|0 1 0 0|1 0 0 0|

Execute			Float,Less_Equal_Zero				|0 0 0 0|0 0 0 1|0 1 0 0|1 0 0 1|
Execute			Float,Greater_Equal_Zero			|0 0 0 0|0 0 0 1|0 1 0 0|1 0 1 0|
Execute			Float,Less_Zero					|0 0 0 0|0 0 0 1|0 1 0 0|1 0 1 1|
Execute			Float,Greater_Zero				|0 0 0 0|0 0 0 1|0 1 0 0|1 1 0 0|
Execute			Float,Not_Equal_Zero				|0 0 0 0|0 0 0 1|0 1 0 0|1 1 0 1|
Execute			Float,Equal_Zero				|0 0 0 0|0 0 0 1|0 1 0 0|1 1 1 0|
Execute			Float,Not_In_Range				|0 0 0 0|0 0 0 1|0 1 0 0|1 1 1 1|

Execute			Variant_Record,Make_Constrained			|0 0 0 0|0 0 0 1|0 1 0 1|1 0 1 1|
Execute			Variant_Record,Is_Constrained_Object		|0 0 0 0|0 0 0 1|0 1 0 1|1 1 0 0|
Execute			Variant_Record,Field_Type_Dynamic		|0 0 0 0|0 0 0 1|0 1 0 1|1 1 0 1|
Execute			Variant_Record,Field_Reference_Dynamic		|0 0 0 0|0 0 0 1|0 1 0 1|1 1 1 0|
Execute			Variant_Record,Field_Write_Dynamic		|0 0 0 0|0 0 0 1|0 1 0 1|1 1 1 1|
Execute			Variant_Record,Field_Read_Dynamic		|0 0 0 0|0 0 0 1|0 1 1 0|0 0 0 0|
Execute			Variant_Record,Check_In_Formal_Type		|0 0 0 0|0 0 0 1|0 1 1 0|0 0 0 1|
Execute			Variant_Record,Check_In_Type			|0 0 0 0|0 0 0 1|0 1 1 0|0 0 1 0|
Execute			Variant_Record,Not_In_Type			|0 0 0 0|0 0 0 1|0 1 1 0|0 0 1 1|
Execute			Variant_Record,In_Type				|0 0 0 0|0 0 0 1|0 1 1 0|0 1 0 0|
Execute			Variant_Record,Convert				|0 0 0 0|0 0 0 1|0 1 1 0|0 1 0 1|
Execute			Variant_Record,Component_Offset			|0 0 0 0|0 0 0 1|0 1 1 0|0 1 1 0|
Execute			Variant_Record,Structure_Query			|0 0 0 0|0 0 0 1|0 1 1 0|0 1 1 1|
Execute			Variant_Record,Reference_Makes_Copy		|0 0 0 0|0 0 0 1|0 1 1 0|1 0 0 0|
Execute			Variant_Record,Read_Discriminant_Constraint	|0 0 0 0|0 0 0 1|0 1 1 0|1 0 0 1|

# 2fa0095f7: emulation has nothing
# a9d4fb5bd: has execute,variant_record,indirects_appended  !other_group
execute			Variant_Record,Indirects_Appended		|0 0 0 0|0 0 0 1|0 1 1 0|1 0 1 0|

Execute			Variant_Record,Read_Variant			|0 0 0 0|0 0 0 1|0 1 1 0|1 0 1 1|
Execute			Variant_Record,Is_Constrained			|0 0 0 0|0 0 0 1|0 1 1 0|1 1 0 0|
Execute			Variant_Record,Structure_Write			|0 0 0 0|0 0 0 1|0 1 1 0|1 1 0 1|
Execute			Variant_Record,Not_Equal			|0 0 0 0|0 0 0 1|0 1 1 0|1 1 1 0|
Execute			Variant_Record,Equal				|0 0 0 0|0 0 0 1|0 1 1 0|1 1 1 1|

Execute			Record,Field_Type_Dynamic			|0 0 0 0|0 0 0 1|0 1 1 1|0 1 1 1|
Execute			Record,Field_Reference_Dynamic			|0 0 0 0|0 0 0 1|0 1 1 1|1 0 0 0|
Execute			Record,Field_Write_Dynamic			|0 0 0 0|0 0 0 1|0 1 1 1|1 0 0 1|
Execute			Record,Field_Read_Dynamic			|0 0 0 0|0 0 0 1|0 1 1 1|1 0 1 0|
Execute			Record,Convert					|0 0 0 0|0 0 0 1|0 1 1 1|1 0 1 1|
Execute			Record,Component_Offset				|0 0 0 0|0 0 0 1|0 1 1 1|1 1 0 0|
Execute			Record,Structure_Write				|0 0 0 0|0 0 0 1|0 1 1 1|1 1 0 1|
Execute			Record,Not_Equal				|0 0 0 0|0 0 0 1|0 1 1 1|1 1 1 0|
Execute			Record,Equal					|0 0 0 0|0 0 0 1|0 1 1 1|1 1 1 1|

Execute			Subvector,Structure_Write			|0 0 0 0|0 0 0 1|1 0 0 0|1 0 0 0| # 1145
Execute			Subvector,Field_Reference			|0 0 0 0|0 0 0 1|1 0 0 0|1 0 0 1|
Execute			Subvector,Field_Write				|0 0 0 0|0 0 0 1|1 0 0 0|1 0 1 0|
Execute			Subvector,Field_Read				|0 0 0 0|0 0 0 1|1 0 0 0|1 0 1 1|

Execute			Subarray,Structure_Write			|0 0 0 0|0 0 0 1|1 0 0 0|1 1 0 0|
Execute			Subarray,Field_Reference			|0 0 0 0|0 0 0 1|1 0 0 0|1 1 0 1|
Execute			Subarray,Field_Write				|0 0 0 0|0 0 0 1|1 0 0 0|1 1 1 0|
Execute			Subarray,Field_Read				|0 0 0 0|0 0 0 1|1 0 0 0|1 1 1 1|

Execute			Matrix,Check_In_Type				|0 0 0 0|0 0 0 1|1 0 0 1|1 0 1 1|
Execute			Matrix,Not_In_Type				|0 0 0 0|0 0 0 1|1 0 0 1|1 1 0 0|
Execute			Matrix,In_Type					|0 0 0 0|0 0 0 1|1 0 0 1|1 1 0 1|
Execute			Matrix,Convert_To_Formal			|0 0 0 0|0 0 0 1|1 0 0 1|1 1 1 0|
Execute			Matrix,Convert					|0 0 0 0|0 0 0 1|1 0 0 1|1 1 1 1|

Execute			Matrix,Subarray					|0 0 0 0|0 0 0 1|1 0 1 0|0 0 1 1|
Execute			Matrix,Structure_Write				|0 0 0 0|0 0 0 1|1 0 1 0|0 1 0 0|
Execute			Matrix,Field_Reference				|0 0 0 0|0 0 0 1|1 0 1 0|0 1 0 1|
Execute			Matrix,Field_Write				|0 0 0 0|0 0 0 1|1 0 1 0|0 1 1 0|
Execute			Matrix,Field_Read				|0 0 0 0|0 0 0 1|1 0 1 0|0 1 1 1|
Execute			Matrix,Element_Type				|0 0 0 0|0 0 0 1|1 0 1 0|1 0 0 0|
Execute			Matrix,Reverse_Bounds				|0 0 0 0|0 0 0 1|1 0 1 0|1 0 0 1|
Execute			Matrix,Bounds					|0 0 0 0|0 0 0 1|1 0 1 0|1 0 1 0|
Execute			Matrix,Length					|0 0 0 0|0 0 0 1|1 0 1 0|1 0 1 1|
Execute			Matrix,Last					|0 0 0 0|0 0 0 1|1 0 1 0|1 1 0 0|
Execute			Matrix,First					|0 0 0 0|0 0 0 1|1 0 1 0|1 1 0 1|
Execute			Matrix,Not_Equal				|0 0 0 0|0 0 0 1|1 0 1 0|1 1 1 0|
Execute			Matrix,Equal					|0 0 0 0|0 0 0 1|1 0 1 0|1 1 1 1|

Execute			Vector,Hash					|0 0 0 0|0 0 0 1|1 0 1 1|1 1 1 0|
Execute			Vector,Less_Equal				|0 0 0 0|0 0 0 1|1 0 1 1|1 1 1 1|
Execute			Vector,Greater_Equal				|0 0 0 0|0 0 0 1|1 1 0 0|0 0 0 0|
Execute			Vector,Less					|0 0 0 0|0 0 0 1|1 1 0 0|0 0 0 1|
Execute			Vector,Greater					|0 0 0 0|0 0 0 1|1 1 0 0|0 0 1 0|
Execute			Vector,Check_In_Type				|0 0 0 0|0 0 0 1|1 1 0 0|0 0 1 1|
Execute			Vector,Not_In_Type				|0 0 0 0|0 0 0 1|1 1 0 0|0 1 0 0|
Execute			Vector,In_Type					|0 0 0 0|0 0 0 1|1 1 0 0|0 1 0 1|
Execute			Vector,Convert_To_Formal			|0 0 0 0|0 0 0 1|1 1 0 0|0 1 1 0|
Execute			Vector,Convert					|0 0 0 0|0 0 0 1|1 1 0 0|0 1 1 1|

Execute			Vector,Prepend					|0 0 0 0|0 0 0 1|1 1 0 0|1 0 1 0|
Execute			Vector,Append					|0 0 0 0|0 0 0 1|1 1 0 0|1 0 1 1|
Execute			Vector,Catenate					|0 0 0 0|0 0 0 1|1 1 0 0|1 1 0 0|
Execute			Vector,Slice_Reference				|0 0 0 0|0 0 0 1|1 1 0 0|1 1 0 1|
Execute			Vector,Slice_Write				|0 0 0 0|0 0 0 1|1 1 0 0|1 1 1 0|
Execute			Vector,Slice_Read				|0 0 0 0|0 0 0 1|1 1 0 0|1 1 1 1|
Execute			Vector,Complement				|0 0 0 0|0 0 0 1|1 1 0 1|0 0 0 0|
Execute			Vector,Xor					|0 0 0 0|0 0 0 1|1 1 0 1|0 0 0 1|
Execute			Vector,Or					|0 0 0 0|0 0 0 1|1 1 0 1|0 0 1 0|
Execute			Vector,And					|0 0 0 0|0 0 0 1|1 1 0 1|0 0 1 1|
Execute			Vector,Structure_Write				|0 0 0 0|0 0 0 1|1 1 0 1|0 1 0 0|
Execute			Vector,Field_Reference				|0 0 0 0|0 0 0 1|1 1 0 1|0 1 0 1|
Execute			Vector,Field_Write				|0 0 0 0|0 0 0 1|1 1 0 1|0 1 1 0|
Execute			Vector,Field_Read				|0 0 0 0|0 0 0 1|1 1 0 1|0 1 1 1|
Execute			Vector,Element_Type				|0 0 0 0|0 0 0 1|1 1 0 1|1 0 0 0|
Execute			Vector,Reverse_Bounds				|0 0 0 0|0 0 0 1|1 1 0 1|1 0 0 1|
Execute			Vector,Bounds					|0 0 0 0|0 0 0 1|1 1 0 1|1 0 1 0|
Execute			Vector,Length					|0 0 0 0|0 0 0 1|1 1 0 1|1 0 1 1|
Execute			Vector,Last					|0 0 0 0|0 0 0 1|1 1 0 1|1 1 0 0|
Execute			Vector,First					|0 0 0 0|0 0 0 1|1 1 0 1|1 1 0 1|
Execute			Vector,Not_Equal				|0 0 0 0|0 0 0 1|1 1 0 1|1 1 1 0|
Execute			Vector,Equal					|0 0 0 0|0 0 0 1|1 1 0 1|1 1 1 1|

Execute			Array,Check_In_Type				|0 0 0 0|0 0 0 1|1 1 1 0|1 0 1 1| #1494
Execute			Array,Not_In_Type				|0 0 0 0|0 0 0 1|1 1 1 0|1 1 0 0|
Execute			Array,In_Type					|0 0 0 0|0 0 0 1|1 1 1 0|1 1 0 1|
Execute			Array,Convert_To_Formal				|0 0 0 0|0 0 0 1|1 1 1 0|1 1 1 0|
Execute			Array,Convert					|0 0 0 0|0 0 0 1|1 1 1 0|1 1 1 1|

Execute			Array,Subarray					|0 0 0 0|0 0 0 1|1 1 1 1|0 0 1 1| #1476
Execute			Array,Structure_Write				|0 0 0 0|0 0 0 1|1 1 1 1|0 1 0 0|
Execute			Array,Field_Reference				|0 0 0 0|0 0 0 1|1 1 1 1|0 1 0 1|
Execute			Array,Field_Write				|0 0 0 0|0 0 0 1|1 1 1 1|0 1 1 0|
Execute			Array,Field_Read				|0 0 0 0|0 0 0 1|1 1 1 1|0 1 1 1|
Execute			Array,Element_Type				|0 0 0 0|0 0 0 1|1 1 1 1|1 0 0 0| #1458
Execute			Array,Reverse_Bounds				|0 0 0 0|0 0 0 1|1 1 1 1|1 0 0 1|
Execute			Array,Bounds					|0 0 0 0|0 0 0 1|1 1 1 1|1 0 1 0|
Execute			Array,Length					|0 0 0 0|0 0 0 1|1 1 1 1|1 0 1 1|
Execute			Array,Last					|0 0 0 0|0 0 0 1|1 1 1 1|1 1 0 0|
Execute			Array,First					|0 0 0 0|0 0 0 1|1 1 1 1|1 1 0 1| #143a
Execute			Array,Not_Equal					|0 0 0 0|0 0 0 1|1 1 1 1|1 1 1 0|
Execute			Array,Equal					|0 0 0 0|0 0 0 1|1 1 1 1|1 1 1 1| #142e

Execute			Module,Check_Elaborated				|0 0 0 0|0 0 1 0|0 0 0 0|0 1 1 0| #1428

Execute			Task,Abort_Multiple				|0 0 0 0|0 0 1 0|0 0 0 0|1 0 0 0| #1422
Execute			Task,Abort					|0 0 0 0|0 0 1 0|0 0 0 0|1 0 0 1|

Execute			Module,Get_Name					|0 0 0 0|0 0 1 0|0 0 0 0|1 0 1 0|
Execute			Module,Is_Terminated				|0 0 0 0|0 0 1 0|0 0 0 0|1 0 1 1|
Execute			Module,Is_Callable				|0 0 0 0|0 0 1 0|0 0 0 0|1 1 0 0|
Execute			Module,Elaborate				|0 0 0 0|0 0 1 0|0 0 0 0|1 1 0 1|
Execute			Module,Augment_Imports				|0 0 0 0|0 0 1 0|0 0 0 0|1 1 1 0|
Execute			Module,Activate					|0 0 0 0|0 0 1 0|0 0 0 0|1 1 1 1|

Execute			Heap_Access,Get_Segment				|0 0 0 0|0 0 1 0|0 0 0 1|0 0 0 0|
Execute			Heap_Access,Convert_Reference			|0 0 0 0|0 0 1 0|0 0 0 1|0 0 0 1|
Execute			Heap_Access,Address				|0 0 0 0|0 0 1 0|0 0 0 1|0 0 1 0|
Execute			Heap_Access,Check_In_Type			|0 0 0 0|0 0 1 0|0 0 0 1|0 0 1 1|
Execute			Heap_Access,Not_In_Type				|0 0 0 0|0 0 1 0|0 0 0 1|0 1 0 0|
Execute			Heap_Access,In_Type				|0 0 0 0|0 0 1 0|0 0 0 1|0 1 0 1|
Execute			Heap_Access,Convert				|0 0 0 0|0 0 1 0|0 0 0 1|0 1 1 0|
Execute			Heap_Access,All_Reference			|0 0 0 0|0 0 1 0|0 0 0 1|0 1 1 1|
Execute			Heap_Access,All_Write				|0 0 0 0|0 0 1 0|0 0 0 1|1 0 0 0|
Execute			Heap_Access,All_Read				|0 0 0 0|0 0 1 0|0 0 0 1|1 0 0 1|
Execute			Heap_Access,Element_Type			|0 0 0 0|0 0 1 0|0 0 0 1|1 0 1 0|
Execute			Heap_Access,Set_Null				|0 0 0 0|0 0 1 0|0 0 0 1|1 0 1 1|
Execute			Heap_Access,Not_Null				|0 0 0 0|0 0 1 0|0 0 0 1|1 1 0 0|
Execute			Heap_Access,Is_Null				|0 0 0 0|0 0 1 0|0 0 0 1|1 1 0 1|
Execute			Heap_Access,Maximum				|0 0 0 0|0 0 1 0|0 0 0 1|1 1 1 0|
Execute			Heap_Access,Equal				|0 0 0 0|0 0 1 0|0 0 0 1|1 1 1 1|

Execute			Access,Deallocate				|0 0 0 0|0 0 1 0|0 0 1 0|0 0 0 0|
Execute			Access,Allow_Deallocate				|0 0 0 0|0 0 1 0|0 0 1 0|0 0 0 1|
Execute			Access,Convert_Reference			|0 0 0 0|0 0 1 0|0 0 1 0|0 0 1 0|
Execute			Access,Check_In_Type				|0 0 0 0|0 0 1 0|0 0 1 0|0 0 1 1|
Execute			Access,Not_In_Type				|0 0 0 0|0 0 1 0|0 0 1 0|0 1 0 0|
Execute			Access,In_Type					|0 0 0 0|0 0 1 0|0 0 1 0|0 1 0 1|
Execute			Access,Convert					|0 0 0 0|0 0 1 0|0 0 1 0|0 1 1 0|
Execute			Access,All_Reference				|0 0 0 0|0 0 1 0|0 0 1 0|0 1 1 1|
Execute			Access,All_Write				|0 0 0 0|0 0 1 0|0 0 1 0|1 0 0 0|
Execute			Access,All_Read					|0 0 0 0|0 0 1 0|0 0 1 0|1 0 0 1|
Execute			Access,Element_Type				|0 0 0 0|0 0 1 0|0 0 1 0|1 0 1 0|
Execute			Access,Set_Null					|0 0 0 0|0 0 1 0|0 0 1 0|1 0 1 1|
Execute			Access,Not_Null					|0 0 0 0|0 0 1 0|0 0 1 0|1 1 0 0|
Execute			Access,Is_Null					|0 0 0 0|0 0 1 0|0 0 1 0|1 1 0 1|
Execute			Access,Not_Equal				|0 0 0 0|0 0 1 0|0 0 1 0|1 1 1 0|
Execute			Access,Equal					|0 0 0 0|0 0 1 0|0 0 1 0|1 1 1 1|

Execute			Float,In_Range					|0 0 0 0|0 0 1 0|0 0 1 1|0 0 0 0|
Execute			Float,Write_Unchecked				|0 0 0 0|0 0 1 0|0 0 1 1|0 0 0 1|
Execute			Float,Check_In_Type				|0 0 0 0|0 0 1 0|0 0 1 1|0 0 1 0|
Execute			Float,Not_In_Type				|0 0 0 0|0 0 1 0|0 0 1 1|0 0 1 1|
Execute			Float,In_Type					|0 0 0 0|0 0 1 0|0 0 1 1|0 1 0 0|
Execute			Float,Round_To_Discrete				|0 0 0 0|0 0 1 0|0 0 1 1|0 1 0 1|
Execute			Float,Truncate_To_Discrete			|0 0 0 0|0 0 1 0|0 0 1 1|0 1 1 0|
Execute			Float,Convert_From_Discrete			|0 0 0 0|0 0 1 0|0 0 1 1|0 1 1 1|
Execute			Float,Convert					|0 0 0 0|0 0 1 0|0 0 1 1|1 0 0 0|
Execute			Float,Exponentiate				|0 0 0 0|0 0 1 0|0 0 1 1|1 0 0 1|
Execute			Float,Divide					|0 0 0 0|0 0 1 0|0 0 1 1|1 0 1 0|
Execute			Float,Times					|0 0 0 0|0 0 1 0|0 0 1 1|1 0 1 1|
Execute			Float,Minus					|0 0 0 0|0 0 1 0|0 0 1 1|1 1 0 0|
Execute			Float,Plus					|0 0 0 0|0 0 1 0|0 0 1 1|1 1 0 1|
Execute			Float,Absolute_Value				|0 0 0 0|0 0 1 0|0 0 1 1|1 1 1 0|
Execute			Float,Unary_Minus				|0 0 0 0|0 0 1 0|0 0 1 1|1 1 1 1|
Execute			Float,Last					|0 0 0 0|0 0 1 0|0 1 0 0|0 0 0 0|
Execute			Float,First					|0 0 0 0|0 0 1 0|0 1 0 0|0 0 0 1|
Execute			Float,Less_Equal				|0 0 0 0|0 0 1 0|0 1 0 0|0 0 1 0|
Execute			Float,Greater_Equal				|0 0 0 0|0 0 1 0|0 1 0 0|0 0 1 1|
Execute			Float,Less					|0 0 0 0|0 0 1 0|0 1 0 0|0 1 0 0|
Execute			Float,Greater					|0 0 0 0|0 0 1 0|0 1 0 0|0 1 0 1|
Execute			Float,Not_Equal					|0 0 0 0|0 0 1 0|0 1 0 0|0 1 1 0|
Execute			Float,Equal					|0 0 0 0|0 0 1 0|0 1 0 0|0 1 1 1|

Execute			Discrete,Check_In_Integer			|0 0 0 0|0 0 1 0|0 1 0 0|1 0 0 0|
Execute			Discrete,Case_In_Range				|0 0 0 0|0 0 1 0|0 1 0 0|1 0 0 1|
Execute			Discrete,Is_Unsigned				|0 0 0 0|0 0 1 0|0 1 0 0|1 0 1 0|
Execute			Discrete,Count_Trailing_Zeros			|0 0 0 0|0 0 1 0|0 1 0 0|1 0 1 1|
Execute			Discrete,Count_Leading_Zeros			|0 0 0 0|0 0 1 0|0 1 0 0|1 1 0 0|
Execute			Discrete,Count_Nonzero_Bits			|0 0 0 0|0 0 1 0|0 1 0 0|1 1 0 1|
Execute			Discrete,Extract_Bits				|0 0 0 0|0 0 1 0|0 1 0 0|1 1 1 0|
Execute			Discrete,Insert_Bits				|0 0 0 0|0 0 1 0|0 1 0 0|1 1 1 1|
Execute			Discrete,Rotate					|0 0 0 0|0 0 1 0|0 1 0 1|0 0 0 0|
Execute			Discrete,Logical_Shift				|0 0 0 0|0 0 1 0|0 1 0 1|0 0 0 1|
Execute			Discrete,Arithmetic_Shift			|0 0 0 0|0 0 1 0|0 1 0 1|0 0 1 0|
Execute			Discrete,Binary_Scale				|0 0 0 0|0 0 1 0|0 1 0 1|0 0 1 1|
Execute			Discrete,Partial_Minus				|0 0 0 0|0 0 1 0|0 1 0 1|0 1 0 0|
Execute			Discrete,Partial_Plus				|0 0 0 0|0 0 1 0|0 1 0 1|0 1 0 1|
Execute			Discrete,Instruction_Read			|0 0 0 0|0 0 1 0|0 1 0 1|0 1 1 0|
Execute			Discrete,Raise,>R				|0 0 0 0|0 0 1 0|0 1 0 1|0 1 1 1|
Execute			Discrete,Test_And_Set_Next			|0 0 0 0|0 0 1 0|0 1 0 1|1 0 0 0|
Execute			Discrete,Test_And_Set_Previous			|0 0 0 0|0 0 1 0|0 1 0 1|1 0 0 1|
Execute			Discrete,Write_Unchecked			|0 0 0 0|0 0 1 0|0 1 0 1|1 0 1 0|
Execute			Discrete,Check_In_Type				|0 0 0 0|0 0 1 0|0 1 0 1|1 0 1 1|

# 2fa0095f7: emulation has nothing
# a9d4fb5bd: has execute,discrete,reverse_bounds_check
Execute			Discrete,ReverseBounds_Check			|0 0 0 0|0 0 1 0|0 1 0 1|1 1 0 0|

Execute			Discrete,Bounds_Check				|0 0 0 0|0 0 1 0|0 1 0 1|1 1 0 1|
Execute			Discrete,Convert				|0 0 0 0|0 0 1 0|0 1 0 1|1 1 1 0|
Execute			Discrete,Not_In_Type				|0 0 0 0|0 0 1 0|0 1 0 1|1 1 1 1|
Execute			Discrete,In_Type				|0 0 0 0|0 0 1 0|0 1 1 0|0 0 0 0|
Execute			Discrete,Not_In_Range				|0 0 0 0|0 0 1 0|0 1 1 0|0 0 0 1|
Execute			Discrete,In_Range				|0 0 0 0|0 0 1 0|0 1 1 0|0 0 1 0|
Execute			Discrete,Above_Bound				|0 0 0 0|0 0 1 0|0 1 1 0|0 0 1 1|
Execute			Discrete,Below_Bound				|0 0 0 0|0 0 1 0|0 1 1 0|0 1 0 0|
Execute			Discrete,Reverse_Bounds				|0 0 0 0|0 0 1 0|0 1 1 0|0 1 0 1|
Execute			Discrete,Bounds					|0 0 0 0|0 0 1 0|0 1 1 0|0 1 1 0|
Execute			Discrete,Predecessor				|0 0 0 0|0 0 1 0|0 1 1 0|0 1 1 1|
Execute			Discrete,Successor				|0 0 0 0|0 0 1 0|0 1 1 0|1 0 0 0|
Execute			Discrete,Last					|0 0 0 0|0 0 1 0|0 1 1 0|1 0 0 1|
Execute			Discrete,First					|0 0 0 0|0 0 1 0|0 1 1 0|1 0 1 0|
Execute			Discrete,Maximum				|0 0 0 0|0 0 1 0|0 1 1 0|1 0 1 1|
Execute			Discrete,Minimum				|0 0 0 0|0 0 1 0|0 1 1 0|1 1 0 0|
Execute			Discrete,Exponentiate				|0 0 0 0|0 0 1 0|0 1 1 0|1 1 0 1|
Execute			Discrete,Modulo					|0 0 0 0|0 0 1 0|0 1 1 0|1 1 1 0|
Execute			Discrete,Remainder				|0 0 0 0|0 0 1 0|0 1 1 0|1 1 1 1|
Execute			Discrete,Divide					|0 0 0 0|0 0 1 0|0 1 1 1|0 0 0 0|
Execute			Discrete,Times					|0 0 0 0|0 0 1 0|0 1 1 1|0 0 0 1|
Execute			Discrete,Minus					|0 0 0 0|0 0 1 0|0 1 1 1|0 0 1 0|
Execute			Discrete,Plus					|0 0 0 0|0 0 1 0|0 1 1 1|0 0 1 1|
Execute			Discrete,Absolute_Value				|0 0 0 0|0 0 1 0|0 1 1 1|0 1 0 0|
Execute			Discrete,Unary_Minus				|0 0 0 0|0 0 1 0|0 1 1 1|0 1 0 1|
Execute			Discrete,Complement				|0 0 0 0|0 0 1 0|0 1 1 1|0 1 1 0|
Execute			Discrete,Xor					|0 0 0 0|0 0 1 0|0 1 1 1|0 1 1 1|
Execute			Discrete,Or					|0 0 0 0|0 0 1 0|0 1 1 1|1 0 0 0|
Execute			Discrete,And					|0 0 0 0|0 0 1 0|0 1 1 1|1 0 0 1|
Execute			Discrete,Less_Equal				|0 0 0 0|0 0 1 0|0 1 1 1|1 0 1 0|
Execute			Discrete,Greater_Equal				|0 0 0 0|0 0 1 0|0 1 1 1|1 0 1 1|
Execute			Discrete,Less					|0 0 0 0|0 0 1 0|0 1 1 1|1 1 0 0|
Execute			Discrete,Greater				|0 0 0 0|0 0 1 0|0 1 1 1|1 1 0 1|
Execute			Discrete,Not_Equal				|0 0 0 0|0 0 1 0|0 1 1 1|1 1 1 0|
Execute			Discrete,Equal					|0 0 0 0|0 0 1 0|0 1 1 1|1 1 1 1|

Declare_Subprogram	For_Accept,subp					|0 0 0 0|0 0 1 0|1 0 0 1|1 0 0 1| subp				|
Declare_Subprogram	For_Outer_Call,Visible,Unelaborated,subp	|0 0 0 0|0 0 1 0|1 0 0 1|1 0 1 0| subp				|
Declare_Subprogram	For_Outer_Call,Unelaborated,subp		|0 0 0 0|0 0 1 0|1 0 0 1|1 0 1 1| subp				|
Declare_Subprogram	For_Outer_Call,Visible,subp			|0 0 0 0|0 0 1 0|1 0 0 1|1 1 0 0| subp				|
Declare_Subprogram	For_Outer_Call,subp				|0 0 0 0|0 0 1 0|1 0 0 1|1 1 0 1| subp				|
Declare_Subprogram	For_Call,Unelaborated,subp			|0 0 0 0|0 0 1 0|1 0 0 1|1 1 1 0| subp				|
Declare_Subprogram	For_Call,subp					|0 0 0 0|0 0 1 0|1 0 0 1|1 1 1 1| subp				|
Declare_Subprogram	Null_Subprogram					|0 0 0 0|0 0 1 0|1 0 1 0|0 0 0 0|

Declare_Subprogram	For_Accept,With_Address				|0 0 0 0|0 0 1 0|1 0 1 0|0 0 1 0|

Declare_Subprogram	For_Outer_Call,Visible,With_Address		|0 0 0 0|0 0 1 0|1 0 1 0|0 1 0 0|
Declare_Subprogram	For_Outer_Call,With_Address			|0 0 0 0|0 0 1 0|1 0 1 0|0 1 0 1|

Declare_Subprogram	For_Call,Visible,Unelaborated,With_Address	|0 0 0 0|0 0 1 0|1 0 1 0|1 0 0 0|
Declare_Subprogram	For_Call,Unelaborated,With_Address		|0 0 0 0|0 0 1 0|1 0 1 0|1 0 0 1|
Declare_Subprogram	For_Call,Visible,With_Address			|0 0 0 0|0 0 1 0|1 0 1 0|1 0 1 0|
Declare_Subprogram	For_Call,With_Address				|0 0 0 0|0 0 1 0|1 0 1 0|1 0 1 1|

Declare_Variable	Float,Visible,With_Value,With_Constraint	|0 0 0 0|0 0 1 0|1 0 1 1|1 1 1 0|
Declare_Variable	Float,With_Value,With_Constraint		|0 0 0 0|0 0 1 0|1 0 1 1|1 1 1 1|

Declare_Variable	Any,Visible					|0 0 0 0|0 0 1 0|1 1 0 0|0 1 1 0|
Declare_Variable	Any						|0 0 0 0|0 0 1 0|1 1 0 0|0 1 1 1|

Declare_Variable	Family						|0 0 0 0|0 0 1 0|1 1 0 0|1 0 0 1|

Declare_Variable	Entry						|0 0 0 0|0 0 1 0|1 1 0 0|1 0 1 1|

Declare_Variable	Select,Choice_Open				|0 0 0 0|0 0 1 0|1 1 0 0|1 1 1 0|
Declare_Variable	Select						|0 0 0 0|0 0 1 0|1 1 0 0|1 1 1 1|

Declare_Variable	Variant_Record,Visible,With_Constraint		|0 0 0 0|0 0 1 0|1 1 1 1|1 0 1 1|
Declare_Variable	Variant_Record,With_Constraint			|0 0 0 0|0 0 1 0|1 1 1 1|1 1 0 0|
Declare_Variable	Variant_Record,Duplicate			|0 0 0 0|0 0 1 0|1 1 1 1|1 1 0 1|
Declare_Variable	Variant_Record,Visible				|0 0 0 0|0 0 1 0|1 1 1 1|1 1 1 0|
Declare_Variable	Variant_Record					|0 0 0 0|0 0 1 0|1 1 1 1|1 1 1 1|

Complete_Type		Variant_Record,By_Component_Completion		|0 0 0 0|0 0 1 1|0 0 0 0|0 0 1 1|
Complete_Type		Variant_Record,By_Completing_Constraint		|0 0 0 0|0 0 1 1|0 0 0 0|0 1 0 0|
Complete_Type		Variant_Record,By_Constraining_Incomplete	|0 0 0 0|0 0 1 1|0 0 0 0|0 1 0 1|
Complete_Type		Variant_Record,By_Renaming			|0 0 0 0|0 0 1 1|0 0 0 0|0 1 1 0|
Complete_Type		Variant_Record,By_Defining			|0 0 0 0|0 0 1 1|0 0 0 0|0 1 1 1|

# a9d4fb5bd has comment: -formerly declare_type,variant_record,incomplete,constrained          !declare_group
Declare_Type		Variant_Record,Constrained_Incomplete		|0 0 0 0|0 0 1 1|0 0 0 1|0 0 0 1|

# a9d4fb5bd has comment: -formerly declare_type,variant_record,incomplete,visible,constrained
Declare_Type		Variant_Record,Constrained_Incomplete,Visible	|0 0 0 0|0 0 1 1|0 0 0 1|0 0 1 0|

# a9d4fb5bd has comment: -formerly declare_type,variant_record,constrained_incomplete          !declare_group
# ?			?						|0 0 0 0|0 0 1 1|0 0 0 1|0 0 1 1|

# a9d4fb5bd has comment: -formerly declare_type,variant_record,constrained_incomplete,visible  !declare_group
# ?			?						|0 0 0 0|0 0 1 1|0 0 0 1|0 1 0 0|

Declare_Type		Variant_Record,Defined_Incomplete		|0 0 0 0|0 0 1 1|0 0 0 1|0 1 0 1|
Declare_Type		Variant_Record,Defined_Incomplete,Visible	|0 0 0 0|0 0 1 1|0 0 0 1|0 1 1 0|

Declare_Type		Variant_Record,Incomplete			|0 0 0 0|0 0 1 1|0 0 0 1|1 0 0 0|
Declare_Type		Variant_Record,Incomplete,Visible		|0 0 0 0|0 0 1 1|0 0 0 1|1 0 0 1|

Declare_Type		Variant_Record,Constrained			|0 0 0 0|0 0 1 1|0 0 0 1|1 0 1 1|
Declare_Type		Variant_Record,Constrained,Visible		|0 0 0 0|0 0 1 1|0 0 0 1|1 1 0 0|
Declare_Type		Variant_Record,Defined				|0 0 0 0|0 0 1 1|0 0 0 1|1 1 0 1|
Declare_Type		Variant_Record,Defined,Visible			|0 0 0 0|0 0 1 1|0 0 0 1|1 1 1 0|

Declare_Variable	Record,Duplicate				|0 0 0 0|0 0 1 1|0 0 1 0|0 0 0 0|
Declare_Variable	Record,Visible					|0 0 0 0|0 0 1 1|0 0 1 0|0 0 0 1|
Declare_Variable	Record						|0 0 0 0|0 0 1 1|0 0 1 0|0 0 1 0|

Complete_Type		Record,By_Component_Completion			|0 0 0 0|0 0 1 1|0 0 1 0|0 1 0 0|
Complete_Type		Record,By_Renaming				|0 0 0 0|0 0 1 1|0 0 1 0|0 1 0 1|
Complete_Type		Record,By_Defining				|0 0 0 0|0 0 1 1|0 0 1 0|0 1 1 0|

Declare_Type		Record,Defined_Incomplete			|0 0 0 0|0 0 1 1|0 0 1 0|0 1 1 1|
Declare_Type		Record,Defined_Incomplete,Visible		|0 0 0 0|0 0 1 1|0 0 1 0|1 0 0 0|

Declare_Type		Record,Incomplete				|0 0 0 0|0 0 1 1|0 0 1 0|1 0 1 0|
Declare_Type		Record,Incomplete,Visible			|0 0 0 0|0 0 1 1|0 0 1 0|1 0 1 1|

Declare_Type		Record,Defined					|0 0 0 0|0 0 1 1|0 0 1 0|1 1 0 1|
Declare_Type		Record,Defined,Visible				|0 0 0 0|0 0 1 1|0 0 1 0|1 1 1 0|

Declare_Variable	Array,Visible,With_Constraint			|0 0 0 0|0 0 1 1|0 0 1 1|0 0 1 1|
Declare_Variable	Array,With_Constraint				|0 0 0 0|0 0 1 1|0 0 1 1|0 1 0 0|
Declare_Variable	Array,Duplicate					|0 0 0 0|0 0 1 1|0 0 1 1|0 1 0 1|
Declare_Variable	Array,Visible					|0 0 0 0|0 0 1 1|0 0 1 1|0 1 1 0|
Declare_Variable	Array						|0 0 0 0|0 0 1 1|0 0 1 1|0 1 1 1|

Complete_Type		Array,By_Component_Completion			|0 0 0 0|0 0 1 1|0 1 0 0|0 0 0 0|
Complete_Type		Array,By_Constraining				|0 0 0 0|0 0 1 1|0 1 0 0|0 0 0 1|
Complete_Type		Array,By_Renaming				|0 0 0 0|0 0 1 1|0 1 0 0|0 0 1 0|
Complete_Type		Array,By_Defining				|0 0 0 0|0 0 1 1|0 1 0 0|0 0 1 1|

Declare_Type		Array,Constrained_Incomplete,Bounds_With_Object		|1 0 0 0|0 0 1 1|0 1 0 0|0 1 1 0|
Declare_Type		Array,Constrained_Incomplete,Visible,Bounds_With_Object	|0 0 0 0|0 0 1 1|0 1 0 0|0 1 1 1|
Declare_Type		Array,Defined_Incomplete,Bounds_With_Object		|0 0 0 0|0 0 1 1|0 1 0 0|1 0 0 0|
Declare_Type		Array,Defined_Incomplete,Visible,Bounds_With_Object	|0 0 0 0|0 0 1 1|0 1 0 0|1 0 0 1|

Declare_Type		Array,Incomplete,Bounds_With_Object			|0 0 0 0|0 0 1 1|0 1 0 0|1 0 1 1|
Declare_Type		Array,Incomplete,Visible,Bounds_With_Object		|0 0 0 0|0 0 1 1|0 1 0 0|1 1 0 0|

# 2fa0095f7: emulation has nothing
# in a9d4fb5bd
Declare_Type		Array,Constrained,Bounds_With_Object		|0 0 0 0|0 0 1 1|0 1 0 0|1 1 1 0|

Declare_Type		Array,Constrained,Visible,Bounds_With_Object	|0 0 0 0|0 0 1 1|0 1 0 0|1 1 1 1|
Declare_Type		Array,Defined,Bounds_With_Object		|0 0 0 0|0 0 1 1|0 1 0 1|0 0 0 0|
Declare_Type		Array,Defined,Visible,Bounds_With_Object	|0 0 0 0|0 0 1 1|0 1 0 1|0 0 0 1|

Declare_Type		Array,Constrained_Incomplete			|0 0 0 0|0 0 1 1|0 1 0 1|0 0 1 1|
Declare_Type		Array,Constrained_Incomplete,Visible		|0 0 0 0|0 0 1 1|0 1 0 1|0 1 0 0|
Declare_Type		Array,Defined_Incomplete			|0 0 0 0|0 0 1 1|0 1 0 1|0 1 0 1|
Declare_Type		Array,Defined_Incomplete,Visible		|0 0 0 0|0 0 1 1|0 1 0 1|0 1 1 0|

Declare_Type		Array,Incomplete				|0 0 0 0|0 0 1 1|0 1 0 1|1 0 0 0|
Declare_Type		Array,Incomplete,Visible			|0 0 0 0|0 0 1 1|0 1 0 1|1 0 0 1|

Declare_Type		Array,Constrained				|0 0 0 0|0 0 1 1|0 1 0 1|1 0 1 1|
Declare_Type		Array,Constrained,Visible			|0 0 0 0|0 0 1 1|0 1 0 1|1 1 0 0|
Declare_Type		Array,Defined					|0 0 0 0|0 0 1 1|0 1 0 1|1 1 0 1|
Declare_Type		Array,Defined,Visible				|0 0 0 0|0 0 1 1|0 1 0 1|1 1 1 0|

Declare_Variable	Task,On_Processor,As_Component			|0 0 0 0|0 0 1 1|0 1 1 0|1 0 1 0|
Declare_Variable	Task,As_Component				|0 0 0 0|0 0 1 1|0 1 1 0|1 0 1 1|
Declare_Variable	Task,Visible,On_Processor			|0 0 0 0|0 0 1 1|0 1 1 0|1 1 0 0|
Declare_Variable	Task,On_Processor				|0 0 0 0|0 0 1 1|0 1 1 0|1 1 0 1|
Declare_Variable	Task,Visible					|0 0 0 0|0 0 1 1|0 1 1 0|1 1 1 0|
Declare_Variable	Task						|0 0 0 0|0 0 1 1|0 1 1 0|1 1 1 1|

Complete_Type		Task,By_Renaming				|0 0 0 0|0 0 1 1|0 1 1 1|0 1 0 0|

Declare_Type		Task,Incomplete					|0 0 0 0|0 0 1 1|0 1 1 1|0 1 1 1|
Declare_Type		Task,Incomplete,Visible				|0 0 0 0|0 0 1 1|0 1 1 1|1 0 0 0|

Declare_Type		Task,Defined,Not_Elaborated			|0 0 0 0|0 0 1 1|0 1 1 1|1 0 1 0|
Declare_Type		Task,Defined,Visible,Not_Elaborated		|0 0 0 0|0 0 1 1|0 1 1 1|1 0 1 1|

Declare_Type		Task,Defined					|0 0 0 0|0 0 1 1|0 1 1 1|1 1 0 1|
Declare_Type		Task,Defined,Visible				|0 0 0 0|0 0 1 1|0 1 1 1|1 1 1 0|

Declare_Variable	Package,Visible,On_Processor			|0 0 0 0|0 0 1 1|1 0 0 0|0 1 0 0|
Declare_Variable	Package,On_Processor				|0 0 0 0|0 0 1 1|1 0 0 0|0 1 0 1|
Declare_Variable	Package,Visible					|0 0 0 0|0 0 1 1|1 0 0 0|0 1 1 0|
Declare_Variable	Package						|0 0 0 0|0 0 1 1|1 0 0 0|0 1 1 1|

Declare_Type		Package,Defined,Not_Elaborated			|0 0 0 0|0 0 1 1|1 0 0 0|1 1 0 0|
Declare_Type		Package,Defined,Visible,Not_Elaborated		|0 0 0 0|0 0 1 1|1 0 0 0|1 1 0 1|
Declare_Type		Package,Defined					|0 0 0 0|0 0 1 1|1 0 0 0|1 1 1 0|
Declare_Type		Package,Defined,Visible				|0 0 0 0|0 0 1 1|1 0 0 0|1 1 1 1|

Declare_Variable	Heap_Access,Visible,By_Allocation,With_Value		|0 0 0 0|0 0 1 1|1 0 0 1|0 1 0 1|
Declare_Variable	Heap_Access,By_Allocation,With_Value			|0 0 0 0|0 0 1 1|1 0 0 1|0 1 1 0|
Declare_Variable	Heap_Access,Visible,By_Allocation,With_Subtype		|0 0 0 0|0 0 1 1|1 0 0 1|0 1 1 1|
Declare_Variable	Heap_Access,By_Allocation,With_Subtype			|0 0 0 0|0 0 1 1|1 0 0 1|1 0 0 0|
Declare_Variable	Heap_Access,Visible,By_Allocation,With_Constraint	|0 0 0 0|0 0 1 1|1 0 0 1|1 0 0 1|
Declare_Variable	Heap_Access,By_Allocation,With_Constraint		|0 0 0 0|0 0 1 1|1 0 0 1|1 0 1 0|
Declare_Variable	Heap_Access,Visible,By_Allocation			|0 0 0 0|0 0 1 1|1 0 0 1|1 0 1 1|
Declare_Variable	Heap_Access,By_Allocation				|0 0 0 0|0 0 1 1|1 0 0 1|1 1 0 0|
Declare_Variable	Heap_Access,Duplicate					|0 0 0 0|0 0 1 1|1 0 0 1|1 1 0 1|
Declare_Variable	Heap_Access,Visible					|0 0 0 0|0 0 1 1|1 0 0 1|1 1 1 0|
Declare_Variable	Heap_Access						|0 0 0 0|0 0 1 1|1 0 0 1|1 1 1 1|

Complete_Type		Heap_Access,By_Component_Completion				|0 0 0 0|0 0 1 1|1 0 1 0|0 0 0 0|
Complete_Type		Heap_Access,By_Constraining					|0 0 0 0|0 0 1 1|1 0 1 0|0 0 0 1|
Complete_Type		Heap_Access,By_Renaming						|0 0 0 0|0 0 1 1|1 0 1 0|0 0 1 0|
Complete_Type		Heap_Access,By_Defining						|0 0 0 0|0 0 1 1|1 0 1 0|0 0 1 1|

Declare_Type		Heap_Access,Incomplete,Values_Relative,With_Size		|0 0 0 0|0 0 1 1|1 0 1 0|0 1 0 0|
Declare_Type		Heap_Access,Incomplete,Values_Relative				|0 0 0 0|0 0 1 1|1 0 1 0|0 1 0 1|
Declare_Type		Heap_Access,Incomplete,Visible,Values_Relative			|0 0 0 0|0 0 1 1|1 0 1 0|0 1 1 0|
Declare_Type		Heap_Access,Incomplete,Visible,Values_Relative,With_Size	|0 0 0 0|0 0 1 1|1 0 1 0|0 1 1 1|
Declare_Type		Heap_Access,Incomplete						|0 0 0 0|0 0 1 1|1 0 1 0|1 0 0 0|
Declare_Type		Heap_Access,Incomplete,Visible					|0 0 0 0|0 0 1 1|1 0 1 0|1 0 0 1|

Declare_Type		Heap_Access,Constrained				|0 0 0 0|0 0 1 1|1 0 1 0|1 0 1 1|
Declare_Type		Heap_Access,Constrained,Visible			|0 0 0 0|0 0 1 1|1 0 1 0|1 1 0 0|
Declare_Type		Heap_Access,Defined				|0 0 0 0|0 0 1 1|1 0 1 0|1 1 0 1|
Declare_Type		Heap_Access,Defined,Visible			|0 0 0 0|0 0 1 1|1 0 1 0|1 1 1 0|

Declare_Variable	Access,Visible,By_Allocation,With_Value		|0 0 0 0|0 0 1 1|1 0 1 1|0 1 0 1|
Declare_Variable	Access,By_Allocation,With_Value			|0 0 0 0|0 0 1 1|1 0 1 1|0 1 1 0|
Declare_Variable	Access,Visible,By_Allocation,With_Subtype	|0 0 0 0|0 0 1 1|1 0 1 1|0 1 1 1|
Declare_Variable	Access,By_Allocation,With_Subtype		|0 0 0 0|0 0 1 1|1 0 1 1|1 0 0 0|
Declare_Variable	Access,Visible,By_Allocation,With_Constraint	|0 0 0 0|0 0 1 1|1 0 1 1|1 0 0 1|
Declare_Variable	Access,By_Allocation,With_Constraint		|0 0 0 0|0 0 1 1|1 0 1 1|1 0 1 0|
Declare_Variable	Access,Visible,By_Allocation			|0 0 0 0|0 0 1 1|1 0 1 1|1 0 1 1|
Declare_Variable	Access,By_Allocation				|0 0 0 0|0 0 1 1|1 0 1 1|1 1 0 0|
Declare_Variable	Access,Duplicate				|0 0 0 0|0 0 1 1|1 0 1 1|1 1 0 1|
Declare_Variable	Access,Visible					|0 0 0 0|0 0 1 1|1 0 1 1|1 1 1 0|
Declare_Variable	Access						|0 0 0 0|0 0 1 1|1 0 1 1|1 1 1 1|

Complete_Type		Access,By_Component_Completion			|0 0 0 0|0 0 1 1|1 1 0 0|0 1 0 0|
Complete_Type		Access,By_Constraining				|0 0 0 0|0 0 1 1|1 1 0 0|0 1 0 1|
Complete_Type		Access,By_Renaming				|0 0 0 0|0 0 1 1|1 1 0 0|0 1 1 0|

# 2fa0095f7: emulation has nothing
Complete_Type		Access,By_Defining				|0 0 0 0|0 0 1 1|1 1 0 0|0 1 1 1|


Declare_Type		Access,Incomplete,Accesses_Protected		|0 0 0 0|0 0 1 1|1 1 0 0|1 1 0 0|
Declare_Type		Access,Incomplete,Visible,Accesses_Protected	|0 0 0 0|0 0 1 1|1 1 0 0|1 1 0 1|
Declare_Type		Access,Incomplete				|0 0 0 0|0 0 1 1|1 1 0 0|1 1 1 0|
Declare_Type		Access,Incomplete,Visible			|0 0 0 0|0 0 1 1|1 1 0 0|1 1 1 1|

Declare_Type		Access,Constrained				|0 0 0 0|0 0 1 1|1 1 0 1|0 0 0 1|
Declare_Type		Access,Constrained,Visible			|0 0 0 0|0 0 1 1|1 1 0 1|0 0 1 0|
Declare_Type		Access,Defined,Accesses_Protected		|0 0 0 0|0 0 1 1|1 1 0 1|0 0 1 1|
Declare_Type		Access,Defined,Visible,Accesses_Protected	|0 0 0 0|0 0 1 1|1 1 0 1|0 1 0 0|
Declare_Type		Access,Defined					|0 0 0 0|0 0 1 1|1 1 0 1|0 1 0 1|
Declare_Type		Access,Defined,Visible				|0 0 0 0|0 0 1 1|1 1 0 1|0 1 1 0|

Declare_Variable	Float,Duplicate					|0 0 0 0|0 0 1 1|1 1 0 1|1 0 0 0|
Declare_Variable	Float,Visible					|0 0 0 0|0 0 1 1|1 1 0 1|1 0 0 1|
Declare_Variable	Float						|0 0 0 0|0 0 1 1|1 1 0 1|1 0 1 0|
Declare_Variable	Float,Visible,With_Value			|0 0 0 0|0 0 1 1|1 1 0 1|1 0 1 1|

Complete_Type		Float,By_Constraining				|0 0 0 0|0 0 1 1|1 1 0 1|1 1 0 0|
Complete_Type		Float,By_Renaming				|0 0 0 0|0 0 1 1|1 1 0 1|1 1 0 1|
Complete_Type		Float,By_Defining				|0 0 0 0|0 0 1 1|1 1 0 1|1 1 1 0|

Declare_Variable	Float,With_Value				|0 0 0 0|0 0 1 1|1 1 0 1|1 1 1 1|

Declare_Type		Float,Incomplete				|0 0 0 0|0 0 1 1|1 1 1 0|0 0 0 0|
Declare_Type		Float,Incomplete,Visible			|0 0 0 0|0 0 1 1|1 1 1 0|0 0 0 1|

Declare_Type		Float,Constrained				|0 0 0 0|0 0 1 1|1 1 1 0|0 0 1 1|
Declare_Type		Float,Constrained,Visible			|0 0 0 0|0 0 1 1|1 1 1 0|0 1 0 0|
Declare_Type		Float,Defined					|0 0 0 0|0 0 1 1|1 1 1 0|0 1 0 1|
Declare_Type		Float,Defined,Visible				|0 0 0 0|0 0 1 1|1 1 1 0|0 1 1 0|

Declare_Variable	Discrete,Visible,With_Value,With_Constraint	|0 0 0 0|0 0 1 1|1 1 1 0|1 0 0 0|
Declare_Variable	Discrete,Duplicate				|0 0 0 0|0 0 1 1|1 1 1 0|1 0 0 1|
Declare_Variable	Discrete,Visible				|0 0 0 0|0 0 1 1|1 1 1 0|1 0 1 0|
Declare_Variable	Discrete					|0 0 0 0|0 0 1 1|1 1 1 0|1 0 1 1|
Declare_Variable	Discrete,With_Value,With_Constraint		|0 0 0 0|0 0 1 1|1 1 1 0|1 1 0 0|

Complete_Type		Discrete,By_Constraining			|0 0 0 0|0 0 1 1|1 1 1 0|1 1 0 1|
Complete_Type		Discrete,By_Renaming				|0 0 0 0|0 0 1 1|1 1 1 0|1 1 1 0|
Complete_Type		Discrete,By_Defining				|0 0 0 0|0 0 1 1|1 1 1 0|1 1 1 1|

Declare_Variable	Discrete,Visible,With_Value			|0 0 0 0|0 0 1 1|1 1 1 1|0 0 0 0|
Declare_Variable	Discrete,With_Value				|0 0 0 0|0 0 1 1|1 1 1 1|0 0 0 1|
Declare_Variable	Discrete,Incomplete,Unsigned			|0 0 0 0|0 0 1 1|1 1 1 1|0 0 1 0|
Declare_Variable	Discrete,Incomplete,Visible,Unsigned		|0 0 0 0|0 0 1 1|1 1 1 1|0 0 1 1|

Declare_Variable	Discrete,Incomplete				|0 0 0 0|0 0 1 1|1 1 1 1|0 1 0 1|
Declare_Variable	Discrete,Incomplete,Visible			|0 0 0 0|0 0 1 1|1 1 1 1|0 1 1 0|

# Guess, used after defining Discrete type
#QQ_Declare_Variable	Discrete,XXX					|0 0 0 0|0 0 1 1|1 1 1 1|0 1 1 1|

Declare_Type		Discrete,Constrained				|0 0 0 0|0 0 1 1|1 1 1 1|1 0 0 0|
Declare_Type		Discrete,Constrained,Visible			|0 0 0 0|0 0 1 1|1 1 1 1|1 0 0 1|
Declare_Type		Discrete,Defined,With_Size			|0 0 0 0|0 0 1 1|1 1 1 1|1 0 1 0|
Declare_Type		Discrete,Defined,Visible,With_Size		|0 0 0 0|0 0 1 1|1 1 1 1|1 0 1 1|

Declare_Type		Discrete,Defined				|0 0 0 0|0 0 1 1|1 1 1 1|1 1 0 1|

# 2fa0095f7: emulation has nothing
Declare_Type		Discrete,Defined,Visible			|0 0 0 0|0 0 1 1|1 1 1 1|1 1 1 0|

# 20250528 rev. to here.

# 0400	UNSIGNED_IMMEDIATE
Execute_Immediate	Set_Value_Visible_Unchecked,uimmediate		|0 0 0 0|0 1 0 0|   uimmediate  |
# 0500	UNSIGNED_IMMEDIATE
Execute_Immediate	Set_Value_Visible,uimmediate			|0 0 0 0|0 1 0 1|   uimmediate  |

#-----------------------
# g43,0037		SET_VALUE_UNCHECKED_OP,33			|0 0 0 0|0 1 1 0|0 0 1 0|0 0 0 1|
Execute_Immediate	Set_Value_Unchecked,uimmediate			|0 0 0 0|0 1 1 0|   uimmediate	|
Execute_Immediate	Set_Value,uimmediate				|0 0 0 0|0 1 1 1|   uimmediate  |
Execute_Immediate	Raise,uimmediate,>R				|0 0 0 0|1 0 0 0|   uimmediate  |

#-----------------------
# ⟦cb8e43375⟧ @0x108
# ⟦85b414c73⟧ @0x0170 /phk
# NB: microcode splits this in four:
# Execute_Immediate	Binary_Scale	0900 LIMITED_POSITIVE
# Execute_Immediate	Logical_Shift	0940 LIMITED_NEGATIVE
# Execute_Immediate	Logical_Shift	0980 LIMITED_POSITIVE	Not decoded by microcode
# Execute_Immedate	Binary_Scale	09c0 LIMITED_NEGATIVE
#BINARY_SCALE_OP	s8						|0 0 0 0|1 0 0 1|	s8	|
Execute_Immediate	Binary_Scale,limitedpos				|0 0 0 0|1 0 0 1|0 0| limitedpos|
Execute_Immediate	Logical_Shift,limitedneg			|0 0 0 0|1 0 0 1|0 1| limitedneg|
#Execute_Immedate	Logical_Shift,limitedpos			|0 0 0 0|1 0 0 1|1 0| limitedpos|
Execute_Immediate	Binary_Scale,limitedneg				|0 0 0 0|1 0 0 1|1 1| limitedneg|

#-----------------------
# /aa (3bf0c159 00da )
# NB: microcode splits this in two:
# Execute_Immediate	Plus	0a00	POSITIVE_IMMEDIATE
# Execute_Immediate	Plus	0a80	NEGATIVE_IMMEDIATE
Execute_Immediate	Plus,s8						|0 0 0 0|1 0 1 0|	s8	|

#-----------------------
# See ⟦a53169a08⟧ @0x64, some kind of comparison/test
# Almost always followed by 0x70xx conditional jump /phk
# 93b91846e @0x0168	case Colons_Observed is 	when 2 =>
Execute_Immediate	Case_Compare,uimmediate				|0 0 0 0|1 0 1 1|   uimmediate	|

#-----------------------
# See ⟦657fb377c⟧ @0x1d7c, some kind of comparison/test
# Almost always followed by 0x70xx or 0x68xx conditional jump /phk
# Maybe Greater_Equal_Op  ⟦36a4ea3d7⟧ @0x0609   if Months'Pos (T.Month) >= 3 then
Execute_Immediate	Greater_Equal,s8				|0 0 0 0|1 1 0 0| 	s8	|

Execute_Immediate	Less,s8						|0 0 0 0|1 1 0 1|	s8	|
Execute_Immediate	Not_Equal,s8					|0 0 0 0|1 1 1 0|       s8      |
Execute_Immediate	Equal,s8					|0 0 0 0|1 1 1 1|       s8      |

# 1000	FIELD_NUMBER
Execute			Select,Guard_Write,fieldnum			|0 0 0 1|0 0 0 0|    fieldnum   |
Execute			Select,Member_Write,fieldnum			|0 0 0 1|0 0 0 1|    fieldnum   |
Execute			Task,Family_Timed,fieldnum			|0 0 0 1|0 0 1 0|    fieldnum   |
Execute			Task,Family_Cond,fieldnum			|0 0 0 1|0 0 1 1|    fieldnum   |
Execute			Task,Family_Call,fieldnum			|0 0 0 1|0 1 0 0|    fieldnum   |
Execute			Task,Timed_Call,fieldnum			|0 0 0 1|0 1 0 1|    fieldnum   |
Execute			Task,Conditional_Call,fieldnum			|0 0 0 1|0 1 1 0|    fieldnum   |
Execute			Task,Entry_Call,fieldnum			|0 0 0 1|0 1 1 1|    fieldnum   |


#-----------------------
# g43,002c		PACKAGE_CLASS,FIELD_EXECUTE_OP,13		|0 0 0 1|1 0 0 0|0 0 0 0|1 1 0 1|
# g44,0071		PACKAGE_CLASS,FIELD_EXECUTE_OP,17		|0 0 0 1|1 0 0 0|0 0 0 1|0 0 0 1|
# g45,008e		PACKAGE_CLASS,FIELD_EXECUTE_OP,24		|0 0 0 1|1 0 0 0|0 0 0 1|1 0 0 0|
# g45,0091		PACKAGE_CLASS,FIELD_EXECUTE_OP,100		|0 0 0 1|1 0 0 0|0 1 1 0|0 1 0 0|
Execute			Package,Field_Execute,fieldnum			|0 0 0 1|1 0 0 0|    fieldnum   |

#-----------------------
# g88,0032		PACKAGE_CLASS,FIELD_REFERENCE_OP,13		|0 0 0 1|1 0 0 1|0 0 0 0|1 1 0 1|
Execute			Package,Field_Reference,fieldnum		|0 0 0 1|1 0 0 1|    fieldnum   |


#-----------------------
# ⟦cb8e43375⟧ @0x10b
Execute			Package,Field_Write,fieldnum			|0 0 0 1|1 0 1 0|    fieldnum	|

#-----------------------
# ⟦cb8e43375⟧ @0xfe
Execute			Package,Field_Read,fieldnum			|0 0 0 1|1 0 1 1|    fieldnum	|

#-----------------------
# ⟦36a4ea3d7⟧ @0x068e
Execute_Immediate	Run_Utility,uimmediate				|0 0 0 1|1 1 0 0|   uimmediate  |

#-----------------------
# g42,000e		REFERENCE_LEX_1_OP,13				|0 0 0 1|1 1 0 1|0 0 0 0|1 1 0 1|
Execute_Immediate	Reference_Lex_1,uimmediate			|0 0 0 1|1 1 0 1|   uimmediate	|

Execute			Variant_Record,Set_Variant,fieldnum			|0 0 1 0|0 0 0 0|    fieldnum   |
Execute			Variant_Record,Set_Bounds,fieldnum			|0 0 1 0|0 0 0 1|    fieldnum   |
Execute			Variant_Record,Field_Constrain,fieldnum			|0 0 1 0|0 0 1 0|    fieldnum   |
Execute			Variant_Record,Field_Type,fieldnum			|0 0 1 0|0 0 1 1|    fieldnum   |
Execute			Variant_Record,Field_Reference,Fixed,Direct,fieldnum	|0 0 1 0|0 1 0 0|    fieldnum   |
#-----------------------
# ⟦3f2fe70c1⟧ @0x0259	not sure /aa	return P.Subitem;	P.Subitem is a string
Execute			Variant_Record,Field_Reference,Indirect,fieldnum	|0 0 1 0|0 1 0 1|    fieldnum   |
Execute			Variant_Record,Field_Reference,Variant,Direct,fieldnum	|0 0 1 0|0 1 1 0|    fieldnum   |
Execute			Variant_Record,Field_Reference,Variant,Indirect,fieldnum|0 0 1 0|0 1 1 1|    fieldnum   |
Execute			Variant_Record,Field_Write,Fixed,Direct,fieldnum	|0 0 1 0|1 0 0 0|    fieldnum   |
Execute			Variant_Record,Field_Write,Fixed,Indirect,fieldnum	|0 0 1 0|1 0 0 1|    fieldnum   |
Execute			Variant_Record,Field_Write,Variant,Direct,fieldnum	|0 0 1 0|1 0 1 0|    fieldnum   |
Execute			Variant_Record,Field_Write,Variant,Indirect,fieldnum	|0 0 1 0|1 0 1 1|    fieldnum   |
#-----------------------
# ⟦3f2fe70c1⟧ @0x0245	not sure/aa		if P.Next = null then	P.Next = Access type
Execute			Variant_Record,Field_Read,Fixed,Direct,fieldnum		|0 0 1 0|1 1 0 0|    fieldnum   |
Execute			Variant_Record,Field_Append,Fixed,Indirect,fieldnum	|0 0 1 0|1 1 0 1|    fieldnum   |
Execute			Variant_Record,Field_Read,Variant,Direct,fieldnum	|0 0 1 0|1 1 1 0|    fieldnum   |
Execute			Variant_Record,Field_Append,Variant,Indirect,fieldnum	|0 0 1 0|1 1 1 1|    fieldnum   |

Execute			Record,Field_Type,fieldnum			|0 0 1 1|0 0 0 0|    fieldnum   |
Execute			Record,Field_Reference,fieldnum			|0 0 1 1|0 1 0 0|    fieldnum   |
Loop_Decreasing		pcrelneg,>JC					|0 0 1 1|0 1 1| pcrelneg        |
Execute			Record,Field_Write,fieldnum			|0 0 1 1|1 0 0 0|    fieldnum   |
Execute			Record,Field_Read,fieldnum			|0 0 1 1|1 1 0 0|    fieldnum   |

#-----------------------
# g44,005d		-5						|0 0 1 1|1 1 1 1|1 1 1 1|1 0 1 1|
Loop_Increasing		pcrelneg,>JC					|0 0 1 1|1 1 1| pcrelneg	|

#-----------------------
# phk
# 4100 PARAMETER_COUNT
End_Rendezvous		>R,parmcnt					|0 1 0 0|0 0 0 1|    parmcnt	|

#-----------------------
# phk
# 4200 NEW_TOP_OFFSET
Exit_Subprogram		From_Utility,With_Result,>R,topoffset		|0 1 0 0|0 0 1 0|   topoffset	|

#-----------------------
# phk
Exit_Subprogram		From_Utility,>R,topoffset			|0 1 0 0|0 0 1 1|   topoffset	|

#-----------------------
# phk
Exit_Subprogram		With_Result,>R,topoffset			|0 1 0 0|0 1 0 0|   topoffset	|

#-----------------------
# g43,002d		1						|0 1 0 0|0 1 0 1|0 0 0 0|0 0 0 1|
# g44,0080		2						|0 1 0 0|0 1 0 1|0 0 0 0|0 0 1 0|
# feh269,1e		1						|0 1 0 0|0 1 0 1|0 0 0 0|0 0 0 1|
Exit_Subprogram		topoffset,>R					|0 1 0 0|0 1 0 1|   topoffset	|

#-----------------------
# ⟦fad6fc6ba⟧ limits the argument to 8 bits
# /phk
# 4e00 CASE_MAXIMUM (and 0x1ff) = 9 bits (2fa0095f7)
Jump_Case		case_max					|0 1 0 0|0 1 1|   case_max	|

#-----------------------
# g43,001b		0						|0 1 0 0|1 0 0 0|0 0 0 0 0 0 0 0|
# g43,0024		3						|0 1 0 0|1 0 0 0|0 0 0 0 0 0 1 1|
# g44,0045		10						|0 1 0 0|1 0 0 0|0 0 0 0 1 0 1 1|
# g44,004e		24						|0 1 0 0|1 0 0 0|0 0 0 1 1 0 0 0|
Short_Literal		slit						|0 1 0 0|1| slit		|

# Any type
Indirect_Literal	Any,pcrel,literal				|0 1 0 1|0| pcrel               |

#-----------------------
# ⟦85b414c73⟧ (sin/cos/tan) @0x42b...
# Indirect_Literal	Float
Indirect_Literal	Float,pcrel,dbl					|0 1 0 1|1| pcrel		|

#-----------------------
# g88,0026		Discrete_Class,57				|0 1 1 0|0 0 0 0|0 0 1 1 1 0 0 1|
# g88,0027		Discrete_Class,52				|0 1 1 0|0 0 0 0|0 0 1 1 0 1 0 0|
# g88,002d		Discrete_Class,42				|0 1 1 0|0 0 0 0|0 0 1 0 1 0 1 0|
# feh269,1b		Discrete, #0020					|0 1 1 0|0 0 0 0|0 0 0 0 0 1 0 0|
Indirect_Literal	Discrete,pcrel,literal				|0 1 1 0|0| pcrel		|

#-----------------------
# jump_if_not		pcrel,>JC
Jump_Zero		pcrel,>JC					|0 1 1 0|1| pcrel		|

#-----------------------
# ⟦85b414c73⟧ @0x326
# (93b91846e, 0087	function Is_Digit, case Char is when '0'..'9' => return True;
# jump_if_true
Jump_Nonzero		pcrel,>JC					|0 1 1 1|0| pcrel		|

#-----------------------
# XXX: Not obvious if "1" and "2" is count of extension words or if and why those words are jumped over
# g88,001a		1						|0 1 1 1|1 0 0 0|0 0 0 0|0 0 0 1|
# g88,0047		2						|0 1 1 1|1 0 0 0|0 0 0 0|0 0 1 0|
Jump			pcrel,>J					|0 1 1 1|1| pcrel		|

#-----------------------
# g44,007d		1,15						|1 0 0 0|0 0 1|0 0 0 0 0 1 1 1 1|
# g44,007f		2,9						|1 0 0 0|0 1 0|0 0 0 0 0 1 0 0 1|
# feh269,22		0						|1 0 0 0|0 0 0|0 0 0 0 0 0 0 0 0|
Call			llvl,ldelta					|1 0 0| llvl  | ldelta		|

#-----------------------
# g45,009d		2,2						|1 0 1 0|0 1 0|0 0 0 0 0 0 0 1 0|
# g45,009f		3,2						|1 0 1 0|0 1 1|0 0 0 0 0 0 0 1 0|
# g45,00a1		1,14						|1 0 1 0|0 0 1|0 0 0 0 0 1 1 1 0|
Store_Unchecked		llvl,ldelta					|1 0 1| llvl  | ldelta		|

#-----------------------
# g44,0062		2,7						|1 1 0 0|0 1 0 0|0 0 0 0|0 1 1 1|
# g44,0075		2,8						|1 1 0 0|0 1 0 0|0 0 0 0|1 0 0 0|
Store			llvl,ldelta					|1 1 0| llvl  | ldelta		|

#-----------------------
# g43,0021		0,1						|1 1 1 0|0 0 0|0 0 0 0 0 0 0 0 1|
# g43,0022		0,2						|1 1 1 0|0 0 0|0 0 0 0 0 0 0 1 0|
# g43,0023		0,3						|1 1 1 0|0 0 0|0 0 0 0 0 0 0 1 1|
# g43,0025		2,2						|1 1 1 0|0 1 0|0 0 0 0 0 0 0 1 0|
# g44,004c		2,3						|1 1 1 0|0 1 0|0 0 0 0 0 0 0 1 1|
# g44,0079		2,-1						|1 1 1 0|0 1 0|1 1 1 1 1 1 1 1 1|
# g45,00a0		3,-1						|1 1 1 0|0 1 1|1 1 1 1 1 1 1 1 1|
Load			llvl,ldelta					|1 1 1| llvl  | ldelta		|
"""

class ucode_ins(assy.Instree_ins):
    ''' '''
    def assy_x(self):
        v = self['x']
        return "0x%x" % v

    def assy_i(self):
        # print("microcode does not like", self)
        raise assy.Invalid("Invalid Instruction")

class r1000_ins(assy.Instree_ins):
    ''' '''

    def assy_case_max(self):
        i = self['case_max']
        for j in range(i + 1):
            self += code.Jump(cond="#0x%x" % j, to=self.hi + j)
            self.lang.m.set_line_comment(self.hi + j, "case 0x%x" % j)
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

    def assy_limitedneg(self):
        v = self['limitedneg']
        return "-0x%x" % (0x040 - v)

    def assy_limitedpos(self):
        v = self['limitedpos']
        return "0x%x" % v

    def assy_fieldnum(self):
        v = self['fieldnum']
        return "Field_Number 0x%x" % v

    def assy_s8(self):
        v = self['s8']
        if v & 0x80:
            return "-0x%x" % (0x100 - v)
        return "0x%x" % v

    def assy_uimmediate(self):
        v = self['uimmediate']
        return "0x%x" % v

    def assy_parmcnt(self):
        v = self['parmcnt']
        return "0x%x" % v

    def assy_topoffset(self):
        v = self['topoffset']
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
        v = self['slit']
        # Short_Literal_Value [-2**10..2**10-1]
        #if v & (1<<10):
        #    v = v - (1<<11)
        #    return "-0x%x" % (-v)
        return "0x%x" % v

    def assy_llvl(self):
        # Lexical_Level [0..15]
        return "0x%x" % self['llvl']

    def assy_ldelta(self):
        # Lexical_Delta [-256..511]
        v = self['ldelta']
        y = self['llvl']
        if y == 1:
            return "0x%x" % v
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
        self.mne = "Declare_Variable	Select"
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
            'XXX',
            'Value_05',
            'Value_15',
            'Value_25',
            'Abort',
            'Constrained_Incomplete',
            'Make_Constrained',
            'Check_In_Integer',
            'Count_Leading_Zeros',
            'Predecessor',
            'Minus',
            'Null_Subprogram',
            'With_Address',
            'Entry',
            'Action',
            'Value_04',
            'Value_14',
            'Value_24',
            'Convert_Unchecked',
            'Adaptive_Balanced_Tree_Lookup',
            'Field_Read_Dynamic',
            'By_Constraining',
            'Address',
            'By_Allocation',
            'Reference_Lex_1',
            'Variant_Record',
            'From_Utility',
            'Value_06',
            'Value_16',
            'Value_26',
            'Is_Default',
            'Round_To_Discrete',
            'Modulo',
            'Defined',
            'Value_07',
            'Value_17',
            'Value_27',
            'Bounds',
            'Store_Top_Unchecked',
            'Make_Default',
            'Convert_To_Formal',
            'Minimum',
            'Declare_Subprogram',
            'Values_Relative',
            'Store_Dynamic',
            'Mark_Auxiliary',
            'Value_02',
            'Value_12',
            'Value_22',
            'Count_Nonzero_Bits',
            'Diana_Arity_For_Kind',
            'Value_03',
            'Value_13',
            'Value_23',
            'Vector',
            'Change_Utility',
            'Declare_Variable',
            'Equal',
            'Execute',
            'Value_01',
            'Value_11',
            'Value_21',
            'Value_31',
            'Timed_Guard_Write',
            'Defined_Incomplete',
            'Illegal',
            'Is_Constrained',
            'Length',
            'Variant',
            'Arithmetic_Shift',
            'Value_00',
            'Value_10',
            'Value_20',
            'Value_30',
            'First',
            'Unary_Minus',
            'Package',
            'Direct',
            'Jump_Zero_Dynamic',
            'Set_Constraint',
            'Jump',
            'Spare7_Action',
            'Spare6_Action',
            'Multiply_And_Scale',
            'With_Result',
            'Reference_Dynamic',
            'Value_09',
            'Value_19',
            'Value_29',
            'Timed_Duration_Write',
            'Make_Parent',
            'Access',
            'Plus',
            'Less',
            'Execute_Immediate',
            'Value_08',
            'Value_18',
            'Value_28',
            'Greater',
            'Select',
            'Loop_Decreasing',
            'Loop_Increasing',
            'Pop_Auxiliary_Loop',
            'Count',
            'Get_Offset',
            'Check_In_Formal_Type',
            'Array',
            'Activate_Heap_Tasks',
            'Set_Block_Start',
            'Prepend',
            'As_Component',
            'Exit_Subprogram',
            'On_Processor',
            'Run_Utility',
            'Establish_Frame',
            'Set_Priority',
            'Get_Priority',
            'Augment_Imports',
            'Last',
            'Push_Float_Extended',
            'Float',
            'Jump_Extended',
            'Allow_Deallocate',
            'Test_And_Set_Next',
            'Set_Value_Visible',
            'Pop_Auxiliary_Range',
            'Slice_Reference',
            'Is_Null',
            'And',
            'Set_Value_Unchecked',
            'Address_Of_Type',
            'Accept_Activation',
            'Diana_Tree_Kind',
            'Signal_Completion',
            'Check_Elaborated',
            'Times',
            'Jump_Nonzero_Dynamic',
            'Pop_Auxiliary',
            'Divide_And_Scale',
            'Accesses_Protected',
            'Reraise',
            'Truncate_To_Discrete',
            'Query_Break_Mask',
            'At_Offset_6',
            'In_Type',
            'Family',
            'Exit_Nullary_Function',
            'Reverse_Bounds_Check',
            'Convert',
            'Diana_Map_Kind_To_Vci',
            'Signal_Activated',
            'Field_Reference_Dynamic',
            'Structure_Write',
            'Maximum',
            'At_Offset_4',
            'Is_Program_Error',
            'For_Outer_Call',
            'Convert_From_Discrete',
            'Visible',
            'Conditional_Call',
            'Indirect_Literal',
            'At_Offset_5',
            'Construct_Segment',
            'Less_Equal_Zero',
            'Greater_Equal_Zero',
            'Not_Equal_Zero',
            'Structure_Query',
            'Indirects_Appended',
            'Convert_Reference',
            'Partial_Minus',
            'Field_Constrain',
            'Field_Reference',
            'Jump_Zero_Extended',
            'Spare14',
            'Matrix',
            'Logical_Shift',
            'Pop_Count_1',
            'Activate_Tasks',
            'Elaborate_Subprogram',
            'Is_Numeric_Error',
            'Reverse_Bounds',
            'With_Constraint',
            'Increase_Priority',
            'Is_Tasking_Error',
            'Partial_Plus',
            'Query_Break_Cause',
            'Jump_Nonzero_Extended',
            'Or',
            'Pop_Count_3',
            'Abort_Multiple',
            'Extract_Bits',
            'Instruction_Read',
            'Name_Partner',
            'Pop_Count_2',
            'Push_String_Extended',
            'End_Rendezvous',
            'Diana_Spare2',
            'Read_Variant',
            'Component_Offset',
            'Initiate_Delay',
            'Read_Discriminant_Constraint',
            'Diana_Spare1',
            'Is_Storage_Error',
            'Field_Write_Dynamic',
            'Xor',
            'Break_Unconditional',
            'Structure_Clear',
            'Diana_Spare0',
            'Alter_Break_Mask',
            'Field_Type_Dynamic',
            'Catenate',
            'Is_Constraint_Error',
            'Not_Elaborated',
            'By_Component_Completion',
            'Set_Variant',
            'Not_In_Range',
            'By_Completing_Constraint',
            'Short_Literal',
            'Less_Equal',
            'Family_Call',
            'Bounds_With_Object',
            'Raise',
            'Entry_Call',
            'Pop_Block_With_Result',
            'Pop_Block',
            'Element_Type',
            'Store',
            'Insert_Bits',
            'Declare_Type',
            'Constrained',
            'Push_Discrete_Extended',
            'Pop_Count_5',
            'Rendezvous',
            'Deallocate',
            'Any',
            'Discrete',
            'Pop_Count_4',
            'By_Renaming',
            'All_Reference',
            'Guard_Write',
            'Pop_Count_7',
            'Above_Bound',
            'By_Constraining_Incomplete',
            'Make_Root_Type',
            'By_Defining',
            'Pop_Count_6',
            'Jump_Case',
            'Push_Structure_Extended',
            'At_Offset_2',
            'Loop_Decreasing_Extended',
            'Loop_Increasing_Extended',
            'Check_In_Type',
            'Member_Write',
            'Field_Type',
            'Check_Subprogram_Elaborated',
            'At_Offset_3',
            'Is_Initialization_Repeated',
            'Unelaborated',
            'Timed_Call',
            'Field_Write',
            'At_Offset_0',
            'Equal_Zero',
            'Activate',
            'Below_Bound',
            'Set_Value',
            'Family_Cond',
            'Field_Append',
            'Is_Instruction_Error',
            'Query_Break_Address',
            'Field_Execute_Dynamic',
            'At_Offset_1',
            'All_Write',
            'Not_In_Type',
            'Unsigned',
            'Exponentiate',
            'Complete_Type',
            'Make_Visible',
            'Store_String_Extended',
            'Case_In_Range',
            'Absolute_Value',
            'Choice_Open',
            'Append',
            'Slice_Write',
            'Family_Timed',
            'Greater_Zero',
            'Binary_Scale',
            'Diana_Put_Node_On_Seq_Type',
            'Slice_Read',
            'Is_Unsigned',
            'Write_Unchecked',
            'Set_Value_Visible_Unchecked',
            'Is_Terminated',
            'Divide',
            'Is_Constrained_Object',
            'Jump_Dynamic',
            'For_Accept',
            'With_Subtype',
            'Greater_Equal',
            'Terminate_Guard_Write',
            'Rotate',
            'Store_Unchecked',
            'Pop_Control',
            'Complement',
            'Indirect',
            'Subarray',
            'Reference_Makes_Copy',
            'Break_Optional',
            'Heap_Access',
            'Has_Repeated_Initialization',
            'Get_Segment',
            'Load',
            'All_Read',
            'Query_Frame',
            'Get_Name',
            'Count_Trailing_Zeros',
            'With_Size',
            'Idle',
            'Store_Top',
            'Size',
            'Diana_Find_Permanent_Attribute',
            'Subvector',
            'Field_Read',
            'Load_Dynamic',
            'Has_Default_Initialization',
            'Incomplete',
            'Reference',
            'Module',
            'Test_And_Set_Previous',
            'With_Value',
            'Exit_Break',
            'Make_Self',
            'Not_Equal',
            'Call',
            'Diana_Seq_Type_Get_Head',
            'Load_Encached',
            'Is_Value',
            'Set_Null',
            'Not_Null',
            'For_Call',
            'Diana_Allocate_Tree_Node',
            'Make_Scope',
            'Make_Aligned',
            'Call_Dynamic',
            'Is_Scalar',
            'Hash',
            'Is_Callable',
            'Duplicate',
            'Case_Compare',
            'Less_Zero',
            'In_Range',
            'Set_Bounds',
            'Fixed',
            'Push_String_Extended_Indexed',
            'Swap_Control',
            'Elaborate',
            'Successor',
            'Remainder',
            'Jump_Zero',
            'Run_Initialization_Utility',
            'Load_Top',
            'Field_Execute',
            'Jump_Nonzero',
            'Bounds_Check',
            'Task',
            'Record',
            'Exception',
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
        assert adr & 7 in (0, 3)
        a0 = adr & ~3
        if a0 in self.subprograms:
            return
        self.subprograms.add(adr)
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
