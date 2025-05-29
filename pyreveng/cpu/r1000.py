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

# Noteworthy segments:
#   ⟦120ea4603⟧ - has unreach{ed|able} subprograms: 0x25b, 0x28b, 0x4fb

r1000_desc = """

QQUnknown		-						| unknown			|

# No comments means present in both 2fa0095f7 emulation and a9d4fb5bd

Action			Illegal,>R					| 0000				|

Action			Break_Optional					| 0007				|
Action			Idle						| 0008				|

Store_Top		Heap_Access,At_Offset_1				| 0031				|
Store_Top		Heap_Access,At_Offset_2				| 0032				|
Store_Top		Heap_Access,At_Offset_3				| 0033				|
Store_Top		Heap_Access,At_Offset_4				| 0034				|
Store_Top		Heap_Access,At_Offset_5				| 0035				|
Store_Top		Heap_Access,At_Offset_6				| 0036				|

Store_Top               Access,At_Offset_1				| 0039				|
Store_Top               Access,At_Offset_2				| 003A				|
Store_Top               Access,At_Offset_3				| 003B				|
Store_Top               Access,At_Offset_4				| 003C				|
Store_Top               Access,At_Offset_5				| 003D				|
Store_Top               Access,At_Offset_6                         	| 003E				|

Store_Top_Unchecked	Float,At_Offset_1                               | 0041				|
Store_Top_Unchecked	Float,At_Offset_2                               | 0042				|
Store_Top_Unchecked	Float,At_Offset_3                               | 0043				|
Store_Top_Unchecked	Float,At_Offset_4                               | 0044				|
Store_Top_Unchecked	Float,At_Offset_5                               | 0045				|
Store_Top_Unchecked	Float,At_Offset_6                               | 0046				|

Store_Top               Float,At_Offset_1				| 0049				|
Store_Top               Float,At_Offset_2				| 004A				|
Store_Top               Float,At_Offset_3				| 004B				|
Store_Top               Float,At_Offset_4				| 004C				|
Store_Top               Float,At_Offset_5				| 004D				|
Store_Top               Float,At_Offset_6				| 004E				|

Store_Top_Unchecked     Discrete,At_Offset_1				| 0051				|
Store_Top_Unchecked     Discrete,At_Offset_2				| 0052				|
Store_Top_Unchecked     Discrete,At_Offset_3				| 0053				|
Store_Top_Unchecked     Discrete,At_Offset_4				| 0054				|
Store_Top_Unchecked     Discrete,At_Offset_5				| 0055				|
Store_Top_Unchecked     Discrete,At_Offset_6				| 0056				|

Store_Top               Discrete,At_Offset_1				| 0059				|
Store_Top               Discrete,At_Offset_2				| 005A				|
Store_Top               Discrete,At_Offset_3				| 005B				|
Store_Top               Discrete,At_Offset_4				| 005C				|
Store_Top               Discrete,At_Offset_5				| 005D				|
Store_Top               Discrete,At_Offset_6				| 005E				|

Action			Establish_Frame					| 0068				|
Action			Query_Frame					| 0069				|
Action			Alter_Break_Mask				| 006A				|
Action			Query_Break_Address				| 006B				|
Action			Query_Break_Mask				| 006C				|
Action			Query_Break_Cause				| 006D				|
Action			Exit_Break					| 006E				|
Action			Break_Unconditional				| 006F				|

# 2fa0095f7: has it
# a9d4fb5bd: unused
Execute			Discrete,Diana_Spare2				| 0087				|

# a9d4fb5bd has comment "- execute,heap_access,diana_module_table_lookup  !other_group"
Execute			Heap_Access,Diana_Spare2			| 0088				|

# a9d4fb5bd has comment "- execute,discrete,diana_translate_sm_ptr  !other_group"
Execute			Discrete,Diana_Spare1				| 0089				|

# a9d4fb5bd has comment "- execute,discrete,diana_is_id_node  !other_group"
Execute			Discrete,Diana_Spare0				| 008A				|

Execute			Heap_Access,Diana_Seq_Type_Get_Head		| 008B				|
Execute			Heap_Access,Diana_Put_Node_On_Seq_Type		| 008C				|
Execute			Heap_Access,Diana_Allocate_Tree_Node		| 008D				|
Execute			Discrete,Diana_Arity_For_Kind			| 008E				|
Execute			Discrete,Diana_Map_Kind_To_Vci			| 008F				|

Action			Store_String_Extended,pse			| 0090				| pse				|
Action			Push_String_Extended_Indexed,pse		| 0091				| pse				|
Action			Push_String_Extended,pse			| 0092				| pse				|

# 0093: see ucode_desc

Execute			Package,Field_Reference_Dynamic			| 0095				|
Execute			Package,Field_Execute_Dynamic			| 0096				|
Execute			Package,Field_Write_Dynamic			| 0097				|
Execute			Package,Field_Read_Dynamic			| 0098				|

Action			Reference_Dynamic				| 0099				|
Action			Call_Dynamic					| 009A				|
Action			Store_Dynamic					| 009B				|
Action			Load_Dynamic					| 009C				|
Action			Jump_Nonzero_Dynamic				| 009D				|
Action			Jump_Zero_Dynamic				| 009E				|
Action			Jump_Dynamic					| 009F				|

Action			Push_Structure_Extended,abs,mark		| 00A0				| abs				|
Action			Push_Float_Extended				| 00A1				| abs				|
Action			Push_Discrete_Extended				| 00A2				| abs				|
Action			Loop_Decreasing_Extended,abs,>JC		| 00A3				| abs				|
Action			Loop_Increasing_Extended,abs,>JC		| 00A4				| abs				|
Action			Jump_Nonzero_Extended,abs,>JC			| 00A5				| abs				|
Action			Jump_Zero_Extended,abs,>JC			| 00A6				| abs				|
Action			Jump_Extended,abs,>J				| 00A7				| abs				|

Action			Increase_Priority				| 00B3				|
Action			Name_Partner					| 00B4				|
Action			Make_Parent					| 00B5				|
Action			Make_Scope					| 00B6				|
Action			Make_Self					| 00B7				|
Action			Set_Priority					| 00B8				|
Action			Get_Priority					| 00B9				|
Action			Initiate_Delay					| 00BA				|
Action			Signal_Completion,>R				| 00BB				|
Action			Signal_Activated				| 00BC				|
Action			Activate_Heap_Tasks				| 00BD				|
Action			Activate_Tasks					| 00BE				|
Action			Accept_Activation				| 00BF				|

Action			Make_Default					| 00C4				|
Action			Set_Block_Start					| 00C5				|
Action			Check_Subprogram_Elaborated			| 00C6				|
Action			Elaborate_Subprogram				| 00C7				|
Action			Pop_Auxiliary_Range				| 00C8				|
Action			Pop_Auxiliary_Loop				| 00C9				|
Action			Exit_Nullary_Function,>R			| 00CA				|
Action			Pop_Block_With_Result				| 00CB				|
Action			Pop_Block					| 00CC				|

# a9d4fb5bd has comment "- action  compress_control"
Action			Spare6_Action					| 00CD				|

Action			Pop_Auxiliary					| 00CE				|
Action			Mark_Auxiliary					| 00CF				|
Action			Swap_Control					| 00D0				|

Pop_Control		Pop_Count_1					| 00D1				|
Pop_Control		Pop_Count_2					| 00D2				|
Pop_Control		Pop_Count_3					| 00D3				|
Pop_Control		Pop_Count_4					| 00D4				|
Pop_Control		Pop_Count_5					| 00D5				|
Pop_Control		Pop_Count_6					| 00D6				|
Pop_Control		Pop_Count_7					| 00D7				|

Load_Top		At_Offset_0					| 00D8				|
Load_Top		At_Offset_1					| 00D9				|
Load_Top		At_Offset_2					| 00DA				|
Load_Top		At_Offset_3					| 00DB				|
Load_Top		At_Offset_4					| 00DC				|
Load_Top		At_Offset_5					| 00DD				|
Load_Top		At_Offset_6					| 00DE				|

#-----------------------
# feh269,1c		Value_02					|0 0 0 0|0 0 0 0|1 1 1 0|0 0 1 0|
# gc44,0046		1						|0 0 0 0|0 0 0 0|1 1 1 0|0 0 0 1|
# gc43,0036		2						|0 0 0 0|0 0 0 0|1 1 1 0|0 0 1 0|
# 2fa0095f7: emulation skips value_17
# a9d4fb5bd: has value_00 to value_31
Load_Encached		eon						|0 0 0 0|0 0 0 0|1 1 1| eon	|

Execute			Exception,Raise,>R				| 0100				|
Execute			Exception,Reraise,>R				| 0101				|

Execute			Exception,Address				| 0106				|
Execute			Exception,Get_Name				| 0107				|

#a9d4fb5bd has comment "the exception raise instruction depends on the last 8 bits being 0"
Execute			Exception,Is_Instruction_Error			| 0109				|
Execute			Exception,Is_Tasking_Error			| 010A				|
Execute			Exception,Is_Storage_Error			| 010B				|
Execute			Exception,Is_Program_Error			| 010C				|
Execute			Exception,Is_Numeric_Error			| 010D				|
Execute			Exception,Is_Constraint_Error			| 010E				|
Execute			Exception,Equal					| 010F				|

Execute			Any,Is_Initialization_Repeated			| 0110				|
Execute			Any,Has_Repeated_Initialization			| 0111				|
Execute			Any,Make_Constrained				| 0112				|

Execute			Heap_Access,Size				| 0113				|

Execute			Access,Size					| 0114				|

Execute			Any,Structure_Clear				| 0115				|
Execute			Any,Address_Of_Type				| 0116				|
Execute			Any,Structure_Query				| 0117				|
Execute			Any,Write_Unchecked				| 0118				|
Execute			Any,Check_In_Formal_Type			| 0119				|
Execute			Any,Not_In_Type					| 011A				|
Execute			Any,In_Type					| 011B				|
Execute			Any,Convert_Unchecked				| 011C				|
Execute			Any,Convert_To_Formal				| 011D				|
Execute			Any,Convert					| 011E				|
Execute			Any,Is_Scalar					| 011F				|
Execute			Any,Is_Value					| 0120				|
Execute			Any,Is_Default					| 0121				|
Execute			Any,Make_Root_Type				| 0122				|
Execute			Any,Make_Aligned				| 0123				|
Execute			Any,Is_Constrained				| 0124				|
Execute			Any,Set_Constraint				| 0125				|
Execute			Any,Has_Default_Initialization			| 0126				|
Execute			Any,Run_Initialization_Utility			| 0127				|

Execute			Any,Make_Visible				| 0129				|
Execute			Any,Change_Utility				| 012A				|

# a9d4fb5bd has comment "- execute,any,is_deallocation_allowed"
Execute			Any,Spare14					| 012B				|

Execute			Any,Size					| 012C				|
Execute			Any,Address					| 012D				|
Execute			Any,Not_Equal					| 012E				|
Execute			Any,Equal					| 012F				|

Execute			Family,Count					| 0132				|
Execute			Family,Rendezvous				| 0133				|

Execute			Entry,Count					| 0136				|
Execute			Entry,Rendezvous				| 0137				|

Execute			Select,Terminate_Guard_Write			| 013C				|
Execute			Select,Timed_Duration_Write			| 013D				|
Execute			Select,Timed_Guard_Write			| 013E				|
Execute			Select,Rendezvous				| 013F				|

Execute			Discrete,Divide_And_Scale			| 0140				|
Execute			Discrete,Multiply_And_Scale			| 0141				|

Execute			Heap_Access,Diana_Find_Permanent_Attribute	| 0142				|
Execute			Heap_Access,Adaptive_Balanced_Tree_Lookup	| 0143				|
Execute			Heap_Access,Get_Name				| 0144				|
Execute			Heap_Access,Diana_Tree_Kind			| 0145				|
Execute			Heap_Access,Hash				| 0146				|
Execute			Heap_Access,Construct_Segment			| 0147				|
Execute			Heap_Access,Get_Offset				| 0148				|

Execute			Float,Less_Equal_Zero				| 0149				|
Execute			Float,Greater_Equal_Zero			| 014A				|
Execute			Float,Less_Zero					| 014B				|
Execute			Float,Greater_Zero				| 014C				|
Execute			Float,Not_Equal_Zero				| 014D				|
Execute			Float,Equal_Zero				| 014E				|
Execute			Float,Not_In_Range				| 014F				|

Execute			Variant_Record,Make_Constrained			| 015B				|
Execute			Variant_Record,Is_Constrained_Object		| 015C				|
Execute			Variant_Record,Field_Type_Dynamic		| 015D				|
Execute			Variant_Record,Field_Reference_Dynamic		| 015E				|
Execute			Variant_Record,Field_Write_Dynamic		| 015F				|
Execute			Variant_Record,Field_Read_Dynamic		| 0160				|
Execute			Variant_Record,Check_In_Formal_Type		| 0161				|
Execute			Variant_Record,Check_In_Type			| 0162				|
Execute			Variant_Record,Not_In_Type			| 0163				|
Execute			Variant_Record,In_Type				| 0164				|
Execute			Variant_Record,Convert				| 0165				|
Execute			Variant_Record,Component_Offset			| 0166				|
Execute			Variant_Record,Structure_Query			| 0167				|
Execute			Variant_Record,Reference_Makes_Copy		| 0168				|
Execute			Variant_Record,Read_Discriminant_Constraint	| 0169				|

# 2fa0095f7: emulation has nothing
# a9d4fb5bd: has execute,variant_record,indirects_appended  !other_group
Execute			Variant_Record,Indirects_Appended		| 016A				|

Execute			Variant_Record,Read_Variant			| 016B				|
Execute			Variant_Record,Is_Constrained			| 016C				|
Execute			Variant_Record,Structure_Write			| 016D				|
Execute			Variant_Record,Not_Equal			| 016E				|
Execute			Variant_Record,Equal				| 016F				|

Execute			Record,Field_Type_Dynamic			| 0177				|
Execute			Record,Field_Reference_Dynamic			| 0178				|
Execute			Record,Field_Write_Dynamic			| 0179				|
Execute			Record,Field_Read_Dynamic			| 017A				|
Execute			Record,Convert					| 017B				|
Execute			Record,Component_Offset				| 017C				|
Execute			Record,Structure_Write				| 017D				|
Execute			Record,Not_Equal				| 017E				|
Execute			Record,Equal					| 017F				|

# a9d4fb5bd has comment "!unimplemented"
Execute			Subvector,Structure_Write			| 0188				|

Execute			Subvector,Field_Reference			| 0189				|
Execute			Subvector,Field_Write				| 018A				|
Execute			Subvector,Field_Read				| 018B				|

# a9d4fb5bd has comment "!unimplemented"
Execute			Subarray,Structure_Write			| 018C				|

Execute			Subarray,Field_Reference			| 018D				|
Execute			Subarray,Field_Write				| 018E				|
Execute			Subarray,Field_Read				| 018F				|

Execute			Matrix,Check_In_Type				| 019B				|
Execute			Matrix,Not_In_Type				| 019C				|
Execute			Matrix,In_Type					| 019D				|
Execute			Matrix,Convert_To_Formal			| 019E				|
Execute			Matrix,Convert					| 019F				|

Execute			Matrix,Subarray					| 01A3				|
Execute			Matrix,Structure_Write				| 01A4				|
Execute			Matrix,Field_Reference				| 01A5				|
Execute			Matrix,Field_Write				| 01A6				|
Execute			Matrix,Field_Read				| 01A7				|
Execute			Matrix,Element_Type				| 01A8				|
Execute			Matrix,Reverse_Bounds				| 01A9				|
Execute			Matrix,Bounds					| 01AA				|
Execute			Matrix,Length					| 01AB				|
Execute			Matrix,Last					| 01AC				|
Execute			Matrix,First					| 01AD				|
Execute			Matrix,Not_Equal				| 01AE				|
Execute			Matrix,Equal					| 01AF				|

Execute			Vector,Hash					| 01BE				|
Execute			Vector,Less_Equal				| 01BF				|
Execute			Vector,Greater_Equal				| 01C0				|
Execute			Vector,Less					| 01C1				|
Execute			Vector,Greater					| 01C2				|
Execute			Vector,Check_In_Type				| 01C3				|
Execute			Vector,Not_In_Type				| 01C4				|
Execute			Vector,In_Type					| 01C5				|
Execute			Vector,Convert_To_Formal			| 01C6				|
Execute			Vector,Convert					| 01C7				|

Execute			Vector,Prepend					| 01CA				|
Execute			Vector,Append					| 01CB				|
Execute			Vector,Catenate					| 01CC				|
Execute			Vector,Slice_Reference				| 01CD				|
Execute			Vector,Slice_Write				| 01CE				|
Execute			Vector,Slice_Read				| 01CF				|
Execute			Vector,Complement				| 01D0				|
Execute			Vector,Xor					| 01D1				|
Execute			Vector,Or					| 01D2				|
Execute			Vector,And					| 01D3				|
Execute			Vector,Structure_Write				| 01D4				|
Execute			Vector,Field_Reference				| 01D5				|
Execute			Vector,Field_Write				| 01D6				|
Execute			Vector,Field_Read				| 01D7				|
Execute			Vector,Element_Type				| 01D8				|
Execute			Vector,Reverse_Bounds				| 01D9				|
Execute			Vector,Bounds					| 01DA				|
Execute			Vector,Length					| 01DB				|
Execute			Vector,Last					| 01DC				|
Execute			Vector,First					| 01DD				|
Execute			Vector,Not_Equal				| 01DE				|
Execute			Vector,Equal					| 01DF				|

Execute			Array,Check_In_Type				| 01EB				|
Execute			Array,Not_In_Type				| 01EC				|
Execute			Array,In_Type					| 01ED				|
Execute			Array,Convert_To_Formal				| 01EE				|
Execute			Array,Convert					| 01EF				|

Execute			Array,Subarray					| 01F3				|
Execute			Array,Structure_Write				| 01F4				|
Execute			Array,Field_Reference				| 01F5				|
Execute			Array,Field_Write				| 01F6				|
Execute			Array,Field_Read				| 01F7				|
Execute			Array,Element_Type				| 01F8				|
Execute			Array,Reverse_Bounds				| 01F9				|
Execute			Array,Bounds					| 01FA				|
Execute			Array,Length					| 01FB				|
Execute			Array,Last					| 01FC				|
Execute			Array,First					| 01FD				|
Execute			Array,Not_Equal					| 01FE				|
Execute			Array,Equal					| 01FF				|

Execute			Module,Check_Elaborated				| 0206				|

# a9d4fb5bd has comment "!unimplemented
Execute			Task,Abort_Multiple				| 0208				|

Execute			Task,Abort					| 0209				|

Execute			Module,Get_Name					| 020A				|
Execute			Module,Is_Terminated				| 020B				|
Execute			Module,Is_Callable				| 020C				|
Execute			Module,Elaborate				| 020D				|
Execute			Module,Augment_Imports				| 020E				|
Execute			Module,Activate					| 020F				|

Execute			Heap_Access,Get_Segment				| 0210				|
Execute			Heap_Access,Convert_Reference			| 0211				|
Execute			Heap_Access,Address				| 0212				|
Execute			Heap_Access,Check_In_Type			| 0213				|
Execute			Heap_Access,Not_In_Type				| 0214				|
Execute			Heap_Access,In_Type				| 0215				|
Execute			Heap_Access,Convert				| 0216				|
Execute			Heap_Access,All_Reference			| 0217				|
Execute			Heap_Access,All_Write				| 0218				|
Execute			Heap_Access,All_Read				| 0219				|
Execute			Heap_Access,Element_Type			| 021A				|
Execute			Heap_Access,Set_Null				| 021B				|
Execute			Heap_Access,Not_Null				| 021C				|
Execute			Heap_Access,Is_Null				| 021D				|
Execute			Heap_Access,Maximum				| 021E				|
Execute			Heap_Access,Equal				| 021F				|

# a9d4fb5bd has comment "!unimplemented
Execute			Access,Deallocate				| 0220				|

# a9d4fb5bd has comment "!unimplemented
Execute			Access,Allow_Deallocate				| 0221				|

Execute			Access,Convert_Reference			| 0222				|
Execute			Access,Check_In_Type				| 0223				|
Execute			Access,Not_In_Type				| 0224				|
Execute			Access,In_Type					| 0225				|
Execute			Access,Convert					| 0226				|
Execute			Access,All_Reference				| 0227				|
Execute			Access,All_Write				| 0228				|
Execute			Access,All_Read					| 0229				|
Execute			Access,Element_Type				| 022A				|
Execute			Access,Set_Null					| 022B				|
Execute			Access,Not_Null					| 022C				|
Execute			Access,Is_Null					| 022D				|
Execute			Access,Not_Equal				| 022E				|
Execute			Access,Equal					| 022F				|

Execute			Float,In_Range					| 0230				|
Execute			Float,Write_Unchecked				| 0231				|
Execute			Float,Check_In_Type				| 0232				|
Execute			Float,Not_In_Type				| 0233				|
Execute			Float,In_Type					| 0234				|
Execute			Float,Round_To_Discrete				| 0235				|
Execute			Float,Truncate_To_Discrete			| 0236				|
Execute			Float,Convert_From_Discrete			| 0237				|
Execute			Float,Convert					| 0238				|
Execute			Float,Exponentiate				| 0239				|
Execute			Float,Divide					| 023A				|
Execute			Float,Times					| 023B				|
Execute			Float,Minus					| 023C				|
Execute			Float,Plus					| 023D				|
Execute			Float,Absolute_Value				| 023E				|
Execute			Float,Unary_Minus				| 023F				|
Execute			Float,Last					| 0240				|
Execute			Float,First					| 0241				|
Execute			Float,Less_Equal				| 0242				|
Execute			Float,Greater_Equal				| 0243				|
Execute			Float,Less					| 0244				|
Execute			Float,Greater					| 0245				|
Execute			Float,Not_Equal					| 0246				|
Execute			Float,Equal					| 0247				|

Execute			Discrete,Check_In_Integer			| 0248				|
Execute			Discrete,Case_In_Range				| 0249				|
Execute			Discrete,Is_Unsigned				| 024A				|
Execute			Discrete,Count_Trailing_Zeros			| 024B				|
Execute			Discrete,Count_Leading_Zeros			| 024C				|
Execute			Discrete,Count_Nonzero_Bits			| 024D				|
Execute			Discrete,Extract_Bits				| 024E				|
Execute			Discrete,Insert_Bits				| 024F				|
Execute			Discrete,Rotate					| 0250				|
Execute			Discrete,Logical_Shift				| 0251				|
Execute			Discrete,Arithmetic_Shift			| 0252				|
Execute			Discrete,Binary_Scale				| 0253				|
Execute			Discrete,Partial_Minus				| 0254				|
Execute			Discrete,Partial_Plus				| 0255				|
Execute			Discrete,Instruction_Read			| 0256				|
Execute			Discrete,Raise,>R				| 0257				|
Execute			Discrete,Test_And_Set_Next			| 0258				|
Execute			Discrete,Test_And_Set_Previous			| 0259				|
Execute			Discrete,Write_Unchecked			| 025A				|
Execute			Discrete,Check_In_Type				| 025B				|

# 2fa0095f7: emulation has nothing
# a9d4fb5bd: has execute,discrete,reverse_bounds_check
Execute			Discrete,ReverseBounds_Check			| 025C				|

Execute			Discrete,Bounds_Check				| 025D				|
Execute			Discrete,Convert				| 025E				|
Execute			Discrete,Not_In_Type				| 025F				|
Execute			Discrete,In_Type				| 0260				|
Execute			Discrete,Not_In_Range				| 0261				|
Execute			Discrete,In_Range				| 0262				|
Execute			Discrete,Above_Bound				| 0263				|
Execute			Discrete,Below_Bound				| 0264				|
Execute			Discrete,Reverse_Bounds				| 0265				|
Execute			Discrete,Bounds					| 0266				|
Execute			Discrete,Predecessor				| 0267				|
Execute			Discrete,Successor				| 0268				|
Execute			Discrete,Last					| 0269				|
Execute			Discrete,First					| 026A				|
Execute			Discrete,Maximum				| 026B				|
Execute			Discrete,Minimum				| 026C				|
Execute			Discrete,Exponentiate				| 026D				|
Execute			Discrete,Modulo					| 026E				|
Execute			Discrete,Remainder				| 026F				|
Execute			Discrete,Divide					| 0270				|
Execute			Discrete,Times					| 0271				|
Execute			Discrete,Minus					| 0272				|
Execute			Discrete,Plus					| 0273				|
Execute			Discrete,Absolute_Value				| 0274				|
Execute			Discrete,Unary_Minus				| 0275				|
Execute			Discrete,Complement				| 0276				|
Execute			Discrete,Xor					| 0277				|
Execute			Discrete,Or					| 0278				|
Execute			Discrete,And					| 0279				|
Execute			Discrete,Less_Equal				| 027A				|
Execute			Discrete,Greater_Equal				| 027B				|
Execute			Discrete,Less					| 027C				|
Execute			Discrete,Greater				| 027D				|
Execute			Discrete,Not_Equal				| 027E				|
Execute			Discrete,Equal					| 027F				|

Declare_Subprogram	For_Accept,subp					| 0299				| subp				|
Declare_Subprogram	For_Outer_Call,Visible,Unelaborated,subp	| 029A				| subp				|
Declare_Subprogram	For_Outer_Call,Unelaborated,subp		| 029B				| subp				|
Declare_Subprogram	For_Outer_Call,Visible,subp			| 029C				| subp				|
Declare_Subprogram	For_Outer_Call,subp				| 029D				| subp				|
Declare_Subprogram	For_Call,Unelaborated,subp			| 029E				| subp				|
Declare_Subprogram	For_Call,subp					| 029F				| subp				|

Declare_Subprogram	Null_Subprogram					| 02A0				|

Declare_Subprogram	For_Accept,With_Address				| 02A2				|

Declare_Subprogram	For_Outer_Call,Visible,With_Address		| 02A4				|
Declare_Subprogram	For_Outer_Call,With_Address			| 02A5				|

Declare_Subprogram	For_Call,Visible,Unelaborated,With_Address	| 02A8				|
Declare_Subprogram	For_Call,Unelaborated,With_Address		| 02A9				|
Declare_Subprogram	For_Call,Visible,With_Address			| 02AA				|
Declare_Subprogram	For_Call,With_Address				| 02AB				|

Declare_Variable	Float,Visible,With_Value,With_Constraint	| 02BE				|
Declare_Variable	Float,With_Value,With_Constraint		| 02BF				|

Declare_Variable	Any,Visible					| 02C6				|
Declare_Variable	Any						| 02C7				|

Declare_Variable	Family						| 02C9				|

Declare_Variable	Entry						| 02CB				|

Declare_Variable	Select,Choice_Open				| 02CE				|
Declare_Variable	Select						| 02CF				|

Declare_Variable	Variant_Record,Visible,With_Constraint		| 02FB				|
Declare_Variable	Variant_Record,With_Constraint			| 02FC				|
Declare_Variable	Variant_Record,Duplicate			| 02FD				|
Declare_Variable	Variant_Record,Visible				| 02FE				|
Declare_Variable	Variant_Record					| 02FF				|

Complete_Type		Variant_Record,By_Component_Completion		| 0303				|
Complete_Type		Variant_Record,By_Completing_Constraint		| 0304				|
Complete_Type		Variant_Record,By_Constraining_Incomplete	| 0305				|
Complete_Type		Variant_Record,By_Renaming			| 0306				|
Complete_Type		Variant_Record,By_Defining			| 0307				|

# a9d4fb5bd has comment: -formerly declare_type,variant_record,incomplete,constrained          !declare_group
Declare_Type		Variant_Record,Constrained_Incomplete		| 0311				|

# a9d4fb5bd has comment: -formerly declare_type,variant_record,incomplete,visible,constrained
Declare_Type		Variant_Record,Constrained_Incomplete,Visible	| 0312				|

# a9d4fb5bd has comment: -formerly declare_type,variant_record,constrained_incomplete          !declare_group
# 2fa0095f7 does not mention
# M207_54 does not implement
# ?			?						| 0313				|

# a9d4fb5bd has comment: -formerly declare_type,variant_record,constrained_incomplete,visible  !declare_group
# 2fa0095f7 does not mention
# M207_54 does not implement
# ?			?						| 0314				|

Declare_Type		Variant_Record,Defined_Incomplete		| 0315				|
Declare_Type		Variant_Record,Defined_Incomplete,Visible	| 0316				|

Declare_Type		Variant_Record,Incomplete			| 0318				|
Declare_Type		Variant_Record,Incomplete,Visible		| 0319				|

Declare_Type		Variant_Record,Constrained			| 031B				|
Declare_Type		Variant_Record,Constrained,Visible		| 031C				|
Declare_Type		Variant_Record,Defined				| 031D				|
Declare_Type		Variant_Record,Defined,Visible			| 031E				|

Declare_Variable	Record,Duplicate				| 0320				|
Declare_Variable	Record,Visible					| 0321				|
Declare_Variable	Record						| 0322				|

Complete_Type		Record,By_Component_Completion			| 0324				|
Complete_Type		Record,By_Renaming				| 0325				|
Complete_Type		Record,By_Defining				| 0326				|

Declare_Type		Record,Defined_Incomplete			| 0327				|
Declare_Type		Record,Defined_Incomplete,Visible		| 0328				|

Declare_Type		Record,Incomplete				| 032A				|
Declare_Type		Record,Incomplete,Visible			| 032B				|

Declare_Type		Record,Defined					| 032D				|
Declare_Type		Record,Defined,Visible				| 032E				|

Declare_Variable	Array,Visible,With_Constraint			| 0333				|
Declare_Variable	Array,With_Constraint				| 0334				|
Declare_Variable	Array,Duplicate					| 0335				|
Declare_Variable	Array,Visible					| 0336				|
Declare_Variable	Array						| 0337				|

Complete_Type		Array,By_Component_Completion			| 0340				|
Complete_Type		Array,By_Constraining				| 0341				|
Complete_Type		Array,By_Renaming				| 0342				|
Complete_Type		Array,By_Defining				| 0343				|

Declare_Type		Array,Constrained_Incomplete,Bounds_With_Object		| 0346				|
Declare_Type		Array,Constrained_Incomplete,Visible,Bounds_With_Object	| 0347				|
Declare_Type		Array,Defined_Incomplete,Bounds_With_Object		| 0348				|
Declare_Type		Array,Defined_Incomplete,Visible,Bounds_With_Object	| 0349				|

Declare_Type		Array,Incomplete,Bounds_With_Object			| 034B				|
Declare_Type		Array,Incomplete,Visible,Bounds_With_Object		| 034C				|

# 2fa0095f7: emulation has nothing
# a9d4fb5bd has it
Declare_Type		Array,Constrained,Bounds_With_Object		| 034E				|

Declare_Type		Array,Constrained,Visible,Bounds_With_Object	| 034F				|
Declare_Type		Array,Defined,Bounds_With_Object		| 0350				|
Declare_Type		Array,Defined,Visible,Bounds_With_Object	| 0351				|

Declare_Type		Array,Constrained_Incomplete			| 0353				|
Declare_Type		Array,Constrained_Incomplete,Visible		| 0354				|
Declare_Type		Array,Defined_Incomplete			| 0355				|
Declare_Type		Array,Defined_Incomplete,Visible		| 0356				|

Declare_Type		Array,Incomplete				| 0358				|
Declare_Type		Array,Incomplete,Visible			| 0359				|

Declare_Type		Array,Constrained				| 035B				|
Declare_Type		Array,Constrained,Visible			| 035C				|
Declare_Type		Array,Defined					| 035D				|
Declare_Type		Array,Defined,Visible				| 035E				|

Declare_Variable	Task,On_Processor,As_Component			| 036A				|
Declare_Variable	Task,As_Component				| 036B				|
Declare_Variable	Task,Visible,On_Processor			| 036C				|
Declare_Variable	Task,On_Processor				| 036D				|
Declare_Variable	Task,Visible					| 036E				|
Declare_Variable	Task						| 036F				|

Complete_Type		Task,By_Renaming				| 0374				|

Declare_Type		Task,Incomplete					| 0377				|
Declare_Type		Task,Incomplete,Visible				| 0378				|

Declare_Type		Task,Defined,Not_Elaborated			| 037A				|
Declare_Type		Task,Defined,Visible,Not_Elaborated		| 037B				|

Declare_Type		Task,Defined					| 037D				|
Declare_Type		Task,Defined,Visible				| 037E				|

Declare_Variable	Package,Visible,On_Processor			| 0384				|
Declare_Variable	Package,On_Processor				| 0385				|
Declare_Variable	Package,Visible					| 0386				|
Declare_Variable	Package						| 0387				|

Declare_Type		Package,Defined,Not_Elaborated			| 038C				|
Declare_Type		Package,Defined,Visible,Not_Elaborated		| 038D				|
Declare_Type		Package,Defined					| 038E				|
Declare_Type		Package,Defined,Visible				| 038F				|

Declare_Variable	Heap_Access,Visible,By_Allocation,With_Value		| 0395				|
Declare_Variable	Heap_Access,By_Allocation,With_Value			| 0396				|
Declare_Variable	Heap_Access,Visible,By_Allocation,With_Subtype		| 0397				|
Declare_Variable	Heap_Access,By_Allocation,With_Subtype			| 0398				|
Declare_Variable	Heap_Access,Visible,By_Allocation,With_Constraint	| 0399				|
Declare_Variable	Heap_Access,By_Allocation,With_Constraint		| 039A				|
Declare_Variable	Heap_Access,Visible,By_Allocation			| 039B				|
Declare_Variable	Heap_Access,By_Allocation				| 039C				|
Declare_Variable	Heap_Access,Duplicate					| 039D				|
Declare_Variable	Heap_Access,Visible					| 039E				|
Declare_Variable	Heap_Access						| 039F				|

Complete_Type		Heap_Access,By_Component_Completion				| 03A0				|
Complete_Type		Heap_Access,By_Constraining					| 03A1				|
Complete_Type		Heap_Access,By_Renaming						| 03A2				|
Complete_Type		Heap_Access,By_Defining						| 03A3				|

Declare_Type		Heap_Access,Incomplete,Values_Relative,With_Size		| 03A4				|
Declare_Type		Heap_Access,Incomplete,Values_Relative				| 03A5				|
Declare_Type		Heap_Access,Incomplete,Visible,Values_Relative			| 03A6				|
Declare_Type		Heap_Access,Incomplete,Visible,Values_Relative,With_Size	| 03A7				|
Declare_Type		Heap_Access,Incomplete						| 03A8				|
Declare_Type		Heap_Access,Incomplete,Visible					| 03A9				|

Declare_Type		Heap_Access,Constrained				| 03AB				|
Declare_Type		Heap_Access,Constrained,Visible			| 03AC				|
Declare_Type		Heap_Access,Defined				| 03AD				|
Declare_Type		Heap_Access,Defined,Visible			| 03AE				|

Declare_Variable	Access,Visible,By_Allocation,With_Value		| 03B5				|
Declare_Variable	Access,By_Allocation,With_Value			| 03B6				|
Declare_Variable	Access,Visible,By_Allocation,With_Subtype	| 03B7				|
Declare_Variable	Access,By_Allocation,With_Subtype		| 03B8				|
Declare_Variable	Access,Visible,By_Allocation,With_Constraint	| 03B9				|
Declare_Variable	Access,By_Allocation,With_Constraint		| 03BA				|
Declare_Variable	Access,Visible,By_Allocation			| 03BB				|
Declare_Variable	Access,By_Allocation				| 03BC				|
Declare_Variable	Access,Duplicate				| 03BD				|
Declare_Variable	Access,Visible					| 03BE				|
Declare_Variable	Access						| 03BF				|

Complete_Type		Access,By_Component_Completion			| 03C4				|
Complete_Type		Access,By_Constraining				| 03C5				|
Complete_Type		Access,By_Renaming				| 03C6				|

# 2fa0095f7: emulation has nothing
Complete_Type		Access,By_Defining				| 03C7				|

Declare_Type		Access,Incomplete,Accesses_Protected		| 03CC				|
Declare_Type		Access,Incomplete,Visible,Accesses_Protected	| 03CD				|
Declare_Type		Access,Incomplete				| 03CE				|
Declare_Type		Access,Incomplete,Visible			| 03CF				|

Declare_Type		Access,Constrained				| 03D1				|
Declare_Type		Access,Constrained,Visible			| 03D2				|
Declare_Type		Access,Defined,Accesses_Protected		| 03D3				|
Declare_Type		Access,Defined,Visible,Accesses_Protected	| 03D4				|
Declare_Type		Access,Defined					| 03D5				|
Declare_Type		Access,Defined,Visible				| 03D6				|

Declare_Variable	Float,Duplicate					| 03D8				|
Declare_Variable	Float,Visible					| 03D9				|
Declare_Variable	Float						| 03DA				|
Declare_Variable	Float,Visible,With_Value			| 03DB				|

Complete_Type		Float,By_Constraining				| 03DC				|
Complete_Type		Float,By_Renaming				| 03DD				|
Complete_Type		Float,By_Defining				| 03DE				|

Declare_Variable	Float,With_Value				| 03DF				|

Declare_Type		Float,Incomplete				| 03E0				|
Declare_Type		Float,Incomplete,Visible			| 03E1				|

Declare_Type		Float,Constrained				| 03E3				|
Declare_Type		Float,Constrained,Visible			| 03E4				|
Declare_Type		Float,Defined					| 03E5				|
Declare_Type		Float,Defined,Visible				| 03E6				|

Declare_Variable	Discrete,Visible,With_Value,With_Constraint	| 03E8				|
Declare_Variable	Discrete,Duplicate				| 03E9				|
Declare_Variable	Discrete,Visible				| 03EA				|
Declare_Variable	Discrete					| 03EB				|
Declare_Variable	Discrete,With_Value,With_Constraint		| 03EC				|

Complete_Type		Discrete,By_Constraining			| 03ED				|
Complete_Type		Discrete,By_Renaming				| 03EE				|
Complete_Type		Discrete,By_Defining				| 03EF				|

Declare_Variable	Discrete,Visible,With_Value			| 03F0				|
Declare_Variable	Discrete,With_Value				| 03F1				|
Declare_Variable	Discrete,Incomplete,Unsigned			| 03F2				|
Declare_Variable	Discrete,Incomplete,Visible,Unsigned		| 03F3				|

Declare_Variable	Discrete,Incomplete				| 03F5				|
Declare_Variable	Discrete,Incomplete,Visible			| 03F6				|

Declare_Type		Discrete,Constrained				| 03F8				|
Declare_Type		Discrete,Constrained,Visible			| 03F9				|
Declare_Type		Discrete,Defined,With_Size			| 03FA				|
Declare_Type		Discrete,Defined,Visible,With_Size		| 03FB				|

Declare_Type		Discrete,Defined				| 03FD				|

# 2fa0095f7: emulation has nothing
Declare_Type		Discrete,Defined,Visible			| 03FE				|

Execute_Immediate	Set_Value_Visible_Unchecked,uimmediate		|0 0 0 0|0 1 0 0|   uimmediate  |
Execute_Immediate	Set_Value_Visible,uimmediate			|0 0 0 0|0 1 0 1|   uimmediate  |
Execute_Immediate	Set_Value_Unchecked,uimmediate			|0 0 0 0|0 1 1 0|   uimmediate	|
Execute_Immediate	Set_Value,uimmediate				|0 0 0 0|0 1 1 1|   uimmediate  |

Execute_Immediate	Raise,uimmediate,>R				|0 0 0 0|1 0 0 0|   uimmediate  |

Execute_Immediate	Binary_Scale,limitedpos				|0 0 0 0|1 0 0 1|0 0| limitedpos|
Execute_Immediate	Logical_Shift,limitedneg			|0 0 0 0|1 0 0 1|0 1| limitedneg|
Execute_Immediate	Logical_Shift,limitedpos			|0 0 0 0|1 0 0 1|1 0| limitedpos|
Execute_Immediate	Binary_Scale,limitedneg				|0 0 0 0|1 0 0 1|1 1| limitedneg|

# a9d4fb5bd splits in two
Execute_Immediate	Plus,s8						|0 0 0 0|1 0 1 0|	s8	|

Execute_Immediate	Case_Compare,uimmediate				|0 0 0 0|1 0 1 1|   uimmediate	|
Execute_Immediate	Greater_Equal,uimmediate			|0 0 0 0|1 1 0 0|   uimmediate	|
Execute_Immediate	Less,uimmediate					|0 0 0 0|1 1 0 1|   uimmediate	|
Execute_Immediate	Not_Equal,uimmediate				|0 0 0 0|1 1 1 0|   uimmediate	|
Execute_Immediate	Equal,uimmediate				|0 0 0 0|1 1 1 1|   uimmediate	|

Execute			Select,Guard_Write,fieldnum			|0 0 0 1|0 0 0 0|    fieldnum   |
Execute			Select,Member_Write,fieldnum			|0 0 0 1|0 0 0 1|    fieldnum   |
Execute			Task,Family_Timed,fieldnum			|0 0 0 1|0 0 1 0|    fieldnum   |
Execute			Task,Family_Cond,fieldnum			|0 0 0 1|0 0 1 1|    fieldnum   |
Execute			Task,Family_Call,fieldnum			|0 0 0 1|0 1 0 0|    fieldnum   |
Execute			Task,Timed_Call,fieldnum			|0 0 0 1|0 1 0 1|    fieldnum   |
Execute			Task,Conditional_Call,fieldnum			|0 0 0 1|0 1 1 0|    fieldnum   |
Execute			Task,Entry_Call,fieldnum			|0 0 0 1|0 1 1 1|    fieldnum   |
Execute			Package,Field_Execute,fieldnum			|0 0 0 1|1 0 0 0|    fieldnum   |
Execute			Package,Field_Reference,fieldnum		|0 0 0 1|1 0 0 1|    fieldnum   |
Execute			Package,Field_Write,fieldnum			|0 0 0 1|1 0 1 0|    fieldnum	|
Execute			Package,Field_Read,fieldnum			|0 0 0 1|1 0 1 1|    fieldnum	|

Execute_Immediate	Run_Utility,uimmediate				|0 0 0 1|1 1 0 0|   uimmediate  |

Execute_Immediate	Reference_Lex_1,uimmediate			|0 0 0 1|1 1 0 1|   uimmediate	|

Execute			Variant_Record,Set_Variant,fieldnum			|0 0 1 0|0 0 0 0|    fieldnum   |
Execute			Variant_Record,Set_Bounds,fieldnum			|0 0 1 0|0 0 0 1|    fieldnum   |
Execute			Variant_Record,Field_Constrain,fieldnum			|0 0 1 0|0 0 1 0|    fieldnum   |
Execute			Variant_Record,Field_Type,fieldnum			|0 0 1 0|0 0 1 1|    fieldnum   |
Execute			Variant_Record,Field_Reference,Fixed,Direct,fieldnum	|0 0 1 0|0 1 0 0|    fieldnum   |
Execute			Variant_Record,Field_Reference,Fixed,Indirect,fieldnum	|0 0 1 0|0 1 0 1|    fieldnum   |
Execute			Variant_Record,Field_Reference,Variant,Direct,fieldnum	|0 0 1 0|0 1 1 0|    fieldnum   |
Execute			Variant_Record,Field_Reference,Variant,Indirect,fieldnum|0 0 1 0|0 1 1 1|    fieldnum   |
Execute			Variant_Record,Field_Write,Fixed,Direct,fieldnum	|0 0 1 0|1 0 0 0|    fieldnum   |
Execute			Variant_Record,Field_Write,Fixed,Indirect,fieldnum	|0 0 1 0|1 0 0 1|    fieldnum   |
Execute			Variant_Record,Field_Write,Variant,Direct,fieldnum	|0 0 1 0|1 0 1 0|    fieldnum   |
Execute			Variant_Record,Field_Write,Variant,Indirect,fieldnum	|0 0 1 0|1 0 1 1|    fieldnum   |
Execute			Variant_Record,Field_Read,Fixed,Direct,fieldnum		|0 0 1 0|1 1 0 0|    fieldnum   |
Execute			Variant_Record,Field_Append,Fixed,Indirect,fieldnum	|0 0 1 0|1 1 0 1|    fieldnum   |
Execute			Variant_Record,Field_Read,Variant,Direct,fieldnum	|0 0 1 0|1 1 1 0|    fieldnum   |
Execute			Variant_Record,Field_Append,Variant,Indirect,fieldnum	|0 0 1 0|1 1 1 1|    fieldnum   |

Execute			Record,Field_Type,fieldnum			|0 0 1 1|0 0 0 0|    fieldnum   |

Execute			Record,Field_Reference,fieldnum			|0 0 1 1|0 1 0 0|    fieldnum   |

# 2fa0095f7: unsigned arg
# See also Loop_Increasing
Loop_Decreasing		pcrelneg,>JC					|0 0 1 1|0 1 1| pcrelneg        |

Execute			Record,Field_Write,fieldnum			|0 0 1 1|1 0 0 0|    fieldnum   |

Execute			Record,Field_Read,fieldnum			|0 0 1 1|1 1 0 0|    fieldnum   |

# 2fa0095f7: unsigned arg
# g44,005d		-5						|0 0 1 1|1 1 1 1|1 1 1 1|1 0 1 1|
Loop_Increasing		pcrelneg,>JC					|0 0 1 1|1 1 1| pcrelneg	|

End_Rendezvous		>R,parmcnt					|0 1 0 0|0 0 0 1|    parmcnt	|

Exit_Subprogram		From_Utility,With_Result,>R,topoffset		|0 1 0 0|0 0 1 0|   topoffset	|
Exit_Subprogram		From_Utility,>R,topoffset			|0 1 0 0|0 0 1 1|   topoffset	|
Exit_Subprogram		With_Result,>R,topoffset			|0 1 0 0|0 1 0 0|   topoffset	|
Exit_Subprogram		topoffset,>R					|0 1 0 0|0 1 0 1|   topoffset	|

# ⟦fad6fc6ba⟧ limits the argument to 8 bits
# /phk
# 4e00 CASE_MAXIMUM (and 0x1ff) = 9 bits (2fa0095f7)
Jump_Case		case_max					|0 1 0 0|0 1 1|   case_max	|

# signed or unsigned ?!
# 2fa0095f7: unsigned, but emulation of 2fa0095f7 needs signed.
Short_Literal		slit						|0 1 0 0|1| slit		|

Indirect_Literal	Any,pcrel,literal				|0 1 0 1|0| pcrel               |
Indirect_Literal	Float,pcrel,dbl					|0 1 0 1|1| pcrel		|
Indirect_Literal	Discrete,pcrel,literal				|0 1 1 0|0| pcrel		|

Jump_Zero		pcrel,>JC					|0 1 1 0|1| pcrel		|
Jump_Nonzero		pcrel,>JC					|0 1 1 1|0| pcrel		|
Jump			pcrel,>J					|0 1 1 1|1| pcrel		|

Call			llvl,ldelta					|1 0 0| llvl  | ldelta		|
Reference		zdelta						|1 0 1|0 0 0 0| zdelta		|
Store_Unchecked		llvl,ldelta					|1 0 1| llvl  | ldelta		|
Store			llvl,ldelta					|1 1 0| llvl  | ldelta		|
Load			llvl,ldelta					|1 1 1| llvl  | ldelta		|
"""

# Instructions decoded by M207_54.M200_UCODE but not explained elsewhere
ucode_desc = """


QQUnknown		InMicrocode					| 0001				|
QQUnknown		InMicrocode					| 0002				|
QQUnknown		InMicrocode					| 0003				|
QQUnknown		InMicrocode					| 0004				|
QQUnknown		InMicrocode					| 0005				|
QQUnknown		InMicrocode					| 0006				|

QQUnknown		InMicrocode					| 0009				|
QQUnknown		InMicrocode					| 000A				|
QQUnknown		InMicrocode					| 000B				|
QQUnknown		InMicrocode					| 000C				|
QQUnknown		InMicrocode					| 000D				|
QQUnknown		InMicrocode					| 000E				|
QQUnknown		InMicrocode					| 000F				|


# a9d4fb5bd has comment "- temporarily being used for performance analysis"
QQUnknown		InMicrocode					|0 0 0 0|0 0 0 0|0 0 0 1| x	|

# Same Microcode as 0x0145 Execute Heap_Access,Diana_Tree_Kind
QQUnknown		InMicrocode					| 0070				|

QQUnknown		InMicrocode					| 0071				|
QQUnknown		InMicrocode					| 0072				|
QQUnknown		InMicrocode					| 0073				|
QQUnknown		InMicrocode					| 0074				|
QQUnknown		InMicrocode					| 0075				|
QQUnknown		InMicrocode					| 0076				|

# a9d4fb5bd has comment "- TEMPORARILY BEING USED FOR COLLECTION_RESET -- DO NOT REUSE"
QQUnknown		InMicrocode					| 0080				|

QQUnknown		InMicrocode					| 0081				|
QQUnknown		InMicrocode					| 0082				|

# a9d4fb5bd: unused
# 2fa0095f7: Action, Spare7_Action
# guru course at pg43,001c comments this as "push full address of a location in current code segment"
PushFullAddress		InMicrocode,caddr				| 0093				| caddr				|

QQUnknown		InMicrocode					| 00A8				|
QQUnknown		InMicrocode					| 00A9				|
QQUnknown		InMicrocode					| 00AA				|
QQUnknown		InMicrocode					| 00AB				|
QQUnknown		InMicrocode					| 00AC				|

# Guess, Fits parameters, Field_Execute_Dynamic is not used elsewhere.
# Terminal_Essai.Recoit.Nouveau_Caractere (No, C); (785f3e358,2c9c18aad)
Action			InMicrocode,Package,Field_Execute_Dynamic	| 00AD				|

QQUnknown		InMicrocode					| 0128				|
QQUnknown		InMicrocode					| 0205				|
Declare_Type		InMicrocode,Discrete				| 03F7				|
Declare_Type		InMicrocode,Discrete				| 03FC				|

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

    def assy_caddr(self):
        self.dstadr = self['caddr']
        if self.dstadr:
            self.lang.subprogram(self.dstadr)
            return assy.Arg_dst(self.lang.m, self.dstadr)

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
        # From Guru_Course_01 pdf page 38
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

    def assy_zdelta(self):
        v = self['zdelta']
        return "0x0,0x%x" % v

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
        self.add_ins(ucode_desc, r1000_ins)
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
            'InMicrocode',
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
