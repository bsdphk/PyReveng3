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

'''Motorola M68020
'''

from pyreveng.cpu import m68010

m68020_desc = """
#		src,dst		ea	|_ _ _ _|_ _ _v_|_ _v_ _|_v_ _ _|_ _ _ _|_ _ _ _|_ _ _ _|_ _ _ _|

# 139/4.35
BFCLR		L,ea,BF		365	|1 1 1 0 1 1 0 0 1 1| ea	|0 0 0 0|o| off	    |w| wid	|

# 141/4.37
BFEXTS		L,ea,BF,Dn	f75	|1 1 1 0 1 0 1 1 1 1| ea        |0| Dn  |o| off     |w| wid     |

# 144/4.40
BFEXTU		L,ea,BF,Dn	f75	|1 1 1 0 1 0 0 1 1 1| ea        |0| Dn  |o| off     |w| wid     |

# 147/4.43 (nb: Typo)
BFFFO		ea,BF,Dn	f65	|1 1 1 0 1 1 0 1 1 1| ea	|0| Dn	|o| off     |w| wid	|

# 150/4.46
BFINS 		L,Dn,ea,BF	375	|1 1 1 0 1 1 1 1 1 1| ea        |0| Dn  |o| off     |w| wid     |

# 153/4.49
BFSET		L,ea,BF		365	|1 1 1 0 1 1 1 0 1 1| ea	|0 0 0 0|o| off	    |w| wid	|

# 155/4.51
BFTST		L,ea,BF		f65	|1 1 1 0 1 0 0 0 1 1| ea	|0 0 0 0|o| off	    |w| wid	|

# 186/4.82
CMP2		Z,ea,Dn		f62	|0 0 0 0 0|sz |0 1 1| ea	|0| Dn  |0 0 0 0 0 0 0 0 0 0 0 0|
CMP2		Z,ea,An		f62	|0 0 0 0 0|sz |0 1 1| ea	|1| An  |0 0 0 0 0 0 0 0 0 0 0 0|

# 196/4.92
DIVS		L,ea,Dx,Dy	1f7d    |0 1 0 0 1 1 0 0 0 1| ea        |0| Dy  |1|0|0 0 0 0 0 0 0| Dx  |
DIVSL		L,ea,Dx,Dy	1f7d    |0 1 0 0 1 1 0 0 0 1| ea        |0| Dy  |1|1|0 0 0 0 0 0 0| Dx  |

# 200/4.96
DIVU		L,ea,Dx,Dy	1f7d    |0 1 0 0 1 1 0 0 0 1| ea        |0| Dy  |0|0|0 0 0 0 0 0 0| Dx  |
DIVUL		L,ea,Dx,Dy	1f7d    |0 1 0 0 1 1 0 0 0 1| ea        |0| Dy  |0|1|0 0 0 0 0 0 0| Dx  |

# 210/4.106
EXTB		L,Dn		0000	|0 1 0 0|1 0 0|1 1 1|0 0 0| Dn  | {
	DN = exts i8 DN to i32
	STDF4 DN
}

# 239/4.135
MULS		L,ea,Dy		1f7d    |0 1 0 0 1 1 0 0 0 0| ea        |0| Dy  |1|0|0 0 0 0 0 0 0| Dx  |
mULS		L,ea,Dx,Dy	1f7d    |0 1 0 0 1 1 0 0 0 0| ea        |0| Dy  |1|1|0 0 0 0 0 0 0| Dx  |

# 242/4.138
mULU		L,ea,Dy		1f7d    |0 1 0 0 1 1 0 0 0 0| ea        |0| Dy  |0|0|0 0 0 0 0 0 0| Dx  |
mULU		L,ea,Dx,Dy	1f7d	|0 1 0 0 1 1 0 0 0 0| ea        |0| Dy  |0|1|0 0 0 0 0 0 0| Dx  |

# 260/4.156
PACK		W,Dx,Dy,data	-	|1 0 0 0| Dy  |1 0 1 0 0|0| Dx  |
PACK		W,decAx,decAy,data -	|1 0 0 0| Ay  |1 0 1 0 0|1| Ax  |

# 300/4.196
UNPK		W,Dx,Dy,data	-	|1 0 0 0| Dy  |1 1 0 0 0|0| Dx  |
UNPK		W,decAx,decAy,data -	|1 0 0 0| Ay  |1 1 0 0 0|1| Ax  |

"""

#######################################################################

class m68020_ins(m68010.m68010_ins):

    def assy_BF(self):
        t = "{"
        if self['o']:
            t += "D%d" % self['off']
        else:
            t += "%d" % self['off']
        t += ":"
        if self['w']:
            t += "D%d" % self['wid']
        else:
            t += "%d" % self['wid']
        return t + "}"


class m68020(m68010.m68010):
    def __init__(self, lang="m68020"):
        super().__init__(lang)
        self.it.load_string(m68020_desc, m68020_ins)
        self.ea_fullext = True
        self.ea_scale = True
        self.cregs.update({
            0x002: ("CACR", "Cache Control Register"),
            0x802: ("CAAR", "Cache Address Register"),
            0x803: ("MSP", "Master Stack Pointer"),
            0x804: ("ISP", "Interrupt Stack Pointer"),
        })

if __name__ == '__main__':
    m = m68020()
    m.it.dump()
