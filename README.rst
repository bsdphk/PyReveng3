PyReveng3 is a toolkit for reverse engineering and analysing binary
programs, or for that matter any binary data, for computer archaeologic
investigations.

Computers used to be pretty strange, and some of the fundamental
assumptions modern reverse-engineering tools make, notably "memory
is a linear array of bytes", makes them useless for historic computers.

PyReveng3 approaches all such issues with as much generality as possible,
to handle any weird computer architecture I have ever encountered.

Another important idea has been to make it easy to add a new
disassembler, without having to deal with a lot of binary arithmetic,
by taking in the instruction descriptions as they are typically
found in manuals:

```
    PUSH    r2      |0 1 0 1 0| reg |
    PUSH    sr      |0 0 0|sr |1 1 0|
    POP     W,ea    |1 0 0 0 1 1 1 1|mod|0 0 0| rm  |
    POP     r2      |0 1 0 1 1| reg |
    POP     sr      |0 0 0|sr |1 1 1|
    XCHG    r,ea    |1 0 0 0 0 1 1|w|mod| reg | rm  |
    XCHG    W,a,r2  |1 0 0 1 0| reg |
    NOP     -       |1 0 0 1 0 0 0 0|
```

Disassemblers are not just for CPUs, they can also be used to
analyze interpreted code instructions, graphical primitives
and much more.

The fundamental strategy is to build data structures representing the
analysis, available for further programatic spelunking, rather than
just a textual representation where the structure is flattened.

Of course, dumping the textual representation in the shape of a
listing is one of the most typical "further programatic spelunkings"
one can do, but it is not limited to only that.

The project contains a number of examples which I have deemed both
sufficiently obsolete, obscure and out-dated to be covered by the
"fair use" doctrine, if you disagree please let me know.

Should you have access to the original source code for any of the
examples, I would love to receive a copy, even if I cannot publish
it.

Disassemblers and examples
--------------------------

* HP1345A Vector Graphics Processor
  * `HP1345A/example.py`
    HP1345 - Built-in Diagnostic processor
  * `HP1347A_prototype/example.py`
    HP1347 - Prototype

* HP85662 Vector Graphical Processor
  * `HP8568B/example.py`
    HP8568A Spectrum Analyzer

* Hewlett Packard Nanoprocessor (1820-1692)
  * `HP3325A/example.py`
    HP3325 Synthesizer/Function Generator
  * `HP3336/example.py`
    HP3336 Synthesizer/Level Generator
  * `HP3455A/example.py`
    HP3455 Digital Voltmeter

* Intel i8085
  (No in-project examples)

* Intel i8088/i8086
  * `Apollo_618C/example_main.py`
    II Morrow Apollo 618C Loran - Navigation Processor

* Motorola M68000
  * `HP8568B/example.py`
    HP8568A Spectrum Analyzer

* Motorola M68010
  (No in-project examples)

* Motorola M68020
  * `R1000_400/example.py`
    Rational R1000/400 - IOC EEPROM
  * `R1000_400/example_FS_0.py`
  * `R1000_400/example_IOC.py`
  * `R1000_400/example_RECOVERY.py`

* Motorola MC68881/882 Floating Point Coprocessor
  (No in-project examples)

* Motorola MC6800/MC68HC11
  * `Austron_2100F/example_107.py`
    Austron 2100F Loran-C Frequency Receiver
  * `HP3335A/example.py`
    HP3335 Synthesizer/Level Generator
  * `PL99/example.py`
    Ray Jefferson PL99 Handheld Loran-C receiver

* Motorola MC6809
  * `HP1347A_prototype/example.py`
    HP1347 - Prototype
  * `HP6626A/example.py`
    HP6626A Multiple Output Linear System DC Power Supply

* Intel 4004/MCS-4
  * `Micrologic_ML200/example.py`
    Micrologic ML200 Loran-C Receiver

* Intel MCS-48 - 8035/39/40/48/49/50
  * `CBM900/example_wdc.py`
    Commodore CBM900 - Hard Disk Controller
  * `HP1345A/example.py`
    HP1345 - Built-in Diagnostic processor

* Intel MCS-51 - 8032/51
  * `Apollo_618C/example_cdu.py`
    II Morrow Apollo 618C Loran - Display Controller

* MOS Technology 6500 Family
  * `CBM900/example_fdc.py`
    Commodore CBM900 - Floppy controller

* Data General Nova CPU
  (No in-project examples)

* Texas Instruments TMS9990
  * `HP6034A/example.py`
    HP6034A System DC Power Supply

* Zilog Z80
  * `RC702_bootrom/example_roa_375.py`
    Regnecentralen Piccolo - RC702 boot EPROM
  * `RC702_bootrom/example_rob_357.py`
    Regnecentralen Piccolo - RC702 boot EPROM

* Zilog Z8000
  * `CBM900/example_boot.py`
    Commodore CBM900 - Boot EPROM


Enjoy,

Poul-Henning
