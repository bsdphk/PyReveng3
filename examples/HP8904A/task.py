#!/usr/bin/env python
#
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

from __future__ import print_function

import os
from pyreveng import job, mem, listing, data, code, assy
import decompile

fwd="/critter/Doc/TestAndMeasurement/HP8904A/FW/"

#######################################################################
# The HP8904A has five memory pages, four of which occupy the same
# address space.  We analyse them separately.

def setup(pg):
	if pg < 4:
		m = mem.byte_mem(0x4000, 0x8000)
		fi = open(fwd + "/08904-87008.hex")
		for i in fi:
			j = i.split()
			if int(j[0],10) == pg:
				m.wr(int(j[1],16), int(j[2],16))
		fi.close()
	else:
		m = mem.byte_mem(0x8000, 0x10000)
		m.load_binfile(0x8000, 1, fwd + "08904-87007.bin")

	pj = job.Job(m, "HP8904A_pg%d" % pg)
	pj.pg = pg
	pj.banks.append([0x4000,0x100000])
	return pj,m

#######################################################################
# Collect error strings from pg=3

def collect_errors():
	pj,m = setup(3)
	a = 0x7348
	n = m.rd(a)
	a += 1
	e = {}
	for i in range(n):
		x = m.rd(a)
		a += 1
		l = m.rd(a)
		a += 1
		p = m.bu16(a)
		a += 2
		y1 = data.Txt(pj, p, p + l, label=False)
		e[x] = y1.txt
	return e

errors = collect_errors()

#######################################################################
#

def collect_keys():
	keys = {}
	pj,m = setup(3)
	n = 0
	for a in range(0x4a3f, 0x4aad, 2):
		y = pj.m.bu16(a)
		assert pj.m.rd(y) == 0xcc
		x = pj.m.bu16(y + 1)
		y = data.Txt(pj, x, x + 9)
		t = y.txt[:-4].strip().replace(" ","_")
		pj.set_label(a, "k_0x%02x" % n)
		pj.set_label(y, "test_key_" + t)
		keys[n] = t
		n += 1
	return keys

if False:
	# This gets us the un-shifted name twice
	keys = collect_keys()

keys = {
	0x00:	"NOKEY",
	0x01:	"local",
	0x02:	"f1",
	0x03:	"phase",
	0x04:	"waveform",
	0x05:	"ampl",
	0x06:	"freq",
	0x07:	"shift",
	0x08:	"f2",
	0x09:	"-",
	0x0a:	"7",
	0x0b:	"4",
	0x0c:	"1",
	0x0d:	"inc_set",
	0x0e:	"last",
	0x0f:	"0",
	0x10:	"8",
	0x11:	"5",
	0x12:	"2",
	0x13:	"up_arrow",
	0x14:	"next",
	0x15:	".",
	0x16:	"9",
	0x17:	"6",
	0x18:	"3",
	0x19:	"dn_arrow",
	0x1a:	"f3",
	0x1b:	"enter",
	0x1c:	"deg",
	0x1d:	"Hz",
	0x1e:	"kHz",
	0x1f:	"bkspace",
	0x20:	"f4",
	0x21:	"SPARE0",
	0x22:	"SPARE1",
	0x23:	"SPARE2",
	0x24:	"SPARE3",
	0x25:	"float",
	0x26:	"output",
	0x27:	"adrs",
	0x28:	"filter",
	0x29:	"service",
	0x2a:	"destn",
	0x2b:	"inc_set",
	0x2c:	"main",
	0x2d:	"save",
	0x2e:	"special",
	0x2f:	"recall",
	0x30:	"preset",
	0x31:	"ph_reset",
	0x32:	"shift_f2",
	0x33:	"shift_f4",
	0x34:	"end",
	0x35:	"INVALID",
	0x36:	"DOUBLE",
}

#######################################################################

hpib = {
	"AHR":	"Amplitude Hop",
	"DPE":	"Digital Port",
	"FRH":	"Frequncy Hop Mode",
	"FHR":	"Frequncy Hop",
	"HRA":	"Hop Register",
	"PHH":	"Phase Hop Mode",
	"PHR":	"Phase Hop",
	"QRE":	"Query Port Status",
	"LO":	"Gaussian Filter",
	"SH":	"Sharp Filter",
	"AU":	"Auto Filter",
	"SI":	"Sine",
	"RA":	"Ramp",
	"TR":	"Triangle",
	"SQ":	"Square",
	"NS":	"Noise",
	"DC":	"DC",
	"KZ":	"kHz",
	"HZ":	"Hz",
	"DG":	"Degrees",
	"RD":	"Radians",
	"VL":	"Volts",
	"MV":	"Millivolts",
	"UV":	"Microvolts",
	"ET":	"Enter",
	"SC":	"Seconds",
	"MS":	"Milliseconds",
	"PC":	"Percent",
	"UP":	"Increment Up",
	"DN":	"Increment Down",
	"SEQE":	"Sequence end",
	"SEQP":	"Sequence index",
	"WSQ":	"Sequence string",
	"FRH":	"Tone Frequency",
	"RUNC":	"Run cont.",
	"RUNM": "Run man.",
	"RUNS":	"Run single",
	"STOP":	"Stop Run mode",
	"AM":	"AM mod.",
	"FM":	"FM mod.",
	"PM":	"PM mod.",
	"DS":	"DSB mod.",
	"PU":	"Pulse mod.",
	"APH":	"Tone/DTMF Amplitude",
	"DAPH":	"Dig.Seq. On Level",
	"DAPL":	"Dig.Seq. Off Level",
	"BSB":	"Dig.Seq. Binary Base",
	"BSO":	"Dig.Seq. Octal Base",
	"BSH":	"Dig.Seq. Hex Base",
	"STOF":	"Tone/DTMF Off time",
	"STON":	"Tone/DTMF On time",
	"SBP":	"Dig.Seq. Period",
	"HRA":	"Tone/DTMF Register Number",
	"APA":	"Amplitude A",
	"APB":	"Amplitude B",
	"APC":	"Amplitude C",
	"APD":	"Amplitude D",
	"BO":	"Backlight On",
	"BF":	"Backlight Off",
	"BP":	"Beep",
	"DEA":	"Destination",
	"DEB":	"Destination",
	"DEC":	"Destination",
	"DED":	"Destination",
	"EM":	"Exit",
	"FS":	"Filter",
	"FC":	"Float Control",
	"FRA":	"Frequency",
	"FRB":	"Frequency",
	"FRC":	"Frequency",
	"FRD":	"Frequency",
	"GM":	"Goto Mode",
	"HP":	"Help",
	"ID":	"Id",
	"IS":	"Increment Set",
	"OF":	"Off",
	"ON":	"On",
	"OO":	"Output Control",
	"PHA":	"Phase",
	"PHB":	"Phase",
	"PHC":	"Phase",
	"PHD":	"Phase",
	"PR":	"Phase Reset",
	"PS":	"Instrument Preset",
	"RC":	"Recall",
	"RP":	"Reverse Power",
	"SV":	"Save",
	"RM":	"Read Service Req Mask",
	"SM":	"Set Service Req Mask",
	"SF":	"Special Function",
	"RSF":	"Read Special Function",
	"EO":	"Read External Reference Status",
	"WFA":	"Waveform",
	"WFB":	"Waveform",
	"WFC":	"Waveform",
	"WFD":	"Waveform",
}

#######################################################################

def symb(pj, cpu):
	for p,a,n in [
		(0, 0x4003, "OPT1_LAST_MAIN_MENU_PAGE"),
		(0, 0x4018, "MAIN_MENUS"),
		(0, 0x43bd, "HOP_RAM_ADRS"),
		(0, 0x4908, "HOP_CFG"),
		(0, 0x4ed8, "0x4ed8"),		# @0:54cb -> 3b85
		(0, 0x51e3, "0x51e3"),		# @1:55bc -> 2213
		(0, 0x5253, "APP_CHAN_FINI"),	# @0:54d1 -> 2213
		(0, 0x528f, "APP_CHAN_INIT"),	# @0:54d1 -> 2213
		(0, 0x5d0c, "APP_CHAN_KEYBOARD"),

		(1, 0x42d1, "NMI_0x42d1"),	# @1:6cc4
		(1, 0x444c, "NMI_0x444c"),	# @1:6cb1
		(1, 0x4567, "0x4567"),		# @1:5517
		(1, 0x47fa, "TONE_NBR"),
		(1, 0x4842, "TONE_ON_TIME"),
		(1, 0x4860, "TONE_OFF_TIME"),
		(1, 0x492c, "TONE_F3"),
		(1, 0x49ee, "TSEQ_NBR"),
		(1, 0x4a19, "TSEQ_CONT"),
		(1, 0x4aa2, "TSEQ_SINGLE"),
		(1, 0x4ab9, "TSEQ_STOP"),
		(1, 0x4c01, "KEYBOARD_0x4c01"),		# @1:550b -> 220f
		(1, 0x5185, "0x5185"),		# @1:5511 -> 2211
		(1, 0x51e3, "APPFINI_0x51e3"),	# @1:55bf -> 2213
		(1, 0x55c5, "APP_TONE"),
		(1, 0x71b4, "TSEQ_INDEX"),
		(1, 0x71de, "TSEQ_END"),
		(1, 0x7203, "TSEQ_EDIT"),
		(1, 0x726a, "TSEQ_HEX"),
		(1, 0x7870, "0x7870"),		# @1:79e5
		(1, 0x7a81, "APP_DTMF"),

		(2, 0x4196, "NMI_0x4196"),	# @2:543a
		(2, 0x5b24, "DSEQ_INDEX"),
		(2, 0x5b4e, "DSEQ_END"),
		(2, 0x5b73, "DSEQ_EDIT"),
		(2, 0x5bda, "DSEQ_HEX"),
		(2, 0x642e, "0x642e"),		# @2:6581
		(2, 0x6646, "0x6646"),		# @2:72f0
		(2, 0x689b, "DSEQ_BASE"),
		(2, 0x6917, "DSEQ_PERIOD"),
		(2, 0x6940, "DSEQ_ON_LEVEL"),
		(2, 0x6976, "DSEQ_OFF_LEVEL"),
		(2, 0x69ed, "DSEQ_BIT"),
		(2, 0x6a18, "DSEQ_CONT"),
		(2, 0x6aa1, "DSEQ_SINGLE"),
		(2, 0x6ab8, "DSEQ_STOP"),
		(2, 0x6ad0, "KEYBOARD_0x6ad0"),		# @2:72e4 -> 220f
		(2, 0x6f60, "0x6f60"),		# @2:72ea -> 2211
		(2, 0x6fbe, "APPFINI_0x6fbe"),		# @2:735b -> 2213
		(2, 0x7364, "APP_DSEQ"),

		(3, 0x471c, "ROM_CHECK"),
		(3, 0x4803, "KEY_TEST_KEYS"),	# @3:4b72 -> 23b0
		(3, 0x4b1e, "KEYBOARD_CHECK"),
		(3, 0x4b85, "DIAG_KEYBOARD"),
		(3, 0x4c26, "APP_DIAG"),
		(3, 0x4dcf, "RAM_CHECK"),
		(3, 0x4ef7, "LCD_CHECK"),
		(3, 0x4ff4, "MEM_ACCESS_SET_DEV"),
		(3, 0x50ce, "MEM_ACCESS_KEYBOARD"),
		(3, 0x51f3, "mem_access_up"),
		(3, 0x5108, "mem_access_down"),
		(3, 0x511c, "mem_access_next"),
		(3, 0x513a, "mem_access_prev"),
		(3, 0x5298, "MEM_ACCESS"),
		(3, 0x530f, "PLL_CHECK"),
		(3, 0x5517, "SHOW_REGNAME"),
		(3, 0x5914, "COWCHIP_KEYBOARD"),
		(3, 0x5ec8, "MANUAL_COWCHIP"),
		(3, 0x5a23, "cowchip_next"),
		(3, 0x5a5b, "cowchip_prev"),
		(3, 0x5f96, "MEMORY_KEYBOARD"),
		(3, 0x61bb, "MANUAL_MEMORY"),
		(3, 0x6a25, "KEYPAD_0x6a25"),
		(3, 0x6d64, "INSCODE_KEYPAD"),
		(3, 0x6f80, "SERIAL_KEYPAD"),
		(3, 0x7246, "APP_XX5"),
		(3, 0x7ac3, "APP_ERR"),
		(3, 0x7b7a, "0x7b7a"),

		(4, 0x8000, "SERNO_OPTS"),
		(4, 0x80d2, "LCD_SERNO_OPTS"),
		(4, 0x83a0, "MAIN"),
		(4, 0x8939, "CONFIG_MAIN_MENU"),
		(4, 0x89aa, "0x89aa"),
		(4, 0x8a08, "SET_MENU"),
		(4, 0x8a2f, "0x8a2f"),
		(4, 0x8ad0, "DO_KEYPRESS"),
		(4, 0x8aea, "START_APP"),
		(4, 0x8b4c, "MENU_EXIT"),
		(4, 0x8b63, "SHOW_MAIN_MENU"),
		(4, 0x8c14, "MAIN_KEYBOARD"),		# @0x8d51,0x8edb -> 220f
		(4, 0x8c20, "main_menu_err"),
		(4, 0x8c2d, "main_menu_f1"),
		(4, 0x8c44, "main_menu_nop"),
		(4, 0x8c47, "main_menu_f3"),
		(4, 0x8c5e, "main_menu_next"),
		(4, 0x8c83, "main_menu_prev"),
		(4, 0x90c9, "0x90c9"),
		(4, 0x975e, "0x975e"),
		(4, 0x9a37, "INIT_LEDS"),
		(4, 0x9a40, "LEDS____0___*"),
		(4, 0x9a43, "LEDS____0___"),
		(4, 0x9a47, "LEDS_____0__"),
		(4, 0x9a4b, "LEDS______0_"),
		(4, 0x9a4f, "LEDS_______0"),
		(4, 0x9a53, "LEDS___0____"),
		(4, 0x9a57, "LEDS__0_____"),
		(4, 0x9a5b, "LEDS____1___*"),
		(4, 0x9a5e, "LEDS____1___"),
		(4, 0x9a62, "LEDS_____1__"),
		(4, 0x9a66, "LEDS______1_"),
		(4, 0x9a6a, "LEDS_______1"),
		(4, 0x9a6e, "LEDS___1____"),
		(4, 0x9a72, "LEDS__1_____"),
		(4, 0x9a76, "LEDS__111111"),
		(4, 0x9a7d, "LEDS__000000"),
		(4, 0x9b08, "0x9b08"),
		(4, 0x9b70, "0x9b70"),
		(4, 0x9da2, "0x9da2"),
		(4, 0x9e53, "0x9e53"),		# @0x8d51,0x8edb -> 220f
		(4, 0x9e7a, "0x9e7a"),
		(4, 0x9ffe, "HPIB_SEND"),
		(4, 0xa0d4, "KEYPAD_0xa0d4"),
		(4, 0xa23f, "KEYPAD_0xa23f"),
		(4, 0xa30e, "HPIB_HP"),
		(4, 0xa3a0, "HPIB_ID"),
		(4, 0xa3c6, "HPIB_ST_ID"),
		(4, 0xa3e3, "0xa3e3"),
		(4, 0xa9a2, "KBD_SENSE"),
		(4, 0xaae8, "XLATE_KEYPRESS"),
		(4, 0xab7a, "GETKEY"),
		(4, 0xaba9, "DISPLAY_DEST"),
		(4, 0xabef, "DISPLAY_UNIT"),
		(4, 0xac35, "NP_INIT"),
		(4, 0xad4d, "KEY_TRANSLATE"),
		(4, 0xae22, "non_func_key"),
		(4, 0xb3c2, "KEY_EVENT"),
		(4, 0xb646, "RESET_OUTPUTS"),
		(4, 0xb852, "COUNT_OUTPUTS"),
		(4, 0xb8ad, "0xb8ad"),
		(4, 0xb8cc, "0xb8cc"),
		(4, 0xc1e3, "0xc1e3"),
		(4, 0xc239, "NULL"),
		(4, 0xc242, "MEMCMP"),
		(4, 0xc285, "MEMCPY"),
		(4, 0xc2c4, "CLEAR_NVRAM"),
		(4, 0xc36e, "CHECK_NVRAM"),
		(4, 0xc3fe, "RAISE_ERROR"),
		(4, 0xc418, "SHOW_CLR_ERROR"),
		(4, 0xc7b0, "0xc7b0"),
		(4, 0xc855, "0xc855"),
		(4, 0xc885, "0xc885"),
		(4, 0xc973, "0xc973"),
		(4, 0xc912, "WORD2ASC"),
		(4, 0xc9d1, "BYTE2ASC"),
		(4, 0xca8f, "NUM2ASC"),
		(4, 0xcb10, "0xcb10"),
		(4, 0xcba6, "BYTE2HEX"),
		(4, 0xcc09, "WORD2HEX"),
		(4, 0xccb5, "0xccb5"),
		(4, 0xccff, "ZERO_SUPRESS"),
		(4, 0xcd50, "0xcd50"),
		(4, 0xd022, "0xd022"),
		(4, 0xd17d, "0xd17d"),
		(4, 0xd2c6, "0xd2c6"),
		(4, 0xd303, "MUL32"),
		(4, 0xd37d, "NUM_SET"),
		(4, 0xd392, "NUM_ADD"),
		(4, 0xd3c6, "NUM_SUB"),
		(4, 0xd57c, "0xd57c"),
		(4, 0xd596, "INIT_PTM"),
		(4, 0xd5f1, "PTM_DISABLE_IRQ"),
		(4, 0xd640, "DELAY"),
		(4, 0xd670, "SLEEP"),
		(4, 0xd6c8, "BEEP"),
		(4, 0xd71d, "LCD_WR_CTRL"),
		(4, 0xd73f, "LCD_WR_DATA"),
		(4, 0xd761, "LCD_RD_DATA"),
		(4, 0xd781, "LCD_RD_CTRL"),
		(4, 0xd7a0, "LCD_DDRAM"),
		(4, 0xd7be, "LCD_CURSOR"),
		(4, 0xd841, "LCD_DEF_CHAR"),
		(4, 0xd8a5, "LCD_SHOW"),
		(4, 0xd8ea, "DISPLAY"),
		(4, 0xd989, "DISPLAY2L"),
		(4, 0xd9c6, "LCD_AS_MIRROR"),
		(4, 0xd9e6, "LCD_INIT"),
		(4, 0xdae0, "BANKSWITCH"),
		(4, 0xdb2b, "CALL_BANK"),
		(4, 0xdb5c, "BACKLIGHT_ON"),
		(4, 0xdb7d, "BACKLIGHT_OFF"),
		(4, 0xdba1, "OUTPUT_AND_OR"),
		(4, 0xdc7b, "RAM_ROM_TEST"),
		(4, 0xdc82, "RAM_TEST"),
		(4, 0xdca9, "ROM_SUM"),
		(4, 0xdd1e, "APP_JMP"),
		(4, 0xdeb6, "0xdeb6"),
		(4, 0xe029, "0xe029"),
		(4, 0xe185, "0xe185"),
		(4, 0xe319, "0xe319"),
		(4, 0xe69c, "0xe69c"),
		(4, 0xe8a7, "0xe8a7"),
		(4, 0xef4a, "KEY_XLATE_TAB"),
		(4, 0xf02a, "SET_NMI_VEC"),
		(4, 0xf044, "SET_FIRQ_VEC"),
		(4, 0xf0a1, "HANDLE_FIRQ"),
		(4, 0xf05e, "PTM_IRQ"),
		(4, 0xf154, "HANDLE_IRQ"),
		(4, 0xf1d9, "KEYPAD_0xf1d9"),
		(4, 0xf3f0, "KEYPAD_0xf3f0"),
		(4, 0xf7ec, "0xf7ec"),
		(4, 0xf9d4, "KEYPAD_0xf9d4"),
		(4, 0xfcea, "ARRAY_INDEX"),
		(4, 0xfd50, "PROLOGUE"),
		(4, 0xfd80, "D=A+B"),
		(4, 0xfd8f, "D=A-B"),
		(4, 0xfd9e, "B=A<<B"),
		(4, 0xfdb6, "B=CC:Z"),
		(4, 0xfe5f, "B=A/B"),
		(4, 0xffa4, "D=X<<B"),
		(4, 0xffc0, "ret_0"),
		(4, 0xffc6, "ret_1"),

		(5, 0xee62, "dest_strings"),
		(5, 0xeeee, "unit_strings"),
		(5, 0xed11, "blank_line"),

		(6, 0x0100, "SERVICE_SWITCH"),
		(6, 0x0200, "NSMIC"),
		(6, 0x0300, "LCD_CTL"),
		(6, 0x0301, "LCD_DATA"),
		(6, 0x0400, "HPIB_0"),
		(6, 0x0401, "HPIB_1"),
		(6, 0x0402, "HPIB_2"),
		(6, 0x0403, "HPIB_3"),
		(6, 0x0404, "HPIB_4"),
		(6, 0x0405, "HPIB_5"),
		(6, 0x0406, "HPIB_6"),
		(6, 0x0407, "HPIB_7"),
		(6, 0x0600, "IO_600"),
		(6, 0x0900, "LEDS"),
		(6, 0x0a00, "KBDSCAN"),
		(6, 0x0b00, "HOPLATCH"),
		(6, 0x0c00, "OUTPUT_1"),
		(6, 0x0d00, "OUTPUT_2"),
		(6, 0x0e00, "OUTPUT_3"),
		(6, 0x0f00, "OUTPUT_4"),
		(6, 0x1000, "PTM_0"),
		(6, 0x1001, "PTM_1"),
		(6, 0x1002, "PTM_TIMER1"),
		(6, 0x1004, "PTM_TIMER2"),
		(6, 0x1006, "PTM_TIMER3"),
		# 0x2202:0x0001, "shift pressed"
		# 0x2204:0x0001, "IRQ happened"
		# 0x2204:0x0080, "backlight on"
		(6, 0x220d, "APP_KEYPAD"),
		(6, 0x220f, "APP_KEYBOARD"),
		(6, 0x2213, "APP_FINI"),
		(6, 0x2217, "KEYPRESS"),
		(6, 0x2219, "MAIN_MENU_APPNO"),
		(6, 0x2223, "MAIN_MENU_LAST_PG"),
		(6, 0x2224, "MAIN_MENU_APPTBL"),
		(6, 0x23b2, "N_OUTPUTS"),
		(6, 0x23dd, "NVRAM_CHECK_STATUS"),
		(6, 0x23de, "ERROR_CODE"),
		(6, 0x2420, "LEDS_COPY"),
		(6, 0x2421, "PTM_CR1_COPY"),
		(6, 0x2422, "PTM_CR2_COPY"),
		(6, 0x2423, "PTM_CR3_COPY"),
		(6, 0x2424, "PTM_TIMER1_COPY"),
		(6, 0x2426, "PTM_TIMER2_COPY"),
		(6, 0x2428, "PTM_TIMER3_COPY"),
		(6, 0x242a, "cursor-state"),
		(6, 0x2240, "MENU_PTR"),
		(6, 0x2245, "MAIN_MENU_CUR_PG"),
		(6, 0x2242, "MENU_CNT"),
		(6, 0x23be, "Array*35_idx"),
		(6, 0x23df, "ERRMSG_LEN"),
		(6, 0x23e0, "ERRMSG_BUF"),
		(6, 0x241f, "KBDSCAN_COPY"),
		(6, 0x242b, "LCD_MIRROR"),
		(6, 0x247b, "CUR_BANK"),
		(6, 0x247c, "APP_BANK"),
		(6, 0x247d, "APP_VECTOR"),
		(6, 0x24d8, "NMIVEC"),
		(6, 0x24da, "FIRQVEC"),
		(6, 0x24dc, "KEY_PRESSED"),
		(6, 0x24e6, "CURR_APP"),
		(6, 0x24f0, "OUTPUT_COPY[4]"),
		(6, 0x24f4, "Array*35_idx"),
		(6, 0x24f5, "Array*35"),
		(6, 0x2581, "Array*15"),
		(6, 0x268f, "Array_Save_Recall_(12*425)"),
		(6, 0x3c05, "Array*4_idx"),
		(6, 0x3c10, "Array*4"),
		(6, 0x3c50, "Array*3"),
		(6, 0x3fa1, "PREV_KEY"),
		(6, 0x3fa9, "mem_access_device"),
		(6, 0x3faa, "mem_access_max"),
		(6, 0x3fab, "mem_access_base"),
		(6, 0x3fad, "mem_access_ptr"),
		(6, 0x3faf, "mem_access_name"),
		(6, 0x3ffc, "OPTIONS"),
	]:
		if p == pj.pg:
			assert a >= pj.m.lo and a < pj.m.hi
			cpu.disass(pj, a)
		if p == pj.pg or p >= 4:
			pj.set_label(a, n)


#######################################################################

def romsum(pj):
	b = 0
	c = 0
	for x in range(pj.m.lo, pj.m.hi):
		b += pj.m.rd(x) + c
		c = b >> 8
		c = 1
		b &= 0xff
	print("CKSUM(0x%04x-0x%04x) = 0x%x" % (pj.m.lo, pj.m.hi, b))

	if pj.pg == 0:
		y = data.Const(pj, 0x4002, 0x4003)
		pj.set_label(y.lo, "EPROM_PAGES")

	if pj.pg < 4:
		assert b == pj.pg

		y = data.Const(pj, 0x4001, 0x4002)
		pj.set_label(y.lo, "EPROM_SUM_%d" % pj.pg)

		y = data.Const(pj, 0x4000, 0x4001, "'%c'")
		assert pj.m.rd(y.lo) == 0x30 + pj.pg
		pj.set_label(y.lo, "EPROM_PAGE_%d" % pj.pg)

	else:
		assert b == 0

#######################################################################

def lexer(pj):

	assert pj.pg == 4

	class lex(data.Data):
		def __init__(self, pj, lo, pfx):
			hi = lo + 4
			self.f = pj.m.rd(lo + 1)
			self.t = pj.m.bu16(lo + 2)
			self.pfx = pfx + "%c" % pj.m.rd(lo)
			if self.f > 0:
				hi += 1
			super(lex, self).__init__(pj, lo, hi, "lex")
			if self.f > 0 and self.pfx in hpib:
				self.lcmt += hpib[self.pfx] + "\n"
			self.compact = True
			if self.f > 0 and self.t not in pj.labels:
				pj.set_label(self.t, "J_" + self.pfx)
				cpu.disass(pj, self.t)
				h = hpib.get(self.pfx)
				if h == None:
					h = "UNDOC!"
				y=pj.t.find_lo(self.t)
				assert len(y) == 1
				y[0].lcmt += "HPIB: " + h + "\n"

		def render(self, pj):
			s = ".LEX\t\"%s\", " % self.pfx
			s += "%d, " % pj.m.rd(self.lo + 1)
			s += pj.render_adr(pj.m.bu16(self.lo + 2))
			if self.f:
				s += ", 0x%02x" % pj.m.rd(self.lo + 4)
			return s

	def tx(a, pfx):
		t0 = a
		while pj.m.rd(a) != 0:
			y = lex(pj, a, pfx)
			a = y.hi
			if y.f == 0:
				b = pj.m.bu16(y.lo + 2)
				p = pfx + "%c" % pj.m.rd(y.lo)
				pj.set_label(b, "LEX_" + p)
				tx(b, p)
		data.Const(pj, a, a + 1)

	pj.set_label(0x9780, "LEXTAB_ALPHABET")
	n = 65
	for i in range(0x9780, 0x97b4, 2):
		data.Dataptr(pj, i, i + 2, pj.m.bu16(i))
		a = pj.m.bu16(i)
		if n != 0x5a:
			pj.set_label(a, "LEX_%c" % n)
		else:
			pj.set_label(a, "LEX_NULL")
		tx(a, "%c" % n)
		n += 1

	pj.set_label(0x9a22, "LEXTAB_OTHER")
	tx(0x9a22, "")

#######################################################################

class Num(data.Data):
	def __init__(self, pj, lo):
		super(Num, self).__init__(pj, lo, lo + 3, "Num")
		a = pj.m.rd(lo) << 16
		a += pj.m.rd(lo + 1) << 8
		a += pj.m.rd(lo + 2)
		self.val = a
		self.fmt = ".NUM\t%d" % a
		pj.set_label(lo, "N%d" % a)

#######################################################################

class MenuPage(data.Data):
	def __init__(self, pj, cpu, lo):
		super(MenuPage, self).__init__(pj, lo, lo + 10, "MenuPage")
		t = pj.m.bu16(lo)
		y1 = data.Txt(pj, t, t + 40, label=False)
		y1.compact = True
		y2 = data.Txt(pj, t + 40, t + 80, label=False)
		y2.compact = True
		self.t1 = y1.txt
		self.t2 = y2.txt
		self.ptr = []
		for i in range(1, 5):
			u = pj.m.bu16(lo + 2 * i)
			self.ptr.append(u)
			if u >= pj.m.lo and u < pj.m.hi:
				cpu.disass(pj, u)

	def render(self, pj):
		s = "MENUPAGE {\n"
		s += "\t.txt1 = \"%s\"\n" % self.t1
		s += "\t.txt2 = \"%s\"\n" % self.t2
		for i in range(4):
			s += "\t.f%d = " % (i + 1)
			s += "%s\n" % pj.render_adr(self.ptr[i])
		s += "}"
		return s

def Menu(pj, cpu, a, nm):
	pj.set_label(a, nm)
	data.Const(pj, a - 1, a)
	n = pj.m.rd(a - 1)
	for i in range(0, n + 1):
		MenuPage(pj, cpu, a + i * 10)

#######################################################################
# Markup RAISE

def error_arg(pj, dst, arg, errors):
	for i in pj:
		if type(i) != decompile.Call or i.dst != dst:
			continue
		if i.args[arg][0] != "#":
			continue
		n = int(i.args[arg][1:], 16)
		if n in errors:
			i.lcmt += '"%s"\n' % errors[n]

#######################################################################
# Markup Number arguments

def num_arg(pj, dst, arg):
	for i in pj:
		if type(i) != decompile.Call or i.dst != dst:
			continue
		if i.args[arg][:3] != "#0x":
			continue
		n = int(i.args[arg][1:], 16)
		if n < pj.m.lo or n >= pj.m.hi:
			continue
		j = pj.t.find_lo(n)
		print("NUM", "%04x" % n, i, i.args, j)
		if len(j) == 0:
			j.append(Num(pj, n))
		i.args[arg] = "NUM(%d)" % j[0].val

#######################################################################
# String+length args

arg_strings = set()

def str_len_args(pj, dst, args, argl):
	for i in pj:
		if type(i) != decompile.Call or i.dst != dst:
			continue
		if i.args[args][:3] != "#0x":
			continue
		if argl >= 0 and i.args[argl][:3] != "#0x":
			continue
		s = int(i.args[args][1:],16)
		if s < pj.m.lo or s >= pj.m.hi:
			continue
		if argl < 0:
			l = -argl
		else:
			l = int(i.args[argl][1:],16)
		print("SL", "%04x" % s, l, i, i.args)
		j = pj.t.find_lo(s)
		if len(j) == 0:
			y = data.Txt(pj, s, s + l)
			y.compact = True
			j.append(y)
			print("SLN", y.txt)
			arg_strings.add(s)
		elif s not in arg_strings:
			print("SLX", pj.pg, "%04x" % j[0].lo, j[0].txt)
		i.lcmt += '"%s"\n' % j[0].txt

#######################################################################

def hints(pj, cpu):

	if pj.pg == 0:
		Menu(pj, cpu, 0x433e, "CHANMENU")

		# @0x8948
		data.Const(pj, 0x4003, 0x4004)

		# @0x8954
		for a,n in [
		    [ 0x4008, "START_TONE_APP" ],
		    [ 0x400a, "START_DTMF_APP" ],
		    [ 0x400c, "START_DSEQ_APP" ],
		    [ 0x4022, "START_DIAG_APP" ],
		    [ 0x4024, "START_XX5_APP" ],
		    [ 0x404f, "START_ERR_APP" ],
		]:
			cpu.codeptr(pj, a)
			u = pj.m.bu16(a)
			pj.set_label(u, n.lower())
			pj.set_label(a, n)

		cpu.codeptr(pj, 0x4004)
		cpu.codeptr(pj, 0x4006)
		for a in range(0x400e, 0x4018, 2):
			cpu.codeptr(pj, a)

		for a in range(0x4018, 0x4022, 2):
			y = data.Dataptr(pj, a, a + 2, pj.m.bu16(a))
			u = pj.m.bu16(a)
			y = data.Txt(pj, u, u + 40, label=False)
			y.compact = True


		# @0xc4a5, @0xc318
		for a in range(0x404f,0x4053,2):
			cpu.codeptr(pj, a)

		for a,b in (
			(0x4027, 0x28),
			(0x411b, 0x28),
			(0x4143, 0x28),
			(0x416b, 0x28),
			(0x4193, 0x28),
			(0x4391, 0x04),
			(0x4395, 0x0f),
			(0x43a4, 0x0c),
			(0x43b0, 0x0d),
			(0x5cce, 0x1),
			(0x5cd0, 0x1),
			(0x5cd2, 0x1),
			(0x5cd4, 0x1),
		):
			y = data.Txt(pj, a, a + b, label=False)
			y.compact = True

		y = data.Txt(pj, 0x41bb, 0x41bb + 12, label=False)
		y.compact = True


	if pj.pg == 1:
		Menu(pj, cpu, 0x416b, "TONEMENU")
		Menu(pj, cpu, 0x4234, "DTMFMENU")

		for a,n in (
		    (0x5609, 7),
		    (0x69a6, 0x28),
		    (0x69d1, 5),
		):
			y = data.Txt(pj, a, a + n, label=False)
			y.compact = True
		for a in (0x4142,0x4156):
			y = data.Txt(pj, a, a + 0x14, label=False)
			y.compact = True
		for a in range(0x43bc, 0x43f2, 3):
			data.Const(pj, a, a + 3)

		Num(pj, 0x4262)
		Num(pj, 0x4265)

	if pj.pg == 2:
		Menu(pj, cpu, 0x416b, "DSEQMENU")
		for a in range(0x4245, 0x4255, 2):
			cpu.codeptr(pj, a)
		for a in range(0x4330, 0x4340, 2):
			cpu.codeptr(pj, a)
		for a,b in (
			(0x5144,20),
			(0x5159,20),
			(0x516f,3),
			(0x5173,3),
			(0x5177,3),
			(0x517b,5),
		):
			y = data.Txt(pj, a, a + b, label=False)
			y.compact = True

	if pj.pg == 3:
		Menu(pj, cpu, 0x4178, "DIAGMENU")
		MenuPage(pj, cpu, 0x4196)
		for i in range(0x3f):
			a = 0x7349 + 4 * i
			y = data.Const(pj, a, a + 2)
			y.typ = ".BYTE"
			y.fmt = "%d, %d" % (pj.m.rd(a), pj.m.rd(a + 1))
			u = pj.m.bu16(a + 2)
			l = pj.m.rd(a + 1)
			data.Dataptr(pj, a + 2, a + 4, pj.m.bu16(a + 2))
			y = data.Txt(pj, u, u + l, label=False)
			y.compact = True
		for a,b in (
			(0x4002,53),
			(0x4466,6),
			(0x7339,3),
			(0x733d,3),
			(0x550f,2),
		):
			y = data.Txt(pj, a, a + b, label=False)
			y.compact = True

		for a in range(0x63da, 0x665a, 40):
			y = data.Txt(pj, a, a + 40, label=False)
			y.compact = True

		a = 0x4c64
		while a < 0x4dcb:
			y = data.Txt(pj, a)
			y.compact = True
			a = y.hi

		a = 0x54cf
		while a < 0x550d:
			y = data.Txt(pj, a)
			y.compact = True
			a = y.hi

		a = 0x624d
		while a < 0x63a4:
			y = data.Txt(pj, a)
			y.compact = True
			a = y.hi

		for a in range(0x4a3f, 0x4aad, 2):
			y = pj.m.bu16(a)
			assert pj.m.rd(y) == 0xcc
			x = pj.m.bu16(y + 1)
			z = pj.t.find_lo(x)
			if len(z) > 0:
				t = z[0].txt[:-4].strip().replace(" ","_")
				pj.set_label(y, "test_key_" + t)

		Num(pj, 0x684a)


	if pj.pg == 4:
		data.Const(pj, 0xfd6e, 0xfd70)
		for a in range(0xee62, 0xee88, 2):
			u = pj.m.bu16(a)
			y = data.Dataptr(pj, a, a + 2, u)
			y = data.Const(pj, u, u + 1)
			y = data.Txt(pj, u + 1, u + 1 + pj.m.rd(u), label=False)
			y.compact = True
		for a in range(0xeeee, 0x0ef0e, 2):
			u = pj.m.bu16(a)
			y = data.Dataptr(pj, a, a + 2, u)
			y = data.Const(pj, u, u + 1)
			y = data.Txt(pj, u + 1, u + 1 + pj.m.rd(u), label=False)
			y.compact = True
		for a in range(0xef94, 0xf014, 8):
			y = data.Const(pj, a, a + 8, fmt="0x%02x")

		for a,b in (
			(0x8f7c,35),
			(0x977b, 5),
			(0xed11,40),
			(0xea99,0x23),
			(0xeb41,40),
			(0xeb69,40),
			(0xec5b,14),
			(0xec69,14),
			(0xec77,14),
			(0xec85,0x36),
			(0xecbb,6),
			(0xecc1,40),
			(0xece9,40),
		):
			y = data.Txt(pj, a, a + b, label=False)
			y.compact = True

		def char_def(pj, a):
			for i in range(8):
				y = data.Data(pj, a + i, a + i + 1)
				x = pj.m.rd(a + i)
				y.fmt = ".BITS\t"
				for j in range(8):
					if x & 0x80:
						y.fmt += "#"
					else:
						y.fmt += "-"
					x = x << 1

		l = [ "LCD_CHR_f", "LCD_CHR_1", "LCD_CHR_2", "LCD_CHR_3",
		      "LCD_CHR_4", "LCD_CHR_phi", "LCD_CHR_mu", "LCD_CHR_is", ]
		for a in range(0xea15, 0xea4e, 8):
			pj.set_label(a, l.pop(0))
			char_def(pj, a)

		data.Const(pj, 0x929d, 0x929d + 8)
		data.Const(pj, 0x9777, 0x9777 + 4)
		data.Const(pj, 0xdd73, 0xdd9d)

		# 2 x 35 bytes, no idea...
		for a in range(0xed89, 0xedcf, 5):
			data.Const(pj, a, a + 5, "0x%02x")

		n = 1
		for a in range(0xae3d, 0xaea5, 2):
			print("%x -> " % a + keys[n])
			u = pj.m.bu16(a)
			if u != 0xae22:
				pj.set_label(u, "key_" + keys[n])
			n += 1

		Num(pj, 0xea55)
		Num(pj, 0xea6e)
		Num(pj, 0xea65)
		Num(pj, 0xea6b)
		Num(pj, 0xea62)
		Num(pj, 0xea68)
		for a in range(0xee4a,0xee62, 3):
			Num(pj,a)

		for a in range(0xef4a, 0xef94, 2):
			y = data.Const(pj, a, a + 2, fmt="0x%02x")
			i = keys.get(pj.m.rd(a))
			j = keys.get(pj.m.rd(a + 1))
			y.lcmt += "%8s | %-8s\n" % (i, j)

#######################################################################

for pg in (0,1,2,3,4):

	pj,m = setup(pg)

	romsum(pj)

	decompile.setup(pj)

	cpu = decompile.mc6809a()

	hints(pj, cpu)

	symb(pj, cpu)

	if pj.pg == 4:
		lexer(pj)
		cpu.vectors(pj)

	while pj.run():
		pass

	decompile.analyse(pj, cpu)

	while pj.run():
		pass

	str_len_args(pj, 0xd8a5, 3, 2)
	str_len_args(pj, 0x9ffe, 1, 2)
	error_arg(pj, 0xc3fe, 1, errors)
	num_arg(pj, 0xd37d, 1)
	num_arg(pj, 0xd37d, 2)
	num_arg(pj, 0xd392, 1)
	num_arg(pj, 0xd392, 2)
	num_arg(pj, 0xd3c6, 1)
	num_arg(pj, 0xd3c6, 2)
	str_len_args(pj, 0xd8ea, 3, 2)
	if pj.pg == 2:
		str_len_args(pj, 0x44ee, 3, 2)

	decompile.mopup(pj, cpu)

	code.lcmt_flows(pj)

	listing.Listing(pj)

#######################################################################
# fcea is array index multiplicator
#	A is always 0x01
#	X points to six bytes: {00 01 00 00 xx xx} where xxxx is stride
#	Stack contains base + index
#	result in X
