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
Disassembler for ARM processors, Thumb1 instruction set
"""

from pyreveng import assy, data
from pyreveng.cpu.arm import arm_base

thumb_desc = '''
#		|       |       |       |       |       |       |       |       |
#		|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|

xxx221	-	|opcode     |operand		|
xxx222	-	|0 0|opcode |operand		|
xxx223	-	|0 1 0 0 0 0|opcode |x		|
xxx224	-	|0 1 0 0 0 1|opcode |x		|
xxx225	-	|0 1 0 1|opb	|operand	|
xxx225	-	|0 1 1|x|opb	|operand	|
xxx225	-	|1 0 0|x|opb	|operand	|
xxx226	-	|1 0 1 1|opcode       |operand	|
#xxx227a	-	|1 0 1 1|1 1 1 1|opa	|opb	|
#xxx227b	-	|1 1 0 1|opcode	|operand	|
xxx228	-	|1 1 1|op1|op2		|operand|o|operand2			|
xxx229	-	|1 1 1 1 0|x|0|y      |s|rn	|0|z 	|rd	|operand	|
xxx232	-	|1 1 1 1 0|x|1|op	|rn	|0|operand2			|
xxx233	-	|1 1 1 1 0|op		|rn	|1|op1	|ope	|imm8		|
xxx234	-	|1 1 1 1 0|0 1 1 1 0 1 0|op	|1 0|x|0|y|op1	|op2		|
xxx235a	-	|1 1 1 1 0|0 1 1 1 0 1 1|op	|1 0|x|0|op1	|op2	|op3	|
xxx235b	-	|1 1 1 0 1 0 0|op |0|w|l|rn	|op				|
xxx236	-	|1 1 1 0 1 0 0|op1|1|op2|rn	|op4		|op3	|op5	|
xxx237 	-	|1 1 1 1 1 0 0|op1|1 0 1|rn	|op3		|op2	|op4	|
xxx238	-	|1 1 1 1 1 0 0|op1|0 1 1|rn	|rt	|op2	    |op3	|
xxx239	-	|1 1 1 1 1 0 0|op1|0 0 1|rn	|rt	|op2	    |op3	|
xxx240	-	|1 1 1 1 1 0 0 0|op1  |0|x	|y	|op2	    |z		|
xxx241a	-	|1 1 1 0 1 0 1|op     |s|rn	|x	|rd	|y		|
xxx241b	-	|1 1 1 0 1 0 1 0 0 1 0|x|1 1 1 1|y|imm3	|z	|i2 |typ|w	|
xxx243a	-	|1 1 1 1 1 0 1 0|op1	|rn	|1 1 1 1|x	|op2	|y	|
xxx243b	-	|1 1 1 1 1 0 1 0 1|op1	|x	|1 1 1 1|y	|0 0|op2|z	|
xxx244	-	|1 1 1 1 1 0 1 0 1|op1	|x	|1 1 1 1|y	|0 1|op2|z	|
xxx246	-	|1 1 1 1 1 0 1 0 1 0|op1|x	|1 1 1 1|y	|1 0|op2|z	|
xxx247	-	|1 1 1 1 1 0 1 1 0|op1	|x	|ra	|y	|0 0|op2|z	|
xxx248	-	|1 1 1 1 1 0 1 1 1|op1	|x	|y		|op2	|z	|
xxx249	-	|1 1 1|x|1 1|op1	|rn	|y	|cop	|z    |o|w	|
'''

thumb_t1_desc = '''
#				|       |       |       |       |       |       |       |       |
#				|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|
# 298
ADC	Rd,Rn,imm8		|1 1 1 1 0|i|0 1 0 1 0|s|rn	|0|imm3	|rd	|imm8		|
# 300
ADC	Rdn,Rm			|0 1 0 0 0 0|0 1 0 1|rm   |rdn	|
# 304
ADD	Rd,Rn,imm3		|0 0 0 1 1 1 0|imm3 |rn	  |rd	|
# 308
ADD	Rd,Rn,Rm		|0 0 0 1 1 0 0|rm   |rn   |rd	|
# 314
ADD	Rd,SP,imm8		|1 0 1 0 1|rd 	|imm8		|
# 316
ADD	Rdm,SP,Rdm		|0 1 0 0 0 1 0 0|d|1 1 0 1|rdm	|
# 320
ADR	Rd,dst			|1 0 1 0 0|rd	|imm8		|
# 322
AND	Rd,Rn,imm		|1 1 1 1 0|i|0 0 0 0 0|s|rn	|0|imm3	|rd	|imm8		|
# 324
AND	Rdn,Rm			|0 1 0 0 0 0 0 0 0 0|rm   |rdn	|
# 328
ASR	Rd,Rm,imm5		|0 0 0 1 0|imm5	    |rm   |rd	|
# 330
ASR	Rdn,Rm			|0 1 0 0 0 0 0 1 0 0|rm	  |rdn  |
# 332
B	dst,>J			|1 1 0 1|cc	|imm8		|
# 334
BFC	Rd,Lsb,Wid		|1 1 1 1 0 0 1 1 0 1 1 0 1 1 1 1|0|imm3	|rd	|im2|0|msb	|
# 336
BFI	Rd,Rn,Lsb,Wid		|1 1 1 1 0 0 1 1 0 1 1 0|rn	|0|imm3	|rd	|im2|0|msb	|
# 338
BIC	Rd,Rn.imm		|1 1 1 1 0|i|0 0 0 0 1|s|rn	|0|imm3	|rd	|imm8		|
# 340
BIC	Rdn,Rm			|0 1 0 0 0 0 1 1 1 0|rm   |rdn	|
# 344
BKPT	imm8,>C			|1 0 1 1 1 1 1 0|imm8		|
#346
BL	dst,>C			|1 1 1 1 0|s|imm10		|1 1|j|1|k|imm11		|
# 348
BLX	Rm,>C			|0 1 0 0 0 1 1 1 1|rm     |0 0 0|
# 350
BX	Rm,>J			|0 1 0 0 0 1 1 1 0|rm	  |0 0 0|
# 352
BXJ	Rm,>J			|1 1 1 1 0 0 1 1 1 1 0 0|rm	|1 0 0 0 1 1 1 1 0 0 0 0 0 0 0 0|
# 354
CBnZ	Rn,dst			|1 0 1 1|o|0|i|1|imm5	  |rn	|
# 356
CDP	Cop,Op1,Crd,Crn,Crm,Op2	|1 1 1 0|1 1 1 0|opc1	|crn	|crd	|cop	|opc2 |0|crm	|
# 358
CLREX	-			|1 1 1 1 0 0 1 1 1 0 1 1 1 1 1 1|1 0 0 0 1 1 1 1 0 0 1 0 1 1 1 1|
# 360
CLZ	Rd,Rm			|1 1 1 1 1 0 1 0 1 0 1 1|rm	|1 1 1 1|rd	|1 0 0 0|rm	|
# 362
CMN	Rn,const		|1 1 1 1 0|i|0 1 0 0 0 1|rn	|0|imm3	|1 1 1 1|imm8		|
# 364
CMN	Rn,Rm			|0 1 0 0 0 0 1 0 1 1|rm	  |rn	|
# 368
CMP	Rn,imm8			|0 0 1 0 1|rm	|imm8		|
# 370
CMP	Rn,Rm			|0 1 0 0 0 0|1 0 1 0|rm   |rn	|
# 376
CSDB	-			|1 1 1 1 0 0 1 1 1 0 1 0 1 1 1 1|1 0 0 0 0 0 0 0 0 0 0 1 0 1 0 0|
# 378
DBG	Opt			|1 1 1 1 0 0 1 1 1 0 1 0 1 1 1 1|1 0 0 0 0 0 0 0 1 1 1 1|opt	|
# 379
DMB	Opt			|1 1 1 1 0 0 1 1 1 0 1 1 1 1 1 1|1 0 0 0 1 1 1 1 0 1 0 1|opt	|
# 381
DSB	Opt			|1 1 1 1 0 0 1 1 1 0 1 1 1 1 1 1|1 0 0 0 1 1 1 1 0 1 0 0|opt	|
# 383
EOR	Rd,Rn,imm		|1 1 1 1 0|i|0 0 1 0 0|s|rn	|0|imm3	|rd	|imm8		|
# 385
EORS	Rdn,Rm			|0 1 0 0 0 0 0 0 0 1|rm   |rdn	|
# 390
ISB	Opt			|1 1 1 1 0 0 1 1 1 0 1 1 1 1 1 1|1 0 0 0 1 1 1 1 0 1 1 0|opt	|
# 391
IT	Cond,Mask		|1 0 1 1 1 1 1 1|fcond	|mask	|
# 393
LDC	Cop,Crd,Dst		|cc	|1 1 0|p|u|d|w|1|rn	|crd	|cop	|imm8		|
# 395
LDC	Cop,Crd,Dst		|cc	|1 1 0|p|u|d|w|1 1 1 1 1|crd	|cop	|imm8		|
# 397
LDM	Rn,Reglist		|1 1 0 0 1|rn	|reglist	|
# 403
LDMD	Rn,Reglist		|1 1 1 0 1 0 0 1 0 0|w|rn	|p|m|0|reglist			|
# 407
LDR	Rt,Rn,Imm		|0 1 1 0 1|imm5	    |rn   |rt	|
# 411
LDR	Rt,Dst			|0 1 0 0 1|rt	|imm8		|
# 413
LDR	Rt,Rn,Rm		|0 1 0 1 1 0 0|rm   |rn   |rt	|
# 417
LDRB	Rt,Rn,Imm		|0 1 1 1 1|imm5	    |rn	  |rt	|
# 421
LDRB	Rt,Dst			|1 1 1 1 1 0 0 0|u|0 0 1 1 1 1 1|rt	|imm12			|
# 423
LDRB	Rt,Rn,Rm		|0 1 0 1 1 1 0|rm   |rm   |rt	|
# 425
LDRBT	Rt,Rn,Imm		|1 1 1 1 1 0 0 0 0 0 0 1|rn	|rt	|1 1 1 0|imm8		|
# 427
LDRD	Rt,Rt2,Rn,Imm		|1 1 1 0 1 0 0|p|u|1|w|1|rn	|rt	|rt2	|imm8		|
# 429
LDRD	Rt,Rt2,Dst		|1 1 1 0 1 0 0|p|u|1|w|1 1 1 1 1|rt	|rt2	|imm8		|
# 433
LDREX	Rt,Rn,Imm		|1 1 1 0 1 0 0 0 0 1 0 1|rn	|rt	|1 1 1 1|imm8		|
# 435
LDREXB	Rt,Rn			|1 1 1 0 1 0 0 0 1 1 0 1|rn	|rt	|1 1 1 1|0 1 0 0 1 1 1 1|
# 437
LDREXD	Rt,Rt2,Rn		|1 1 1 0 1 0 0 0 1 1 0 1|rn	|rt	|rt2	|0 1 1 1 1 1 1 1|
# 439
LDREXH	Rt,Rn			|1 1 1 0 1 0 0 0 1 1 0 1|rn	|rt	|1 1 1 1|0 1 0 1 1 1 1 1|
# 441
LDRH	Rt,Rn,Imm		|1 0 0 0 1|imm5     |rn   |rt	|
# 445
LDRH	Rt,Dst			|1 1 1 1 1 0 0 0|u|0 1 1 1 1 1 1|rt	|imm12			|
# 447
LDRH	Rt,Rn,Rm		|0 1 0 1 1 0 1|rm   |rn   |rt	|
# 449
LDRHT	Rt,Rn,Imm		|1 1 1 1 1 0 0 0 0 0 1 1|rn	|rt	|1 1 1 0|imm8		|
# 451
LDRSB	Rt,Rn,Imm12		|1 1 1 1 1 0 0 1 1 0 0 1|rn	|rt	|imm12			|
# 453
LDRSB	Rt,Dst			|1 1 1 1 1 0 0 1|u|0 0 1 1 1 1 1|rt	|imm12			|
# 455
LDRSB	Rt,Rn,Rm		|0 1 0 1 0 1 1|rm   |rn   |rt	|
# 457
LDRSBT	Rt,Rn,Imm8		|1 1 1 1 1 0 0 1 0 0 0 1|rn	|rt	|1 1 1 0|imm8		|
# 459
LDRSH	Rt,Rn,Imm12		|1 1 1 1 1 0 0 1 1 0 1 1|rn	|rt	|imm12			|
# 461
LDRSH	Rt,Dst			|1 1 1 1 1 0 0 1|u|0 1 1 1 1 1 1|rt	|imm12			|
# 463
LDRSH	Rt,Rn,Rm		|0 1 0 1 1 1 1|rm   |rn   |rt	|
# 465
LDRSHT	Rt,Rn,Imm8		|1 1 1 1 1 0 0 1 0 0 1 1|rn	|rt	|1 1 1 0|imm8		|
# 467
LDRT	Rt,Rn,Imm8		|1 1 1 1 1|0 0 0 0 1 0 1|rn	|rt	|1 1 1 0|imm8		|
# 469
LSL	Rd,Rm,Imm5		|0 0 0 0 0|imm5	    |rm   |rd	|
# 471
LSL	Rdn,Rm			|0 1 0 0 0 0 0 0 1 0|rm   |rdn	|
# 473
LSRS	Rd,Rm,Imm5		|0 0 0 0 1|imm5	    |rm   |rd	|
# 475
LSR	Rdn,Rm			|0 1 0 0 0 0 0 0 1 1|rm	  |rdn	|
# 477
MCR	Cop,Op1,Rt,Crn,Crm,Op2	|cond	|1 1 1 0|op1|0	|crn	|rt	|cop	|op2  |1|crm	|
# 479
MCRR	Cop,Op1,Rt,Rt2,Crm	|cond	|1 1 0 0 0 1 0 0|rt2	|rt	|cop	|op1	|crm	|
# 481
MLA	Rd,Rn,Rm,Ra		|1 1 1 1 1 0 1 1 0 0 0 0|rn	|ra	|rd	|0 0 0 0|rm	|
# 483
MLS	Rd,Rn,Rm,Ra		|1 1 1 1 1 0 1 1 0 0 0 0|rn	|ra	|rd	|0 0 0 1|rm	|
# 485
MOV	Rd,Imm8			|0 0 1 0 0|rd	|imm8		|
# 487
MOV	Rd,Rm			|0 1 0 0 0 1 1 0|d|rm	  |rd	|
# 492
MOVT	Rd,Imm16		|1 1 1 1 0|i|1 0 1 1 0 0|imm4	|0|imm3	|rd	|imm8		|
# 493
MRC	Cop,Op1,Rt,Crn,Crm,op2	|cond	|1 1 1 0|op1  |1|crn	|rt	|cop	|op2  |1|crm	|
# 495
MRCC	Cop,Op1,Rt,Rt2,Crm	|cond	|1 1 0 0 0 1 0 1|rt2	|rt	|cop	|op1	|crm	|
# 497
MRS	Rd,Spec			|1 1 1 1 0 1 1 1 1 1 0 1 1 1 1 1|1 0 0 0|rd	|0 0 0 0 0 0 0 0|
# 501
MSR	Spec,Rn			|1 1 1 1 0 0 1 1 1 0 0 0|rn	|1 0 0 0|msk|0 0|0 0 0 0 0 0 0 0|
# 503
MUL	Rdm,Rn,Rdm		|0 1 0 0 0 0 1 1 0 1|rn   |rdm	|
# 505
MVN	Rd,Imm			|1 1 1 1 0|i|0 0 0 1 1|s|1 1 1 1|0|imm3	|rd	|imm8		|
# 507
MVN	Rd,Rm			|0 1 0 0 0 0 1 1 1 1|rm   |rd	|
# 511
NOP	-			|1 0 1 1 1 1 1 1 0 0 0 0 0 0 0 0|
# 513
ORN	Rd,Rn,Const		|1 1 1 1 0|i|0 0 0 1 1|s|rn	|0|imm3	|rd	|imm8		|
# 515
ORN	Rd,Rn,Rm,Shift		|1 1 1 0 1|0 1 0 0 1 1|s|rn	|0|imm3	|rd	|im2|typ|rm	|
# 517
ORR	Rd,Rn,Const		|1 1 1 1 0|i|0 0 0 1 0|s|rn	|0|imm3	|rd	|imm8		|
# 519
ORR	Rdn,Rm			|0 1 0 0 0 0 1 1 0 0|rm   |rdn	|
# 523
PKH	Rd,Rn,Rm,Pack		|1 1 1 0 1 0 1 0 1 1 0|s|rn	|0|imm3	|rd	|im2|b|t|rm	|
# 525
PLD	Rn,Imm12		|1 1 1 1 1 0 0 0 1 0|w|1|rn	|1 1 1 1|imm12			|
# 527
PLD	Dst			|1 1 1 1 1 0 0 0|u|0 0 1 1 1 1 1|1 1 1 1|imm12			|
# 529
PLD	Rn,Rm,Lsl,Imm2		|1 1 1 1 1 0 0 0 0 0|w|1|rn	|1 1 1 1|0 0 0 0 0 0|im2|rm	|
# 531
PLI	Rn,Imm12		|1 1 1 1 1 0 0 1 1 0 0 1|rn	|1 1 1 1|imm12			|
# 533
PLI	Rn,Rm,Lsl,Imm2		|1 1 1 1 1 0 0 1 0 0 0 1|rn	|1 1 1 1|0 0 0 0 0 0|im2|rm	|
# 535
POP	Reglist			|1 0 1 1 1 1 0|p|reglist	|
# 539
PUSH	Reglist			|1 0 1 1 0 1 0|m|reglist	|
# 541
QADD	Rd,Rm,Rn		|1 1 1 1 1 0 1 0 1 0 0 0|rn	|1 1 1 1|rd	|1 0 0 0|rm	|
# 543
QADD16	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 0 1|rn	|1 1 1 1|rd	|0 0 0 1|rm	|
# 545
QADD8	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 0 0|rn	|1 1 1 1|rd	|0 0 0 1|rm	|
# 547
QASX	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 1 0|rn	|1 1 1 1|rd	|0 0 0 1|rm	|
# 549
QDADD	Rd,Rm,Rn		|1 1 1 1 1 0 1 0 1 0 0 0|rn	|1 1 1 1|rd	|1 0 0 1|rm	|
# 551
QDSUB	Rd,Rm,Rn		|1 1 1 1 1 0 1 0 1 0 0 0|rn	|1 1 1 1|rd	|1 0 1 1|rm	|
# 553
QSAX	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 1 0|rn	|1 1 1 1|rd	|0 0 0 1|rm	|
# 555
QSUB	Rd,Rm,Rn		|1 1 1 1 1 0 1 0 1 0 0 0|rn	|1 1 1 1|rd	|1 0 1 0|rm	|
# 557
QSUB16	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 0 1|rn	|1 1 1 1|rd	|0 0 0 1|rm	|
# 559
QSUB8	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 0 0|rm	|1 1 1 1|rd	|0 0 0 1|rm	|
# 561
RBIT	Rd,Rm			|1 1 1 1 1 0 1 0 1 0 0 1|rm	|1 1 1 1|rd	|1 0 1 0|rm	|
# 563
REV	Rd,Rm			|1 0 1 1 1 0 1 0 0 0|rm   |rd	|
# 565
REV16	Rd,Rm			|1 0 1 1 1 0 1 0 0 1|rm   |rd	|
# 567
REVSH	Rd,Rm			|1 0 1 1 1 0 1 0 1 1|rm   |rd	|
# 569
ROR	Rd,Rm,Imm		|1 1 1 0 1 0 1 0 0 1 0|s|1 1 1 1|0|imm3	|rd	|im2|1 1|rm	|
# 571
ROR	Rdn,Rm			|0 1 0 0 0 0 0 1 1 1|rm   |rdn	|
# 573
RRX	Rd,Rm			|1 1 1 0 1 0 1 0 0 1 0|s|1 1 1 1|0 0 0 0|rd	|0 0 1 1|rm	|
# 575
RSB	Rd,Rn,Zero		|0 1 0 0 0 0 1 0 0 1|rn   |rd	|
# 577
RSB	Rd,Rn,Rm,Shift		|1 1 1 0 1 0 1 1 1 1 0|s|rn	|0|imm3	|rd	|im2|typ|rm	|
# 587
SADD	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 0 1|rn	|1 1 1 1|rd	|0 0 0 0|rm	|
# 589
SADD8	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 0 0|rn	|1 1 1 1|rd	|0 0 0 0|rm	|
# 591
SASX	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 1 0|rn	|1 1 1 1|rd	|0 0 0 0|rm	|
# 593
SBC	Rd,Rn,Const		|1 1 1 1 0|i|0 1 0 1 1|s|rn	|0|imm3	|rd	|imm8		|
# 595
SBC	Rdn,Rm			|0 1 0 0 0 0 0 1 1 0|rm   |rdn	|
# 599
SBFX	Rd,Rn,Lsb,Wid		|1 1 1 1 0 0 1 1 0 1 0 0|rn	|0|imm3	|rd	|im2|0|widthm1	|
# 601
SDIV	Rd,Rn,Rm		|1 1 1 1 1 0 1 1 1 0 0 1|rn	|1 1 1 1|rd	|1 1 1 1|rm	|
# 603
SEL	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 1 0|rn	|1 1 1 1|rd	|1 0 0 0|rm	|
# 605
SETEND	Endian			|1 0 1 1 0 1 1 0 0 1 0 1|e|0 0 0|
# 607
SEV	-			|1 0 1 1 1 1 1 1 0 1 0 0 0 0 0 0|
# 609
SHADD16	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 0 1|rn	|1 1 1 1|rd	|0 0 1 0|rm	|
# 611
SHADD8	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 0 0|rn	|1 1 1 1|rd	|0 0 1 0|rm	|
# 613
SHAX	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 1 0|rn	|1 1 1 1|rd	|0 0 1 0|rm	|
# 615
SHSAX	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 1 0|rn	|1 1 1 1|rd	|0 0 1 0|rm	|
# 617
SHSUB16	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 0 1|rn	|1 1 1 1|rd	|0 0 1 0|rm	|
# 619
SHSUB8	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 0 0|rn	|1 1 1 1|rd	|0 0 1 0|rm	|
# 621
SMLABB	Rd,Rn,Rm,Ra		|1 1 1 1 1 0 1 1 0 0 0 1|rn	|ra	|rd	|0 0|n|m|rm	|
# 623
SMLAD	Rd,Rn,Rm,Ra		|1 1 1 1 1 0 1 1 0 0 1 0|rn	|ra	|rd	|0 0 0|m|rm	|
# 625
SMLAL	Rdlo,Rdhi,Rn,Rm		|1 1 1 1 1 0 1 1 1 1 0 0|rn	|rdlo	|rdhi	|0 0 0 0|rm	|
# 627
SMLAL	Rdlo,Rdhi,Rn,Rm		|1 1 1 1 1 0 1 1 1 1 0 0|rm	|rdlo	|rdhi	|1 0|n|m|rm	|
# 629
SMLALD	Rdlo,Rdhi,Rn,Rm		|1 1 1 1 1 0 1 1 1 1 0 0|rm	|rdlo	|rdhi	|1 1 0|m|rm	|
# 631
SMLAWB	Rd,Rn,Rm,Ra		|1 1 1 1 1 0 1 1 0 0 1 1|rn	|ra	|rd	|0 0 0|m|rm	|
# 633
SMLSD	Rd,Rn,Rm,Ra		|1 1 1 1 1 0 1 1 0 1 0 0|rn	|ra	|rd	|0 0 0|m|rm	|
# 635
SMLSLD	Rdlo,Rdhi,Rn,Rm		|1 1 1 1 1 0 1 1 1 1 0 1|rn	|rdlo	|rdhi	|1 1 0|m|rm	|
# 637
SMMLA	Rd,Rn,Rm,Ra		|1 1 1 1 1 0 1 1 0 1 0 1|rn	|ra	|rd	|0 0 0|r|rm	|
# 639
SMMLS	Rd,Rn,Rm,Ra		|1 1 1 1 1 0 1 1 0 1 1 0|rn	|ra	|rd	|0 0 0|r|rm	|
# 641
SMMUL	Rd,Rn,Rm		|1 1 1 1 1 0 1 1 0 1 0 1|rn	|1 1 1 1|rd	|0 0 0|r|rm	|
# 643
SMUAD	Rd,Rn,Rm		|1 1 1 1 1 0 1 1 0 0 1 0|rn	|1 1 1 1|rd	|0 0 0|m|rm	|
# 645
SMUL	Rd,Rn,Rm		|1 1 1 1 1 0 1 1 0 0 0 1|rn	|1 1 1 1|rd	|0 0|n|m|rm	|
# 647
SMULL	Rdlo,Rdhi,Rn,Rm		|1 1 1 1 1 0 1 1 1 0 0 0|rn	|rdlo	|rdhi	|0 0 0 0|rm	|
# 649
SMULWB	Rd,Rn,Rm		|1 1 1 1 1 0 1 1 0 0 1 1|rn	|1 1 1 1|rd	|0 0 0|m|rm	|
# 651
SMUSD	Rd,Rn,Rm		|1 1 1 1 1 0 1 1 0 1 0 0|rn	|1 1 1 1|rd	|0 0 0|m|rm	|
# 653
SSAT	Rd,Imm,Rn,Shift		|1 1 1 1 0 0 1 1 0 0|s|0|rn	|0|imm3	|rd	|im2|0|sat_imm	|
# 655
SSAT16	Rd,Imm,Rn		|1 1 1 1 0 0 1 1 0 0 1 0|rn	|0 0 0 0|rd	|0 0 0 0|sat_imm|
# 657
SSAX	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 1 0|rn	|1 1 1 1|rd	|0 0 0 0|rm	|
# 659
SSUB16	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 0 1|rn	|1 1 1 1|rd	|0 0 0 0|rm	|
# 661
SSUB8	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 0 0|rn	|1 1 1 1|rd	|0 0 0 0|rm	|
# 663
STC	Cop,Crd,Rn,Imm		|cond	|1 1 0|p|u|d|w|0|rn	|crd	|cop	|imm8		|
# 665
STM	Rd,Reglist		|1 1 0 0 0|rn	|reglist	|
# 669
STMDB	Rn,Reglist		|1 1 1 0 1|0 0 1 0 0|w|0|rn	|0|m|0|reglist			|
# 671
STMIB	Rn,Reglist		|cond	|1 0 0 1 1 0|w|0|rn	|reglist			|
# 673
STR	Rt,Rn,Imm		|0 1 1 0 0|imm5	    |rn   |rt	|
# 677
STR	Rt,Rn,Rm		|0 1 0 1 0 0 0|rm   |rn   |rt	|
# 679
STRB	Rt,Rn,Imm5		|0 1 1 1 0|imm5	    |rn   |rt	|
# 683
STRB	Rt,Rn,Rm		|0 1 0 1 0 1 0|rm   |rn   |rt	|
# 685
STRBT	Rt,Rn,Imm8		|1 1 1 1 1|0 0 0 0 0 0 0|rn	|rt	|1 1 1 0|imm8		|
# 687
STRD	Rt,Rt2,Rn		|1 1 1 0 1 0 0|p|u|1|w|0|rn	|rt	|rt2	|imm8		|
# 691
STREX	Rd,Rt,Rn		|1 1 1 0 1 0 0 0 0 1 0 0|rn	|rt	|rtd	|imm8		|
# 693
STREXB	Rd,Rt,Rn		|1 1 1 0 1 0 0 0 1 1 0 0|rn	|rt	|1 1 1 1|0 1 0 0|rd	|
# 695
STREXD	Rd,Rt,Rt2,Rn		|1 1 1 0 1 0 0 0 1 1 0 0|rn	|rt	|rt2	|0 1 1 1|rd	|
# 697
STREXH	Rd,Rt,Rn		|1 1 1 0 1 0 0 0 1 1 0 0|rn	|rt	|1 1 1 1 0 1 0 1|rd	|
# 699
STRH	Rt,Rn,Imm		|1 0 0 0 0|imm5     |rn   |rt	|
# 703
STRH	Rt,Rn,Rm		|0 1 0 1 0 0 1|rm   |rn   |rt	|
# 705
STRHT	Rt,Rn,Imm8		|1 1 1 1 1 0 0 0 0 0 1 0|rn	|rt	|1 1 1 0|imm8		|
# 707
STRT	Rt,Rn,Imm8		|1 1 1 1 1 0 0 0 0 1 0 0|rn	|rt	|1 1 1 0|imm8		|
# 709
SUB	Rd,Rn,Imm3		|0 0 0 1 1 1 1|im3  |rn   |rd	|
# 713
SUB	Rb,Rn,Rm		|0 0 0 1 1 0 1|rm   |rn   |rd	|
# 715
SUB	SP,SP,Imm		|1 0 1 1 0 0 0 0 1|imm7		|
# 719
SUB	Rd,SP,Rm,Shift		|1 1 1 0 1 0 1 1 1 0 1|s|1 1 0 1|0|imm3	|rd	|im2|typ|rm	|
# 721
SVC	Imm8			|1 1 0 1 1 1 1 1|imm8		|
# 725
SXTAB	Rd,Rn,Rm,Rot		|1 1 1 1 1 0 1 0 0 1 0 0|rn	|1 1 1 1|rd	|1|0|rot|rm	|
# 727
SXTAB16	Rd,Rn,Rm,Rot		|1 1 1 1 1 0 1 0 0 0 1 0|rn	|1 1 1 1|rd	|1|0|rot|rm	|
# 729
SXTAH	Rd,Rn,Rm,Rot		|1 1 1 1 1 0 1 0 0 0 0 0|rn	|1 1 1 1|rd	|1 0|rot|rm	|
# 731
SXTB	Rd,Rm			|1 0 1 1 0 0 1 0 0 1|rm   |rd	|
# 733
SXTB16	Rd,Rm,Rot		|1 1 1 1 1 0 1 0 0 0 1 0 1 1 1 1|1 1 1 1|rd	|1 0|rot|rm	|
# 735
SXTH	Rd,Rm			|1 0 1 1 0 0 1 0 0 0|rm   |rd	|
# 737
TBB	Rn,Rm			|1 1 1 0 1 0 0 0 1 1 0 1|rn	|1 1 1 1 0 0 0 0 0 0 0|h|rm	|
# 739
TEQ	Rn,Const		|1 1 1 1 0|i|0 0 1 0 0 1|rn	|0|imm3 |1 1 1 1|imm8		|
# 741
TEQ	Rn,Rm,Shift		|1 1 1 0 1 0 1 0 1 0 0 1|rn	|0|imm3	|1 1 1 1|im2|typ|rm	|
# 745
TST	Rn,Const		|1 1 1 1 0|i|0 0 0 0 0 1|rn	|0|imm3 |1 1 1 1|imm8		|
# 747
TST	Rn,Rm			|0 1 0 0 0 0 1 0 0 0|rm   |rn	|
# 751
UADD16	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 0 1|rn	|1 1 1 1|rd	|0 1 0 0|rm	|
# 753
UADD8	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 0 0|rn	|1 1 1 1|rd	|0 1 0 0|rm	|
# 755
UASX	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 1 0|rn	|1 1 1 1|rd	|0 1 0 0|rm	|
# 757
UBFX	Rd,Rn,Lsb,Wid		|1 1 1 1 0 0 1 1 1 1 0 0|rn	|0|imm3	|rd	|im2|0|widthm1	|
# 759
UDF	Imm8			|1 1 0 1 1 1 1 0|imm8		|
# 761
UDIV	Rd,Rn,Rm		|1 1 1 1 1 0 1 1 1 0 1 1|rn	|1 1 1 1|rd	|1 1 1 1|rm	|
# 763
UHADD16	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 0 1|rn	|1 1 1 1|rd	|0 1 1 0|rm	|
# 765
UHADD8	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 0 0|rn	|1 1 1 1|rd	|0 1 1 0|rm	|
# 767
UHASX	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 1 0|rn	|1 1 1 1|rd	|0 1 1 0|rm	|
# 769
UHSAX	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 1 0|rm	|1 1 1 1|rd	|0 1 1 0|rm	|
# 771
UHSUB16	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 0 1|rn	|1 1 1 1|rd	|0 1 1 0|rm	|
# 773
UHSUB8	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 0 0|rn	|1 1 1 1|rd	|0 1 1 0|rm	|
# 775
UMAAL	Rdlo,Rdhi,Rn,Rm		|1 1 1 1 1 0 1 1 1 1 1 0|rn	|rdlo	|rdhi	|0 1 1 0|rm	|
# 777
UMLAL	Rdlo,Rdhi,Rn,Rm		|1 1 1 1 1 0 1 1 1 1 1 0|rn	|rdlo	|rdhi	|0 0 0 0|rm	|
# 779
UMULL	Rdlo,Rdhi,Rn,Rm		|1 1 1 1 1 0 1 1 1 0 1 0|rn	|rdlo	|rdhi	|0 0 0 0|rm	|
# 781
UQADD16	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 0 1|rn	|1 1 1 1|rd	|0 1 0 1|rm	|
# 783
UQADD8	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 0 0|rn	|1 1 1 1|rd	|0 1 0 1|rm	|
# 785
UQASX	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 0 1 0|rn	|1 1 1 1|rd	|0 1 0 1|rm	|
# 787
UQSAX	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 1 0|rn	|1 1 1 1|rd	|0 1 0 1|rm	|
# 789
UQSUB16	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 0 1|rn	|1 1 1 1|rd	|0 1 0 1|rm	|
# 791
UQSUB8	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 0 0|rn	|1 1 1 1|rd	|0 1 0 1|rm	|
# 793
USAD8	Rd,Rn,Rm		|1 1 1 1 1 0 1 1 0 1 1 1|rn	|1 1 1 1|rd	|0 0 0 0|rm	|
# 795
USADA8	Rd,Rn,Rm,Ra		|1 1 1 1 1 0 1 1 0 1 1 1|rn	|ra	|rd	|0 0 0 0|rm	|
# 797
USAT	Rd,Imm5,Rn,Shift	|1 1 1 1 0 0 1 1 1 0|s|0|rn	|0|imm3	|rd	|im2|0|sat_imm	|
# 799
USAT16	Rd,Imm4,Rn		|1 1 1 1 0 0 1 1 1 0 1 0|rn	|0 0 0 0|rd	|0 0 0 0|sat_imm|
# 801
USAX	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 1 0|rn	|1 1 1 1|rd	|0 1 0 0|rm	|
# 803
USUB16	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 0 1|rn	|1 1 1 1|rd	|0 1 0 0|rm	|
# 805
USUB8	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 1 1 0 0|rn	|1 1 1 1|rd	|0 1 0 0|rm	|
# 807
UXTAB	Rd,Rn,Rm,Rot		|1 1 1 1 1 0 1 0 0 1 0 1|rn	|1 1 1 1|rd	|1 0|rot|rm	|
# 809
UXTAB16	Rd,Rn,Rm,Rot		|1 1 1 1 1 0 1 0 0 0 1 1|rn	|1 1 1 1|rd	|1 0|rot|rm	|
# 811
UXTAH	Rd,Rn,Rm,Rot		|1 1 1 1 1 0 1 0 0 0 0 1|rn	|1 1 1 1|rd	|1 0|rot|rm	|
# 813
UXTB	Rd,Rm			|1 0 1 1 0 0 1 0 1 1|rm   |rd	|
# 815
UXB16	Rd,Rm			|1 1 1 1 1 0 1 0 0 0 1 1 1 1 1 1|1 1 1 1|rd	|1 0|rot|rm	|
# 817
UXTH	Rd,Rm			|1 0 1 1 0 0 1 0 1 0|rm   |rd	|
# <vector stuff>
# 955
VMRS	Rt,FPSCR		|cond	|1 1 1 0 1 1 1 1 0 0 0 1|rt	|1 0 1 0 0 0 0 1 0 0 0 0|
# 957
VMSR	FPSCR,Rt		|cond	|1 1 1 0 1 1 1 0 0 0 0 1|rt	|1 0 1 0 0 0 0 1 0 0 0 0|
# <vector stuff>
# 1105
WFE	-			|1 0 1 1 1 1 1 1 0 0 1 0 0 0 0 0|
# 1107
WFI	-			|1 0 1 1 1 1 1 1 0 0 1 1 0 0 0 0|
# 1109
YIELD	-			|1 0 1 1 1 1 1 1 0 0 0 1 0 0 0 0|
'''

thumb_t2_desc = '''
#				|       |       |       |       |       |       |       |       |
#				|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|
# 300
ADC	Rd,Rn,Rm		|1 1 1 0 1 0 1 1 0 1 0|s|rn	|0|imm3	|rd	|im2|typ|rm	|
# 304
ADD	Rdn,Imm8		|0 0 1 1 0|rd	|imm8		|
# 308
ADD	Rdn,Rm			|0 1 0 0 0 1 0 0|d|rm     |rdn	|
# 314
ADD	SP,SP,Imm7		|1 0 1 1 0 0 0 0 0|imm7		|
# 316
ADD	SP,Rm			|0 1 0 0 0 1 0 0|d|rm     |1 0 1|
# 320
ADR	Rd,Dst			|1 1 1 1 0|i|1 0 1 0 1 0 1 1 1 1|0|imm3	|rd	|imm8		|
# 324
AND	Rd,Rn,Rm,Shift		|1 1 1 0 1 0 1 0 0 0 0|s|rn	|0|imm3	|rd	|im2|typ|rm	|
# 328
ASR	Rd,Rm,Imm		|1 1 1 0 1 0 1 0 0 1 0|s|1 1 1 1|0|imm3	|rd	|im2|1 0|rm	|
# 330
ASR	Rd,Rn,Rm		|1 1 1 1 1 0 1 0 0 1 0|s|rn	|1 1 1 1|rd	|0 0 0 0|rm	|
# 332
B	Dst,>J			|1 1 1 0 0|imm11		|
# 340
BIC	Rd,Rn,Rm,Shift		|1 1 1 0 1 0 1 0 0 0 1|s|rn	|0|imm3	|rd	|im2|typ|rm	|
# 346
BLX	Dst,>C			|1 1 1 1 0|s|imm10h		|1 1|j|0|k|imm10l		|
# 356 XXX: COND ?
CDP2	Cop,Op1,Rd,Rn,Rm,Op2	|1 1 1 1 1 1 1 0|opc	|crn	|crd	|cop	|opc2 |0|crm	|
# 364
CMN	Rn,Rn,Shift		|1 1 1 0 1 0 1 1 0 0 0 1|rn	|0|imm3	|1 1 1 1|im2|typ|rm	|
# 368
CMP	Rn,Const		|1 1 1 1 0|i|0 1 1 0 1 1|rn	|0|imm3	|1 1 1 1|imm8		|
# 370
CMP	Rn,Rm			|0 1 0 0 0 1 0 1|n|rm	  |rn	|
# 385
EOR	Rd,Rn,Rm,Shift		|1 1 1 0 1 0 1 0 1 0 0|s|rn	|0|imm3 |rd	|im2|typ|rm	|
# 393 XXX: COND ?
LDC	Cop,Crd,Rn		|1 1 1 1 1 1 0|p|u|d|w|1|rn	|crd	|cop	|imm8		|
# 395 XXX: COND ?
LDC	Cop,Crd,Dst		|1 1 1 1 1 1 0|p|u|d|w|1 1 1 1 1|crd	|cop	|imm8		|
# 397
LDM	Rn,Reglist		|1 1 1 0 1 0 0 0 1 0|w|1|rn	|p|m|0|reglist			|
# 407
LDR	Rt,Sp,Imm		|1 0 0 1 1|rt	|imm8		|
# 411
LDR	Rt,Dst			|1 1 1 1 1 0 0 0|u|1 0 1 1 1 1 1|rt	|imm12			|
# 413
LDR	Rt,Rn,Rm		|1 1 1 1 1 0 0 0 0 1 0 1|rn	|rt	|0 0 0 0 0 0|im2|rm	|
# 417
LDRB	Rt,Rn,Imm		|1 1 1 1 1 0 0 0 1 0 0 1|rn	|rt	|imm12			|


'''

class Arm_Thumb_ins(arm_base.Arm_Base_ins):

	def __init__(self, pj, lim, lang):
		super().__init__(pj, lim, lang)
		if self.lo & 1:
			raise assy.Invalid("Unaligned Instruction")

class Arm_Thumb(assy.Instree_disass):
	def __init__(self):
		super().__init__("arm_thumb", 16, 8, "<")
		self.add_ins(thumb_desc, Arm_Thumb_ins)
		self.add_ins(thumb_t1_desc, Arm_Thumb_ins)
		self.add_ins(thumb_t2_desc, Arm_Thumb_ins)

	def codeptr(self, pj, adr):
		t = pj.m.lu32(adr)
		c = data.Codeptr(pj, adr, adr + 4, t)
		pj.todo(t, self.disass)
		return c

	def vector(self, pj, adr):
		return

	def vectors(self, pj, adr=0x0, xops=1):
		return

if __name__ == "__main__":
	h = Arm_Thumb()
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
