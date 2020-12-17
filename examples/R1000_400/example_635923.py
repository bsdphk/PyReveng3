
from pyreveng import mem, listing

import example_ada

FILENAME = "635923.SEG"
NAME = "seg_635923"

def example():
    mb = mem.Stackup((FILENAME,), nextto=__file__)
    cx = example_ada.segment_file(mb)
    for a, b, c in (
        (0x057a, 0x0171, "Operand_Class[19]"),
        (0x058d, 0x0189, "Operation[191]"),
        (0x064c, 0x01a1, "Type_Sort[5]"),
        (0x0651, 0x01b9, "Type_Completion_Mode[6]"),
        (0x0657, 0x01d1, "Subprogram_Sort[4]"),
        (0x065b, 0x01e9, "Field_Sort[2]"),
        (0x065d, 0x0201, "Field_Mode[2]"),
        (0x065f, 0x0411, "Extension_Kind[2]"),
        (0x0661, 0x0461, "Unclassed_Action[61]"),
        (0x069e, 0x0479, "Op_Code[32]"),
    ):
        cx.m.set_block_comment(
            a,
            "Indexed from 0x%04x -- Machine_Code::type %s" % (b, c)
        )
        cx.m.set_label(a, "NAME_" + c)

    for a, l in (
        (0x000b, "Operand_Class'First"),
        (0x000c, "Operand_Class'Last"),
        (0x000f, "Operand_Class"),
        (0x0010, "Operation'First"),
        (0x0011, "Operation'Last"),
        (0x0014, "Operation"),
        (0x0015, "Type_Sort'First"),
        (0x0016, "Type_Sort'Last"),
        (0x0019, "Type_Sort"),
        (0x001a, "Boolean (Is_Visible)"),
        (0x001b, "Boolean (Unsigned)"),
        (0x001c, "Boolean (With_Size)"),
        (0x001d, "Boolean (Access_Protected)"),
        (0x001e, "Boolean (Values_Relative)"),
        (0x001f, "Boolean (Bounds_With_Object)"),
        (0x0020, "Boolean (Not_Elaborated)"),
        (0x0022, "record size (7)"),
        (0x0023, "Type_Option_Set"),
        (0x0028, "Type_Completion_Mode"),
        (0x0034, "Variable_Option_Set"),
        (0x0039, "Subprogram_Sort"),
        (0x003f, "Subprogram_Option_Set"),
        (0x0044, "Exit_Option_Set"),
        (0x0045, "Field_Index'First"),
        (0x0046, "Field_Index'Last"),
        (0x0047, "Integer (Field_Index)"),
        (0x0048, "Field_Index\n(Declare_Type, Discrete_Class, Defined ?)"),
        (0x0049, "Variant_Record_Index'First (subtype af Field_Index)"),
        (0x004a, "Variant_Record_Index'Last"),
        (0x004b, "Load top 2 (Field_Index på stakken)\nErstatter LOAD_ENCACHED for subtype ???"),
        (0x004c, "Variant_Record_Index (subtype af Field_Index)\n(Declare_Type, Discrete_Class, Defined ?)"),
        (0x004d, "Field_Sort'First"),
        (0x004e, "Field_Sort'Last"),
        (0x0051, "Field_Sort"),
        (0x0056, "Field_Mode"),
        (0x0057, "Field_Op'First"),
        (0x0058, "Field_Op'Last"),
        (0x0059, "0xe pointer til Operation, se evt Guru1 p 56"),
        (0x005a, "Field_Op (subtype af Operation)"),
        (0x005b, "Component_Op'First"),
        (0x005c, "Component_Op'Last"),
        (0x005d, "Load top 2 (Field_OP pos på stak)\nErstatter LOAD_ENCACHED for subtype ???"),
        (0x005e, "Component_Op (subtype af Field_Op)"),
        (0x005f, "0xe : Pointer til Operation typen"),
        (0x0060, "record size?"),
        (0x0061, "0x18 : Pointer til Field_Sort"),
        (0x0062, "0x19 : Pointer til Field_Mode"),
        (0x006a, "(Declare_Type, Variant_Record_Class ?)"),
        (0x006b, "0xd : Pointer til Operand_Class typen?"),
        (0x006c, "0xe : Pointer til Operation typen?"),
        (0x006f, "0x16 : Pointer til Field_Index typen?"),
        (0x0072, "0x16 : Pointer til Field_Index typen?"),
        (0x0075, "0x16 : Pointer til Field_Index typen?"),
        (0x0076, "0x1c : Pointer til Access_Spec typen?"),
        (0x007f, "Field_Spec\n(Declare_Type, Variant_Record_Class ?)"),
        (0x0080, "0xd : Pointer til Operand_Class typen?"),
        (0x0081, "0xe : Pointer til Operation typen?"),
        (0x0084, "0x1c : Pointer til Field_Spec typen?"),
        (0x008d, "Field_Spec\n(Declare_Type, Variant_Record_Class ?)"),
    ):
        cx.m.set_line_comment(a, l)

    cx.m.set_block_comment(0x5f, "Start på første Variant record (type Access_Spec)")
    cx.m.set_block_comment(0x6b, "Start på Variant record (type Field_Spec)")
    cx.m.set_block_comment(0x80, "Start på Variant record (type Operator_Spec)")
    cx.m.set_block_comment(0x8e, "Slut på Variant record (type Operator_Spec)")

    return NAME, (cx.m,)

if __name__ == '__main__':
    listing.Example(example, ncol=1, leaf_width=48)
    
