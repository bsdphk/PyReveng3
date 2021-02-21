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

    0x9303e000: "IO_RESHA_SCA_CTL",
    0x9303e001: "IO_DISK_WRITE_PROTECT",
    0x9303e002: "IO_RESHA_SCB_CTL",
    0x9303e004: "IO_RESHA_ETH_CTL",
    0x9303e006: "IO_RESHA_VME_CTL",
    0x9303e008: "IO_RESHA_RES_CTL",
    0x9303e00a: "IO_RESHA_EEPROM_PAGE_REGISTER",

    0x9303e100: "IO_SCSI_D_ADDRESS_REGISTER",
    0x9303e104: "IO_SCSI_T_ADDRESS_REGISTER",
    0x9303e108: "IO_SCSI_D_SEGMENT_REGISTER",
    0x9303e10c: "IO_SCSI_T_SEGMENT_REGISTER",

    0x9303e800: "IO_SCSI_D_00_OWN_ID_CDB_SIZE",
    0x9303e801: "IO_SCSI_D_01_CONTROL",
    0x9303e802: "IO_SCSI_D_02_TIMEOUT_PERIOD",
    0x9303e803: "IO_SCSI_D_03_CDBx1",
    0x9303e804: "IO_SCSI_D_04_CDBx2",
    0x9303e805: "IO_SCSI_D_05_CDBx3",
    0x9303e806: "IO_SCSI_D_06_CDBx4",
    0x9303e807: "IO_SCSI_D_07_CDBx5",
    0x9303e808: "IO_SCSI_D_08_CDBx6",
    0x9303e809: "IO_SCSI_D_09_CDBx7",
    0x9303e80a: "IO_SCSI_D_0a_CDBx8",
    0x9303e80b: "IO_SCSI_D_0b_CDBx9",
    0x9303e80c: "IO_SCSI_D_0c_CDBxa",
    0x9303e80d: "IO_SCSI_D_0d_CDBxb",
    0x9303e80e: "IO_SCSI_D_0e_CDBxc",
    0x9303e80f: "IO_SCSI_D_0f_LUN",
    0x9303e810: "IO_SCSI_D_10_CMD_PHASE",
    0x9303e811: "IO_SCSI_D_11_SYNC_XFER",
    0x9303e812: "IO_SCSI_D_12_COUNT2",
    0x9303e813: "IO_SCSI_D_13_COUNT1",
    0x9303e814: "IO_SCSI_D_14_COUNT0",
    0x9303e815: "IO_SCSI_D_15_DEST_ID",
    0x9303e816: "IO_SCSI_D_16_SRC_ID",
    0x9303e817: "IO_SCSI_D_17_SCSI_STATUS",
    0x9303e818: "IO_SCSI_D_18_CMD",
    0x9303e819: "IO_SCSI_D_19_DATA",
    0x9303e81f: "IO_SCSI_D_1f_AUX_STATUS",


    0x9303ec00: "IO_SCSI_T_00_OWN_ID_CDB_SIZE",
    0x9303ec01: "IO_SCSI_T_01_CONTROL",
    0x9303ec02: "IO_SCSI_T_02_TIMEOUT_PERIOD",
    0x9303ec03: "IO_SCSI_T_03_CDBx1",
    0x9303ec04: "IO_SCSI_T_04_CDBx2",
    0x9303ec05: "IO_SCSI_T_05_CDBx3",
    0x9303ec06: "IO_SCSI_T_06_CDBx4",
    0x9303ec07: "IO_SCSI_T_07_CDBx5",
    0x9303ec08: "IO_SCSI_T_08_CDBx6",
    0x9303ec09: "IO_SCSI_T_09_CDBx7",
    0x9303ec0a: "IO_SCSI_T_0a_CDBx8",
    0x9303ec0b: "IO_SCSI_T_0b_CDBx9",
    0x9303ec0c: "IO_SCSI_T_0c_CDBxa",
    0x9303ec0d: "IO_SCSI_T_0d_CDBxb",
    0x9303ec0e: "IO_SCSI_T_0e_CDBxc",
    0x9303ec0f: "IO_SCSI_T_0f_LUN",
    0x9303ec10: "IO_SCSI_T_10_CMD_PHASE",
    0x9303ec11: "IO_SCSI_T_11_SYNC_XFER",
    0x9303ec12: "IO_SCSI_T_12_COUNT2",
    0x9303ec13: "IO_SCSI_T_13_COUNT1",
    0x9303ec14: "IO_SCSI_T_14_COUNT0",
    0x9303ec15: "IO_SCSI_T_15_DEST_ID",
    0x9303ec16: "IO_SCSI_T_16_SRC_ID",
    0x9303ec17: "IO_SCSI_T_17_SCSI_STATUS",
    0x9303ec18: "IO_SCSI_T_18_CMD",
    0x9303ec19: "IO_SCSI_T_19_DATA",
    0x9303ec1f: "IO_SCSI_T_1f_AUX_STATUS",

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

    # SCN2661 UART (BVDEC0p18/15)
    0xffff9000: "IO_UART_DATA",
    0xffff9001: "IO_UART_STATUS",
    0xffff9002: "IO_UART_MODE",
    0xffff9003: "IO_UART_COMMAND",

    # SCN2681 DUART (BVDEC0p18/14)
    0xffffa000: "IO_DUART_MODEM_MODE",
    0xffffa001: "IO_DUART_MODEM_STATUS",
    0xffffa002: "IO_DUART_MODEM_COMMAND",
    0xffffa003: "IO_DUART_MODEM_DATA",
    0xffffa004: "IO_DUART_ACR_IPCR",
    0xffffa005: "IO_DUART_IMR_ISR",
    0xffffa006: "IO_DUART_CTUR_CTU",
    0xffffa007: "IO_DUART_CTLR_CTL",
    0xffffa008: "IO_DUART_DIAG_MODE",
    0xffffa009: "IO_DUART_DIAG_STATUS",
    0xffffa00a: "IO_DUART_DIAG_COMMAND",
    0xffffa00b: "IO_DUART_DIAG_DATA",
    0xffffa00c: "IO_DUART_RESERVED",
    0xffffa00d: "IO_DUART_OPCR",
    0xffffa00e: "IO_DUART_SET_OPC_START_COUNTER",
    0xffffa00f: "IO_DUART_CLR_OPC_STOP_COUNTER",

    # EXT MODEM  (BVDEC0p18/13)
    0xffffb002: "IO_EXT_MODEM_DATA",
    0xffffb003: "IO_EXT_MODEM_CONTROL",

    # BVDEC1 @p18
    0xfffff000: "IO_CLR_RUN_LED_p16",
    0xfffff100: "IO_GET_REQUEST_p69",
    0xfffff200: "IO_FRONT_PANEL_p27",
    0xfffff300: "IO_SENSE_TEST_p25",
    0xfffff400: "IO_WRITE_CONTROL_p24",
    0xfffff500: "IO_FIFO_INIT_p68_p69",
    0xfffff600: "IO_CPU_RESPONSE_p68",
    0xfffff700: "IO_CPU_REQUEST_p69",

    # BVDEC2 @p18
    0xfffff800: "IO_READ_STATUS_p24",
    0xfffff900: "IO_CLEAR_BERR_p24",
    0xfffffa00: "IO_MARGIN_CLOCK_p74",
    0xfffffb00: "IO_RD_IO_SLOT_p33",
    0xfffffc00: "IO_CONTROL_p28",
    0xfffffd00: "IO_CLR_PFINT_p23",
    0xfffffe00: "IO_CPU_CONTROL_PSU_MARGIN_BREG4_p23",
    0xffffff00: "IO_READ_SENSE_p25",
}

def add_symbols(asp):
    ''' Add our symbols to an address-space '''
    for a, b in DEVICE_SYMBOLS.items():
        asp.set_label(a, b)
