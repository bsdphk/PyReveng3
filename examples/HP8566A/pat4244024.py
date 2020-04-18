
from pyreveng import data

def symb(cx, a, b):
    if b[0] == '_':
        cx.m.set_label(a, b[1:])
        cx.disass(a)
    elif b[0] == '#':
        cx.m.set_label(a, b[1:])
        y = data.Data(cx.m, a, a + 1)
        y.rendered = ".CONST\t0x%04x" % cx.m[a]
    else:
        cx.m.set_label(a, b)

#######################################################################

class appendix_b_1():
    '''Patent 4,244,024, Appendix B-1 (pg188)'''
    def __init__(self, cx, lo):
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:	"_SUB1",
            0o003:	"_SUB1B",
            0o005:	"_SUB1P",
            0o007:	"_SUB11",
            0o011:	"_MIN1B",
            0o012:	"_ADD1B",
            0o014:	"_MIN1",
            0o015:	"_ADD1",
            0o017:	"_MIN1P",
            0o020:	"_ADD1P",
            0o022:	"_SFIA",
            0o031:	"_X11",
            0o032:	"_MIN1D",
            0o033:	"_ADD1D",
            0o034:	"_FADC",
            0o055:	"_ADONE",
            0o071:	"_AR12",
            0o075:	"_NORM",
            0o104:	"_NZERO",
            0o107:	"_MPY1P",
            0o111:	"_MPY1B",
            0o113:	"_MPY1",
            0o115:	"_MPY1T",
            0o116:	"_FMPC",
            0o135:	"_FMPX",
            0o136:	"_DIV1P",
            0o140:	"_DIV1B",
            0o142:	"_DIV1",
            0o144:	"_DIV1T",
            0o145:	"_FDVC",
            0o152:	"_FDVD",
            0o162:	"#=D-12",
            0o163:	"#=D0",
            0o164:	"#=B100",
            0o165:	"#=D1",
            0o166:	"#=D-5",
            0o167:	"#=B100100",
            0o170:	"#=D12",
        }.items():
            symb(cx, lo + a, b)

#######################################################################

class appendix_b_2():
    '''Patent 4,244,024, Appendix B-2 (pg189)'''
    def __init__(self, cx, lo):
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:	"#AR2M",
            0o001:	"#AR1M",
            0o002:	"#AR0M",
            0o003:	"#AR0L",
            0o004:	"#AR3M",
            0o005:	"#AR3L",
            0o006:	"_SUB2",
            0o011:	"_SUB2B",
            0o013:	"_SUB2P",
            0o015:	"_SUB2T",
            0o017:	"_MIN2P",
            0o020:	"_ADD2P",
            0o022:	"_MIN2B",
            0o023:	"_ADD2B",
            0o025:	"_MIN2",
            0o026:	"_ADD2",
            0o030:	"_MIN2T",
            0o031:	"_ADD2T",
            0o032:	"_.LADC",
            0o037:	"_SMSGN",
            0o041:	"_OPSGN",
            0o054:	"_NAR2",
            0o066:	"_DOIT",
            0o072:	"_CXIT",
            0o074:	"_MPY2P",
            0o076:	"_MPY2B",
            0o100:	"_MPY2T",
            0o101:	"_SMPYC",
            0o106:	"_MPY2",
            0o110:	"_.MPYD",
            0o137:	"_MPY40",
            0o141:	"_MPY42",
            0o157:	"_MPY50",
            0o165:	"_DIV2P",
            0o167:	"_DIV2B",
            0o171:	"_DIV2T",
            0o172:	"_SDIVC",
            0o177:	"_DIV2",
            0o201:	"_MOD2P",
            0o203:	"_MOD2B",
            0o205:	"_MOD2I",
            0o206:	"_SMODC",
            0o211:	"_MOD2",
            0o213:	"_.DIVF",
            0o225:	"_.DIVD",
            0o237:	"_DOVFL",
            0o244:	"_DV001",
            0o277:	"_DV002",
            0o322:	"_LOOP5",
            0o333:	"_DV005",
            0o342:	"_DV015",
            0o343:	"_DV020",
            0o355:	"_DV045",
            0o364:	"_DV050",
            0o403:	"_NINEC",
            0o405:	"_NINED",
            0o413:	"_FRP1",
            0o421:	"_AR1SL",
            0o422:	"_AR1SA",
            0o427:	"_AR1SN",
            0o431:	"_AR1SP",
            0o437:	"_AR1LD",
            0o443:	"_AR1LN",
            0o444:	"_AR1LA",
            0o454:	"_AR1LT",
            0o461:	"_.AMIN",
            0o473:	"_.BMIN",
            0o507:	"_SUB3",
            0o512:	"_SUB3B",
            0o514:	"_SUB3P",
            0o516:	"_MIN3P",
            0o517:	"_ADD3P",
            0o521:	"_MIN3B",
            0o522:	"_ADD3B",
            0o524:	"_MIN3",
            0o525:	"_ADD3",
            0o527:	"_MPY3P",
            0o531:	"_MPY3B",
            0o533:	"_MPY3",
            0o535:	"_DIV3P",
            0o537:	"_DIV3B",
            0o541:	"_DIV3",
            0o543:	"_MOD3P",
            0o545:	"_MOD3B",
            0o547:	"_MOD3",
            0o551:	"_MOD4B",
            0o553:	"_MOD4P",
            0o555:	"_MOD4T",
            0o557:	"_MOD4",
            0o562:	"_MOD4C",
            0o565:	"_DIV4B",
            0o567:	"_DIV4P",
            0o571:	"_DIV4T",
            0o573:	"_DIV4",
            0o576:	"_BDIVB",
            0o577:	"_BDIVC",
            0o601:	"_BD005",
            0o606:	"_BD010",
            0o611:	"_BD011",
            0o612:	"_.BDVF",
            0o617:	"_.BD030",
            0o635:	"_.BDVS",
            0o653:	"_.BOVFL",
            0o661:	"_ADD4B",
            0o663:	"_ADD4P",
            0o666:	"_ADD4T",
            0o671:	"_MPY4B",
            0o673:	"_MPY4P",
            0o677:	"_MPY4T",
            0o702:	"_SUB4P",
            0o703:	"_SUBC",
            0o707:	"_SUB4B",
            0o711:	"_SUB4T",
            0o713:	"_MIN4P",
            0o714:	"_MINC",
            0o717:	"_MIN4B",
            0o721:	"_MIN4T",
            0o725:	"#=B177701",
            0o726:	"#=D-4",
            0o727:	"#=D1",
            0o730:	"#=D0",
            0o731:	"#=D4",
            0o732:	"#=D-12",
            0o733:	"#=B114631",
            0o734:	"#=D12",
            0o735:	"#=D9",
            0o736:	"#=D-10",
            0o737:	"#=D-1",
            0o740:	"#=D-2",
            0o741:	"#=D-15",
            0o742:	"#=D32767",	# 3ca4
        }.items():
            symb(cx, lo + a, b)

#######################################################################

class appendix_b_3():
    '''Patent 4,244,024, Appendix B-3 (pg195)'''
    def __init__(self, cx, lo):
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:	"_.ADDR",
            0o004:	"_.FRPB",
            0o014:	"_.LDBI",
            0o020:	"_.LDBP",
            0o021:	"_.LDBA",
            0o022:	"_.LDB",
            0o025:	"_.MVE4",
            0o034:	"_.STBC",
            0o036:	"_.STBP",
            0o040:	"_.STBD",
            0o044:	"_.SAR2",
            0o050:	"_.STRB",
            0o054:	"_.RTNB",
            0o055:	"_.RTNI",
            0o061:	"_.RTNA",
            0o071:	"_.RTNL",
            0o076:	"_.RAR2",
            0o103:	"_.DSGN",
            0o106:	"_.ARGL",
            0o112:	"_.ARGA",
            0o113:	"_.ARGS",
            0o121:	"_.UPC4",
            0o125:	"_.CLBI",
            0o131:	"_.CLBP",
            0o132:	"_.CLBV",
            0o141:	"_.CLAI",
            0o145:	"_.CLAP",
            0o147:	"_.CLNP",
            0o151:	"_.CSHV",
            0o153:	"_.CSH",
            0o156:	"_.LDAP",
            0o161:	"_.LDSA",
            0o164:	"_.LDS1",
            0o172:	"_.LDSP",
            0o175:	"_.LDS1",
            0o176:	"_.LDS2",
            0o200:	"_.STAP",
            0o203:	"#=D4",
            0o204:	"#=D-3",
            0o205:	"#=D-4",
            0o206:	"#=D3",
        }.items():
            symb(cx, lo + a, b)

class appendix_b_4():
    '''Patent 4,244,024, Appendix B-4 (pg197)'''
    def __init__(self, cx, lo):
        #cx.m.add_range(lo, lo + 0o36, self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:      "_.ARRP",
            0o002:      "_.ARRY",
            0o005:      "_ARRAY",
            0o015:      "_LOOP",
            0o021:      "_LSTRT",
            0o036:	"#=D-1",
        }.items():
            symb(cx, lo + a, b)

class appendix_b_5():
    '''Patent 4,244,024, Appendix B-5 (pg198)'''
    def __init__(self, cx, lo):
        #cx.m.add_range(lo, lo + 0o27, self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:      "_.LRAP",
            0o002:      "_.ARAP",
            0o004:      "_.LRAY",
            0o006:      "_.ARAY",
            0o011:      "_ARRAY",
            0o025:	"#=D-3",
            0o026:	"#=D-1",
            0o027:	"#=D2",
        }.items():
            symb(cx, lo + a, b)

class appendix_b_7():
    '''Patent 4,244,024, Appendix B-7 (pg200)'''
    def __init__(self, cx, lo):
        #cx.m.add_range(lo, lo + 0o27, self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:      "_ROUND",
            0o017:	"#=D11",
            0o020:	"#=D-5",
            0o021:	"#=D1",
        }.items():
            symb(cx, lo + a, b)

class appendix_b_8():
    '''Patent 4,244,024, Appendix B-8 (pg201)'''
    def __init__(self, cx, lo):
        #cx.m.add_range(lo, lo + 0o27, self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:      "_.FDIG",
            0o001:      "_.DSFT",
            0o011:      "_DL20",
            0o012:      "_.DRGT",
            0o020:      "#=B0",
        }.items():
            symb(cx, lo + a, b)

class appendix_b_9():
    '''Patent 4,244,024, Appendix B-9 (pg201)'''
    def __init__(self, cx, lo):
        #cx.m.add_range(lo, lo + 0o27, self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:      "_.SRGT",
            0o001:      "_.SLFT",
            0o003:      "_.ARGT",
            0o005:      "_.RRGT",
            0o006:      "_STAB",
            0o012:      "_ZCHK",
            0o026:      "_ZRTN",
            0o030:      "_.RLFT",
            0o033:      "#=D-1",
            0o034:      "#=D16",
        }.items():
            symb(cx, lo + a, b)

class appendix_b_10():
    '''Patent 4,244,024, Appendix B-10 (pg202)'''
    def __init__(self, cx, lo):
        #cx.m.add_range(lo, lo + 0o27, self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:      "_.TBIT",
            0o005:      "_.SBIT",
            0o010:      "_.RBIT",
            0o014:      "_BIT",
            0o024:      "_RTN",
            0o026:      "_SLFT",
            0o027:      "#=D-1",
            0o030:      "#=D15",
            0o031:      "#=D1",
        }.items():
            symb(cx, lo + a, b)

class appendix_b_11():
    '''Patent 4,244,024, Appendix B-11 (pg203)'''
    def __init__(self, cx, lo):
        #cx.m.add_range(lo, lo + 0o27, self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o040:      "#=D0",
            0o041:      "#=D-1",
            0o000:      "_.TEST",
            0o010:      "_.TURN",
            0o015:      "_KMGET",
        }.items():
            symb(cx, lo + a, b)

class appendix_b_12():
    '''Patent 4,244,024, Appendix B-12 (pg203)'''
    def __init__(self, cx, lo):
        #cx.m.add_range(lo, lo + 0o27, self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:      "_.DEQL",
            0o003:      "_.EQL",
            0o004:      "_FALSE",
            0o006:      "_TRUE",
            0o010:      "_.NEQL",
            0o012:      "#=D0",
            0o013:      "#=D-1",
        }.items():
            symb(cx, lo + a, b)

class appendix_b_13():
    '''Patent 4,244,024, Appendix B-13 (pg203)'''
    def __init__(self, cx, lo):
        #cx.m.add_range(lo, lo + 0o15, self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:      "_.CASE",
        }.items():
            symb(cx, lo + a, b)

class appendix_b_15():
    '''Patent 4,244,024, Appendix B-15 (pg204)'''
    def __init__(self, cx, lo):
        #cx.m.add_range(lo, lo + 0o15, self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:      "_.RS7",
            0o001:      "_.R7",
            0o003:      "_.RS6",
            0o004:      "_.R6",
            0o006:      "_.RS5",
            0o007:      "_.R5",
            0o011:      "_.RS4",
            0o012:      "_.R4",
            0o014:      "_.WS4",
            0o015:      "_.W4",
            0o020:      "_.WS5",
            0o021:      "_.W5",
            0o024:      "_.WS6",
            0o025:      "_.W6",
            0o027:      "_RWEXT",
            0o032:      "_.WS7",
            0o033:      "_.W7",
            0o036:      "_.WSPS",
            0o044:      "_.WSTP",
            0o050:      "_.WSTR",
            0o053:      "_.WSTS",
            0o057:      "_WS010",
            0o065:      "_WS020",
        }.items():
            symb(cx, lo + a, b)

class appendix_b_16():
    '''Patent 4,244,024, Appendix B-16 (pg206)'''
    def __init__(self, cx, lo):
        #cx.m.add_range(lo, lo + 0o2, self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:      "_.STAC",
        }.items():
            symb(cx, lo + a, b)

class appendix_b_17():
    '''Patent 4,244,024, Appendix B-17 (pg206)'''
    def __init__(self, cx, lo):
        #cx.m.add_range(lo, lo + 0o2, self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:      "_.ANDB",
        }.items():
            symb(cx, lo + a, b)

class appendix_b_18():
    '''Patent 4,244,024, Appendix B-18 (pg206)'''
    def __init__(self, cx, lo):
        #cx.m.add_range(lo, lo + 0o2, self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:      "_.ORB",
        }.items():
            symb(cx, lo + a, b)

class appendix_b_19():
    '''Patent 4,244,024, Appendix B-19 (pg206)'''
    def __init__(self, cx, lo):
        cx.m.add_range(lo, lo + 0o2, txt=self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:      "_.ANDT",
        }.items():
            symb(cx, lo + a, b)

class appendix_b_21():
    '''Patent 4,244,024, Appendix B-21 (pg207)'''
    def __init__(self, cx, lo):
        cx.m.add_range(lo, lo + 0o24, txt=self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
            0o000:      "_ATNER",
            0o020:      "#=D7",
            0o021:      "#=D-2",
            0o022:      "#=D6",
            0o023:      "#=D4",
        }.items():
            symb(cx, lo + a, b)

# XXX: Not sure how the listing gets from 0x10 to 0x200 in line 46,
# XXX: So we split this one in two.

class appendix_b_28a():
    '''Patent 4,244,024, Appendix B-28 (pg217) - part A'''
    def __init__(self, cx, lo):
        cx.m.add_range(lo, lo + 0o10, txt=self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        for a, b in {
             0o00:	"PWRON",
             0o03:	"#AR0D",
             0o04:	"#AR1D",
             0o05:	"#AR2D",
             0o06:	"#AR3D",
        }.items():
            symb(cx, lo + a, b)

class appendix_b_28b():
    '''Patent 4,244,024, Appendix B-28 (pg217) - part B'''
    # XXX: Not sure how the listing gets from 0x10 to 0x200 in line 46...
    def __init__(self, cx, lo):
        # cx.m.add_range(lo, lo + 0o24, self.__doc__)
        cx.m.set_block_comment(lo, self.__doc__)
        cx.m.set_block_comment(lo + 0o10, "Instrument Preset Begins Here")
        cx.m.set_block_comment(lo + 0o11, "Hybrid Register Check")
        cx.m.set_block_comment(lo + 0o42, "ROM Checksum")
        cx.m.set_block_comment(lo + 0o111, "RAM TEST ROUTINE (for four 1kx4 rams)")
        for a, b in {
            0o000:	"#CM1",
            0o001:	"#B30",
            0o002:	"#B10",
            0o003:	"#HYPT1",
            0o004:	"#B40",
            0o005:	"#ROMMX",
            0o006:	"#SLRC1",
            0o007:	"#SLRC2",
            0o010:	"_BEG",
            0o020:	"_HYB2",
            0o021:	"_HYB3",
            0o027:	"_HYC4",
            0o044:	"_ROMCH",
            0o067:	"_CHK2",
            0o073:	"_ERR",
            0o075:	"_THRU",
            0o076:	"_MDSA",
            0o102:	"_DSA",
        }.items():
            symb(cx, lo + a, b)
