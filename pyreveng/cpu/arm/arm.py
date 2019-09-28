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
Disassembler for ARM processors
"""

from pyreveng import assy, data
from pyreveng.cpu.arm import arm_base

arm_desc = """

# pages ref: DDI0406C_d_armv7ar_arm.pdf
# XXX: Wildcards until comple
misc_192	?		|cond	|op1  |x1				      |b|x2	|
misc_194	?		|cond	|0 0|p|op1	|x0			|op2	|x1	|
misc_195	?		|cond	|0 0 0|op	|x0		|imm5	  |op2|0|x1	|
misc_195b	?		|cond	|0 0 0|op1	|x0			|0|op2|1|x1	|
misc_197	?		|cond	|0 0 1|op1	|Rn	|x0				|
misc_200	?		|cond	|0 0 0 0|op	|x0			|1 0 0 1|x1	|
misc_200b	?		|cond	|0 0 0 1|0|op |0|x0			|0 1 0 1|x1	|
misc_200c	?		|cond	|0 0 0 1|0|op |0|x0			|1|y|c|0|x2	|
misc_201	?		|cond	|0 0 0|op1	|rn	|x0		|1|op2|1|x1	|
misc_202	?		|cond	|0 0 0 0|x1 |1|o|x0	|x1	|x2	|1|op2|1|x3	|
misc_203	?		|cond	|0 0 0 1|op	|x0			|1 0 0 1|x1	|
misc_204	?		|cond	|0 0 1 1 0|o|1 0|op1	|x0		|x2		|
misc_205	?		|cond	|0 0 0|1 0|op |0|op1	|xxx0	    |b|x|0|op2	|xxx1	|
misc_206	?		|cond	|0 0 1 1 0|0|1 0|op1	|x0		|x2		|
misc_207	?		|cond	|0 1 1|opt	|x0	|rd	|x1	|op2  |1|rn	|
misc_208	?		|cond	|0 1 1 0 0 0|op |x0			|op2  |1|x1	|
misc_208b	?		|cond	|0 1 1 0 0 1|op |x0			|op2  |1|x1	|
misc_209	?		|cond	|0 1 1 0 1|op	|a	|x0		|op2  |1|x1	|
misc_211	?		|cond	|0 1 1 1 0|op1	|x1	|a	|x2	|op2  |1|x1	|
misc_212	?		|cond	|1 0|op		|rn	|r|x1				|
misc_213	?		|cond	|1 1|op		|rn	|x1	|cp	|x2   |o|x3	|
misc_214	?		|1 1 1 1| xyz							|
misc_215	?		|1 1 1 1 0|op1		|rn	|x1		|op2	|x2	|
"""

arm_desc = """

################################################################################################

# A8-298...303
ADC		S,Rd,Rn,imm12	|cond	|0 0|1|0 1 0 1|s|rn	|rd	|imm12			|
ADC		S,Rd,Rn,Rm,sh	|cond	|0 0|0|0 1 0 1|s|rn	|rd	|imm5	  |typ|0|rm	|
ADC		S,Rd,Rn,Rm,Rs	|cond	|0 0|0|0 1 0 1|s|rn	|rd	|rs	|0|typ|1|rm	|

# p304-313
ADD		S,Rd,Rn,imm12	|cond	|0 0|1|0 1 0 0|s|rn	|rd	|imm12			|
ADD		S,Rd,Rn,Rm,sh	|cond	|0 0|0|0 1 0 0|s|rn	|rd	|imm5	  |typ|0|rm	|
ADD		S,Rd,Rn,Rm,Rs	|cond	|0 0|0|0 1 0 0|s|rn	|rd	|rs	|0|typ|1|rm	|

# p320-321
ADR		Rd,adr_plus	|cond	|0 0 1 0 1 0 0 0 1 1 1 1|rd	|imm12			|
ADR		Rd,adr_minus	|cond	|0 0 1 0 0 1 0 0 1 1 1 1|rd	|imm12			|

# p322-327
AND		S,Rd,Rn,imm12	|cond	|0 0|1|0 0 0 0|s|rn	|rd	|imm12			|
AND		S,Rd,Rn,Rm,sh	|cond	|0 0|0|0 0 0 0|s|rn	|rd	|imm5	  |typ|0|rm	|
AND		S,Rd,Rn,Rm,Rs	|cond	|0 0|0|0 0 0 0|s|rn	|rd	|rs	|0|typ|1|rm	|

# p328-331
ASR		S,Rd,Rm,imm5	|cond	|0 0|0|1 1 0 1|s|0 0 0 0|rd	|imm5	  |1 0 0|rm	|
ASR		S,Rd,Rn,Rm 	|cond	|0 0|0|1 1 0 1|s|0 0 0 0|rd	|rm	|0 1 0 1|rn	|

# p332-333
B		dst,>J		|cond	|1 0 1 0|off						|

# p336-337
BFC		?		|cond	|0 1 1 1 1 1 0|msb	|rd	|lsb	  |0 0 1|1 1 1 1|

# p336-337
BFI		?		|cond	|0 1 1 1 1 1 0|msb	|rd	|lsb	  |0 0 1|rn	|

# p338-343
BIC		S,Rd,Rn,imm12	|cond	|0 0|1|1 1 1 0|s|rn	|rd	|imm12			|
BIC		S,Rd,Rn,Rm,sh	|cond	|0 0|0|1 1 1 0|s|rn	|rd	|imm5	  |typ|0|rm	|
BIC		S,Rd,Rn,Rm,Rs	|cond	|0 0|0|1 1 1 0|s|rn	|rd	|rs	|0|typ|1|rm	|

# p344-345
BKPT		?		|cond	|0 0 0 1 0 0 1 0|imm12			|0 1 1 1|imm4	|

# p346-349
BL		dst,>C		|cond	|1 0 1 1|off						|
BLX		dst,>C		|1 1 1 1|1 0 1|0|off						|
BLX		imm24,>C	|1 1 1 1|1 0 1|1|off						|
BLX		Rm,>C		|cond	|0 0 0 1 0 0 1 0|1 1 1 1|1 1 1 1|1 1 1 1|0 0 1 1|rm	|

# p350-351
BX		Rm,>J		|cond	|0 0 0 1 0 0 1 0|1 1 1 1|1 1 1 1|1 1 1 1|0 0 0 1|rm	|

# p352-353
BXJ		?		|cond	|0 0 0 1 0 0 1 0|1 1 1 1|1 1 1 1|1 1 1 1|0 0 1 0|rm	|

# p356-357
CDP		?		|cond	|1 1 1 0|opc1	|crn	|crd	|coproc	|opc2 |0|crm	|
CDP2		?		|1 1 1 1|1 1 1 0|opc1	|crn	|crd	|coproc	|opc2 |0|crm	|

# p358-359
CLREX		?		|cond	|0 1 0 1 0 1 1 1|1 1 1 1|1 1 1 1|0 0 0 0|0 0 0 1|1 1 1 1|

# p360-361
CLZ		?		|cond	|0 0 0 1 0 1 1 0|1 1 1 1|rd	|1 1 1 1|0 0 0 1|rm	|

# p362-367
CMN		Rn,imm12	|cond	|0 0|1|1 0 1 1|1|rn	|0 0 0 0|imm12			|
CMN		Rn,Rm,sh	|cond	|0 0|0|1 0 1 1|1|rn	|0 0 0 0|imm5	  |typ|0|rm	|
CMN		Rn,Rm,Rs 	|cond	|0 0|0|1 0 1 1|1|rn	|0 0 0 0|rs	|0|typ|1|rm	|

# p368-373
CMP		Rn,imm12	|cond	|0 0|1|1 0 1 0|1|rn	|0 0 0 0|imm12			|
CMP		Rn,Rm,sh	|cond	|0 0|0|1 0 1 0|1|rn	|0 0 0 0|imm5	  |typ|0|rm	|
CMP		Rn,Rm,Rs 	|cond	|0 0|0|1 0 1 0|1|rn	|0 0 0 0|rs	|0|typ|1|rm	|

# p383-388
EOR		S,Rd,Rn,imm12	|cond	|0 0|1|0 0 0 1|s|rn	|rd	|imm12			|
EOR		S,Rd,Rn,Rm,sh	|cond	|0 0|0|0 0 0 1|s|rn	|rd	|imm5	  |typ|0|rm	|
EOR		S,Rd,Rn,Rm,Rs	|cond	|0 0|0|0 0 0 1|s|rn	|rd	|rs	|0|typ|1|rm	|

# p399-400
LDM		Rnw,wreglist	|cond	|1 0|0 0 1 0|w|1|rn	|reglist			|

# p401-402
LDMDA		Rnw,wreglist	|cond	|1 0|0 0 0 0|w|1|rn	|reglist			|

# p403-404
LDMDB		Rn,w,wreglist	|cond	|1 0|0 1 0 0|w|1|rn	|reglist			|

# p405-406
LDMIB		Rn,w,wreglist	|cond	|1 0|0 1 1 0|w|1|rn	|reglist			|

# p407-417
LDR		WRt,a_rn	|cond	|0 1 0|p|u|0|w|1|rn	|rt	|imm12			|
LDR		WRt,a_imm5	|cond	|0 1 1|p|u|0|w|1|rn	|rt	|imm5	  |typ|0|rm	|

# p417-424
LDRB		?		|1 1 1 1 1|0 0|0|0|0 0|1|rn	|rt	|1|p|u|w|imm8		|
LDRB		WRt,a_rn	|cond	|0 1 0|p|u|1|w|1|rn	|rt	|imm12			|
LDRB		WRt,a_imm5	|cond	|0 1 1|p|u|1|w|1|rn	|rt	|imm5	  |typ|0|rm	|

# p425-426
LDRBT		?		|cond	|0 1 1|0|u|1 1 1|rn	|rt	|imm5	  |typ|0|rm	|

# p427-432
LDRD		WRt,a_imm4	|cond	|0 0 0|p|u|1|w|0|rn	|rt	|imm4h	|1 1 0 1|imm4l	|
LDRD		?		|cond	|0 0 0|p|u|0|w|0|rn	|rt	|0 0 0 0|1 1 0 1|rm	|


# p433-434
LDREX		?		|cond	|0 0 0 1 1 0 0|1|rn	|rt	|1 1 1 1|1 0 0 1|1 1 1 1|

# p435-436
LDREXB		?		|cond	|0 0 0|1 1 1 0|1|rn	|rt	|1 1 1 1|1 0 0 1|1 1 1 1|

# p437-438
LDREXD		?		|cond	|0 0 0|1 1 0 1|1|rn	|rt	|1 1 1 1|1 0 0 1|1 1 1 1|

# p439-440
LDREXH		?		|cond	|0 0 0|1 1 1 1|1|rn	|rt	|1 1 1 1|1 0 0 1|1 1 1 1|

# p441-448
LDRH		WRt,a_imm4	|cond	|0 0 0|p|u|1|w|1|rn	|rt	|imm4h	|1 0 1 1|imm4l	|
LDRH		WRt,a_rnrm	|cond	|0 0 0|p|u|0|w|1|rn	|rt	|0 0 0 0|1 0 1 1|rm	|

# p449-450
LDRHT		?		|cond	|0 0 0|0|u|0|1|1|rn	|rt	|0 0 0 0|1 0 1 1|rm	|

# p451-456
LDRSB		WRt,a_imm4	|cond	|0 0 0|p|u|1|w|1|rn	|rt	|imm4h	|1 1 0 1|imm4l	|
LDRSB		WRt,a_rnrm	|cond	|0 0 0|p|u|0|w|1|rn	|rt	|0 0 0 0|1 1 0 1|rm	|

# p457-458
LDRSBT		?		|cond	|0 0 0|0|u|0|1|1|rn	|rt	|0 0 0 0|1 1 0 1|rm	|

# p459-464
LDRSH		WRt,a_imm4	|cond	|0 0 0|p|u|1|w|1|rn	|rt	|imm4h	|1 1 1 1|imm4l	|
LDRSH		?		|cond	|0 0 0|p|u|0|w|1|rn	|rt	|0 0 0 0|1 1 1 1|rm	|

# p465-466
LDRSHT		?		|cond	|0 0 0|0|u|0|1|1|rn	|rt	|0 0 0 0|1 1 1 1|rm	|

# p467-468
LDRT		WRt,a_rn	|cond	|0 1|0 0|u|0|1 1|rn	|rt	|imm12			|
LDRT		WRt,a_imm5	|cond	|0 1|1 0|u|0|1 1|rn	|rt	|imm5	  |typ|0|rm	|

# p469-472
LSL		S,Rd,Rm,imm5	|cond	|0 0|0|1 1 0 1|s|0 0 0 0|rd	|imm5	  |0 0 0|rm	|
LSL		S,Rd,Rn,Rm 	|cond	|0 0|0|1 1 0 1|s|0 0 0 0|rd	|rm	|0 0 0 1|rn	|

# p473-476
LSR		S,Rd,Rm,imm5	|cond	|0 0|0|1 1 0 1|s|0 0 0 0|rd	|imm5	  |0 1 0|rm	|
LSR		S,Rd,Rn,Rm 	|cond	|0 0|0|1 1 0 1|s|0 0 0 0|rd	|rm	|0 0 1 1|rn	|

# p477-478
MCR		COP		|cond	|1 1 1 0|opc1 |0|crn	|rt	|cop	|opc2 |1|crm	|
MCR2		COP		|1 1 1 1|1 1 1 0|opc1 |0|crn	|rt	|cop	|opc2 |1|crm	|

# p479-480
MCRR		?		|cond	|1 1 0 0 0 1 0 0|rt2	|rt	|cop	|opc1	|crm	|
MCRR2		?		|1 1 1 1|1 1 0 0 0 1 0 0|rt2	|rt	|cop	|opc1	|crm	|

# p481-482
MLA		S,Rd,Rn,Rm,Ra	|cond	|0 0 0 0 0 0 1|s|rd	|ra	|rm	|1 0 0 1|rn	|

# p483-484
MLS		?		|cond	|0 0 0 0 0 1 1 0|rd	|ra	|rm	|1 0 0 1|rn	|

# p485-491
MOV		S,Rd,imm12	|cond	|0 0|1|1 1 0 1|s|0 0 0 0|rd	|imm12			|
MOV		?		|cond	|0 0 1 1|0 0 0 0|imm4	|rd	|imm12			|
MOV		S,Rd,Rm		|cond	|0 0|0|1 1 0 1|s|0 0 0 0|rd	|0 0 0 0 0 0 0 0|rm	|
MOV		S,Rd,Rm,Rs 	|cond	|0 0|0|1 1 0 1|s|0 0 0 0|rd	|rs	|0|typ|1|rm	|
MOV		S,Rd,Rm,sh	|cond	|0 0|0|1 1 0 1|s|0 0 0 0|rd	|imm5	  |typ|0|rm	|

# p492
MOVT		?		|cond	|0 0 1 1|0 1 0 0|imm4	|rd	|imm12			|

# p493-494
MRC		COP		|cond	|1 1 1 0|opc1 |1|crn	|rt	|cop	|opc2 |1|crm	|
MRC2		COP		|1 1 1 1|1 1 1 0|opc1 |1|crn	|rt	|cop	|opc2 |1|crm	|

# p495-496
MRRC		?		|cond	|1 1 0 0|0 1 0|1|rt2	|rt	|cop	|opc1	|crm	|
MRRC2		?		|1 1 1 1|1 1 1 0|0 1 0|1|crn	|rt	|cop	|opc1	|crm	|

# p497-498
# MRS see below 1976

# p499-502
MSR		?		|cond	|0 0 1 1 0|0 1 0|msk|0 0|1 1 1 1|imm12			|
MSR		?		|cond	|0 0 0 1 0|0|1 0|msk|0 0|1 1 1 1|0 0 0 0 0 0 0 0|rn	|

# p503-504
MUL		Rd,Rn,Rm	|cond	|0 0 0 0 0 0 0|s|rd	|0 0 0 0|rm	|1 0 0 1|rn	|

# p505...510
MVN		?		|cond	|0 0|1|1 1 1 1|s|rn	|rd	|oper2			|
MVN		S,Rd,imm12	|cond	|0 0|1|1 1 1 1|s|0 0 0 0|rd	|imm12			|
MVN		S,Rd,Rm,Rs 	|cond	|0 0|0|1 1 1 1|s|0 0 0 0|rd	|rs	|0|typ|1|rm	|
MVN		S,Rd,Rm,sh	|cond	|0 0|0|1 1 1 1|s|0 0 0 0|rd	|imm5	  |typ|0|rm	|

# p511-512
NOP		-		|cond	|0 0 1 1 0 0 1 0|0 0 0 0|1 1 1 1|0 0 0 0|0 0 0 0 0 0 0 0|

# p519-522
ORR		S,Rd,Rn,imm12	|cond	|0 0|1|1 1 0 0|s|rn	|rd	|imm12			|
ORR		S,Rd,Rn,Rm,sh	|cond	|0 0|0|1 1 0 0|s|rn	|rd	|imm5     |typ|0|rm	|
ORR		S,Rd,Rn,Rm,Rs	|cond	|0 0|0|1 1 0 0|s|rn	|rd	|rs	|0|typ|1|rm	|

# p535-538
POP		wreglist	|cond	|1 0 0 0 1 0 1 1|1 1 0 1|reglist			|
POP		Rt		|cond	|0 1 0 0 1 0 0 1|1 1 0 1|rt	|0 0 0 0 0 0 0 0 0 0 0 0|

# p539-540
PUSH		reglist		|cond	|1 0 0 1 0 0 1 0|1 1 0 1|reglist			|
PUSH		Rt		|cond	|0 1 0 1 0 0 1 0|1 1 0 1|rt	|0 0 0 0 0 0 0 0 0 1 0 0|

# p541-542
QADD		?		|cond	|0 0 0 1 0 0 0 0|rn	|rd	|0 0 0 0|0 1 0 1|rm	|

# p543-544
QADD16		?		|cond	|0 1 1 0 0 0 1 0|rn	|rd	|1 1 1 1|0 0 0 1|rm	|

# p545-546
QADD8		?		|cond	|0 1 1 0 0 0 1 0|rn	|rd	|1 1 1 1|1 0 0 1|rm	|

# p547-548
QASX		?		|cond	|0 1 1 0 0 0 1 0|rn	|rd	|1 1 1 1|0 0 1 1|rm	|

# p573-574
RRX		S,Rd,Rm	|cond	|0 0|0|1 1 0 1|s|0 0 0 0|rd	|0 0 0 0 0|1 1 0|rm	|

# p575-580
RSB		S,Rd,Rn,imm12	|cond	|0 0|1|0 0 1 1|s|rn	|rd	|imm12			|
RSB		S,Rd,Rn,Rm,sh	|cond	|0 0|0|0 0 1 1|s|rn	|rd	|imm5	  |typ|0|rm	|
RSB		S,Rd,Rn,Rm,Rs	|cond	|0 0|0|0 0 1 1|s|rn	|rd	|rs	|0|typ|1|rm	|

# P581-587
RSC		S,Rd,Rn,imm12	|cond	|0 0|1|0 1 1 1|s|rn	|rd	|imm12			|
RSC		S,Rd,Rn,Rm,sh	|cond	|0 0|0|0 1 1 1|s|rn	|rd	|imm5	  |typ|0|rm	|
RSC		S,Rd,Rn,Rm,Rs	|cond	|0 0|0|0 1 1 1|s|rn	|rd	|rs	|0|typ|1|rm	|

# p593-598
SBC		S,Rd,Rn,imm12	|cond	|0 0|1|0 1 1 0|s|rn	|rd	|imm12			|
SBC		S,Rd,Rn,Rm,sh	|cond	|0 0|0|0 1 1 0|s|rn	|rd	|imm5	  |typ|0|rm	|
SBC		S,Rd,Rn,Rm,Rs	|cond	|0 0|0|0 1 1 0|s|rn	|rd	|rs	|0|typ|1|rm	|

# p599-600
SBFX		?		|cond	|0 1 1 1 1|0|1|w1	|rd	|lsb	  |1 0 1|rn	|

# p601-602
SDIV		Rd,Rn,Rm	|cond	|0 1 1 1 0 0 0 1|rd	|1 1 1 1|rm	|0 0 0|1|rn	|

# p603-604
SEL		Rd,Rn,Rm	|cond	|0 1 1 0 1 0 0 0|rn	|rd	|1 1 1 1|1 0 0 1|rm	|

# p605-606
SETEND		?		|1 1 1 1|0 0 0 1 0 0 0 0|0 0 0 1|0 0 0 0 0 0|e|0|0 0 0 0|0 0 0 0|

# p607-608
SEV		-		|cond	|0 0 1 1 0 0 1 0|0 0 0 0|1 1 1 1|0 0 0 0|0 0 0 0|0 1 0 0|

# p609-610
SHADD		Rd,Rn,Rm	|cond	|0 1 1 0 0 0 1 1|rn	|rd	|1 1 1 1|0 0 0 1|rm	|

# p611-612
SHADD8		Rd,Rn,Rm	|cond	|0 1 1 0 0 0 1 1|rn	|rd	|1 1 1 1|1 0 0 1|rm	|

# p613-614
SHASX		Rd,Rn,Rm	|cond	|0 1 1 0 0 0 1 1|rn	|rd	|1 1 1 1|0 0 1 1|rm	|

# p615-616
SHSAX		Rd,Rn,Rm	|cond	|0 1 1 0 0 0 1 1|rm	|rd	|1 1 1 1|0 1 0 1|rm	|

# p617-618
SHSUB16		Rd,Rn,Rm	|cond	|0 1 1 0 0 0 1 1|rn	|rd	|1 1 1 1|0 1 1 1|rm	|

# p619-620
SHSUB8		Rd,Rn,Rm	|cond	|0 1 1 0 0 0 1 1|rn	|rd	|1 1 1 1|1 1 1 1|rm	|

# p621-622
SMLA		Rd,Rn,Rm,Ra,?	|cond	|0 0 0 1 0 0 0 0|rd	|ra	|rm	|1|m|n|0|rn	|

# p623-624
SMLAD		Rd,Rn,Rm,Ra,?	|cond	|0 1 1 1 0 0 0 0|rd	|ra	|rm	|0|0|m|1|rn	|

# p625-626
SMLAL		Rdlo,Rdhi,Rn,Rm	|cond	|0 0 0 0 1 1 1|s|Rdhi	|rdlo	|rm	|1 0 0 1|rn	|

# p627-628
SMLAL		Rdlo,Rdhi,Rn,Rm,?	|cond	|0 0 0 1 0 1 0 0|rdhi	|rdlo	|rm	|1|m|n|0|rn	|

# p629-630
SMLALD		Rdlo,Rdhi,Rn,Rm,?	|cond	|0 1 1 1 0 1 0 0|rdhi	|rdlo	|rm	|0 0|m|1|rn	|

# p631-632
SMLAW		Rd,Rn,Rm,Ra,?	|cond	|0 0 0 1|0 0 1 0|rd	|ra	|rm	|1|m|0 0|rn	|

# p633-p634
SMLSD		Rd,Rn,Rm,Ra,?	|cond	|0 1 1 1|0 0 0 0|rd	|ra	|rm	|0 1|m|1|rn	|

# p635-636
SMLSLD		Rdlo,Rdhi,Rn,Rm,?	|cond	|0 1 1 1 0 1 0 0|rdhi	|rdlo	|rm	|0 1|m|1|rn	|

# p637-638
SMMLA		Rd,Rn,Rm,Ra,?	|cond	|0 1 1 1 0 1 0 1|rd	|ra	|rm	|0 0|r|1|rn	|


# p639-640
SMMLS		Rd,Rn,Rm,Ra,?	|cond	|0 1 1 1 0 1 0 1|rd	|ra	|rm	|1 1|r|1|rn	|

# p641-642
SMMUL		Rd,Rn,Rm	|cond	|0 1 1 1 0 1 0 1|rd	|1 1 1 1|rm	|0 0|r|1|rn	|

# p643-644
SMUAD		Rd,Rn,Rm,?	|cond	|0 1 1 1 0 0 0 0|rd	|1 1 1 1|rm	|0 0|m|1|rn	|

# p645-646
SMUL		Rd,Rn,Rm,?	|cond	|0 0 0 1 0 1 1 0|rd	|0 0 0 0|rm	|1|m|n|0|rn	|

# p647-648
SMULL		Rdlo,Rdhi,Rn,Rm	|cond	|0 0 0 0 1 1 0|s|rdhi	|rdlo	|rm	|1 0 0 1|rn	|


# p665-666
STM		Rnw,reglist	|cond	|1 0|0 0 1 0|w|0|rn	|reglist			|

# p667-668
STMDA		Rnw,reglist	|cond	|1 0|0 0 0 0|w|0|rn	|reglist			|

# p669-670
STMDB		Rnw,reglist	|cond	|1 0|0 1 0 0|w|0|rn	|reglist			|

# p671-672
STMIB		Rn,w,reglist	|cond	|1 0|0 1 1 0|w|0|rn	|reglist			|

# p673-678
STR		Rt,a_rn		|cond	|0 1 0|p|u|0|w|0|rn	|rt	|imm12			|
STR		Rt,a_imm5	|cond	|0 1 1|p|u|0|w|0|rn	|rt	|imm5	  |typ|0|rm	|

# p679-684
STRB		Rt,a_rn		|cond	|0 1 0|p|u|1|w|0|rn	|rt	|imm12			|
STRB		Rt,a_imm5	|cond	|0 1 1|p|u|1|w|0|rn	|rt	|imm5	  |typ|0|rm	|

# p685-686
STRBT		Rt,a_imm5	|cond	|0 1 1|0|u|1|1|0|rn	|rt	|imm5	  |typ|0|rm	|

# p687-690
STRD		Rt,a_imm4	|cond	|0 0 0|p|u|1|w|0|rn	|rt	|imm4h	|1 1 1 1|imm4l	|
STRD		?		|cond	|0 0 0|p|u|0|w|0|rn	|rt	|0 0 0 0|1 1 1 1|rm	|

# p691-692
STREX		?		|cond	|0 0 0 1 1 0 0|0|rn	|rd	|1 1 1 1|1 0 0 1|rt	|

# p693-694
STREXB		?		|cond	|0 0 0|1 1 1 0|0|rn	|rd	|1 1 1 1|1 0 0 1|rt	|

# p695-696
STREXD		?		|cond	|0 0 0|1 1 0 1|0|rn	|rd	|1 1 1 1|1 0 0 1|rt	|

# p697-698
STREXH		?		|cond	|0 0 0|1 1 1 1|0|rn	|rd 	|1 1 1 1|1 0 0 1|rt	|

# p699-704
STRH		?		|1 1 1 1 1|0 0|0|0|0 1|0|rn	|rt	|1|p|u|w|imm8		|
STRH		Rt,a_imm4	|cond	|0 0 0|p|u|1|w|0|rn	|rt	|imm4h	|1 0 1 1|imm4l	|
STRH		?		|cond	|0 0 0|p|u|0|w|0|rn	|rt	|0 0 0 0|1 0 1 1|rm	|

# A8-709...720
SUB		S,Rd,Rn,imm12	|cond	|0 0|1|0 0 1 0|s|rn	|rd	|imm12			|
SUB		S,Rd,Rn,Rm,sh	|cond	|0 0|0|0 0 1 0|s|rn	|rd	|imm5	  |typ|0|rm	|
SUB		S,Rd,Rn,Rm,Rs	|cond	|0 0|0|0 0 1 0|s|rn	|rd	|rs	|0|typ|1|rm	|
#SUB		?		|cond	|0 0|1|0 0 1 0|s|1 1 0 1|rd	|imm12			|
#SUB		?		|cond	|0 0|0|0 0 1 0|s|1 1 0 1|rd	|imm5	  |typ|0|rm	|

# p723-724
SWP		UN		|cond	|0 0 0 1 0|x|0 0|1 1 1 1|rt	|0 0 0 0|1 0 0 1|rt2	|
SWP		UN		|cond	|0 0 0 1 0|x|0 0|rn	|1 1 1 1|0 0 0 0|1 0 0 1|rt2	|
SWP		UN		|cond	|0 0 0 1 0|x|0 0|rn	|rt	|0 0 0 0|1 0 0 1|1 1 1 1|
SWP		Rt,Rt2,vrn	|cond	|0 0 0 1 0|0|0 0|rn	|rt	|0 0 0 0|1 0 0 1|rt2	|
SWPB		Rt,Rt2,vrn	|cond	|0 0 0 1 0|1|0 0|rn	|rt	|0 0 0 0|1 0 0 1|rt2	|

# p725-726
SXTAB		?		|cond	|0 1 1 0 1 0 1 0|rn	|rd	|rot|0 0|0 1 1 1|rm	|

# p739-744
TEQ		Rn,imm12	|cond	|0 0|1|1 0 0 1|1|rn	|0 0 0 0|imm12			|
TEQ		Rn,Rm,sh	|cond	|0 0|0|1 0 0 1|1|rn	|0 0 0 0|imm5	  |typ|0|rm	|
TEQ		Rn,Rm,Rs 	|cond	|0 0|0|1 0 0 1|1|rn	|0 0 0 0|rs	|0|typ|1|rm	|

# p745-750
TST		Rn,imm12	|cond	|0 0|1|1 0 0 0|1|rn	|0 0 0 0|imm12			|
TST		Rn,Rm,sh	|cond	|0 0|0|1 0 0 0|1|rn	|0 0 0 0|imm5	  |typ|0|rm	|
TST		Rn,Rm,Rs 	|cond	|0 0|0|1 0 0 0|1|rn	|0 0 0 0|rs	|0|typ|1|rm	|

# p751-752
UADD16		?		|cond	|0 1 1 0 0 1 0 1|rn	|rd	|1 1 1 1|0 0 0 1|rm	|

# p753-754
UADD8		>		|cond	|0 1 1 0 0 1 0 1|rn	|rd	|1 1 1 1|1 0 0 1|rm	|

# p779
UMULL		Rdlo,Rdhi,Rn,Rm	|cond	|0 0 0 0 1 0 0|s|rdhi	|rdlo	|rm	|1 0 0 1|rn	|

# p1966-1967
CPS		?		|1 1 1 1|0 0 0 1 0 0 0 0|imo|m|0|0 0 0 0|0 0 0 0|a|i|f|0|mode	|

# p1968
ERET_1968	?		|cond	|0 0 0 1 0 1 1 0|0 0 0 0|0 0 0 0|0 0 0 0|0 1 1 0|1 1 1 0|

# p1972
LDM	amode,Rnw,reglist3	|cond	|1 0|0|p|u|1|w|1|rn	|1|reglist			|

# p1970
HVC_1970	?		|cond	|0 0 0 1 0 1 0 0|imm12			|0 1 1 1|imm4	|

# p1974
LDM	amode,Rnw,reglist2	|cond	|1 0|0|p|u|1|w|1|rn	|0|reglist			|

# p497-498
# p1976-1977
MRS		Rd,SPSR		|cond	|0 0 0 1 0|1|0 0|1 1 1 1|rd	|0 0 0|0|0 0 0 0|0 0 0 0|
MRS		Rd,CPSR		|cond	|0 0 0 1 0|0|0 0|1 1 1 1|rd	|0 0 0 0 0 0 0 0 0 0 0 0|
MRS		UN		|cond	|0 0 0 1 0|r|0 0|1 1 1 1|1 1 1 1|0 0 0|0|0 0 0 0|0 0 0 0|

# p1978
MRS_1978	?		|cond	|0 0 0 1 0|r|0 0|m1	|rd	|0 0 1|m|0 0 0 0|0 0 0 0|

# p1980
MSR_1980	?		|cond	|0 0 0 1 0|r|1 0|m1	|1 1 1 1 0 0|1|m|0 0 0 0|rn	|

# p1982
MSR_1982	?		|cond	|0 0 1 1 0|r|1 0|mask   |1 1 1 1|imm12			|

# p1984
MSR		cpsr,Rn		|cond	|0 0 0 1 0|r|1 0|msk	|1 1 1 1|0 0 0 0 0 0 0 0|rn	|
MSR		UN		|cond	|0 0 0 1 0|r|1 0|msk	|1 1 1 1|0 0 0 0 0 0 0 0|1 1 1 1|
MSR		UN		|cond	|0 0 0 1 0|r|1 0|0 0 0 0|1 1 1 1|0 0 0 0 0 0 0 0|rn	|

# p1988
SMC_1988	?		|cond	|0 0 0 1 0 1 1|0|0 0 0 0 0 0 0 0 0 0 0 0|0 1 1 1|imm4	|

# p1994
STM	amode,Rnw,reglist2	|cond	|1 0|0|p|u|1|w|0|rn	|reglist			|


"""

OBJDUMP_COMPAT = arm_base.OBJDUMP_COMPAT
CC = arm_base.CC
REG = arm_base.REG

class Arm_ins(arm_base.Arm_Base_ins):

	def __init__(self, pj, lim, lang):
		super().__init__(pj, lim, lang)
		if self.lo & 3:
			raise assy.Invalid("Unaligned Instruction")


	def args_done(self, pj):
		if 'cond' in self.lim[-1].flds:
			cond = self['cond']
			self.mne += CC[cond]
			if self['cond'] != 14:
				self.add_flow('>', '?', self.hi)

	def assy_UN(self):
		raise assy.Invalid("UNPREDICTABLE")

	def assy_COP(self):
		return ([
			assy.Arg_verbatim("%d" % self['cop']),
			assy.Arg_verbatim("%d" % self['opc1']),
			self.assy_Rt(pj),
			assy.Arg_verbatim("CR%d" % self['crn']),
			assy.Arg_verbatim("CR%d" % self['crm']),
			assy.Arg_verbatim("{%d}" % self['opc2']),
		])

	def assy_amode(self):
		self.mne += {
			0: "DA",
			1: "",		# IA
			2: "DB",
			3: "IB",
		}[self['p'] * 2 + self['u']]
		

	def assy_cpsr(self):
		t = "CPSR_"
		if self['msk'] & 8:
			t += "f"
		if self['msk'] & 4:
			t += "s"
		if self['msk'] & 2:
			t += "x"
		if self['msk'] & 1:
			t += "c"
		return assy.Arg_verbatim(t)

	def imm12_rotate(self):
		v = self['imm12']
		if not (v & 0xf00):
			return v
		r = v >> 8
		b = v & 0xff
		b |= b << 32
		b = b >> (r * 2)
		return b & 0xffffffff

	def assy_adr_plus(self):
		v = self.imm12_rotate()
		return assy.Arg_dst(self.lang.m, self.hi + 4 + v, "")

	def assy_adr_minus(self):
		v = self.imm12_rotate()
		return assy.Arg_dst(self.lang.m, self.hi + 4 - v, "")
	
	def assy_S(self):
		if self['s']:
			self.mne += "S"

	def assy_C(self):
		return
		cond = self['cond']
		self.mne += CC[cond]
		if self['cond'] != 14:
			self.add_flow('>', '?', self.hi)

	def assy_dst(self):
		o = self['off'] << 2
		if o & (1<<25):
			o |= 0xfc000000
		self.dstadr = 4 + (self.hi + o) & 0xffffffff
		if self.mne.find("L") != -1:
			pj.m.set_block_comment(self.dstadr, "from %x" % self.lo)
		return assy.Arg_dst(self.lang.m, self.dstadr, "")

	def assy_imm5(self):
		return assy.Arg_verbatim("#0x%x" % self['imm5'])

	def assy_imm12(self):
		v = self['imm12']
		s = v >> 8
		v = v & 0xff
		# return "#0x%x,%d" % (v, s)
		v = v << (32 - 2 * s)
		v |= v >> 32
		v &= 0xffffffff
		return "#0x%x" % v

	def assy_vrn(self):
		return assy.Arg_verbatim("[%s]" % REG[self['rn']])

	def assy_a_rnrm(self):
		rn = REG[self['rn']]
		rm = REG[self['rm']]
		if not self['u']:
			rm = "-" + rm
		p = self.lim[-1].flds.get('p')
		w = self.lim[-1].flds.get('w')

		if not p:
			if not w:
				return "[%s]," % rn + rm
			raise assy.Invalid("a_imm4 mode wrong (!p,w)")

		if w:
			return "[%s," % rn + rm + "]!"

		return "[%s," % rn + rm + "]"


	def assy_a_imm4(self):
		imm32 = (self['imm4h'] << 4) | self['imm4l']
		if self['u']:
			imm = "#0x%x" % imm32
		else:
			imm = "#-0x%x" % imm32
		p = self.lim[-1].flds.get('p')
		w = self.lim[-1].flds.get('w')
		rn = REG[self['rn']]

		if not p:
			if not w:
				return "[%s]," % rn + imm
			raise assy.Invalid("a_imm4 mode wrong (!p,w)")

		if w:
			return "[%s," % rn + imm + "]!"

		if True or self['rn'] != 15 or OBJDUMP_COMPAT:
			if imm32:
				return "[%s," % rn + imm + "]"
			return "[%s]" % rn

		if self['u']:
			t = self.hi + 4 + imm32
		else:
			t = self.hi + 4 - imm32
		try:
			v = pj.m.lu32(t)
			data.Const(pj.m, t, t + 4, func=pj.m.lu32, size=4)
			self.lcmt += "[%s,%s] = [#0x%x]\n" % (rn, imm, t)
			return "#0x%x" % v
		except:
			self.lcmt += "[%s,%s]\n" % (rn, imm)
			return "[#0x%x]" % t

	def assy_a_imm5(self):
		''' Addressing mode Rn/U/P/W/imm5 '''
		shf = self.assy_sh(pj)
		if shf is None:
			shf = ""
		else:
			shf = "," + shf
		rn = REG[self['rn']]
		rm = REG[self['rm']]
		if not self['u']:
			rm = "-" + rm
		p = self.lim[-1].flds.get('p')
		w = self.lim[-1].flds.get('w')
		if p:
			if w:
				return "[%s,%s%s]!" % (rn, rm, shf)
			return "[%s,%s%s]" % (rn, rm, shf)
		else:
			if not w:
				return "[%s],%s%s" % (rn, rm, shf)
			raise assy.Invalid("a_imm5 mode wrong (!p,w)")

	def assy_a_rn(self):
		''' Addressing mode Rn/U/P/W '''
		imm32 = self['imm12']
		rn = REG[self['rn']]
		if self['u']:
			imm = "#0x%x" % imm32
		else:
			imm = "#-0x%x" % imm32

		p = self.lim[-1].flds.get('p')
		w = self.lim[-1].flds.get('w')

		if not p:
			if not w:
				#return [assy.Arg_verbatim("[%s]" % rn), assy.Arg_dst(self.lang.m, imm)]
				return "[%s]," % rn + imm
			raise assy.Invalid("a_rn mode wrong (!p,w)")

		if w:
			return "[%s," % rn + imm + "]!"

		if self['rn'] != 15 or OBJDUMP_COMPAT:
			if imm32:
				return "[%s," % rn + imm + "]"
			return "[%s]" % rn

		if self['u']:
			t = self.hi + 4 + imm32
		else:
			t = self.hi + 4 - imm32
		try:
			v = pj.m.lu32(t)
			data.Const(pj.m, t, t + 4, func=pj.m.lu32, size=4)
			self.lcmt += "[%s,%s] = [#0x%x]\n" % (rn, imm, t)
			return assy.Arg_dst(self.lang.m, v, pfx="#")
			return "#0x%x" % v
		except:
			self.lcmt += "[%s,%s]\n" % (rn, imm)
			return "[#0x%x]" % t

	def assy_w(self):
		if (self['w']):
			return assy.Arg_verbatim("!")
		
	def assy_Rs(self):
		typ = self['typ']
		rs = self['rs']
		return assy.Arg_verbatim("%s,%s" % (
			["lsl", "lsr", "asr", "ror"][typ], REG[rs]
		))
		
	def assy_Rnw(self):
		if self['w']:
			return REG[self['rn']] + "!"
		return REG[self['rn']]

	def assy_Ra(self):
		return REG[self['ra']]

	def assy_Rm(self):
		return REG[self['rm']]

	def assy_reglist2(self):
		return self.assy_reglist(pj) + "^"

	def assy_reglist3(self):
		return self.assy_reglist(pj)[:-1] + "," + REG[15] + "}^"


class Arm(assy.Instree_disass):
	def __init__(self):
		super().__init__(
			"arm",
			32,
			8,
			"<",
			abits=32,
		)
		self.add_ins(arm_desc, Arm_ins)
		self.verbatim.add("CPSR")
		self.verbatim.add("SPSR")

	def codeptr(self, pj, adr):
		t = pj.m.lu32(adr)
		c = data.Codeptr(pj.m, adr, adr + 4, t)
		self.disass(pj, t)
		return c

	def vector(self, pj, adr):
		return vector(pj, adr, self)

	def vectors(self, pj, adr=0x0, xops=1):
		return

if __name__ == "__main__":
	h = Arm()
	dom = {}

	def dl(l):
		t = ""
		for i in range(0, len(l), 2):
			t += " %08x" % l[i]
		t += "\n"
		for i in range(0, len(l), 2):
			t += " %08x" % l[i + 1]
		t += "\n"
		return t

	for a, aa in h.it:
		for b, bb in h.it:
			if aa == bb:
				continue
			i = 0
			while i < len(a) and i < len(b):
				if b[0] & a[0] != b[0]:
					i += 2
					continue
				if b[0] & a[1] != b[1]:
					i += 2
					continue
				if aa not in dom:
					dom[aa] = []
				dom[aa].append(bb)
				i += 2

	for a, b in dom.items():
		print("B", a)
		for i in b:
			print("  ", i)
		i = 0
		a.elide = set()
		while i < len(b):
			j = 0
			while j < len(b):
				if j != i and b[i] in dom and b[j] in dom[b[i]]:
					print(a)
					print(".",b[i])
					print("..", b[j])
					a.elide.add(b[j])
				j += 1
			i += 1
		print("A", a)
		print(a.elide)
		for i in b:
			print("  ", i)

	fo = open("/tmp/_.dot", "w")
	fo.write("digraph {\n")
	for a, b in dom.items():
		for i in b:
			if i not in a.elide:
				fo.write('"%s" -> "%s"\n' % ("_".join(i.assy), "_".join(a.assy)))
	
	fo.write("}\n")
