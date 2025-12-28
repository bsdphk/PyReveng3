
from pyreveng import assy, mem, listing, data
import pyreveng.cpu.mos6500 as mos6500
import pyreveng.cpu.banked as banked

NAME = "C64_Comal80"
NPG = 4

hack_desc = '''
SKIP	x	| 2C		| A0		|
SKIP	x	| 2C		| A2		|
SKIP	x	| 2C		| A9		|
'''

class hack_ins(assy.Instree_ins):
    ''' ... '''

    def assy_x(self):
        # XXX: Figure out proper flow
        self.hi -= 1

class HiLoTab(data.Struct):
    
    def __init__(self, tree, lo, count):
        super().__init__(
            tree=tree,
            lo=lo,
            top_=data.Array(count, data.Bu8),
            bot_=data.Array(count, data.Bu8),
            vertical=True,
        )

    def render(self):
        yield 'HiLoTab {'
        n = 0
        for t,b in zip(self.top, self.bot):
            yield '    [0x%02x]: 0x%02x, 0x%02x' % (n, t.val, b.val)
        yield '}'

class ReturnIndexTab(HiLoTab):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dst = list(t.val*256 + b.val + 1 for t,b in zip(self.top, self.bot))

    def render(self):
        yield 'ReturnIndexTab {'
        for n, d in enumerate(self.dst):
            yield '    [0x%02x]: %s' % (n, self.tree.adr(d))
        yield '}'


class ListTab(HiLoTab):
    def __init__(self, tree, lo, count, offset, tokentab):
        super().__init__(tree, lo, count)
        self.offset = offset
        self.tokentab = tokentab

    def render(self):
        yield 'ListTab {'
        n = 0
        for t,b in zip(self.top, self.bot):
            mode = t.val & 0x3f
            flag = t.val & 0xc0
            l = [
                "   ",
                "[0x%03x]" % (n+self.offset),
                "0x%02x,0x%02x" % (t.val, b.val),
                "-",
                "%02x" % flag,
                "%02x" % mode,
                "# 0x%03x:" % (n+self.offset),
            ]

            tok = self.tokentab[b.val - 1]
            if b.val and tok:
                tok = tok.txt
            else:
                tok = ""

            if flag == 0x40:
                extra=", extra=1"
            elif flag == 0x80:
                extra=", extra=2"
            elif flag == 0xc0:
                extra=", extra=3"
            else:
                extra=""

            varkind = {
                0x0: "RealVar",
                0x1: "IntVar",
                0x2: "StringVar",
            }.get(b.val, "?")

            if mode == 0x04:
                l.append('EndVar.kind(StringVar, "%s "%s),' %  (tok, extra))
            elif mode == 0x06:
                l.append('Wrap.inside("", " %s"%s),' % (tok, extra))
            elif mode == 0x07 and flag == 0:
                l.append('RVar,')
            elif mode == 0x08:
                l.append('VarParan.kind(RealVar%s),' % extra)
            elif mode == 0x09:
                l.append('VarParan.kind(IntVar%s),' % extra)
            elif mode == 0x0a:
                l.append('VarParan.kind(StringVar%s),' % extra)
            elif mode == 0x0b:
                l.append('Join.suffix("%s"%s),' % (tok, extra))
            elif mode == 0x0c:
                l.append('Wrap.inside("%s", ""%s),' % (tok, extra))
            elif mode == 0x0d:
                l.append('Join.around("%s"%s),' % (tok, extra))
            elif mode == 0x0e:
                l.append('Join.around(" %s "%s),' % (tok, extra))
            elif mode == 0x0f:
                l.append('Wrap.inside("%s ", ""%s),' % (tok, extra))
            elif mode == 0x10:
                l.append('Join.around("%s "%s),' % (tok, extra))
            elif mode == 0x11:
                l.append('Push.this("%s"%s),' % (tok, extra))
            elif mode == 0x12:
                l.append('Wrap.inside("%s", ")"%s),' % (tok, extra))
            elif mode == 0x13:
                l.append('Wrap.inside("%s(", ")"%s),' % (tok, extra))
            elif mode == 0x14:
                l.append('Wrap.inside("%s$(", ")"%s),' % (tok, extra))
            elif mode == 0x15:
                l.append('Push.this("%s "%s),' % (tok, extra))
            elif mode == 0x16:
                l.append('Push.this("%s ", indent=-2%s),' % (tok, extra))
            elif mode == 0x17:
                l.append('Push.this("%s", indent_this=-2%s),' % (tok, extra))
            elif mode == 0x18:
                l.append('Push.this("%s", indent=2%s),' % (tok, extra))
            elif mode == 0x19 and flag == 0:
                l.append('TrimLastChar,')
            elif mode == 0x1a:
                l.append('Join.around("%s ", sfx=": "%s),' %  (tok, extra))
            elif mode == 0x1b:
                l.append('Wrap.inside("%s(", ")"%s),' % (tok, extra))
            elif mode == 0x1c:
                l.append('Join.suffix(" %s "%s),' % (tok, extra))
            elif mode == 0x1d and flag == 0:
                l.append('CommaToSemi,')
            elif mode == 0x1e:
                l.append('Wrap.inside("", "%s"%s),' % (tok, extra))
            elif mode == 0x1f:
                # XXX: The indent without flag is suspious
                l.append('Wrap.inside("", " %s", indent=2%s),' % (tok, extra))
            elif mode == 0x20:
                l.append('Wrap.inside("", " %s "%s),' % (tok, extra))
            elif mode == 0x23:
                l.append('EndVar.kind(RealVar, "%s "%s),' %  (tok, extra))
            elif mode == 0x24:
                l.append('EndVar.kind(IntVar, "%s "%s),' %  (tok, extra))
            elif mode == 0x25 and flag == 0:
                l.append('CallRVar,')
            elif mode == 0x26:
                l.append('Wrap.inside("", " %s "%s),' %  (tok, extra))
            elif mode == 0x27:
                l.append('TakesName.word("%s "%s),' %  (tok, extra))
            elif mode == 0x29 and flag == 0:
                l.append('DimOf,')
            elif mode == 0x2a and flag == 0:
                l.append('Wrap.inside("", ":"),')
            elif mode == 0x2c and flag == 0x80:
                l.append('DataJoin,')
            elif mode == 0x2d and flag == 0:
                l.append('AssignVar.kind(%s),' % varkind)
            elif mode == 0x2e and flag == 0:
                l.append('Join.around(" UNTIL ", pfx="REPEAT "),')
            elif mode == 0x2f:
                l.append('Wrap.inside("", sfx=" %s", indent=2%s),' %  (tok, extra))
            elif mode == 0x31:
                l.append('Join.around(",", pfx="%s ", sfx=": "%s),' %  (tok, extra))
            elif mode == 0x32:
                l.append('Join.around(",", pfx="%s "%s),' %  (tok, extra))
            elif mode == 0x33 and flag == 0:
                l.append('Push.this("%s ", extra=2),' % tok)
            elif mode == 0x3a and flag == 0x80:
                l.append('Label,')
            elif mode == 0x3b and flag == 0:
                l.append('InputPrompt,')
            elif mode == 0x3c:
                l.append('Push.this("%s$"%s),' % (tok, extra))
            elif mode == 0x3d and flag == 0x00:
                l.append('Dparas,')

            elif flag:
                l.append('? %s' % tok)
            elif mode == 0x00:
                l.append('NoOpToken,')
            elif mode == 0x3e:
                l.append('PrefixOpen,')
            else:
                l.append('? %s' % tok)

            yield " ".join(l)
            n += 1
        yield '}'

class Comal80():

    def __init__(self):
    
        crt = open("Comal80.crt", "rb").read()

        m0 = mem.ByteMem(0x0, 0x4000)
        for n in range(0x4000):
            m0[n] = crt[0x0050 + n]

        m1 = mem.ByteMem(0x0, 0x4000)
        for n in range(0x4000):
            m1[n] = crt[0x4060 + n]

        m2 = mem.ByteMem(0x0, 0x4000)
        for n in range(0x4000):
            m2[n] = crt[0x8070 + n]

        m3 = mem.ByteMem(0x0, 0x4000)
        for n in range(0x4000):
            m3[n] = crt[0xc080 + n]

        self.cx = banked.BankedCPU(NPG, mos6500.mos6500)
        self.cx.add_ins(hack_desc, hack_ins)
        self.cx.bank[0].m.map(m0, lo=0x8000)
        self.cx.bank[1].m.map(m1, lo=0x8000)
        self.cx.bank[2].m.map(m2, lo=0x8000)
        self.cx.bank[3].m.map(m3, lo=0x8000)

        self.foo00()
        self.foo01()
        #self.foo03()
        self.foo04()
        self.foo05()
        self.foo06()

    def foo06(self):

        for a, l in (
            (0x0012, "List_ElementCount"),
            (0x0089, "List_Ptr"),
            (0xc65f, "List_Stack-1"),
            (0xc660, "List_Stack"),
            (0xc661, "List_Stack+1"),
            (0xc846, "List_Indent"),
        ):
            for b in self.cx.bank:
                b.m.set_label(a, l)

    def foo05(self):

        for b, a, l in (
             (1, 0x0038, "CurTokenNo"),
             (1, 0xb745, "List_AppendOpen_Swap_Join_AppendClose"),
             (1, 0xb9ef, "ListSwapJoin"),
             (1, 0xb9f2, "ListJoin"),
             (1, 0xba21, "ListPushTok"),
             (1, 0xba77, "ListVarParen_[RIS](X)"),
             (1, 0xbad2, "ListSwap"),
             (1, 0xbcae, "ListAppendSpace"),
             (1, 0xbcab, "ListAppendDoubleQuote"),
             (1, 0xbcb1, "ListAppendComma"),
             (1, 0xbcb4, "ListAppendOpenParens"),
             (1, 0xbcb7, "ListAppendCloseParens"),
             (1, 0xbcb9, "ListAppend(Y)"),
             (1, 0xbccb, "ListPrependComma"),
             (1, 0xbcce, "ListPrependSpace"),
             (1, 0xbce3, "ListTrimLastChar()"),
        ):
             self.cx.bank[b].m.set_label(a, l)

        for b, a, lc in (
        ):
             self.cx.bank[b].m.set_line_comment(a, lc)

    def foo04(self):

        expl = {
            0x00: "Nop",
            0x06: "AppendSpace_PushTok_Join",
            0x08: "VarParenReal",
            0x09: "VarParenInt",
            0x0a: "VarParenString",
            0x0b: "Join_PushTok_Join",
            0x0c: "PushTok_Swap_Join",
            0x0d: "PushTok_Swap_Join_Join",
            0x0e: "PushTok_AppendSpace_PrependSpace_Swap_Join_Join",
            0x0f: "PushTok_AppendSpace_Swap_Join",
            0x10: "PushTok_AppendSpace_Swap_Join_Join",
            0x11: "PushTok",
            0x12: "PushTok_Swap_Join_AppendClose",
            0x13: "PushTok_AppendOpen_Swap_Join_AppendClose",
            0x14: "PushTok_AppendDollar_AppendOpen_Swap_Join_AppendClose",
            0x15: "PushTok_AppendSpace",
            0x16: "PushTok_AppendSpace_Indent2",
            0x17: "PushTok_AppendSpace_Indent3",
            0x18: "PushTok_AppendSpace_Indent1",
            0x19: "TrimLast",
            0x1a: "StackOp_PushTok_AppendSpace_Swap_Join_Join_AppendColon_AppendSpace",
            0x1b: "PushTok_AppendOpen_Swap_Join_AppendClose_Join",
            0x1e: "PushTok_Join",
            0x20: "Indent4_AppendSpace_PushTok_Join_AppendSpace",
            0x2a: "Join_AppendColon_PushTok",
            0x2b: "Error",
            0x30: "Error",
            0x32: "PrependComma_Join_PushTok_AppendSpace_Swap_Join",
            0x34: "Error",
            0x35: "Error",
            0x37: "Error",
            0x38: "Error",
            0x3b: "Join_AppendColon_AppendSpace",
            0x3c: "PushTok_AppendDollar",
            0x3d: "TrimLast_AppendClose_AppendOpen",
            0x3e: "PrependComma_Join_PushTok_AppendSpace_Swap_Join_AppendComma",
        }

        y = ReturnIndexTab(self.cx.bank[1].m, 0xb960, 0x3f).insert()
        self.cx.bank[1].m.set_label(y.lo, "StackOpTbl[0x3f]")
        for n, adr in enumerate(y.dst):
             self.cx.bank[1].disass(adr)
             lbl = expl.get(n)
             if lbl:
                 self.cx.bank[1].m.set_label(adr, "StackOp_%s_[0x%02x]" % (lbl, n))
             else:
                 self.cx.bank[1].m.set_label(adr, "StackOp[0x%02x]" % n)

    def foo00(self):
        self.lextokens = data.Array(
            0xad,
            (data.Text, {"pfx": 1,}),
            vertical=True,
        )(
            self.cx.bank[1].m,
            0x8009,
        ).insert()
        self.cx.bank[1].m.set_label(self.lextokens.lo, "LexTokens[0xad]")
        data.Bu8(self.cx.bank[1].m, self.lextokens.hi).insert()
        self.cx.bank[1].m.set_line_comment(self.lextokens.hi, "List terminator")

        with open("/tmp/c64_unicomal_tables.py", "w") as file:
            file.write("# Machine-generated by PyReveng3\n\n")
            file.write("TOKENS = [\n")
            file.write("    None,\n")
            for n, ltok in enumerate(self.lextokens):
                if ltok.txt != "\\x00":
                    file.write(("    '''%s'''," % ltok.txt).ljust(20))
                else:
                    file.write(("    None,").ljust(20))
                file.write(" # 0x%x\n" % (n+1))
            file.write("]\n")

    def foo01(self):

        self.tab_list_1 = ListTab(self.cx.bank[1].m, 0xb3ce, 255, 0, self.lextokens).insert()
        self.cx.bank[1].m.set_label(self.tab_list_1.lo, "TAB_LIST_1")

        self.tab_list_2 = ListTab(self.cx.bank[1].m, 0xb5cc, 44, 0x114, self.lextokens).insert()
        self.cx.bank[1].m.set_label(self.tab_list_2.lo, "TAB_LIST_2")

        with open("/tmp/c64_unicomal_tables.py", "a") as file:
            file.write("\n")
            file.write("DISPATCH = {\n")
            for tbl in (
                self.tab_list_1,
                self.tab_list_2,
            ):
                n = tbl.offset
                for top, bot in zip(tbl.top, tbl.bot):
                    extra = top.val >> 6
                    mode = top.val & 0x3f
                    tok = bot.val
                    file.write("    0x%03x: (0x%02x, 0x%x, 0x%02x)," % (
                            n, mode, extra, tok
                        )
                    )
                    if 0 < tok < 0xad:
                        file.write(" # %s" % self.lextokens[tok-1].txt)
                    file.write("\n")
                    n += 1
            file.write("}\n")

    def retval(self):
        retval = [
           self.cx.bank[0].m,
           self.cx.bank[1].m,
           self.cx.bank[2].m,
           self.cx.bank[3].m,
        ]
        return NAME, retval

if __name__ == '__main__':
    ex = Comal80()
    listing.Example(ex.retval, ncol=8, pil=False)
