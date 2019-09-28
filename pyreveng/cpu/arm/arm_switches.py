#!/usr/bin/env python
#
# Copyright (c) 2019 Poul-Henning Kamp <phk@phk.freebsd.dk>
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
#

"""
Switch-constructions for ARM processors
"""

from pyreveng import assy, data

ARM_SWITCH = '''
+CMP	-	|1 1 1 0|0 0|1|1 0 1 0|1|rn	|0 0 0 0|imm12			|
+BHI	-	|1 0 0 0|1 0 1 0| off						|
+ADR	-	|1 1 1 0|0 0 1 0 1 0 0 0 1 1 1 1|rd	|imm12			|

+LDRB	-	|1 1 1 0|0 1 1|p|u|1|w|1|rn	|rt	|imm5	  |typ|0|rm	|

+LSL	-	|1 1 1 0|0 0|0|1 1 0 1|s|0 0 0 0|rd	|imm5	  |0 0 0|rm	|
+LDRH	-,-	|1 1 1 0|0 0 0|p|u|0|w|1|rn	|rt	|0 0 0 0|1 0 1 1|rm	|

ADD	not	|1 1 1 0|0 0|0|0 1 0 0|s|rn	|rd	|imm5	  |typ|0|rm	|
'''


def switchblock_8(pj, adr, nswitch, lang):
	nswitch += 1
	tl = (nswitch + 3) & ~3
	a = adr
	txt = ''
	for i in range(nswitch):
		o = pj.m[a] * 4
		d = adr + 4 + o
		pj.m.set_label(d, "switch_0x%x_%d" % (adr, i))
		lang.disass(pj, d)
		txt += '[%d] .+0x%x (0x%x)\n' % (i, o, d)
		a += 1
	y = data.Data(pj, adr, adr + tl, fmt=txt)

def switchblock_16(pj, adr, nswitch, lang):
	nswitch += 1
	tl = (nswitch * 2 + 3) & ~3
	a = adr
	txt = ''
	for i in range(nswitch):
		o = pj.m.lu16(a) * 4
		d = adr + 4 + o
		pj.m.set_label(d, "switch_0x%x_%d" % (adr, i))
		lang.disass(pj, d)
		txt += '[%d] .+0x%x (0x%x)\n' % (i, o, d)
		a += 2
	y = data.Data(pj, adr, adr + tl, fmt=txt)


class ArmSwitchIns(assy.Instree_ins):

	def __init__(self, pj, lim, lang):
		super().__init__(pj, lim, lang)
		ref = [
			("+CMP",),
			("+BHI",),
			("+ADR",),
			("+LDRB", "+LSL",),
			("ADD", "+LDRH",),
			("ADD",)
		]
		for i in self.lim:
			if i.assy[0] not in ref[0]:
				raise assy.Invalid("NOT A switch construction")
			ref.pop(0)

	def assy_not(self):

		def fail(why):
			print("FAIL", why)
			raise assy.Invalid(why)

		if False:
			print("SWX ?")
			for i in self.lim:
				print("\t", i, i.assy)
				for j in i.flds:
					print("\t\t", j, i[j])

		ri = self.lim[0]['rn']
		nswitch = self.lim[0]['imm12']

		# XXX: default dst from lim[1]

		rd = self.lim[2]['rd']

		if self.lim[-1].assy[0] != "ADD":
			fail("NOT A switch construction (!add)")

		if self.lim[-1]['rm'] != rd:
			fail("NOT A switch construction (rd/add/rm)")

		if self.lim[-1]['imm5'] != 2:
			fail("NOT A switch construction (add/imm5)")


		txt = ''
		if self.lim[3].assy[0] == "+LSL":
			# 16 bit
			if len(self.lim) != 6:
				fail("NOT A switch construction (16b/len)")

			if self.lim[2]['imm12'] != 8:
				fail("NOT A switch construction (16b/2imm12)")

			if self.lim[3].assy[0] != "+LSL":
				fail("NOT A switch construction (16b/!lsl)")

			if self.lim[4].assy[0] != "+LDRH":
				fail("NOT A switch construction (16b/!ldrh)")

			switchblock_16(pj, self.hi, nswitch, self.lang)

		else:
			# 8 bit
			if len(self.lim) != 5:
				fail("NOT A switch construction (8b/len)")

			if self.lim[2]['imm12'] != 4:
				fail("NOT A switch construction (8b/2imm12)")

			if self.lim[3].assy[0] != "+LDRB":
				fail("NOT A switch construction (8b/!ldrb)")

			if self.lim[3]['rm'] != ri:
				fail("NOT A switch construction (ri/3rm)")
			if self.lim[3]['rn'] != rd:
				fail("NOT A switch construction (rd/3rn)")

			if self.lim[3]['rt'] != rd:
				fail("NOT A switch construction (rd/3rt)")

			switchblock_8(pj, self.hi, nswitch, self.lang)

		raise assy.Invalid("NOTYET")

def arm_switches(disass):
	disass.add_ins(ARM_SWITCH, ArmSwitchIns)
