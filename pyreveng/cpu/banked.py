
from pyreveng import job, leaf, mem, data, seven_segment, code, listing, discover, tree, assy

class BankedMem(mem.MemMapper):
    def __init__(self, lo, hi, bank):
        super().__init__(lo, hi, name="Bank %d" % bank)
        self.bank = bank

    def __repr__(self):
        return "<BankedMem %x-%x %s>" % (self.lo, self.hi, self.name)

    def adr(self, dst):
        lbl = list(self.get_labels(dst))
        if lbl:
            return lbl[0]
        return "0x%x:" % self.bank + self.apct % dst

    def afmt(self, adr):
        return "0x%x:" % self.bank + super().afmt(adr)

class BankedCPU():

    def __init__(self, banks, model):
        self.model = model
        self.banks = banks
        self.bank = []

        class BCPU(model):
            def __init__(self, bank, up):
                super().__init__()
                self.bank = bank
                self.up = up
                self.add_as("mem", aspace=BankedMem(self.m.lo, self.m.hi, bank))

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

#############################################################################

if False:

	class MemBanked(mem.MemMapper):
		pass

		def __repr__(self):
			return "<MemBanked %x-%x %s>" % (self.lo, self.hi, self.name)

	class MemBank(mem.MemMapper):

		def __init__(self, up, bankno, lo, hi):
			self.up = up
			self.bankno = bankno
			self.bankoff = bankno * hi
			super().__init__(lo, hi, "Bank#%d" % bankno)

		def __repr__(self):
			return "<MemBank[%d] %x-%x @%x %s>" % (self.bankno, self.lo, self.hi, self.bankoff, self.name)

		def map(self, mem, lo, hi, offset):
			''' Map into this bank of memory '''
			super().map(mem, lo, hi, offset)

		def set_label(self, adr, lbl):
			self.up.up_set_label(self, adr, lbl)
			super().set_label(adr, lbl)

		def set_line_comment(self, adr, lbl):
			self.up.up_set_line_comment(self, adr, lbl)
			super().set_line_comment(adr, lbl)

		def set_block_comment(self, adr, lbl):
			self.up.up_set_block_comment(self, adr, lbl)
			super().set_block_comment(adr, lbl)

		def insert(self, item):
			self.up.up_insert(self, item)
			super().insert(item)

	class BankedCPU2():

		def __init__(self, cpu, banks):
			self.cpu = cpu
			self.cpu.up = self
			self.dist = cpu.m.hi
			self.mglobal = MemBanked(cpu.m.lo, self.dist * banks)
			self.mglobal.adr = self.myadr
			self.m = self.mglobal
			self.bank = {}
			self.todo = []
			self.allmap = tree.Tree(cpu.m.lo, cpu.m.hi)
			# XXX: handle iterable 'banks' argument
			for i in range(banks):
				self.bank[i] = MemBank(self, i, cpu.m.lo, cpu.m.hi)
				self.bank[i].name = "Bank%d" % i

		def myadr(self, a):
			return "%02x:%03x" % (a >> 11, a & 0x7ff)

		def __repr__(self):
			return "<BankCPU[%d] %x-%x>" % (len(self.bank), self.cpu.m.lo, self.cpu.m.hi)

		def map_one(self, bank, mem, lo, hi, **kwargs):
			self.mglobal.map(mem, lo + bank * self.dist, hi + bank *self.dist, **kwargs)
			self.bank[bank].map(mem, lo, hi, **kwargs)
			
		def map_all(self, mem, lo, hi, **kwargs):
			l = leaf.Leaf(lo, hi, "mapall")
			self.allmap.insert(l)
			self.mglobal.mapping.sort()
			self.mglobal.map(mem, lo, hi, **kwargs)
			for i, j in self.bank.items():
				j.map(mem, lo, hi, **kwargs)

		def gmapped(self, lo, hi=None):
			if hi is None:
				hi = lo + 1
			x = self.allmap.find_range(lo, hi)
			return len(x[0])

		def page(self, n):
			self.cpu.m = self.bank[n]

		def __getattr__(self, a):
			return getattr(self.cpu, a)

		def set_label(self, adr, lbl):
			if self.gmapped(adr):
				for i in self.bank.values():
					i.set_label(adr, lbl)
			self.mglobal.set_label(adr, lbl)

		def up_insert(self, bank, item):
			if self.gmapped(item.lo, item.hi):
				ll = leaf.Link(item.lo, item.hi, item)
			else:
				ll = leaf.Link(item.lo + bank.bankoff, item.hi + bank.bankoff, item)
			self.mglobal.insert(ll)

		def up_set_label(self, bank, adr, label):
			if self.gmapped(adr):
				self.mglobal.set_label(adr, label)
			else:
				self.mglobal.set_label(adr + bank.bankoff, label)

		def up_set_line_comment(self, bank, adr, label):
			if self.gmapped(adr):
				self.mglobal.set_line_comment(adr, label)
			else:
				self.mglobal.set_line_comment(adr + bank.bankoff, label)

		def up_set_block_comment(self, bank, adr, label):
			if self.gmapped(adr):
				self.mglobal.set_block_comment(adr, label)
			else:
				self.mglobal.set_block_comment(adr + bank.bankoff, label)
