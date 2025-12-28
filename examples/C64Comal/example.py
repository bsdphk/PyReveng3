
from pyreveng import mem, listing, data
import pyreveng.cpu.mos6500 as mos6500
import pyreveng.cpu.banked as banked

NAME = "C64_Comal80"
NPG = 4

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
            yield '    [0x%02x] 0x%02x, 0x%02x' % (n, t.val, b.val)
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
        self.cx.bank[0].m.map(m0, lo=0x8000)
        self.cx.bank[1].m.map(m1, lo=0x8000)
        self.cx.bank[2].m.map(m2, lo=0x8000)
        self.cx.bank[3].m.map(m3, lo=0x8000)

        self.foo00()
        self.foo01()
        #self.foo03()
        self.foo04()

    def foo04(self):

        y = HiLoTab(self.cx.bank[1].m, 0xb960, 0x3f).insert()

    def foo03(self):
        self.f2 = [0] * 64
        self.foo02(0, self.tab_list_1, self.tab_list_2)
        for i in range(0x100, 0x114):
            print("NI %03x" % i)
        self.foo02(0x114, self.tab_list_3, self.tab_list_4)
        for n, i in enumerate(self.f2):
            if not i:
                continue
            print("%02x" % n, i)

    def foo00(self):
        self.lextokens = data.Array(
            173,
            (data.Text, {"pfx": 1,}),
            vertical=True,
        )(
            self.cx.bank[1].m,
            0x8009,
        ).insert()
        return
        ptr = 0x8009
        self.lextokens = []
        while ptr < 0x834e:
            y = data.Text(self.cx.bank[1].m, ptr, pfx=1).insert()
            self.lextokens.append(y.txt)
            ptr = y.hi
        print("LEN", len(self.lextokens))

    def foo01(self):

        self.tab_list_1 = ListTab(self.cx.bank[1].m, 0xb3ce, 255, 0, self.lextokens).insert()
        self.cx.bank[1].m.set_label(self.tab_list_1.lo, "TAB_LIST_1")

        self.tab_list_2 = ListTab(self.cx.bank[1].m, 0xb5cc, 44, 0x114, self.lextokens).insert()
        self.cx.bank[1].m.set_label(self.tab_list_2.lo, "TAB_LIST_2")

        return

        self.tab_list_1 = data.Array(
            255,
            data.Bu8,
            vertical=True
        )(
            self.cx.bank[1].m,
            0xb3ce
        ).insert()
        self.cx.bank[1].m.set_label(self.tab_list_1.lo, "TAB_LIST_1")

        self.tab_list_2 = data.Array(
            255,
            data.Bu8,
            vertical=True
        )(
            self.cx.bank[1].m,
            0xb4cd
        ).insert()
        self.cx.bank[1].m.set_label(self.tab_list_2.lo, "TAB_LIST_2")

        self.tab_list_3 = data.Array(
            44,
            data.Bu8,
            vertical=True
        )(
            self.cx.bank[1].m,
            0xb5b8 + 20
        ).insert()
        self.cx.bank[1].m.set_label(self.tab_list_3.lo, "TAB_LIST_3")

        self.tab_list_4 = data.Array(
            44,
            data.Bu8,
            vertical=True
        )(
            self.cx.bank[1].m,
            0xb5e4 + 20
        ).insert()
        self.cx.bank[1].m.set_label(self.tab_list_4.lo, "TAB_LIST_4")

    def foo02(self, off, list1, list2):

        #for n, i in enumerate(self.tab_list_1):
        for n, i in enumerate(list1):
            tl2 = self.tab_list_2[n]
            tl2 = list2[n]
            l = [
                "NI",
                "%03x:" % (n+off),
                "%02x" % i.val,
                "%02x" % tl2.val,
                "-",
                "%02x" % (i.val & 0xc0),
                "%02x" % (i.val & 0x3f),
            ]
            g = self.lextokens[tl2.val - 1].txt
            if i.val & 0x3f == 0x11:
                print(*l, 'Push.this("%s"),' % g)
            elif i.val & 0x3f == 0x0b:
                g = {
                    0x00: '""',
                    0x01: '")"',
                    0x03: '","',
                    0x6b: '":"',
                }.get(tl2.val)
                print(*l, 'Join.suffix(%s),' % g)
            elif i.val & 0x3f == 0x0c:
                print(*l, 'Wrap.inside("%s", ""),' % g)
            elif i.val & 0x3f == 0x0d:
                print(*l, 'Join.around("%s"),' % g)
            elif i.val & 0x3f == 0x0e:
                print(*l, 'Join.around(" %s "),' % g)
            elif i.val & 0x3f == 0x0f:
                print(*l, 'Wrap.inside("%s ", ""),' % g)
            elif i.val & 0x3f == 0x13:
                g = '"' + self.lextokens[tl2.val - 1].txt + '("'
                print(*l, "WRAP.inside", g, '"),"')
            elif i.val & 0x3f == 0x14:
                g = '"' + self.lextokens[tl2.val - 1].txt + '$("'
                print(*l, "WRAP.inside", g, '"),"')
            elif i.val & 0x3f == 0x15:
                print(*l, 'Push.this("%s "),' % g)
            elif i.val & 0x3f == 0x16:
                print(*l, 'Push.this("%s", indent=-2),' % g)
            elif i.val & 0x3f == 0x1e:
                print(*l, 'Wrap.inside("", "%s"),' % g)
            elif i.val & 0x3f == 0x32:
                print(*l, 'Join.around(",", pfx="%s "),' %  g)
            elif i.val & 0x3f == 0x3c:
                print(*l, 'Push.this("%s$"),' % g)
            elif i.val & 0x3f == 0x3e:
                print(*l, 'PrefixOpen,')
            else:
                self.f2[i.val & 0x3f] += 1
                print(*l)


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
