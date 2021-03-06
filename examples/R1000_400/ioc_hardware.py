#!/usr/bin/env python
#
# Copyright (c) 2012-2021 Poul-Henning Kamp <phk@phk.freebsd.dk>
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

'''
   IOC hardware definitions
   ------------------------
'''

DEVICE_SYMBOLS = {
    0x80007f6e: "NV_MACHINE_TYPE",
    0x9303e001: "IO_DISK_WRITE_PROTECT",
    0x9303e800: "IO_SCSI_00_OWN_ID_CDB_SIZE",
    0x9303e801: "IO_SCSI_01_CONTROL",
    0x9303e802: "IO_SCSI_02_TIMEOUT_PERIOD",
    0x9303e803: "IO_SCSI_03_CDB1_TOTSECT",
    0x9303e804: "IO_SCSI_04_CDB2_TOTHEAD",
    0x9303e805: "IO_SCSI_05_CDB3_TOTCYL1",
    0x9303e806: "IO_SCSI_06_CDB4_TOTCYL0",
    0x9303e807: "IO_SCSI_07_CDB5_LBA3",
    0x9303e808: "IO_SCSI_08_CDB6_LBA2",
    0x9303e809: "IO_SCSI_09_CDB7_LBA1",
    0x9303e80a: "IO_SCSI_0a_CDB8_LBA0",
    0x9303e80b: "IO_SCSI_0b_CDB9_SECT",
    0x9303e80c: "IO_SCSI_0c_CDB10_HEAD",
    0x9303e80d: "IO_SCSI_0d_CDB11_CYL1",
    0x9303e80e: "IO_SCSI_0e_CDB12_CYL2",
    0x9303e80f: "IO_SCSI_0f_LUN",
    0x9303e810: "IO_SCSI_10_CMD_PHASE",
    0x9303e811: "IO_SCSI_11_SYNC_XFER",
    0x9303e812: "IO_SCSI_12_COUNT2",
    0x9303e813: "IO_SCSI_13_COUNT1",
    0x9303e814: "IO_SCSI_14_COUNT0",
    0x9303e815: "IO_SCSI_15_DEST_ID",
    0x9303e816: "IO_SCSI_16_SRC_ID",
    0x9303e817: "IO_SCSI_17_SCSI_STATUS",
    0x9303e818: "IO_SCSI_18_CMD",
    0x9303e819: "IO_SCSI_19_DATA",
    0x9303e81f: "IO_SCSI_1f_AUX_STATUS",
    0xffff0000: "IO_BDRV1_p24",
    0xffff0001: "IO_BDRV2_p24",
    0xffff0002: "IO_BDRV3_p24",
    0xffff0003: "IO_BDRV4_p24",

    # MM58167 RTC Chip
    0xffff8000: "IO_RTC_COUNTER_M_SEC",
    0xffff8001: "IO_RTC_COUNTER_H_T_SEC",
    0xffff8002: "IO_RTC_COUNTER_SEC",
    0xffff8003: "IO_RTC_COUNTER_MIN",
    0xffff8004: "IO_RTC_COUNTER_HOUR",
    0xffff8005: "IO_RTC_COUNTER_WEEKDAY",
    0xffff8006: "IO_RTC_COUNTER_MONTHDAY",
    0xffff8007: "IO_RTC_COUNTER_MONTH",
    0xffff8008: "IO_RTC_RAM_M_SEC",
    0xffff8009: "IO_RTC_RAM_YEAR",
    0xffff800a: "IO_RTC_RAM_SEC",
    0xffff800b: "IO_RTC_RAM_MIN",
    0xffff800c: "IO_RTC_RAM_HOUR",
    0xffff800d: "IO_RTC_RAM_WEEKDAY",
    0xffff800e: "IO_RTC_RAM_MONTHDAY",
    0xffff800f: "IO_RTC_RAM_MONTH",
    0xffff8010: "IO_RTC_INTERRUPT_STATUS",
    0xffff8011: "IO_RTC_INTERRUPT_CONTROL",
    0xffff8012: "IO_RTC_COUNTERS_RESET",
    0xffff8013: "IO_RTC_RAM_RESET",
    0xffff8014: "IO_RTC_STATUS_BIT",
    0xffff8015: "IO_RTC_GO_COMMAND",
    0xffff8016: "IO_RTC_STANDBY_INTERRUPT",
    0xffff801f: "IO_RTC_TEST_MODE",

    # SCN2661 UART
    0xffff9000: "IO_UART_DATA",
    0xffff9001: "IO_UART_STATUS",
    0xffff9002: "IO_UART_MODE",
    0xffff9003: "IO_UART_COMMAND",

    # SCN2681 DUART
    0xffffa000: "IO_DUART_MODEM_MODE",
    0xffffa001: "IO_DUART_MODEM_STATUS",
    0xffffa002: "IO_DUART_MODEM_COMMAND",
    0xffffa003: "IO_DUART_MODEM_HOLDING",
    0xffffa004: "IO_DUART_MODEM_AUX",
    0xffffa005: "IO_DUART_MODEM_INTERRUPT",
    0xffffa006: "IO_DUART_MODEM_COUNTER_HIGH",
    0xffffa007: "IO_DUART_MODEM_COUNTER_LOW",
    0xffffa008: "IO_DUART_DIAG_MODE",
    0xffffa009: "IO_DUART_DIAG_STATUS",
    0xffffa00a: "IO_DUART_DIAG_COMMAND",
    0xffffa00b: "IO_DUART_DIAG_HOLDING",
    0xffffa00c: "IO_DUART_DIAG_AUX",
    0xffffa00d: "IO_DUART_DIAG_INTERRUPT",
    0xffffa00e: "IO_DUART_DIAG_COUNTER_HIGH",
    0xffffa00f: "IO_DUART_DIAG_COUNTER_LOW",

    # 0xffffbxxx = DEV.EXTERNAL signal, modem ?

    0xfffff300: "IO_SENREG_p25",
    0xfffff400: "IO_DREG5_p24",
    0xfffffe00: "IO_BREG4_p23",
    0xffffff00: "IO_SENSE_p25",
}

def add_symbols(asp):
    ''' Add our symbols to an address-space '''
    for a, b in DEVICE_SYMBOLS.items():
        asp.set_label(a, b)
