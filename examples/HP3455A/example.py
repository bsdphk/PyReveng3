#!/usr/bin/env python
#
# Copyright (c) 2012-2014 Poul-Henning Kamp <phk@phk.freebsd.dk>
# HP 3455A modifications: Copyright (c) 2016 Orin Eman <orin.eman@gmail.com>
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

from __future__ import print_function

import os
from pyreveng import job, mem, code, listing
import pyreveng.cpu.hp_nanoproc as hp_nanoproc

def setup():

	m = mem.byte_mem(0x0000, 0x0200)
	fn = os.path.join(os.path.dirname(__file__), "1818-2270B.bin")
	m.load_binfile(0, 1, fn)

	pj = job.Job(m, "HP3455A")

	dx = hp_nanoproc.hp_nanoproc_pg()

	return pj, dx

def line_comment(adr, cmt):
	i = pj.find(adr)
	if i == None:
		return
	assert len(i) == 1
	i = i[0]
	if hasattr(i, 'lcmt'):
	    i.lcmt += cmt
	else:
	    i.lcmt = cmt

symbols = {
	0x001E: "WAIT_CLOCK_LOW",
	0x0021: "WAIT_CLOCK_HIGH",
	0x0028: "PARITY_ERROR",
	0x002A: "WAIT_CLOCK_LOW2",
	0x0032: "SET_LATCHES",
	0x003C: "START_AUTOZERO",
	0x003E: "AUTOZERO_LOOP",
	0x004C: "ZERO_COUNTS",
	0x004C: "SET_LVIN",
	0x0052: "SET_1PLC",
	0x0055: "SET_LNRF_HPRF",
	0x0058: "SET_LVIN_OFF",
	0x005A: "INTEGRATE_LOOP",
	0x0068: "INIT_DISCHARGE_COUNT",
	0x006D: "ATOD_AUTOCAL",
	0x0075: "SET_LNRF_HPRF2",
	0x0078: "SET_LVIN_OFF2",
	0x007C: "INTEGRATE_LOOP_NEXT",
	0x0081: "GOTO_RUNDOWN1",
	0x0088: "GOTO_RUNDOWN2",
	0x008B: "OVER10V",
	0x009C: "DISCHARGE_DURING_INTEGRATE",
	0x00AD: "DISCHARGE_DURING_INTEGRATE2",
	0x00BE: "NO_CARRY",
	0x00C0: "OUTPUT_NEXT_BYTE",
	0x00C3: "OUTPUT_BIT",
	0x00C9: "OUTPUT_FIRST_BYTE",
	0x00CA: "WAIT_CLOCK_HIGH2",
	0x00D5: "SET_OUTPUT_BIT",
	0x00E9: "PATCH_0E9",
	0x00FA: "DELAY3",
	0x00FB: "DELAY2",
	0x00FF: "INTERRUPT",
	0x0110: "SIGNS_DIFFERENT",
	0x0118: "SUBTRACT_SLOW_COUNT",
	0x0130: "LOC_130",
	0x0131: "LOC_131",
	0x0136: "OUTPUT_TO_OUTGUARD",
	0x0145: "RESTART_OUTPUT",
	0x014A: "RUNDOWN",
	0x014F: "MUL8",
	0x016C: "FD_LNRF",
	0x016E: "FAST_DECREMENT_LOOP",
	0x016F: "FDL2",
	0x0177: "FD_HPRF",
	0x017B: "FI_HPRF",
	0x017F: "FI_LNRF",
	0x0184: "FAST_INCREMENT_LOOP",
	0x0185: "FIL2",
	0x018B: "END_FAST_RUNDOWN",
	0x0196: "FR_NO_OVERFLOW",
	0x019B: "SLOW_RUNDOWN",
	0x01A1: "SR_HPRS",
	0x01A5: "SR_LNRS",
	0x01A8: "SLOW_RUNDOWN_LOOP",
	0x01AB: "CHECK_RESULT_SIGN",
	0x01BB: "LAB_1BB",
	0x01BD: "LAB_1BD",
	0x01C5: "LAB_1C5",
	0x01C6: "LAB_1C6",
	0x01C8: "LAB_1C8",
	0x01CB: "INC_PLCCTR",
	0x01D7:	"READ_OUTGUARD",
	0x01D9: "RO_LOOP",
	0x01DD: "RO_WAIT_CLOCK",
	0x01EA: "RO_ZERO_BIT",
	0x01F0:	"STARTUP",
}

def task(pj, dx):
	pj.todo(0, dx.disass)
	pj.todo(0xf7, dx.disass)
	pj.todo(0xfd, dx.disass)
	pj.todo(0xff, dx.disass)

	if True:
		for a,l in symbols.items():
			pj.set_label(a,l)

	pj.set_block_comment(0x000, """HP 3455A inguard ROM

The nanoprocessor takes two clocks per instruction.
The clock runs at 819.2 kHz if 50Hz line frequency is selected
and 983.04 kHz for 60Hz line frequency.

The internal power line cycle counter is 256 times a 32 instruction loop
per PLC, i.e. 256*32*2/983040 giving 16.67 ms for 60Hz.

The startup code is at 0x0FD

DEV1 bits:        REG3 bits:
0x20    LNRF      0   Autocal LNRF and HPRF only
0x10    HPRF      1   8 PLC
0x08    HAZ       2   Autocal - no input to AtoD
0x04    HPRS      3
0x02    LNRS      4   Set device latches to values from outguard
0x01    LVIN      5
Note all device output is inverted in hardware, so the complement must be written to DEV1
""")
	pj.set_block_comment(0x03C, """AtoD Auto-Zero
0x14 = HAZ on, everything else off
AUTOZERO_LOOP is 16 instructions per iteration
""")
	pj.set_block_comment(0x05A, """Main Integration Loop

Register usage:
REG0			# PLCs
REG2			AtoD autocal counter
REG3			Control bits from Outguard
REG5			AtoD device bits for discharge during integration
REG7			Discharge during integration counter
REG9:REG8		PLC counter (REG9 has PLCs elapsed)
REG15			AtoD device bits
REG13:REG12:REG11	Count

These device control bits are used as temporary flags.  It is assumed that
the outguard doesn't drive them and doesn't look at them during integration.

DCTL0	Tentative sign of result is valid
DCTL3	Tentative sign of result

DCTL3 is set during integration when the count is zero.  Should the input voltage
change such that the sign of the voltage on the integration capacitor changes
and the magnitude is greater than 10V, then DCTL0 is cleared to indicate the
sign is potentially invalid and the count should be decremented during the current
discharge period.  Given the approximately 80 times multiplication factor between input
voltage and voltage on the integration capacitor, it wouldn't require much reverse
voltage for very long for this to happen.

DEV1 is written by the second instruction of each loop/sub-loop.
(This fact is used by the PLC counter.)
Each loop or sub-loop during integration is exactly 32 instructions
The count is shifted left by 3 after integration
During fast rundown, each loop is exactly 4 instructions and
during slow rundown, each loop is exactly 2 instructions
REG11 is set during slow rundown, REG13:REG12 are used during integration and fast rundown
The doubling of the count rate and inherent 8 bit shift give the 128:1 weighting between
fast and slow rundown.
""")
	pj.set_block_comment(0x60, """Select discharge type

This code assumes that if DCTL0 (0DETECT) is zero, then DCTL2 is set.
The instruction counts and control bits in REG5 will be wrong otherwise.
DCTL2 was initialized to 1 and does not appear to change during the integration phase.
""")
	pj.set_block_comment(0x8B, """Start discharge during integration

The loop initialization code assumes that there will be no overflow of REG12
when it increments it.  This is usually true since this loop will increment
the count by 8 each time it runs, so we won't hit a count of 255 here.
However, if the input sign changes, with the count at a multiple of 256,
we will decrement the counter and miss the underflow!
REG12 overflow IS handled in the loop itself.
This loop runs for (8 * 32 * 2) clock periods or about 0.5ms.  This will reduce
the magnitude of voltage on the integration capacitor by about 6.1V (1mA from a 0.082uF
capacitor for 0.5ms).

Note that the 0V detect signal was used to set up REG5 and is also used in
CHECK_RESULT_SIGN to determine whether we will increment of decrement the count.
Since we are over 10V here, there is no chance it changed inbetween.
""")
	pj.set_block_comment(0xFF, """Interrupt Handler

The interrupt breaks the slow rundown loop which was accumulating the count in A.
The slow rundown count is saved in REG11 and added to/subtracted from the
rest of the count in REG13:REG12.
The rundown is stopped and auto-zero started immediately.
""")
	pj.set_block_comment(0x14A, """Stop integrating the input and start the rundown

First, counts accumulated during the integration phase are multiplied by 8.
This is because each count represented 32 instruction periods and in the fast
rundown phase, each count represents 4 instruction periods.
It's possible the rundown during integration overshot 0V, so the counts here
may need subtracting from the count, hence the two loops, one that increments
and one that decrements.
""")
	pj.set_block_comment(0x19B, """Slow Rundown

In the slow rundown, counts represent 2 instruction periods.  This, along with the
fact that the current count is effectively shifted left by 8 bits when the slow
count is concatenated gives the 128:1 weighting.
Again, the fast rundown might have overshot 0V, so the direction of the rundown
must be set accordingly.  The interrupt is armed to fire when 0VDETECT changes -
It's the only way you can increment a counter and conditionally loop with two instructions
(it took four instructions per iteration during the fast rundown).
""")
	pj.set_block_comment(0x1CB, """Increment the PLC Counter

This is called every 32 instructions during integration, hence every 64 clocks.
(256 * 64 * clock period) is one PLC, so the high byte of the counter (REG9) ends
up with the number of PLCs elapsed since the counter was zeroed.
REG9 is returned in the accumulator.
""")
	while pj.run():
		pass

	line_comment(0x004, "Use existing settings\n")
	line_comment(0x006, "Default Control Bits\n")
	line_comment(0x009, "Use default settings\n")
	line_comment(0x01D, "Calculated parity\n")
	line_comment(0x03C, "HAZ on\n")
	line_comment(0x03E, "1..11 instructions; loop is 16 instr. per iteration\n")
	line_comment(0x046, "Initialize (zero) the count\n")
	line_comment(0x04C, "LVIN on\n")
	line_comment(0x055, "LNRF,HPRF on\n")
	line_comment(0x075, "LNRF,HPRF on\n")
	line_comment(0x058, "All AtoD inputs off\n")
	line_comment(0x078, "All AtoD inputs off\n")
	line_comment(0x062, "HPRF\n")
	line_comment(0x064, "LNRF\n")
	line_comment(0x06A, "REG7 = 7\n")
	line_comment(0x088, "Maintain 32 instr. between writes to DEV1\n")
	line_comment(0x09E, "Inc/dec count as appropriate\n")
	line_comment(0x0FF, "Stops rundown and sets HAZ\n")
	line_comment(0x132, "Result is negative\n")
	line_comment(0x14A, "Set Integrator to 'Hold'\n")
	line_comment(0x16C, "LNRF on\n")
	line_comment(0x173, "Set Integrator to 'Hold'\n")
	line_comment(0x177, "HPRF on\n")
	line_comment(0x17B, "HPRF on\n")
	line_comment(0x182, "LNRF on\n")
	line_comment(0x189, "Set Integrator to 'Hold'\n")
	line_comment(0x19B, "Arm interrupt on 0VDETECT change\n")
	line_comment(0x1A1, "HPRS on\n")
	line_comment(0x1A5, "LNRS on\n")
	line_comment(0x1A8, "Loop is broken by interrupt\n")
	line_comment(0x1B4, "Result so far is positive\n")
	line_comment(0x1B4, "Result so far is negative\n")

def output(pj):
	code.lcmt_flows(pj)
	listing.Listing(pj, "HP3455A_Inguard.lst")

if __name__ == '__main__':
	pj, cx = setup()
	task(pj, cx)
	output(pj)

