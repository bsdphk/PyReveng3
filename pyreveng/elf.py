#!/usr/bin/env python
#
# Copyright (c) 2025 Poul-Henning Kamp <phk@phk.freebsd.dk>
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

"""
ELF file
"""

from pyreveng import leaf
from pyreveng import mem, data, listing

class Elf32Msb():
    addr=data.Bu32
    half=data.Bu16
    #lword=data.Bu64
    off=data.Bu32
    #sword=data.Bs32
    word=data.Bu32

class ElfIdent(data.Struct):
    def __init__(self, tree, lo):
        super().__init__(
            tree,
            lo,
            vertical=True,
            ei_mag_=4,
            ei_class_=data.Bu8,
            ei_data_=data.Bu8,
            ei_version_=data.Bu8,
            ei_osabi_=data.Bu8,
            ei_abiversion_=data.Bu8,
            ei_pad_=5,
            ei_brand_=data.Bu8,
            ei_nident_=data.Bu8,
        )

class ElfHeader(data.Struct):
    def __init__(self, fmt, tree, lo):
        super().__init__(
            tree,
            lo,
            vertical=True,
            e_type_=fmt.half,
            e_machine_=fmt.half,
            e_version_=fmt.word,
            e_entry_=fmt.addr,
            e_phoff_=fmt.off,
            e_shoff_=fmt.off,
            e_flags_=fmt.word,
            e_ehsize_=fmt.half,
            e_phentsize_=fmt.half,
            e_phnum_=fmt.half,
            e_shentsize_=fmt.half,
            e_shnum_=fmt.half,
            e_shstrndx_=fmt.half,
        )

class ElfPhdr(data.Struct):
    fmt = None
    def __init__(self, tree, lo):
        fmt = self.fmt
        super().__init__(
            tree,
            lo,
            vertical=True,
            p_type_=fmt.word,
            p_offset_=fmt.off,
            p_vaddr_=fmt.addr,
            p_paddr_=fmt.addr,
            p_filesz_=fmt.word,
            p_memsz_=fmt.word,
            p_flags_=fmt.word,
            p_align_=fmt.word,
        )

class Elf():

    def __init__(self, fn=None, octets=None):
        if fn is not None:
            self.octets = open(fn, "rb").read()
        else:
            self.octets = octets
        assert self.octets[:4] == b'\x7fELF'
        self.m = mem.ByteMem(lo=0x0, hi=len(self.octets))
        self.m.load_data(0, 1, self.octets)

        self.e_ident = ElfIdent(self.m, 0).insert()
        if self.e_ident.ei_class == 1 and self.e_ident.ei_data == 2:
            self.fmt = Elf32Msb()
        else:
            self.fmt=None

        self.e_hdr = ElfHeader(self.fmt, self.m, self.e_ident.hi).insert()

        class ElfPhdrFmt(ElfPhdr):
            fmt = self.fmt

        if self.e_hdr.e_phoff > 0 and self.e_hdr.e_phnum > 0:
            self.e_phdr = data.Array(
                self.e_hdr.e_phnum,
                ElfPhdrFmt,
                vertical=True,
            )(self.m, self.e_hdr.e_phoff).insert()

    def load(self, cx):
        for psec in self.e_phdr:
            mt = mem.ByteMem(0, psec.p_filesz)
            mt.load_data(
                0,
                1,
                self.octets[psec.p_offset : psec.p_offset + psec.p_filesz ]
            )
            cx.m.map(mt, psec.p_vaddr)

    def listing(self, fn):
        with open(fn, "w", encoding="utf8") as file:
            listing.Listing(self.m, fo=file)
