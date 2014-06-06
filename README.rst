PyReveng3 is a toolkit for reverse engineering and analysing binary
programs, or for that matter, binary data.

The fundamental idea is to build data structures representing the
analysis, available for further programatic spelunking, rather than
just a textual representation where the structure is flattened.

Of course, dumping the textual representation in the shape of a
listing is one of the most typical "further programatic spelunkings"
one can do, but it is not limited to only that.

Complete & usable disassemblers
-------------------------------

* HP Nanoprocessor
 * 1820-1692
  * examples/HP9411/task_09411.py
 * 1820-1692 w/paged mode as in HP3325 and HP3336
  * examples/HP3325A/example.py
  * examples/HP3336/example.py
* Motorola 6800
 * MC6800
  * examples/Austron_2100F/example_107.py
  * examples/HP3335A/example.py
  * examples/HP5370/example_hp5370a.py
  * examples/HP5370/example_hp5370b.py
  * examples/HP5370/example_hp5359b.py
 * MC68HC11
  * examples/PL99/example.py

* Intel MCS4
 * 4004
  * examples/Micrologic_ML200/example.py
* Intel MCS51
 * mcs51
 * i8032
  * examples/Apollo_618C/example_cdu.py
* Texas Instruments TMS9900
 * TMS9900
 * TMS9981
  * examples/HP6034A/example.py
* Zilog Z-80
 * Z-80
  * examples/RC702_bootrom/example_roa_375.py
  * examples/RC702_bootrom/example_rob_357.py

Incomplete or Experimental disassemblers
----------------------------------------
* Intel x86
 * 8088/8086
  * examples/Apollo_618C/example_main.py

Enjoy,

Poul-Henning
