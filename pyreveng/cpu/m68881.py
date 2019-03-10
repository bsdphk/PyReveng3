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
#

"""
MC68881/68882 floating point instructions

Page numbers with '*' reference MC68881/68882 USER's MANUAL (MC68881UM/AD Rev2)

"""

from pyreveng import assy, data, mem

m68881_instructions = '''
#		src,dst		ea	|_ _ _ _|_ _ _v_|_ _v_ _|_v_ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|

# *88/4-30
FBcc		-		0	|1 1 1 1| cid |0 1|0| condpred	| oper				|
FBcc		-		0	|1 1 1 1| cid |0 1|1| condpred	| oper				| oper2				|

# *96/4-38
FDBcc		-		0	|1 1 1 1| cid |0 0 1|0 0 1|count|0 0 0 0 0 0 0 0 0 0| condpred	| disp				|

# *122/4-64
FMOVE		L,ea		1f7d	|1 1 1 1| cid |0 0 0| ea	|0|R|0| src | dst |0 0 0 0 0 0 0|

# *124/4-66
FMOVEFPN	L,ea		37d	|1 1 1 1| cid |0 0 0| ea	|0 1 1| dfm | src | kfact	|

# *128/4-70
FMOVE		L,ea		1f7f	|1 1 1 1| cid |0 0 0| ea	|1 0|R| reg |0 0 0|0 0 0 0 0 0 0|

# *130/4-72
FMOVECR		-		0	|1 1 1 1| cid |0 0 0|0 0 0 0 0 0|0|1|0|1 1 1| dst | rom         |

# *132/4-74
# 387/5-85
FMOVEM.X	L,ea		0f6c	|1 1 1 1| cid |0 0 0| ea	|1 1|0|mod|0 0 0| rlist		|
FMOVEM.X	L,ea		0374	|1 1 1 1| cid |0 0 0| ea	|1 1|1|mod|0 0 0| rlist		|

# *136/4-78
FMOVEM		L,ea		1f7f	|1 1 1 1| cid |0 0 0| ea	|1 0|D|rl |0 0 0 0 0 0 0 0 0 0 0|

# *143/4-85
FNOP		-		0	|1 1 1 1| cid |0 1 0|0 0 0 0 0 0|0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0|

# *146/4-88
FRESTORE	L,ea		76c	|1 1 1 1| cid |1 0 1| ea        |

# *148/4-90
FSAVE		L,ea		374	|1 1 1 1| cid |1 0 0| ea        |

# *154/4-96
# 412/5-110
FScc		B,ea		37d	|1 1 1 1| cid |0 0 1| ea	|0 0 0 0 0 0 0 0 0 0| condpred	|

# *177/4-119
FTRAPcc		-		0	|1 1 1 1| cid |0 0 1 1 1 1|0 1 0|0 0 0 0 0 0 0 0 0 0| condpred	| oper				|
FTRAPcc		-		0	|1 1 1 1| cid |0 0 1 1 1 1|0 1 1|0 0 0 0 0 0 0 0 0 0| condpred	| oper				| oper2				|
FTRAPcc		-		0	|1 1 1 1| cid |0 0 1 1 1 1|1 0 0|0 0 0 0 0 0 0 0 0 0| condpred	|

#############
Fsomething	L,ea		1f7d	|1 1 1 1| cid |0 0 0| ea	|0|R|0| src | dst | something   |

'''

def m68881(cpu):
	cpu.it.load_string(m68881_instructions)
