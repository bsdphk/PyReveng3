package Machine_Code is

   pragma Subsystem (Ada_Base);

   pragma Module_Name (4, 67);

   Version : constant := 15;

   type Operand_Class is (
                          Discrete_Class,
                          Float_Class,
                          Access_Class,
                          Heap_Access_Class,
                          Package_Class,
                          Task_Class,
                          Module_Class,
                          Array_Class,
                          Vector_Class,
                          Matrix_Class,
                          Subarray_Class,
                          Subvector_Class,
                          Record_Class,
                          Variant_Record_Class,
                          Select_Class,
                          Entry_Class,
                          Family_Class,
                          Exception_Class,
                          Any_Class
                         );

   type Operation is (
                      Equal_Op,
                      Not_Equal_Op,
                      Greater_Op,
                      Less_Op,

                      Greater_Equal_Op,
                      Less_Equal_Op,
                      Case_Compare_Op,

                      Below_Bound_Op,
                      Above_Bound_Op,
                      In_Range_Op,

                      Not_In_Range_Op,
                      Case_In_Range_Op,
                      Bounds_Check_Op,

                      Reverse_Bounds_Check_Op,
                      Bounds_Op,
                      Reverse_Bounds_Op,

                      First_Op,
                      Last_Op,
                      Set_Value_Op,
                      Set_Value_Unchecked_Op,

                      Set_Value_Visible_Op,
                      Set_Value_Visible_Unchecked_Op,

                      Test_And_Set_Previous_Op,
                      Test_And_Set_Next_Op,

                      Successor_Op,
                      Predecessor_Op,
                      And_Op,
                      Or_Op,
                      Xor_Op,

                      Complement_Op,
                      Unary_Minus_Op,
                      Absolute_Value_Op,

                      Plus_Op,
                      Minus_Op,
                      Times_Op,
                      Divide_Op,
                      Modulo_Op,

                      Remainder_Op,
                      Minimum_Op,
                      Maximum_Op,
                      Exponentiate_Op,

                      Binary_Scale_Op,
                      Multiply_And_Scale_Op,

                      Divide_And_Scale_Op,
                      Partial_Plus_Op,
                      Partial_Minus_Op,

                      Arithmetic_Shift_Op,
                      Logical_Shift_Op,

                      Rotate_Op,
                      Insert_Bits_Op,
                      Extract_Bits_Op,

                      Is_Unsigned_Op,
                      Count_Nonzero_Bits_Op,

                      Count_Leading_Zeros_Op,
                      Count_Trailing_Zeros_Op,

                      Round_To_Discrete_Op,
                      Truncate_To_Discrete_Op,

                      Convert_From_Discrete_Op,
                      Equal_Zero_Op,

                      Not_Equal_Zero_Op,
                      Greater_Zero_Op,
                      Less_Zero_Op,

                      Greater_Equal_Zero_Op,
                      Less_Equal_Zero_Op,
                      Is_Null_Op,

                      Not_Null_Op,
                      Set_Null_Op,
                      Element_Type_Op,
                      All_Read_Op,

                      All_Write_Op,
                      All_Reference_Op,
                      Convert_Reference_Op,

                      Allow_Deallocate_Op,
                      Deallocate_Op,
                      Hash_Op,

                      Construct_Segment_Op,
                      Get_Segment_Op,
                      Get_Offset_Op,

                      Diana_Tree_Kind_Op,
                      Diana_Map_Kind_To_Vci_Op,

                      Diana_Arity_For_Kind_Op,
                      Diana_Allocate_Tree_Node_Op,

                      Diana_Put_Node_On_Seq_Type_Op,
                      Diana_Seq_Type_Get_Head_Op,

                      Diana_Find_Permanent_Attribute_Op,
                      Diana_Spare0_Op,

                      Diana_Spare1_Op,
                      Diana_Spare2_Op,

                      Adaptive_Balanced_Tree_Lookup_Op,
                      Elaborate_Op,
                      Check_Elaborated_Op,

                      Augment_Imports_Op,
                      Activate_Op,
                      Abort_Op,

                      Abort_Multiple_Op,
                      Redezvous_Op,
                      Count_Op,

                      Is_Callable_Op,
                      Is_Terminated_Op,

                      Timed_Duration_Write_Op,
                      Terminate_Guard_Write_Op,

                      Timed_Guard_Write_Op,
                      Lenght_Op,

                      Structure_Write_Op,
                      Structure_Clear_Op,

                      Slice_Read_Op,
                      Slice_Write_Op,

                      Slice_Reference_Op,
                      Catenate_Op,

                      Append_Op,
                      Prepend_Op,
                      Subarray_Op,

                      Component_Offset_Op,
                      Is_Constrained_Op,

                      Is_Constrained_Object_Op,
                      Make_Constrained_Op,

                      Indirect_Appended_Op,
                      Structure_Query_Op,

                      Reference_Makes_Copy_Op,
                      Read_Variant_Op,

                      Read_Discriminant_Constraint_Op,

                      Field_Read_Op,
                      Field_Write_Op,

                      Field_Reference_Op,
                      Field_Append_Op,

                      Field_Type_Op,
                      Field_Constrain_Op,

                      Set_Bounds_Op,
                      Set_Variant_Op,

                      Field_Execute_Op,
                      Entry_Call_Op,

                      Conditional_Call_Op,
                      Timed_Call_Op,

                      Family_Call_Op,
                      Family_Timed_Op,

                      Family_Conditional_Op,
                      Guard_Write_Op,

                      Member_Write_Op,
                      Write_Unchecked_Op,

                      Field_Read_Dynamic_Op,
                      Field_Write_Dynamic_Op,

                      Field_Type_Dynamic_Op,
                      Field_Execute_Dynamic_Op,

                      Field_Reference_Dynamic_Op,

                      Reference_Lex_1_Op,
                      Convert_Op,

                      Convert_Unchecked_Op,
                      Convert_To_Formal_Op,

                      Check_In_Type_Op,
                      Check_In_Formal_Type_Op,

                      Check_In_Integer_Op,
                      In_Type_Op,

                      Not_In_Type_Op,
                      Address_Op,
                      Size_Op,

                      AddresS_Of_Type_Op,
                      Make_Root_Type_Op,

                      Set_Constraint_Op,
                      Is_Value_Op,

                      Is_Scalar_Op,
                      Is_Default_Op,

                      Make_Visible_Op,
                      Make_Aligned_Op,

                      Run_Utility_Op,
                      Change_Utility_Op,

                      Has_Default_Initialization_Op,

                      Has_Repeated_Initialization_Op,

                      Is_Initialization_Repated_Op,
                      Raise_Op,
                      Reraise_Op,

                      Get_Name_Op,
                      Is_Constraint_Error_Op,

                      Is_Numeric_Error_Op,
                      Is_Program_error_Op,

                      Is_Tasking_Error_Op,
                      Is_Storage_Error_Op,

                      Is_Instruction_Error_Op,
                      Instruction_Read_Op,

                      Spare14_Op,
                      Spare15_Op,
                      Spare16_Op,
                      Spare17_Op,
                      Spare18_Op,
                      Spare19_Op,
                      Spare20_Op,
                      Spare21_Op,
                      Spare22_Op,
                      Spare23_Op,
                      Spare24_Op,
                      Spare25_Op
                     );

   type Type_Sort is (
                      Defined,
                      Constrained,
                      Incomplete,
                      Defined_Incomplete,
                      Constrained_Incomplete
                     );

   type Type_Option_Set is
      record
         Is_Visible : Boolean;
         Unsigned : Boolean;
         With_Size : Boolean;
         Access_Protected : Boolean;
         Values_Relative : Boolean;
         Bounds_With_Object : Boolean;
         Not_Elaborated : Boolean;
      end record;

   type Type_Completion_Mode is (
                                 By_Defining,
                                 By_Renaming,
                                 By_Constraining,
                                 By_Constraining_Incomplete,
                                 By_Completing_Constraint,
                                 By_Component_Completion
                                );

   type Variable_Option_Set is
      record
         Is_Visible : Boolean;
         Duplicate : Boolean;
         By_Allocation : Boolean;
         With_Constraint : Boolean;
         With_Subtype : Boolean;
         With_Value : Boolean;
         As_Component : Boolean;
         On_Processor : Boolean;
         Choice_Open : Boolean;
      end record;

   type Subprogram_Sort is (
                            For_Call,
                            For_Outher_Call,
                            For_Accept,
                            Null_Subprogram
                           );

   type Subprogram_Option_Set is
      record
         Is_Visible : Boolean;
         Not_Elaborated : Boolean;
         With_Address : Boolean;
      end record;

   type Exit_Option_Set is
      record
         With_Result : Boolean;
         From_Utility : Boolean;
      end record;

   Field_Index_Size : constant Integer := 8;

   type Field_Index is new Integer range 0 .. 2 ** Field_Index_Size - 1;

   subtype Variant_Record_Index is Field_Index range 1 .. Field_Index'Last;

   No_Variants : constant Variant_Record_Index := Field_Index'Last;

   type Field_Sort is (
                       Fixed,
                       Variant
                      );

   type Field_Mode is (
                       Direct,
                       Indirect
                      );

   subtype Field_Op is Operation range Field_Read_Op .. Member_Write_Op;

   subtype Component_Op is Field_Op range Field_Read_Op .. Field_Append_Op;

   type Access_Spec (
                     Op : Operation := Equal_Op
                    ) is
      record
         case Op is
            when Component_Op =>
               Kind : Field_Sort;
               Mode : Field_Mode;
            when others =>
               null;
         end case;
      end record;

   type Field_Spec (
                    Class : Operand_Class := Discrete_Class;
                    Op : Operation := Equal_Op
                   ) is
      record
         case Class is
            when Package_Class | Task_Class =>
               Offset : Field_Index;
            when Record_Class | Select_Class =>
               Number : Field_Index;
            when Variant_Record_Class =>
               Index : Field_Index;
               Component : Access_Spec (Op);
            when others =>
               null;
         end case;
      end record;

   type Operator_Spec (
                       Class : Operand_Class := Discrete_Class;
                       Op : Operation := Equal_Op
                      ) is
      record
         case Op is
            when Field_Op =>
               Field : Field_Spec (Class, Op);
            when others =>
               null;
         end case;
      end record;

   type Lexical_Level is new Integer range 0 .. 15;

   type Lexical_Delta is new Integer range -256 .. 511;

   subtype Scope_Delta is Lexical_Delta range 0 .. 511;

   subtype Frame_Delta is Lexical_Delta range -256 .. 255;

   type Object_Reference is
      record
         Level : Lexical_Level;
         Offset : Lexical_Delta;
      end record;

   type Inner_Frame_Delta is new Integer range 0 .. 2 ** 8 - 1;

   type Parameter_Count is new Integer range 0 .. 2 ** 8 - 1;

   type Pc_Offset is new Integer range -2 ** 10 .. 2 ** 10 - 1;

   subtype Loop_Offset is Pc_Offset range -2 ** 9 .. -1;

   type Case_Maximum is new Integer range 0 .. 2 ** 9 - 1;

   type Stack_Top_Offset is new Integer range -6 .. 0;

   type Stack_Pop_Count is new Integer range 1 .. 7;

   type Encached_Object_Number is new Integer range 0 .. 31;

   type Symbolic_Label is new Integer;

   type Segment_Index is new Integer range 0 .. 2 ** 3 - 1;

   type Segment_Displacement is new Integer range 0 .. 2 ** 12 - 1;

   type Segment_Reference is
      record
         Offset : Segment_Displacement;
         Index : Segment_Index;
      end record;

   type Short_Literal_Value is new Integer range -2 ** 10 .. 2 ** 10 - 1;

   type Partial_Structure is new Long_Integer range 0 .. 2 ** 32 - 1;

   type Structure_Literal_Value is
      record
         High : Partial_Structure;
         Low : Partial_Structure;
      end record;

   type Literal (
                 Of_Kind : Operand_Class := Discrete_Class
                ) is
      record
         case Of_Kind is
            when Discrete_Class =>
               Discrete_Literal : Long_Integer;
            when Float_Class =>
               Float_Literal : Float;
            when Any_Class =>
               Structure_Literal : Structure_Literal_Value;
            when others =>
               null;
         end case;
      end record;

   type Unsigned_Immediate_Value is new Integer range 0 .. 255;

   type Signed_Immediate_Value is new Integer range -128 .. 127;

   type Immediate_Value (
                         Is_Signed : Boolean := True
                        ) is
      record
         case Is_Signed is
            when True =>
               Signed_Value : Signed_Immediate_Value;
            when False =>
               Unsigned_Value : Unsigned_Immediate_Value;
         end case;
      end record;

   type Extended_Literal is new Integer range 0 .. 2 ** 16 - 1;

   type Extension_Kind is (Is_Literal, Is_Location);

   type Instruction_Extension (
                               Of_Kind : Extension_Kind := Is_Literal
                              ) is
      record
         case Of_Kind is
            when Is_Literal =>
               Value : Extended_Literal;
            when Is_Location =>
               Location : Segment_Reference;
         end case;
      end record;

   type Unclassed_Action is (
                             Illegal,
                             Idle,

                             Elaborate_Subprogram,
                             Check_Subprogram_Elaborated,

                             Accept_Activation,
                             Activate_Tasks,
                             Activate_Heap_Tasks,

                             Signal_Activated,
                             Signal_Completion,
                             Propagate_Abort,

                             Set_Priority,
                             Increase_Priority,
                             Get_Priority,

                             Initiate_Delay,
                             Exit_Nullary_Function,
                             Set_Block_Start,

                             Make_Default,
                             Make_Self,
                             Make_Scope,
                             Make_Parent,
                             Name_Partner,

                             Swap_Control,
                             Mark_Auxillary,
                             Pop_Auxillary,

                             Pop_Auxillary_Loop,
                             Pop_Auxillary_Range,

                             Pop_Block,
                             Pop_Block_With_Result,

                             Break_Unconditional,
                             Break_Optional,
                             Exit_Break,

                             Query_Break_Cause,
                             Query_Break_Address,
                             Query_Break_Mask,

                             Alter_Break_Mask,
                             Query_Frame,
                             Establish_Frame,

                             Loop_Increasing_Extended,
                             Loop_Decreasing_Extended,

                             Push_Discrete_Extended,
                             Push_Float_Extended,

                             Push_Structure_Extended,
                             Push_String_Extended,

                             Push_String_Extended_Indexed,
                             Store_String_Extended,

                             Jump_Extended,
                             Jump_Zero_Extended,
                             Jump_Nonzero_Extended,

                             Jump_Dynamic,
                             Jump_Zero_Dynamic,
                             Jump_nonzero_Dynamic,

                             Load_Dynamic,
                             Store_Dynamic,
                             Call_Dynamic,
                             Reference_Dynamic,

                             Spare6_Action,
                             Spare7_Action,
                             Spare8_Action,
                             Spare9_Action,
                             Spare10_Action,
                             Spare11_Action
                            );

   type Op_Code is (
                    Declare_Type,
                    Complete_Type,
                    Declare_Variable,
                    Declare_Subprogram,
                    Load,
                    Store,
                    Store_Unchecked,
                    Reference,
                    Call,
                    Exit_Subprogram,
                    End_Rendezvous,
                    Execute,
                    Action,
                    Execute_Immediate,
                    Jump,
                    Jump_Zero,
                    Jump_Nonzero,
                    Jump_Case,
                    Loop_Increasing,
                    Loop_Decreasing,
                    Short_Literal,
                    Indirect_Literal,
                    Pop_Control,
                    Load_Top,
                    Store_Top,
                    Store_Top_Unchecked,
                    Load_Encached,
                    Extension,
                    Literal_Value,
                    Block_Begin,
                    Block_Handler,
                    End_Locals
                   );

   type Instruction (
                     For_Op : Op_Code := Action
                    ) is
      record
         case For_Op is
            when Declare_Type =>
               Type_Class : Operand_Class;
               Type_Kind : Type_Sort;
               Type_Options : Type_Option_Set;
            when Complete_Type =>
               Completion_Class : Operand_Class;
               Completion_Mode : Type_Completion_Mode;
            when Declare_Variable =>
               Variable_Class : Operand_Class;
               Variable_Options : Variable_Option_Set;
            when Declare_Subprogram =>
               Subprogram_Kind : Subprogram_Sort;
               Subprogram_Options : Subprogram_Option_Set;
            when Load | Store | Store_Unchecked | Reference | Call =>
               Object : Object_Reference;
            when Exit_Subprogram =>
               New_Top_Offset : Inner_Frame_Delta;
               Exit_Options : Exit_Option_Set;
            when End_Rendezvous =>
               Return_Count : Parameter_Count;
            when Execute =>
               Operator : Operator_Spec;
            when Action =>
               To_Perform : Unclassed_Action;
            when Execute_Immediate =>
               Discrete_Op : Operation;
               With_Value : Immediate_Value;
            when Jump | Jump_Zero | Jump_Nonzero |
                 Loop_Increasing | Loop_Decreasing =>
               Relative : Pc_Offset;

            when Jump_Case =>
               Case_Max : Case_Maximum;
            when Pop_Control =>
               Pop_Count : Stack_Pop_Count;
            when Load_Top =>
               At_Offset : Stack_Top_Offset;
            when Store_Top | Store_Top_Unchecked =>
               Target_Class : Operand_Class;
               Target_Offste : Stack_Top_Offset;
            when Load_Encached =>
               With_Number : Encached_Object_Number;
            when Short_Literal =>
               Short_Value : Short_Literal_Value;
            when Indirect_Literal =>
               Value_Class : Operand_Class;
               Value_Relative : Pc_Offset;
            when Literal_Value =>
               Value : Literal;
            when Extension =>
               Argument : Instruction_Extension;
            when Block_Begin | Block_Handler =>
               Location : Segment_Reference;
            when End_Locals =>
               Offset : Extended_Literal;
         end case;
      end record;

end Machine_Code;
