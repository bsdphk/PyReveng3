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

arm_desc = """

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
BLX		imm24,>C	|1 1 1 1|1 0 1|h|imm24						|
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
LDM		Rn,w,wreglist	|cond	|1 0|0 0 1 0|w|1|rn	|reglist			|

# p401-402
LDMDA		?		|cond	|1 0|0 0 0 0|a|1|rn	|r|oper				|

# p403-404
LDMDB		Rn,w,wreglist	|cond	|1 0|0 1 0 0|w|1|rn	|reglist			|

# p405-406
LDMIB		Rn,w,wreglist	|cond	|1 0|0 1 1 0|w|1|rn	|reglist			|

# p407-417
LDR		WRt,irn		|cond	|0 1 0|p|u|0|w|1|rn	|rt	|imm12			|
LDR		WRt,ipc		|cond	|0 1 0|p|u|0|w|1|1 1 1 1|rt	|imm12			|
LDR		?		|cond	|0 1 1|p|u|0|w|1|rn	|rt	|imm5	  |typ|0|rm	|

# p417-424
LDRB		?		|1 1 1 1 1|0 0|0|0|0 0|1|rn	|rt	|1|p|u|w|imm8		|
LDRB		WRt,irn		|cond	|0 1 0|p|u|1|w|1|rn	|rt	|imm12			|
LDRB		Wrt,ipc		|cond	|0 1 0|p|u|1|w|1|1 1 1 1|rt	|imm12			|
LDRB		WRt,Rn,Rm,sh	|cond	|0 1 1|p|u|1|w|1|rn	|rt	|imm5	  |typ|0|rm	|

# p425-426
LDRBT		?		|cond	|0 1 1|0|u|1 1 1|rn	|rt	|imm5	  |typ|0|rm	|

# p427-432
LDRD		?		|cond	|0 0 0|p|u|1|w|0|rn	|rt	|imm4h	|1 1 0 1|imm4l	|
LDRD		?		|cond	|0 0 0|1|u|1|0|0|1 1 1 1|rt	|imm4h	|1 1 0 1|imm4l	|
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
LDRH		?		|1 1 1 1 1|0 0|0|0|0 1|1|rn	|rt	|1|p|u|w|imm8		|
LDRH		?		|cond	|0 0 0|p|u|1|w|1|rn	|rt	|imm4h	|1 0 1 1|imm4l	|
LDRH		?		|cond	|0 0 0|p|u|1|w|1|1 1 1 1|rt	|imm4h	|1 0 1 1|imm4l	|
LDRH		?		|cond	|0 0 0|p|u|0|w|1|rn	|rt	|0 0 0 0|1 0 1 1|rm	|

# p449-450
LDRHT		?		|cond	|0 0 0|0|u|0|1|1|rn	|rt	|0 0 0 0|1 0 1 1|rm	|

# p451-456
LDRSB		?		|cond	|0 0 0|p|u|1|w|1|rn	|rt	|imm4h	|1 1 0 1|imm4l	|
LDRSB		?		|cond	|0 0 0|p|u|1|w|1|1 1 1 1|rt	|imm4h	|1 1 0 1|imm4l	|
LDRSB		?		|cond	|0 0 0|p|u|0|w|1|rn	|rt	|0 0 0 0|1 1 0 1|rm	|

# p457-458
LDRSBT		?		|cond	|0 0 0|0|u|0|1|1|rn	|rt	|0 0 0 0|1 1 0 1|rm	|

# p459-464
LDRSH		?		|cond	|0 0 0|p|u|1|w|1|rn	|rt	|imm4h	|1 1 1 1|imm4l	|
LDRSH		?		|cond	|0 0 0|p|u|1|w|1|1 1 1 1|rt	|imm4h	|1 1 1 1|imm4l	|
LDRSH		?		|cond	|0 0 0|p|u|0|w|1|rn	|rt	|0 0 0 0|1 1 1 1|rm	|

# p465-466
LDRSHT		?		|cond	|0 0 0|0|u|0|1|1|rn	|rt	|0 0 0 0|1 1 1 1|rm	|

# p467-468
LDRT		?		|cond	|0 1|0 0|u|0|1 1|rn	|rt	|imm12			|

# p469-472
LSL		S,Rd,Rm,imm5	|cond	|0 0|0|1 1 0 1|s|0 0 0 0|rd	|imm5	  |0 0 0|rm	|
LSL		S,Rd,Rn,Rm 	|cond	|0 0|0|1 1 0 1|s|0 0 0 0|rd	|rm	|0 0 0 1|rn	|

# p473-476
LSR		S,Rd,Rm,imm5	|cond	|0 0|0|1 1 0 1|s|0 0 0 0|rd	|imm5	  |0 1 0|rm	|
LSR		S,Rd,Rn,Rm 	|cond	|0 0|0|1 1 0 1|s|0 0 0 0|rd	|rm	|0 0 1 1|rn	|

# p477-478
MCR		?		|cond	|1 1 1 0|opc1 |0|crn	|rt	|cop	|opc2 |1|crm	|
MCR2		?		|1 1 1 1|1 1 1 0|opc1 |0|crn	|rt	|cop	|opc2 |1|crm	|

# p479-480
MCRR		?		|cond	|1 1 0 0 0 1 0 0|rt2	|rt	|cop	|opc1	|crm	|
MCRR2		?		|1 1 1 1|1 1 0 0 0 1 0 0|rt2	|rt	|cop	|opc1	|crm	|

# p481-482
MLA		?		|cond	|0 0 0 0 0 0 1|s|rd	|ra	|rm	|1 0 0 1|rn	|

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
MMR		?		|cond	|1 1 1 0|opc1 |1|crn	|rt	|cop	|opc2 |1|crm	|
MMR2		?		|1 1 1 1|1 1 1 0|opc1 |1|crn	|rt	|cop	|opc2 |1|crm	|

# p495-496
MMRC		?		|cond	|1 1 0 0|0 1 0|1|rt2	|rt	|cop	|opc1	|crm	|
MMRC2		?		|1 1 1 1|1 1 1 0|0 1 0|1|crn	|rt	|cop	|opc1	|crm	|

# p497-498
# MRS see below 1976

# p499-502
MSR		?		|cond	|0 0 1 1 0|0 1 0|msk|0 0|1 1 1 1|imm12			|
MSR		?		|cond	|0 0 0 1 0|0|1 0|msk|0 0|1 1 1 1|0 0 0 0 0 0 0 0|rn	|

# p503-504
MUL		?		|cond	|0 0 0 0 0 0 0|s|rd	|0 0 0 0|rm	|1 0 0 1|rn	|

# p505...510
MVN		?		|cond	|0 0|i|1 1 1 1|s|rn	|rd	|oper2			|
MVN		S,Rd,imm12	|cond	|0 0|1|1 1 1 1|s|0 0 0 0|rd	|imm12			|
MVN		S,Rd,Rm,sh	|cond	|0 0|0|1 1 1 1|s|0 0 0 0|rd	|imm5	  |typ|0|rm	|
MVN		S,Rd,Rm,Rs 	|cond	|0 0|0|1 1 1 1|s|0 0 0 0|rd	|rs	|0|typ|1|rm	|

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

# p641-642
SMMUL		?		|cond	|0 1 1 1 0 1 0 1|rd	|1 1 1 1|rm	|0 0|r|1|rn	|

# p647-648
SMULL		?		|cond	|0 0 0 0 1 1 0|s|rdhi	|rdlo	|rm	|1 0 0 1|rn	|

# p665-666
STM		Rn,w,reglist	|cond	|1 0|0 0 1 0|w|0|rn	|reglist			|

# p667-668
STMDA		?		|cond	|1 0|0 0 0 0|a|0|rn	|r|oper				|

# p669-670
STMDB		?		|cond	|1 0|0 1 0 0|w|0|rn	|r|oper				|

# p671-672
STMIB		Rn,w,reglist	|cond	|1 0|0 1 1 0|w|0|rn	|reglist			|

# p673-678
STR		Rt,irn		|cond	|0 1 0|p|u|0|w|0|rn	|rt	|imm12			|
STR		?		|cond	|0 1 1|p|u|0|w|0|rn	|rt	|imm5	  |typ|0|rm	|

# p679-684
STRB		?		|1 1 1 1 1|0 0|0|0|0 0|0|rn	|rt	|1|p|u|w|imm8		|
STRB		?		|cond	|0 1 0|p|u|1|w|0|rn	|rt	|imm12			|
STRB		?		|cond	|0 1 1|p|u|1|w|0|rn	|rt	|imm5	  |typ|0|rm	|

# p685-686
STRBT		?		|cond	|0 1 1|0|u|1|1|0|rn	|rt	|imm5	  |typ|0|rm	|

# p687-690
STRD		?		|cond	|0 0 0|p|u|1|w|0|rn	|rt	|imm4h	|1 1 1 1|imm4l	|
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
STRH		?		|cond	|0 0 0|p|u|1|w|0|rn	|rt	|imm4h	|1 0 1 1|imm4l	|
STRH		?		|cond	|0 0 0|p|u|0|w|0|rn	|rt	|0 0 0 0|1 0 1 1|rm	|

# A8-709...720
SUB		S,Rd,Rn,imm12	|cond	|0 0|1|0 0 1 0|s|rn	|rd	|imm12			|
SUB		S,Rd,Rn,Rm,sh	|cond	|0 0|0|0 0 1 0|s|rn	|rd	|imm5	  |typ|0|rm	|
SUB		S,Rd,Rn,Rm,Rs	|cond	|0 0|0|0 0 1 0|s|rn	|rd	|rs	|0|typ|1|rm	|
SUB		?		|cond	|0 0|1|0 0 1 0|s|1 1 0 1|rd	|imm12			|
SUB		?		|cond	|0 0|0|0 0 1 0|s|1 1 0 1|rd	|imm5	  |typ|0|rm	|

# p723-724
SWP		?		|cond	|0 0 0 1 0|0|0 0|rn	|rt	|0 0 0 0|1 0 0 1|rt2	|
SWPB		?		|cond	|0 0 0 1 0|1|0 0|rn	|rt	|0 0 0 0|1 0 0 1|rt2	|

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
UMULL		?		|cond	|0 0 0 0 1 0 0|s|rdhi	|rdlo	|rm	|1 0 0 1|rn	|

# p1966-1967
CPS		?		|1 1 1 1|0 0 0 1 0 0 0 0|imo|m|0|0 0 0 0|0 0 0 0|a|i|f|0|mode	|

# p1968
ERET_1968	?		|cond	|0 0 0 1 0 1 1 0|0 0 0 0|0 0 0 0|0 0 0 0|0 1 1 0|1 1 1 0|

# p1972
LDM		?		|cond	|1 0|0|a|b|1|c|1|rn	|1|oper				|

# p1970
HVC_1970	?		|cond	|0 0 0 1 0 1 0 0|imm12			|0 1 1 1|imm4	|

# p1974
LDM		?		|cond	|1 0|0|a|b|1|c|1|rn	|0|oper				|

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
STM		?		|cond	|1 0|0|a|b|1|c|0|rn	|r|oper				|


"""

CC = [ "EQ", "NE", "CS", "LO", "MI", "PL", "VS", "VC", "HI", "LS", "GE", "LT", "GT", "LE", "", "NV" ]

class Arm_ins(assy.Instree_ins):

	def __init__(self, pj, lim, lang):
		super().__init__(pj, lim, lang)
		if self.lo & 3:
			raise assy.Invalid("Unaligned Instruction")
		if 'cond' in self.lim[-1].flds:
			cond = self['cond']
			self.mne += CC[cond]
			if self['cond'] != 14:
				self.add_flow(pj, '>', '?', self.hi)

	def assy_UN(self, pj):
		raise assy.Invalid("UNPREDICTABLE")

	def assy_cpsr(self, pj):
		t = "CPSR_"
		if self['msk'] & 8:
			t += "f"
		if self['msk'] & 4:
			t += "s"
		if self['msk'] & 2:
			t += "x"
		if self['msk'] & 1:
			t += "c"
		return assy.Arg_verbatim(pj, t)

	def imm12_rotate(self):
		v = self['imm12']
		if not (v & 0xf00):
			return v
		r = v >> 8
		b = v & 0xff
		b |= b << 32
		b = b >> (r * 2)
		return b & 0xffffffff

	def assy_adr_plus(self, pj):
		v = self.imm12_rotate()
		return assy.Arg_dst(pj, self.hi + 4 + v, "#")

	def assy_adr_minus(self, pj):
		v = self.imm12_rotate()
		return assy.Arg_dst(pj, self.hi + 4 - v, "#")
	
	def assy_S(self, pj):
		if self['s']:
			self.mne += "S"

	def assy_C(self, pj):
		return
		cond = self['cond']
		self.mne += CC[cond]
		if self['cond'] != 14:
			self.add_flow(pj, '>', '?', self.hi)

	def assy_dst(self, pj):
		o = self['off'] << 2
		if o & (1<<25):
			o |= 0xfc000000
		self.dstadr = 4 + (self.hi + o) & 0xffffffff
		pj.m.set_block_comment(self.dstadr, "from %x" % self.lo)
		return assy.Arg_dst(pj, self.dstadr, "#")

	def assy_sh(self, pj):
		typ = self['typ']
		imm5 = self['imm5']
		if typ == 0:
			if not imm5:
				return
			return assy.Arg_verbatim(pj, "lsl#%d" % imm5)
		if typ == 1:
			if not imm5:
				imm5 = 32
			return assy.Arg_verbatim(pj, "lsr#%d" % imm5)
		if typ == 2:
			if not imm5:
				imm5 = 32
			return assy.Arg_verbatim(pj, "asr#%d" % imm5)
		if not imm5:
			return assy.Arg_verbatim(pj, "rrx#1")
		return assy.Arg_verbatim(pj, "ror#%d" % imm5)

	def assy_imm5(self, pj):
		return assy.Arg_verbatim(pj, "#0x%x" % self['imm5'])

	def assy_imm12(self, pj):
		v = self['imm12']
		s = v >> 8
		v = v & 0xff
		v = v << (32 - 2 * s)
		v |= v >> 32
		v &= 0xffffffff
		return assy.Arg_verbatim(pj, "#0x%x" % v)

	def assy_irn(self, pj):
		imm32 = self['imm12']
		rn = "R%d" % self['rn']
		if self['w'] or not self['p']:
			wb="XXX_WRITEBACK"
		else:
			wb=""
		if not imm32 or not self['p']:
			return assy.Arg_verbatim(pj, "[%s]" % rn + wb)
		if self['u']:
			return assy.Arg_verbatim(pj, "[%s+#0x%x]" % (rn, imm32) + wb)
		else:
			return assy.Arg_verbatim(pj, "[%s-#0x%x]" % (rn, imm32) + wb)
		
	def assy_ipc(self, pj):
		v = self['imm12']
		if self['u']:
			t = self.hi + 4 + v
		else:
			t = self.hi + 4 - v
		data.Const(pj, t, t + 4, func=pj.m.lu32, size=4)
		return assy.Arg_verbatim(pj, "[#0x%x]" % t)
		

	def assy_w(self, pj):
		if (self['w']):
			return assy.Arg_verbatim(pj, "!")
		
	def assy_Rd(self, pj):
		if self['rd'] == 15:
			self.flow_R(pj)
		return assy.Arg_verbatim(pj, "R%d" % self['rd'])

	def assy_WRt(self, pj):
		if self['rt'] == 15:
			self.flow_J(pj)
		return assy.Arg_verbatim(pj, "R%d" % self['rt'])

	def assy_Rs(self, pj):
		typ = self['typ']
		rs = self['rs']
		return assy.Arg_verbatim(pj, "%s R%d" % (
			["lsl", "lsr", "asr", "ror"][typ], rs
		))
		

	def assy_Rt(self, pj):
		return assy.Arg_verbatim(pj, "R%d" % self['rt'])

	def assy_Rn(self, pj):
		return assy.Arg_verbatim(pj, "R%d" % self['rn'])

	def assy_Rm(self, pj):
		return assy.Arg_verbatim(pj, "R%d" % self['rm'])

	def assy_reglist(self, pj):
		r = self['reglist']
		l = []
		i = 0
		while r:
			if r & 1:
				l.append("R%d" % i)
			r = r >> 1
			i += 1
		return assy.Arg_verbatim(pj, "(" + ",".join(l) + ")")

	def assy_wreglist(self, pj):
		r = self['reglist']
		if r & 0x8000:
			self.flow_R(pj)
		return self.assy_reglist(pj)

class Arm(assy.Instree_disass):
	def __init__(self):
		super().__init__("arm", 32, 8, "<")
		self.add_ins(arm_desc, Arm_ins)
		self.verbatim.add("CPSR")
		self.verbatim.add("SPSR")

	def codeptr(self, pj, adr):
		t = pj.m.lu32(adr)
		c = data.Codeptr(pj, adr, adr + 4, t)
		pj.todo(t, self.disass)
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
