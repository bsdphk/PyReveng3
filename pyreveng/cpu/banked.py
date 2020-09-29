
from pyreveng import mem

class BankedMem(mem.MemMapper):
    def __init__(self, lo, hi, bank, apfx=None, asfx=""):
        if apfx is None:
            apfx = "0x%x:" % bank
        super().__init__(lo, hi, name="Bank %d" % bank, apfx=apfx, asfx=asfx)
        self.bank = bank

    def __repr__(self):
        return "<BankedMem %x-%x %s>" % (self.lo, self.hi, self.name)

class BankedCPU():

    def __init__(self, banks, model, mem=BankedMem):
        self.model = model
        self.banks = banks
        self.bank = []

        class BCPU(model):
            def __init__(self, bank, up):
                super().__init__()
                self.bank = bank
                self.up = up
                self.add_as("mem", aspace=mem(self.m.lo, self.m.hi, bank))

            def __repr__(self):
                return "<Banked CPU %s #%d>" % (self.name, self.bank)

            def __getitem__(self, n):
                return self.up.bank[n]

            def disass(self, dst, asp=None):
                rv = super().disass(dst, asp)
                while not self.lang.busy:
                    n = 0
                    for i in self.up.bank:
                        n += len(i.todo)
                        if i.todo:
                            i.run_todo(0)
                    if not n:
                        break

        for i in range(banks):
            self.bank.append(BCPU(i, self))
            self.bank[i].lang = self.bank[0]
            self.bank[i].m.name = "Bank %d" % i

    def __repr__(self):
        return "<Banked CPU %d*%s>" % (self.banks, str(self.bank[0]))

    def __getitem__(self, n):
        return self.bank[n]

    def add_ins(self, desc, ins):
        for i in self.bank:
            i.add_ins(desc, ins)
